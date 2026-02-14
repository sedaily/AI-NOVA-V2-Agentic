#!/bin/bash

# 새로운 S3 + CloudFront 배포 스크립트
# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   새로운 Frontend 배포 시작${NC}"
echo -e "${GREEN}========================================${NC}"

# 설정 변수
TIMESTAMP=$(date +%Y%m%d%H%M%S)
BUCKET_NAME="nexus-title-frontend-${TIMESTAMP}"
REGION="ap-northeast-2"
FRONTEND_DIR="./frontend"

# 1. S3 버킷 생성
echo -e "\n${YELLOW}1. S3 버킷 생성 중...${NC}"
aws s3api create-bucket \
    --bucket ${BUCKET_NAME} \
    --region ${REGION} \
    --create-bucket-configuration LocationConstraint=${REGION}

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ S3 버킷 생성 완료: ${BUCKET_NAME}${NC}"
else
    echo -e "${RED}✗ S3 버킷 생성 실패${NC}"
    exit 1
fi

# 2. 버킷 정책 설정 (CloudFront OAI용)
echo -e "\n${YELLOW}2. S3 버킷 정책 설정 중...${NC}"

# OAI 생성
OAI_ID=$(aws cloudfront create-cloud-front-origin-access-identity \
    --cloud-front-origin-access-identity-config \
    CallerReference="${BUCKET_NAME}-oai",Comment="OAI for ${BUCKET_NAME}" \
    --query 'CloudFrontOriginAccessIdentity.Id' \
    --output text)

echo -e "${GREEN}✓ OAI 생성 완료: ${OAI_ID}${NC}"

# S3 버킷 정책 적용
cat > /tmp/bucket-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowCloudFrontOAI",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity ${OAI_ID}"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::${BUCKET_NAME}/*"
        }
    ]
}
EOF

aws s3api put-bucket-policy \
    --bucket ${BUCKET_NAME} \
    --policy file:///tmp/bucket-policy.json

# 3. 정적 웹 호스팅 설정
echo -e "\n${YELLOW}3. S3 정적 웹 호스팅 설정 중...${NC}"
aws s3api put-bucket-website \
    --bucket ${BUCKET_NAME} \
    --website-configuration \
    '{"IndexDocument":{"Suffix":"index.html"},"ErrorDocument":{"Key":"index.html"}}'

# 4. Frontend 빌드
echo -e "\n${YELLOW}4. Frontend 빌드 중...${NC}"
cd ${FRONTEND_DIR}
npm run build

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Frontend 빌드 완료${NC}"
else
    echo -e "${RED}✗ Frontend 빌드 실패${NC}"
    exit 1
fi

# 5. S3에 업로드
echo -e "\n${YELLOW}5. S3에 파일 업로드 중...${NC}"
aws s3 sync dist/ s3://${BUCKET_NAME}/ \
    --delete \
    --cache-control "public, max-age=31536000" \
    --exclude "index.html" \
    --exclude "*.js" \
    --exclude "*.css"

# HTML, JS, CSS는 캐시 설정을 다르게
aws s3 cp dist/index.html s3://${BUCKET_NAME}/index.html \
    --cache-control "no-cache, no-store, must-revalidate" \
    --content-type "text/html"

aws s3 sync dist/ s3://${BUCKET_NAME}/ \
    --exclude "*" \
    --include "*.js" \
    --include "*.css" \
    --cache-control "public, max-age=86400"

echo -e "${GREEN}✓ S3 업로드 완료${NC}"

# 6. CloudFront 배포 생성
echo -e "\n${YELLOW}6. CloudFront 배포 생성 중...${NC}"

cat > /tmp/cloudfront-config.json << EOF
{
    "CallerReference": "${BUCKET_NAME}-cf-${TIMESTAMP}",
    "Comment": "CloudFront for ${BUCKET_NAME}",
    "DefaultRootObject": "index.html",
    "Origins": {
        "Quantity": 1,
        "Items": [
            {
                "Id": "S3-${BUCKET_NAME}",
                "DomainName": "${BUCKET_NAME}.s3.${REGION}.amazonaws.com",
                "S3OriginConfig": {
                    "OriginAccessIdentity": "origin-access-identity/cloudfront/${OAI_ID}"
                }
            }
        ]
    },
    "DefaultCacheBehavior": {
        "TargetOriginId": "S3-${BUCKET_NAME}",
        "ViewerProtocolPolicy": "redirect-to-https",
        "AllowedMethods": {
            "Quantity": 2,
            "Items": ["GET", "HEAD"],
            "CachedMethods": {
                "Quantity": 2,
                "Items": ["GET", "HEAD"]
            }
        },
        "Compress": true,
        "MinTTL": 0,
        "DefaultTTL": 86400,
        "MaxTTL": 31536000,
        "ForwardedValues": {
            "QueryString": false,
            "Cookies": {
                "Forward": "none"
            },
            "Headers": {
                "Quantity": 0
            }
        },
        "TrustedSigners": {
            "Enabled": false,
            "Quantity": 0
        }
    },
    "CustomErrorResponses": {
        "Quantity": 1,
        "Items": [
            {
                "ErrorCode": 404,
                "ResponsePagePath": "/index.html",
                "ResponseCode": "200",
                "ErrorCachingMinTTL": 300
            }
        ]
    },
    "Enabled": true,
    "PriceClass": "PriceClass_All"
}
EOF

DISTRIBUTION_ID=$(aws cloudfront create-distribution \
    --distribution-config file:///tmp/cloudfront-config.json \
    --query 'Distribution.Id' \
    --output text)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ CloudFront 배포 생성 완료${NC}"
    echo -e "${GREEN}  Distribution ID: ${DISTRIBUTION_ID}${NC}"
    
    # CloudFront 도메인 가져오기
    CF_DOMAIN=$(aws cloudfront get-distribution \
        --id ${DISTRIBUTION_ID} \
        --query 'Distribution.DomainName' \
        --output text)
    
    echo -e "${GREEN}  CloudFront URL: https://${CF_DOMAIN}${NC}"
else
    echo -e "${RED}✗ CloudFront 배포 생성 실패${NC}"
    exit 1
fi

# 7. 배포 정보 저장
echo -e "\n${YELLOW}7. 배포 정보 저장 중...${NC}"
cat > deployment-info-${TIMESTAMP}.json << EOF
{
    "timestamp": "${TIMESTAMP}",
    "s3_bucket": "${BUCKET_NAME}",
    "region": "${REGION}",
    "cloudfront_distribution_id": "${DISTRIBUTION_ID}",
    "cloudfront_domain": "${CF_DOMAIN}",
    "oai_id": "${OAI_ID}",
    "url": "https://${CF_DOMAIN}"
}
EOF

echo -e "${GREEN}✓ 배포 정보가 deployment-info-${TIMESTAMP}.json에 저장되었습니다${NC}"

# 완료
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}   배포 완료!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${YELLOW}접속 URL: ${GREEN}https://${CF_DOMAIN}${NC}"
echo -e "${YELLOW}S3 Bucket: ${GREEN}${BUCKET_NAME}${NC}"
echo -e "${YELLOW}Distribution ID: ${GREEN}${DISTRIBUTION_ID}${NC}"
echo -e "\n${YELLOW}참고: CloudFront 배포가 완전히 활성화되기까지 10-15분 정도 소요됩니다.${NC}"

# 정리
rm -f /tmp/bucket-policy.json /tmp/cloudfront-config.json

cd ..