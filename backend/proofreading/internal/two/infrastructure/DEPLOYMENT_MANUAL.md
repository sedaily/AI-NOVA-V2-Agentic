# Infrastructure 배포 매뉴얼

## 개요

Infrastructure 폴더는 AWS 리소스 정의와 배포 스크립트를 관리. 코드와 분리된 인프라 구성으로 IaC(Infrastructure as Code) 원칙 준수.

## 사전 준비

### 필수 도구
- AWS CLI v2 이상
- jq (JSON 처리)
- Bash 4.0 이상
- Python 3.9 이상 (스크립트용)

### AWS 권한
- AdministratorAccess 또는 다음 서비스별 권한:
  - IAM, DynamoDB, Lambda, API Gateway, S3, CloudFront
  - Route53, ACM, Cognito, Bedrock, CloudWatch

### 초기 설정
```bash
# AWS CLI 프로필 설정
aws configure --profile new-service
AWS_PROFILE=new-service
AWS_REGION=us-east-1
```

## 1단계: 프로젝트 구조 복제

### 1.1 디렉토리 생성
```bash
mkdir -p new-service-infra/infrastructure
cd new-service-infra/infrastructure

# 기존 구조 복사
cp -r [source]/infrastructure/aws ./
cp -r [source]/infrastructure/scripts ./
```

### 1.2 구조 확인
```
infrastructure/
├── aws/                    # AWS 서비스별 설정
│   ├── api-gateway/       # REST/WebSocket API
│   ├── bedrock/          # AI 모델 설정
│   ├── cloudfront/       # CDN 설정
│   ├── cognito/         # 인증 설정
│   ├── dynamodb/        # 데이터베이스
│   ├── iam/            # 권한 정책
│   ├── lambda/         # 함수 설정
│   ├── route53/        # DNS 설정
│   └── s3/            # 스토리지
└── scripts/           # 배포 스크립트
```

## 2단계: 설정 파일 수정

### 2.1 전역 설정
`config.json` 생성:
```json
{
  "service_name": "new-service",
  "region": "us-east-1",
  "account_id": "887078546492",
  "environment": "production",
  "domain": "new-service.com"
}
```

### 2.2 서비스별 설정 수정

#### DynamoDB 테이블
`aws/dynamodb/tables.yaml` 수정:
```yaml
tables:
  - name: ${SERVICE_NAME}-conversations
    partition_key: conversation_id
    sort_key: timestamp
    billing_mode: PAY_PER_REQUEST
    stream: true
    ttl_attribute: ttl
    
  - name: ${SERVICE_NAME}-prompts
    partition_key: prompt_id
    sort_key: user_id
    billing_mode: PAY_PER_REQUEST
    
  - name: ${SERVICE_NAME}-usage
    partition_key: user_id
    sort_key: date
    billing_mode: PAY_PER_REQUEST
    
  - name: ${SERVICE_NAME}-websocket-connections
    partition_key: connection_id
    billing_mode: PAY_PER_REQUEST
    ttl_attribute: ttl
```

#### Lambda 함수
`aws/lambda/functions.yaml` 수정:
```yaml
defaults:
  runtime: python3.9
  timeout: 30
  memory: 512
  environment:
    SERVICE_NAME: ${SERVICE_NAME}
    STAGE: ${ENVIRONMENT}

functions:
  - name: ${SERVICE_NAME}-conversation-api
  - name: ${SERVICE_NAME}-prompt-crud
  - name: ${SERVICE_NAME}-usage-handler
  - name: ${SERVICE_NAME}-websocket-connect
  - name: ${SERVICE_NAME}-websocket-disconnect
  - name: ${SERVICE_NAME}-websocket-message
```

#### API Gateway
`aws/api-gateway/rest-api.yaml` 수정:
```yaml
api:
  name: ${SERVICE_NAME}-rest-api
  endpoints:
    - path: /conversations
      methods: [GET, POST, PUT, DELETE, OPTIONS]
    - path: /prompts
      methods: [GET, POST, PUT, DELETE, OPTIONS]
    - path: /usage
      methods: [GET, OPTIONS]
```

## 3단계: IAM 역할 및 정책

