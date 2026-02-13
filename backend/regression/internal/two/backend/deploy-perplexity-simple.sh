#!/bin/bash

# Perplexity 통합 배포 스크립트 (간단 버전)
set -e

echo "🚀 Perplexity API 통합 배포 시작..."

# 환경 변수 설정
LAMBDA_NAME="sedaily-column-websocket-message"
PERPLEXITY_API_KEY=${1:-""}

if [ -z "$PERPLEXITY_API_KEY" ]; then
    echo "⚠️  사용법: ./deploy-perplexity-simple.sh YOUR_PERPLEXITY_API_KEY"
    exit 1
fi

# 1. 기존 환경 변수 가져오기
echo "📝 환경 변수 업데이트 중..."
aws lambda get-function-configuration \
    --function-name $LAMBDA_NAME \
    --query 'Environment.Variables' \
    --output json > /tmp/current_env.json

# 2. Python으로 환경 변수 업데이트
cat > /tmp/update_env.py << 'PYTHON_SCRIPT'
import json
import sys

with open('/tmp/current_env.json', 'r') as f:
    env = json.load(f)

env['PERPLEXITY_API_KEY'] = sys.argv[1]
env['ENABLE_WEB_SEARCH'] = 'true'

print(json.dumps(env))
PYTHON_SCRIPT

NEW_ENV=$(python3 /tmp/update_env.py "$PERPLEXITY_API_KEY")

aws lambda update-function-configuration \
    --function-name $LAMBDA_NAME \
    --environment "Variables=$NEW_ENV" \
    --region us-east-1 > /dev/null

echo "✅ 환경 변수 설정 완료"

# 3. 코드 패키징 및 업데이트
echo "📦 코드 업데이트 중..."
cd /tmp
rm -rf lambda-pkg
mkdir lambda-pkg
cd lambda-pkg

# 파일 복사
cp -r "/Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/칼럼/sedaily_ column/backend/handlers"/* .
cp -r "/Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/칼럼/sedaily_ column/backend/lib" .
cp -r "/Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/칼럼/sedaily_ column/backend/services" .
cp -r "/Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/칼럼/sedaily_ column/backend/utils" .

# ZIP 생성
zip -r ../perplexity-update.zip . -q

# Lambda 업데이트
aws lambda update-function-code \
    --function-name $LAMBDA_NAME \
    --zip-file fileb:///tmp/perplexity-update.zip \
    --region us-east-1 > /dev/null

echo "✅ 코드 업데이트 완료"

echo ""
echo "🎉 배포 완료!"
echo ""
echo "📌 테스트: https://r1.sedaily.ai"
echo "💬 웹 검색 질문 예시:"
echo "   - '오늘 서울 날씨는?'"
echo "   - '최근 AI 뉴스 알려줘'"
echo "   - '현재 비트코인 가격은?'"