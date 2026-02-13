#!/bin/bash

# 색상 코드 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# deployment-info.json 파일 확인
if [ ! -f "deployment-info.json" ]; then
    echo -e "${RED}❌ deployment-info.json 파일을 찾을 수 없습니다.${NC}"
    echo -e "${YELLOW}먼저 cloudfront-deploy.sh를 실행해주세요.${NC}"
    exit 1
fi

# 배포 정보 읽기
BUCKET_NAME=$(jq -r '.bucketName' deployment-info.json)
CF_ID=$(jq -r '.cloudFrontId' deployment-info.json)
CF_DOMAIN=$(jq -r '.cloudFrontDomain' deployment-info.json)

echo -e "${GREEN}🔄 기존 배포 업데이트 시작...${NC}"
echo -e "${YELLOW}S3 버킷: ${BUCKET_NAME}${NC}"
echo -e "${YELLOW}CloudFront ID: ${CF_ID}${NC}"

# 1. 빌드 실행
echo -e "${GREEN}1. 프론트엔드 빌드 중...${NC}"
cd ../
npm run build

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 빌드 실패${NC}"
    exit 1
fi

# 2. S3에 파일 업로드
echo -e "${GREEN}2. S3에 빌드 파일 업로드 중...${NC}"
aws s3 sync dist/ s3://${BUCKET_NAME}/ \
    --delete \
    --cache-control "public, max-age=31536000" \
    --exclude index.html

# index.html은 캐시하지 않음
aws s3 cp dist/index.html s3://${BUCKET_NAME}/ \
    --cache-control "no-cache, no-store, must-revalidate"

# 3. CloudFront 캐시 무효화
echo -e "${GREEN}3. CloudFront 캐시 무효화 중...${NC}"
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id ${CF_ID} \
    --paths "/*" \
    --output json | jq -r '.Invalidation.Id')

echo -e "${GREEN}✅ 업데이트가 성공적으로 완료되었습니다!${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}CloudFront URL: https://${CF_DOMAIN}${NC}"
echo -e "${GREEN}Invalidation ID: ${INVALIDATION_ID}${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}⚠️  캐시 무효화는 약 5-10분이 소요됩니다.${NC}"