# API 배포 가이드

## 📋 개요

sedaily-column REST API 배포 및 관리 가이드입니다. AWS Lambda + API Gateway 서버리스 아키텍처를 사용합니다.

## 🏗️ 아키텍처

### 서비스 구성

```
Frontend (React/Next.js)
    ↓
API Gateway (REST API)
    ↓
Lambda Functions
    ↓
DynamoDB Tables
```

### AWS 리소스

- **API Gateway**: REST API 엔드포인트 관리
- **Lambda Functions**: 비즈니스 로직 처리
- **DynamoDB**: 데이터 저장소
- **CloudWatch**: 로깅 및 모니터링

## 🌐 API Gateway 설정

### 기본 정보

```yaml
API ID: t75vorhge1
Region: us-east-1
Stage: prod
Base URL: https://t75vorhge1.execute-api.us-east-1.amazonaws.com/prod
```

### 스테이지 관리

```bash
# 개발 스테이지 생성
aws apigateway create-stage \
  --rest-api-id t75vorhge1 \
  --stage-name dev \
  --deployment-id <deployment-id> \
  --region us-east-1

# 스테이징 스테이지 생성
aws apigateway create-stage \
  --rest-api-id t75vorhge1 \
  --stage-name staging \
  --deployment-id <deployment-id> \
  --region us-east-1

# 프로덕션 배포
aws apigateway create-deployment \
  --rest-api-id t75vorhge1 \
  --stage-name prod \
  --region us-east-1
```

### 환경별 URL

- **개발**: `https://t75vorhge1.execute-api.us-east-1.amazonaws.com/dev`
- **스테이징**: `https://t75vorhge1.execute-api.us-east-1.amazonaws.com/staging`
- **프로덕션**: `https://t75vorhge1.execute-api.us-east-1.amazonaws.com/prod`

## 🛣️ API 라우트 구조

### 1. 프롬프트 관리 (`/prompts`)

#### 기본 프롬프트 작업

```http
GET    /prompts                    # 모든 프롬프트 조회
POST   /prompts                    # 프롬프트 생성
GET    /prompts/{promptId}         # 특정 프롬프트 조회
PUT    /prompts/{promptId}         # 프롬프트 업데이트
DELETE /prompts/{promptId}         # 프롬프트 삭제
```

#### 파일 관리

```http
GET    /prompts/{promptId}/files           # 파일 목록 조회
POST   /prompts/{promptId}/files           # 파일 생성
GET    /prompts/{promptId}/files/{fileId}  # 파일 조회
PUT    /prompts/{promptId}/files/{fileId}  # 파일 수정
DELETE /prompts/{promptId}/files/{fileId}  # 파일 삭제
```

### 2. 대화 관리 (`/conversations`)

```http
GET    /conversations                      # 대화 목록 조회
POST   /conversations                      # 대화 생성/저장
GET    /conversations/{conversationId}     # 특정 대화 조회
PATCH  /conversations/{conversationId}     # 대화 제목 수정
DELETE /conversations/{conversationId}     # 대화 삭제
```

### 3. 사용량 추적 (`/usage`)

```http
GET    /usage/{userId}/{engineType}       # 특정 엔진 사용량 조회
GET    /usage/{userId}/all                # 전체 사용량 조회
POST   /usage                             # 사용량 업데이트
```

## 🔧 Lambda 함수 설정

### 함수 목록

```yaml
Functions:
  - Name: sedaily-column-prompt-crud
    Handler: handlers/api/prompt.handler
    Runtime: python3.9
    Timeout: 30s
    Memory: 512MB

  - Name: sedaily-column-conversation-api
    Handler: handlers/api/conversation.handler
    Runtime: python3.9
    Timeout: 30s
    Memory: 512MB

  - Name: sedaily-column-usage-handler
    Handler: handlers/api/usage.handler
    Runtime: python3.9
    Timeout: 30s
    Memory: 256MB

  - Name: sedaily-column-authorizer
    Handler: handlers/api/authorizer.handler
    Runtime: python3.9
    Timeout: 10s
    Memory: 256MB
```

### 환경 변수

```bash
# 공통 환경 변수
AWS_REGION=us-east-1
STAGE=prod

# 테이블 이름
PROMPTS_TABLE=sedaily-column-prompts
FILES_TABLE=sedaily-column-files
CONVERSATIONS_TABLE=sedaily-column-conversations
USAGE_TABLE=sedaily-column-usage

# 멀티테넌트 설정
DEFAULT_TENANT_ID=sedaily
JWT_SECRET_KEY=<your-jwt-secret>
```

