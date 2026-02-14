#!/bin/bash

# 색상 코드 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 배포 설정
STACK_NAME="bodo-frontend-stack"
BUCKET_NAME="bodo-frontend-$(date +%Y%m%d)-$(openssl rand -hex 4)"
REGION="ap-northeast-2"  # 서울 리전

echo -e "${GREEN}🚀 새로운 CloudFront + S3 배포를 시작합니다...${NC}"
echo -e "${YELLOW}버킷 이름: ${BUCKET_NAME}${NC}"
echo -e "${YELLOW}리전: ${REGION}${NC}"

# 1. S3 버킷 생성
echo -e "${GREEN}1. S3 버킷 생성 중...${NC}"
aws s3api create-bucket \
    --bucket ${BUCKET_NAME} \
    --region ${REGION} \
    --create-bucket-configuration LocationConstraint=${REGION}

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ S3 버킷 생성 실패${NC}"
    exit 1
fi

# 2. 정적 웹사이트 호스팅 설정
echo -e "${GREEN}2. 정적 웹사이트 호스팅 설정 중...${NC}"
aws s3 website s3://${BUCKET_NAME}/ \
    --index-document index.html \
    --error-document index.html

# 3. S3 버킷을 퍼블릭으로 설정 (CloudFront 없이 직접 접근 가능)
echo -e "${GREEN}3. S3 버킷 퍼블릭 액세스 설정 중...${NC}"

# 퍼블릭 액세스 차단 해제
aws s3api put-public-access-block \
    --bucket ${BUCKET_NAME} \
    --public-access-block-configuration \
    "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

# 버킷 정책 설정
cat > /tmp/bucket-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::${BUCKET_NAME}/*"
        }
    ]
}
EOF

aws s3api put-bucket-policy --bucket ${BUCKET_NAME} --policy file:///tmp/bucket-policy.json

# 4. 빌드 실행
echo -e "${GREEN}4. 프론트엔드 빌드 중...${NC}"
cd ../
npm run build

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 빌드 실패${NC}"
    exit 1
fi

# 5. S3에 파일 업로드
echo -e "${GREEN}5. S3에 빌드 파일 업로드 중...${NC}"
aws s3 sync dist/ s3://${BUCKET_NAME}/ \
    --delete \
    --cache-control "public, max-age=31536000" \
    --exclude index.html

# index.html은 캐시하지 않음
aws s3 cp dist/index.html s3://${BUCKET_NAME}/ \
    --cache-control "no-cache, no-store, must-revalidate"

# 6. CloudFront 배포 생성
echo -e "${GREEN}6. CloudFront 배포 생성 중...${NC}"
cat > /tmp/cloudfront-config.json <<EOF
{
    "CallerReference": "${BUCKET_NAME}-$(date +%s)",
    "Comment": "Bodo Frontend Distribution",
    "DefaultRootObject": "index.html",
    "Origins": {
        "Quantity": 1,
        "Items": [
            {
                "Id": "S3-${BUCKET_NAME}",
                "DomainName": "${BUCKET_NAME}.s3-website-${REGION}.amazonaws.com",
                "CustomOriginConfig": {
                    "HTTPPort": 80,
                    "HTTPSPort": 443,
                    "OriginProtocolPolicy": "http-only"
                }
            }
        ]
    },
    "DefaultCacheBehavior": {
        "TargetOriginId": "S3-${BUCKET_NAME}",
        "ViewerProtocolPolicy": "redirect-to-https",
        "AllowedMethods": {
            "Quantity": 7,
            "Items": ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"],
            "CachedMethods": {
                "Quantity": 2,
                "Items": ["GET", "HEAD"]
            }
        },
        "Compress": true,
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
        "MinTTL": 0
    },
    "CustomErrorResponses": {
        "Quantity": 2,
        "Items": [
            {
                "ErrorCode": 404,
                "ResponseCode": "200",
                "ResponsePagePath": "/index.html",
                "ErrorCachingMinTTL": 300
            },
            {
                "ErrorCode": 403,
                "ResponseCode": "200",
                "ResponsePagePath": "/index.html",
                "ErrorCachingMinTTL": 300
            }
        ]
    },
    "Enabled": true,
    "PriceClass": "PriceClass_All"
}
EOF

CF_RESULT=$(aws cloudfront create-distribution \
    --distribution-config file:///tmp/cloudfront-config.json \
    --output json)

CF_ID=$(echo $CF_RESULT | jq -r '.Distribution.Id')
CF_DOMAIN=$(echo $CF_RESULT | jq -r '.Distribution.DomainName')

# 7. 배포 정보 저장
echo -e "${GREEN}7. 배포 정보 저장 중...${NC}"
cat > deployment-info.json <<EOF
{
    "bucketName": "${BUCKET_NAME}",
    "region": "${REGION}",
    "cloudFrontId": "${CF_ID}",
    "cloudFrontDomain": "${CF_DOMAIN}",
    "s3WebsiteUrl": "http://${BUCKET_NAME}.s3-website-${REGION}.amazonaws.com",
    "deployedAt": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF

echo -e "${GREEN}✅ 배포가 성공적으로 완료되었습니다!${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}CloudFront URL: https://${CF_DOMAIN}${NC}"
echo -e "${GREEN}S3 Website URL: http://${BUCKET_NAME}.s3-website-${REGION}.amazonaws.com${NC}"
echo -e "${GREEN}CloudFront ID: ${CF_ID}${NC}"
echo -e "${GREEN}S3 Bucket: ${BUCKET_NAME}${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}⚠️  CloudFront 배포가 전파되는데 약 15-20분이 소요됩니다.${NC}"
echo -e "${YELLOW}    S3 웹사이트는 바로 접속 가능합니다.${NC}"

# 정리
rm /tmp/bucket-policy.json
rm /tmp/cloudfront-config.json