# Phase 3: 프롬프트 시스템 구축

## 개요
DynamoDB 기반 프롬프트 관리 및 Agent 적용

**작업 기간**: 2026-02-15
**상태**: 완료

---

## 1. 프롬프트 아키텍처

### 1.1 로딩 흐름

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────┐
│  Agent 요청     │ ──▶ │  PromptLoader    │ ──▶ │  DynamoDB      │
│  (W1, T1, ...)  │     │  (prompt_loader) │     │  (프롬프트 저장)│
└─────────────────┘     └──────────────────┘     └────────────────┘
                               │                         │
                               │ 실패 시                  │
                               ▼                         │
                        ┌──────────────────┐             │
                        │  폴백 템플릿      │             │
                        │  (prompt_templates)            │
                        └──────────────────┘             │
                               │                         │
                               ▼                         ▼
                        ┌──────────────────────────────────┐
                        │        시스템 프롬프트           │
                        │  + KB 컨텍스트                   │
                        │  + 스타일북 컨텍스트             │
                        │  + 기자 스타일 컨텍스트          │
                        └──────────────────────────────────┘
```

### 1.2 프롬프트 유형

| 프롬프트 | 테이블명 | 설명 |
|---------|---------|------|
| W1 | sedaily-bodo-prompts | 기사 작성 (Engine 11/22) |
| T1 | sedaily-title-prompts | 제목 생성 (TITLE-NOMICS) |
| P1 | sedaily-proofreading-prompts | 교정 |
| R1 | sedaily-regression-prompts | 퇴고 |
| FACT_CHECK | (폴백 사용) | 팩트체크 |
| STYLE_CHECK | (폴백 사용) | 스타일 검사 |

---

## 2. 구현 파일

### 2.1 프롬프트 로더

**파일**: `src/prompts/prompt_loader.py`

```python
PROMPT_TABLES = {
    "W1": os.getenv("DYNAMO_BODO_TABLE", "sedaily-bodo-prompts"),
    "T1": os.getenv("DYNAMO_TITLE_TABLE", "sedaily-title-prompts"),
    "P1": os.getenv("DYNAMO_PROOF_TABLE", "sedaily-proofreading-prompts"),
    "R1": os.getenv("DYNAMO_REGRESSION_TABLE", "sedaily-regression-prompts"),
}

DEFAULT_PROMPT_IDS = {
    "W1_11": "system_w1_engine11",  # 기업 보도자료
    "W1_22": "system_w1_engine22",  # 정부/공공 보도자료
    "T1": "system_t1_titlegen",
    "P1": "system_p1_proofread",
    "R1": "system_r1_revision",
}

class PromptLoader:
    @lru_cache(maxsize=50)
    def get_prompt(self, prompt_type, engine_type=None, prompt_id=None):
        """DynamoDB에서 프롬프트 조회"""
        # 1. 캐시 확인
        # 2. DynamoDB 조회
        # 3. 실패 시 폴백 템플릿 사용
        ...

    def get_system_prompt(self, prompt_type, engine_type=None) -> str:
        """시스템 프롬프트 텍스트만 반환"""
        ...

    def get_prompt_with_files(self, prompt_type, engine_type=None):
        """프롬프트 + 첨부 파일"""
        ...
```

### 2.2 폴백 템플릿

**파일**: `src/prompts/prompt_templates.py`

```python
PROMPT_TEMPLATES = {
    "W1": {
        "11": {  # 기업 보도자료
            "instruction": """당신은 서울경제신문의 AI 기자입니다.
[기업 보도자료 기사화 시스템 W1 v2.0]
...
""",
        },
        "22": {  # 정부/공공 보도자료
            "instruction": """당신은 서울경제신문의 AI 기자입니다.
[정부/공공 보도자료 기사화 시스템 W1 v2.0]

절대 규칙:
- 정치인(대통령, 장관, 국회의원) 실명 사용 금지
- 여당, 야당, 정당명 언급 금지
...
""",
        },
    },
    "T1": {
        "default": {
            "instruction": """당신은 TITLE-NOMICS 3.0...
[4명의 전문가 협업 시스템]
1. 정통 경제 저널리스트 (김기자)
2. 디지털 마케터 (이매니저)
3. 소셜 미디어 전략가 (박에디터)
4. 행동경제학자 (최박사)
...
""",
        },
    },
    "P1": { ... },
    "R1": { ... },
    "FACT_CHECK": { ... },
    "STYLE_CHECK": { ... },
}
```

---

## 3. Agent 적용

### 3.1 BaseAgent 메서드

```python
# src/agents/base_agent.py

