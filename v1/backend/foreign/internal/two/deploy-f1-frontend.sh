#!/bin/bash

# ============================================
# Nexus Foreign - TWO Frontend Deployment
# ============================================
# Last Updated: 2025-12-24 (KST)
# Target: https://d22634fcti3bhs.cloudfront.net
# Backend: Shared f1-two stack (us-east-1)
# ============================================

set -e

# Configuration
STACK_NAME="nexus-foreign"
S3_BUCKET="nexus-frontend-20251204224751"
REGION="ap-northeast-2"
DISTRIBUTION_ID="E1Y608786VRTT5"
CLOUDFRONT_DOMAIN="d22634fcti3bhs.cloudfront.net"
CUSTOM_DOMAIN="d22634fcti3bhs.cloudfront.net"

echo "========================================="
echo "   Nexus Foreign - TWO Deployment"
echo "========================================="
echo ""
echo "스택: ${STACK_NAME}"
echo "S3 버킷: ${S3_BUCKET}"
echo "CloudFront ID: ${DISTRIBUTION_ID}"
echo "도메인: ${CUSTOM_DOMAIN}"
echo ""

# 프로젝트 루트로 이동
cd "$(dirname "$0")"
PROJECT_ROOT=$(pwd)

# 1. 프론트엔드 빌드
echo "🔨 프론트엔드 빌드 중..."
cd "${PROJECT_ROOT}/frontend"

# 의존성 설치 (필요한 경우)
if [ ! -d "node_modules" ]; then
    echo "📦 NPM 패키지 설치 중..."
    npm install
fi

# 빌드
echo "⚙️  빌드 실행 중..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ 프론트엔드 빌드 실패"
    exit 1
fi

echo "✅ 프론트엔드 빌드 완료"

# 2. S3에 업로드 (with correct MIME types)
echo ""
echo "📤 S3에 파일 업로드 중..."

# Upload with correct content types to prevent MIME type errors
aws s3 sync dist/ "s3://${S3_BUCKET}/" --delete --region ${REGION} \
    --exclude "*.js" --exclude "*.css" --exclude "*.html"

# Upload JS files with correct MIME type
aws s3 cp dist/ "s3://${S3_BUCKET}/" --recursive --region ${REGION} \
    --exclude "*" --include "*.js" --content-type "application/javascript"

# Upload CSS files with correct MIME type
aws s3 cp dist/ "s3://${S3_BUCKET}/" --recursive --region ${REGION} \
    --exclude "*" --include "*.css" --content-type "text/css"

# Upload HTML files with correct MIME type
aws s3 cp dist/ "s3://${S3_BUCKET}/" --recursive --region ${REGION} \
    --exclude "*" --include "*.html" --content-type "text/html"

if [ $? -ne 0 ]; then
    echo "❌ S3 업로드 실패"
    exit 1
fi

echo "✅ S3 업로드 완료 (MIME types applied)"

# 3. CloudFront 캐시 무효화
echo ""
echo "🔄 CloudFront 캐시 무효화 중..."
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id ${DISTRIBUTION_ID} \
    --paths "/*" \
    --query 'Invalidation.Id' \
    --output text)

if [ $? -ne 0 ]; then
    echo "❌ CloudFront 캐시 무효화 실패"
    exit 1
fi

echo "✅ CloudFront 캐시 무효화 요청 완료 (ID: ${INVALIDATION_ID})"

# 결과 출력
echo ""
echo "========================================="
echo "✅ 배포 완료!"
echo "========================================="
echo ""
echo "🌐 접속 URL:"
echo "   - https://${CUSTOM_DOMAIN}"
echo "   - https://${CLOUDFRONT_DOMAIN}"
echo ""
echo "⏳ CloudFront 캐시 무효화가 완료되기까지 약 1-2분 소요됩니다."
echo ""
echo "📋 배포 정보:"
echo "   배포 시각: $(date '+%Y-%m-%d %H:%M:%S')"
echo "   S3 버킷: s3://${S3_BUCKET}/"
echo "   CloudFront 배포 ID: ${DISTRIBUTION_ID}"
echo "   캐시 무효화 ID: ${INVALIDATION_ID}"
echo ""

cd "${PROJECT_ROOT}"
