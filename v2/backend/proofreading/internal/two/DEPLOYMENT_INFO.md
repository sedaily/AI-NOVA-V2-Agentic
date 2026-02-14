# 🚀 Nexus Proofreading (교열) 배포 정보

> **프로젝트**: p1.sedaily.ai - AI 교열 서비스
> **최종 업데이트**: 2025-11-21
> **AWS 리전**: us-east-1

---

## 📋 프로덕션 스택 정보

### 🎨 프론트엔드

| 항목 | 값 | 설명 |
|------|-----|------|
| **도메인** | https://p1.sedaily.ai | 프로덕션 URL |
| **CloudFront ID** | E39OHKSWZD4F8J | CDN 배포 ID |
| **CloudFront Domain** | d1tas3e2v5373v.cloudfront.net | CDN 엔드포인트 |
| **S3 버킷** | nx-wt-prf-frontend-prod | 정적 파일 스토리지 |
| **빌드 경로** | `frontend/dist/` | 프로덕션 빌드 위치 |

### 🔧 백엔드 - REST API

| 항목 | 값 | 설명 |
|------|-----|------|
| **API ID** | wxwdb89w4m | API Gateway ID |
| **API 이름** | nx-wt-prf-api | API Gateway 이름 |
| **Stage** | prod | 배포 스테이지 |
| **엔드포인트** | https://wxwdb89w4m.execute-api.us-east-1.amazonaws.com/prod | REST API URL |
| **커스텀 도메인** | ❌ 없음 | 직접 엔드포인트 사용 |

### 📡 백엔드 - WebSocket API

| 항목 | 값 | 설명 |
|------|-----|------|
| **API ID** | p062xh167h | WebSocket API ID |
| **API 이름** | nx-wt-prf-websocket-api | WebSocket API 이름 |
| **Stage** | prod | 배포 스테이지 |
| **엔드포인트** | wss://p062xh167h.execute-api.us-east-1.amazonaws.com/prod | WebSocket URL |
| **커스텀 도메인** | ❌ 없음 | 직접 엔드포인트 사용 |

### ⚡ Lambda 함수 (6개)

| 함수명 | 핸들러 | 용도 |
|--------|---------|------|
| nx-wt-prf-conversation-api | handlers.api.conversation.handler | 대화 CRUD |
| nx-wt-prf-prompt-crud | handlers.api.prompt.handler | 프롬프트 관리 |
| nx-wt-prf-usage-handler | handlers.api.usage.handler | 사용량 추적 |
| nx-wt-prf-websocket-connect | handlers.websocket.connect.handler | WebSocket 연결 |
| nx-wt-prf-websocket-disconnect | handlers.websocket.disconnect.handler | WebSocket 해제 |
| nx-wt-prf-websocket-message | handlers.websocket.message.handler | WebSocket 메시지 |

### 🔐 인증 (Cognito)

| 항목 | 값 |
|------|-----|
| **User Pool ID** | us-east-1_ohLOswurY |
| **Client ID** | 4m4edj8snokmhqnajhlj41h9n2 |
| **리전** | us-east-1 |

---

## 🔄 배포 방법

### 1️⃣ 전체 배포 (프론트엔드 + 백엔드)

```bash
./deploy.sh
```

### 2️⃣ 프론트엔드만 배포

```bash
./deploy.sh --frontend
```

**배포 과정**:
1. `frontend/` 빌드 (`npm run build`)
2. `dist/` → S3 업로드 (`nx-wt-prf-frontend-prod`)
3. CloudFront 캐시 무효화 (E39OHKSWZD4F8J)

**예상 시간**: 2-3분

### 3️⃣ 백엔드만 배포

```bash
./deploy.sh --backend
```

**배포 과정**:
1. Lambda 배포 패키지 생성 (`lambda_deploy.zip`)
2. 6개 Lambda 함수 코드 업데이트
3. 함수 활성화 대기

**예상 시간**: 1-2분

