# Phase 5: KB/스타일북 데이터 로딩

## 개요
초기 데이터 로딩 스크립트 구현

**작업 기간**: 2026-02-15
**상태**: 완료

---

## 1. 데이터 로딩 스크립트

### 1.1 KB 규칙 로딩

**파일**: `scripts/load_kb_data.py`

#### KB 규칙 데이터

| Agent | 규칙 유형 | 예시 |
|-------|----------|-----|
| W1 | structure | 역피라미드 구조 |
| W1 | style | 첫 문장 규칙 (50자 이내) |
| W1 | policy | 정치 중립성 원칙 |
| W1 | term | 경제 전문용어 사용 |
| T1 | format | 제목 글자 수 (50자) |
| T1 | style | 제목 문체 (현재형) |
| T1 | seo | SEO 최적화 |
| P1 | grammar | 주어-서술어 호응 |
| P1 | spelling | 띄어쓰기 |
| P1 | format | 숫자 표기 |
| R1 | style | 간결한 문장 |
| R1 | style | 피동 → 능동 |
| R1 | structure | 문단 구성 |

```python
KB_RULES_DATA = [
    {
        "agent_id": "W1",
        "rule_type": "structure",
        "title": "역피라미드 구조",
        "content": "기사는 역피라미드 구조로 작성합니다. 첫 문단에 핵심 내용(5W1H)을 배치...",
        "priority": 10
    },
    {
        "agent_id": "W1",
        "rule_type": "policy",
        "title": "정치 중립성 원칙",
        "content": "정부/공공 보도자료(Engine 22) 기사화 시 정치적 중립을 엄격히 유지...",
        "priority": 10
    },
    # ... 총 13개 규칙
]
```

### 1.2 스타일북 데이터

| 카테고리 | 서브카테고리 | 규칙 |
|---------|------------|-----|
| 표기법 | 숫자 | 금액 표기 (만 단위 한글 혼용) |
| 표기법 | 숫자 | 퍼센트 표기 (%) |
| 표기법 | 날짜 | 날짜 표기 |
| 용어 | 경제 | 주식 관련 용어 |
| 용어 | 금융 | 금리 관련 용어 |
| 문체 | 어미 | 서술어 어미 (~다) |
| 문체 | 시제 | 시제 통일 |
| 인용 | 직접인용 | 인용문 형식 |
| 인용 | 간접인용 | 간접인용 표현 |

```python
STYLEBOOK_DATA = [
    {
        "category": "표기법",
        "subcategory": "숫자",
        "rule_name": "금액 표기",
        "description": "만 단위 이상의 금액은 한글을 혼용하여 표기합니다.",
        "correct_example": "1억5000만원, 23조원, 500만달러",
        "incorrect_example": "150,000,000원, 23,000,000,000,000원"
    },
    # ... 총 9개 규칙
]
```

### 1.3 Few-shot 예시

```python
EXAMPLES_DATA = [
    # P1 교정 예시
    {
        "agent_id": "P1",
        "example_type": "correction",
        "wrong_text": "삼성전자가 새로운 반도체 개발에 착수 했다.",
        "correct_text": "삼성전자가 새로운 반도체 개발에 착수했다.",
        "explanation": "동사와 보조동사 사이 띄어쓰기 오류"
    },
    {
        "agent_id": "P1",
        "example_type": "correction",
        "wrong_text": "150,000,000원의 투자를 유치했다.",
        "correct_text": "1억5000만원의 투자를 유치했다.",
        "explanation": "금액 표기 규칙. 만 단위 이상은 한글 혼용."
    },
    # ... 총 5개 예시
]
```

---

## 2. DynamoDB 프롬프트 로딩

**파일**: `scripts/load_prompts_dynamodb.py`

### 2.1 테이블 생성

```python
TABLES = {
    "sedaily-bodo-prompts": {...},
    "sedaily-title-prompts": {...},
    "sedaily-proofreading-prompts": {...},
    "sedaily-regression-prompts": {...},
}
```

### 2.2 프롬프트 데이터

