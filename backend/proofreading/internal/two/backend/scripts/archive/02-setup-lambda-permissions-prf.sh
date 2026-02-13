#!/bin/bash

# 색상 설정
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 설정
REGION="us-east-1"
PROJECT_PREFIX="nx-wt-prf"

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}   Lambda 실행 권한 설정 - ${PROJECT_PREFIX}   ${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# API Gateway ID 읽기
if [ -f "api_gateway_id.txt" ]; then
    API_ID=$(cat api_gateway_id.txt)
    echo -e "${GREEN}✅ API Gateway ID 로드: $API_ID${NC}"
else
    echo -e "${YELLOW}API Gateway ID를 입력하세요:${NC}"
    read API_ID
fi

if [ -z "$API_ID" ]; then
    echo -e "${RED}❌ API Gateway ID가 필요합니다${NC}"
    exit 1
fi

# AWS 계정 ID 가져오기
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✅ AWS Account ID: $ACCOUNT_ID${NC}"

# Lambda 함수 목록
LAMBDA_FUNCTIONS=(
    "${PROJECT_PREFIX}-conversation-api"
    "${PROJECT_PREFIX}-prompt-crud"
    "${PROJECT_PREFIX}-usage-handler"
    "${PROJECT_PREFIX}-websocket-message"
)

# 권한 추가 함수
add_lambda_permission() {
    local function_name=$1
    local statement_id=$2
    local source_arn=$3
    
    # 기존 권한 제거 (있을 경우)
    aws lambda remove-permission \
        --function-name $function_name \
        --statement-id $statement_id \
        --region $REGION 2>/dev/null
    
    # 새 권한 추가
    aws lambda add-permission \
        --function-name $function_name \
        --statement-id $statement_id \
        --action lambda:InvokeFunction \
        --principal apigateway.amazonaws.com \
        --source-arn "$source_arn" \
        --region $REGION > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✓${NC} $statement_id 권한 추가 완료"
    else
        echo -e "  ${YELLOW}⚠${NC} $statement_id 권한 추가 실패 (함수가 존재하지 않을 수 있음)"
    fi
}

echo -e "\n${BLUE}Lambda 실행 권한 추가 중...${NC}"

# 1. conversation-api 권한
echo -e "\n${CYAN}📌 ${PROJECT_PREFIX}-conversation-api 권한 설정${NC}"
FUNC="${PROJECT_PREFIX}-conversation-api"

add_lambda_permission $FUNC \
    "api-gateway-conversations-all" \
    "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*/*/conversations"

add_lambda_permission $FUNC \
    "api-gateway-conversations-id" \
    "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*/*/conversations/*"

# 2. prompt-crud 권한
echo -e "\n${CYAN}📌 ${PROJECT_PREFIX}-prompt-crud 권한 설정${NC}"
FUNC="${PROJECT_PREFIX}-prompt-crud"

add_lambda_permission $FUNC \
    "api-gateway-prompts-all" \
    "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*/*/prompts"

add_lambda_permission $FUNC \
    "api-gateway-prompts-id" \
    "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*/*/prompts/*"

add_lambda_permission $FUNC \
    "api-gateway-prompts-files" \
    "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*/*/prompts/*/files"

add_lambda_permission $FUNC \
    "api-gateway-prompts-files-id" \
    "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*/*/prompts/*/files/*"

# 3. usage-handler 권한
echo -e "\n${CYAN}📌 ${PROJECT_PREFIX}-usage-handler 권한 설정${NC}"
FUNC="${PROJECT_PREFIX}-usage-handler"

add_lambda_permission $FUNC \
    "api-gateway-usage" \
    "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*/*/usage"

# 4. WebSocket 메시지 핸들러 권한 (WebSocket API용)
echo -e "\n${CYAN}📌 ${PROJECT_PREFIX}-websocket-message 권한 설정 (WebSocket API용)${NC}"
echo -e "  ${YELLOW}ℹ${NC} WebSocket API 생성 후 별도로 설정 필요"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   ✅ Lambda 권한 설정 완료!   ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Lambda 함수 상태 확인
echo -e "${CYAN}📋 Lambda 함수 상태 확인:${NC}"
for func in "${LAMBDA_FUNCTIONS[@]}"; do
    STATUS=$(aws lambda get-function --function-name $func --region $REGION --query 'Configuration.State' --output text 2>/dev/null)
    
    if [ -n "$STATUS" ]; then
        if [ "$STATUS" = "Active" ]; then
            echo -e "  ${GREEN}✓${NC} $func: $STATUS"
        else
            echo -e "  ${YELLOW}⚠${NC} $func: $STATUS"
        fi
    else
        echo -e "  ${RED}✗${NC} $func: 함수가 존재하지 않음"
    fi
done

echo ""
echo -e "${CYAN}📌 다음 단계:${NC}"
echo -e "  1. Lambda 함수가 존재하지 않는 경우, 함수 생성 필요"
echo -e "  2. API Gateway 테스트 실행"
echo -e "  3. CloudWatch 로그에서 권한 오류 확인"
echo ""