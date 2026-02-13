#!/bin/bash

# 색상 설정
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}Lambda 함수 배포 스크립트${NC}"
echo -e "${BLUE}=================================${NC}"

# 스크립트 디렉토리
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
cd $BACKEND_DIR

# 배포 패키지 생성
echo -e "\n${BLUE}1. 배포 패키지 생성 중...${NC}"
rm -rf lambda_deploy.zip
# src 폴더를 포함하여 새 구조 반영
zip -r lambda_deploy.zip handlers services repositories utils lib models config src -x "*.pyc" -x "*__pycache__*" -x ".*"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ ZIP 파일 생성 실패${NC}"
    exit 1
fi

echo -e "${GREEN}✅ ZIP 파일 생성 완료${NC}"

# Lambda 함수 목록
FUNCTIONS=(
    "nx-tt-dev-ver3-conversation-api"
    "nx-tt-dev-ver3-prompt-crud"
    "nx-tt-dev-ver3-usage-handler"
    "nx-tt-dev-ver3-websocket-message"
)

# 핸들러 매핑 (조건부 설정)
get_handler_for_function() {
    case "$1" in
        "nx-tt-dev-ver3-conversation-api")
            echo "handlers.api.conversation.handler"
            ;;
        "nx-tt-dev-ver3-prompt-crud")
            echo "handlers.api.prompt.handler"
            ;;
        "nx-tt-dev-ver3-usage-handler")
            echo "handlers.api.usage.handler"
            ;;
        "nx-tt-dev-ver3-websocket-message")
            echo "handlers.websocket.message.handler"
            ;;
        *)
            echo ""
            ;;
    esac
}

# 각 함수 업데이트
echo -e "\n${BLUE}2. Lambda 함수 업데이트 중...${NC}"
for func in "${FUNCTIONS[@]}"; do
    echo -e "\n${YELLOW}처리 중: $func${NC}"
    
    # 코드 업데이트
    echo -e "  코드 업데이트..."
    aws lambda update-function-code \
        --function-name $func \
        --zip-file fileb://lambda_deploy.zip \
        --region us-east-1 > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✅ 코드 업데이트 성공${NC}"
    else
        echo -e "  ${RED}❌ 코드 업데이트 실패${NC}"
        continue
    fi
    
    # 핸들러 업데이트
    HANDLER=$(get_handler_for_function "$func")
    if [ -n "$HANDLER" ]; then
        echo -e "  핸들러 설정..."
        aws lambda update-function-configuration \
            --function-name $func \
            --handler "$HANDLER" \
            --region us-east-1 > /dev/null 2>&1
        
        if [ $? -eq 0 ]; then
            echo -e "  ${GREEN}✅ 핸들러 설정 성공 ($HANDLER)${NC}"
        else
            echo -e "  ${RED}❌ 핸들러 설정 실패${NC}"
        fi
    fi
    
    # 함수가 준비될 때까지 대기
    echo -e "  함수 준비 대기..."
    aws lambda wait function-active \
        --function-name $func \
        --region us-east-1 2>/dev/null
    
    echo -e "  ${GREEN}✅ $func 업데이트 완료${NC}"
done

# 정리
rm -f lambda_deploy.zip

echo -e "\n${BLUE}=================================${NC}"
echo -e "${GREEN}✅ 배포 완료!${NC}"
echo -e "${BLUE}=================================${NC}"

# 배포 결과 확인
echo -e "\n${BLUE}3. 배포 상태 확인${NC}"
for func in "${FUNCTIONS[@]}"; do
    STATE=$(aws lambda get-function --function-name $func --region us-east-1 --query 'Configuration.State' --output text 2>/dev/null)
    HANDLER=$(aws lambda get-function --function-name $func --region us-east-1 --query 'Configuration.Handler' --output text 2>/dev/null)
    
    if [ "$STATE" = "Active" ]; then
        echo -e "  ${GREEN}✓${NC} $func: $STATE (Handler: $HANDLER)"
    else
        echo -e "  ${RED}✗${NC} $func: $STATE"
    fi
done

echo -e "\n${YELLOW}다음 단계:${NC}"
echo -e "  1. CloudWatch 로그에서 에러 확인"
echo -e "  2. API Gateway에서 테스트 실행"
echo -e "  3. 필요시 롤백: git checkout -- ."