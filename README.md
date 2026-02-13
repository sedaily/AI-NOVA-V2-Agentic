# AI NOVA (Agentic-Nexus)

서울경제신문 AI 기자 어시스턴트 통합 플랫폼

## 개요

AI NOVA는 서울경제신문의 AI 서비스들(제목생성, 교열, 보도자료, 외신, 퇴고, 버디)을 하나의 통합 인터페이스로 제공하는 **모노레포 프로젝트**입니다.

- **frontend/**: React 기반 통합 UI
- **backend/**: AWS Lambda 기반 6개 서비스 (Python 3.11)

## 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│  AI NOVA Frontend (이 프로젝트)                              │
│  /Users/yeong-gwang/Documents/work/서울경제신문/DEV/Agentic-Nexus │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  buddy (b1)   │   │  title (t1)   │   │ proofreading  │
│ b1.sedaily.ai │   │ t1.sedaily.ai │   │  (p1)         │
└───────────────┘   └───────────────┘   │ p1.sedaily.ai │
                                        └───────────────┘
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  foreign (f1) │   │   bodo (w1)   │   │ regression(r1)│
│ f1.sedaily.ai │   │ w1.sedaily.ai │   │ r1.sedaily.ai │
└───────────────┘   └───────────────┘   └───────────────┘
```

## 프로젝트 구조

```
Agentic-Nexus/
├── README.md
├── frontend/                    # React 프론트엔드
│   ├── src/
│   │   ├── config/
│   │   │   └── buddyServiceConfig.js  # 서비스 엔드포인트 매핑
│   │   ├── features/
│   │   │   ├── auth/           # AWS Cognito 인증
│   │   │   ├── chat/           # 채팅 (WebSocket)
│   │   │   │   ├── components/
│   │   │   │   │   ├── BuddyButtons.jsx
│   │   │   │   │   ├── ChatPage.jsx
│   │   │   │   │   └── ChatInput.jsx
│   │   │   │   └── services/
│   │   │   │       └── websocketService.js
│   │   │   └── dashboard/
│   │   └── config.js
│   ├── .env
│   └── package.json
│
└── backend/                     # AWS Lambda 백엔드
    ├── README.md
    ├── buddy/                   # b1 - 일보버디, 기사버디
    │   ├── internal/            # 내부용 (sedaily.com)
    │   └── external/            # 외부용 (b1.sedaily.ai)
    │       └── two/             # 현재 운영 버전
    ├── title/                   # t1 - 제목생성
    │   ├── internal/
    │   └── external/
    │       └── two/
    ├── proofreading/            # p1 - 교열
    │   ├── internal/
    │   └── external/
    │       └── two/
    ├── bodo/                    # w1 - 보도자료
    │   ├── internal/
    │   └── external/
    │       └── two/
    ├── foreign/                 # f1 - 외신
    │   ├── internal/
    │   └── external/
    │       └── two/
    └── regression/              # r1 - 퇴고
        ├── internal/
        └── external/
            └── two/
```

## 버디 ↔ 백엔드 서비스 매핑

| 버디 | 서비스코드 | 백엔드 위치 | 도메인 |
|------|-----------|-------------|--------|
| 일보버디, 기사버디 | b1 | `backend/buddy/external/two` | b1.sedaily.ai |
| 제목생성_5종, 제목창의_7종 | t1 | `backend/title/external/two` | t1.sedaily.ai |
| 교열_경제분야, 교열_사회분야 | p1 | `backend/proofreading/external/two` | p1.sedaily.ai |
| 보도자료_기업, 보도자료_공공 | w1 | `backend/bodo/external/two` | w1.sedaily.ai |
| 외신_영어, 외신_일어 | f1 | `backend/foreign/external/two` | f1.sedaily.ai |
| 퇴고_단문, 퇴고_장문 | r1 | `backend/regression/external/two` | r1.sedaily.ai |

## AWS 리소스 엔드포인트

### WebSocket API (실시간 채팅)

| 서비스 | WebSocket URL |
|--------|---------------|
| buddy (b1) | `wss://dwc2m51as4.execute-api.us-east-1.amazonaws.com/prod` |
| title (t1) | `wss://hsdpbajz23.execute-api.us-east-1.amazonaws.com/prod` |
| proofreading (p1) | `wss://p062xh167h.execute-api.us-east-1.amazonaws.com/prod` |
| foreign (f1) | `wss://5c6e29dg50.execute-api.us-east-1.amazonaws.com/prod` |
| bodo (w1) | `wss://prsebeg7ub.execute-api.us-east-1.amazonaws.com/prod` |
| regression (r1) | `wss://ebqodb8ax9.execute-api.us-east-1.amazonaws.com/production` |

### REST API (대화 저장, 프롬프트 관리)

| 서비스 | REST API URL |
|--------|--------------|
| buddy (b1) | `https://pisnqqgu75.execute-api.us-east-1.amazonaws.com/prod` |
| title (t1) | `https://qyfams2iva.execute-api.us-east-1.amazonaws.com/prod` |
| proofreading (p1) | `https://wxwdb89w4m.execute-api.us-east-1.amazonaws.com/prod` |
| foreign (f1) | `https://razlubfzw1.execute-api.us-east-1.amazonaws.com/prod` |
| bodo (w1) | `https://16ayefk5lc.execute-api.us-east-1.amazonaws.com/prod` |
| regression (r1) | `https://t75vorhge1.execute-api.us-east-1.amazonaws.com/prod` |

### AWS Cognito (인증 - 공통)

| 리소스 | 값 |
|--------|-----|
| User Pool ID | `us-east-1_ohLOswurY` |
| Client ID | `4m4edj8snokmhqnajhlj41h9n2` |
| Region | `us-east-1` |

## 서비스별 DynamoDB 테이블

### buddy (b1)
- `p2-two-conversations-two` - 대화 히스토리
- `p2-two-prompts-two` - 시스템 프롬프트
- `p2-two-usage-two` - 사용량 추적
- `p2-two-websocket-connections-two` - WebSocket 연결

### title (t1)
- `nx-tt-dev-ver3-conversations` - 대화 히스토리
- `nx-tt-dev-ver3-prompts` - 시스템 프롬프트
- `nx-tt-dev-ver3-usage-tracking` - 사용량 추적
- `nx-tt-dev-ver3-websocket-connections` - WebSocket 연결

### proofreading (p1)
- `nx-wt-prf-conversations` - 대화 히스토리
- `nx-wt-prf-prompts` - 시스템 프롬프트

## 기술 스택

### Frontend
- React 18
- Vite
- Tailwind CSS
- AWS Amplify Auth (Cognito)
- React Router

### Backend (기존 서비스)
- AWS Lambda (Python 3.11)
- AWS API Gateway (REST + WebSocket)
- AWS DynamoDB
- Anthropic Claude API (Opus 4.5)

## 설치 및 실행

### 설치
```bash
cd frontend
npm install
```

### 개발 서버 실행
```bash
npm run dev
```
→ http://localhost:3000

### 빌드
```bash
npm run build
```

## 환경 변수

`frontend/.env` 파일:
```env
VITE_API_BASE_URL=https://pisnqqgu75.execute-api.us-east-1.amazonaws.com/prod
VITE_WS_URL=wss://dwc2m51as4.execute-api.us-east-1.amazonaws.com/prod
VITE_AWS_REGION=us-east-1
VITE_COGNITO_USER_POOL_ID=us-east-1_ohLOswurY
VITE_COGNITO_CLIENT_ID=4m4edj8snokmhqnajhlj41h9n2
VITE_ADMIN_EMAIL=ai@sedaily.com
```

## 백엔드 배포

각 서비스 폴더 내의 배포 스크립트를 사용합니다:

```bash
# 예: buddy 서비스 배포
cd backend/buddy/external/two
./update-buddy-code.sh      # 백엔드 Lambda 배포

# 예: title 서비스 배포
cd backend/title/external/two
./deploy.sh                 # Lambda 배포
```

### 배포 스크립트 목록

| 서비스 | 경로 | 배포 스크립트 |
|--------|------|---------------|
| buddy | `backend/buddy/external/two/` | `update-buddy-code.sh` |
| title | `backend/title/external/two/` | `deploy.sh` |
| proofreading | `backend/proofreading/external/two/` | `deploy.sh` |
| bodo | `backend/bodo/external/two/` | `deploy.sh` |
| foreign | `backend/foreign/external/two/` | `deploy.sh` |
| regression | `backend/regression/external/two/` | `deploy.sh` |

## 라이선스

Proprietary - Seoul Economic Daily
