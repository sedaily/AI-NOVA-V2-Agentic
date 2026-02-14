#!/bin/bash

# 색상 설정
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}SEDAILY-COLUMN LAMBDA DEPLOYMENT${NC}"
echo -e "${BLUE}=================================${NC}"

REGION="us-east-1"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 임시 디렉토리 생성
TEMP_DIR="/tmp/lambda-deploy-column"
rm -rf $TEMP_DIR
mkdir -p $TEMP_DIR

echo -e "${YELLOW}Creating deployment package...${NC}"

# handlers 폴더 전체 복사
cp -r "$SCRIPT_DIR"/handlers $TEMP_DIR/

# 나머지 모듈 복사
cp -r "$SCRIPT_DIR"/src $TEMP_DIR/
cp -r "$SCRIPT_DIR"/utils $TEMP_DIR/
cp -r "$SCRIPT_DIR"/services $TEMP_DIR/ 2>/dev/null || true
cp -r "$SCRIPT_DIR"/lib $TEMP_DIR/ 2>/dev/null || true

# requirements.txt 설치
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r "$SCRIPT_DIR"/requirements.txt -t $TEMP_DIR --upgrade --quiet

# ZIP 파일 생성
cd $TEMP_DIR
zip -r deployment.zip . -q
PACKAGE_SIZE=$(du -h deployment.zip | cut -f1)
echo -e "${GREEN}✅ Package created (${PACKAGE_SIZE})${NC}"

# Lambda 함수 업데이트
echo -e "\n${BLUE}Deploying Lambda functions...${NC}"

FUNCTIONS=(
    "sedaily-column-websocket-connect"
    "sedaily-column-websocket-disconnect"
    "sedaily-column-websocket-message"
    "sedaily-column-conversation-api"
    "sedaily-column-prompt-crud"
    "sedaily-column-usage-handler"
)

SUCCESS=0
FAILED=0

for FUNCTION in "${FUNCTIONS[@]}"; do
    echo -e "\n${YELLOW}Deploying ${FUNCTION}...${NC}"

    aws lambda update-function-code \
        --function-name "$FUNCTION" \
        --zip-file "fileb://$TEMP_DIR/deployment.zip" \
        --region $REGION \
        --output text >/dev/null 2>&1

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}  ✓ ${FUNCTION} deployed${NC}"
        ((SUCCESS++))
    else
        echo -e "${RED}  ✗ ${FUNCTION} failed${NC}"
        ((FAILED++))
    fi
done

# 정리
rm -rf $TEMP_DIR

echo -e "\n${GREEN}=================================${NC}"
echo -e "${BLUE}Deployment Summary:${NC}"
echo -e "  ${GREEN}✓ Success: ${SUCCESS}${NC}"
echo -e "  ${RED}✗ Failed: ${FAILED}${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✅ All functions deployed successfully!${NC}"
else
    echo -e "\n${YELLOW}⚠️  Some deployments failed${NC}"
fi