### 3.1 Lambda 실행 역할
`scripts/01-setup-iam.sh`:
```bash
#!/bin/bash
SERVICE_NAME=${1:-new-service}

# Lambda 실행 역할 생성
aws iam create-role \
  --role-name ${SERVICE_NAME}-lambda-role \
  --assume-role-policy-document file://aws/iam/lambda-trust-policy.json

# DynamoDB 권한
aws iam attach-role-policy \
  --role-name ${SERVICE_NAME}-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess

# CloudWatch 권한
aws iam attach-role-policy \
  --role-name ${SERVICE_NAME}-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess

# Bedrock 권한 (WebSocket 핸들러용)
aws iam put-role-policy \
  --role-name ${SERVICE_NAME}-lambda-role \
  --policy-name BedrockAccess \
  --policy-document file://aws/iam/bedrock-policy.json
```

### 3.2 API Gateway 권한
```bash
# Lambda 호출 권한
aws lambda add-permission \
  --function-name ${SERVICE_NAME}-conversation-api \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:*:*:*/*/*"
```

## 4단계: DynamoDB 테이블 생성

### 4.1 테이블 생성 스크립트
`scripts/02-setup-dynamodb.sh`:
```bash
#!/bin/bash
SERVICE_NAME=${1:-new-service}

# Conversations 테이블
aws dynamodb create-table \
  --table-name ${SERVICE_NAME}-conversations \
  --attribute-definitions \
    AttributeName=conversation_id,AttributeType=S \
    AttributeName=user_id,AttributeType=S \
  --key-schema \
    AttributeName=conversation_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --stream-specification StreamEnabled=true,StreamViewType=NEW_AND_OLD_IMAGES \
  --global-secondary-indexes \
    IndexName=user-index,Keys=[{AttributeName=user_id,KeyType=HASH}],Projection={ProjectionType=ALL}

# TTL 활성화
aws dynamodb update-time-to-live \
  --table-name ${SERVICE_NAME}-conversations \
  --time-to-live-specification Enabled=true,AttributeName=ttl

echo "DynamoDB 테이블 생성 완료"
```

### 4.2 실행
```bash
chmod +x scripts/02-setup-dynamodb.sh
./scripts/02-setup-dynamodb.sh new-service
```

## 5단계: Lambda 함수 배포

### 5.1 함수 생성 스크립트
`scripts/03-setup-lambda.sh`:
```bash
#!/bin/bash
SERVICE_NAME=${1:-new-service}
CODE_PATH=${2:-../../backend}

# 코드 패키징
cd $CODE_PATH
zip -r deployment.zip handlers/ src/ lib/ utils/ -x "*.pyc" -x "*__pycache__*"

# 함수 생성/업데이트
FUNCTIONS=(
  "conversation-api"
  "prompt-crud"
  "usage-handler"
  "websocket-connect"
  "websocket-disconnect"
  "websocket-message"
)

for FUNCTION in "${FUNCTIONS[@]}"; do
  aws lambda create-function \
    --function-name ${SERVICE_NAME}-${FUNCTION} \
    --runtime python3.9 \
    --role arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/${SERVICE_NAME}-lambda-role \
    --handler handlers.${FUNCTION//-/_}.handler \
    --zip-file fileb://deployment.zip \
    --timeout 30 \
    --memory-size 512 \
    --environment Variables="{
      SERVICE_NAME=${SERVICE_NAME},
      STAGE=production
    }" || \
  aws lambda update-function-code \
    --function-name ${SERVICE_NAME}-${FUNCTION} \
    --zip-file fileb://deployment.zip
done
```

## 6단계: API Gateway 설정

### 6.1 REST API 생성
`scripts/04-setup-api-gateway.sh`:
```bash
#!/bin/bash
SERVICE_NAME=${1:-new-service}

# REST API 생성
API_ID=$(aws apigateway create-rest-api \
  --name ${SERVICE_NAME}-rest-api \
  --endpoint-configuration types=REGIONAL \
  --query 'id' --output text)

# 루트 리소스 ID
ROOT_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --query 'items[0].id' --output text)

# /conversations 리소스
CONV_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part conversations \
  --query 'id' --output text)

# GET 메서드
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $CONV_ID \
  --http-method GET \
  --authorization-type NONE

# Lambda 통합
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $CONV_ID \
  --http-method GET \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:${AWS_REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:${AWS_REGION}:${ACCOUNT_ID}:function:${SERVICE_NAME}-conversation-api/invocations

# CORS 설정
source scripts/setup-cors.sh $API_ID $CONV_ID

# 배포
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name production

echo "REST API URL: https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com/production"
```

