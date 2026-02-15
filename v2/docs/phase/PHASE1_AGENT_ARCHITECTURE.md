# Phase 1: Agent 아키텍처 구축

## 개요
AI NOVA (Agentic-Nexus) v2의 핵심 Agent 시스템 구축

**작업 기간**: 2026-02-15
**상태**: 완료

---

## 1. 아키텍처 설계

### 1.1 16개 Agent 구성

| Phase | Agent | ID | 역할 |
|-------|-------|----|----|
| **Phase 1: 소재 수집** | IssueCollector | ISSUE | 이슈 수집 |
| | SourceAnalyzer | SRC_ANAL | 소스 분석 |
| | SourceIntegrator | SRC_INT | 소스 통합 |
| **Phase 2: 기사 작성** | W1Writer | W1 | 기사 초안 작성 |
| | T1Titler | T1 | 제목 생성 (TITLE-NOMICS 3.0) |
| | P1Proofreader | P1 | 교정 |
| | R1Reviser | R1 | 퇴고 |
| | QualityGate | QGATE | 품질 검증 |
| | StyleChecker | STYLE | 스타일 검사 |
| **Phase 3: 최종 마무리** | LayoutAgent | LAYOUT | 레이아웃 |
| | DrugAgent | DRUG | 약물/금칙어 검사 |
| | FactChecker | FACT | 팩트체크 |
| | InfographicAgent | INFOG | 인포그래픽 |
| | ImageAgent | IMAGE | 이미지 생성 |
| | TTSAgent | TTS | 음성 변환 |
| | FinalReviewer | FINAL | 최종 검토 |

### 1.2 LangGraph 워크플로우

```
[START]
    │
    ▼
┌─────────────────────────────────────┐
│  Phase 1: 소재 수집                  │
│  ┌──────────────────────────────┐   │
│  │ issue_collector              │   │
│  │       ↓                      │   │
│  │ source_analyzer              │   │
│  │       ↓                      │   │
│  │ source_integrator            │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  Phase 2: 기사 작성 (Quality Loop)   │
│  ┌──────────────────────────────┐   │
│  │ w1_writer → t1_titler        │   │
│  │       ↓                      │   │
│  │ p1_proofreader               │   │
│  │       ↓                      │   │
│  │ r1_reviser                   │   │
│  │       ↓                      │   │
│  │ quality_gate ─────────────┐  │   │
│  │   │ pass        │ revise  │  │   │
│  │   ▼             └─────────┘  │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  Phase 3: 최종 마무리 (병렬 실행)    │
│  ┌────────────────────────────────┐ │
│  │ layout_agent  ║  drug_agent   │ │
│  │ fact_checker  ║  style_checker│ │
│  │       ↓                       │ │
│  │ infographic ║ image ║ tts    │ │
│  │       ↓                       │ │
│  │    final_reviewer             │ │
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘
    │
    ▼
  [END]
```

---

## 2. 핵심 구현 파일

### 2.1 디렉토리 구조

```
backend/agents/
├── src/
│   ├── agents/                 # 16개 Agent 구현
│   │   ├── __init__.py
│   │   ├── base_agent.py       # 기본 Agent 클래스
│   │   ├── w1_writer.py        # 기사 작성
│   │   ├── t1_titler.py        # 제목 생성
│   │   ├── p1_proofreader.py   # 교정
│   │   ├── r1_reviser.py       # 퇴고
│   │   ├── quality_gate.py     # 품질 검증
│   │   ├── style_checker.py    # 스타일 검사
│   │   ├── fact_checker.py     # 팩트체크
│   │   └── ... (기타 Agent)
│   │
│   ├── workflow/               # LangGraph 워크플로우
│   │   ├── __init__.py
│   │   ├── graph.py            # 워크플로우 정의
│   │   └── state.py            # 상태 스키마
│   │
│   ├── prompts/                # 프롬프트 관리
│   │   ├── __init__.py
│   │   ├── prompt_loader.py    # DynamoDB 프롬프트 로더
│   │   └── prompt_templates.py # 폴백 템플릿
│   │
│   ├── tools/                  # Agent 도구
│   │   ├── bigkinds.py         # 빅카인즈 API
│   │   ├── web_search.py       # 웹 검색
│   │   ├── image_gen.py        # 이미지 생성
│   │   └── tts.py              # TTS
│   │
│   ├── database/               # 데이터베이스
│   │   ├── connection.py       # DB 연결
│   │   ├── vector_store.py     # 벡터 스토어
│   │   ├── kb_repository.py    # KB 규칙 저장소
│   │   └── stylebook_repository.py
│   │
│   └── memory/                 # 메모리 관리
│       ├── agent_core.py       # AgentCore 통합
│       ├── session_memory.py   # 세션 메모리
│       └── reporter_memory.py  # 기자 스타일 학습
│
├── docker/                     # 로컬 개발 환경
├── scripts/                    # 설정 스크립트
├── main.py                     # FastAPI 서버
├── requirements.txt
└── .env.example
```

