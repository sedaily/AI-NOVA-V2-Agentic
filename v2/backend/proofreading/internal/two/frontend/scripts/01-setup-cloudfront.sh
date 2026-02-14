#!/bin/bash

BUCKET_NAME="nexus-title-hub-frontend"
REGION="us-east-1"

echo "☁️ CloudFront 배포 생성 중..."

# CloudFront Origin Access Identity 생성
OAI_COMMENT="OAI for $BUCKET_NAME"
OAI_ID=$(aws cloudfront create-cloud-front-origin-access-identity \
    --cloud-front-origin-access-identity-config \
    CallerReference="$(date +%s)",Comment="$OAI_COMMENT" \
    --query 'CloudFrontOriginAccessIdentity.Id' \
    --output text 2>/dev/null)

if [ -z "$OAI_ID" ]; then
    echo "기존 OAI 사용 또는 새 OAI 생성 실패"
    OAI_ID="E2QWRUHAPOMQZL"  # 기본값 (실제 값으로 대체 필요)
fi

echo "OAI ID: $OAI_ID"

# CloudFront 배포 설정 파일 생성
cat > cloudfront-config.json <<EOF
{
    "CallerReference": "$(date +%s)",
    "Comment": "Nexus Title Hub Frontend",
    "DefaultRootObject": "index.html",
    "Origins": {
        "Quantity": 1,
        "Items": [
            {
                "Id": "S3-$BUCKET_NAME",
                "DomainName": "$BUCKET_NAME.s3.amazonaws.com",
                "S3OriginConfig": {
                    "OriginAccessIdentity": "origin-access-identity/cloudfront/$OAI_ID"
                }
            }
        ]
    },
    "DefaultCacheBehavior": {
        "TargetOriginId": "S3-$BUCKET_NAME",
        "ViewerProtocolPolicy": "redirect-to-https",
        "AllowedMethods": {
            "Quantity": 7,
            "Items": ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"],
            "CachedMethods": {
                "Quantity": 2,
                "Items": ["GET", "HEAD"]
            }
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
    "PriceClass": "PriceClass_100",
    "HttpVersion": "http2",
    "IsIPV6Enabled": true
}
EOF

# CloudFront 배포 생성
DISTRIBUTION_ID=$(aws cloudfront create-distribution \
    --distribution-config file://cloudfront-config.json \
    --query 'Distribution.Id' \
    --output text)

if [ -n "$DISTRIBUTION_ID" ]; then
    echo "✅ CloudFront 배포 생성 완료!"
    echo "Distribution ID: $DISTRIBUTION_ID"
    
    # deploy-s3.sh 파일 업데이트
    sed -i '' "s/CLOUDFRONT_DISTRIBUTION_ID=\"\"/CLOUDFRONT_DISTRIBUTION_ID=\"$DISTRIBUTION_ID\"/" deploy-s3.sh
    
    DOMAIN_NAME=$(aws cloudfront get-distribution \
        --id "$DISTRIBUTION_ID" \
        --query 'Distribution.DomainName' \
        --output text)
    
    echo ""
    echo "🎉 CloudFront 설정 완료!"
    echo "CloudFront URL: https://$DOMAIN_NAME"
    echo ""
    echo "⏳ 배포가 완전히 활성화되기까지 15-20분 정도 걸립니다."
    echo ""
    echo "📝 S3 버킷 정책을 CloudFront OAI용으로 업데이트해야 합니다:"
    echo "   1. S3 콘솔에서 버킷 선택"
    echo "   2. 권한 탭 → 버킷 정책"
    echo "   3. OAI를 사용하도록 정책 수정"
else
    echo "❌ CloudFront 배포 생성 실패"
fi

# 임시 파일 삭제
rm -f cloudfront-config.json