# AWS 스택 매핑 - b1.sedaily.ai

> **생성일**: 2025-11-21
> **목적**: b1.sedaily.ai 커스텀 도메인에 연결된 모든 AWS 리소스를 명확하게 파악

---

## 🌐 커스텀 도메인 구조

### 도메인 → CloudFront → S3 흐름
```
b1.sedaily.ai (Route53)
    ↓
CloudFront E2WPOE6AL2G5DZ (dxiownvrignup.cloudfront.net)
    ↓
S3 p2-two-frontend (정적 웹사이트)
```

---

## 📍 1. 도메인 및 DNS (Route53)

### Hosted Zone
- **Zone ID**: `Z07543813V4FC5RK599U0`
- **도메인**: `sedaily.ai`
- **레코드 수**: 40개

### b1.sedaily.ai DNS 레코드
```bash
Type: A (Alias)
Target: dxiownvrignup.cloudfront.net
CloudFront Hosted Zone: Z2FDTNDATAQYW2
```

### SSL 인증서 검증 레코드
```
_07bdec47581f5a7f95f8aeaa273f9cf1.b1.sedaily.ai
  → _92ba48531b42dc96008adfaef51d7152.xlfgrmvvlj.acm-validations.aws.
```

**조회 명령어**:
```bash
aws route53 list-resource-record-sets \
  --hosted-zone-id Z07543813V4FC5RK599U0 \
  --query 'ResourceRecordSets[?contains(Name, `b1`)]'
```

---

## 🌍 2. CDN (CloudFront)

### Distribution 정보
- **Distribution ID**: `E2WPOE6AL2G5DZ`
- **도메인**: `dxiownvrignup.cloudfront.net`
- **커스텀 도메인**: `b1.sedaily.ai`
- **코멘트**: "p2-two frontend"
- **상태**: Deployed ✅

### Origin 설정
- **Origin Domain**: `p2-two-frontend.s3.us-east-1.amazonaws.com`
- **Origin ID**: `S3-p2-two-frontend`

**조회 명령어**:
```bash
aws cloudfront get-distribution \
  --id E2WPOE6AL2G5DZ \
  --query 'Distribution.{Aliases:DistributionConfig.Aliases.Items,Origins:DistributionConfig.Origins.Items[*].DomainName}'
```

---

## 🪣 3. 프론트엔드 호스팅 (S3)

### 버킷 정보
- **버킷명**: `p2-two-frontend`
- **리전**: `us-east-1`
- **용도**: React 앱 정적 파일 호스팅
- **Website 설정**: 없음 (CloudFront로만 접근)

### 배포 스크립트
- **파일**: `deploy-p2-frontend.sh`
- **명령어**: `npm run build` → S3 sync → CloudFront 캐시 무효화

**조회 명령어**:
```bash
aws s3 ls s3://p2-two-frontend/ --region us-east-1
```

---

## 🔌 4. REST API (API Gateway)

### API 정보
- **API ID**: `pisnqqgu75`
- **API 이름**: `p2-two-api`
- **생성일**: 2025-09-26
- **엔드포인트**: `https://pisnqqgu75.execute-api.us-east-1.amazonaws.com/prod`

### REST API 엔드포인트
```
GET    /conversations              # 대화 목록 조회
GET    /conversations/{id}         # 특정 대화 조회
POST   /conversations              # 새 대화 생성
PUT    /conversations/{id}         # 대화 수정
DELETE /conversations/{id}         # 대화 삭제

GET    /prompts                    # 프롬프트 목록 조회
GET    /prompts/{id}               # 특정 프롬프트 조회
POST   /prompts                    # 프롬프트 생성
PUT    /prompts/{id}               # 프롬프트 수정
DELETE /prompts/{id}               # 프롬프트 삭제

GET    /usage/daily                # 일별 사용량
GET    /usage/user/{userId}        # 사용자별 사용량
```

**조회 명령어**:
```bash
aws apigateway get-rest-api \
  --rest-api-id pisnqqgu75 \
  --region us-east-1
```

