#!/bin/bash

# 최종 완전한 API Gateway 배포 스크립트
# Swagger 스펙 100% 반영 버전
# nexus-template-v2용 p2-two 스택

set -e  # 에러 발생시 즉시 중단

# config.sh 파일 로드
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

STACK_NAME="${SERVICE_NAME}"

echo "=========================================="
echo "🚀 최종 API Gateway 배포"
echo "스택: ${STACK_NAME}"
echo "카드 수: ${CARD_COUNT}"
echo "=========================================="

# Lambda 함수 이름들 (실제 생성된 Lambda 이름과 일치)
LAMBDA_CONVERSATIONS="p2-two-conversation-api-two"
LAMBDA_PROMPTS="p2-two-prompt-crud-two"
LAMBDA_USAGE="p2-two-usage-handler-two"

# AWS 계정 ID 가져오기
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION="us-east-1"

echo "계정 ID: $ACCOUNT_ID"
echo "리전: $REGION"
echo ""

# 1. REST API 생성
echo "[1/10] REST API 생성..."
REST_API_ID=$(aws apigateway create-rest-api \
  --name "${SERVICE_NAME}-api" \
  --description "P2 Service REST API - Complete" \
  --endpoint-configuration types=REGIONAL \
  --query 'id' \
  --output text)

echo "✅ REST API 생성 완료: $REST_API_ID"

# Root 리소스 ID
ROOT_ID=$(aws apigateway get-resources \
  --rest-api-id $REST_API_ID \
  --query 'items[?path==`/`].id' \
  --output text)

echo "✅ Root 리소스: $ROOT_ID"

# 2. 리소스 생성
echo ""
echo "[2/10] 리소스 구조 생성..."

# /admin
echo "  Creating /admin..."
ADMIN_ID=$(aws apigateway create-resource \
  --rest-api-id $REST_API_ID \
  --parent-id $ROOT_ID \
  --path-part "admin" \
  --query 'id' \
  --output text)

# /admin/dashboard
echo "  Creating /admin/dashboard..."
ADMIN_DASHBOARD_ID=$(aws apigateway create-resource \
  --rest-api-id $REST_API_ID \
  --parent-id $ADMIN_ID \
  --path-part "dashboard" \
  --query 'id' \
  --output text)

# /admin/tenants
echo "  Creating /admin/tenants..."
ADMIN_TENANTS_ID=$(aws apigateway create-resource \
  --rest-api-id $REST_API_ID \
  --parent-id $ADMIN_ID \
  --path-part "tenants" \
  --query 'id' \
  --output text)

# /admin/usage
echo "  Creating /admin/usage..."
ADMIN_USAGE_ID=$(aws apigateway create-resource \
  --rest-api-id $REST_API_ID \
  --parent-id $ADMIN_ID \
  --path-part "usage" \
  --query 'id' \
  --output text)

# /admin/users
echo "  Creating /admin/users..."
ADMIN_USERS_ID=$(aws apigateway create-resource \
  --rest-api-id $REST_API_ID \
  --parent-id $ADMIN_ID \
  --path-part "users" \
  --query 'id' \
  --output text)

# /conversations
echo "  Creating /conversations..."
CONVERSATIONS_ID=$(aws apigateway create-resource \
  --rest-api-id $REST_API_ID \
  --parent-id $ROOT_ID \
  --path-part "conversations" \
  --query 'id' \
  --output text)

# /conversations/{conversationId}
echo "  Creating /conversations/{conversationId}..."
CONVERSATION_ID_ID=$(aws apigateway create-resource \
  --rest-api-id $REST_API_ID \
  --parent-id $CONVERSATIONS_ID \
  --path-part "{conversationId}" \
  --query 'id' \
  --output text)

# /prompts
echo "  Creating /prompts..."
PROMPTS_ID=$(aws apigateway create-resource \
  --rest-api-id $REST_API_ID \
  --parent-id $ROOT_ID \
  --path-part "prompts" \
  --query 'id' \
  --output text)

# /prompts/{promptId}
echo "  Creating /prompts/{promptId}..."
PROMPT_ID_ID=$(aws apigateway create-resource \
  --rest-api-id $REST_API_ID \
  --parent-id $PROMPTS_ID \
  --path-part "{promptId}" \
  --query 'id' \
  --output text)

