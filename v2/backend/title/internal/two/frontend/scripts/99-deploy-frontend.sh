#!/bin/bash

# S3 버킷 이름 설정 (고유한 이름으로 변경 필요)
BUCKET_NAME="nexus-title-hub-frontend"
REGION="us-east-1"  # CloudFront는 us-east-1 권장
CLOUDFRONT_DISTRIBUTION_ID="EIYU5SFVTHQMN"  # CloudFront 생성 후 입력

echo "🚀 S3 및 CloudFront 배포 시작..."

# 1. S3 버킷 생성 (처음 한 번만)
echo "📦 S3 버킷 확인/생성 중..."
if ! aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
    echo "새 S3 버킷 생성 중..."
    aws s3api create-bucket \
        --bucket "$BUCKET_NAME" \
        --region "$REGION"
    
    # 버킷 정책 설정 (정적 웹사이트 호스팅)
    aws s3api put-bucket-policy \
        --bucket "$BUCKET_NAME" \
        --policy '{
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": "arn:aws:s3:::'$BUCKET_NAME'/*"
                }
            ]
        }'
    
    # 정적 웹사이트 호스팅 활성화
    aws s3 website s3://"$BUCKET_NAME"/ \
        --index-document index.html \
        --error-document index.html
    
    echo "✅ S3 버킷 생성 및 설정 완료"
else
    echo "✅ S3 버킷이 이미 존재합니다"
fi

# 2. 빌드 파일 S3에 업로드
echo "📤 빌드 파일 업로드 중..."
aws s3 sync ./dist s3://"$BUCKET_NAME"/ \
    --delete \
    --cache-control "public, max-age=31536000" \
    --exclude "index.html"

# index.html은 캐시 설정 없이 업로드 (항상 최신 버전 제공)
aws s3 cp ./dist/index.html s3://"$BUCKET_NAME"/index.html \
    --cache-control "no-cache, no-store, must-revalidate" \
    --content-type "text/html"

echo "✅ S3 업로드 완료"

# 3. CloudFront 캐시 무효화 (Distribution ID가 설정된 경우)
if [ -n "$CLOUDFRONT_DISTRIBUTION_ID" ]; then
    echo "🔄 CloudFront 캐시 무효화 중..."
    aws cloudfront create-invalidation \
        --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" \
        --paths "/*"
    echo "✅ CloudFront 캐시 무효화 완료"
fi

echo "🎉 배포 완료!"
echo "웹사이트 URL: http://$BUCKET_NAME.s3-website-$REGION.amazonaws.com"

# CloudFront가 설정되면 다음 URL 사용
# echo "CloudFront URL: https://your-distribution-id.cloudfront.net"