### 4️⃣ 캐시 무효화 없이 배포

```bash
./deploy.sh --frontend --no-cache
```

---

## 🔗 Route 53 DNS 설정

```yaml
호스팅 영역: sedaily.ai (Z07543813V4FC5RK599U0)

레코드:
  - 이름: p1.sedaily.ai
  - 타입: A (Alias)
  - 값: d1tas3e2v5373v.cloudfront.net
  - 라우팅: Simple
```

---

## 🌐 프론트엔드 환경 변수

**파일**: `frontend/.env`

```bash
# REST API
VITE_API_BASE_URL=https://wxwdb89w4m.execute-api.us-east-1.amazonaws.com/prod

# WebSocket API
VITE_WS_URL=wss://p062xh167h.execute-api.us-east-1.amazonaws.com/prod

# Cognito
VITE_AWS_REGION=us-east-1
VITE_COGNITO_USER_POOL_ID=us-east-1_ohLOswurY
VITE_COGNITO_CLIENT_ID=4m4edj8snokmhqnajhlj41h9n2
```

---

## 📊 DynamoDB 테이블

| 테이블명 | Partition Key | Sort Key | GSI | 용도 |
|----------|---------------|----------|-----|------|
| nx-wt-prf-conversations | conversationId | - | user-index | 대화 저장 |
| nx-wt-prf-prompts | promptId | - | - | 프롬프트 관리 |
| nx-wt-prf-usage | userId | yearMonth | - | 사용량 추적 |
| nx-wt-prf-websocket-connections | connectionId | - | user-index | WebSocket 연결 관리 |
| nx-wt-prf-files | fileId | - | promptId-index | 파일 첨부 |

---

## 🔍 배포 후 확인 사항

### ✅ 프론트엔드 확인

```bash
# 1. 웹사이트 접속
open https://p1.sedaily.ai

# 2. CloudFront 상태
aws cloudfront get-distribution --id E39OHKSWZD4F8J --query 'Distribution.Status'

# 3. S3 파일 확인
aws s3 ls s3://nx-wt-prf-frontend-prod/
```

### ✅ 백엔드 확인

```bash
# 1. Lambda 함수 상태
aws lambda list-functions --query 'Functions[?contains(FunctionName, `nx-wt-prf`)].{Name:FunctionName,State:State}' --output table

# 2. CloudWatch 로그
aws logs tail /aws/lambda/nx-wt-prf-websocket-message --follow

# 3. API Gateway 테스트
curl https://wxwdb89w4m.execute-api.us-east-1.amazonaws.com/prod/health
```

---

## 🚨 트러블슈팅

### 문제 1: CloudFront 캐시 때문에 변경사항이 반영 안됨

```bash
# 수동 캐시 무효화
aws cloudfront create-invalidation \
  --distribution-id E39OHKSWZD4F8J \
  --paths "/*"
```

### 문제 2: Lambda 함수가 업데이트 안됨

```bash
# 함수 상태 확인
aws lambda get-function --function-name nx-wt-prf-websocket-message

# 강제 재배포
cd backend
./scripts/99-deploy-lambda.sh
```

### 문제 3: CORS 에러

**원인**: API Gateway CORS 설정 문제
**해결**: `backend/scripts/archive/` 참고

---

## 📝 변경 이력

| 날짜 | 변경 내용 | 작성자 |
|------|-----------|--------|
| 2025-11-21 | deploy.sh 배포 정보 수정 (정확한 리소스 ID 반영) | Claude |
| 2025-11-21 | temperature/top_p 충돌 수정 (bedrock_client_enhanced.py) | Claude |
| 2025-09-13 | 프로덕션 스택 최초 배포 | - |

---

## 📞 지원

- **GitHub**: https://github.com/1282saa/sed-nexus-proofreading
- **브랜치**: refactoring-1121
- **CloudWatch 로그**: `/aws/lambda/nx-wt-prf-*`
