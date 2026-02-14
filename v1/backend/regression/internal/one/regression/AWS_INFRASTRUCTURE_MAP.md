# SEDAILY COLUMN AWS 인프라 맵

**생성일**: 2025-11-21
**도메인**: r1.sedaily.ai
**목적**: 실제 배포된 AWS 리소스와 스택 정보 정리

---

## 🌐 도메인 및 DNS 구조

### Route 53 Hosted Zone
```
Zone ID: Z07543813V4FC5RK599U0
Domain: sedaily.ai
```

### r1.sedaily.ai DNS 레코드
```yaml
Type: A (Alias)
Target: d3ck0lkvawjvhg.cloudfront.net
Hosted Zone: Z2FDTNDATAQYW2 (CloudFront)
```

**흐름**: `r1.sedaily.ai` → `CloudFront` → `S3 Bucket`

---

## 📦 프론트엔드 인프라

### CloudFront Distribution
```yaml
Distribution ID: EH9OF7IFDTPLW
Domain: d3ck0lkvawjvhg.cloudfront.net
Custom Domain: r1.sedaily.ai
Comment: "SEDAILY Column Service Frontend"
Status: Deployed

Origin:
  ID: S3-sedaily-column-frontend
  Domain: sedaily-column-frontend.s3.us-east-1.amazonaws.com
  Type: S3
```

**배포 스크립트**: `/deploy-column-frontend.sh`

### S3 Bucket
```yaml
Bucket Name: sedaily-column-frontend
Region: us-east-1
Website Hosting: Enabled
  Index Document: index.html
  Error Document: error.html

Files: React SPA Build Output (frontend/dist/)
```

**업로드 명령**:
```bash
aws s3 sync frontend/dist/ s3://sedaily-column-frontend/ --delete
```

**캐시 무효화**:
```bash
aws cloudfront create-invalidation \
  --distribution-id EH9OF7IFDTPLW \
  --paths "/*"
```

---

## ⚙️ 백엔드 API 인프라

### REST API Gateway
```yaml
API Name: sedaily-column-rest-api
API ID: t75vorhge1
Type: REST API
Region: us-east-1

Stage: prod
Deployment ID: dwg7hm
Last Updated: 2025-10-11

Endpoint: https://t75vorhge1.execute-api.us-east-1.amazonaws.com/prod
```

**설정 스크립트**: `backend/scripts/03-setup-api-gateway.sh`

**주요 엔드포인트**:
```
POST   /conversations          # 대화 생성
GET    /conversations          # 대화 목록
GET    /conversations/{id}     # 대화 조회
PUT    /conversations/{id}     # 대화 수정
DELETE /conversations/{id}     # 대화 삭제

POST   /prompts                # 프롬프트 생성
GET    /prompts                # 프롬프트 목록
GET    /prompts/{id}           # 프롬프트 조회
PUT    /prompts/{id}           # 프롬프트 수정
DELETE /prompts/{id}           # 프롬프트 삭제

GET    /usage                  # 사용량 조회
POST   /usage                  # 사용량 기록
```

---

### WebSocket API Gateway
```yaml
API Name: sedaily-column-websocket-api
API ID: ebqodb8ax9
Type: WEBSOCKET
Region: us-east-1
Protocol: WSS

Stage: prod
Deployment ID: ziizwx
Last Updated: 2025-09-21

Endpoint: wss://ebqodb8ax9.execute-api.us-east-1.amazonaws.com/prod
```

**설정 스크립트**: `backend/scripts/04-setup-websocket.sh`

**Routes**:
```
$connect      → sedaily-column-websocket-connect
$disconnect   → sedaily-column-websocket-disconnect
$default      → sedaily-column-websocket-message
sendMessage   → sedaily-column-websocket-message
```

---

## 🔧 Lambda Functions

### 핵심 Lambda (6개) - 05-deploy-lambda.sh로 배포

