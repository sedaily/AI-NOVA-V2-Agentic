#!/bin/bash

# ============================================
# t1.sedaily.ai 백엔드 배포 스크립트
# ============================================

set -e

PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONFIG_FILE="$PROJECT_ROOT/config/t1-production.env"

# Load configuration
source "$CONFIG_FILE"

echo "📦 백엔드 배포 시작..."

cd "$PROJECT_ROOT/backend"

# Clean and package
echo "🧹 기존 패키지 정리..."
rm -rf package lambda-deployment.zip

echo "📥 의존성 설치..."
mkdir -p package
pip install -r requirements.txt -t package/ --quiet

echo "📄 코드 복사..."
cp -r handlers lib *.py package/ 2>/dev/null || true

echo "🗜️ ZIP 생성..."
cd package
zip -r ../lambda-deployment.zip . -q
cd ..

PACKAGE_SIZE=$(ls -lh lambda-deployment.zip | awk '{print $5}')
echo "📦 패키지 크기: $PACKAGE_SIZE"

# Deploy Lambda functions
LAMBDA_FUNCTIONS=(
    "$LAMBDA_WS_MESSAGE"
    "$LAMBDA_CONVERSATION"
    "$LAMBDA_PROMPT"
    "$LAMBDA_USAGE"
)

for func in "${LAMBDA_FUNCTIONS[@]}"; do
    echo "🚀 배포: $func"
    aws lambda update-function-code \
        --function-name "$func" \
        --zip-file fileb://lambda-deployment.zip \
        --region "$AWS_REGION" \
        --output text > /dev/null 2>&1 || echo "⚠️  $func 건너뜀"
done

echo "✅ 백엔드 배포 완료!"