## 🗄️ DynamoDB 테이블

### 테이블 구조

```yaml
Tables:
  sedaily-column-prompts:
    PartitionKey: promptId (String)
    Attributes:
      - description (String)
      - instruction (String)
      - createdAt (String)
      - updatedAt (String)

  sedaily-column-files:
    PartitionKey: promptId (String)
    SortKey: fileId (String)
    Attributes:
      - fileName (String)
      - fileContent (String)
      - createdAt (String)
      - updatedAt (String)

  sedaily-column-conversations:
    PartitionKey: conversationId (String)
    GSI1: userId-createdAt-index
    Attributes:
      - userId (String)
      - engineType (String)
      - title (String)
      - messages (List)
      - createdAt (String)
      - updatedAt (String)

  sedaily-column-usage:
    PartitionKey: PK (String) # user#{userId}
    SortKey: SK (String) # engine#{engineType}#{yearMonth}
    Attributes:
      - userId (String)
      - engineType (String)
      - yearMonth (String)
      - totalTokens (Number)
      - inputTokens (Number)
      - outputTokens (Number)
      - messageCount (Number)
```

## 🚀 배포 스크립트

### 1. 전체 배포 스크립트

```bash
#!/bin/bash
# deploy.sh

set -e

STAGE=${1:-prod}
REGION=${2:-us-east-1}
API_ID="t75vorhge1"

echo "=== Deploying sedaily-column API to $STAGE ==="

# Lambda 함수 배포
echo "📦 Deploying Lambda functions..."
./deploy-lambdas.sh $STAGE $REGION

# API Gateway 라우트 설정
echo "🛣️ Setting up API routes..."
./setup-api-routes.sh

# API 배포
echo "🚀 Deploying API..."
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name $STAGE \
  --region $REGION

echo "✅ Deployment complete!"
echo "API URL: https://$API_ID.execute-api.$REGION.amazonaws.com/$STAGE"
```

### 2. Lambda 배포 스크립트

```bash
#!/bin/bash
# deploy-lambdas.sh

STAGE=${1:-prod}
REGION=${2:-us-east-1}

FUNCTIONS=(
  "sedaily-column-prompt-crud"
  "sedaily-column-conversation-api"
  "sedaily-column-usage-handler"
  "sedaily-column-authorizer"
)

for FUNCTION in "${FUNCTIONS[@]}"; do
  echo "Deploying $FUNCTION..."

  # 패키지 생성
  zip -r $FUNCTION.zip handlers/ src/ utils/ requirements.txt

  # Lambda 함수 업데이트
  aws lambda update-function-code \
    --function-name $FUNCTION \
    --zip-file fileb://$FUNCTION.zip \
    --region $REGION

  # 환경 변수 업데이트
  aws lambda update-function-configuration \
    --function-name $FUNCTION \
    --environment Variables="{
      AWS_REGION=$REGION,
      STAGE=$STAGE,
      PROMPTS_TABLE=sedaily-column-prompts,
      FILES_TABLE=sedaily-column-files,
      CONVERSATIONS_TABLE=sedaily-column-conversations,
      USAGE_TABLE=sedaily-column-usage
    }" \
    --region $REGION

  rm $FUNCTION.zip
  echo "✅ $FUNCTION deployed"
done
```

### 3. 테이블 생성 스크립트

```bash
#!/bin/bash
# create-tables.sh

REGION=${1:-us-east-1}

echo "Creating DynamoDB tables..."

# Prompts 테이블
aws dynamodb create-table \
  --table-name sedaily-column-prompts \
  --attribute-definitions \
    AttributeName=promptId,AttributeType=S \
  --key-schema \
    AttributeName=promptId,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region $REGION

# Files 테이블
aws dynamodb create-table \
  --table-name sedaily-column-files \
  --attribute-definitions \
    AttributeName=promptId,AttributeType=S \
    AttributeName=fileId,AttributeType=S \
  --key-schema \
    AttributeName=promptId,KeyType=HASH \
    AttributeName=fileId,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region $REGION

# Conversations 테이블
aws dynamodb create-table \
  --table-name sedaily-column-conversations \
  --attribute-definitions \
    AttributeName=conversationId,AttributeType=S \
    AttributeName=userId,AttributeType=S \
    AttributeName=createdAt,AttributeType=S \
  --key-schema \
    AttributeName=conversationId,KeyType=HASH \
  --global-secondary-indexes \
    IndexName=userId-createdAt-index,KeySchema=[{AttributeName=userId,KeyType=HASH},{AttributeName=createdAt,KeyType=RANGE}],Projection={ProjectionType=ALL} \
  --billing-mode PAY_PER_REQUEST \
  --region $REGION

# Usage 테이블
aws dynamodb create-table \
  --table-name sedaily-column-usage \
  --attribute-definitions \
    AttributeName=PK,AttributeType=S \
    AttributeName=SK,AttributeType=S \
  --key-schema \
    AttributeName=PK,KeyType=HASH \
    AttributeName=SK,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region $REGION

echo "✅ All tables created"
```

