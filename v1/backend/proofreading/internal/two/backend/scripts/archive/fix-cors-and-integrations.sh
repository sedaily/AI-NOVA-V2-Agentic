#!/bin/bash

# 색상 설정
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}   API Gateway CORS 및 통합 수정   ${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

REST_API_ID="gda9ojk5c7"
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# 모든 리소스 가져오기
echo -e "${BLUE}1. 리소스 목록 가져오기...${NC}"
RESOURCES=$(aws apigateway get-resources --rest-api-id $REST_API_ID --region $REGION --query "items[*].[id,path]" --output json)

# 메소드 통합 설정 함수
setup_method_integration() {
    local resource_id=$1
    local http_method=$2
    local lambda_function=$3
    
    echo -e "  ${YELLOW}$http_method 메소드 통합 설정 중...${NC}"
    
    # Lambda ARN
    local lambda_arn="arn:aws:lambda:$REGION:$ACCOUNT_ID:function:$lambda_function"
    
    # 통합 설정
    aws apigateway put-integration \
        --rest-api-id $REST_API_ID \
        --resource-id $resource_id \
        --http-method $http_method \
        --type AWS_PROXY \
        --integration-http-method POST \
        --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/$lambda_arn/invocations" \
        --region $REGION > /dev/null 2>&1
    
    # 통합 응답 설정
    aws apigateway put-integration-response \
        --rest-api-id $REST_API_ID \
        --resource-id $resource_id \
        --http-method $http_method \
        --status-code 200 \
        --region $REGION > /dev/null 2>&1
    
    # 메소드 응답 설정
    aws apigateway put-method-response \
        --rest-api-id $REST_API_ID \
        --resource-id $resource_id \
        --http-method $http_method \
        --status-code 200 \
        --response-parameters '{"method.response.header.Access-Control-Allow-Origin":true}' \
        --region $REGION > /dev/null 2>&1
    
    echo -e "  ${GREEN}✓${NC} $http_method 통합 완료"
}

# /prompts 리소스
echo -e "\n${BLUE}2. /prompts 리소스 설정${NC}"
PROMPTS_ID=$(aws apigateway get-resources --rest-api-id $REST_API_ID --region $REGION --query "items[?path=='/prompts'].id" --output text)
if [ -n "$PROMPTS_ID" ]; then
    setup_method_integration $PROMPTS_ID "GET" "nx-wt-prf-prompt-crud"
    setup_method_integration $PROMPTS_ID "POST" "nx-wt-prf-prompt-crud"
fi

# /prompts/{promptId} 리소스
echo -e "\n${BLUE}3. /prompts/{promptId} 리소스 설정${NC}"
PROMPT_ID=$(aws apigateway get-resources --rest-api-id $REST_API_ID --region $REGION --query "items[?path=='/prompts/{promptId}'].id" --output text)
if [ -n "$PROMPT_ID" ]; then
    setup_method_integration $PROMPT_ID "GET" "nx-wt-prf-prompt-crud"
    setup_method_integration $PROMPT_ID "PUT" "nx-wt-prf-prompt-crud"
    setup_method_integration $PROMPT_ID "DELETE" "nx-wt-prf-prompt-crud"
fi

# /conversations 리소스
echo -e "\n${BLUE}4. /conversations 리소스 설정${NC}"
CONV_ID=$(aws apigateway get-resources --rest-api-id $REST_API_ID --region $REGION --query "items[?path=='/conversations'].id" --output text)
if [ -n "$CONV_ID" ]; then
    setup_method_integration $CONV_ID "GET" "nx-wt-prf-conversation-api"
    setup_method_integration $CONV_ID "POST" "nx-wt-prf-conversation-api"
fi

# /conversations/{id} 리소스
echo -e "\n${BLUE}5. /conversations/{id} 리소스 설정${NC}"
CONV_ITEM_ID=$(aws apigateway get-resources --rest-api-id $REST_API_ID --region $REGION --query "items[?path=='/conversations/{id}'].id" --output text)
if [ -n "$CONV_ITEM_ID" ]; then
    setup_method_integration $CONV_ITEM_ID "GET" "nx-wt-prf-conversation-api"
    setup_method_integration $CONV_ITEM_ID "PUT" "nx-wt-prf-conversation-api"
    setup_method_integration $CONV_ITEM_ID "DELETE" "nx-wt-prf-conversation-api"
fi

# /usage 리소스
echo -e "\n${BLUE}6. /usage 리소스 설정${NC}"
USAGE_ID=$(aws apigateway get-resources --rest-api-id $REST_API_ID --region $REGION --query "items[?path=='/usage'].id" --output text)
if [ -n "$USAGE_ID" ]; then
    setup_method_integration $USAGE_ID "GET" "nx-wt-prf-usage-handler"
fi

# API 재배포
echo -e "\n${BLUE}7. API 재배포 중...${NC}"
DEPLOYMENT_ID=$(aws apigateway create-deployment \
    --rest-api-id $REST_API_ID \
    --stage-name prod \
    --description "Fix CORS and integrations" \
    --region $REGION \
    --query 'id' \
    --output text)

echo -e "${GREEN}✅ API 재배포 완료: $DEPLOYMENT_ID${NC}"

# WebSocket Lambda 권한 설정
echo -e "\n${BLUE}8. WebSocket Lambda 권한 재설정${NC}"
WS_API_ID="tj12bntr3c"

# WebSocket Lambda 함수들에 권한 추가
for func in "nx-wt-prf-websocket-connect" "nx-wt-prf-websocket-disconnect" "nx-wt-prf-websocket-message"; do
    echo -e "  ${YELLOW}$func 권한 설정 중...${NC}"
    
    # 기존 권한 제거
    aws lambda remove-permission \
        --function-name $func \
        --statement-id "websocket-api-permission" \
        --region $REGION 2>/dev/null
    
    # 새 권한 추가
    aws lambda add-permission \
        --function-name $func \
        --statement-id "websocket-api-permission" \
        --action lambda:InvokeFunction \
        --principal apigateway.amazonaws.com \
        --source-arn "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$WS_API_ID/*/*" \
        --region $REGION > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✓${NC} $func 권한 추가 완료"
    else
        echo -e "  ${YELLOW}⚠${NC} $func 권한 추가 실패"
    fi
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   ✅ CORS 및 통합 설정 완료!   ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 테스트
echo -e "${BLUE}9. API 테스트${NC}"
sleep 3
echo -e "\n${CYAN}Prompts 엔드포인트 테스트:${NC}"
curl -s -X GET "https://$REST_API_ID.execute-api.$REGION.amazonaws.com/prod/prompts" \
    -H "Origin: http://localhost:3000" \
    -w "\nHTTP Status: %{http_code}\n" | tail -3

echo ""