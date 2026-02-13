#!/bin/bash

# S3 버킷 생성 및 설정

source "$(dirname "$0")/00-config.sh"

log_info "S3 버킷 생성 시작..."

# S3 버킷 생성
if aws s3 ls "s3://$S3_BUCKET" 2>/dev/null; then
    log_warning "S3 버킷이 이미 존재합니다: $S3_BUCKET"
else
    log_info "S3 버킷 생성 중: $S3_BUCKET"
    
    if [ "$REGION" == "us-east-1" ]; then
        aws s3 mb "s3://$S3_BUCKET" --region "$REGION"
    else
        aws s3 mb "s3://$S3_BUCKET" --region "$REGION" --create-bucket-configuration LocationConstraint="$REGION"
    fi
    
    if [ $? -eq 0 ]; then
        log_success "S3 버킷 생성 완료"
    else
        log_error "S3 버킷 생성 실패"
        exit 1
    fi
fi

# 정적 웹사이트 호스팅 설정
log_info "정적 웹사이트 호스팅 설정 중..."

cat > /tmp/website-config.json <<EOF
{
    "IndexDocument": {
        "Suffix": "index.html"
    },
    "ErrorDocument": {
        "Key": "index.html"
    }
}
EOF

aws s3api put-bucket-website \
    --bucket "$S3_BUCKET" \
    --website-configuration file:///tmp/website-config.json \
    --region "$REGION"

# 버킷 정책 설정 (CloudFront를 통해서만 접근 가능)
log_info "S3 버킷 정책 설정 중..."

cat > /tmp/bucket-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowCloudFrontAccess",
            "Effect": "Allow",
            "Principal": {
                "Service": "cloudfront.amazonaws.com"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$S3_BUCKET/*",
            "Condition": {
                "StringEquals": {
                    "AWS:SourceAccount": "$ACCOUNT_ID"
                }
            }
        }
    ]
}
EOF

aws s3api put-bucket-policy \
    --bucket "$S3_BUCKET" \
    --policy file:///tmp/bucket-policy.json \
    --region "$REGION"

# CORS 설정
log_info "S3 CORS 설정 중..."

cat > /tmp/cors-config.json <<EOF
{
    "CORSRules": [
        {
            "AllowedHeaders": ["*"],
            "AllowedMethods": ["GET", "HEAD"],
            "AllowedOrigins": ["*"],
            "ExposeHeaders": [],
            "MaxAgeSeconds": 3000
        }
    ]
}
EOF

aws s3api put-bucket-cors \
    --bucket "$S3_BUCKET" \
    --cors-configuration file:///tmp/cors-config.json \
    --region "$REGION"

# 공개 액세스 차단 해제 (필요한 경우)
log_info "S3 퍼블릭 액세스 블록 설정 해제 중..."

aws s3api put-public-access-block \
    --bucket "$S3_BUCKET" \
    --public-access-block-configuration \
        "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false" \
    --region "$REGION"

log_success "S3 버킷 설정 완료: $S3_BUCKET"

# 정리
rm -f /tmp/website-config.json /tmp/bucket-policy.json /tmp/cors-config.json