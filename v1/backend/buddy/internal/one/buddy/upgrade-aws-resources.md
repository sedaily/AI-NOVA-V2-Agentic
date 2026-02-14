# 🚀 B1.SEDAILY.AI AWS 리소스 및 배포 가이드

> 최종 업데이트: 2024-12-14
> 서비스 도메인: b1.sedaily.ai

## 📋 목차

1. [AWS 리소스 구성](#aws-리소스-구성)
2. [배포 프로세스](#배포-프로세스)
3. [업그레이드 절차](#업그레이드-절차)
4. [트러블슈팅](#트러블슈팅)

---

## 🏗️ AWS 리소스 구성

### 1. Lambda Functions (6개)

모든 Lambda 함수는 `p2-two-*-two` 패턴을 따릅니다:

| 함수명                            | 용도                  | 런타임     |
| --------------------------------- | --------------------- | ---------- |
| `p2-two-websocket-message-two`    | WebSocket 메시지 처리 | Python 3.9 |
| `p2-two-websocket-connect-two`    | WebSocket 연결 처리   | Python 3.9 |
| `p2-two-websocket-disconnect-two` | WebSocket 연결 해제   | Python 3.9 |
| `p2-two-conversation-api-two`     | 대화 REST API         | Python 3.9 |
| `p2-two-prompt-crud-two`          | 프롬프트 CRUD         | Python 3.9 |
| `p2-two-usage-handler-two`        | 사용량 추적           | Python 3.9 |

### 2. DynamoDB Tables (6개)

| 테이블명                           | 용도                | 주요 키                           |
| ---------------------------------- | ------------------- | --------------------------------- |
| `p2-two-conversations-two`         | 대화 내역 저장      | PK: userId, SK: conversationId    |
| `p2-two-messages-two`              | 메시지 저장         | PK: conversationId, SK: timestamp |
| `p2-two-prompts-two`               | 프롬프트 관리       | PK: engineType                    |
| `p2-two-files-two`                 | 파일 메타데이터     | PK: fileId                        |
| `p2-two-usage-two`                 | 사용량 추적         | PK: userId, SK: date              |
| `p2-two-websocket-connections-two` | WebSocket 연결 관리 | PK: connectionId                  |

### 3. API Gateway

#### WebSocket API

- **API ID**: `dwc2m51as4`
- **Endpoint**: `wss://dwc2m51as4.execute-api.us-east-1.amazonaws.com/prod`
- **Stage**: prod

#### REST API

- **API ID**: `pisnqqgu75`
- **Endpoint**: `https://pisnqqgu75.execute-api.us-east-1.amazonaws.com/prod`
- **Stage**: prod

### 4. CloudFront & S3

#### CloudFront Distribution

- **Distribution ID**: `E2WPOE6AL2G5DZ`
- **Domain**: `b1.sedaily.ai`
- **Origin**: `p2-two-frontend.s3.us-east-1.amazonaws.com`

#### S3 Buckets

- **Frontend**: `p2-two-frontend` (프론트엔드 정적 파일)
- **Legacy**: `b1.sedaily.ai` (사용 안함, 레거시)

### 5. Secrets Manager

- **Secret Name**: `buddy-v1`
- **내용**: Anthropic API Key
- **Region**: us-east-1

---

## 🚀 배포 프로세스

### 1. 백엔드 Lambda 코드 배포

#### 기본 배포 스크립트 (권장)

```bash
# 모든 Lambda 함수 업데이트
./update-buddy-code.sh
```

#### 스크립트 동작

1. Python 의존성 설치 (`backend/package/` 디렉토리)
2. 소스 코드 패키징 (`lambda-deployment.zip`)
3. 6개 Lambda 함수 순차 업데이트
4. 환경 변수 설정

### 2. 환경 변수 설정

현재 설정된 주요 환경 변수:

```json
{
  "ANTHROPIC_SECRET_NAME": "buddy-v1",
  "USE_ANTHROPIC_API": "true",
  "USE_OPUS_MODEL": "true",
  "ANTHROPIC_MODEL_ID": "claude-opus-4-5-20251101",
  "SERVICE_NAME": "buddy",
  "AI_PROVIDER": "anthropic_api",
  "MAX_TOKENS": "4096",
  "TEMPERATURE": "0.3",
  "FALLBACK_TO_BEDROCK": "true",
  "ENABLE_NATIVE_WEB_SEARCH": "true",
  "PROMPTS_TABLE": "p2-two-prompts-two",
  "FILES_TABLE": "p2-two-files-two",
  "CONVERSATIONS_TABLE": "p2-two-conversations-two"
}
```

### 3. 프론트엔드 배포

```bash
# 프론트엔드 빌드 및 S3 업로드
./deploy-p2-frontend.sh
```

---

## 🔄 업그레이드 절차

### upgrade-01: 코드 수정 및 배포

```bash
# 1. 코드 수정
vim backend/lib/anthropic_client.py  # 또는 수정할 파일

# 2. 로컬 테스트
python3 test-api-direct.py
python3 test-web-search.py

# 3. Lambda 배포
./update-buddy-code.sh

# 4. 배포 확인 (30초 대기)
sleep 30

# 5. 실제 서비스 테스트
curl -X POST https://pisnqqgu75.execute-api.us-east-1.amazonaws.com/prod/conversations
```

### upgrade-02: 환경 변수만 업데이트

```bash
# update-buddy-code.sh 파일 수정
vim update-buddy-code.sh

# ENVIRONMENT_VARS 섹션 수정 후
./update-buddy-code.sh

# 또는 AWS CLI 직접 사용
aws lambda update-function-configuration \
    --function-name p2-two-websocket-message-two \
    --environment "Variables={KEY=value}" \
    --region us-east-1
```

### upgrade-03: 새로운 기능 추가

1. **백엔드 코드 작성**

   ```bash
   # 새 모듈 추가
   vim backend/lib/new_feature.py
   ```

2. **테스트 코드 작성**

   ```bash
   vim test-new-feature.py
   python3 test-new-feature.py
   ```

3. **배포**

   ```bash
   ./update-buddy-code.sh
   ```

4. **모니터링**
   ```bash
   # CloudWatch Logs 확인
   aws logs tail /aws/lambda/p2-two-websocket-message-two --follow
   ```

### upgrade-04: DynamoDB 스키마 변경

```bash
# GSI 추가 예시
aws dynamodb update-table \
    --table-name p2-two-conversations-two \
    --attribute-definitions \
        AttributeName=userId,AttributeType=S \
    --global-secondary-index-updates \
        '[{"Create":{"IndexName":"userId-index","Keys":[{"AttributeName":"userId","KeyType":"HASH"}],"Projection":{"ProjectionType":"ALL"}}}]' \
    --region us-east-1
```

### upgrade-05: API Gateway 라우트 추가

```bash
# REST API 라우트 추가
aws apigateway put-method \
    --rest-api-id pisnqqgu75 \
    --resource-id RESOURCE_ID \
    --http-method POST \
    --authorization-type NONE \
    --region us-east-1

# WebSocket 라우트 추가
aws apigatewayv2 create-route \
    --api-id dwc2m51as4 \
    --route-key 'newAction' \
    --target 'integrations/INTEGRATION_ID' \
    --region us-east-1
```

---

## 🔧 트러블슈팅

### 문제 1: Lambda 배포 실패

```bash
# 로그 확인
aws logs tail /aws/lambda/p2-two-websocket-message-two --follow

# 함수 상태 확인
aws lambda get-function --function-name p2-two-websocket-message-two
```

### 문제 2: WebSocket 연결 실패

```bash
# WebSocket 연결 테스트
wscat -c wss://dwc2m51as4.execute-api.us-east-1.amazonaws.com/prod

# API Gateway 로그 확인
aws logs tail /aws/apigateway/dwc2m51as4 --follow
```

### 문제 3: DynamoDB 오류

```bash
# 테이블 상태 확인
aws dynamodb describe-table --table-name p2-two-conversations-two

# 항목 조회
aws dynamodb scan --table-name p2-two-conversations-two --limit 1
```

### 문제 4: CloudFront 캐시 문제

```bash
# 캐시 무효화
aws cloudfront create-invalidation \
    --distribution-id E2WPOE6AL2G5DZ \
    --paths "/*"
```

---

## 📝 주의사항

### ⚠️ 사용하면 안되는 스크립트

- ❌ `deploy-buddy-v1.sh` - 잘못된 Lambda 함수명 사용
- ❌ `deprecated-scripts/` 디렉토리의 모든 스크립트

### ✅ 사용해야 하는 스크립트

- ✅ `update-buddy-code.sh` - 메인 배포 스크립트
- ✅ `deploy-p2-frontend.sh` - 프론트엔드 배포
- ✅ `scripts-v2/` 디렉토리의 스크립트들

### 🔐 보안 주의사항

1. API 키는 절대 코드에 하드코딩하지 않음
2. Secrets Manager 사용 (`buddy-v1`)
3. IAM 역할 최소 권한 원칙 적용

---

## 📊 모니터링

### CloudWatch Dashboards

- Lambda 함수 실행 메트릭
- API Gateway 요청 수
- DynamoDB 읽기/쓰기 용량
- 오류율 모니터링

### 로그 그룹

- `/aws/lambda/p2-two-websocket-message-two`
- `/aws/lambda/p2-two-conversation-api-two`
- `/aws/apigateway/dwc2m51as4` (WebSocket)
- `/aws/apigateway/pisnqqgu75` (REST)

---

## 🔄 백업 및 복구

### DynamoDB 백업

```bash
# 온디맨드 백업 생성
aws dynamodb create-backup \
    --table-name p2-two-conversations-two \
    --backup-name "backup-$(date +%Y%m%d-%H%M%S)"
```

### Lambda 함수 버전 관리

```bash
# 새 버전 발행
aws lambda publish-version \
    --function-name p2-two-websocket-message-two \
    --description "Version before major update"
```

---

## 📞 문의

- 서비스: b1.sedaily.ai
- Region: us-east-1
- 마지막 업데이트: 2024-12-14
