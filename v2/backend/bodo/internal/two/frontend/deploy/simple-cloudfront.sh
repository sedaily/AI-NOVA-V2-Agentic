#!/bin/bash

# 색상 코드 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BUCKET_NAME="bodo-frontend-20251204-230645dc"
REGION="ap-northeast-2"

echo -e "${GREEN}🚀 새 CloudFront 배포 생성 중...${NC}"

# CloudFront 배포 생성 (S3 직접 연결)
cat > /tmp/cf-config.json <<EOF
{
    "CallerReference": "${BUCKET_NAME}-$(date +%s)",
    "Comment": "Bodo Frontend Simple Distribution",
    "DefaultRootObject": "index.html",
    "Origins": {
        "Quantity": 1,
        "Items": [
            {
                "Id": "S3-${BUCKET_NAME}",
                "DomainName": "${BUCKET_NAME}.s3.ap-northeast-2.amazonaws.com",
                "S3OriginConfig": {
                    "OriginAccessIdentity": ""
                },
                "ConnectionAttempts": 3,
                "ConnectionTimeout": 10,
                "OriginCustomHeaders": {
                    "Quantity": 0
                }
            }
        ]
    },
    "DefaultCacheBehavior": {
        "TargetOriginId": "S3-${BUCKET_NAME}",
        "ViewerProtocolPolicy": "redirect-to-https",
        "TrustedSigners": {
            "Enabled": false,
            "Quantity": 0
        },
        "ForwardedValues": {
            "QueryString": false,
            "Cookies": {
                "Forward": "none"
            },
            "Headers": {
                "Quantity": 0
            }
        },
        "MinTTL": 0,
        "AllowedMethods": {
            "Quantity": 2,
            "Items": ["GET", "HEAD"],
            "CachedMethods": {
                "Quantity": 2,
                "Items": ["GET", "HEAD"]
            }
        },
        "SmoothStreaming": false,
        "DefaultTTL": 86400,
        "MaxTTL": 31536000,
        "Compress": true
    },
    "CustomErrorResponses": {
        "Quantity": 2,
        "Items": [
            {
                "ErrorCode": 404,
                "ResponseCode": "200",
                "ResponsePagePath": "/index.html",
                "ErrorCachingMinTTL": 10
            },
            {
                "ErrorCode": 403,
                "ResponseCode": "200",
                "ResponsePagePath": "/index.html",
                "ErrorCachingMinTTL": 10
            }
        ]
    },
    "Enabled": true,
    "PriceClass": "PriceClass_All",
    "HttpVersion": "http2",
    "IsIPV6Enabled": true
}
EOF

# CloudFront 생성
CF_RESULT=$(aws cloudfront create-distribution \
    --distribution-config file:///tmp/cf-config.json \
    --output json 2>&1)

if [[ "$CF_RESULT" == *"error"* ]] || [[ "$CF_RESULT" == *"Error"* ]]; then
    echo -e "${RED}CloudFront 생성 실패:${NC}"
    echo "$CF_RESULT"
    exit 1
fi

CF_ID=$(echo $CF_RESULT | jq -r '.Distribution.Id')
CF_DOMAIN=$(echo $CF_RESULT | jq -r '.Distribution.DomainName')

# 배포 정보 저장
cat > deployment-info.json <<EOF
{
    "bucketName": "${BUCKET_NAME}",
    "region": "${REGION}",
    "cloudFrontId": "${CF_ID}",
    "cloudFrontDomain": "${CF_DOMAIN}",
    "s3DirectUrl": "http://${BUCKET_NAME}.s3.ap-northeast-2.amazonaws.com/index.html",
    "deployedAt": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF

echo -e "${GREEN}✅ 새 CloudFront 배포가 생성되었습니다!${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}CloudFront URL: https://${CF_DOMAIN}${NC}"
echo -e "${GREEN}S3 Direct URL: http://${BUCKET_NAME}.s3.ap-northeast-2.amazonaws.com/index.html${NC}"
echo -e "${GREEN}CloudFront ID: ${CF_ID}${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}⚠️  CloudFront가 전파되는데 15-20분이 소요됩니다.${NC}"
echo -e "${GREEN}✅  S3 Direct URL은 지금 바로 사용 가능합니다!${NC}"

rm /tmp/cf-config.json