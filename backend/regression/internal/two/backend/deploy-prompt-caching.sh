#!/bin/bash

# 프롬프트 캐싱 배포 스크립트
set -e

echo "🚀 프롬프트 캐싱 Lambda 배포 시작..."

LAMBDA_NAME="sedaily-column-websocket-message"
BACKEND_DIR="/Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/칼럼/sedaily_ column/backend"

# 1. 코드 패키징
echo "📦 코드 패키징 중..."
cd /tmp
rm -rf lambda-pkg
mkdir lambda-pkg
cd lambda-pkg

# 파일 복사
cp -r "$BACKEND_DIR/handlers" .
cp -r "$BACKEND_DIR/lib" .
cp -r "$BACKEND_DIR/services" .
cp -r "$BACKEND_DIR/src" .
cp -r "$BACKEND_DIR/utils" .

# __pycache__ 정리
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# ZIP 생성
zip -r ../prompt-caching.zip . -q

echo "✅ 패키징 완료"

# 2. Lambda 업데이트
echo "🔄 Lambda 함수 업데이트 중..."
aws lambda update-function-code \
    --function-name $LAMBDA_NAME \
    --zip-file fileb:///tmp/prompt-caching.zip \
    --region us-east-1 > /dev/null

echo "✅ 배포 완료!"
echo ""
echo "📊 캐시 확인 명령:"
echo "aws logs tail /aws/lambda/$LAMBDA_NAME --since 5m --region us-east-1 | grep 'Cache metrics'"
echo ""
echo "💡 두 번째 요청에서 'read: XXXX' (0이 아닌 값)가 나오면 성공!"