# /prompts/{promptId}/files
echo "  Creating /prompts/{promptId}/files..."
PROMPT_FILES_ID=$(aws apigateway create-resource \
  --rest-api-id $REST_API_ID \
  --parent-id $PROMPT_ID_ID \
  --path-part "files" \
  --query 'id' \
  --output text)

# /prompts/{promptId}/files/{fileId}
echo "  Creating /prompts/{promptId}/files/{fileId}..."
PROMPT_FILE_ID_ID=$(aws apigateway create-resource \
  --rest-api-id $REST_API_ID \
  --parent-id $PROMPT_FILES_ID \
  --path-part "{fileId}" \
  --query 'id' \
  --output text)

# /transcribe
echo "  Creating /transcribe..."
TRANSCRIBE_ID=$(aws apigateway create-resource \
  --rest-api-id $REST_API_ID \
  --parent-id $ROOT_ID \
  --path-part "transcribe" \
  --query 'id' \
  --output text)

# /usage
echo "  Creating /usage..."
USAGE_ID=$(aws apigateway create-resource \
  --rest-api-id $REST_API_ID \
  --parent-id $ROOT_ID \
  --path-part "usage" \
  --query 'id' \
  --output text)

# /usage/{userId}
echo "  Creating /usage/{userId}..."
USAGE_USER_ID=$(aws apigateway create-resource \
  --rest-api-id $REST_API_ID \
  --parent-id $USAGE_ID \
  --path-part "{userId}" \
  --query 'id' \
  --output text)

# /usage/{userId}/{engineType}
echo "  Creating /usage/{userId}/{engineType}..."
USAGE_ENGINE_ID=$(aws apigateway create-resource \
  --rest-api-id $REST_API_ID \
  --parent-id $USAGE_USER_ID \
  --path-part "{engineType}" \
  --query 'id' \
  --output text)

# /usage/update - 사용량 업데이트 엔드포인트
echo "  Creating /usage/update..."
USAGE_UPDATE_ID=$(aws apigateway create-resource \
  --rest-api-id $REST_API_ID \
  --parent-id $USAGE_ID \
  --path-part "update" \
  --query 'id' \
  --output text)

echo "✅ 리소스 구조 생성 완료"

# 3. 메서드 생성 함수
create_lambda_method() {
    local RESOURCE_ID=$1
    local METHOD=$2
    local LAMBDA_NAME=$3
    local PATH_DESC=$4

    echo "  Adding $METHOD to $PATH_DESC..."

    # Method 생성
    aws apigateway put-method \
      --rest-api-id $REST_API_ID \
      --resource-id $RESOURCE_ID \
      --http-method $METHOD \
      --authorization-type NONE \
      --no-api-key-required > /dev/null

    # Integration 설정
    aws apigateway put-integration \
      --rest-api-id $REST_API_ID \
      --resource-id $RESOURCE_ID \
      --http-method $METHOD \
      --type AWS_PROXY \
      --integration-http-method POST \
      --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${LAMBDA_NAME}/invocations" > /dev/null

    # Method Response
    aws apigateway put-method-response \
      --rest-api-id $REST_API_ID \
      --resource-id $RESOURCE_ID \
      --http-method $METHOD \
      --status-code 200 \
      --response-parameters '{"method.response.header.Access-Control-Allow-Origin":false,"method.response.header.Access-Control-Allow-Headers":false,"method.response.header.Access-Control-Allow-Methods":false,"method.response.header.Access-Control-Allow-Credentials":false}' > /dev/null

    # Integration Response
    aws apigateway put-integration-response \
      --rest-api-id $REST_API_ID \
      --resource-id $RESOURCE_ID \
      --http-method $METHOD \
      --status-code 200 \
      --response-parameters '{"method.response.header.Access-Control-Allow-Origin":"'"'"'*'"'"'","method.response.header.Access-Control-Allow-Headers":"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'","method.response.header.Access-Control-Allow-Methods":"'"'"'GET,POST,PUT,DELETE,OPTIONS,PATCH'"'"'","method.response.header.Access-Control-Allow-Credentials":"'"'"'true'"'"'"}' > /dev/null
}

