# AI NOVA (Agentic-Nexus) v2 - 개발 Phase 문서

## 프로젝트 개요

**AI NOVA**는 서울경제신문의 AI 기자 어시스턴트 플랫폼입니다.
LangGraph 기반 Multi-Agent 시스템으로 보도자료를 전문적인 경제 기사로 변환합니다.

---

## Phase 진행 현황

| Phase | 제목 | 상태 | 문서 |
|-------|-----|------|-----|
| 1 | Agent 아키텍처 구축 | ✅ 완료 | [PHASE1_AGENT_ARCHITECTURE.md](./PHASE1_AGENT_ARCHITECTURE.md) |
| 2 | 프론트엔드 연동 | ✅ 완료 | [PHASE2_FRONTEND_INTEGRATION.md](./PHASE2_FRONTEND_INTEGRATION.md) |
| 3 | 프롬프트 시스템 | ✅ 완료 | [PHASE3_PROMPT_SYSTEM.md](./PHASE3_PROMPT_SYSTEM.md) |
| 4 | 로컬 Docker 환경 | ✅ 완료 | [PHASE4_LOCAL_DOCKER_SETUP.md](./PHASE4_LOCAL_DOCKER_SETUP.md) |
| 5 | 데이터 로딩 | ✅ 완료 | [PHASE5_DATA_LOADING.md](./PHASE5_DATA_LOADING.md) |

---

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │ WriterWorkspace  │  │  ArticleEditor   │  │ AgentProgress  │ │
│  └────────┬─────────┘  └────────┬─────────┘  └───────┬────────┘ │
└───────────┼──────────────────────┼─────────────────────┼────────┘
            │ REST API             │ WebSocket           │
            ▼                      ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  LangGraph Workflow                       │   │
│  │  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐  │   │
│  │  │ Phase 1 │ → │ Phase 2 │ → │ Phase 3 │ → │  END    │  │   │
│  │  │ 소재수집 │   │ 기사작성 │   │ 마무리  │   │         │  │   │
│  │  └─────────┘   └─────────┘   └─────────┘   └─────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
            │                      │                     │
            ▼                      ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                        AWS Services                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐ │
│  │  Bedrock   │  │  Aurora    │  │  DynamoDB  │  │ AgentCore │ │
│  │ (Claude 4) │  │ (pgvector) │  │ (Prompts)  │  │ (Memory)  │ │
│  └────────────┘  └────────────┘  └────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 16개 Agent 구성

### Phase 1: 소재 수집
| Agent | ID | 역할 |
|-------|----|----|
| IssueCollector | ISSUE | 이슈 수집 |
| SourceAnalyzer | SRC_ANAL | 소스 분석 |
| SourceIntegrator | SRC_INT | 소스 통합 |

### Phase 2: 기사 작성
| Agent | ID | 역할 | Temperature |
|-------|----|----|------------|
| W1Writer | W1 | 기사 초안 작성 | 0.81 |
| T1Titler | T1 | 제목 생성 | 0.85 |
| P1Proofreader | P1 | 교정 | 0.02 |
| R1Reviser | R1 | 퇴고 | 0.5 |
| QualityGate | QGATE | 품질 검증 | - |
| StyleChecker | STYLE | 스타일 검사 | 0.1 |

### Phase 3: 최종 마무리
| Agent | ID | 역할 |
|-------|----|----|
| LayoutAgent | LAYOUT | 레이아웃 |
| DrugAgent | DRUG | 금칙어 검사 |
| FactChecker | FACT | 팩트체크 |
| InfographicAgent | INFOG | 인포그래픽 |
| ImageAgent | IMAGE | 이미지 생성 |
| TTSAgent | TTS | 음성 변환 |
| FinalReviewer | FINAL | 최종 검토 |

---

## 기술 스택

| 구성 요소 | 기술 |
|----------|-----|
| LLM | AWS Bedrock (Claude Sonnet 4) |
| 워크플로우 | LangGraph |
| 벡터 DB | Aurora PostgreSQL + pgvector |
| 프롬프트 저장 | DynamoDB |
| 캐시 | Redis |
| API 서버 | FastAPI |
| 프론트엔드 | React + Vite |
| 메모리 | AgentCore (AWS Managed) |

---

## 빠른 시작

### 1. 로컬 환경 설정

```bash
# Docker 서비스 시작
cd backend/agents/docker
./start-local.sh

# 전체 설정 (DB + 프롬프트 + 데이터)
cd backend/agents
./scripts/setup_local.sh
```

### 2. 백엔드 서버 시작

```bash
cd backend/agents
source venv/bin/activate
python main.py
```

### 3. 프론트엔드 시작

```bash
cd frontend
npm install
npm run dev
```

### 4. 접속

- Frontend: http://localhost:5173
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

---

## 디렉토리 구조

```
v2/
├── frontend/
│   └── src/
│       └── features/
│           └── workspace/
│               ├── components/
│               │   ├── ArticleEditor.jsx
│               │   └── AgentProgressPanel.jsx
│               ├── hooks/
│               │   └── useAgentWorkflow.js
│               └── services/
│                   └── agentWorkflowService.js
│
├── backend/
│   └── agents/
│       ├── src/
│       │   ├── agents/          # 16개 Agent
│       │   ├── workflow/        # LangGraph
│       │   ├── prompts/         # 프롬프트 로더
│       │   ├── tools/           # Agent 도구
│       │   ├── database/        # DB 연결
│       │   └── memory/          # 메모리 관리
│       ├── docker/              # 로컬 환경
│       ├── scripts/             # 설정 스크립트
│       └── main.py              # FastAPI
│
└── docs/
    └── phase/                   # 개발 문서
        ├── README.md
        ├── PHASE1_AGENT_ARCHITECTURE.md
        ├── PHASE2_FRONTEND_INTEGRATION.md
        ├── PHASE3_PROMPT_SYSTEM.md
        ├── PHASE4_LOCAL_DOCKER_SETUP.md
        └── PHASE5_DATA_LOADING.md
```

---

## 다음 단계 (TODO)

- [ ] 통합 테스트 작성
- [ ] AWS 프로덕션 배포 설정
- [ ] 모니터링/로깅 시스템
- [ ] 성능 최적화
- [ ] 기자 스타일 학습 고도화

---

## 작성자

- **작업일**: 2026-02-15
- **모델**: Claude Opus 4.5
