#!/bin/bash

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
BUCKET_NAME="nx-wt-prf-frontend-prod"  # 새로운 버킷 이름
REGION="us-east-1"
FRONTEND_DIR="./frontend"
CLOUDFRONT_DISTRIBUTION_ID=""  # 생성 후 자동으로 설정됨

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

# S3 버킷 정책 설정 (CloudFront OAI 사용)
cat > /tmp/bucket-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowCloudFrontOAI",
            "Effect": "Allow",
            "Principal": {
                "AWS": "*"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$BUCKET_NAME/*",
            "Condition": {
                "StringLike": {
                    "AWS:SourceArn": "arn:aws:cloudfront::*:distribution/*"
                }
            }
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

# 5. CloudFront 배포 생성
echo -e "\n${BLUE}5. CloudFront 배포 확인/생성...${NC}"

# 기존 배포 확인
DISTRIBUTION_ID=$(aws cloudfront list-distributions \
    --query "DistributionList.Items[?Origins.Items[0].DomainName=='$BUCKET_NAME.s3.amazonaws.com'].Id" \
    --output text)

if [ -z "$DISTRIBUTION_ID" ]; then
    echo -e "${YELLOW}CloudFront 배포 생성 중...${NC}"

    # CloudFront 설정 파일 생성
    cat > /tmp/cf-config.json << EOF
{
    "CallerReference": "nx-wt-prf-$(date +%s)",
    "Comment": "NX WT PRF Frontend Distribution",
    "Enabled": true,
    "Origins": {
        "Quantity": 1,
        "Items": [
            {
                "Id": "S3-$BUCKET_NAME",
                "DomainName": "$BUCKET_NAME.s3.amazonaws.com",
                "S3OriginConfig": {
                    "OriginAccessIdentity": ""
                }
            }
        ]
    },
    "DefaultRootObject": "index.html",
    "DefaultCacheBehavior": {
        "TargetOriginId": "S3-$BUCKET_NAME",
        "ViewerProtocolPolicy": "redirect-to-https",
        "AllowedMethods": {
            "Quantity": 2,
            "Items": ["HEAD", "GET"]
        },
        "ForwardedValues": {
            "QueryString": false,
            "Cookies": {
                "Forward": "none"
            }
        },
        "TrustedSigners": {
            "Enabled": false,
            "Quantity": 0
        },
        "MinTTL": 0,
        "DefaultTTL": 86400,
        "MaxTTL": 31536000,
        "Compress": true
    },
    "CustomErrorResponses": {
        "Quantity": 1,
        "Items": [
            {
                "ErrorCode": 404,
                "ResponseCode": "200",
                "ResponsePagePath": "/index.html",
                "ErrorCachingMinTTL": 300
            }
        ]
    },
    "PriceClass": "PriceClass_100"
}
EOF

    # CloudFront 배포 생성
    DISTRIBUTION_OUTPUT=$(aws cloudfront create-distribution \
        --distribution-config file:///tmp/cf-config.json)

    DISTRIBUTION_ID=$(echo $DISTRIBUTION_OUTPUT | jq -r '.Distribution.Id')
    DOMAIN_NAME=$(echo $DISTRIBUTION_OUTPUT | jq -r '.Distribution.DomainName')

    echo -e "${GREEN}✅ CloudFront 배포 생성 완료${NC}"
    echo -e "${BLUE}Distribution ID: $DISTRIBUTION_ID${NC}"
    echo -e "${BLUE}Domain Name: $DOMAIN_NAME${NC}"
else
    echo -e "${YELLOW}ℹ️  기존 CloudFront 배포 사용: $DISTRIBUTION_ID${NC}"

    # 캐시 무효화
    echo -e "${BLUE}캐시 무효화 중...${NC}"
    aws cloudfront create-invalidation \
        --distribution-id $DISTRIBUTION_ID \
        --paths "/*" > /dev/null

    echo -e "${GREEN}✅ 캐시 무효화 요청 완료${NC}"
fi

# 6. CloudFront 도메인 정보 출력
echo -e "\n${BLUE}=================================${NC}"
echo -e "${GREEN}✅ 배포 완료!${NC}"
echo -e "${BLUE}=================================${NC}"

if [ ! -z "$DISTRIBUTION_ID" ]; then
    DOMAIN_NAME=$(aws cloudfront get-distribution \
        --id $DISTRIBUTION_ID \
        --query 'Distribution.DomainName' \
        --output text)

    echo -e "\n${YELLOW}접속 정보:${NC}"
    echo -e "CloudFront URL: ${GREEN}https://$DOMAIN_NAME${NC}"
    echo -e "S3 버킷: ${GREEN}$BUCKET_NAME${NC}"
    echo -e "Distribution ID: ${GREEN}$DISTRIBUTION_ID${NC}"

    echo -e "\n${YELLOW}다음 단계:${NC}"
    echo -e "1. CloudFront 배포가 완전히 활성화될 때까지 15-20분 대기"
    echo -e "2. https://$DOMAIN_NAME 접속 테스트"
    echo -e "3. 커스텀 도메인 연결 (Route 53)"
fi

# 정리
rm -f /tmp/bucket-policy.json /tmp/cf-config.json

cd ..