---

## 🔄 5. WebSocket API (API Gateway v2)

### WebSocket 정보
- **API ID**: `dwc2m51as4`
- **API 이름**: `p2-two-websocket`
- **프로토콜**: WEBSOCKET
- **엔드포인트**: `wss://dwc2m51as4.execute-api.us-east-1.amazonaws.com/prod`

### WebSocket 라우트
```
$connect      → p2-two-websocket-connect-two
$disconnect   → p2-two-websocket-disconnect-two
$default      → p2-two-websocket-message-two
```

**조회 명령어**:
```bash
aws apigatewayv2 get-api \
  --api-id dwc2m51as4 \
  --region us-east-1
```

---

## ⚡ 6. Lambda Functions (Backend)

### 전체 Lambda 함수 목록

| 함수명 | 런타임 | 최종 수정일 | 용도 |
|--------|--------|------------|------|
| `p2-two-websocket-connect-two` | python3.9 | 2025-11-15 | WebSocket 연결 |
| `p2-two-websocket-disconnect-two` | python3.9 | 2025-11-15 | WebSocket 연결 해제 |
| `p2-two-websocket-message-two` | python3.9 | 2025-11-21 | **실시간 대화 처리** |
| `p2-two-conversation-api-two` | python3.9 | 2025-11-21 | 대화 CRUD API |
| `p2-two-prompt-crud-two` | python3.9 | 2025-11-15 | 프롬프트 CRUD |
| `p2-two-usage-handler-two` | python3.9 | 2025-11-15 | 사용량 조회 |

### Lambda 배포 패키지
- **소스**: `backend/` 디렉토리
- **ZIP 파일**: `lambda-deployment.zip` (생성 후 업로드)
- **핸들러 경로**:
  - WebSocket: `handlers.websocket.{connect,disconnect,message}.handler`
  - REST API: `handlers.api.{conversation,prompt,usage}.handler`

**조회 명령어**:
```bash
aws lambda list-functions \
  --region us-east-1 \
  --query 'Functions[?contains(FunctionName, `p2-two`)]'
```

---

## 🗄️ 7. DynamoDB Tables

### 전체 테이블 목록

| 테이블명 | 용도 | Primary Key |
|----------|------|-------------|
| `p2-two-conversations-two` | 대화 메타데이터 | userId (PK), conversationId (SK) |
| `p2-two-messages-two` | 대화 메시지 내역 | conversationId (PK), timestamp (SK) |
| `p2-two-prompts-two` | 프롬프트 템플릿 | userId (PK), promptId (SK) |
| `p2-two-usage-two` | 토큰 사용량 추적 | userId (PK), timestamp (SK) |
| `p2-two-websocket-connections-two` | 활성 WebSocket 연결 | connectionId (PK) |
| `p2-two-files-two` | 파일 메타데이터 | fileId (PK) |

**조회 명령어**:
```bash
aws dynamodb list-tables \
  --region us-east-1 \
  --query 'TableNames[?contains(@, `p2-two`)]'
```

---

## 📊 8. CloudWatch Logs

### Lambda 로그 그룹

| 로그 그룹 | Lambda 함수 | 주요 로그 내용 |
|-----------|-------------|----------------|
| `/aws/lambda/p2-two-websocket-message-two` | WebSocket 메시지 | 실시간 대화, AI 응답, 캐시 히트 |
| `/aws/lambda/p2-two-conversation-api-two` | 대화 API | 대화 CRUD 작업 |
| `/aws/lambda/p2-two-prompt-crud-two` | 프롬프트 API | 프롬프트 관리 |
| `/aws/lambda/p2-two-usage-handler-two` | 사용량 API | 토큰 사용량, 비용 |
| `/aws/lambda/p2-two-websocket-connect-two` | WebSocket 연결 | 연결 생성 |
| `/aws/lambda/p2-two-websocket-disconnect-two` | WebSocket 연결 해제 | 연결 종료 |

