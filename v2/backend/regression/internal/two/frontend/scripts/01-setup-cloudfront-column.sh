#!/bin/bash

BUCKET_NAME="sedaily-column-frontend"
REGION="us-east-1"
CUSTOM_DOMAIN="col1.sedaily.ai"
CERTIFICATE_ARN=""  # SSL 인증서 ARN (필요시 추가)

echo "☁️ CloudFront 배포 생성 중 (Column Service)..."

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
    "Comment": "SEDAILY Column Service Frontend",
    "DefaultRootObject": "index.html",
    "Aliases": {
        "Quantity": 1,
        "Items": ["$CUSTOM_DOMAIN"]
    },
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
            },
            "Headers": {
                "Quantity": 0
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
    "CacheBehaviors": {
        "Quantity": 1,
        "Items": [
            {
                "PathPattern": "*.js",
                "TargetOriginId": "S3-$BUCKET_NAME",
                "ViewerProtocolPolicy": "redirect-to-https",
                "AllowedMethods": {
                    "Quantity": 2,
                    "Items": ["GET", "HEAD"],
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
                "DefaultTTL": 31536000,
                "MaxTTL": 31536000,
                "Compress": true
            }
        ]
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

# SSL 인증서가 있는 경우 추가
if [ -n "$CERTIFICATE_ARN" ]; then
    echo "SSL 인증서 설정 추가 중..."
    # ViewerCertificate 섹션을 추가하는 jq 명령
    jq --arg arn "$CERTIFICATE_ARN" \
        '. + {ViewerCertificate: {ACMCertificateArn: $arn, SSLSupportMethod: "sni-only", MinimumProtocolVersion: "TLSv1.2_2021"}}' \
        cloudfront-config.json > cloudfront-config-ssl.json
    mv cloudfront-config-ssl.json cloudfront-config.json
fi

# CloudFront 배포 생성
DISTRIBUTION_ID=$(aws cloudfront create-distribution \
    --distribution-config file://cloudfront-config.json \
    --query 'Distribution.Id' \
    --output text 2>/dev/null)

if [ -n "$DISTRIBUTION_ID" ]; then
    echo "✅ CloudFront 배포 생성 완료!"
    echo "Distribution ID: $DISTRIBUTION_ID"

    # 배포 정보 저장
    cat > cloudfront-info.txt <<EOF
CLOUDFRONT_DISTRIBUTION_ID=$DISTRIBUTION_ID
CUSTOM_DOMAIN=$CUSTOM_DOMAIN
S3_BUCKET=$BUCKET_NAME
EOF

    DOMAIN_NAME=$(aws cloudfront get-distribution \
        --id "$DISTRIBUTION_ID" \
        --query 'Distribution.DomainName' \
        --output text)

    echo ""
    echo "🎉 CloudFront 설정 완료!"
    echo "CloudFront URL: https://$DOMAIN_NAME"
    echo "Custom Domain: https://$CUSTOM_DOMAIN"
    echo ""
    echo "📌 다음 단계:"
    echo "1. Route 53에서 col1.sedaily.ai 도메인의 A 레코드를 CloudFront 배포로 지정"
    echo "2. ACM에서 col1.sedaily.ai 용 SSL 인증서 발급 (us-east-1 리전)"
    echo "3. CloudFront 배포에 SSL 인증서 연결"
    echo ""
    echo "⏳ 배포가 완전히 활성화되기까지 15-20분 정도 걸립니다."
else
    echo "❌ CloudFront 배포 생성 실패"
    echo "기존 배포 확인 중..."

    # 기존 배포 확인
    EXISTING_DISTRIBUTION=$(aws cloudfront list-distributions \
        --query "DistributionList.Items[?Comment=='SEDAILY Column Service Frontend'].Id" \
        --output text)

    if [ -n "$EXISTING_DISTRIBUTION" ]; then
        echo "✅ 기존 배포 발견: $EXISTING_DISTRIBUTION"
        DISTRIBUTION_ID=$EXISTING_DISTRIBUTION
    fi
fi

# 임시 파일 삭제
rm -f cloudfront-config.json

echo ""
echo "💡 Tip: Route 53 설정 예시"
echo "- Type: A"
echo "- Name: col1.sedaily.ai"
echo "- Alias: Yes"
echo "- Alias Target: CloudFront 배포 ($DOMAIN_NAME)"