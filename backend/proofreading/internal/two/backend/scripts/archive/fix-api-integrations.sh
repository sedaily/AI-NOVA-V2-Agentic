#!/bin/bash

# 색상 설정
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}   API Gateway 통합 재설정   ${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

REST_API_ID="gda9ojk5c7"
REGION="us-east-1"

# conversations/{id} 리소스 메소드 추가
echo -e "${BLUE}conversations/{id} 메소드 재설정 중...${NC}"
CONV_ID_RESOURCE=$(aws apigateway get-resources --rest-api-id $REST_API_ID --region $REGION --query "items[?path=='/conversations/{id}'].id" --output text)

if [ -n "$CONV_ID_RESOURCE" ]; then
    # GET 메소드 추가
    aws apigateway put-method \
        --rest-api-id $REST_API_ID \
        --resource-id $CONV_ID_RESOURCE \
        --http-method GET \
        --authorization-type NONE \
        --request-parameters "method.request.path.id=true" \
        --region $REGION > /dev/null 2>&1
    
    # PUT 메소드 추가
    aws apigateway put-method \
        --rest-api-id $REST_API_ID \
        --resource-id $CONV_ID_RESOURCE \
        --http-method PUT \
        --authorization-type NONE \
        --request-parameters "method.request.path.id=true" \
        --region $REGION > /dev/null 2>&1
    
    # DELETE 메소드 추가
    aws apigateway put-method \
        --rest-api-id $REST_API_ID \
        --resource-id $CONV_ID_RESOURCE \
        --http-method DELETE \
        --authorization-type NONE \
        --request-parameters "method.request.path.id=true" \
        --region $REGION > /dev/null 2>&1
    
    echo -e "${GREEN}✅ conversations/{id} 메소드 추가 완료${NC}"
fi

# prompts/{promptId} 리소스 메소드 추가
echo -e "${BLUE}prompts/{promptId} 메소드 재설정 중...${NC}"
PROMPT_ID_RESOURCE=$(aws apigateway get-resources --rest-api-id $REST_API_ID --region $REGION --query "items[?path=='/prompts/{promptId}'].id" --output text)

if [ -n "$PROMPT_ID_RESOURCE" ]; then
    # GET 메소드 추가
    aws apigateway put-method \
        --rest-api-id $REST_API_ID \
        --resource-id $PROMPT_ID_RESOURCE \
        --http-method GET \
        --authorization-type NONE \
        --request-parameters "method.request.path.promptId=true" \
        --region $REGION > /dev/null 2>&1
    
    # PUT 메소드 추가
    aws apigateway put-method \
        --rest-api-id $REST_API_ID \
        --resource-id $PROMPT_ID_RESOURCE \
        --http-method PUT \
        --authorization-type NONE \
        --request-parameters "method.request.path.promptId=true" \
        --region $REGION > /dev/null 2>&1
    
    # DELETE 메소드 추가
    aws apigateway put-method \
        --rest-api-id $REST_API_ID \
        --resource-id $PROMPT_ID_RESOURCE \
        --http-method DELETE \
        --authorization-type NONE \
        --request-parameters "method.request.path.promptId=true" \
        --region $REGION > /dev/null 2>&1
    
    echo -e "${GREEN}✅ prompts/{promptId} 메소드 추가 완료${NC}"
fi

# prompts/{promptId}/files 리소스 메소드 추가
echo -e "${BLUE}prompts/{promptId}/files 메소드 재설정 중...${NC}"
FILES_RESOURCE=$(aws apigateway get-resources --rest-api-id $REST_API_ID --region $REGION --query "items[?path=='/prompts/{promptId}/files'].id" --output text)

if [ -n "$FILES_RESOURCE" ]; then
    # GET 메소드 추가
    aws apigateway put-method \
        --rest-api-id $REST_API_ID \
        --resource-id $FILES_RESOURCE \
        --http-method GET \
        --authorization-type NONE \
        --request-parameters "method.request.path.promptId=true" \
        --region $REGION > /dev/null 2>&1
    
    # POST 메소드 추가
    aws apigateway put-method \
        --rest-api-id $REST_API_ID \
        --resource-id $FILES_RESOURCE \
        --http-method POST \
        --authorization-type NONE \
        --request-parameters "method.request.path.promptId=true" \
        --region $REGION > /dev/null 2>&1
    
    echo -e "${GREEN}✅ prompts/{promptId}/files 메소드 추가 완료${NC}"
fi

# API 재배포
echo -e "\n${BLUE}API 재배포 중...${NC}"
DEPLOYMENT_ID=$(aws apigateway create-deployment \
    --rest-api-id $REST_API_ID \
    --stage-name prod \
    --description "Fix missing methods" \
    --region $REGION \
    --query 'id' \
    --output text)

echo -e "${GREEN}✅ API 재배포 완료: $DEPLOYMENT_ID${NC}"

# 테스트
echo -e "\n${BLUE}API 테스트 중...${NC}"
sleep 3
curl -s -X GET "https://$REST_API_ID.execute-api.$REGION.amazonaws.com/prod/prompts" | jq '.prompts[].id' 2>/dev/null

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}   ✅ API Gateway 통합 재설정 완료!   ${NC}"
echo -e "${GREEN}========================================${NC}"