**조회 명령어**:
```bash
aws logs tail /aws/lambda/p2-two-websocket-message-two \
  --region us-east-1 \
  --since 1h \
  --follow
```

상세 가이드: [CLOUDWATCH_LOGS_GUIDE.md](./CLOUDWATCH_LOGS_GUIDE.md)

---

## 🔐 9. 환경 변수 설정

### Backend (.env)
```bash
# DynamoDB
CONVERSATIONS_TABLE=p2-two-conversations-two
MESSAGES_TABLE=p2-two-messages-two
PROMPTS_TABLE=p2-two-prompts-two
USAGE_TABLE=p2-two-usage-two
CONNECTIONS_TABLE=p2-two-websocket-connections-two
FILES_TABLE=p2-two-files-two

# API Gateway
REST_API_URL=https://pisnqqgu75.execute-api.us-east-1.amazonaws.com/prod
WEBSOCKET_API_ID=dwc2m51as4

# AWS
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=533267403867
```

### Frontend (.env.production)
```bash
VITE_API_BASE_URL=https://pisnqqgu75.execute-api.us-east-1.amazonaws.com/prod
VITE_WEBSOCKET_URL=wss://dwc2m51as4.execute-api.us-east-1.amazonaws.com/prod
```

---

## 🚀 10. 배포 스크립트 정리

### ✅ 안전한 배포 스크립트

#### 프론트엔드만 배포 (권장)
```bash
./deploy-p2-frontend.sh
```
- **대상**: S3 `p2-two-frontend`
- **CloudFront**: E2WPOE6AL2G5DZ 캐시 무효화
- **안전성**: ✅ 백엔드 미영향

#### 백엔드 Lambda만 업데이트 (권장)
```bash
# 개별 Lambda 함수 업데이트
cd backend
zip -r lambda-deployment.zip . -x "*.pyc" -x "__pycache__/*" -x "backup_*/*"

# WebSocket 메시지 핸들러 업데이트
aws lambda update-function-code \
  --function-name p2-two-websocket-message-two \
  --zip-file fileb://lambda-deployment.zip \
  --region us-east-1

# 대화 API 업데이트
aws lambda update-function-code \
  --function-name p2-two-conversation-api-two \
  --zip-file fileb://lambda-deployment.zip \
  --region us-east-1
```

### ⚠️ 주의: 사용하면 안 되는 스크립트

#### deploy-service.sh (위험)
```bash
# ❌ 이 스크립트는 사용하지 마세요!
# 새로운 스택을 생성하므로 기존 p2-two 스택과 충돌
./deploy-service.sh p3 1  # ← 새 스택 생성됨
```

**문제점**:
- 기존 `p2-two` 스택을 업데이트하는 것이 아니라 **새 스택을 생성**
- DynamoDB, Lambda, API Gateway 모두 새로 생성
- 기존 데이터와 연결이 끊김

#### scripts/ (레거시, 삭제 예정)
```bash
# ❌ 레거시 스크립트, 사용 금지
scripts/01-create-dynamodb.sh
scripts/02-create-lambda-functions.sh
...
```

**이유**:
- `scripts-v2/`로 개선되었으나, 여전히 새 스택 생성 방식
- p2-two 업데이트용으로는 부적합

---

## 📋 11. 스택 네이밍 규칙

### 현재 스택 (Production)
- **스택 접두사**: `p2-two`
- **인스턴스 번호**: `two` (2번째 버전)
- **도메인**: `b1.sedaily.ai`

### 네이밍 패턴
```
{service}-{version}-{resource}-{instance}

예시:
- p2-two-websocket-message-two
- p2-two-conversations-two
- p2-two-frontend
```

### 기타 도메인/스택 (참고)
- **w1.sedaily.ai**: 다른 스택 (확인 필요)
- **m1.sedaily.ai**: 다른 스택 (확인 필요)
- **f1.sedaily.ai**: 다른 스택 (확인 필요)

---

## 🔍 12. 리소스 조회 체크리스트