create_options_method() {
    local RESOURCE_ID=$1
    local PATH_DESC=$2

    echo "  Adding OPTIONS to $PATH_DESC..."

    # OPTIONS Method
    aws apigateway put-method \
      --rest-api-id $REST_API_ID \
      --resource-id $RESOURCE_ID \
      --http-method OPTIONS \
      --authorization-type NONE \
      --no-api-key-required > /dev/null

    # Mock Integration
    aws apigateway put-integration \
      --rest-api-id $REST_API_ID \
      --resource-id $RESOURCE_ID \
      --http-method OPTIONS \
      --type MOCK \
      --request-templates '{"application/json": "{\"statusCode\": 200}"}' > /dev/null

    # Method Response
    aws apigateway put-method-response \
      --rest-api-id $REST_API_ID \
      --resource-id $RESOURCE_ID \
      --http-method OPTIONS \
      --status-code 200 \
      --response-parameters '{"method.response.header.Access-Control-Allow-Origin":false,"method.response.header.Access-Control-Allow-Headers":false,"method.response.header.Access-Control-Allow-Methods":false,"method.response.header.Access-Control-Allow-Credentials":false}' > /dev/null

    # Integration Response
    aws apigateway put-integration-response \
      --rest-api-id $REST_API_ID \
      --resource-id $RESOURCE_ID \
      --http-method OPTIONS \
      --status-code 200 \
      --response-parameters '{"method.response.header.Access-Control-Allow-Origin":"'"'"'*'"'"'","method.response.header.Access-Control-Allow-Headers":"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'","method.response.header.Access-Control-Allow-Methods":"'"'"'GET,POST,PUT,DELETE,OPTIONS,PATCH'"'"'","method.response.header.Access-Control-Allow-Credentials":"'"'"'true'"'"'"}' > /dev/null
}

# 4. 메서드 추가
echo ""
echo "[3/10] 메서드 추가..."

# Admin endpoints
create_lambda_method $ADMIN_DASHBOARD_ID "GET" $LAMBDA_PROMPTS "/admin/dashboard"
create_lambda_method $ADMIN_DASHBOARD_ID "PUT" $LAMBDA_PROMPTS "/admin/dashboard"
create_options_method $ADMIN_DASHBOARD_ID "/admin/dashboard"

create_lambda_method $ADMIN_TENANTS_ID "GET" $LAMBDA_PROMPTS "/admin/tenants"
create_lambda_method $ADMIN_TENANTS_ID "PUT" $LAMBDA_PROMPTS "/admin/tenants"
create_options_method $ADMIN_TENANTS_ID "/admin/tenants"

create_lambda_method $ADMIN_USAGE_ID "GET" $LAMBDA_PROMPTS "/admin/usage"
create_lambda_method $ADMIN_USAGE_ID "PUT" $LAMBDA_PROMPTS "/admin/usage"
create_options_method $ADMIN_USAGE_ID "/admin/usage"

create_lambda_method $ADMIN_USERS_ID "GET" $LAMBDA_PROMPTS "/admin/users"
create_lambda_method $ADMIN_USERS_ID "PUT" $LAMBDA_PROMPTS "/admin/users"
create_options_method $ADMIN_USERS_ID "/admin/users"

# Conversations endpoints
create_lambda_method $CONVERSATIONS_ID "GET" $LAMBDA_CONVERSATIONS "/conversations"
create_lambda_method $CONVERSATIONS_ID "POST" $LAMBDA_CONVERSATIONS "/conversations"
create_lambda_method $CONVERSATIONS_ID "PUT" $LAMBDA_CONVERSATIONS "/conversations"
create_options_method $CONVERSATIONS_ID "/conversations"

create_lambda_method $CONVERSATION_ID_ID "GET" $LAMBDA_CONVERSATIONS "/conversations/{conversationId}"
create_lambda_method $CONVERSATION_ID_ID "PUT" $LAMBDA_CONVERSATIONS "/conversations/{conversationId}"
create_lambda_method $CONVERSATION_ID_ID "DELETE" $LAMBDA_CONVERSATIONS "/conversations/{conversationId}"
create_lambda_method $CONVERSATION_ID_ID "PATCH" $LAMBDA_CONVERSATIONS "/conversations/{conversationId}"
create_options_method $CONVERSATION_ID_ID "/conversations/{conversationId}"

# Prompts endpoints
create_lambda_method $PROMPTS_ID "GET" $LAMBDA_PROMPTS "/prompts"
create_lambda_method $PROMPTS_ID "POST" $LAMBDA_PROMPTS "/prompts"
create_options_method $PROMPTS_ID "/prompts"

create_lambda_method $PROMPT_ID_ID "GET" $LAMBDA_PROMPTS "/prompts/{promptId}"
create_lambda_method $PROMPT_ID_ID "POST" $LAMBDA_PROMPTS "/prompts/{promptId}"
create_lambda_method $PROMPT_ID_ID "PUT" $LAMBDA_PROMPTS "/prompts/{promptId}"
create_options_method $PROMPT_ID_ID "/prompts/{promptId}"

