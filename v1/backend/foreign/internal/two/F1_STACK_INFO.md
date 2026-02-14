# 🏗️ f1.sedaily.ai (f1-two) 스택 정보

> **업데이트**: 2025-11-21
> **도메인**: https://f1.sedaily.ai
> **스택명**: f1-two
> **리전**: us-east-1

---

## 📋 리소스 매핑

### 🌐 프론트엔드
```yaml
도메인: f1.sedaily.ai
CloudFront:
  ID: E196O1FYMHCBWL
  도메인: d35j0v9a2xhzgj.cloudfront.net
  상태: Deployed
S3 버킷: f1-two-frontend
Route53: f1.sedaily.ai → CloudFront (A 레코드, Alias)
```

### ⚡ API Gateway
```yaml
REST API:
  ID: razlubfzw1
  이름: f1-rest-api-two
  엔드포인트: https://razlubfzw1.execute-api.us-east-1.amazonaws.com/prod

WebSocket API:
  ID: 5c6e29dg50
  이름: f1-websocket-api-two
  엔드포인트: wss://5c6e29dg50.execute-api.us-east-1.amazonaws.com/prod
```

### 🔧 Lambda 함수 (6개)
```yaml
REST API Lambda:
  - f1-conversation-api-two    # 대화 CRUD
  - f1-prompt-crud-two          # 프롬프트 관리
  - f1-usage-handler-two        # 사용량 추적

WebSocket Lambda:
  - f1-websocket-connect-two    # 연결
  - f1-websocket-disconnect-two # 연결 해제
  - f1-websocket-message-two    # 메시지 처리

환경변수:
  SERVICE_NAME: f1
  CARD_COUNT: two
  ENABLE_NEWS_SEARCH: true
```

### 🗄️ DynamoDB 테이블 (6개)
```yaml
- f1-conversations-two         # 대화 저장
- f1-files-two                 # 파일 첨부
- f1-messages-two              # 메시지 (사용 여부 확인 필요)
- f1-prompts-two               # 시스템 프롬프트
- f1-usage-two                 # 사용량 추적
- f1-websocket-connections-two # WebSocket 연결
```

### 🔐 인증
```yaml
Cognito:
  User Pool ID: us-east-1_ohLOswurY
  Client ID: 4m4edj8snokmhqnajhlj41h9n2
  리전: us-east-1
```

---

## 🚀 배포 명령어

### 프론트엔드만 배포 (권장)
```bash
./deploy-f1-frontend.sh
```
**수행 작업**:
1. `frontend/` 빌드 (npm run build)
2. S3 업로드 (f1-two-frontend)
3. CloudFront 캐시 무효화 (E196O1FYMHCBWL)

**소요 시간**: 약 2-3분

---

### 백엔드만 배포 (Lambda 코드 업데이트)
```bash
./deploy-f1-backend.sh
```
**수행 작업**:
1. `backend/extracted/` ZIP 압축
2. 6개 Lambda 함수 코드 업데이트

**소요 시간**: 약 1-2분

---

## 📁 프로젝트 구조

```
nexus-template-v2/
├── .api-ids                   # API Gateway ID 저장 (수정됨 ✅)
├── deploy-f1-frontend.sh      # 프론트엔드 배포 (수정됨 ✅)
├── deploy-f1-backend.sh       # 백엔드 배포 (신규 ✅)
│
├── frontend/
│   ├── .env                   # 개발 환경변수
│   ├── .env.production        # 프로덕션 환경변수
│   ├── dist/                  # 빌드 결과물 → S3 업로드
│   └── deployment-info.txt    # 배포 정보
│
└── backend/
    ├── .env                   # Lambda 환경변수
    ├── extracted/             # 소스 코드
    │   ├── handlers/         # Lambda 핸들러
    │   ├── lib/              # Bedrock 클라이언트
    │   ├── services/         # 비즈니스 로직
    │   └── src/              # 도메인 계층
    └── lambda-deployment.zip  # 배포 패키지
```

---

## 🔑 주요 설정 파일

