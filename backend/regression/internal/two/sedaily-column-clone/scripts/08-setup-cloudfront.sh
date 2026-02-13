#!/bin/bash

# CloudFront 배포 설정

source "$(dirname "$0")/00-config.sh"

log_info "CloudFront 배포 설정 시작..."

# Origin Access Control 생성
log_info "Origin Access Control 생성 중..."

OAC_ID=$(aws cloudfront create-origin-access-control \
    --origin-access-control-config \
        Name="${SERVICE_NAME}-oac",\
Description="OAC for ${SERVICE_NAME}",\
SigningProtocol="sigv4",\
SigningBehavior="always",\
OriginAccessControlOriginType="s3" \
    --query 'OriginAccessControl.Id' \
    --output text \
    --region "$REGION" 2>/dev/null || echo "existing")

if [ "$OAC_ID" == "existing" ]; then
    log_warning "Origin Access Control이 이미 존재합니다. 기존 OAC 사용."
    OAC_ID=$(aws cloudfront list-origin-access-controls \
        --query "OriginAccessControlList.Items[?Name=='${SERVICE_NAME}-oac'].Id" \
        --output text --region "$REGION")
else
    log_success "Origin Access Control 생성 완료: $OAC_ID"
fi

# CloudFront 배포 생성
log_info "CloudFront 배포 생성 중..."

cat > /tmp/cf-config.json <<EOF
{
    "CallerReference": "${SERVICE_NAME}-$(date +%s)",
    "Comment": "CloudFront for ${SERVICE_NAME}",
    "DefaultRootObject": "index.html",
    "Origins": {
        "Quantity": 1,
        "Items": [
            {
                "Id": "S3-${S3_BUCKET}",
                "DomainName": "${S3_BUCKET}.s3.${REGION}.amazonaws.com",
                "S3OriginConfig": {
                    "OriginAccessIdentity": ""
                },
                "OriginAccessControlId": "${OAC_ID}"
            }
        ]
    },
    "DefaultCacheBehavior": {
        "TargetOriginId": "S3-${S3_BUCKET}",
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
        "OriginRequestPolicyId": "88a5eaf4-2fd4-4709-b370-b4c650ea3fcf"
    },
    "CustomErrorResponses": {
        "Quantity": 2,
        "Items": [
            {
                "ErrorCode": 403,
                "ResponseCode": "200",
                "ResponsePagePath": "/index.html",
                "ErrorCachingMinTTL": 300
            },
            {
                "ErrorCode": 404,
                "ResponseCode": "200",
                "ResponsePagePath": "/index.html",
                "ErrorCachingMinTTL": 300
            }
        ]
    },
    "Enabled": true,
    "PriceClass": "PriceClass_100"
}
EOF

CF_DISTRIBUTION_ID=$(aws cloudfront create-distribution \
    --distribution-config file:///tmp/cf-config.json \
    --query 'Distribution.Id' \
    --output text \
    --region "$REGION")

if [ $? -eq 0 ]; then
    log_success "CloudFront 배포 생성 완료: $CF_DISTRIBUTION_ID"
else
    log_error "CloudFront 배포 생성 실패"
    exit 1
fi

# CloudFront 도메인 가져오기
CF_DOMAIN=$(aws cloudfront get-distribution \
    --id "$CF_DISTRIBUTION_ID" \
    --query 'Distribution.DomainName' \
    --output text \
    --region "$REGION")

log_success "CloudFront 도메인: $CF_DOMAIN"

# 엔드포인트 저장
echo "CLOUDFRONT_DOMAIN=$CF_DOMAIN" >> "$PROJECT_ROOT/endpoints.txt"
echo "CLOUDFRONT_DISTRIBUTION_ID=$CF_DISTRIBUTION_ID" >> "$PROJECT_ROOT/endpoints.txt"

# 정리
rm -f /tmp/cf-config.json

log_info "CloudFront 배포가 활성화되기까지 15-20분 정도 소요됩니다."