### 6.2 WebSocket API 생성
`scripts/05-setup-websocket.sh`:
```bash
#!/bin/bash
SERVICE_NAME=${1:-new-service}

# WebSocket API 생성
WS_API_ID=$(aws apigatewayv2 create-api \
  --name ${SERVICE_NAME}-websocket-api \
  --protocol-type WEBSOCKET \
  --route-selection-expression '$request.body.action' \
  --query 'ApiId' --output text)

# 라우트 생성
for ROUTE in connect disconnect default; do
  if [ "$ROUTE" = "connect" ]; then
    ROUTE_KEY='$connect'
    FUNCTION="websocket-connect"
  elif [ "$ROUTE" = "disconnect" ]; then
    ROUTE_KEY='$disconnect'
    FUNCTION="websocket-disconnect"
  else
    ROUTE_KEY='$default'
    FUNCTION="websocket-message"
  fi
  
  # 통합 생성
  INTEGRATION_ID=$(aws apigatewayv2 create-integration \
    --api-id $WS_API_ID \
    --integration-type AWS_PROXY \
    --integration-uri arn:aws:lambda:${AWS_REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:${AWS_REGION}:${ACCOUNT_ID}:function:${SERVICE_NAME}-${FUNCTION}/invocations \
    --query 'IntegrationId' --output text)
  
  # 라우트 생성
  aws apigatewayv2 create-route \
    --api-id $WS_API_ID \
    --route-key "$ROUTE_KEY" \
    --target integrations/${INTEGRATION_ID}
done

# 스테이지 생성
aws apigatewayv2 create-stage \
  --api-id $WS_API_ID \
  --stage-name production

echo "WebSocket API URL: wss://${WS_API_ID}.execute-api.${AWS_REGION}.amazonaws.com/production"
```

## 7단계: S3 및 CloudFront 설정

### 7.1 S3 버킷 생성
`scripts/06-setup-s3.sh`:
```bash
#!/bin/bash
SERVICE_NAME=${1:-new-service}

# Frontend 버킷
aws s3 mb s3://${SERVICE_NAME}-frontend --region ${AWS_REGION}

# 정적 웹 호스팅
aws s3 website s3://${SERVICE_NAME}-frontend \
  --index-document index.html \
  --error-document error.html

# 버킷 정책
cat > /tmp/bucket-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::${SERVICE_NAME}-frontend/*"
  }]
}
EOF

aws s3api put-bucket-policy \
  --bucket ${SERVICE_NAME}-frontend \
  --policy file:///tmp/bucket-policy.json
```

### 7.2 CloudFront 배포
`scripts/07-setup-cloudfront.sh`:
```bash
#!/bin/bash
SERVICE_NAME=${1:-new-service}

# CloudFront 배포 설정
cat > /tmp/cloudfront-config.json << EOF
{
  "CallerReference": "${SERVICE_NAME}-$(date +%s)",
  "Comment": "${SERVICE_NAME} Frontend Distribution",
  "DefaultRootObject": "index.html",
  "Origins": {
    "Quantity": 1,
    "Items": [{
      "Id": "S3-${SERVICE_NAME}-frontend",
      "DomainName": "${SERVICE_NAME}-frontend.s3-website-${AWS_REGION}.amazonaws.com",
      "CustomOriginConfig": {
        "HTTPPort": 80,
        "HTTPSPort": 443,
        "OriginProtocolPolicy": "http-only"
      }
    }]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-${SERVICE_NAME}-frontend",
    "ViewerProtocolPolicy": "redirect-to-https",
    "TrustedSigners": {
      "Enabled": false,
      "Quantity": 0
    },
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": {"Forward": "none"}
    },
    "MinTTL": 0,
    "Compress": true
  },
  "Enabled": true
}
EOF

# 배포 생성
DIST_ID=$(aws cloudfront create-distribution \
  --distribution-config file:///tmp/cloudfront-config.json \
  --query 'Distribution.Id' --output text)

echo "CloudFront Distribution ID: ${DIST_ID}"
```

## 8단계: Cognito 사용자 풀

