#!/bin/bash

#############################################
# B1.SEDAILY.AI 전체 배포 스크립트
#############################################

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   B1.SEDAILY.AI 전체 배포${NC}"
echo -e "${GREEN}========================================${NC}"

# 배포 스크립트 실행 권한 확인
chmod +x deploy-backend.sh
chmod +x deploy-frontend.sh
chmod +x update-env.sh

# 백엔드 배포
echo -e "${YELLOW}[1/2] 백엔드 배포 시작...${NC}"
./deploy-backend.sh
if [ $? -ne 0 ]; then
    echo -e "${RED}백엔드 배포 실패${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}백엔드 배포 완료. 프론트엔드 배포를 시작하시겠습니까?${NC}"
read -p "계속하시겠습니까? (y/n): " continue_deploy

if [ "$continue_deploy" != "y" ]; then
    echo -e "${YELLOW}배포가 중단되었습니다.${NC}"
    exit 0
fi

# 프론트엔드 배포
echo -e "${YELLOW}[2/2] 프론트엔드 배포 시작...${NC}"
./deploy-frontend.sh
if [ $? -ne 0 ]; then
    echo -e "${RED}프론트엔드 배포 실패${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   전체 배포 완료!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}배포 완료 체크리스트:${NC}"
echo "  ✓ Lambda 함수 6개 업데이트"
echo "  ✓ S3 버킷 동기화"
echo "  ✓ CloudFront 캐시 무효화"
echo ""
echo -e "${YELLOW}테스트 URL:${NC}"
echo "  https://b1.sedaily.ai"
echo ""
echo -e "${YELLOW}확인사항:${NC}"
echo "  1. 웹사이트 접속 테스트"
echo "  2. WebSocket 연결 테스트"
echo "  3. AI 대화 기능 테스트"
echo "  4. CloudWatch 로그 확인"