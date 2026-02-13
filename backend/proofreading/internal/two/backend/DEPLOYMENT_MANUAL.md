# Backend 배포 매뉴얼

## 사전 준비

### 필수 도구

- AWS CLI 설치 및 설정
- Python 3.9 이상
- Node.js 18 이상
- Git

### AWS 계정 준비

- IAM 사용자 생성
- 프로그래매틱 액세스 키 발급
- 필요 권한: Lambda, API Gateway, DynamoDB, S3, CloudFront, IAM

## 1단계: 프로젝트 복제 및 설정 변경

### 1.1 프로젝트 복제

```bash
git clone [repository-url] new-service-name
cd new-service-name/backend
```

### 1.2 서비스 이름 변경

`src/config/aws.py` 파일 수정:

```python
SERVICE_PREFIX = "new-service"  # 기존: nexus
STAGE = "prod"
REGION = "us-east-1"
```

### 1.3 환경 변수 파일 생성

`.env.production` 파일 생성:

```bash
# DynamoDB 테이블
CONVERSATIONS_TABLE=new-service-conversations
PROMPTS_TABLE=new-service-prompts
USAGE_TABLE=new-service-usage
WEBSOCKET_TABLE=new-service-websocket-connections

# API Gateway
REST_API_NAME=new-service-rest-api
WEBSOCKET_API_NAME=new-service-websocket-api

# Lambda 함수 접두어
LAMBDA_PREFIX=new-service

# S3 버킷
S3_BUCKET=new-service-frontend

# CloudFront
CLOUDFRONT_COMMENT=New Service Distribution
```

## 2단계: AWS 리소스 생성

### 2.1 DynamoDB 테이블 생성

```bash
cd scripts

# 테이블 이름 수정
vi 01-setup-dynamodb.sh
# TABLE_PREFIX 변경: new-service

# 실행
./01-setup-dynamodb.sh
```

생성될 테이블:

- new-service-conversations
- new-service-prompts
- new-service-usage
- new-service-websocket-connections

### 2.2 Lambda 함수 생성

#### 2.2.1 함수 이름 설정

`scripts/99-deploy-lambda.sh` 수정:

```bash
FUNCTION_PREFIX="new-service"
FUNCTIONS=(
    "${FUNCTION_PREFIX}-conversation-api"
    "${FUNCTION_PREFIX}-prompt-crud"
    "${FUNCTION_PREFIX}-usage-handler"
    "${FUNCTION_PREFIX}-websocket-connect"
    "${FUNCTION_PREFIX}-websocket-disconnect"
    "${FUNCTION_PREFIX}-websocket-message"
)
```

#### 2.2.2 패키징 및 배포

```bash
# 의존성 설치
pip install -r ../requirements.txt -t ../package/

# 코드 패키징
cd ..
zip -r deployment.zip handlers/ src/ lib/ utils/ -x "*.pyc" -x "*__pycache__*"

# Lambda 함수 생성
aws lambda create-function \
    --function-name new-service-conversation-api \
    --runtime python3.9 \
    --role arn:aws:iam::[ACCOUNT_ID]:role/[ROLE_NAME] \
    --handler handlers.api.conversation.handler \
    --zip-file fileb://deployment.zip \
    --timeout 30 \
    --memory-size 512
```

### 2.3 API Gateway 설정

#### 2.3.1 REST API 생성

```bash
# API 생성
aws apigateway create-rest-api \
    --name new-service-rest-api \
    --endpoint-configuration types=REGIONAL

# API ID 저장
REST_API_ID=[생성된 API ID]
```

#### 2.3.2 리소스 및 메서드 생성

```bash
# /conversations 리소스
aws apigateway create-resource \
    --rest-api-id $REST_API_ID \
    --parent-id [ROOT_ID] \
    --path-part conversations

# GET 메서드
aws apigateway put-method \
    --rest-api-id $REST_API_ID \
    --resource-id [RESOURCE_ID] \
    --http-method GET \
    --authorization-type NONE
```