## 🔐 보안 설정

### IAM 역할

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": ["arn:aws:dynamodb:us-east-1:*:table/sedaily-column-*"]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

### CORS 설정

```json
{
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
  "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
}
```

## 📊 모니터링

### CloudWatch 대시보드

```bash
# 로그 그룹 확인
aws logs describe-log-groups \
  --log-group-name-prefix "/aws/lambda/sedaily-column" \
  --region us-east-1

# 에러 로그 검색
aws logs filter-log-events \
  --log-group-name "/aws/lambda/sedaily-column-prompt-crud" \
  --filter-pattern "ERROR" \
  --region us-east-1
```

### 주요 메트릭

- **Invocation Count**: Lambda 호출 횟수
- **Duration**: 실행 시간
- **Error Rate**: 에러 발생률
- **Throttles**: 제한 발생 횟수

## 🧪 테스트

### API 테스트 스크립트

```bash
#!/bin/bash
# test-api.sh

BASE_URL="https://t75vorhge1.execute-api.us-east-1.amazonaws.com/prod"

echo "Testing API endpoints..."

# 프롬프트 목록 조회
curl -X GET "$BASE_URL/prompts" \
  -H "Content-Type: application/json"

# 대화 목록 조회
curl -X GET "$BASE_URL/conversations?userId=test@example.com" \
  -H "Content-Type: application/json"

# 사용량 조회
curl -X GET "$BASE_URL/usage/test@example.com/all" \
  -H "Content-Type: application/json"

echo "✅ API tests completed"
```

## 🔄 롤백 절차

### 이전 버전으로 롤백

```bash
#!/bin/bash
# rollback.sh

API_ID="t75vorhge1"
STAGE="prod"
REGION="us-east-1"

# 이전 배포 ID 확인
PREVIOUS_DEPLOYMENT=$(aws apigateway get-deployments \
  --rest-api-id $API_ID \
  --region $REGION \
  --query 'items[1].id' \
  --output text)

# 스테이지 업데이트
aws apigateway update-stage \
  --rest-api-id $API_ID \
  --stage-name $STAGE \
  --patch-ops op=replace,path=/deploymentId,value=$PREVIOUS_DEPLOYMENT \
  --region $REGION

echo "✅ Rollback completed to deployment: $PREVIOUS_DEPLOYMENT"
```

## 📝 체크리스트

### 배포 전 확인사항

- [ ] Lambda 함수 코드 업데이트
- [ ] 환경 변수 설정 확인
- [ ] DynamoDB 테이블 존재 확인
- [ ] IAM 권한 설정 확인
- [ ] API Gateway 라우트 설정

### 배포 후 확인사항

- [ ] API 엔드포인트 응답 확인
- [ ] CloudWatch 로그 확인
- [ ] 에러율 모니터링
- [ ] 성능 메트릭 확인
- [ ] CORS 설정 동작 확인

## 🆘 트러블슈팅

### 자주 발생하는 문제

1. **CORS 에러**: OPTIONS 메서드 설정 확인
2. **권한 에러**: IAM 역할 정책 확인
3. **타임아웃**: Lambda 함수 타임아웃 설정 증가
4. **메모리 부족**: Lambda 메모리 할당량 증가

### 로그 확인 방법

```bash
# 실시간 로그 확인
aws logs tail /aws/lambda/sedaily-column-prompt-crud --follow

# 특정 시간대 로그 확인
aws logs filter-log-events \
  --log-group-name "/aws/lambda/sedaily-column-prompt-crud" \
  --start-time 1640995200000 \
  --end-time 1641081600000
```
