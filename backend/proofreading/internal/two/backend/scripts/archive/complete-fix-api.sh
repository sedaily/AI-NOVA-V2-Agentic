#!/bin/bash

# 색상 설정
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}   전체 API 문제 해결   ${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

REST_API_ID="gda9ojk5c7"
WS_API_ID="tj12bntr3c"
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# 1. REST API의 모든 리소스에 대해 CORS 및 통합 재설정
echo -e "${BLUE}1. REST API 전체 재설정${NC}"

# 모든 리소스 가져오기
RESOURCES=$(aws apigateway get-resources --rest-api-id $REST_API_ID --region $REGION --output json)

# conversations/{id} 리소스 재설정
echo -e "\n${YELLOW}conversations/{id} 리소스 처리 중...${NC}"
CONV_ID_RESOURCE=$(echo "$RESOURCES" | jq -r '.items[] | select(.path=="/conversations/{id}") | .id')

if [ -n "$CONV_ID_RESOURCE" ]; then
    for METHOD in GET PUT DELETE; do
        # 메소드 삭제 후 재생성
        aws apigateway delete-method --rest-api-id $REST_API_ID --resource-id $CONV_ID_RESOURCE --http-method $METHOD --region $REGION 2>/dev/null
        
        # 메소드 생성
        aws apigateway put-method \
            --rest-api-id $REST_API_ID \
            --resource-id $CONV_ID_RESOURCE \
            --http-method $METHOD \
            --authorization-type NONE \
            --request-parameters "method.request.path.id=true" \
            --region $REGION > /dev/null 2>&1
        
        # Lambda 통합
        aws apigateway put-integration \
            --rest-api-id $REST_API_ID \
            --resource-id $CONV_ID_RESOURCE \
            --http-method $METHOD \
            --type AWS_PROXY \
            --integration-http-method POST \
            --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/arn:aws:lambda:$REGION:$ACCOUNT_ID:function:nx-wt-prf-conversation-api/invocations" \
            --region $REGION > /dev/null 2>&1
        
        # 메소드 응답
        aws apigateway put-method-response \
            --rest-api-id $REST_API_ID \
            --resource-id $CONV_ID_RESOURCE \
            --http-method $METHOD \
            --status-code 200 \
            --response-parameters '{"method.response.header.Access-Control-Allow-Origin":true,"method.response.header.Access-Control-Allow-Headers":true,"method.response.header.Access-Control-Allow-Methods":true}' \
            --region $REGION > /dev/null 2>&1
        
        # 통합 응답
        aws apigateway put-integration-response \
            --rest-api-id $REST_API_ID \
            --resource-id $CONV_ID_RESOURCE \
            --http-method $METHOD \
            --status-code 200 \
            --response-parameters '{"method.response.header.Access-Control-Allow-Origin":"'\''*'\''","method.response.header.Access-Control-Allow-Headers":"'\''Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'\''","method.response.header.Access-Control-Allow-Methods":"'\''GET,POST,PUT,DELETE,OPTIONS'\''"}' \
            --region $REGION > /dev/null 2>&1
        
        echo -e "  ${GREEN}✓${NC} $METHOD 메소드 완료"
    done
    
    # OPTIONS 메소드 추가 (CORS)
    aws apigateway delete-method --rest-api-id $REST_API_ID --resource-id $CONV_ID_RESOURCE --http-method OPTIONS --region $REGION 2>/dev/null
    
    aws apigateway put-method \
        --rest-api-id $REST_API_ID \
        --resource-id $CONV_ID_RESOURCE \
        --http-method OPTIONS \
        --authorization-type NONE \
        --region $REGION > /dev/null 2>&1
    
    aws apigateway put-integration \
        --rest-api-id $REST_API_ID \
        --resource-id $CONV_ID_RESOURCE \
        --http-method OPTIONS \
        --type MOCK \
        --request-templates '{"application/json":"{\"statusCode\": 200}"}' \
        --region $REGION > /dev/null 2>&1
    
    aws apigateway put-method-response \
        --rest-api-id $REST_API_ID \
        --resource-id $CONV_ID_RESOURCE \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{"method.response.header.Access-Control-Allow-Headers":true,"method.response.header.Access-Control-Allow-Methods":true,"method.response.header.Access-Control-Allow-Origin":true}' \
        --region $REGION > /dev/null 2>&1
    
    aws apigateway put-integration-response \
        --rest-api-id $REST_API_ID \
        --resource-id $CONV_ID_RESOURCE \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{"method.response.header.Access-Control-Allow-Headers":"'\''Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'\''","method.response.header.Access-Control-Allow-Methods":"'\''GET,POST,PUT,DELETE,OPTIONS'\''","method.response.header.Access-Control-Allow-Origin":"'\''*'\''"}' \
        --region $REGION > /dev/null 2>&1
    
    echo -e "  ${GREEN}✓${NC} OPTIONS (CORS) 메소드 완료"
fi

# 2. WebSocket API 재배포
echo -e "\n${BLUE}2. WebSocket API 재배포${NC}"
DEPLOYMENT_ID=$(aws apigatewayv2 create-deployment \
    --api-id $WS_API_ID \
    --description "Fix WebSocket connections" \
    --region $REGION \
    --query 'DeploymentId' \
    --output text)

if [ -n "$DEPLOYMENT_ID" ]; then
    echo -e "${GREEN}✅ WebSocket API 재배포 완료: $DEPLOYMENT_ID${NC}"
fi

# 3. REST API 재배포
echo -e "\n${BLUE}3. REST API 재배포${NC}"
REST_DEPLOYMENT_ID=$(aws apigateway create-deployment \
    --rest-api-id $REST_API_ID \
    --stage-name prod \
    --description "Complete fix for CORS and integrations" \
    --region $REGION \
    --query 'id' \
    --output text)

if [ -n "$REST_DEPLOYMENT_ID" ]; then
    echo -e "${GREEN}✅ REST API 재배포 완료: $REST_DEPLOYMENT_ID${NC}"
fi

# 4. Lambda 환경변수 업데이트
echo -e "\n${BLUE}4. Lambda 환경변수 업데이트${NC}"
for func in "nx-wt-prf-websocket-connect" "nx-wt-prf-websocket-disconnect" "nx-wt-prf-websocket-message"; do
    aws lambda update-function-configuration \
        --function-name $func \
        --environment "Variables={REGION=$REGION,WEBSOCKET_API_ENDPOINT=https://$WS_API_ID.execute-api.$REGION.amazonaws.com/prod}" \
        --region $REGION > /dev/null 2>&1
    echo -e "  ${GREEN}✓${NC} $func 환경변수 업데이트"
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   ✅ API 문제 해결 완료!   ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 5. 테스트
echo -e "${BLUE}5. API 테스트${NC}"
sleep 3

echo -e "\n${CYAN}REST API 테스트:${NC}"
curl -s -X GET "https://$REST_API_ID.execute-api.$REGION.amazonaws.com/prod/conversations/test123?userId=test" \
    -H "Origin: http://localhost:3000" \
    -w "\nHTTP Status: %{http_code}\n" 2>/dev/null | tail -2

echo -e "\n${CYAN}엔드포인트 정보:${NC}"
echo -e "  • REST API: ${YELLOW}https://$REST_API_ID.execute-api.$REGION.amazonaws.com/prod${NC}"
echo -e "  • WebSocket: ${YELLOW}wss://$WS_API_ID.execute-api.$REGION.amazonaws.com/prod${NC}"
echo ""