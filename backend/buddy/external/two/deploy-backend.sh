#!/bin/bash

# 색상 설정
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}P2 BUDDY LAMBDA DEPLOYMENT${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""

# 설정
REGION="us-east-1"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR/backend"

echo -e "${YELLOW}Deploying Lambda functions for buddy${NC}"
echo -e "${YELLOW}Backend directory: ${BACKEND_DIR}${NC}"
echo ""

# Lambda 함수 목록
FUNCTION_NAMES=(
    "p2-two-conversation-api-two"
    "p2-two-prompt-crud-two"
    "p2-two-usage-handler-two"
    "p2-two-websocket-message-two"
    "p2-two-websocket-connect-two"
    "p2-two-websocket-disconnect-two"
)

FUNCTION_HANDLERS=(
    "handlers.api.conversation.handler"
    "handlers.api.prompt.handler"
    "handlers.api.usage.handler"
    "handlers.websocket.message.handler"
    "handlers.websocket.connect.handler"
    "handlers.websocket.disconnect.handler"
)

# 임시 디렉토리 생성
TEMP_DIR="/tmp/lambda-deploy-buddy"
rm -rf $TEMP_DIR
mkdir -p $TEMP_DIR

# 배포 패키지 생성
echo -e "${BLUE}Creating deployment package...${NC}"

# 소스 코드 복사
cp -r "$BACKEND_DIR"/handlers "$TEMP_DIR"/
cp -r "$BACKEND_DIR"/src "$TEMP_DIR"/
cp -r "$BACKEND_DIR"/utils "$TEMP_DIR"/
cp -r "$BACKEND_DIR"/services "$TEMP_DIR"/ 2>/dev/null || true
cp -r "$BACKEND_DIR"/lib "$TEMP_DIR"/ 2>/dev/null || true

# requirements.txt 확인 및 의존성 설치
if [ -f "$BACKEND_DIR/requirements.txt" ]; then
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    pip install -r "$BACKEND_DIR"/requirements.txt -t "$TEMP_DIR" --upgrade --quiet
    echo -e "${GREEN}Dependencies installed${NC}"
fi

# 불필요한 파일 제거
find $TEMP_DIR -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find $TEMP_DIR -type f -name "*.pyc" -delete
find $TEMP_DIR -type d -name ".git" -exec rm -rf {} + 2>/dev/null
find $TEMP_DIR -type f -name ".DS_Store" -delete

# ZIP 파일 생성
cd $TEMP_DIR
zip -r deployment.zip . -q
PACKAGE_SIZE=$(du -h deployment.zip | cut -f1)
echo -e "${GREEN}Deployment package created (${PACKAGE_SIZE})${NC}"

# Lambda 함수 배포
echo ""
echo -e "${BLUE}Deploying Lambda functions...${NC}"

deploy_function() {
    local FUNCTION_NAME=$1
    local HANDLER=$2

    echo -e "${YELLOW}Deploying ${FUNCTION_NAME}...${NC}"

    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file "fileb://$TEMP_DIR/deployment.zip" \
        --region $REGION \
        --output text >/dev/null 2>&1

    if [ $? -eq 0 ]; then
        aws lambda update-function-configuration \
            --function-name "$FUNCTION_NAME" \
            --handler "$HANDLER" \
            --region $REGION \
            --output text >/dev/null 2>&1

        echo -e "${GREEN}  ✓ ${FUNCTION_NAME} deployed${NC}"
        return 0
    else
        echo -e "${RED}  ✗ ${FUNCTION_NAME} deployment failed${NC}"
        return 1
    fi
}

TOTAL=${#FUNCTION_NAMES[@]}
CURRENT=0
SUCCESS=0
FAILED=0

for i in "${!FUNCTION_NAMES[@]}"; do
    FUNCTION_NAME="${FUNCTION_NAMES[$i]}"
    HANDLER="${FUNCTION_HANDLERS[$i]}"
    ((CURRENT++))
    echo -e "${BLUE}[${CURRENT}/${TOTAL}] ${FUNCTION_NAME}${NC}"

    if deploy_function "$FUNCTION_NAME" "$HANDLER"; then
        ((SUCCESS++))
    else
        ((FAILED++))
    fi
done

# 배포 상태 확인
echo ""
echo -e "${BLUE}Verifying deployment...${NC}"

for FUNCTION_NAME in "${FUNCTION_NAMES[@]}"; do
    STATUS=$(aws lambda get-function \
        --function-name "$FUNCTION_NAME" \
        --region $REGION \
        --query 'Configuration.LastUpdateStatus' \
        --output text 2>/dev/null)

    if [ "$STATUS" == "Successful" ] || [ "$STATUS" == "InProgress" ]; then
        echo -e "${GREEN}  ✓ ${FUNCTION_NAME}: ${STATUS}${NC}"
    else
        echo -e "${YELLOW}  ⚠ ${FUNCTION_NAME}: ${STATUS}${NC}"
    fi
done

# 정리
rm -rf $TEMP_DIR

# 결과
echo ""
echo -e "${GREEN}=================================${NC}"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}DEPLOYMENT COMPLETED SUCCESSFULLY!${NC}"
else
    echo -e "${YELLOW}DEPLOYMENT COMPLETED WITH ISSUES${NC}"
fi
echo -e "${GREEN}=================================${NC}"
echo ""
echo -e "${BLUE}Deployment Summary:${NC}"
echo -e "  ${GREEN}✓ Successful:${NC} ${SUCCESS}"
if [ $FAILED -gt 0 ]; then
    echo -e "  ${RED}✗ Failed:${NC} ${FAILED}"
fi
