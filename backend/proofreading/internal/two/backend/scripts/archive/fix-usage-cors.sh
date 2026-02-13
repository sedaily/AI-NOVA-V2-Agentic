#!/bin/bash

# usage/update CORS 설정 수정 스크립트

set -e

API_ID="wxwdb89w4m"
REGION="us-east-1"
STAGE="prod"

echo "=========================================="
echo "Usage 엔드포인트 CORS 설정"
echo "=========================================="

# /usage/update 리소스 찾기
echo "1. /usage/update 리소스 확인..."
USAGE_UPDATE_RESOURCE=$(aws apigateway get-resources --rest-api-id ${API_ID} --region ${REGION} --query "items[?path=='/usage/update'].id" --output text)

if [ ! -z "$USAGE_UPDATE_RESOURCE" ]; then
    echo "   리소스 ID: $USAGE_UPDATE_RESOURCE"
    
    # OPTIONS 메서드 추가
    echo "2. OPTIONS 메서드 추가..."
    aws apigateway put-method \
        --rest-api-id ${API_ID} \
        --resource-id ${USAGE_UPDATE_RESOURCE} \
        --http-method OPTIONS \
        --authorization-type NONE \
        --region ${REGION} \
        --no-cli-pager 2>/dev/null || echo "   OPTIONS method already exists"
    
    # OPTIONS Integration (Mock)
    aws apigateway put-integration \
        --rest-api-id ${API_ID} \
        --resource-id ${USAGE_UPDATE_RESOURCE} \
        --http-method OPTIONS \
        --type MOCK \
        --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
        --region ${REGION} \
        --no-cli-pager 2>/dev/null || true
    
    # OPTIONS Method Response
    aws apigateway put-method-response \
        --rest-api-id ${API_ID} \
        --resource-id ${USAGE_UPDATE_RESOURCE} \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{
            "method.response.header.Access-Control-Allow-Headers": false,
            "method.response.header.Access-Control-Allow-Methods": false,
            "method.response.header.Access-Control-Allow-Origin": false
        }' \
        --region ${REGION} \
        --no-cli-pager 2>/dev/null || true
    
    # OPTIONS Integration Response
    aws apigateway put-integration-response \
        --rest-api-id ${API_ID} \
        --resource-id ${USAGE_UPDATE_RESOURCE} \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{
            "method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'\''",
            "method.response.header.Access-Control-Allow-Methods": "'\''POST,OPTIONS'\''",
            "method.response.header.Access-Control-Allow-Origin": "'\''*'\''"
        }' \
        --response-templates '{"application/json": ""}' \
        --region ${REGION} \
        --no-cli-pager 2>/dev/null || true
    
    echo "   ✓ OPTIONS 메서드 설정 완료"
    
    # POST 메서드 CORS 헤더 추가
    echo "3. POST 메서드 CORS 헤더 추가..."
    aws apigateway put-method-response \
        --rest-api-id ${API_ID} \
        --resource-id ${USAGE_UPDATE_RESOURCE} \
        --http-method POST \
        --status-code 200 \
        --response-parameters '{
            "method.response.header.Access-Control-Allow-Origin": false
        }' \
        --region ${REGION} \
        --no-cli-pager 2>/dev/null || true
    
    echo "   ✓ POST 메서드 CORS 설정 완료"
else
    echo "   ⚠️  /usage/update 리소스를 찾을 수 없습니다"
fi

# API 배포
echo ""
echo "4. API 재배포..."
DEPLOYMENT_ID=$(aws apigateway create-deployment \
    --rest-api-id ${API_ID} \
    --stage-name ${STAGE} \
    --description "Fix usage CORS $(date +%Y-%m-%d_%H:%M:%S)" \
    --region ${REGION} \
    --query 'id' \
    --output text)

echo "   ✓ 배포 완료 (Deployment ID: ${DEPLOYMENT_ID})"

echo ""
echo "=========================================="
echo "✅ Usage CORS 설정 완료!"
echo "=========================================="