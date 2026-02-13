#!/bin/bash

# Usage 엔드포인트 및 CORS 설정 스크립트

set -e

API_ID="wxwdb89w4m"
REGION="us-east-1"
STAGE="prod"
LAMBDA_ARN="arn:aws:lambda:us-east-1:887078546492:function:nx-wt-prf-usage-handler"

echo "=========================================="
echo "Usage 엔드포인트 설정 시작"
echo "API ID: ${API_ID}"
echo "Region: ${REGION}"
echo "=========================================="

# 1. /usage 리소스 ID 가져오기
echo "1. 기존 /usage 리소스 확인..."
USAGE_RESOURCE_ID=$(aws apigateway get-resources \
    --rest-api-id ${API_ID} \
    --region ${REGION} \
    --query "items[?path=='/usage'].id" \
    --output text)

echo "   /usage 리소스 ID: ${USAGE_RESOURCE_ID}"

# 2. /usage/{userId} 리소스 생성
echo -e "\n2. /usage/{userId} 리소스 생성..."
USER_RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id ${API_ID} \
    --parent-id ${USAGE_RESOURCE_ID} \
    --path-part "{userId}" \
    --region ${REGION} \
    --query 'id' \
    --output text 2>/dev/null || \
    aws apigateway get-resources \
        --rest-api-id ${API_ID} \
        --region ${REGION} \
        --query "items[?path=='/usage/{userId}'].id" \
        --output text)

echo "   /usage/{userId} 리소스 ID: ${USER_RESOURCE_ID}"

# 3. /usage/{userId}/{engineType} 리소스 생성
echo -e "\n3. /usage/{userId}/{engineType} 리소스 생성..."
ENGINE_RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id ${API_ID} \
    --parent-id ${USER_RESOURCE_ID} \
    --path-part "{engineType}" \
    --region ${REGION} \
    --query 'id' \
    --output text 2>/dev/null || \
    aws apigateway get-resources \
        --rest-api-id ${API_ID} \
        --region ${REGION} \
        --query "items[?path=='/usage/{userId}/{engineType}'].id" \
        --output text)

echo "   /usage/{userId}/{engineType} 리소스 ID: ${ENGINE_RESOURCE_ID}"

# 4. GET 메서드 추가
echo -e "\n4. GET 메서드 설정..."
aws apigateway put-method \
    --rest-api-id ${API_ID} \
    --resource-id ${ENGINE_RESOURCE_ID} \
    --http-method GET \
    --authorization-type NONE \
    --region ${REGION} \
    --no-cli-pager > /dev/null 2>&1 || true

# 5. Lambda Integration 설정
echo "5. Lambda Integration 설정..."
aws apigateway put-integration \
    --rest-api-id ${API_ID} \
    --resource-id ${ENGINE_RESOURCE_ID} \
    --http-method GET \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" \
    --region ${REGION} \
    --no-cli-pager > /dev/null 2>&1 || true

# 6. OPTIONS 메서드 추가 (CORS)
echo -e "\n6. OPTIONS 메서드 추가..."
aws apigateway put-method \
    --rest-api-id ${API_ID} \
    --resource-id ${ENGINE_RESOURCE_ID} \
    --http-method OPTIONS \
    --authorization-type NONE \
    --region ${REGION} \
    --no-cli-pager > /dev/null 2>&1 || true

# 7. OPTIONS Mock Integration
aws apigateway put-integration \
    --rest-api-id ${API_ID} \
    --resource-id ${ENGINE_RESOURCE_ID} \
    --http-method OPTIONS \
    --type MOCK \
    --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
    --region ${REGION} \
    --no-cli-pager > /dev/null 2>&1 || true

# 8. OPTIONS Method Response
aws apigateway put-method-response \
    --rest-api-id ${API_ID} \
    --resource-id ${ENGINE_RESOURCE_ID} \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{
        "method.response.header.Access-Control-Allow-Headers": false,
        "method.response.header.Access-Control-Allow-Methods": false,
        "method.response.header.Access-Control-Allow-Origin": false
    }' \
    --region ${REGION} \
    --no-cli-pager > /dev/null 2>&1 || true

# 9. OPTIONS Integration Response
aws apigateway put-integration-response \
    --rest-api-id ${API_ID} \
    --resource-id ${ENGINE_RESOURCE_ID} \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{
        "method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'\''",
        "method.response.header.Access-Control-Allow-Methods": "'\''GET,OPTIONS'\''",
        "method.response.header.Access-Control-Allow-Origin": "'\''*'\''"
    }' \
    --response-templates '{"application/json": ""}' \
    --region ${REGION} \
    --no-cli-pager > /dev/null 2>&1 || true

echo "   ✓ OPTIONS 메서드 및 CORS 설정 완료"

# 10. GET Method Response에도 CORS 헤더 추가
echo -e "\n7. GET 메서드 CORS 헤더 추가..."
aws apigateway put-method-response \
    --rest-api-id ${API_ID} \
    --resource-id ${ENGINE_RESOURCE_ID} \
    --http-method GET \
    --status-code 200 \
    --response-parameters '{
        "method.response.header.Access-Control-Allow-Origin": false
    }' \
    --region ${REGION} \
    --no-cli-pager > /dev/null 2>&1 || true

# 11. Lambda 권한 추가
echo -e "\n8. Lambda 실행 권한 추가..."
aws lambda add-permission \
    --function-name nx-wt-prf-usage-handler \
    --statement-id "apigateway-usage-${ENGINE_RESOURCE_ID}" \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:${REGION}:887078546492:${API_ID}/*/GET/usage/{userId}/{engineType}" \
    --region ${REGION} \
    --no-cli-pager > /dev/null 2>&1 || true

# 12. /conversations/{id} 에도 CORS 설정
echo -e "\n9. /conversations/{id} CORS 설정..."
CONV_ID_RESOURCE=$(aws apigateway get-resources \
    --rest-api-id ${API_ID} \
    --region ${REGION} \
    --query "items[?path=='/conversations/{id}'].id" \
    --output text)

if [ ! -z "${CONV_ID_RESOURCE}" ]; then
    # GET 메서드에 CORS 헤더
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
        --no-cli-pager > /dev/null 2>&1 || true
    
    echo "   ✓ /conversations/{id} CORS 설정 완료"
fi

# 13. API 배포
echo -e "\n10. API 배포..."
DEPLOYMENT_ID=$(aws apigateway create-deployment \
    --rest-api-id ${API_ID} \
    --stage-name ${STAGE} \
    --description "Usage endpoint CORS fix $(date +%Y-%m-%d_%H:%M:%S)" \
    --region ${REGION} \
    --query 'id' \
    --output text)

echo "   ✓ 배포 완료 (Deployment ID: ${DEPLOYMENT_ID})"

# 14. 리소스 목록 확인
echo -e "\n=========================================="
echo "설정된 리소스 목록:"
aws apigateway get-resources \
    --rest-api-id ${API_ID} \
    --region ${REGION} \
    --query "items[?contains(path, 'usage') || contains(path, 'conversation')].[path, resourceMethods]" \
    --output table

echo "=========================================="
echo "✅ Usage 엔드포인트 CORS 설정 완료!"
echo "API Endpoint: https://${API_ID}.execute-api.${REGION}.amazonaws.com/${STAGE}"
echo "=========================================="