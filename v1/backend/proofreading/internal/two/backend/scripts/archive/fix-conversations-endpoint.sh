#!/bin/bash

# Conversations 엔드포인트 수정 스크립트

set -e

API_ID="wxwdb89w4m"
REGION="us-east-1"
STAGE="prod"
LAMBDA_ARN="arn:aws:lambda:us-east-1:887078546492:function:nx-wt-prf-conversation-handler"

echo "=========================================="
echo "Conversations 엔드포인트 설정"
echo "=========================================="

# 1. /conversations/{id} 리소스 ID 가져오기
CONV_ID_RESOURCE=$(aws apigateway get-resources \
    --rest-api-id ${API_ID} \
    --region ${REGION} \
    --query "items[?path=='/conversations/{id}'].id" \
    --output text)

echo "1. /conversations/{id} 리소스 ID: ${CONV_ID_RESOURCE}"

# 2. GET 메서드 추가
echo "2. GET 메서드 추가..."
aws apigateway put-method \
    --rest-api-id ${API_ID} \
    --resource-id ${CONV_ID_RESOURCE} \
    --http-method GET \
    --authorization-type NONE \
    --request-parameters "method.request.querystring.userId=false" \
    --region ${REGION} \
    --no-cli-pager || true

# 3. Lambda Integration 설정
echo "3. Lambda Integration 설정..."
aws apigateway put-integration \
    --rest-api-id ${API_ID} \
    --resource-id ${CONV_ID_RESOURCE} \
    --http-method GET \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" \
    --region ${REGION} \
    --no-cli-pager || true

# 4. Method Response 설정 (CORS 헤더 포함)
echo "4. Method Response 설정..."
aws apigateway put-method-response \
    --rest-api-id ${API_ID} \
    --resource-id ${CONV_ID_RESOURCE} \
    --http-method GET \
    --status-code 200 \
    --response-parameters '{
        "method.response.header.Access-Control-Allow-Origin": false,
        "method.response.header.Access-Control-Allow-Headers": false,
        "method.response.header.Access-Control-Allow-Methods": false
    }' \
    --region ${REGION} \
    --no-cli-pager || true

# 5. OPTIONS 메서드 재설정
echo "5. OPTIONS 메서드 CORS 설정..."
aws apigateway put-integration-response \
    --rest-api-id ${API_ID} \
    --resource-id ${CONV_ID_RESOURCE} \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{
        "method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'\''",
        "method.response.header.Access-Control-Allow-Methods": "'\''GET,OPTIONS'\''",
        "method.response.header.Access-Control-Allow-Origin": "'\''*'\''"
    }' \
    --response-templates '{"application/json": ""}' \
    --region ${REGION} \
    --no-cli-pager || true

# 6. Lambda 권한 추가
echo "6. Lambda 실행 권한 추가..."
aws lambda add-permission \
    --function-name nx-wt-prf-conversation-handler \
    --statement-id "apigateway-conv-get-${CONV_ID_RESOURCE}" \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:${REGION}:887078546492:${API_ID}/*/GET/conversations/{id}" \
    --region ${REGION} \
    --no-cli-pager 2>/dev/null || true

echo "   ✓ 설정 완료"

# 7. WebSocket Lambda 함수 확인
echo -e "\n7. WebSocket Lambda 함수 상태 확인..."
aws lambda get-function \
    --function-name nx-wt-prf-message-handler \
    --region ${REGION} \
    --query 'Configuration.[FunctionName, State, LastModified, Runtime, Handler]' \
    --output table || echo "WebSocket Lambda not found"

# 8. API 배포
echo -e "\n8. API 배포..."
DEPLOYMENT_ID=$(aws apigateway create-deployment \
    --rest-api-id ${API_ID} \
    --stage-name ${STAGE} \
    --description "Fix conversations endpoint $(date +%Y-%m-%d_%H:%M:%S)" \
    --region ${REGION} \
    --query 'id' \
    --output text)

echo "   ✓ 배포 완료 (Deployment ID: ${DEPLOYMENT_ID})"

echo "=========================================="
echo "✅ Conversations 엔드포인트 설정 완료!"
echo "=========================================="