| 함수명 | 핸들러 | Runtime | 역할 | 크기 | 최근 배포 |
|--------|--------|---------|------|------|-----------|
| sedaily-column-conversation-api | handlers.api.conversation.handler | python3.9 | 대화 CRUD API | 15.5MB | 2025-10-30 |
| sedaily-column-prompt-crud | handlers.api.prompt.handler | python3.9 | 프롬프트 관리 API | 15.5MB | 2025-10-30 |
| sedaily-column-usage-handler | handlers.api.usage.handler | python3.9 | 사용량 추적 API | 15.5MB | 2025-10-30 |
| sedaily-column-websocket-connect | handlers.websocket.connect.handler | python3.9 | WS 연결 처리 | 15.5MB | 2025-10-30 |
| sedaily-column-websocket-disconnect | handlers.websocket.disconnect.handler | python3.9 | WS 연결 해제 | 15.5MB | 2025-10-30 |
| sedaily-column-websocket-message | handlers.websocket.message.handler | python3.9 | WS 메시지 & AI 스트리밍 | 64KB | 2025-11-15 ⭐ |

**배포 명령**:
```bash
cd backend/scripts
./05-deploy-lambda.sh
```

---

### 추가 Lambda (5개) - 별도 스크립트로 배포

| 함수명 | 핸들러 | Runtime | 역할 | 크기 | 배포 스크립트 |
|--------|--------|---------|------|------|---------------|
| sedaily-column-authorizer | handlers.api.authorizer.handler | python3.11 | JWT 인증 | 27KB | deploy-authorizer.sh |
| sedaily-column-admin-dashboard | handlers.api.admin_dashboard.handler | python3.12 | 관리자 대시보드 | 41.9MB | deploy-admin-dashboard.sh |
| sedaily-column-prompt-manager | lambda_function.handler | python3.11 | 프롬프트 관리 (레거시?) | 1KB | - |
| sedaily-column-bigkinds-mcp | fixed_bigkinds_final.lambda_handler | python3.11 | 빅카인즈 MCP 통합 | 3.5KB | - |
| sedaily-column-transcribe | handlers.api.transcribe.lambda_handler | python3.9 | 음성 텍스트 변환 | 81.5KB | setup-transcribe.sh |

**중요**:
- 전체 재배포 시 이 5개 함수는 별도 실행 필요
- `deploy-all-column.sh`에 포함되어 있지 않음

---

## 💾 DynamoDB Tables

### 핵심 테이블 (4개) - 01-setup-dynamodb-column.sh로 생성

| 테이블명 | Partition Key | Sort Key | GSI | 용도 |
|----------|---------------|----------|-----|------|
| sedaily-column-conversations | conversation_id (S) | - | user-index (user_id) | 대화 내역 저장 |
| sedaily-column-prompts | prompt_id (S) | - | user-index (user_id) | 프롬프트 템플릿 |
| sedaily-column-usage | user_id (S) | timestamp (S) | - | 사용량 추적 |
| sedaily-column-websocket-connections | connection_id (S) | - | user-index (user_id) | WebSocket 연결 관리 (TTL: 24h) |

**생성 명령**:
```bash
cd backend/scripts
./01-setup-dynamodb-column.sh
```

---

### 추가 테이블 (4개) - 멀티테넌트 및 파일 관리

| 테이블명 | Partition Key | Sort Key | 용도 | 생성 스크립트 |
|----------|---------------|----------|------|---------------|
| sedaily-column-files | file_id (S) | - | 파일 메타데이터 저장 | create-tenant-tables.sh |
| sedaily-column-messages | message_id (S) | timestamp (S) | 메시지 상세 저장 | create-tenant-tables.sh |
| sedaily-column-tenants | tenant_id (S) | - | 테넌트 정보 | create-tenant-tables.sh |
| sedaily-column-user-tenants | user_id (S) | tenant_id (S) | 사용자-테넌트 매핑 | create-tenant-tables.sh |

**생성 명령**:
```bash
cd backend/scripts
./create-tenant-tables.sh
```

---

## 🔐 인증 및 보안

### AWS Cognito
```yaml
User Pool ID: us-east-1_ohLOswurY
Client ID: 4m4edj8snokmhqnajhlj41h9n2
Region: us-east-1
```

**프론트엔드 설정**: `frontend/.env`
```bash
VITE_COGNITO_USER_POOL_ID=us-east-1_ohLOswurY
VITE_COGNITO_CLIENT_ID=4m4edj8snokmhqnajhlj41h9n2
```

### Lambda Authorizer
```yaml
Function: sedaily-column-authorizer
Handler: handlers.api.authorizer.handler
Purpose: JWT 토큰 검증 및 API Gateway 인증
```

