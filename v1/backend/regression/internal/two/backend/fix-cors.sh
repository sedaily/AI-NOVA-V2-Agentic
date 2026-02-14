#!/bin/bash

# API Gateway CORS 설정 스크립트
API_ID="t75vorhge1"
REGION="us-east-1"

echo "Fixing CORS for API Gateway: $API_ID"

# 리소스 ID 가져오기
RESOURCES=$(aws apigateway get-resources --rest-api-id $API_ID --region $REGION --output json)

# prompts 리소스 ID
PROMPTS_ID=$(echo $RESOURCES | jq -r '.items[] | select(.pathPart=="prompts") | .id')
# conversations 리소스 ID
CONV_ID=$(echo $RESOURCES | jq -r '.items[] | select(.pathPart=="conversations") | .id')
# usage 리소스 ID
USAGE_ID=$(echo $RESOURCES | jq -r '.items[] | select(.pathPart=="usage") | .id')

echo "Resource IDs:"
echo "  Prompts: $PROMPTS_ID"
echo "  Conversations: $CONV_ID"
echo "  Usage: $USAGE_ID"

# OPTIONS 메소드 추가/업데이트 함수
add_cors_options() {
    local RESOURCE_ID=$1
    local RESOURCE_NAME=$2

    echo "Adding CORS OPTIONS to $RESOURCE_NAME..."

    # OPTIONS 메소드 삭제 (있으면)
    aws apigateway delete-method \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --region $REGION 2>/dev/null || true

    # OPTIONS 메소드 추가
    aws apigateway put-method \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --authorization-type NONE \
        --region $REGION

    # OPTIONS 응답 설정
    aws apigateway put-method-response \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{"method.response.header.Access-Control-Allow-Origin":true,"method.response.header.Access-Control-Allow-Headers":true,"method.response.header.Access-Control-Allow-Methods":true,"method.response.header.Access-Control-Allow-Credentials":true}' \
        --region $REGION

    # OPTIONS 통합 설정 (MOCK)
    aws apigateway put-integration \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --type MOCK \
        --request-templates '{"application/json":"{\"statusCode\": 200}"}' \
        --region $REGION

    # OPTIONS 통합 응답 설정
    aws apigateway put-integration-response \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{"method.response.header.Access-Control-Allow-Origin":"'"'"'*'"'"'","method.response.header.Access-Control-Allow-Headers":"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'","method.response.header.Access-Control-Allow-Methods":"'"'"'GET,POST,PUT,DELETE,OPTIONS,PATCH'"'"'","method.response.header.Access-Control-Allow-Credentials":"'"'"'true'"'"'"}' \
        --region $REGION

    echo "  ✅ CORS OPTIONS added to $RESOURCE_NAME"
}

# 각 리소스에 CORS 추가
add_cors_options $PROMPTS_ID "prompts"
add_cors_options $CONV_ID "conversations"
add_cors_options $USAGE_ID "usage"

# {proxy+} 리소스 확인 및 추가
echo ""
echo "Checking for proxy resources..."

# prompts/{proxy+} 찾기 또는 생성
PROMPTS_PROXY_ID=$(echo $RESOURCES | jq -r '.items[] | select(.pathPart=="{proxy+}" and .parentId=="'$PROMPTS_ID'") | .id' | head -1)

if [ -z "$PROMPTS_PROXY_ID" ] || [ "$PROMPTS_PROXY_ID" = "null" ]; then
    echo "Creating prompts/{proxy+} resource..."
    PROMPTS_PROXY_ID=$(aws apigateway create-resource \
        --rest-api-id $API_ID \
        --parent-id $PROMPTS_ID \
        --path-part "{proxy+}" \
        --region $REGION \
        --query 'id' --output text)
    echo "  Created: $PROMPTS_PROXY_ID"
fi

# prompts/{proxy+}에도 OPTIONS 추가
if [ -n "$PROMPTS_PROXY_ID" ] && [ "$PROMPTS_PROXY_ID" != "null" ]; then
    add_cors_options $PROMPTS_PROXY_ID "prompts/{proxy+}"

    # ANY 메소드 추가 (Lambda 프록시)
    echo "Adding ANY method to prompts/{proxy+}..."

    aws apigateway put-method \
        --rest-api-id $API_ID \
        --resource-id $PROMPTS_PROXY_ID \
        --http-method ANY \
        --authorization-type NONE \
        --region $REGION 2>/dev/null || true

    aws apigateway put-integration \
        --rest-api-id $API_ID \
        --resource-id $PROMPTS_PROXY_ID \
        --http-method ANY \
        --type AWS_PROXY \
        --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:${REGION}:887078546492:function:sedaily-column-prompt-crud/invocations" \
        --integration-http-method POST \
        --region $REGION 2>/dev/null || true

    echo "  ✅ ANY method added"
fi

# API 배포
echo ""
echo "Deploying API..."
aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name prod \
    --region $REGION \
    --output text

echo ""
echo "✅ CORS configuration complete!"
echo ""
echo "Testing CORS..."
curl -I -X OPTIONS https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod/prompts 2>/dev/null | grep -i "access-control"