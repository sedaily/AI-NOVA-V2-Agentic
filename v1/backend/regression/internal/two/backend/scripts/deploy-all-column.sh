#!/bin/bash

# 색상 설정
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

clear

echo -e "${BLUE}${BOLD}================================================${NC}"
echo -e "${BLUE}${BOLD}   SEDAILY-COLUMN SERVICE FULL DEPLOYMENT${NC}"
echo -e "${BLUE}${BOLD}================================================${NC}"
echo ""
echo -e "${YELLOW}This script will deploy the entire sedaily-column backend infrastructure${NC}"
echo -e "${YELLOW}Including: DynamoDB, Lambda Functions, API Gateway, WebSocket${NC}"
echo ""

# 현재 디렉토리 확인
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $SCRIPT_DIR

# AWS 계정 정보 확인
echo -e "${BLUE}Checking AWS credentials...${NC}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)

if [ -z "$ACCOUNT_ID" ]; then
    echo -e "${RED}✗ AWS credentials not configured!${NC}"
    echo -e "${YELLOW}Please run: aws configure${NC}"
    exit 1
fi

echo -e "${GREEN}✓ AWS Account: ${ACCOUNT_ID}${NC}"
echo -e "${GREEN}✓ Region: us-east-1${NC}"
echo ""

# 사용자 확인
echo -e "${YELLOW}${BOLD}WARNING: This will create new AWS resources and may incur costs!${NC}"
echo -e "${YELLOW}Do you want to continue? (yes/no)${NC}"
read -r CONFIRM

