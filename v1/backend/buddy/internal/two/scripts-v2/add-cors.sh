#!/bin/bash
REST_API_ID="71eh2lfh7l"
REGION="us-east-1"

# 모든 리소스 가져오기
RESOURCES=$(aws apigateway get-resources --rest-api-id $REST_API_ID --query 'items[*].id' --output text)

for resource_id in $RESOURCES; do
    echo "Adding CORS to resource: $resource_id"
    
    # OPTIONS 메소드 추가
    aws apigateway put-method \
        --rest-api-id $REST_API_ID \
        --resource-id $resource_id \
        --http-method OPTIONS \
        --authorization-type NONE \
        --region $REGION 2>/dev/null || true
    
    # MOCK 통합 추가
    aws apigateway put-integration \
        --rest-api-id $REST_API_ID \
        --resource-id $resource_id \
        --http-method OPTIONS \
        --type MOCK \
        --request-templates '{"application/json":"{\"statusCode\":200}"}' \
        --region $REGION 2>/dev/null || true
    
    # Integration Response 추가
    aws apigateway put-integration-response \
        --rest-api-id $REST_API_ID \
        --resource-id $resource_id \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{"method.response.header.Access-Control-Allow-Headers":"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'","method.response.header.Access-Control-Allow-Methods":"'"'"'GET,POST,PUT,DELETE,OPTIONS'"'"'","method.response.header.Access-Control-Allow-Origin":"'"'"'*'"'"'}' \
        --region $REGION 2>/dev/null || true
    
    # Method Response 추가
    aws apigateway put-method-response \
        --rest-api-id $REST_API_ID \
        --resource-id $resource_id \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{"method.response.header.Access-Control-Allow-Headers":false,"method.response.header.Access-Control-Allow-Methods":false,"method.response.header.Access-Control-Allow-Origin":false}' \
        --region $REGION 2>/dev/null || true
done

echo "Deploying API..."
aws apigateway create-deployment \
    --rest-api-id $REST_API_ID \
    --stage-name prod \
    --region $REGION

echo "✅ CORS 설정 완료!"
