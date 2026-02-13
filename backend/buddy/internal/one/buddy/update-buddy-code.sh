#!/bin/bash

# Buddy 서비스 Lambda 코드 업데이트 스크립트
# 수정된 대화 관리 코드 배포용

set -e

echo "🚀 Buddy 서비스 코드 업데이트 시작..."

# 서비스 설정
SERVICE_NAME="p2-two"
REGION="us-east-1"

# Lambda 함수 목록
LAMBDA_FUNCTIONS=(
    "${SERVICE_NAME}-websocket-message-two"
    "${SERVICE_NAME}-websocket-connect-two"
    "${SERVICE_NAME}-websocket-disconnect-two"
    "${SERVICE_NAME}-conversation-api-two"
    "${SERVICE_NAME}-prompt-crud-two"
    "${SERVICE_NAME}-usage-handler-two"
)

echo "📦 배포 패키지 준비 중..."

# Backend 디렉토리로 이동
cd backend

# 기존 패키지 정리
rm -rf package deployment.zip 2>/dev/null || true

# 패키지 디렉토리 생성
mkdir -p package

# 의존성 설치
echo "📥 Python 의존성 설치..."
pip install -r requirements.txt -t ./package --quiet --upgrade

# 소스 코드 복사
echo "📁 소스 코드 복사..."
cd package

# 핵심 모듈들 복사
cp -r ../handlers .
cp -r ../services .
cp -r ../src .
cp -r ../lib .
cp -r ../utils .

# 캐시 파일 정리
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# ZIP 패키지 생성
echo "📦 배포 패키지 생성..."
zip -r ../deployment.zip . -q

cd ..

echo "✅ 배포 패키지 생성 완료"

# 환경변수 설정 (AWS CLI shorthand 형식)
ENVIRONMENT_VARS='Variables={ANTHROPIC_SECRET_NAME=buddy-v1,USE_ANTHROPIC_API=true,USE_OPUS_MODEL=true,ANTHROPIC_MODEL_ID=claude-opus-4-5-20251101,SERVICE_NAME=buddy,AI_PROVIDER=anthropic_api,MAX_TOKENS=4096,TEMPERATURE=0.3,FALLBACK_TO_BEDROCK=true,ENABLE_NATIVE_WEB_SEARCH=true}'

# Lambda 함수별 업데이트
echo ""
echo "🔄 Lambda 함수 업데이트 시작..."

UPDATE_COUNT=0
TOTAL_COUNT=${#LAMBDA_FUNCTIONS[@]}

for FUNCTION_NAME in "${LAMBDA_FUNCTIONS[@]}"; do
    echo ""
    echo "📤 ${FUNCTION_NAME} 업데이트 중..."

    # 함수 존재 여부 확인
    if aws lambda get-function --function-name "${FUNCTION_NAME}" --region ${REGION} &>/dev/null; then
        # 코드 업데이트
        aws lambda update-function-code \
            --function-name "${FUNCTION_NAME}" \
            --zip-file fileb://deployment.zip \
            --region ${REGION} \
            --output text \
            --query 'LastModified' 2>/dev/null

        if [ $? -eq 0 ]; then
            echo "   ✅ 코드 업데이트 완료"

            UPDATE_COUNT=$((UPDATE_COUNT + 1))
        else
            echo "   ❌ 코드 업데이트 실패"
        fi

        # 잠시 대기 (AWS 제한 방지)
        sleep 1
    else
        echo "   ⚠️  ${FUNCTION_NAME} 함수를 찾을 수 없음"
    fi
done

# 정리 (package만 삭제, deployment.zip은 유지)
rm -rf package

echo ""
echo "========================================="
echo "🎉 업데이트 완료!"
echo "========================================="
echo ""
echo "결과: ${UPDATE_COUNT}/${TOTAL_COUNT} 함수 업데이트됨"
echo ""

if [ ${UPDATE_COUNT} -eq ${TOTAL_COUNT} ]; then
    echo "✅ 모든 Lambda 함수가 성공적으로 업데이트되었습니다!"
    echo ""
    echo "🔧 업데이트된 기능:"
    echo "   • Claude Opus 4.5 모델 사용"
    echo "   • Native 웹 검색 기능 활성화"
    echo "   • AI 응답 중복 저장 문제 해결"
    echo "   • WebSocket 매개변수 순서 정정"
    echo "   • conversationId 생성 로직 개선"
    echo ""
    echo "📋 테스트 권장 사항:"
    echo "   1. 새 대화 시작 테스트"
    echo "   2. 동일한 대화에서 연속 메시지 테스트"
    echo "   3. 대화 중복 저장 여부 확인"
else
    echo "⚠️  일부 함수 업데이트 실패. 로그를 확인하세요."
fi

echo ""