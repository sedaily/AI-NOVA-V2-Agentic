#!/bin/bash

# ============================================
# t1.sedaily.ai 프론트엔드 배포 스크립트
# ============================================

set -e

PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONFIG_FILE="$PROJECT_ROOT/config/t1-production.env"

# Load configuration
source "$CONFIG_FILE"

echo "📦 프론트엔드 배포 시작..."
echo "대상: ${CUSTOM_DOMAIN}"

cd "$PROJECT_ROOT/frontend"

# Install dependencies if package.json changed
if [ package.json -nt node_modules ]; then
    echo "📥 의존성 설치..."
    npm install
fi

# Build
echo "🔨 빌드 중..."
npm run build

# Deploy to S3
echo "☁️ S3 업로드..."
aws s3 sync build/ "s3://${S3_BUCKET}" \
    --delete \
    --cache-control "public, max-age=31536000" \
    --exclude "index.html" \
    --exclude "*.json"

# Upload index.html with no-cache
aws s3 cp build/index.html "s3://${S3_BUCKET}/index.html" \
    --cache-control "no-cache, no-store, must-revalidate"

# Upload manifest with appropriate cache
[ -f build/manifest.json ] && aws s3 cp build/manifest.json "s3://${S3_BUCKET}/manifest.json" \
    --cache-control "public, max-age=3600"

# Invalidate CloudFront
echo "🔄 CloudFront 캐시 무효화..."
aws cloudfront create-invalidation \
    --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" \
    --paths "/*" \
    --query 'Invalidation.Id' \
    --output text

echo "✅ 프론트엔드 배포 완료!"
echo "🌐 URL: ${CUSTOM_DOMAIN}"