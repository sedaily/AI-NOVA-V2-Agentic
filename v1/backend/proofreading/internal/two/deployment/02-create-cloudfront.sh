#!/bin/bash

# CloudFront 배포 생성 스크립트
# 사용법: ./02-create-cloudfront.sh

set -e

# deployment-config.json에서 설정 읽기
if [ ! -f "deployment-config.json" ]; then
    echo "❌ deployment-config.json 파일이 없습니다."
    echo "먼저 ./01-create-s3-bucket.sh를 실행하세요."
    exit 1
fi

# JSON 파싱 (macOS와 Linux 호환)
BUCKET_NAME=$(grep -o '"bucketName": *"[^"]*"' deployment-config.json | sed 's/.*: *"\(.*\)"/\1/')
REGION=$(grep -o '"region": *"[^"]*"' deployment-config.json | sed 's/.*: *"\(.*\)"/\1/')
PROFILE=$(grep -o '"profile": *"[^"]*"' deployment-config.json | sed 's/.*: *"\(.*\)"/\1/')

echo "================================================"
echo "CloudFront 배포 생성 스크립트"
echo "================================================"
echo ""
echo "S3 버킷: $BUCKET_NAME"
echo "리전: $REGION"
echo "AWS 프로필: $PROFILE"
echo ""
echo "계속하시겠습니까? (y/n)"
read -r response

if [[ "$response" != "y" ]]; then
    echo "취소되었습니다."
    exit 0
fi

# 1. Origin Access Control (OAC) 생성
echo ""
echo "1. Origin Access Control 생성 중..."

OAC_CONFIG=$(cat <<EOF
{
    "Name": "OAC-${BUCKET_NAME}",
    "Description": "OAC for ${BUCKET_NAME}",
    "SigningProtocol": "sigv4",
    "SigningBehavior": "always",
    "OriginAccessControlOriginType": "s3"
}
EOF
)

OAC_ID=$(aws cloudfront create-origin-access-control \
    --origin-access-control-config "$OAC_CONFIG" \
    --profile "$PROFILE" \
    --query 'OriginAccessControl.Id' \
    --output text 2>/dev/null) || {
    echo "⚠️ OAC 생성 실패 또는 이미 존재. 기존 OAC 사용 시도..."
    OAC_ID=""
}

if [ -n "$OAC_ID" ]; then
    echo "✓ OAC 생성 완료: $OAC_ID"
else
    echo "⚠️ OAC를 수동으로 설정해야 할 수 있습니다."
fi

# 2. CloudFront 배포 설정 파일 생성
echo ""
echo "2. CloudFront 배포 설정 파일 생성 중..."

CALLER_REFERENCE="nexus-multi-$(date +%s)"
DISTRIBUTION_CONFIG=$(cat <<EOF
{
    "CallerReference": "$CALLER_REFERENCE",
    "Comment": "Nexus Multi Frontend Distribution",
    "Enabled": true,
    "Origins": {
        "Quantity": 1,
        "Items": [
            {
                "Id": "S3-${BUCKET_NAME}",
                "DomainName": "${BUCKET_NAME}.s3.${REGION}.amazonaws.com",
                "S3OriginConfig": {
                    "OriginAccessIdentity": ""
                },
                "OriginAccessControlId": "${OAC_ID}"
            }
        ]
    },
    "DefaultRootObject": "index.html",
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
        "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",
        "OriginRequestPolicyId": "88a5eaf4-2fd4-4709-b370-b4c650ea3fcf",
        "ResponseHeadersPolicyId": "67f7725c-6f97-4210-82d7-5512b31e9d03",
        "TrustedSigners": {
            "Enabled": false,
            "Quantity": 0
        },
        "TrustedKeyGroups": {
            "Enabled": false,
            "Quantity": 0
        }
    },
    "CustomErrorResponses": {
        "Quantity": 1,
        "Items": [
            {
                "ErrorCode": 403,
                "ResponsePagePath": "/index.html",
                "ResponseCode": "200",
                "ErrorCachingMinTTL": 10
            }
        ]
    },
    "PriceClass": "PriceClass_All",
    "HttpVersion": "http2and3",
    "IsIPV6Enabled": true
}
EOF
)

echo "$DISTRIBUTION_CONFIG" > cloudfront-config-temp.json
echo "✓ CloudFront 설정 파일 생성 완료"

# 3. CloudFront 배포 생성
echo ""
echo "3. CloudFront 배포 생성 중... (5-10분 소요)"

DISTRIBUTION_ID=$(aws cloudfront create-distribution \
    --distribution-config file://cloudfront-config-temp.json \
    --profile "$PROFILE" \
    --query 'Distribution.Id' \
    --output text)

DISTRIBUTION_DOMAIN=$(aws cloudfront get-distribution \
    --id "$DISTRIBUTION_ID" \
    --profile "$PROFILE" \
    --query 'Distribution.DomainName' \
    --output text)

echo "✓ CloudFront 배포 생성 완료"
echo "  배포 ID: $DISTRIBUTION_ID"
echo "  도메인: https://$DISTRIBUTION_DOMAIN"

# 4. S3 버킷 정책 업데이트 (CloudFront OAC 접근 허용)
echo ""
echo "4. S3 버킷 정책 업데이트 중..."

ACCOUNT_ID=$(aws sts get-caller-identity --profile "$PROFILE" --query 'Account' --output text)

cat > bucket-policy-final.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowCloudFrontServicePrincipal",
            "Effect": "Allow",
            "Principal": {
                "Service": "cloudfront.amazonaws.com"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::${BUCKET_NAME}/*",
            "Condition": {
                "StringEquals": {
                    "AWS:SourceArn": "arn:aws:cloudfront::${ACCOUNT_ID}:distribution/${DISTRIBUTION_ID}"
                }
            }
        }
    ]
}
EOF

aws s3api put-bucket-policy \
    --bucket "$BUCKET_NAME" \
    --policy file://bucket-policy-final.json \
    --profile "$PROFILE"

echo "✓ S3 버킷 정책 업데이트 완료"

# 5. 배포 정보 저장
echo ""
echo "5. 배포 정보 저장 중..."

# 기존 설정 파일 업데이트
cat > deployment-config.json <<EOF
{
    "bucketName": "$BUCKET_NAME",
    "region": "$REGION",
    "profile": "$PROFILE",
    "distributionId": "$DISTRIBUTION_ID",
    "distributionDomain": "$DISTRIBUTION_DOMAIN",
    "cloudfrontUrl": "https://${DISTRIBUTION_DOMAIN}",
    "oac_id": "$OAC_ID",
    "createdAt": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF

echo "✓ 배포 정보 저장 완료: deployment-config.json"

# 6. 정리
rm -f cloudfront-config-temp.json bucket-policy-final.json bucket-policy-temp.json

echo ""
echo "================================================"
echo "CloudFront 배포 생성 완료!"
echo "================================================"
echo "배포 ID: $DISTRIBUTION_ID"
echo "CloudFront URL: https://$DISTRIBUTION_DOMAIN"
echo ""
echo "⚠️ 주의: CloudFront 배포가 완전히 활성화되는데 15-20분 정도 소요됩니다."
echo ""
echo "다음 단계: ./03-deploy-frontend.sh 실행"
echo "================================================"