#!/bin/bash

# 프론트엔드 배포 스크립트
# CloudFront: E1Y608786VRTT5
# S3 Bucket: nexus-frontend-20251204224751

set -e

echo "🚀 프론트엔드 배포 시작..."
echo "📅 배포 시각: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 설정
S3_BUCKET="sedaily-column-frontend-1764856283"
CLOUDFRONT_ID="E2Y96Q11K5DVPS"
REGION="ap-northeast-2"

# frontend 디렉토리 존재 확인
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [[ ! -d "$SCRIPT_DIR/frontend" ]]; then
    echo "❌ frontend 디렉토리를 찾을 수 없습니다."
    exit 1
fi
cd "$SCRIPT_DIR"

# frontend 디렉토리로 이동
cd frontend

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