def get_system_prompt(self, prompt_type: str, engine_type: str = None) -> str:
    """DynamoDB에서 시스템 프롬프트 로딩"""
    try:
        return prompt_loader.get_system_prompt(prompt_type, engine_type)
    except Exception as e:
        logger.warning(f"프롬프트 로딩 실패, 폴백 사용: {e}")
        # 폴백: 템플릿에서 로딩
        template = PROMPT_TEMPLATES.get(prompt_type, {})
        if engine_type and engine_type in template:
            return template[engine_type].get("instruction", "")
        return template.get("default", {}).get("instruction", "")

def get_prompt_with_context(
    self,
    prompt_type: str,
    engine_type: str = None,
    kb_context: str = "",
    style_context: str = "",
    reporter_context: str = "",
) -> str:
    """프롬프트 + KB 컨텍스트 조합"""
    base_prompt = self.get_system_prompt(prompt_type, engine_type)

    context_parts = []
    if kb_context:
        context_parts.append(f"\n\n[KB 규칙]\n{kb_context}")
    if style_context:
        context_parts.append(f"\n\n[스타일 가이드]\n{style_context}")
    if reporter_context:
        context_parts.append(f"\n\n[기자 스타일]\n{reporter_context}")

    return base_prompt + "".join(context_parts)
```

### 3.2 Agent별 적용

#### W1 Writer
```python
# 시스템 프롬프트 구성 (DynamoDB 또는 폴백 템플릿에서 로드)
base_prompt = self.get_prompt_with_context(
    prompt_type="W1",
    engine_type=engine_type,  # "11" 또는 "22"
    kb_context=kb_rules,
    style_context=style_rules,
    reporter_context=reporter_style,
)
```

#### T1 Titler
```python
# DynamoDB에서 T1 프롬프트 로드
base_prompt = self.get_prompt_with_context(
    prompt_type="T1",
    kb_context=kb_rules,
)
```

#### P1 Proofreader
```python
# DynamoDB 또는 폴백 템플릿에서 로드
base_prompt = self.get_prompt_with_context(
    prompt_type="P1",
    kb_context=kb_rules,
    style_context=style_rules,
)
```

#### R1 Reviser
```python
# DynamoDB에서 R1 프롬프트 로드
base_prompt = self.get_prompt_with_context(
    prompt_type="R1",
    kb_context=kb_rules,
    style_context=style_rules,
)
```

---

## 4. DynamoDB 스키마

### 4.1 프롬프트 아이템 구조

```json
{
  "promptId": "system_w1_engine11",
  "promptName": "기업 보도자료 기사화",
  "engineType": "11",
  "isPublic": true,
  "prompt": {
    "description": "기업 보도자료를 전문적인 경제 기사로 변환합니다.",
    "instruction": "당신은 서울경제신문의 AI 기자입니다..."
  },
  "files": [],
  "metadata": {
    "version": "2.0",
    "lastUpdated": "2026-02-15T10:00:00Z"
  }
}
```

---

## 5. 프롬프트 vs Knowledge Base

| 구분 | DynamoDB 프롬프트 | Bedrock Knowledge Base |
|------|------------------|----------------------|
| **용도** | 시스템 instruction (역할 정의) | 참조 자료 검색 (RAG) |
| **예시** | "당신은 서울경제신문 AI 기자입니다..." | 스타일북, KB 규칙, 예시 기사 |
| **로딩 방식** | 직접 로드 → 시스템 프롬프트 | 검색 → 컨텍스트 추가 |
| **변경 빈도** | 낮음 (시스템 설정) | 높음 (지식 업데이트) |

**권장 아키텍처:**
- 시스템 프롬프트: DynamoDB (또는 코드 내 템플릿)
- 참조 자료: Aurora pgvector 또는 Bedrock KB