#### 2.3.3 Lambda 통합

```bash
aws apigateway put-integration \
    --rest-api-id $REST_API_ID \
    --resource-id [RESOURCE_ID] \
    --http-method GET \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri arn:aws:apigateway:[REGION]:lambda:path/2015-03-31/functions/arn:aws:lambda:[REGION]:[ACCOUNT_ID]:function:new-service-conversation-api/invocations
```

#### 2.3.4 CORS 설정

```bash
aws apigateway put-method \
    --rest-api-id $REST_API_ID \
    --resource-id [RESOURCE_ID] \
    --http-method OPTIONS \
    --authorization-type NONE

aws apigateway put-method-response \
    --rest-api-id $REST_API_ID \
    --resource-id [RESOURCE_ID] \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters \
    '{"method.response.header.Access-Control-Allow-Headers":true,
      "method.response.header.Access-Control-Allow-Methods":true,
      "method.response.header.Access-Control-Allow-Origin":true}'
```

#### 2.3.5 배포

```bash
aws apigateway create-deployment \
    --rest-api-id $REST_API_ID \
    --stage-name prod

# API URL
echo "https://$REST_API_ID.execute-api.[REGION].amazonaws.com/prod"
```

### 2.4 WebSocket API 생성

```bash
# WebSocket API 생성
aws apigatewayv2 create-api \
    --name new-service-websocket-api \
    --protocol-type WEBSOCKET \
    --route-selection-expression '$request.body.action'

# API ID 저장
WS_API_ID=[생성된 API ID]

# 라우트 생성
aws apigatewayv2 create-route \
    --api-id $WS_API_ID \
    --route-key '$connect' \
    --target integrations/[INTEGRATION_ID]

aws apigatewayv2 create-route \
    --api-id $WS_API_ID \
    --route-key '$disconnect' \
    --target integrations/[INTEGRATION_ID]

aws apigatewayv2 create-route \
    --api-id $WS_API_ID \
    --route-key '$default' \
    --target integrations/[INTEGRATION_ID]
```

## 3단계: Frontend URL 설정

### 3.1 S3 버킷 생성

```bash
# 버킷 생성
aws s3 mb s3://new-service-frontend

# 정적 웹사이트 호스팅 활성화
aws s3 website s3://new-service-frontend \
    --index-document index.html \
    --error-document error.html

# 버킷 정책 설정
aws s3api put-bucket-policy \
    --bucket new-service-frontend \
    --policy file://bucket-policy.json
```

### 3.2 CloudFront 배포 생성

```bash
aws cloudfront create-distribution \
    --distribution-config file://cloudfront-config.json

# 배포 URL 확인
CLOUDFRONT_URL=[생성된 CloudFront URL]
```

### 3.3 Frontend 설정 업데이트

`frontend/src/config.js` 수정:

```javascript
export const API_BASE_URL =
  "https://[REST_API_ID].execute-api.[REGION].amazonaws.com/prod";
export const WS_URL =
  "wss://[WS_API_ID].execute-api.[REGION].amazonaws.com/prod";
```

## 4단계: 도메인 설정

### 4.1 Route 53 호스팅 영역 생성

```bash
aws route53 create-hosted-zone \
    --name new-service.com \
    --caller-reference $(date +%s)
```

### 4.2 SSL 인증서 요청

```bash
aws acm request-certificate \
    --domain-name new-service.com \
    --subject-alternative-names www.new-service.com \
    --validation-method DNS
```

### 4.3 API Gateway 커스텀 도메인

```bash
# REST API
aws apigateway create-domain-name \
    --domain-name api.new-service.com \
    --certificate-arn [CERTIFICATE_ARN]

# WebSocket API
aws apigatewayv2 create-domain-name \
    --domain-name ws.new-service.com \
    --domain-name-configurations CertificateArn=[CERTIFICATE_ARN]
```

### 4.4 Route 53 레코드 생성

