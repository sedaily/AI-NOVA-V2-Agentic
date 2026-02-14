#!/bin/bash

# Perplexity 통합 배포 스크립트
set -e

echo "🚀 Perplexity API 통합 배포 시작..."

# 환경 변수 설정
LAMBDA_NAME="sedaily-column-websocket-message"
PERPLEXITY_API_KEY=${1:-""}

if [ -z "$PERPLEXITY_API_KEY" ]; then
    echo "⚠️  사용법: ./deploy-perplexity.sh YOUR_PERPLEXITY_API_KEY"
    echo "   Perplexity API 키를 https://www.perplexity.ai/settings/api 에서 발급받으세요"
    exit 1
fi

# 1. Lambda 함수 환경 변수 업데이트
echo "📝 Lambda 환경 변수 설정 중..."

# 기존 환경 변수 가져오기
EXISTING_ENV=$(aws lambda get-function-configuration --function-name $LAMBDA_NAME --query 'Environment.Variables' --output json)

# Python을 사용하여 환경 변수 병합
python3 << EOF
import json
import sys

existing = $EXISTING_ENV
existing['PERPLEXITY_API_KEY'] = '$PERPLEXITY_API_KEY'
existing['ENABLE_WEB_SEARCH'] = 'true'

# JSON 형식으로 출력
print(json.dumps(existing))
EOF > /tmp/env_vars.json

# 환경 변수 업데이트
aws lambda update-function-configuration \
    --function-name $LAMBDA_NAME \
    --environment "Variables=$(cat /tmp/env_vars.json)" \
    --region us-east-1 \
    --output text > /dev/null

echo "✅ 환경 변수 설정 완료"

# 2. 코드 패키징
echo "📦 코드 패키징 중..."
cd /tmp
rm -rf lambda-package
mkdir lambda-package
cd lambda-package

# 파일 복사
cp -r /Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/칼럼/sedaily_\ column/backend/handlers/* .
cp -r /Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/칼럼/sedaily_\ column/backend/lib .
cp -r /Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/칼럼/sedaily_\ column/backend/services .
cp -r /Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/칼럼/sedaily_\ column/backend/utils .

# ZIP 생성
zip -r ../websocket-message-perplexity.zip . -q

echo "✅ 패키징 완료"

# 3. Lambda 함수 업데이트
echo "🔄 Lambda 함수 코드 업데이트 중..."
aws lambda update-function-code \
    --function-name $LAMBDA_NAME \
    --zip-file fileb:///tmp/websocket-message-perplexity.zip \
    --region us-east-1 \
    --output text > /dev/null

echo "✅ Lambda 함수 업데이트 완료"

# 4. 테스트
echo ""
echo "🎉 배포 완료!"
echo ""
echo "📌 다음 단계:"
echo "1. r1.sedaily.ai 에서 테스트"
echo "2. 웹 검색이 필요한 질문 예시:"
echo "   - '오늘 서울 날씨 어때?'"
echo "   - '최신 AI 뉴스 알려줘'"
echo "   - '현재 코스피 지수는?'"
echo ""
echo "💡 웹 검색 비활성화: ENABLE_WEB_SEARCH=false 로 설정"