### 2.2 BaseAgent 클래스

```python
# src/agents/base_agent.py

class BaseAgent(ABC):
    def __init__(
        self,
        name: str,
        agent_id: str,
        model_id: str = "anthropic.claude-sonnet-4-20250514",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        self.llm = ChatBedrockConverse(
            model=model_id,
            region_name="ap-northeast-2",
            temperature=temperature,
            max_tokens=max_tokens,
        )

    @abstractmethod
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        pass

    # KB/스타일북 검색
    async def get_kb_context(self, query: str, top_k: int = 5) -> str
    async def get_style_context(self, query: str, top_k: int = 3) -> str
    async def get_examples(self, query: str, top_k: int = 3) -> List[Dict]
    async def get_reporter_context(self, reporter_id: str) -> str

    # 프롬프트 로딩
    def get_system_prompt(self, prompt_type: str, engine_type: str = None) -> str
    def get_prompt_with_context(self, prompt_type, engine_type, kb_context, ...) -> str
```

### 2.3 워크플로우 상태

```python
# src/workflow/state.py

class WorkflowState(TypedDict):
    # 입력
    user_id: str
    reporter_id: str
    sources: List[Dict[str, Any]]
    article_type: str  # daily, print, online
    engine_type: str   # 11 (기업), 22 (정부/공공)

    # 중간 결과
    selected_sources: List[Dict[str, Any]]
    integrated_context: Dict[str, Any]
    draft: str
    titles: List[Dict[str, str]]
    corrections: List[Dict[str, Any]]

    # 품질 관리
    quality_score: int
    revision_count: int
    max_revisions: int

    # 최종 결과
    final_article: str
    final_title: str
    layout_info: Dict[str, Any]
    media_assets: Dict[str, Any]

    # 메타데이터
    current_step: str
    errors: List[str]
    created_at: str
```

---

## 3. 기술 스택

| 구성 요소 | 기술 |
|----------|-----|
| LLM | AWS Bedrock (Claude Sonnet 4) |
| 워크플로우 | LangGraph |
| 벡터 DB | Aurora PostgreSQL + pgvector |
| 프롬프트 저장 | DynamoDB |
| 캐시 | Redis |
| API 서버 | FastAPI |
| 메모리 | AgentCore (AWS Managed) |

---

## 4. Agent별 설정

| Agent | Temperature | Max Tokens | 특징 |
|-------|-------------|------------|------|
| W1Writer | 0.81 | 16384 | 창의적 기사 작성 |
| T1Titler | 0.85 | 2048 | 높은 창의성 |
| P1Proofreader | 0.02 | 4096 | 정확성 우선 |
| R1Reviser | 0.5 | 8192 | 균형잡힌 퇴고 |
| FactChecker | 0.1 | 4096 | 사실 검증 |
| StyleChecker | 0.1 | 2048 | 규칙 기반 |

---

## 5. 다음 단계

- [ ] Phase 2: 프론트엔드 연동
- [ ] Phase 3: 프롬프트 시스템
- [ ] Phase 4: 로컬 개발 환경
- [ ] Phase 5: 데이터 로딩