if [[ ! "$CONFIRM" =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${RED}Deployment cancelled.${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}${BOLD}Starting deployment...${NC}"
echo ""

# 배포 단계 정의
declare -a STEPS=(
    "01-setup-dynamodb-column.sh:DynamoDB Tables"
    "02-create-lambda-functions.sh:Lambda Functions & IAM Roles"
    "03-setup-api-gateway.sh:REST API Gateway"
    "04-setup-websocket.sh:WebSocket API"
    "05-deploy-lambda.sh:Lambda Code Deployment"
)

TOTAL_STEPS=${#STEPS[@]}
CURRENT_STEP=0
FAILED_STEPS=()

# 각 단계 실행
for STEP in "${STEPS[@]}"; do
    IFS=':' read -r SCRIPT_NAME DESCRIPTION <<< "$STEP"
    ((CURRENT_STEP++))

    echo -e "${BLUE}${BOLD}[Step ${CURRENT_STEP}/${TOTAL_STEPS}] ${DESCRIPTION}${NC}"
    echo -e "${BLUE}════════════════════════════════════════${NC}"

    if [ -f "$SCRIPT_NAME" ]; then
        # 스크립트 실행 권한 부여
        chmod +x "$SCRIPT_NAME"

        # 스크립트 실행
        ./"$SCRIPT_NAME"
        RESULT=$?

        if [ $RESULT -eq 0 ]; then
            echo -e "${GREEN}${BOLD}✓ ${DESCRIPTION} completed successfully${NC}"
        else
            echo -e "${RED}${BOLD}✗ ${DESCRIPTION} failed${NC}"
            FAILED_STEPS+=("$DESCRIPTION")

            # 실패 시 계속할지 묻기
            echo -e "${YELLOW}Do you want to continue with the remaining steps? (yes/no)${NC}"
            read -r CONTINUE_DEPLOY
            if [[ ! "$CONTINUE_DEPLOY" =~ ^[Yy][Ee][Ss]$ ]]; then
                break
            fi
        fi
    else
        echo -e "${RED}✗ Script not found: ${SCRIPT_NAME}${NC}"
        FAILED_STEPS+=("$DESCRIPTION")
    fi

    echo ""
done

# ====================================
# 배포 결과 요약
# ====================================
echo ""
echo -e "${BLUE}${BOLD}================================================${NC}"
echo -e "${BLUE}${BOLD}           DEPLOYMENT SUMMARY${NC}"
echo -e "${BLUE}${BOLD}================================================${NC}"
echo ""

if [ ${#FAILED_STEPS[@]} -eq 0 ]; then
    echo -e "${GREEN}${BOLD}✅ ALL STEPS COMPLETED SUCCESSFULLY!${NC}"
    echo ""

    # API 정보 조회 및 출력
    echo -e "${BLUE}${BOLD}Retrieving API endpoints...${NC}"
    echo ""

    # REST API ID 조회
    REST_API_ID=$(aws apigateway get-rest-apis \
        --region us-east-1 \
        --query "items[?name=='sedaily-column-rest-api'].id" \
        --output text 2>/dev/null | head -1)

    # WebSocket API ID 조회
    WS_API_ID=$(aws apigatewayv2 get-apis \
        --region us-east-1 \
        --query "Items[?Name=='sedaily-column-websocket-api'].ApiId" \
        --output text 2>/dev/null | head -1)

    echo -e "${GREEN}${BOLD}🎉 Deployment Information:${NC}"
    echo -e "${GREEN}════════════════════════════════════════${NC}"
    echo ""

    if [ -n "$REST_API_ID" ]; then
        echo -e "${BLUE}REST API:${NC}"
        echo -e "  ${GREEN}ID:${NC} ${REST_API_ID}"
        echo -e "  ${GREEN}URL:${NC} https://${REST_API_ID}.execute-api.us-east-1.amazonaws.com/prod"
        echo ""
    fi

    if [ -n "$WS_API_ID" ]; then
        echo -e "${BLUE}WebSocket API:${NC}"
        echo -e "  ${GREEN}ID:${NC} ${WS_API_ID}"
        echo -e "  ${GREEN}URL:${NC} wss://${WS_API_ID}.execute-api.us-east-1.amazonaws.com/prod"
        echo ""
    fi

    echo -e "${BLUE}DynamoDB Tables:${NC}"
    echo -e "  ${GREEN}✓${NC} sedaily-column-conversations"
    echo -e "  ${GREEN}✓${NC} sedaily-column-prompts"
    echo -e "  ${GREEN}✓${NC} sedaily-column-usage"
    echo -e "  ${GREEN}✓${NC} sedaily-column-websocket-connections"
    echo -e "  ${GREEN}✓${NC} sedaily-column-files"
    echo ""

    echo -e "${BLUE}Lambda Functions:${NC}"
    echo -e "  ${GREEN}✓${NC} sedaily-column-conversation-api"
    echo -e "  ${GREEN}✓${NC} sedaily-column-prompt-crud"
    echo -e "  ${GREEN}✓${NC} sedaily-column-usage-handler"
    echo -e "  ${GREEN}✓${NC} sedaily-column-websocket-message"
    echo -e "  ${GREEN}✓${NC} sedaily-column-websocket-connect"
    echo -e "  ${GREEN}✓${NC} sedaily-column-websocket-disconnect"
    echo ""

    echo -e "${YELLOW}${BOLD}Next Steps:${NC}"
    echo -e "  1. Update frontend .env file with the API URLs above"
    echo -e "  2. Test the API endpoints using Postman or curl"
    echo -e "  3. Deploy the frontend application"
    echo ""

    # .env 파일 생성 제안
    echo -e "${YELLOW}${BOLD}Suggested frontend .env configuration:${NC}"
    echo -e "${GREEN}════════════════════════════════════════${NC}"
    echo -e "VITE_API_URL=https://${REST_API_ID}.execute-api.us-east-1.amazonaws.com/prod"
    echo -e "VITE_WEBSOCKET_URL=wss://${WS_API_ID}.execute-api.us-east-1.amazonaws.com/prod"
    echo -e "${GREEN}════════════════════════════════════════${NC}"

else
    echo -e "${RED}${BOLD}⚠️  DEPLOYMENT COMPLETED WITH ERRORS${NC}"
    echo ""
    echo -e "${RED}Failed steps:${NC}"
    for FAILED in "${FAILED_STEPS[@]}"; do
        echo -e "  ${RED}✗${NC} $FAILED"
    done
    echo ""
    echo -e "${YELLOW}${BOLD}To fix:${NC}"
    echo -e "  1. Check the error messages above"
    echo -e "  2. Fix any issues"
    echo -e "  3. Re-run the failed scripts individually"
    echo -e "  4. Or re-run this script to retry all steps"
fi

echo ""
echo -e "${BLUE}${BOLD}================================================${NC}"
echo -e "${BLUE}${BOLD}          END OF DEPLOYMENT SCRIPT${NC}"
echo -e "${BLUE}${BOLD}================================================${NC}"