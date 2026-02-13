#!/bin/bash

# f1.sedaily.ai 백엔드 배포 스크립트 (Lambda 함수만)
# 업데이트: 2025-11-21
set -e

# 설정 - f1-two 스택
STACK_NAME="f1-two"
SERVICE_NAME="f1"
CARD_COUNT="two"
REGION="us-east-1"

# Lambda 함수 목록
LAMBDA_FUNCTIONS=(
  "f1-conversation-api-two"
  "f1-prompt-crud-two"
  "f1-usage-handler-two"
  "f1-websocket-connect-two"
  "f1-websocket-disconnect-two"
  "f1-websocket-message-two"
)

echo "========================================="
echo "   f1.sedaily.ai 백엔드 배포"
echo "   Lambda 함수 코드 업데이트"
echo "========================================="
echo ""
echo "스택: ${STACK_NAME}"
echo "Lambda 함수 개수: ${#LAMBDA_FUNCTIONS[@]}"
echo ""

# 프로젝트 루트로 이동
cd "$(dirname "$0")"
PROJECT_ROOT=$(pwd)

# 1. Backend 디렉토리로 이동
echo "📂 Backend 디렉토리로 이동..."
cd "${PROJECT_ROOT}/backend"

if [ ! -d "extracted" ]; then
    echo "❌ backend/extracted 디렉토리가 없습니다."
    echo "   lambda-deployment.zip을 압축 해제하세요."
    exit 1
fi

# 2. 배포 패키지 생성
echo ""
echo "📦 배포 패키지 생성 중..."
cd extracted

# 기존 ZIP 파일 삭제
rm -f ../lambda-deployment-new.zip

# 새 ZIP 파일 생성
zip -r ../lambda-deployment-new.zip . -q

if [ $? -ne 0 ]; then
    echo "❌ ZIP 파일 생성 실패"
    exit 1
fi

cd ..
echo "✅ 배포 패키지 생성 완료 (lambda-deployment-new.zip)"

# 3. Lambda 함수 업데이트
echo ""
echo "🚀 Lambda 함수 업데이트 중..."
UPDATED_COUNT=0
FAILED_COUNT=0

for FUNCTION_NAME in "${LAMBDA_FUNCTIONS[@]}"; do
    echo "   ├─ ${FUNCTION_NAME} 업데이트 중..."

    if aws lambda update-function-code \
        --function-name "${FUNCTION_NAME}" \
        --zip-file fileb://lambda-deployment-new.zip \
        --region "${REGION}" \
        --output text > /dev/null 2>&1; then
        echo "   ✅ ${FUNCTION_NAME} 업데이트 완료"
        ((UPDATED_COUNT++))
    else
        echo "   ❌ ${FUNCTION_NAME} 업데이트 실패"
        ((FAILED_COUNT++))
    fi
done

# 4. 결과 출력
echo ""
echo "========================================="
if [ $FAILED_COUNT -eq 0 ]; then
    echo "✅ 배포 완료!"
else
    echo "⚠️  배포 완료 (일부 실패)"
fi
echo "========================================="
echo ""
echo "📊 배포 결과:"
echo "   성공: ${UPDATED_COUNT}/${#LAMBDA_FUNCTIONS[@]}"
echo "   실패: ${FAILED_COUNT}/${#LAMBDA_FUNCTIONS[@]}"
echo ""
echo "📋 배포 정보:"
echo "   배포 시각: $(date '+%Y-%m-%d %H:%M:%S')"
echo "   스택: ${STACK_NAME}"
echo "   ZIP 파일: lambda-deployment-new.zip ($(du -h lambda-deployment-new.zip | cut -f1))"
echo ""

# 5. 정리
echo "🧹 임시 파일 정리..."
mv lambda-deployment-new.zip lambda-deployment.zip
echo "✅ 정리 완료"
echo ""

cd "${PROJECT_ROOT}"

if [ $FAILED_COUNT -eq 0 ]; then
    exit 0
else
    exit 1
fi