create_lambda_method $PROMPT_FILES_ID "GET" $LAMBDA_PROMPTS "/prompts/{promptId}/files"
create_lambda_method $PROMPT_FILES_ID "POST" $LAMBDA_PROMPTS "/prompts/{promptId}/files"
create_options_method $PROMPT_FILES_ID "/prompts/{promptId}/files"

create_lambda_method $PROMPT_FILE_ID_ID "GET" $LAMBDA_PROMPTS "/prompts/{promptId}/files/{fileId}"
create_lambda_method $PROMPT_FILE_ID_ID "PUT" $LAMBDA_PROMPTS "/prompts/{promptId}/files/{fileId}"
create_lambda_method $PROMPT_FILE_ID_ID "DELETE" $LAMBDA_PROMPTS "/prompts/{promptId}/files/{fileId}"
create_options_method $PROMPT_FILE_ID_ID "/prompts/{promptId}/files/{fileId}"

# Transcribe endpoint
create_lambda_method $TRANSCRIBE_ID "POST" $LAMBDA_CONVERSATIONS "/transcribe"
create_options_method $TRANSCRIBE_ID "/transcribe"

# Usage endpoints
create_lambda_method $USAGE_ID "GET" $LAMBDA_USAGE "/usage"
create_lambda_method $USAGE_ID "POST" $LAMBDA_USAGE "/usage"
create_options_method $USAGE_ID "/usage"

create_lambda_method $USAGE_ENGINE_ID "GET" $LAMBDA_USAGE "/usage/{userId}/{engineType}"
create_lambda_method $USAGE_ENGINE_ID "POST" $LAMBDA_USAGE "/usage/{userId}/{engineType}"
create_options_method $USAGE_ENGINE_ID "/usage/{userId}/{engineType}"

# /usage/update endpoint
create_lambda_method $USAGE_UPDATE_ID "POST" $LAMBDA_USAGE "/usage/update"
create_options_method $USAGE_UPDATE_ID "/usage/update"

echo "✅ 메서드 추가 완료"

# 5. Lambda 권한 추가
echo ""
echo "[4/10] Lambda 권한 설정..."

for LAMBDA in $LAMBDA_CONVERSATIONS $LAMBDA_PROMPTS $LAMBDA_USAGE; do
    echo "  Setting permission for $LAMBDA..."

    # 기존 권한 제거
    aws lambda remove-permission \
      --function-name $LAMBDA \
      --statement-id "apigateway-${REST_API_ID}" \
      2>/dev/null || true

    # 새 권한 추가
    aws lambda add-permission \
      --function-name $LAMBDA \
      --statement-id "apigateway-${REST_API_ID}" \
      --action lambda:InvokeFunction \
      --principal apigateway.amazonaws.com \
      --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${REST_API_ID}/*/*" > /dev/null
done

echo "✅ Lambda 권한 설정 완료"

# 6. REST API 배포
echo ""
echo "[5/10] REST API 배포..."

aws apigateway create-deployment \
  --rest-api-id $REST_API_ID \
  --stage-name prod \
  --description "Complete deployment with all endpoints" > /dev/null

echo "✅ REST API 배포 완료"

# 7. WebSocket API 생성
echo ""
echo "[6/10] WebSocket API 생성..."

WS_API_ID=$(aws apigatewayv2 create-api \
  --name "p2-two-websocket-api-${CARD_COUNT}" \
  --protocol-type WEBSOCKET \
  --route-selection-expression '$request.body.action' \
  --query 'ApiId' \
  --output text)

echo "✅ WebSocket API 생성 완료: $WS_API_ID"

# 8. WebSocket 통합 생성
echo ""
echo "[7/10] WebSocket 통합 설정..."

# Connect route
WS_CONNECT_LAMBDA="p2-two-websocket-connect-${CARD_COUNT}"
CONNECT_INT_ID=$(aws apigatewayv2 create-integration \
  --api-id $WS_API_ID \
  --integration-type AWS_PROXY \
  --integration-uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${WS_CONNECT_LAMBDA}/invocations" \
  --query 'IntegrationId' \
  --output text)

aws apigatewayv2 create-route \
  --api-id $WS_API_ID \
  --route-key '$connect' \
  --target "integrations/${CONNECT_INT_ID}" > /dev/null

# Disconnect route
WS_DISCONNECT_LAMBDA="p2-two-websocket-disconnect-${CARD_COUNT}"
DISCONNECT_INT_ID=$(aws apigatewayv2 create-integration \
  --api-id $WS_API_ID \
  --integration-type AWS_PROXY \
  --integration-uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${WS_DISCONNECT_LAMBDA}/invocations" \
  --query 'IntegrationId' \
  --output text)

aws apigatewayv2 create-route \
  --api-id $WS_API_ID \
  --route-key '$disconnect' \
  --target "integrations/${DISCONNECT_INT_ID}" > /dev/null

# Default route
WS_MESSAGE_LAMBDA="p2-two-websocket-message-${CARD_COUNT}"
MESSAGE_INT_ID=$(aws apigatewayv2 create-integration \
  --api-id $WS_API_ID \
  --integration-type AWS_PROXY \
  --integration-uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${WS_MESSAGE_LAMBDA}/invocations" \
  --query 'IntegrationId' \
  --output text)

aws apigatewayv2 create-route \
  --api-id $WS_API_ID \
  --route-key '$default' \
  --target "integrations/${MESSAGE_INT_ID}" > /dev/null

echo "✅ WebSocket 통합 설정 완료"

# 9. WebSocket Lambda 권한
echo ""
echo "[8/10] WebSocket Lambda 권한 설정..."

for LAMBDA in $WS_CONNECT_LAMBDA $WS_DISCONNECT_LAMBDA $WS_MESSAGE_LAMBDA; do
    aws lambda remove-permission \
      --function-name $LAMBDA \
      --statement-id "websocket-${WS_API_ID}" \
      2>/dev/null || true

    aws lambda add-permission \
      --function-name $LAMBDA \
      --statement-id "websocket-${WS_API_ID}" \
      --action lambda:InvokeFunction \
      --principal apigateway.amazonaws.com \
      --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${WS_API_ID}/*/*" > /dev/null
