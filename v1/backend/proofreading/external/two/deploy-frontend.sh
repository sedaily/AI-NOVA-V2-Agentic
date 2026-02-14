#!/bin/bash

# ============================================
# NX-WT-PRF External Frontend Deployment
# External version - Full features with login
# Target: p1.sedaily.ai
# ============================================

# 색상 설정
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}프론트엔드 CloudFront 배포 스크립트${NC}"
echo -e "${BLUE}=================================${NC}"

# 설정
BUCKET_NAME="nx-prf-prod-frontend-2025"  # 실제 CloudFront Origin 버킷
REGION="us-east-1"
FRONTEND_DIR="./frontend"
CLOUDFRONT_DISTRIBUTION_ID="E39OHKSWZD4F8J"  # p1.sedaily.ai CloudFront

# 1. S3 버킷 생성
echo -e "\n${BLUE}1. S3 버킷 생성 중...${NC}"
aws s3api head-bucket --bucket $BUCKET_NAME 2>/dev/null
if [ $? -ne 0 ]; then
    aws s3api create-bucket \
        --bucket $BUCKET_NAME \
        --region $REGION \
        --acl private

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ S3 버킷 생성 완료${NC}"
    else
        echo -e "${RED}❌ S3 버킷 생성 실패${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}ℹ️  S3 버킷이 이미 존재합니다${NC}"
fi

# 2. S3 버킷 정적 웹사이트 호스팅 설정
echo -e "\n${BLUE}2. S3 정적 웹사이트 호스팅 설정...${NC}"
aws s3 website s3://$BUCKET_NAME \
    --index-document index.html \
    --error-document index.html

# S3 버킷 정책 설정 (Public Read for S3 Website Endpoint)
cat > /tmp/bucket-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$BUCKET_NAME/*"
        }
    ]
}
EOF

aws s3api put-bucket-policy \
    --bucket $BUCKET_NAME \
    --policy file:///tmp/bucket-policy.json

echo -e "${GREEN}✅ S3 설정 완료${NC}"

# 3. 프론트엔드 빌드
echo -e "\n${BLUE}3. 프론트엔드 빌드 중...${NC}"
cd $FRONTEND_DIR
echo -e "${YELLOW}의존성 설치 중...${NC}"
npm install
npm run build

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 빌드 완료${NC}"
else
    echo -e "${RED}❌ 빌드 실패${NC}"
    exit 1
fi

# 4. S3에 빌드 파일 업로드
echo -e "\n${BLUE}4. S3에 파일 업로드 중...${NC}"
aws s3 sync dist/ s3://$BUCKET_NAME \
    --delete \
    --cache-control "public, max-age=31536000" \
    --exclude "index.html" \
    --exclude "*.js" \
    --exclude "*.css"

# HTML, JS, CSS 파일은 캐시 시간을 짧게
aws s3 cp dist/index.html s3://$BUCKET_NAME/index.html \
    --cache-control "no-cache, no-store, must-revalidate" \
    --content-type "text/html"

aws s3 sync dist/ s3://$BUCKET_NAME \
    --exclude "*" \
    --include "*.js" \
    --include "*.css" \
    --cache-control "public, max-age=86400"

echo -e "${GREEN}✅ S3 업로드 완료${NC}"

# 5. CloudFront 캐시 무효화
echo -e "\n${BLUE}5. CloudFront 캐시 무효화 중...${NC}"
echo -e "${YELLOW}Distribution ID: $CLOUDFRONT_DISTRIBUTION_ID${NC}"

aws cloudfront create-invalidation \
    --distribution-id $CLOUDFRONT_DISTRIBUTION_ID \
    --paths "/*" > /dev/null

echo -e "${GREEN}✅ 캐시 무효화 요청 완료${NC}"

# 6. CloudFront 도메인 정보 출력
echo -e "\n${BLUE}=================================${NC}"
echo -e "${GREEN}✅ 배포 완료!${NC}"
echo -e "${BLUE}=================================${NC}"

echo -e "\n${YELLOW}접속 정보:${NC}"
echo -e "도메인: ${GREEN}https://p1.sedaily.ai${NC}"
echo -e "S3 버킷: ${GREEN}$BUCKET_NAME${NC}"
echo -e "Distribution ID: ${GREEN}$CLOUDFRONT_DISTRIBUTION_ID${NC}"

# 정리
rm -f /tmp/bucket-policy.json

cd ..