### 8.1 사용자 풀 생성
`scripts/08-setup-cognito.sh`:
```bash
#!/bin/bash
SERVICE_NAME=${1:-new-service}

# 사용자 풀 생성
POOL_ID=$(aws cognito-idp create-user-pool \
  --pool-name ${SERVICE_NAME}-users \
  --auto-verified-attributes email \
  --username-attributes email \
  --mfa-configuration OPTIONAL \
  --query 'UserPool.Id' --output text)

# 앱 클라이언트 생성
CLIENT_ID=$(aws cognito-idp create-user-pool-client \
  --user-pool-id $POOL_ID \
  --client-name ${SERVICE_NAME}-app \
  --generate-secret \
  --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH \
  --query 'UserPoolClient.ClientId' --output text)

echo "User Pool ID: ${POOL_ID}"
echo "Client ID: ${CLIENT_ID}"

# 도메인 생성
aws cognito-idp create-user-pool-domain \
  --domain ${SERVICE_NAME}-auth \
  --user-pool-id $POOL_ID
```

## 9단계: Route53 및 도메인

### 9.1 호스팅 영역 생성
`scripts/09-setup-route53.sh`:
```bash
#!/bin/bash
DOMAIN=${1:-new-service.com}

# 호스팅 영역 생성
ZONE_ID=$(aws route53 create-hosted-zone \
  --name $DOMAIN \
  --caller-reference $(date +%s) \
  --query 'HostedZone.Id' --output text | cut -d'/' -f3)

echo "Hosted Zone ID: ${ZONE_ID}"

# 네임서버 확인
aws route53 get-hosted-zone --id $ZONE_ID \
  --query 'DelegationSet.NameServers' --output table
```

### 9.2 SSL 인증서
```bash
# ACM 인증서 요청 (us-east-1 필수)
CERT_ARN=$(aws acm request-certificate \
  --domain-name $DOMAIN \
  --subject-alternative-names "*.$DOMAIN" \
  --validation-method DNS \
  --region us-east-1 \
  --query 'CertificateArn' --output text)

# DNS 검증 레코드 추가
aws acm describe-certificate \
  --certificate-arn $CERT_ARN \
  --region us-east-1 \
  --query 'Certificate.DomainValidationOptions[0].ResourceRecord'
```

## 10단계: Bedrock 설정

### 10.1 모델 액세스 활성화
`scripts/10-setup-bedrock.sh`:
```bash
#!/bin/bash

# 모델 액세스 요청
aws bedrock put-model-invocation-logging-configuration \
  --logging-config "{
    \"cloudWatchConfig\": {
      \"logGroupName\": \"/aws/bedrock/${SERVICE_NAME}\",
      \"roleArn\": \"arn:aws:iam::${ACCOUNT_ID}:role/${SERVICE_NAME}-bedrock-role\"
    }
  }"

# 가드레일 생성
aws bedrock create-guardrail \
  --name ${SERVICE_NAME}-guardrail \
  --description "Content filtering for ${SERVICE_NAME}" \
  --topic-policy-config file://aws/bedrock/guardrail-config.json \
  --content-policy-config file://aws/bedrock/content-policy.json
```

## 11단계: 모니터링 설정

### 11.1 CloudWatch 대시보드
`scripts/11-setup-monitoring.sh`:
```bash
#!/bin/bash
SERVICE_NAME=${1:-new-service}

# 대시보드 생성
aws cloudwatch put-dashboard \
  --dashboard-name ${SERVICE_NAME}-overview \
  --dashboard-body file://aws/cloudwatch/dashboard.json

# 알람 생성
aws cloudwatch put-metric-alarm \
  --alarm-name ${SERVICE_NAME}-api-errors \
  --alarm-description "High API error rate" \
  --metric-name 4XXError \
  --namespace AWS/ApiGateway \
  --statistic Average \
  --period 300 \
  --threshold 0.05 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

## 12단계: 통합 배포

### 12.1 마스터 스크립트
`scripts/deploy-all.sh`:
```bash
#!/bin/bash
set -e

SERVICE_NAME=${1:-new-service}
DOMAIN=${2:-new-service.com}
ENVIRONMENT=${3:-production}

echo "====== Infrastructure 배포 시작 ======"
echo "Service: $SERVICE_NAME"
echo "Domain: $DOMAIN"
echo "Environment: $ENVIRONMENT"

# 1. IAM 설정
echo "1. IAM 역할 생성..."
./scripts/01-setup-iam.sh $SERVICE_NAME

