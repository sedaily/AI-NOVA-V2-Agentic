#!/bin/bash

# 색상 설정
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}SEDAILY-COLUMN LAMBDA DEPLOYMENT${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""

# 설정
REGION="us-east-1"
PREFIX="sedaily-column"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${YELLOW}Deploying Lambda functions for ${PREFIX}${NC}"
echo -e "${YELLOW}Backend directory: ${BACKEND_DIR}${NC}"
echo ""

# Lambda 함수 목록과 핸들러 매핑 (bash 3.2 호환)
FUNCTION_NAMES=(
    "${PREFIX}-conversation-api"
    "${PREFIX}-prompt-crud"
    "${PREFIX}-usage-handler"
    "${PREFIX}-websocket-message"
    "${PREFIX}-websocket-connect"
    "${PREFIX}-websocket-disconnect"
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
TEMP_DIR="/tmp/lambda-deploy-${PREFIX}"
rm -rf $TEMP_DIR
mkdir -p $TEMP_DIR

# ====================================
# 배포 패키지 생성
# ====================================
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
    echo -e "${GREEN}✅ Dependencies installed${NC}"
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
echo -e "${GREEN}✅ Deployment package created (${PACKAGE_SIZE})${NC}"

# ====================================
# Lambda 함수 업데이트
# ====================================
echo ""
echo -e "${BLUE}Deploying Lambda functions...${NC}"

# 병렬 배포를 위한 함수
deploy_function() {
    local FUNCTION_NAME=$1
    local HANDLER=$2

    echo -e "${YELLOW}Deploying ${FUNCTION_NAME}...${NC}"

    # 함수 코드 업데이트
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file "fileb://$TEMP_DIR/deployment.zip" \
        --region $REGION \
        --output text >/dev/null 2>&1

    if [ $? -eq 0 ]; then
        # 핸들러 업데이트
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

# 배포 시작
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

# ====================================
# 배포 상태 확인
# ====================================
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

# ====================================
# 배포 결과
# ====================================
echo ""
echo -e "${GREEN}=================================${NC}"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ DEPLOYMENT COMPLETED SUCCESSFULLY!${NC}"
else
    echo -e "${YELLOW}⚠️  DEPLOYMENT COMPLETED WITH ISSUES${NC}"
fi
echo -e "${GREEN}=================================${NC}"
echo ""
echo -e "${BLUE}Deployment Summary:${NC}"
echo -e "  ${GREEN}✓ Successful:${NC} ${SUCCESS}"
if [ $FAILED -gt 0 ]; then
    echo -e "  ${RED}✗ Failed:${NC} ${FAILED}"
fi
echo ""
echo -e "${BLUE}Deployed Functions:${NC}"
for FUNCTION_NAME in "${FUNCTION_NAMES[@]}"; do
    echo -e "  ${GREEN}✓${NC} $FUNCTION_NAME"
done
echo ""

# 다음 단계 안내
if [ $FAILED -eq 0 ]; then
    echo -e "${YELLOW}Next steps:${NC}"
    echo -e "  1. Test the API endpoints"
    echo -e "  2. Update frontend configuration with API URLs"
    echo -e "  3. Run integration tests"
else
    echo -e "${YELLOW}Action required:${NC}"
    echo -e "  1. Check the failed functions"
    echo -e "  2. Fix any code issues"
    echo -e "  3. Re-run this deployment script"
fi