---

## 🔗 환경변수 매핑

### frontend/.env (프론트엔드 설정)
```bash
# API 엔드포인트
VITE_API_BASE_URL=https://t75vorhge1.execute-api.us-east-1.amazonaws.com/prod
VITE_WS_URL=wss://ebqodb8ax9.execute-api.us-east-1.amazonaws.com/prod

# 중복 설정 (정리 권장)
VITE_API_URL=https://t75vorhge1.execute-api.us-east-1.amazonaws.com/prod
VITE_PROMPT_API_URL=https://t75vorhge1.execute-api.us-east-1.amazonaws.com/prod
VITE_WEBSOCKET_URL=wss://ebqodb8ax9.execute-api.us-east-1.amazonaws.com/prod
VITE_USAGE_API_URL=https://t75vorhge1.execute-api.us-east-1.amazonaws.com/prod
VITE_CONVERSATION_API_URL=https://t75vorhge1.execute-api.us-east-1.amazonaws.com/prod

# Cognito
VITE_AWS_REGION=us-east-1
VITE_COGNITO_USER_POOL_ID=us-east-1_ohLOswurY
VITE_COGNITO_CLIENT_ID=4m4edj8snokmhqnajhlj41h9n2

# 기타
VITE_SERVICE_TYPE=column
VITE_USE_MOCK=false
```

---

## 📊 리소스 연결 다이어그램

```
사용자
  ↓
r1.sedaily.ai (Route 53)
  ↓
CloudFront (EH9OF7IFDTPLW)
  ↓
S3 (sedaily-column-frontend)
  ↓ (API 호출)
  ├─→ REST API (t75vorhge1) → Lambda Functions → DynamoDB
  │     ├─ /conversations → sedaily-column-conversation-api
  │     ├─ /prompts       → sedaily-column-prompt-crud
  │     └─ /usage         → sedaily-column-usage-handler
  │
  └─→ WebSocket API (ebqodb8ax9) → Lambda Functions → Bedrock
        ├─ $connect      → sedaily-column-websocket-connect
        ├─ $disconnect   → sedaily-column-websocket-disconnect
        └─ sendMessage   → sedaily-column-websocket-message → Claude Sonnet 4
```

---

## 🚀 배포 시나리오별 명령어

### 1. 프론트엔드만 배포 (가장 빈번)
```bash
# 루트 디렉토리에서 실행
./deploy-column-frontend.sh

# 실행 내용:
# - frontend/ 디렉토리로 이동
# - npm install
# - npm run build
# - S3에 업로드
# - CloudFront 캐시 무효화
```

**대상 리소스**:
- S3: sedaily-column-frontend
- CloudFront: EH9OF7IFDTPLW

---

### 2. 백엔드 핵심 Lambda만 배포
```bash
cd backend/scripts
./05-deploy-lambda.sh

# 배포되는 함수 (6개):
# - sedaily-column-conversation-api
# - sedaily-column-prompt-crud
# - sedaily-column-usage-handler
# - sedaily-column-websocket-message
# - sedaily-column-websocket-connect
# - sedaily-column-websocket-disconnect
```

**주의**:
- authorizer, admin-dashboard는 별도 배포 필요
- 코드 수정 후 가장 자주 사용

---

### 3. 특정 Lambda만 배포 (프롬프트 캐싱 등)
```bash
cd backend
./deploy-prompt-caching.sh

# 대상: sedaily-column-websocket-message만 업데이트
```

---

### 4. 인증 Lambda 배포
```bash
cd backend/scripts
./deploy-authorizer.sh

# 대상: sedaily-column-authorizer
```

---

### 5. 관리자 대시보드 배포
```bash
cd backend/scripts
./deploy-admin-dashboard.sh

# 대상: sedaily-column-admin-dashboard
```

---