#### W1 - 기업 보도자료 (Engine 11)
```json
{
  "promptId": "system_w1_engine11",
  "promptName": "기업 보도자료 기사화",
  "engineType": "11",
  "prompt": {
    "instruction": "당신은 서울경제신문의 AI 기자입니다...",
    "description": "기업 보도자료를 전문적인 경제 기사로 변환"
  }
}
```

#### W1 - 정부/공공 보도자료 (Engine 22)
```json
{
  "promptId": "system_w1_engine22",
  "promptName": "정부/공공 보도자료 기사화",
  "engineType": "22",
  "prompt": {
    "instruction": "절대 규칙: 정치인 실명 사용 금지...",
    "description": "정치적 중립성 유지"
  }
}
```

#### T1 - TITLE-NOMICS 3.0
```json
{
  "promptId": "system_t1_titlegen",
  "promptName": "TITLE-NOMICS 3.0",
  "prompt": {
    "instruction": "4명의 전문가 협업 시스템...",
    "description": "5가지 유형 제목 생성"
  }
}
```

#### P1 - 교정 AI
```json
{
  "promptId": "system_p1_proofread",
  "promptName": "교정 AI P1",
  "prompt": {
    "instruction": "맞춤법, 문법, 스타일 검사...",
    "description": "JSON 형식 교정 결과 반환"
  }
}
```

#### R1 - 퇴고 시스템
```json
{
  "promptId": "system_r1_revision",
  "promptName": "퇴고 시스템 R1",
  "prompt": {
    "instruction": "간결성, 명확성, 가독성 향상...",
    "description": "문장 다듬기"
  }
}
```

---

## 3. 임베딩 생성

### 3.1 Bedrock Titan 사용

```python
bedrock_runtime = boto3.client("bedrock-runtime", region_name="ap-northeast-2")

async def get_embedding(text: str) -> List[float]:
    """Bedrock Titan으로 임베딩 생성"""
    response = bedrock_runtime.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        body=json.dumps({"inputText": text[:8000]}),
        contentType="application/json"
    )
    result = json.loads(response["body"].read())
    return result["embedding"]  # 1536 차원
```

### 3.2 데이터 삽입

```python
async def load_data():
    conn = await asyncpg.connect(DATABASE_URL)

    # KB 규칙 로딩
    for rule in KB_RULES_DATA:
        embedding = await get_embedding(f"{rule['title']} {rule['content']}")
        await conn.execute("""
            INSERT INTO kb_rules (agent_id, rule_type, title, content, embedding, priority)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, rule["agent_id"], rule["rule_type"], rule["title"],
            rule["content"], embedding, rule["priority"])

    # 스타일북 로딩
    for style in STYLEBOOK_DATA:
        text = f"{style['category']} {style['rule_name']} {style['description']}"
        embedding = await get_embedding(text)
        await conn.execute("""
            INSERT INTO stylebook (category, subcategory, rule_name, ...)
            VALUES ($1, $2, $3, ...)
        """, ...)

    await conn.close()
```

---

## 4. 실행 방법

### 4.1 전체 설정

```bash
cd backend/agents
./scripts/setup_local.sh
```

### 4.2 개별 실행

```bash
# DynamoDB 프롬프트
python scripts/load_prompts_dynamodb.py

# KB/스타일북 데이터
python scripts/load_kb_data.py
```

### 4.3 실행 결과

```
============================================
데이터 로딩 완료!
============================================
- KB 규칙: 13건
- 스타일북: 9건
- 예시: 5건
============================================
```

---

## 5. 데이터 확인

### 5.1 PostgreSQL

```sql
-- KB 규칙 확인
SELECT agent_id, COUNT(*) FROM kb_rules GROUP BY agent_id;

-- 스타일북 확인
SELECT category, COUNT(*) FROM stylebook GROUP BY category;

-- 벡터 검색 테스트
SELECT * FROM search_kb_rules(
    'W1',
    (SELECT embedding FROM kb_rules LIMIT 1),
    5,
    0.5
);
```

### 5.2 DynamoDB

```bash
# AWS CLI (로컬)
aws dynamodb scan \
  --table-name sedaily-bodo-prompts \
  --endpoint-url http://localhost:8000

# 테이블 목록
aws dynamodb list-tables --endpoint-url http://localhost:8000
```
