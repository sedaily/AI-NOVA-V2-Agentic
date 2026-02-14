#!/bin/bash

# sedaily_column 프론트엔드 배포 스크립트
# CloudFront: EH9OF7IFDTPLW
# S3 Bucket: sedaily-column-frontend

set -e

echo "🚀 sedaily_column 프론트엔드 배포 시작..."
echo "📅 배포 시각: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 설정
S3_BUCKET="sedaily-column-frontend"
CLOUDFRONT_ID="EH9OF7IFDTPLW"
REGION="us-east-1"

# 스크립트 위치 기준으로 디렉토리 설정
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# frontend 디렉토리 존재 확인
if [[ ! -d "$FRONTEND_DIR" ]]; then
    echo "❌ frontend 디렉토리를 찾을 수 없습니다: $FRONTEND_DIR"
    exit 1
fi

# frontend 디렉토리로 이동
cd "$FRONTEND_DIR"

echo "📦 의존성 설치 중..."
npm install

echo "🔨 프론트엔드 빌드 중..."
npm run build

echo "📤 S3에 업로드 중..."
echo "   S3 버킷: s3://${S3_BUCKET}/"
aws s3 sync dist/ s3://${S3_BUCKET}/ --delete

echo "🔄 CloudFront 캐시 무효화 중..."
echo "   CloudFront 배포 ID: ${CLOUDFRONT_ID}"
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id ${CLOUDFRONT_ID} \
    --paths "/*" \
    --query 'Invalidation.Id' \
    --output text)

# CloudFront 도메인 가져오기
CLOUDFRONT_DOMAIN=$(aws cloudfront get-distribution \
    --id ${CLOUDFRONT_ID} \
    --query 'Distribution.DomainName' \
    --output text)

echo ""
echo "✅ 배포 완료!"
echo "🌐 접속 URL:"
echo "   - https://${CLOUDFRONT_DOMAIN}"
echo ""
echo "📋 배포 정보:"
echo "   배포 시각: $(date '+%Y-%m-%d %H:%M:%S')"
echo "   S3 버킷: s3://${S3_BUCKET}/"
echo "   CloudFront 배포 ID: ${CLOUDFRONT_ID}"
echo "   캐시 무효화 ID: ${INVALIDATION_ID}"
echo ""
echo "⏳ CloudFront 캐시 무효화가 완료되기까지 2-3분 소요됩니다."