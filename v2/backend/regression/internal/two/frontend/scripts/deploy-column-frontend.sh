#!/bin/bash

# SEDAILY Column Service Frontend Deployment Script
# r1.sedaily.ai 도메인으로 배포

set -e

echo "🚀 SEDAILY Column Service Frontend 배포 시작..."
echo ""

# 환경 변수 설정
BUCKET_NAME="sedaily-column-frontend"
REGION="us-east-1"
CLOUDFRONT_DISTRIBUTION_ID=""  # CloudFront 생성 후 입력

# CloudFront 정보 파일이 있으면 로드
if [ -f "scripts/cloudfront-info.txt" ]; then
    source scripts/cloudfront-info.txt
fi

# 빌드 디렉토리 확인
if [ ! -d "dist" ]; then
    echo "❌ dist 디렉토리가 없습니다."
    echo "먼저 npm run build를 실행하세요."
    exit 1
fi

# S3 버킷 확인 또는 생성
echo "📦 S3 버킷 확인 중..."
if aws s3 ls "s3://$BUCKET_NAME" 2>&1 | grep -q 'NoSuchBucket'; then
    echo "S3 버킷 생성 중..."
    aws s3api create-bucket \
        --bucket $BUCKET_NAME \
        --region $REGION

    # 정적 웹사이트 호스팅 설정
    aws s3 website s3://$BUCKET_NAME/ \
        --index-document index.html \
        --error-document error.html

    echo "✅ S3 버킷 생성 완료"
else
    echo "✅ S3 버킷이 이미 존재합니다"
fi

# 기존 파일 삭제 (선택적)
read -p "기존 파일을 삭제하시겠습니까? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️ 기존 파일 삭제 중..."
    aws s3 rm s3://$BUCKET_NAME --recursive
fi

# 파일 업로드
echo "📤 파일 업로드 중..."

# HTML 파일 (캐시 없음)
aws s3 cp dist s3://$BUCKET_NAME/ \
    --recursive \
    --exclude "*" \
    --include "*.html" \
    --cache-control "no-cache, no-store, must-revalidate" \
    --content-type "text/html; charset=utf-8"

# JS 파일 (장기 캐시)
aws s3 cp dist s3://$BUCKET_NAME/ \
    --recursive \
    --exclude "*" \
    --include "*.js" \
    --cache-control "public, max-age=31536000" \
    --content-type "application/javascript"

# CSS 파일 (장기 캐시)
aws s3 cp dist s3://$BUCKET_NAME/ \
    --recursive \
    --exclude "*" \
    --include "*.css" \
    --cache-control "public, max-age=31536000" \
    --content-type "text/css"

# 이미지 파일
aws s3 cp dist s3://$BUCKET_NAME/ \
    --recursive \
    --exclude "*" \
    --include "*.png" \
    --include "*.jpg" \
    --include "*.jpeg" \
    --include "*.gif" \
    --include "*.svg" \
    --include "*.ico" \
    --cache-control "public, max-age=86400"

# 기타 파일
aws s3 cp dist s3://$BUCKET_NAME/ \
    --recursive \
    --exclude "*.html" \
    --exclude "*.js" \
    --exclude "*.css" \
    --exclude "*.png" \
    --exclude "*.jpg" \
    --exclude "*.jpeg" \
    --exclude "*.gif" \
    --exclude "*.svg" \
    --exclude "*.ico"

echo "✅ S3 업로드 완료!"

# CloudFront 캐시 무효화
if [ -n "$CLOUDFRONT_DISTRIBUTION_ID" ]; then
    echo "🔄 CloudFront 캐시 무효화 중..."

    INVALIDATION_ID=$(aws cloudfront create-invalidation \
        --distribution-id $CLOUDFRONT_DISTRIBUTION_ID \
        --paths "/*" \
        --query 'Invalidation.Id' \
        --output text)

    echo "✅ CloudFront 캐시 무효화 요청 완료"
    echo "   Invalidation ID: $INVALIDATION_ID"
    echo ""
    echo "⏳ 캐시 무효화는 몇 분 정도 걸립니다."
else
    echo "⚠️ CloudFront Distribution ID가 설정되지 않았습니다."
    echo "   CloudFront 캐시를 수동으로 무효화해야 합니다."
fi

echo ""
echo "🎉 배포 완료!"
echo ""
echo "📌 접속 URL:"

if [ -n "$CLOUDFRONT_DISTRIBUTION_ID" ]; then
    CF_DOMAIN=$(aws cloudfront get-distribution \
        --id $CLOUDFRONT_DISTRIBUTION_ID \
        --query 'Distribution.DomainName' \
        --output text 2>/dev/null)

    if [ -n "$CF_DOMAIN" ]; then
        echo "   CloudFront: https://$CF_DOMAIN"
    fi
fi

echo "   Custom Domain: https://r1.sedaily.ai"
echo "   S3 Website: http://$BUCKET_NAME.s3-website-$REGION.amazonaws.com"
echo ""
echo "⚠️ 주의사항:"
echo "1. Route 53에서 r1.sedaily.ai A 레코드가 CloudFront로 설정되어 있어야 합니다."
echo "2. SSL 인증서가 CloudFront에 연결되어 있어야 HTTPS가 작동합니다."
echo "3. 첫 배포 후 DNS 전파까지 시간이 걸릴 수 있습니다."