#!/bin/bash

# 프론트엔드 빌드 및 S3 배포 스크립트
# 사용법: ./03-deploy-frontend.sh

set -e

# deployment-config.json에서 설정 읽기
if [ ! -f "deployment-config.json" ]; then
    echo "❌ deployment-config.json 파일이 없습니다."
    echo "먼저 ./01-create-s3-bucket.sh와 ./02-create-cloudfront.sh를 실행하세요."
    exit 1
fi

# JSON 파싱
BUCKET_NAME=$(grep -o '"bucketName": *"[^"]*"' deployment-config.json | sed 's/.*: *"\(.*\)"/\1/')
DISTRIBUTION_ID=$(grep -o '"distributionId": *"[^"]*"' deployment-config.json | sed 's/.*: *"\(.*\)"/\1/')
CLOUDFRONT_URL=$(grep -o '"cloudfrontUrl": *"[^"]*"' deployment-config.json | sed 's/.*: *"\(.*\)"/\1/')
PROFILE=$(grep -o '"profile": *"[^"]*"' deployment-config.json | sed 's/.*: *"\(.*\)"/\1/')

echo "================================================"
echo "프론트엔드 빌드 및 배포 스크립트"
echo "================================================"
echo ""
echo "S3 버킷: $BUCKET_NAME"
echo "CloudFront ID: $DISTRIBUTION_ID"
echo "CloudFront URL: $CLOUDFRONT_URL"
echo "AWS 프로필: $PROFILE"
echo ""
echo "계속하시겠습니까? (y/n)"
read -r response

if [[ "$response" != "y" ]]; then
    echo "취소되었습니다."
    exit 0
fi

# 1. 프론트엔드 디렉토리로 이동
FRONTEND_DIR="../frontend"
if [ ! -d "$FRONTEND_DIR" ]; then
    echo "❌ 프론트엔드 디렉토리를 찾을 수 없습니다: $FRONTEND_DIR"
    exit 1
fi

cd "$FRONTEND_DIR"
echo ""
echo "1. 프론트엔드 디렉토리로 이동 완료"
echo "  현재 경로: $(pwd)"

# 2. 환경 변수 설정 파일 생성
echo ""
echo "2. 프로덕션 환경 변수 설정..."

# 백엔드 API 엔드포인트 확인
echo ""
echo "백엔드 API 엔드포인트를 입력하세요:"
echo "(예: wss://your-api-id.execute-api.ap-northeast-2.amazonaws.com/production)"
read -r BACKEND_ENDPOINT

cat > .env.production <<EOF
VITE_API_URL=${BACKEND_ENDPOINT}
VITE_WS_URL=${BACKEND_ENDPOINT}
VITE_ENV=production
EOF

echo "✓ 환경 변수 설정 완료"

# 3. 의존성 설치
echo ""
echo "3. 의존성 설치 중..."
if [ ! -d "node_modules" ]; then
    npm install
    echo "✓ 의존성 설치 완료"
else
    echo "✓ 의존성 이미 설치됨"
fi

# 4. 프로덕션 빌드
echo ""
echo "4. 프로덕션 빌드 시작..."
npm run build

if [ ! -d "dist" ]; then
    echo "❌ 빌드 실패: dist 디렉토리가 생성되지 않았습니다."
    exit 1
fi

echo "✓ 프로덕션 빌드 완료"
echo "  빌드 파일 크기:"
du -sh dist/

# 5. S3 버킷 기존 파일 삭제 (선택적)
echo ""
echo "S3 버킷의 기존 파일을 삭제하시겠습니까? (y/n)"
read -r delete_response

if [[ "$delete_response" == "y" ]]; then
    echo "5. S3 버킷 기존 파일 삭제 중..."
    aws s3 rm "s3://$BUCKET_NAME/" --recursive --profile "$PROFILE"
    echo "✓ 기존 파일 삭제 완료"
else
    echo "5. 기존 파일 유지"
fi

# 6. S3에 파일 업로드
echo ""
echo "6. S3에 파일 업로드 중..."

# HTML 파일 업로드 (캐시 없음)
aws s3 sync dist/ "s3://$BUCKET_NAME/" \
    --profile "$PROFILE" \
    --exclude "*" \
    --include "*.html" \
    --cache-control "no-cache, no-store, must-revalidate" \
    --content-type "text/html; charset=utf-8"

# JS, CSS 파일 업로드 (장기 캐시)
aws s3 sync dist/ "s3://$BUCKET_NAME/" \
    --profile "$PROFILE" \
    --exclude "*.html" \
    --include "*.js" \
    --include "*.css" \
    --cache-control "public, max-age=31536000, immutable"

# 이미지 파일 업로드
aws s3 sync dist/ "s3://$BUCKET_NAME/" \
    --profile "$PROFILE" \
    --exclude "*" \
    --include "*.jpg" \
    --include "*.jpeg" \
    --include "*.png" \
    --include "*.gif" \
    --include "*.svg" \
    --include "*.ico" \
    --cache-control "public, max-age=86400"

# 나머지 파일 업로드
aws s3 sync dist/ "s3://$BUCKET_NAME/" \
    --profile "$PROFILE" \
    --exclude "*.html" \
    --exclude "*.js" \
    --exclude "*.css" \
    --exclude "*.jpg" \
    --exclude "*.jpeg" \
    --exclude "*.png" \
    --exclude "*.gif" \
    --exclude "*.svg" \
    --exclude "*.ico"

echo "✓ S3 업로드 완료"

# 7. CloudFront 캐시 무효화
echo ""
echo "7. CloudFront 캐시 무효화 중..."

INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id "$DISTRIBUTION_ID" \
    --profile "$PROFILE" \
    --paths "/*" \
    --query 'Invalidation.Id' \
    --output text)

echo "✓ CloudFront 캐시 무효화 시작"
echo "  무효화 ID: $INVALIDATION_ID"

# 8. 배포 정보 표시
echo ""
echo "================================================"
echo "배포 완료!"
echo "================================================"
echo "CloudFront URL: $CLOUDFRONT_URL"
echo "S3 버킷: $BUCKET_NAME"
echo ""
echo "⚠️ 주의사항:"
echo "1. CloudFront 캐시 무효화는 5-10분 정도 소요됩니다."
echo "2. 처음 배포인 경우 CloudFront가 완전히 활성화되는데 15-20분 소요될 수 있습니다."
echo ""
echo "배포된 사이트 확인: $CLOUDFRONT_URL"
echo "================================================"

# deployment 디렉토리로 돌아가기
cd ../deployment