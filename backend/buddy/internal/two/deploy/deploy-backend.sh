#!/bin/bash

#############################################
# B1.SEDAILY.AI 백엔드 배포 스크립트
# Lambda Functions 코드 업데이트
#############################################

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   B1.SEDAILY.AI 백엔드 배포 시작${NC}"
echo -e "${GREEN}========================================${NC}"

# 설정
REGION="us-east-1"
BACKEND_DIR="../backend"

# Lambda 함수 목록 (b1.sedaily.ai 전용)
LAMBDA_FUNCTIONS=(
    "p2-two-websocket-message-two"
    "p2-two-conversation-api-two"
    "p2-two-prompt-crud-two"
    "p2-two-websocket-connect-two"
    "p2-two-websocket-disconnect-two"
    "p2-two-usage-handler-two"
)

# 현재 디렉토리 확인
CURRENT_DIR=$(pwd)
echo -e "${YELLOW}현재 디렉토리: $CURRENT_DIR${NC}"

# backend 디렉토리로 이동
cd "$BACKEND_DIR" || { echo -e "${RED}Backend 디렉토리를 찾을 수 없습니다.${NC}"; exit 1; }

# 기존 배포 패키지 삭제
echo -e "${YELLOW}기존 배포 패키지 정리...${NC}"
rm -f lambda-deployment.zip

# 새 배포 패키지 생성
echo -e "${YELLOW}배포 패키지 생성 중...${NC}"
zip -r lambda-deployment.zip . \
  -x "*.pyc" \
  -x "*__pycache__*" \
  -x "*.zip" \
  -x ".env*" \
  -x "backup_*/*" \
  -x "package/*" \
  -x "aws-setup/*" \
  -x "test_*.py" \
  -x ".git/*" \
  -x ".gitignore" \
  -q

if [ ! -f lambda-deployment.zip ]; then
    echo -e "${RED}배포 패키지 생성 실패${NC}"
    exit 1
fi

PACKAGE_SIZE=$(du -h lambda-deployment.zip | cut -f1)
echo -e "${GREEN}배포 패키지 생성 완료: lambda-deployment.zip (${PACKAGE_SIZE})${NC}"

# 각 Lambda 함수 업데이트
echo -e "${YELLOW}Lambda 함수 업데이트 시작...${NC}"

for func in "${LAMBDA_FUNCTIONS[@]}"; do
    echo -e "${YELLOW}[$func] 업데이트 중...${NC}"
    
    # 함수 존재 확인
    if aws lambda get-function --function-name "$func" --region "$REGION" &>/dev/null; then
        # 코드 업데이트
        aws lambda update-function-code \
            --function-name "$func" \
            --zip-file fileb://lambda-deployment.zip \
            --region "$REGION" \
            --output json > /dev/null 2>&1
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ $func 업데이트 완료${NC}"
        else
            echo -e "${RED}✗ $func 업데이트 실패${NC}"
        fi
    else
        echo -e "${RED}✗ $func 함수를 찾을 수 없습니다${NC}"
    fi
    
    # API 제한 방지를 위한 대기
    sleep 1
done

# 원래 디렉토리로 복귀
cd "$CURRENT_DIR"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   백엔드 배포 완료!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}배포된 Lambda 함수:${NC}"
for func in "${LAMBDA_FUNCTIONS[@]}"; do
    echo "  - $func"
done
echo ""
echo -e "${YELLOW}다음 단계:${NC}"
echo "  1. CloudWatch 로그에서 에러 확인"
echo "  2. 프론트엔드에서 기능 테스트"