```bash
# CloudFront 연결
aws route53 change-resource-record-sets \
    --hosted-zone-id [ZONE_ID] \
    --change-batch file://route53-cloudfront.json

# API Gateway 연결
aws route53 change-resource-record-sets \
    --hosted-zone-id [ZONE_ID] \
    --change-batch file://route53-api.json
```

## 5단계: 환경별 설정

### 5.1 개발 환경

```bash
# 별도 스테이지 생성
aws apigateway create-stage \
    --rest-api-id $REST_API_ID \
    --stage-name dev \
    --deployment-id [DEPLOYMENT_ID]

# 환경 변수 설정
aws lambda update-function-configuration \
    --function-name new-service-conversation-api \
    --environment Variables={STAGE=dev}
```

### 5.2 프로덕션 환경

```bash
# 스테이지 변수 설정
aws apigateway update-stage \
    --rest-api-id $REST_API_ID \
    --stage-name prod \
    --patch-operations op=replace,path=/variables/environment,value=production
```

## 6단계: 배포 검증

### 6.1 API 테스트

```bash
# REST API
curl https://api.new-service.com/conversations

# WebSocket
wscat -c wss://ws.new-service.com
```

### 6.2 로그 확인

```bash
# Lambda 로그
aws logs tail /aws/lambda/new-service-conversation-api --follow

# API Gateway 로그
aws logs tail /aws/api-gateway/$REST_API_ID/prod --follow
```

### 6.3 메트릭 확인

```bash
# Lambda 메트릭
aws cloudwatch get-metric-statistics \
    --namespace AWS/Lambda \
    --metric-name Invocations \
    --dimensions Name=FunctionName,Value=new-service-conversation-api \
    --start-time $(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 300 \
    --statistics Sum
```

## 7단계: 자동화 스크립트

### 7.1 통합 배포 스크립트 생성

`deploy-all.sh` 파일:

```bash
#!/bin/bash
SERVICE_NAME=$1
DOMAIN=$2

# 1. DynamoDB 테이블 생성
./scripts/01-setup-dynamodb.sh $SERVICE_NAME

# 2. Lambda 함수 배포
./scripts/99-deploy-lambda.sh $SERVICE_NAME

# 3. API Gateway 생성
./scripts/02-setup-api-gateway.sh $SERVICE_NAME

# 4. Frontend 배포
cd ../frontend
npm run build
aws s3 sync dist/ s3://$SERVICE_NAME-frontend

# 5. CloudFront 무효화
aws cloudfront create-invalidation \
    --distribution-id [DISTRIBUTION_ID] \
    --paths "/*"

echo "배포 완료: https://$DOMAIN"
```

### 7.2 실행

```bash
chmod +x deploy-all.sh
./deploy-all.sh new-service new-service.com
```

## 주의사항

### Lambda 함수

- 메모리: WebSocket 메시지 처리는 1024MB 이상 권장
- 타임아웃: API Gateway 제한 29초 고려
- 동시 실행: 예약 동시 실행 설정으로 콜드 스타트 방지

### API Gateway

- CORS: Frontend URL 모두 포함 필수
- 스로틀링: 초당 요청 수 제한 설정
- 인증: Cognito 또는 API 키 설정

### DynamoDB

- 용량: On-Demand 또는 Auto Scaling 설정
- TTL: WebSocket 연결 테이블에 필수
- GSI: 쿼리 패턴에 따라 추가

### 보안

- IAM 역할: 최소 권한 원칙 적용
- 환경 변수: Secrets Manager 사용 권장
- 네트워크: VPC 설정 검토

## 트러블슈팅

### Lambda 함수 import 오류

```bash
# 패키지 구조 확인
unzip -l deployment.zip | head -20

# 핸들러 경로 확인
handlers/api/conversation.py 존재 확인
```

### API Gateway 502 오류

```bash
# Lambda 권한 확인
aws lambda add-permission \
    --function-name new-service-conversation-api \
    --statement-id api-gateway-invoke \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com
```

### CORS 오류

```bash
# Lambda 응답 헤더 확인
"headers": {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization"
}
```
