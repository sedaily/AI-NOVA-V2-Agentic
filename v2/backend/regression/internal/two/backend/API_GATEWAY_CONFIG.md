# API Gateway 설정 가이드

## 🌐 CORS 설정

### 1. CORS 개념

- **Cross-Origin Resource Sharing**: 다른 도메인에서 API 호출을 허용하는 설정
- 브라우저의 Same-Origin Policy를 우회하기 위해 필요

### 2. CORS 설정 방법

#### OPTIONS 메서드 추가

```bash
# 각 리소스에 OPTIONS 메서드 생성
aws apigateway put-method \
    --rest-api-id t75vorhge1 \
    --resource-id <resource-id> \
    --http-method OPTIONS \
    --authorization-type NONE \
    --region us-east-1
```

#### CORS 응답 헤더 설정

```bash
# Method Response 설정
aws apigateway put-method-response \
    --rest-api-id t75vorhge1 \
    --resource-id <resource-id> \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{
        "method.response.header.Access-Control-Allow-Origin": true,
        "method.response.header.Access-Control-Allow-Headers": true,
        "method.response.header.Access-Control-Allow-Methods": true
    }' \
    --region us-east-1

# Integration Response 설정
aws apigateway put-integration-response \
    --rest-api-id t75vorhge1 \
    --resource-id <resource-id> \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{
        "method.response.header.Access-Control-Allow-Origin": "'"'"'*'"'"'",
        "method.response.header.Access-Control-Allow-Headers": "'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'",
        "method.response.header.Access-Control-Allow-Methods": "'"'"'GET,POST,PUT,DELETE,OPTIONS'"'"'"
    }' \
    --region us-east-1
```

#### MOCK Integration 설정

```bash
# OPTIONS 메서드에 MOCK 통합 설정
aws apigateway put-integration \
    --rest-api-id t75vorhge1 \
    --resource-id <resource-id> \
    --http-method OPTIONS \
    --type MOCK \
    --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
    --region us-east-1
```

### 3. CORS 헤더 상세

| 헤더                         | 값                                                                     | 설명                           |
| ---------------------------- | ---------------------------------------------------------------------- | ------------------------------ |
| Access-Control-Allow-Origin  | `*`                                                                    | 모든 도메인 허용               |
| Access-Control-Allow-Headers | `Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token` | 허용할 요청 헤더               |
| Access-Control-Allow-Methods | `GET,POST,PUT,DELETE,OPTIONS`                                          | 허용할 HTTP 메서드             |
| Access-Control-Max-Age       | `86400`                                                                | Preflight 캐시 시간 (선택사항) |

## 🛣️ 라우트 설정

### 1. 리소스 구조

```
/
├── prompts
│   ├── {promptId}
│   │   └── files
│   │       └── {fileId}
├── conversations
│   └── {conversationId}
└── usage
    └── {userId}
        └── {engineType}
```

### 2. 리소스 생성 명령어

#### 루트 리소스 확인

```bash
ROOT_ID=$(aws apigateway get-resources \
    --rest-api-id t75vorhge1 \
    --region us-east-1 \
    --query 'items[?path==`/`].id' \
    --output text)
```

#### /prompts 리소스 생성

```bash
PROMPTS_ID=$(aws apigateway create-resource \
    --rest-api-id t75vorhge1 \
    --parent-id $ROOT_ID \
    --path-part "prompts" \
    --region us-east-1 \
    --query 'id' --output text)
```

#### /prompts/{promptId} 리소스 생성

```bash
PROMPT_ID_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id t75vorhge1 \
    --parent-id $PROMPTS_ID \
    --path-part "{promptId}" \
    --region us-east-1 \
    --query 'id' --output text)
```

### 3. HTTP 메서드 설정

#### GET 메서드 추가

```bash
aws apigateway put-method \
    --rest-api-id t75vorhge1 \
    --resource-id $PROMPTS_ID \
    --http-method GET \
    --authorization-type NONE \
    --region us-east-1
```

#### Lambda 통합 설정

```bash
aws apigateway put-integration \
    --rest-api-id t75vorhge1 \
    --resource-id $PROMPTS_ID \
    --http-method GET \
    --type AWS_PROXY \
    --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:887078546492:function:sedaily-column-prompt-crud/invocations" \
    --integration-http-method POST \
    --region us-east-1
```