# 2. DynamoDB 테이블
echo "2. DynamoDB 테이블 생성..."
./scripts/02-setup-dynamodb.sh $SERVICE_NAME

# 3. Lambda 함수
echo "3. Lambda 함수 배포..."
./scripts/03-setup-lambda.sh $SERVICE_NAME

# 4. API Gateway
echo "4. API Gateway 설정..."
./scripts/04-setup-api-gateway.sh $SERVICE_NAME
./scripts/05-setup-websocket.sh $SERVICE_NAME

# 5. S3 & CloudFront
echo "5. S3 및 CloudFront 설정..."
./scripts/06-setup-s3.sh $SERVICE_NAME
./scripts/07-setup-cloudfront.sh $SERVICE_NAME

# 6. Cognito
echo "6. Cognito 사용자 풀 생성..."
./scripts/08-setup-cognito.sh $SERVICE_NAME

# 7. Route53
echo "7. Route53 도메인 설정..."
./scripts/09-setup-route53.sh $DOMAIN

# 8. Bedrock
echo "8. Bedrock 설정..."
./scripts/10-setup-bedrock.sh $SERVICE_NAME

# 9. 모니터링
echo "9. CloudWatch 모니터링 설정..."
./scripts/11-setup-monitoring.sh $SERVICE_NAME

echo "====== 배포 완료 ======"
echo "Frontend URL: https://$DOMAIN"
echo "API URL: https://api.$DOMAIN"
echo "WebSocket URL: wss://ws.$DOMAIN"
```

### 12.2 실행
```bash
chmod +x scripts/*.sh
./scripts/deploy-all.sh new-service new-service.com production
```

## 환경 변수 관리

### 개발/스테이징/프로덕션 분리
`environments/` 디렉토리 구조:
```
environments/
├── dev.env
├── staging.env
└── production.env
```

`production.env`:
```bash
SERVICE_NAME=new-service
ENVIRONMENT=production
AWS_REGION=us-east-1
DOMAIN=new-service.com
LAMBDA_MEMORY=512
LAMBDA_TIMEOUT=30
DYNAMODB_BILLING=PAY_PER_REQUEST
```

## 롤백 전략

### Lambda 함수 버전 관리
```bash
# 버전 생성
aws lambda publish-version \
  --function-name ${SERVICE_NAME}-conversation-api \
  --description "v1.0.0"

# 별칭 업데이트
aws lambda update-alias \
  --function-name ${SERVICE_NAME}-conversation-api \
  --name production \
  --function-version 1
```

### API Gateway 스테이지
```bash
# 새 스테이지 생성
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name staging

# 카나리 배포
aws apigateway update-stage \
  --rest-api-id $API_ID \
  --stage-name production \
  --patch-operations op=replace,path=/canarySettings/percentTraffic,value=10
```

## 비용 최적화

### DynamoDB On-Demand vs Provisioned
```bash
# 사용량 분석
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=${SERVICE_NAME}-conversations \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Average,Sum

# Provisioned로 변경 (비용 절감)
aws dynamodb update-table \
  --table-name ${SERVICE_NAME}-conversations \
  --billing-mode PROVISIONED \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
```

### Lambda 예약 동시 실행
```bash
# 콜드 스타트 방지
aws lambda put-provisioned-concurrency-config \
  --function-name ${SERVICE_NAME}-conversation-api \
  --provisioned-concurrent-executions 2 \
  --qualifier production
```

## 트러블슈팅

### 배포 실패 시 체크리스트
1. IAM 권한 확인
2. 리전 설정 확인 (us-east-1)
3. 서비스 한도 확인
4. 네트워크 설정 (VPC, 보안 그룹)
5. CloudWatch 로그 확인

### 일반적인 오류 해결
```bash
# Lambda 권한 오류
aws lambda add-permission \
  --function-name ${FUNCTION_NAME} \
  --statement-id apigateway-${RANDOM} \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com

# DynamoDB 스로틀링
aws dynamodb update-table \
  --table-name ${TABLE_NAME} \
  --billing-mode PAY_PER_REQUEST

# API Gateway 타임아웃
aws apigateway update-integration \
  --rest-api-id ${API_ID} \
  --resource-id ${RESOURCE_ID} \
  --http-method GET \
  --patch-operations op=replace,path=/timeoutInMillis,value=29000
```