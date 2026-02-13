#!/bin/bash

#############################################
# B1.SEDAILY.AI 프론트엔드 배포 스크립트
# S3 및 CloudFront 배포
#############################################

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   B1.SEDAILY.AI 프론트엔드 배포 시작${NC}"
echo -e "${GREEN}========================================${NC}"

# 설정
REGION="us-east-1"
S3_BUCKET="b1.sedaily.ai"
CLOUDFRONT_DISTRIBUTION_ID="E3R1GGMJXE66MJ"
FRONTEND_DIR="../frontend"

# 현재 디렉토리 저장
CURRENT_DIR=$(pwd)
echo -e "${YELLOW}현재 디렉토리: $CURRENT_DIR${NC}"

# frontend 디렉토리로 이동
cd "$FRONTEND_DIR" || { echo -e "${RED}Frontend 디렉토리를 찾을 수 없습니다.${NC}"; exit 1; }

# .env 파일 확인
if [ ! -f .env ]; then
    echo -e "${RED}.env 파일이 없습니다!${NC}"
    echo -e "${YELLOW}다음 내용으로 .env 파일을 생성하세요:${NC}"
    echo "VITE_API_BASE_URL=https://pisnqqgu75.execute-api.us-east-1.amazonaws.com/prod"
    echo "VITE_PROMPT_API_URL=https://pisnqqgu75.execute-api.us-east-1.amazonaws.com/prod"
    echo "VITE_WS_URL=wss://dwc2m51as4.execute-api.us-east-1.amazonaws.com/prod"
    echo "VITE_ADMIN_EMAIL=ai@sedaily.com"
    echo "VITE_COMPANY_DOMAIN=sedaily.com"
    exit 1
fi

# Node modules 확인 및 설치
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}의존성 설치 중...${NC}"
    npm install
fi

# 기존 빌드 제거
echo -e "${YELLOW}기존 빌드 정리...${NC}"
rm -rf dist

# 프론트엔드 빌드
echo -e "${YELLOW}프론트엔드 빌드 중...${NC}"
npm run build

if [ ! -d "dist" ]; then
    echo -e "${RED}빌드 실패: dist 디렉토리가 생성되지 않았습니다.${NC}"
    exit 1
fi

# S3 버킷 확인
echo -e "${YELLOW}S3 버킷 확인 중...${NC}"
if ! aws s3api head-bucket --bucket "$S3_BUCKET" --region "$REGION" 2>/dev/null; then
    echo -e "${RED}S3 버킷 $S3_BUCKET을 찾을 수 없습니다.${NC}"
    exit 1
fi

# S3에 업로드
echo -e "${YELLOW}S3에 파일 업로드 중...${NC}"
aws s3 sync dist/ s3://$S3_BUCKET/ \
    --region $REGION \
    --delete \
    --cache-control "max-age=31536000" \
    --exclude "*.html" \
    --exclude "*.json"

# HTML과 JSON 파일은 캐시 없이
aws s3 sync dist/ s3://$S3_BUCKET/ \
    --region $REGION \
    --exclude "*" \
    --include "*.html" \
    --include "*.json" \
    --cache-control "no-cache, no-store, must-revalidate"

echo -e "${GREEN}S3 업로드 완료!${NC}"

# CloudFront 무효화
if [ -n "$CLOUDFRONT_DISTRIBUTION_ID" ]; then
    echo -e "${YELLOW}CloudFront 캐시 무효화 중...${NC}"
    
    INVALIDATION_ID=$(aws cloudfront create-invalidation \
        --distribution-id $CLOUDFRONT_DISTRIBUTION_ID \
        --paths "/*" \
        --query 'Invalidation.Id' \
        --output text)
    
    echo -e "${GREEN}CloudFront 무효화 시작: $INVALIDATION_ID${NC}"
    echo -e "${YELLOW}무효화 완료까지 약 5-10분 소요됩니다.${NC}"
else
    echo -e "${YELLOW}CloudFront Distribution ID가 설정되지 않았습니다.${NC}"
fi

# 원래 디렉토리로 복귀
cd "$CURRENT_DIR"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   프론트엔드 배포 완료!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}배포 정보:${NC}"
echo "  - S3 버킷: $S3_BUCKET"
echo "  - CloudFront ID: $CLOUDFRONT_DISTRIBUTION_ID"
echo "  - 웹사이트 URL: https://b1.sedaily.ai"
echo ""
echo -e "${YELLOW}확인사항:${NC}"
echo "  1. https://b1.sedaily.ai 접속 테스트"
echo "  2. 캐시 무효화 완료 대기 (5-10분)"
echo "  3. 브라우저 캐시 삭제 후 테스트"