### 4. 전체 라우트 매핑

| 경로                                 | 메서드                      | Lambda 함수                     | 설명               |
| ------------------------------------ | --------------------------- | ------------------------------- | ------------------ |
| `/prompts`                           | GET, POST, OPTIONS          | sedaily-column-prompt-crud      | 프롬프트 목록/생성 |
| `/prompts/{promptId}`                | GET, PUT, DELETE, OPTIONS   | sedaily-column-prompt-crud      | 프롬프트 상세      |
| `/prompts/{promptId}/files`          | GET, POST, OPTIONS          | sedaily-column-prompt-crud      | 파일 목록/생성     |
| `/prompts/{promptId}/files/{fileId}` | GET, PUT, DELETE, OPTIONS   | sedaily-column-prompt-crud      | 파일 상세          |
| `/conversations`                     | GET, POST, OPTIONS          | sedaily-column-conversation-api | 대화 목록/생성     |
| `/conversations/{conversationId}`    | GET, PATCH, DELETE, OPTIONS | sedaily-column-conversation-api | 대화 상세          |
| `/usage`                             | POST, OPTIONS               | sedaily-column-usage-handler    | 사용량 업데이트    |
| `/usage/{userId}/{engineType}`       | GET, OPTIONS                | sedaily-column-usage-handler    | 사용량 조회        |

## 🏗️ 스테이지 설정

### 1. 스테이지 개념

- **Stage**: API의 배포 환경 (dev, staging, prod)
- 각 스테이지는 독립적인 URL을 가짐
- 스테이지별로 다른 설정 가능

### 2. 스테이지 생성

#### 개발 스테이지

```bash
aws apigateway create-stage \
    --rest-api-id t75vorhge1 \
    --stage-name dev \
    --deployment-id <deployment-id> \
    --description "Development environment" \
    --region us-east-1
```

#### 스테이징 스테이지

```bash
aws apigateway create-stage \
    --rest-api-id t75vorhge1 \
    --stage-name staging \
    --deployment-id <deployment-id> \
    --description "Staging environment" \
    --region us-east-1
```

#### 프로덕션 스테이지

```bash
aws apigateway create-stage \
    --rest-api-id t75vorhge1 \
    --stage-name prod \
    --deployment-id <deployment-id> \
    --description "Production environment" \
    --region us-east-1
```

### 3. 스테이지별 URL

```
개발:     https://t75vorhge1.execute-api.us-east-1.amazonaws.com/dev
스테이징: https://t75vorhge1.execute-api.us-east-1.amazonaws.com/staging
프로덕션: https://t75vorhge1.execute-api.us-east-1.amazonaws.com/prod
```

### 4. 스테이지 변수 설정

```bash
# 스테이지 변수 설정 (Lambda 함수 버전 관리 등)
aws apigateway update-stage \
    --rest-api-id t75vorhge1 \
    --stage-name dev \
    --patch-ops '[
        {
            "op": "replace",
            "path": "/variables/lambdaAlias",
            "value": "DEV"
        },
        {
            "op": "replace",
            "path": "/variables/environment",
            "value": "development"
        }
    ]' \
    --region us-east-1
```

### 5. 스테이지별 설정 예시

#### 개발 환경

```json
{
  "stageName": "dev",
  "variables": {
    "environment": "development",
    "lambdaAlias": "DEV",
    "logLevel": "DEBUG"
  },
  "throttle": {
    "rateLimit": 100,
    "burstLimit": 200
  }
}
```

#### 프로덕션 환경

```json
{
  "stageName": "prod",
  "variables": {
    "environment": "production",
    "lambdaAlias": "PROD",
    "logLevel": "ERROR"
  },
  "throttle": {
    "rateLimit": 1000,
    "burstLimit": 2000
  }
}
```

### 6. 배포 및 스테이지 업데이트

#### 새 배포 생성

```bash
DEPLOYMENT_ID=$(aws apigateway create-deployment \
    --rest-api-id t75vorhge1 \
    --stage-name prod \
    --description "$(date) deployment" \
    --region us-east-1 \
    --query 'id' --output text)
```