### 전체 p2-two 리소스 확인
```bash
# 1. CloudFront
aws cloudfront list-distributions \
  --query 'DistributionList.Items[?contains(Aliases.Items[0] || ``, `b1.sedaily.ai`)]'

# 2. S3
aws s3 ls | grep p2-two

# 3. Lambda
aws lambda list-functions --region us-east-1 \
  --query 'Functions[?contains(FunctionName, `p2-two`)].[FunctionName,Runtime]' \
  --output table

# 4. API Gateway (REST)
aws apigateway get-rest-apis --region us-east-1 \
  --query 'items[?contains(name, `p2-two`)]'

# 5. API Gateway (WebSocket)
aws apigatewayv2 get-apis --region us-east-1 \
  --query 'Items[?contains(Name, `p2-two`)]'

# 6. DynamoDB
aws dynamodb list-tables --region us-east-1 \
  --query 'TableNames[?contains(@, `p2-two`)]'

# 7. Route53
aws route53 list-resource-record-sets \
  --hosted-zone-id Z07543813V4FC5RK599U0 \
  --query 'ResourceRecordSets[?contains(Name, `b1`)]'
```

---

## 📌 13. 주요 확인 사항

### ✅ 현재 확인된 사항
1. **도메인**: b1.sedaily.ai → CloudFront E2WPOE6AL2G5DZ ✅
2. **CloudFront**: E2WPOE6AL2G5DZ → S3 p2-two-frontend ✅
3. **Lambda 함수**: 6개 모두 존재 ✅
4. **DynamoDB 테이블**: 6개 모두 존재 ✅
5. **API Gateway**: REST (pisnqqgu75), WebSocket (dwc2m51as4) ✅
6. **코드 설정**: .env 파일과 AWS 리소스 일치 ✅

### ⚠️ 개선 필요 사항
1. **배포 스크립트**: 기존 스택 업데이트용 스크립트 필요
2. **백업 파일**: ~16MB 정리 필요 (PROJECT_STRUCTURE_ANALYSIS.md 참고)
3. **.gitignore**: 백업 파일 추적 방지 설정 필요
4. **문서화**: API 명세(OpenAPI/Swagger) 추가 권장
5. **테스트**: 자동화된 테스트 코드 부재

---

## 🎯 요약

### b1.sedaily.ai 연결된 AWS 스택 전체 구조
```
┌─────────────────────────────────────────────────────────┐
│                    b1.sedaily.ai                        │
│                   (Route53 A Record)                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│          CloudFront E2WPOE6AL2G5DZ                      │
│       (dxiownvrignup.cloudfront.net)                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              S3 p2-two-frontend                         │
│           (React App Static Files)                      │
└─────────────────────────────────────────────────────────┘

              Frontend ↕ Backend

┌─────────────────────────────────────────────────────────┐
│         REST API: pisnqqgu75 (대화/프롬프트/사용량)        │
│      WebSocket: dwc2m51as4 (실시간 대화)                │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Lambda Functions (6개)                     │
│  - websocket-connect, disconnect, message               │
│  - conversation-api, prompt-crud, usage-handler         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│           DynamoDB Tables (6개)                         │
│  conversations, messages, prompts, usage,               │
│  websocket-connections, files                           │
└─────────────────────────────────────────────────────────┘
```

### 핵심 리소스 ID
- **도메인**: b1.sedaily.ai
- **CloudFront**: E2WPOE6AL2G5DZ
- **S3**: p2-two-frontend
- **REST API**: pisnqqgu75
- **WebSocket**: dwc2m51as4
- **Lambda**: p2-two-*-two (6개)
- **DynamoDB**: p2-two-*-two (6개)
- **리전**: us-east-1
- **스택 이름**: p2-two (버전: two)

---

**문서 버전**: 1.0
**최종 업데이트**: 2025-11-21
**관련 문서**:
- [CLOUDWATCH_LOGS_GUIDE.md](./CLOUDWATCH_LOGS_GUIDE.md)
- [PROJECT_STRUCTURE_ANALYSIS.md](./PROJECT_STRUCTURE_ANALYSIS.md)
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
