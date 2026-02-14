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
API_NAME="nx-wt-prf-websocket-api"
API_DESCRIPTION="Nexus Writer PRF WebSocket API"
STAGE_NAME="prod"
PROJECT_PREFIX="nx-wt-prf"

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}   WebSocket API 생성 - ${PROJECT_PREFIX}   ${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# AWS 계정 ID 가져오기
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✅ AWS Account ID: $ACCOUNT_ID${NC}"

# 1. WebSocket API 생성
echo -e "${BLUE}1. WebSocket API 생성 중...${NC}"
API_ID=$(aws apigatewayv2 create-api \
    --name "$API_NAME" \
    --protocol-type WEBSOCKET \
    --route-selection-expression '$request.body.action' \
    --description "$API_DESCRIPTION" \
    --region $REGION \
    --query 'ApiId' \
    --output text)
    

if [ -z "$API_ID" ]; then
    echo -e "${RED}❌ WebSocket API 생성 실패${NC}"
    exit 1
fi

echo -e "${GREEN}✅ WebSocket API 생성 완료: $API_ID${NC}"

# 2. Lambda 통합 생성 함수
create_integration() {
    local route_key=$1
    local lambda_function=$2
    
    local lambda_arn="arn:aws:lambda:$REGION:$ACCOUNT_ID:function:$lambda_function"
    
    INTEGRATION_ID=$(aws apigatewayv2 create-integration \
        --api-id $API_ID \
        --integration-type AWS_PROXY \
        --integration-uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/$lambda_arn/invocations" \
        --region $REGION \
        --query 'IntegrationId' \
        --output text)
    
    echo "$INTEGRATION_ID"
}

# 3. 라우트 생성 함수
create_route() {
    local route_key=$1
    local integration_id=$2
    
    aws apigatewayv2 create-route \
        --api-id $API_ID \
        --route-key "$route_key" \
        --target "integrations/$integration_id" \
        --region $REGION > /dev/null 2>&1
    
    echo -e "  ${GREEN}✓${NC} $route_key 라우트 생성 완료"
}

# 4. Lambda 권한 추가 함수
add_lambda_permission() {
    local function_name=$1
    local statement_id=$2
    
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
        --source-arn "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*/*" \
        --region $REGION > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✓${NC} $function_name Lambda 권한 추가 완료"
    else
        echo -e "  ${YELLOW}⚠${NC} $function_name Lambda 권한 추가 실패 (함수가 존재하지 않을 수 있음)"
    fi
}

# 5. 연결 관리 라우트 생성
echo -e "\n${BLUE}2. 연결 관리 라우트 생성 중...${NC}"

# $connect 라우트
echo -e "\n${CYAN}📌 \$connect 라우트 설정${NC}"
CONNECT_INT_ID=$(create_integration '$connect' "${PROJECT_PREFIX}-websocket-connect")
create_route '$connect' $CONNECT_INT_ID
add_lambda_permission "${PROJECT_PREFIX}-websocket-connect" "websocket-connect"

# $disconnect 라우트
echo -e "\n${CYAN}📌 \$disconnect 라우트 설정${NC}"
DISCONNECT_INT_ID=$(create_integration '$disconnect' "${PROJECT_PREFIX}-websocket-disconnect")
create_route '$disconnect' $DISCONNECT_INT_ID
add_lambda_permission "${PROJECT_PREFIX}-websocket-disconnect" "websocket-disconnect"

# $default 라우트 (메시지 처리)
echo -e "\n${CYAN}📌 \$default 라우트 설정${NC}"
DEFAULT_INT_ID=$(create_integration '$default' "${PROJECT_PREFIX}-websocket-message")
create_route '$default' $DEFAULT_INT_ID
add_lambda_permission "${PROJECT_PREFIX}-websocket-message" "websocket-default"

# 6. 커스텀 라우트 생성 (필요시)
echo -e "\n${BLUE}3. 커스텀 라우트 생성 중...${NC}"

# sendMessage 라우트
echo -e "\n${CYAN}📌 sendMessage 라우트 설정${NC}"
MESSAGE_INT_ID=$(create_integration 'sendMessage' "${PROJECT_PREFIX}-websocket-message")
create_route 'sendMessage' $MESSAGE_INT_ID
add_lambda_permission "${PROJECT_PREFIX}-websocket-message" "websocket-sendMessage"

# 7. Stage 생성 및 배포
echo -e "\n${BLUE}4. API 배포 중...${NC}"

# 배포 생성
DEPLOYMENT_ID=$(aws apigatewayv2 create-deployment \
    --api-id $API_ID \
    --description "Initial deployment" \
    --region $REGION \
    --query 'DeploymentId' \
    --output text)

if [ -z "$DEPLOYMENT_ID" ]; then
    echo -e "${RED}❌ 배포 생성 실패${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 배포 생성 완료: $DEPLOYMENT_ID${NC}"

# Stage 생성
aws apigatewayv2 create-stage \
    --api-id $API_ID \
    --stage-name $STAGE_NAME \
    --deployment-id $DEPLOYMENT_ID \
    --description "Production stage for $PROJECT_PREFIX WebSocket API" \
    --region $REGION > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Stage 생성 완료: $STAGE_NAME${NC}"
else
    # Stage가 이미 존재하는 경우 업데이트
    aws apigatewayv2 update-stage \
        --api-id $API_ID \
        --stage-name $STAGE_NAME \
        --deployment-id $DEPLOYMENT_ID \
        --region $REGION > /dev/null 2>&1
    echo -e "${GREEN}✅ Stage 업데이트 완료: $STAGE_NAME${NC}"
fi

# 8. 로깅 설정 (선택사항)
echo -e "\n${BLUE}5. 로깅 설정 중...${NC}"
aws apigatewayv2 update-stage \
    --api-id $API_ID \
    --stage-name $STAGE_NAME \
    --default-route-settings "{\"DetailedMetricsEnabled\":true,\"LoggingLevel\":\"INFO\",\"ThrottlingBurstLimit\":500,\"ThrottlingRateLimit\":1000}" \
    --region $REGION > /dev/null 2>&1

echo -e "${GREEN}✅ 로깅 설정 완료${NC}"

# 9. 결과 출력
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   ✅ WebSocket API 생성 완료!   ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${CYAN}📋 WebSocket API 정보:${NC}"
echo -e "  • API ID: ${YELLOW}$API_ID${NC}"
echo -e "  • API Name: ${YELLOW}$API_NAME${NC}"
echo -e "  • Stage: ${YELLOW}$STAGE_NAME${NC}"
echo -e "  • Region: ${YELLOW}$REGION${NC}"
echo -e "  • WebSocket URL: ${YELLOW}wss://$API_ID.execute-api.$REGION.amazonaws.com/$STAGE_NAME${NC}"
echo ""
echo -e "${CYAN}📌 다음 단계:${NC}"
echo -e "  1. Lambda 함수 생성 (${PROJECT_PREFIX}-websocket-connect, ${PROJECT_PREFIX}-websocket-disconnect, ${PROJECT_PREFIX}-websocket-message)"
echo -e "  2. DynamoDB 테이블 생성 (${PROJECT_PREFIX}-websocket-connections)"
echo -e "  3. 프론트엔드 WebSocket URL 업데이트"
echo ""

# WebSocket API ID를 파일로 저장
echo "$API_ID" > websocket_api_id.txt
echo -e "${CYAN}💾 WebSocket API ID가 websocket_api_id.txt 파일에 저장되었습니다.${NC}"