#### 기존 스테이지에 새 배포 적용

```bash
aws apigateway update-stage \
    --rest-api-id t75vorhge1 \
    --stage-name staging \
    --patch-ops op=replace,path=/deploymentId,value=$DEPLOYMENT_ID \
    --region us-east-1
```

### 7. 스테이지 모니터링 설정

#### CloudWatch 로깅 활성화

```bash
aws apigateway update-stage \
    --rest-api-id t75vorhge1 \
    --stage-name prod \
    --patch-ops '[
        {
            "op": "replace",
            "path": "/accessLogSettings/destinationArn",
            "value": "arn:aws:logs:us-east-1:887078546492:log-group:API-Gateway-Execution-Logs_t75vorhge1/prod"
        },
        {
            "op": "replace",
            "path": "/accessLogSettings/format",
            "value": "$requestId $ip $caller $user [$requestTime] \"$httpMethod $resourcePath $protocol\" $status $error.message $error.messageString"
        }
    ]' \
    --region us-east-1
```

#### 메트릭 활성화

```bash
aws apigateway update-stage \
    --rest-api-id t75vorhge1 \
    --stage-name prod \
    --patch-ops '[
        {
            "op": "replace",
            "path": "/metricsEnabled",
            "value": "true"
        },
        {
            "op": "replace",
            "path": "/dataTraceEnabled",
            "value": "true"
        }
    ]' \
    --region us-east-1
```

## 🔧 실제 설정 스크립트

### 완전한 API 설정 스크립트

```bash
#!/bin/bash
# complete-api-setup.sh

API_ID="t75vorhge1"
REGION="us-east-1"

# 1. 루트 리소스 ID 가져오기
ROOT_ID=$(aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query 'items[?path==`/`].id' --output text)

# 2. 리소스 생성 함수
create_resource_with_cors() {
    local PARENT_ID=$1
    local PATH_PART=$2
    local LAMBDA_ARN=$3
    local METHODS=$4

    # 리소스 생성
    RESOURCE_ID=$(aws apigateway create-resource \
        --rest-api-id $API_ID \
        --parent-id $PARENT_ID \
        --path-part "$PATH_PART" \
        --region $REGION \
        --query 'id' --output text)

    # OPTIONS 메서드 (CORS)
    aws apigateway put-method \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --authorization-type NONE \
        --region $REGION

    aws apigateway put-integration \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --type MOCK \
        --request-templates '{"application/json":"{\"statusCode\": 200}"}' \
        --region $REGION

    aws apigateway put-method-response \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{
            "method.response.header.Access-Control-Allow-Origin":true,
            "method.response.header.Access-Control-Allow-Headers":true,
            "method.response.header.Access-Control-Allow-Methods":true
        }' \
        --region $REGION

    aws apigateway put-integration-response \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{
            "method.response.header.Access-Control-Allow-Origin":"'"'"'*'"'"'",
            "method.response.header.Access-Control-Allow-Headers":"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'",
            "method.response.header.Access-Control-Allow-Methods":"'"'"'GET,POST,PUT,DELETE,OPTIONS'"'"'"
        }' \
        --region $REGION

    # 실제 HTTP 메서드들
    for METHOD in $METHODS; do
        aws apigateway put-method \
            --rest-api-id $API_ID \
            --resource-id $RESOURCE_ID \
            --http-method $METHOD \
            --authorization-type NONE \
            --region $REGION

        aws apigateway put-integration \
            --rest-api-id $API_ID \
            --resource-id $RESOURCE_ID \
            --http-method $METHOD \
            --type AWS_PROXY \
            --uri "$LAMBDA_ARN" \
            --integration-http-method POST \
            --region $REGION
    done

    echo $RESOURCE_ID
}

# 3. 리소스 생성
PROMPTS_ID=$(create_resource_with_cors $ROOT_ID "prompts" \
    "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:887078546492:function:sedaily-column-prompt-crud/invocations" \
    "GET POST")

# 4. 배포
aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name prod \
    --region $REGION

echo "API 설정 완료!"
```

이 설정들이 현재 프로젝트의 API Gateway 구성의 핵심입니다.