done

echo "✅ WebSocket Lambda 권한 설정 완료"

# 10. WebSocket API 배포
echo ""
echo "[9/10] WebSocket API 배포..."

DEPLOYMENT_ID=$(aws apigatewayv2 create-deployment \
  --api-id $WS_API_ID \
  --query 'DeploymentId' \
  --output text)

aws apigatewayv2 create-stage \
  --api-id $WS_API_ID \
  --stage-name prod \
  --deployment-id $DEPLOYMENT_ID > /dev/null

echo "✅ WebSocket API 배포 완료"

# 11. API 스펙 내보내기
echo ""
echo "[10/10] API 스펙 내보내기..."

aws apigateway get-export \
  --rest-api-id $REST_API_ID \
  --stage-name prod \
  --export-type swagger \
  p2-api-spec-final.json 2>/dev/null || echo "  (스펙 내보내기 생략)"

# 12. 결과 저장
DEPLOYMENT_INFO="deployment-info.txt"

cat > $DEPLOYMENT_INFO << EOF

========================================
✅ API Gateway 배포 완료!
========================================
생성 시간: $(date '+%Y년 %m월 %d일 %H시 %M분 %S초 KST')
스택: $STACK_NAME

REST API:
  - ID: $REST_API_ID
  - Endpoint: https://$REST_API_ID.execute-api.us-east-1.amazonaws.com/prod
  - 총 13개 경로, 33개 메서드

WebSocket API:
  - ID: $WS_API_ID
  - Endpoint: wss://$WS_API_ID.execute-api.us-east-1.amazonaws.com/prod
  - 3개 라우트 ($connect, $disconnect, $default)

다음 단계:
  1. 설정 업데이트: ./04-update-config.sh
  2. Lambda 코드 배포: ./05-deploy-lambda-code.sh
  3. 프론트엔드 배포: ./06-deploy-frontend.sh
========================================
EOF

# 최종 결과 출력
echo ""
echo "=========================================="
echo "✅ 모든 배포 완료!"
echo "=========================================="
echo ""
echo "REST API Endpoint:"
echo "  https://$REST_API_ID.execute-api.us-east-1.amazonaws.com/prod"
echo ""
echo "WebSocket API Endpoint:"
echo "  wss://$WS_API_ID.execute-api.us-east-1.amazonaws.com/prod"
echo ""
echo "배포 정보가 $DEPLOYMENT_INFO 에 저장되었습니다."
echo "=========================================="