### 6. 전체 백엔드 재배포 (신규 환경 구축)
```bash
cd backend/scripts

# 1단계: DynamoDB 테이블 생성
./01-setup-dynamodb-column.sh
./create-tenant-tables.sh  # 멀티테넌트 사용 시

# 2단계: Lambda 함수 및 IAM 생성
./02-create-lambda-functions.sh

# 3단계: API Gateway 설정
./03-setup-api-gateway.sh
./04-setup-websocket.sh

# 4단계: Lambda 코드 배포
./05-deploy-lambda.sh

# 5단계: 추가 Lambda 배포
./deploy-authorizer.sh
./deploy-admin-dashboard.sh

# 또는 1-4단계 한번에:
./deploy-all-column.sh
# (단, 추가 Lambda는 여전히 별도 실행 필요)
```

---

## ⚠️ 주의사항

### 1. 스크립트 위치 혼동 방지
```
✅ 프론트엔드 배포:
   루트/deploy-column-frontend.sh

✅ 백엔드 Lambda 배포:
   backend/scripts/05-deploy-lambda.sh

❌ 사용하지 말 것:
   frontend/scripts/deploy-column-frontend.sh (CloudFront ID 없음)
```

### 2. 환경별 스택 분리 없음
- 현재는 `prod` 스테이지만 존재
- dev, staging 환경이 없음
- **모든 배포가 프로덕션에 직접 반영됨** ⚠️

### 3. Lambda 배포 누락 방지
```bash
# deploy-all-column.sh는 6개 Lambda만 배포
# 추가 5개는 별도 실행 필요:
./deploy-authorizer.sh
./deploy-admin-dashboard.sh
# (bigkinds, transcribe, prompt-manager는 사용 여부 확인 필요)
```

### 4. 멀티테넌트 테이블
- 기본 배포에 포함되지 않음
- 멀티테넌트 기능 사용 시 반드시 별도 실행:
  ```bash
  ./backend/scripts/create-tenant-tables.sh
  ```

---

## 🔍 리소스 확인 명령어

### CloudFront 상태 확인
```bash
aws cloudfront get-distribution --id EH9OF7IFDTPLW \
  --query "Distribution.{Status:Status,DomainName:DomainName,Aliases:Aliases.Items}" \
  --output json
```

### S3 버킷 내용 확인
```bash
aws s3 ls s3://sedaily-column-frontend/ --recursive | head -20
```

### Lambda 함수 목록
```bash
aws lambda list-functions --region us-east-1 \
  --query "Functions[?contains(FunctionName, 'sedaily-column')].{Name:FunctionName,Runtime:Runtime,Modified:LastModified}" \
  --output table
```

### API Gateway 엔드포인트 확인
```bash
# REST API
aws apigateway get-rest-api --rest-api-id t75vorhge1

# WebSocket API
aws apigatewayv2 get-api --api-id ebqodb8ax9
```

### DynamoDB 테이블 목록
```bash
aws dynamodb list-tables --region us-east-1 \
  --output json | jq '.TableNames[] | select(contains("sedaily-column"))'
```

### Route 53 DNS 레코드
```bash
aws route53 list-resource-record-sets \
  --hosted-zone-id Z07543813V4FC5RK599U0 \
  --query "ResourceRecordSets[?contains(Name, 'r1')]" \
  --output json
```

---

## 📝 정리 및 권장사항

### 확인된 사실
1. ✅ **r1.sedaily.ai** → CloudFront (EH9OF7IFDTPLW) → S3 (sedaily-column-frontend)
2. ✅ **스택 이름 일치**: 모든 리소스가 `sedaily-column` prefix 사용
3. ✅ **API 엔드포인트**: frontend/.env와 실제 API ID 일치
4. ✅ **배포 스크립트**: 루트의 `deploy-column-frontend.sh` 사용 (ID 하드코딩 정확)

### 개선 필요사항
1. ⚠️ **Lambda 배포 누락**: 추가 5개 함수가 메인 스크립트에 없음
2. ⚠️ **테이블 생성 누락**: 멀티테넌트 테이블이 deploy-all에 없음
3. ⚠️ **환경 분리 없음**: dev/staging 환경 구축 권장
4. ⚠️ **중복 스크립트**: frontend/scripts/의 배포 스크립트 정리 필요

### 즉시 조치 가능
1. 환경변수 중앙 관리 파일 생성: `config/aws-resources.env`
2. 마스터 배포 스크립트 작성: 모든 Lambda 포함
3. README에 명확한 배포 가이드 추가

---

**생성일**: 2025-11-21
**작성자**: Claude Code
**버전**: 1.0
