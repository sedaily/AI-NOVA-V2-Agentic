#!/bin/bash

#############################################
# B1.SEDAILY.AI Lambda 환경변수 업데이트
#############################################

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Lambda 환경변수 업데이트${NC}"
echo -e "${GREEN}========================================${NC}"

# 설정
REGION="us-east-1"

# Lambda 함수 목록 (b1.sedaily.ai 전용)
LAMBDA_FUNCTIONS=(
    "p2-two-websocket-message-two"
    "p2-two-conversation-api-two"
    "p2-two-prompt-crud-two"
    "p2-two-websocket-connect-two"
    "p2-two-websocket-disconnect-two"
    "p2-two-usage-handler-two"
)

# 환경변수 선택
echo -e "${YELLOW}업데이트할 환경변수 유형을 선택하세요:${NC}"
echo "1) Claude 4.5 Opus 설정"
echo "2) 웹 검색 활성화/비활성화"
echo "3) 사용자 정의"
read -p "선택 (1-3): " choice

case $choice in
    1)
        echo -e "${YELLOW}Claude 4.5 Opus 설정 업데이트${NC}"
        ENV_VARS='{
            "ANTHROPIC_MODEL_ID": "claude-opus-4-5-20251101",
            "USE_OPUS_MODEL": "true",
            "ANTHROPIC_SECRET_NAME": "buddy-v1",
            "USE_ANTHROPIC_API": "true",
            "AI_PROVIDER": "anthropic_api"
        }'
        ;;
    2)
        echo -e "${YELLOW}웹 검색 설정${NC}"
        read -p "웹 검색 활성화? (y/n): " enable_search
        if [ "$enable_search" = "y" ]; then
            ENV_VARS='{"ENABLE_WEB_SEARCH": "true"}'
        else
            ENV_VARS='{"ENABLE_WEB_SEARCH": "false"}'
        fi
        ;;
    3)
        echo -e "${YELLOW}사용자 정의 환경변수${NC}"
        read -p "변수명: " var_name
        read -p "값: " var_value
        ENV_VARS="{\"$var_name\": \"$var_value\"}"
        ;;
    *)
        echo -e "${RED}잘못된 선택입니다.${NC}"
        exit 1
        ;;
esac

echo -e "${YELLOW}다음 환경변수를 업데이트합니다:${NC}"
echo "$ENV_VARS"
read -p "계속하시겠습니까? (y/n): " confirm

if [ "$confirm" != "y" ]; then
    echo -e "${YELLOW}취소되었습니다.${NC}"
    exit 0
fi

# 각 Lambda 함수 업데이트
for func in "${LAMBDA_FUNCTIONS[@]}"; do
    echo -e "${YELLOW}[$func] 환경변수 업데이트 중...${NC}"
    
    # 현재 환경변수 가져오기
    CURRENT_ENV=$(aws lambda get-function-configuration \
        --function-name "$func" \
        --region "$REGION" \
        --query "Environment.Variables" \
        --output json 2>/dev/null || echo "{}")
    
    # 새 환경변수와 병합
    MERGED_ENV=$(echo "$CURRENT_ENV $ENV_VARS" | jq -s '.[0] * .[1]')
    
    # 환경변수 업데이트
    aws lambda update-function-configuration \
        --function-name "$func" \
        --region "$REGION" \
        --environment "Variables=$MERGED_ENV" \
        --output json > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $func 업데이트 완료${NC}"
    else
        echo -e "${RED}✗ $func 업데이트 실패${NC}"
    fi
    
    sleep 1
done

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   환경변수 업데이트 완료!${NC}"
echo -e "${GREEN}========================================${NC}"