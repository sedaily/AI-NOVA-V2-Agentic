#!/bin/bash

# 모든 CORS 문제 해결 스크립트

set -e

API_ID="wxwdb89w4m"
REGION="us-east-1"
STAGE="prod"

echo "=========================================="
echo "전체 CORS 설정 수정"
echo "=========================================="

# 프롬프트 관련 엔드포인트
echo "1. /prompts/{promptId} 엔드포인트 설정..."
PROMPT_ID_RESOURCE=$(aws apigateway get-resources --rest-api-id ${API_ID} --region ${REGION} --query "items[?path=='/prompts/{promptId}'].id" --output text)

# GET 메서드
echo "   - GET 메서드 설정"
aws apigateway put-method \
    --rest-api-id ${API_ID} \
    --resource-id ${PROMPT_ID_RESOURCE} \
    --http-method GET \
    --authorization-type NONE \
    --region ${REGION} \
    --no-cli-pager > /dev/null 2>&1 || true

aws apigateway put-integration \
    --rest-api-id ${API_ID} \
    --resource-id ${PROMPT_ID_RESOURCE} \
    --http-method GET \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:887078546492:function:nx-wt-prf-prompt-crud/invocations" \
    --region ${REGION} \
    --no-cli-pager > /dev/null 2>&1 || true

aws apigateway put-method-response \
    --rest-api-id ${API_ID} \
    --resource-id ${PROMPT_ID_RESOURCE} \
    --http-method GET \
    --status-code 200 \
    --response-parameters '{
        "method.response.header.Access-Control-Allow-Origin": false,
        "method.response.header.Access-Control-Allow-Headers": false,
        "method.response.header.Access-Control-Allow-Methods": false
    }' \
    --region ${REGION} \
    --no-cli-pager > /dev/null 2>&1 || true

# PUT 메서드
echo "   - PUT 메서드 설정"
aws apigateway put-method-response \
    --rest-api-id ${API_ID} \
    --resource-id ${PROMPT_ID_RESOURCE} \
    --http-method PUT \
    --status-code 200 \
    --response-parameters '{
        "method.response.header.Access-Control-Allow-Origin": false,
        "method.response.header.Access-Control-Allow-Headers": false,
        "method.response.header.Access-Control-Allow-Methods": false
    }' \
    --region ${REGION} \
    --no-cli-pager > /dev/null 2>&1 || true

# OPTIONS 메서드 업데이트
echo "   - OPTIONS 메서드 업데이트"
aws apigateway put-integration-response \
    --rest-api-id ${API_ID} \
    --resource-id ${PROMPT_ID_RESOURCE} \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{
        "method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'\''",
        "method.response.header.Access-Control-Allow-Methods": "'\''GET,PUT,OPTIONS'\''",
        "method.response.header.Access-Control-Allow-Origin": "'\''*'\''"
    }' \
    --response-templates '{"application/json": ""}' \
    --region ${REGION} \
    --no-cli-pager > /dev/null 2>&1 || true

# 파일 관련 엔드포인트
echo "2. /prompts/{promptId}/files 엔드포인트 설정..."
FILES_RESOURCE=$(aws apigateway get-resources --rest-api-id ${API_ID} --region ${REGION} --query "items[?path=='/prompts/{promptId}/files'].id" --output text)

if [ ! -z "${FILES_RESOURCE}" ]; then
    # GET 메서드
    aws apigateway put-method \
        --rest-api-id ${API_ID} \
        --resource-id ${FILES_RESOURCE} \
        --http-method GET \
        --authorization-type NONE \
        --region ${REGION} \
        --no-cli-pager > /dev/null 2>&1 || true
    
    aws apigateway put-integration \
        --rest-api-id ${API_ID} \
        --resource-id ${FILES_RESOURCE} \
        --http-method GET \
        --type AWS_PROXY \
        --integration-http-method POST \
        --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:887078546492:function:nx-wt-prf-prompt-crud/invocations" \
        --region ${REGION} \
        --no-cli-pager > /dev/null 2>&1 || true
    
    # POST 메서드
    aws apigateway put-method \
        --rest-api-id ${API_ID} \
        --resource-id ${FILES_RESOURCE} \
        --http-method POST \
        --authorization-type NONE \
        --region ${REGION} \
        --no-cli-pager > /dev/null 2>&1 || true
    
    aws apigateway put-integration \
        --rest-api-id ${API_ID} \
        --resource-id ${FILES_RESOURCE} \
        --http-method POST \
        --type AWS_PROXY \
        --integration-http-method POST \
        --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:887078546492:function:nx-wt-prf-prompt-crud/invocations" \
        --region ${REGION} \
        --no-cli-pager > /dev/null 2>&1 || true
    
    echo "   ✓ Files 엔드포인트 설정 완료"
fi

# Lambda 권한 추가
echo "3. Lambda 실행 권한 추가..."
aws lambda add-permission \
    --function-name nx-wt-prf-prompt-crud \
    --statement-id apigateway-prompt-crud-all \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:${REGION}:887078546492:${API_ID}/*/*" \
    --region ${REGION} \
    --no-cli-pager > /dev/null 2>&1 || echo "   - 권한 이미 존재"

aws lambda add-permission \
    --function-name nx-wt-prf-conversation-handler \
    --statement-id apigateway-conversation-all \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:${REGION}:887078546492:${API_ID}/*/*" \
    --region ${REGION} \
    --no-cli-pager > /dev/null 2>&1 || echo "   - 권한 이미 존재"

# API 배포
echo "4. API 배포..."
DEPLOYMENT_ID=$(aws apigateway create-deployment \
    --rest-api-id ${API_ID} \
    --stage-name ${STAGE} \
    --description "Complete CORS fix $(date +%Y-%m-%d_%H:%M:%S)" \
    --region ${REGION} \
    --query 'id' \
    --output text)

echo "   ✓ 배포 완료 (Deployment ID: ${DEPLOYMENT_ID})"

# 테스트
echo ""
echo "5. CORS 테스트..."
echo "   테스트 GET: curl -X OPTIONS https://${API_ID}.execute-api.${REGION}.amazonaws.com/${STAGE}/prompts/T5 -I"
echo "   테스트 PUT: curl -X OPTIONS https://${API_ID}.execute-api.${REGION}.amazonaws.com/${STAGE}/prompts/T5 -I"

echo ""
echo "=========================================="
echo "✅ 전체 CORS 설정 완료!"
echo "API URL: https://${API_ID}.execute-api.${REGION}.amazonaws.com/${STAGE}"
echo "=========================================="