### `.api-ids`
```bash
# f1-two Stack API Gateway IDs
export REST_API_ID=razlubfzw1
export WS_API_ID=5c6e29dg50
```

### `frontend/.env`
```bash
VITE_API_BASE_URL=https://razlubfzw1.execute-api.us-east-1.amazonaws.com/prod
VITE_WS_URL=wss://5c6e29dg50.execute-api.us-east-1.amazonaws.com/prod
VITE_COGNITO_USER_POOL_ID=us-east-1_ohLOswurY
VITE_COGNITO_CLIENT_ID=4m4edj8snokmhqnajhlj41h9n2
VITE_ADMIN_EMAIL=ai@sedaily.com
```

### `backend/.env`
```bash
CONVERSATIONS_TABLE=f1-conversations-two
PROMPTS_TABLE=f1-prompts-two
USAGE_TABLE=f1-usage-two
WEBSOCKET_TABLE=f1-websocket-connections-two
FILES_TABLE=f1-files-two
MESSAGES_TABLE=f1-messages-two

REST_API_URL=https://razlubfzw1.execute-api.us-east-1.amazonaws.com/prod
WEBSOCKET_API_URL=wss://5c6e29dg50.execute-api.us-east-1.amazonaws.com/prod
```

---

## ⚠️ 주의사항

### ❌ 사용하지 마세요
- `scripts/` - 이전 w1, b1 스택용
- `scripts-v2/` - 전체 인프라 생성용 (이미 배포됨)

### ✅ 사용하세요
- `deploy-f1-frontend.sh` - 프론트엔드 업데이트
- `deploy-f1-backend.sh` - Lambda 코드 업데이트

---

## 🔍 배포 확인

### 프론트엔드 확인
```bash
# CloudFront 배포 상태
aws cloudfront get-distribution --id E196O1FYMHCBWL --query 'Distribution.Status'

# S3 최신 파일
aws s3 ls s3://f1-two-frontend/ --recursive --human-readable | tail -5
```

### Lambda 확인
```bash
# Lambda 최종 업데이트 시간
aws lambda get-function --function-name f1-conversation-api-two \
  --query 'Configuration.LastModified'

# Lambda 환경변수 확인
aws lambda get-function --function-name f1-conversation-api-two \
  --query 'Configuration.Environment.Variables'
```

### DynamoDB 확인
```bash
# 테이블 존재 확인
aws dynamodb describe-table --table-name f1-conversations-two \
  --query 'Table.TableStatus'
```

---

## 📊 비용 정보

### 현재 사용 중인 리소스
- CloudFront: 1개 (E196O1FYMHCBWL)
- S3: 1개 (f1-two-frontend)
- API Gateway: 2개 (REST + WebSocket)
- Lambda: 6개
- DynamoDB: 6개 테이블
- Cognito: 1개 User Pool

### 불필요한 리소스 (정리 권장)
- CloudFront: 8개 추가 배포 존재
- Lambda: 16개 미사용 함수
- API Gateway: 4개 미사용 API

**예상 절감 비용**: 월 $50-100

---

## 🆘 문제 해결

### 프론트엔드가 업데이트되지 않음
1. CloudFront 캐시 무효화 확인
   ```bash
   aws cloudfront list-invalidations --distribution-id E196O1FYMHCBWL
   ```
2. 브라우저 캐시 강제 새로고침 (Ctrl+Shift+R)

### Lambda 업데이트 후 500 에러
1. Lambda 로그 확인
   ```bash
   aws logs tail /aws/lambda/f1-conversation-api-two --follow
   ```
2. 환경변수 확인
3. 배포 패키지 크기 확인 (50MB 이하)

### API 연결 오류
1. API Gateway ID 확인
2. `.api-ids` 파일 내용 확인
3. `frontend/.env` 설정 확인

---

## 📞 연락처

문제 발생 시:
- AWS 계정 ID: 887078546492
- 리전: us-east-1
- 스택명: f1-two
- 도메인: f1.sedaily.ai
