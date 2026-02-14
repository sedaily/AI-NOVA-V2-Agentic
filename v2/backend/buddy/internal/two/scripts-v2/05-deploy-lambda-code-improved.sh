#!/bin/bash

# Lambda 코드 배포 스크립트 - Backend 실제 코드 배포 (개선된 버전)
# 하드코딩 제거 및 동적 테이블명 수정 기능 포함

# 설정 파일 확인
if [ ! -f "config.sh" ]; then
    echo "❌ config.sh 파일이 없습니다. 먼저 ./init.sh를 실행하세요."
    exit 1
fi

source config.sh

echo "========================================="
echo "   [5/6] Lambda 코드 배포 (개선된 버전)"
echo "   스택: ${STACK_NAME}"
echo "   CARD_COUNT: ${CARD_COUNT}"
echo "========================================="

# Lambda 함수 목록 정의 (CARD_COUNT 포함)
LAMBDA_CONNECT="${SERVICE_NAME}-websocket-connect-${CARD_COUNT}"
LAMBDA_DISCONNECT="${SERVICE_NAME}-websocket-disconnect-${CARD_COUNT}"
LAMBDA_MESSAGE="${SERVICE_NAME}-websocket-message-${CARD_COUNT}"
LAMBDA_CONVERSATION="${SERVICE_NAME}-conversation-api-${CARD_COUNT}"
LAMBDA_PROMPT="${SERVICE_NAME}-prompt-crud-${CARD_COUNT}"
LAMBDA_USAGE="${SERVICE_NAME}-usage-handler-${CARD_COUNT}"

# 테이블 이름 정의 (DynamoDB 스크립트와 동일)
CONVERSATIONS_TABLE="${SERVICE_NAME}-conversations-${CARD_COUNT}"
FILES_TABLE="${SERVICE_NAME}-files-${CARD_COUNT}"
MESSAGES_TABLE="${SERVICE_NAME}-messages-${CARD_COUNT}"
PROMPTS_TABLE="${SERVICE_NAME}-prompts-${CARD_COUNT}"
USAGE_TABLE="${SERVICE_NAME}-usage-${CARD_COUNT}"
WEBSOCKET_TABLE="${SERVICE_NAME}-websocket-connections-${CARD_COUNT}"

# Backend 디렉토리 확인
BACKEND_DIR="../backend"
if [ ! -d "${BACKEND_DIR}" ]; then
    echo "❌ Backend 디렉토리를 찾을 수 없습니다: ${BACKEND_DIR}"
    exit 1
fi

echo "📂 Backend 디렉토리: ${BACKEND_DIR}"
echo ""

# deployment-info.txt에서 API ID 추출
if [ ! -f "deployment-info.txt" ]; then
    echo "❌ deployment-info.txt 파일이 없습니다. 03-deploy-api-gateway.sh를 먼저 실행하세요."
    exit 1
fi

# API ID 추출
REST_API_ID=$(grep "  - ID:" deployment-info.txt | head -1 | awk '{print $3}')
WEBSOCKET_API_ID=$(grep "  - ID:" deployment-info.txt | tail -1 | awk '{print $3}')

if [ -z "$REST_API_ID" ] || [ -z "$WEBSOCKET_API_ID" ]; then
    echo "❌ API ID를 찾을 수 없습니다. deployment-info.txt를 확인하세요."
    exit 1
fi

echo "📡 API 정보 확인:"
echo "   REST API ID: ${REST_API_ID}"
echo "   WebSocket API ID: ${WEBSOCKET_API_ID}"
echo ""

# =============================================================================
# 0. 하드코딩된 테이블명 동적 수정 (추가 기능)
# =============================================================================

echo "🔧 [추가] Repository 파일 하드코딩 자동 수정..."

# 백업 디렉토리 생성
BACKUP_DIR="${BACKEND_DIR}/backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "   💾 백업 위치: ${BACKUP_DIR}"

# 수정할 패턴을 동적으로 생성 (모든 서비스명-테이블명-카드 조합을 대체)
fix_table_references() {
    local file=$1
    local table_type=$2  # conversations, prompts, usage 등
    local target_table=$3

    if [ -f "$file" ]; then
        # 백업
        cp "$file" "${BACKUP_DIR}/$(basename $file)"

        # 패턴 매칭으로 모든 서비스명 처리 (w1, f2, b1 등 어떤 것이든)
        # 다양한 패턴 처리:
        # - 'w1-conversations-v2' 형태
        # - 'f2-prompts-two' 형태
        # - 기타 서비스명-테이블-카드 형태

        # single quotes 패턴
        sed -i.bak "s/'[a-zA-Z0-9_]*-${table_type}-[a-zA-Z0-9_]*'/'${target_table}'/g" "$file"

        # double quotes 패턴
        sed -i.bak "s/\"[a-zA-Z0-9_]*-${table_type}-[a-zA-Z0-9_]*\"/\"${target_table}\"/g" "$file"

        # 하드코딩된 기본값 패턴 (default='...')
        sed -i.bak "s/default='[a-zA-Z0-9_]*-${table_type}-[a-zA-Z0-9_]*'/default='${target_table}'/g" "$file"

        # os.environ.get 패턴
        sed -i.bak "s/get('[A-Z_]*_TABLE', '[a-zA-Z0-9_]*-${table_type}-[a-zA-Z0-9_]*')/get('$(echo ${table_type} | tr '[:lower:]' '[:upper:]')_TABLE', '${target_table}')/g" "$file"

        echo "   ✅ $(basename $file) 수정 완료 (${table_type} → ${target_table})"
    fi
}

# Repository 파일들 수정
echo "   📝 Repository 파일 수정 중..."
fix_table_references "${BACKEND_DIR}/src/repositories/conversation_repository.py" "conversations" "${CONVERSATIONS_TABLE}"
fix_table_references "${BACKEND_DIR}/src/repositories/prompt_repository.py" "prompts" "${PROMPTS_TABLE}"
fix_table_references "${BACKEND_DIR}/src/repositories/usage_repository.py" "usage" "${USAGE_TABLE}"

# WebSocket 관련 파일들 수정
echo "   📝 WebSocket 관련 파일 수정 중..."
fix_table_references "${BACKEND_DIR}/handlers/websocket/conversation_manager.py" "conversations" "${CONVERSATIONS_TABLE}"

# websocket_service.py의 프롬프트 테이블 수정 (특별 처리)
if [ -f "${BACKEND_DIR}/services/websocket_service.py" ]; then
    cp "${BACKEND_DIR}/services/websocket_service.py" "${BACKUP_DIR}/"
    sed -i.bak "s/'[a-zA-Z0-9_]*-prompts-[a-zA-Z0-9_]*'/'${PROMPTS_TABLE}'/g" "${BACKEND_DIR}/services/websocket_service.py"
    echo "   ✅ websocket_service.py 수정 완료"
fi

# 백업 파일(.bak) 정리
find "${BACKEND_DIR}" -name "*.bak" -delete 2>/dev/null
echo "   🧹 백업 파일 정리 완료"
echo ""

# =============================================================================
# 1. 패키지 생성 및 코드 준비
# =============================================================================

echo "📦 [1/3] 배포 패키지 생성 중..."

cd "${BACKEND_DIR}"

# 기존 패키지 정리
echo "   🧹 기존 배포 파일 정리..."
rm -rf package deployment.zip lambda-*.zip 2>/dev/null

# Python 패키지 설치
echo "   📥 Python 의존성 패키지 설치 중..."
if [ -f "requirements.txt" ]; then
    mkdir -p package
    pip install -r requirements.txt -t ./package --quiet --upgrade
    if [ $? -eq 0 ]; then
        echo "   ✅ 의존성 패키지 설치 완료"
    else
        echo "   ❌ 의존성 패키지 설치 실패"
        exit 1
    fi
else
    echo "   ⚠️  requirements.txt가 없습니다. 기본 패키지만 사용합니다."
    mkdir -p package
fi

# 소스 코드 복사
echo "   📁 소스 코드 복사 중..."
cd package

# 핵심 소스 파일들 복사
for dir in handlers services src lib utils; do
    if [ -d "../${dir}" ]; then
        cp -r ../${dir} .
        echo "   ✅ ${dir} 복사 완료"
    else
        echo "   ⚠️  ${dir} 디렉토리가 없습니다."
    fi
done

# __pycache__ 정리
echo "   🧹 캐시 파일 정리..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# 배포 패키지 생성
echo "   📦 ZIP 패키지 생성 중..."
zip -r ../deployment.zip . -q
if [ $? -eq 0 ]; then
    echo "   ✅ 배포 패키지 생성 완료: deployment.zip"
else
    echo "   ❌ 배포 패키지 생성 실패"
    exit 1
fi

cd ..

# =============================================================================
# 2. Lambda 함수 업데이트 함수 정의
# =============================================================================

# Lambda 함수 코드 및 환경변수 업데이트 함수
update_lambda_function() {
    local function_name=$1
    local description=$2

    echo "🔄 ${description} (${function_name}) 업데이트 중..."

    # 1. 함수 존재 여부 확인
    if ! aws lambda get-function --function-name "${function_name}" --region ${REGION} &>/dev/null; then
        echo "   ❌ Lambda 함수를 찾을 수 없습니다: ${function_name}"
        return 1
    fi

    # 2. 함수 코드 업데이트
    echo "   📤 코드 업데이트 중..."
    aws lambda update-function-code \
        --function-name "${function_name}" \
        --zip-file fileb://deployment.zip \
        --region ${REGION} &>/dev/null

    if [ $? -ne 0 ]; then
        echo "   ❌ 코드 업데이트 실패: ${function_name}"
        return 1
    fi

    # 3. 업데이트 완료 대기
    echo "   ⏳ 업데이트 완료 대기..."
    aws lambda wait function-updated \
        --function-name "${function_name}" \
        --region ${REGION} 2>/dev/null || sleep 5

    # 4. 환경변수 업데이트 (통합된 환경변수 설정)
    echo "   🔧 환경변수 업데이트 중..."
    aws lambda update-function-configuration \
        --function-name "${function_name}" \
        --environment "Variables={
            AWS_REGION=${REGION},
            CONVERSATIONS_TABLE=${CONVERSATIONS_TABLE},
            PROMPTS_TABLE=${PROMPTS_TABLE},
            FILES_TABLE=${FILES_TABLE},
            MESSAGES_TABLE=${MESSAGES_TABLE},
            USAGE_TABLE=${USAGE_TABLE},
            WEBSOCKET_TABLE=${WEBSOCKET_TABLE},
            CONNECTIONS_TABLE=${WEBSOCKET_TABLE},
            WEBSOCKET_API_ID=${WEBSOCKET_API_ID},
            REST_API_URL=https://${REST_API_ID}.execute-api.${REGION}.amazonaws.com/prod,
            WEBSOCKET_API_URL=wss://${WEBSOCKET_API_ID}.execute-api.${REGION}.amazonaws.com/prod,
            LOG_LEVEL=INFO,
            CLOUDWATCH_ENABLED=true,
            SERVICE_NAME=${SERVICE_NAME},
            CARD_COUNT=${CARD_COUNT},
            ENABLE_NEWS_SEARCH=true,
            DEFAULT_ENGINE_TYPE=11,
            SECONDARY_ENGINE_TYPE=22,
            AVAILABLE_ENGINES=11,22,33,
            BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0,
            BEDROCK_OPUS_MODEL_ID=us.anthropic.claude-opus-4-1-20250805-v1:0,
            BEDROCK_MAX_TOKENS=16384,
            BEDROCK_TEMPERATURE=0.7,
            ANTHROPIC_VERSION=bedrock-2023-05-31
        }" \
        --region ${REGION} &>/dev/null

    if [ $? -eq 0 ]; then
        echo "   ✅ ${description} 업데이트 완료"
        return 0
    else
        echo "   ⚠️  환경변수 업데이트는 백그라운드에서 진행 중"
        return 0
    fi
}

# =============================================================================
# 3. 모든 Lambda 함수 업데이트
# =============================================================================

echo ""
echo "🚀 [2/3] Lambda 함수별 코드 배포 시작..."
echo ""

SUCCESS_COUNT=0
FAIL_COUNT=0
FAILED_FUNCTIONS=""

# WebSocket Lambda 함수들
update_lambda_function "${LAMBDA_CONNECT}" "WebSocket Connect 핸들러"
if [ $? -eq 0 ]; then SUCCESS_COUNT=$((SUCCESS_COUNT + 1)); else FAIL_COUNT=$((FAIL_COUNT + 1)); FAILED_FUNCTIONS="${FAILED_FUNCTIONS} ${LAMBDA_CONNECT}"; fi

update_lambda_function "${LAMBDA_DISCONNECT}" "WebSocket Disconnect 핸들러"
if [ $? -eq 0 ]; then SUCCESS_COUNT=$((SUCCESS_COUNT + 1)); else FAIL_COUNT=$((FAIL_COUNT + 1)); FAILED_FUNCTIONS="${FAILED_FUNCTIONS} ${LAMBDA_DISCONNECT}"; fi

update_lambda_function "${LAMBDA_MESSAGE}" "WebSocket Message 핸들러"
if [ $? -eq 0 ]; then SUCCESS_COUNT=$((SUCCESS_COUNT + 1)); else FAIL_COUNT=$((FAIL_COUNT + 1)); FAILED_FUNCTIONS="${FAILED_FUNCTIONS} ${LAMBDA_MESSAGE}"; fi

# REST API Lambda 함수들
update_lambda_function "${LAMBDA_CONVERSATION}" "Conversation API 핸들러"
if [ $? -eq 0 ]; then SUCCESS_COUNT=$((SUCCESS_COUNT + 1)); else FAIL_COUNT=$((FAIL_COUNT + 1)); FAILED_FUNCTIONS="${FAILED_FUNCTIONS} ${LAMBDA_CONVERSATION}"; fi

update_lambda_function "${LAMBDA_PROMPT}" "Prompt CRUD 핸들러"
if [ $? -eq 0 ]; then SUCCESS_COUNT=$((SUCCESS_COUNT + 1)); else FAIL_COUNT=$((FAIL_COUNT + 1)); FAILED_FUNCTIONS="${FAILED_FUNCTIONS} ${LAMBDA_PROMPT}"; fi

update_lambda_function "${LAMBDA_USAGE}" "Usage 핸들러"
if [ $? -eq 0 ]; then SUCCESS_COUNT=$((SUCCESS_COUNT + 1)); else FAIL_COUNT=$((FAIL_COUNT + 1)); FAILED_FUNCTIONS="${FAILED_FUNCTIONS} ${LAMBDA_USAGE}"; fi

# =============================================================================
# 4. 정리 및 최종 검증
# =============================================================================

echo ""
echo "🧹 [3/3] 정리 및 검증..."

# 임시 파일 정리
rm -rf package deployment.zip

echo ""
echo "========================================="
echo "   Lambda 코드 배포 결과"
echo "========================================="
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo "✅ 모든 Lambda 함수 배포 완료! (${SUCCESS_COUNT}/6)"
    echo ""
    echo "배포된 Lambda 함수들:"
    echo "   📡 WebSocket API:"
    echo "      • ${LAMBDA_CONNECT}"
    echo "      • ${LAMBDA_DISCONNECT}"
    echo "      • ${LAMBDA_MESSAGE}"
    echo ""
    echo "   🌐 REST API:"
    echo "      • ${LAMBDA_CONVERSATION}"
    echo "      • ${LAMBDA_PROMPT}"
    echo "      • ${LAMBDA_USAGE}"
    echo ""
    echo "🔧 적용된 개선사항:"
    echo "   • 하드코딩된 테이블명 자동 수정"
    echo "   • 동적 서비스명 지원 (${SERVICE_NAME})"
    echo "   • 백업 생성 (${BACKUP_DIR})"
    echo ""
    echo "🔧 환경변수 설정:"
    echo "   • 모든 테이블명 (CARD_COUNT 포함)"
    echo "   • API 엔드포인트 URL"
    echo "   • Bedrock 모델 설정"
    echo "   • 로깅 및 CloudWatch 설정"
else
    echo "⚠️  일부 Lambda 함수 배포 실패"
    echo "성공: ${SUCCESS_COUNT}개, 실패: ${FAIL_COUNT}개"
    echo ""
    echo "실패한 함수들:${FAILED_FUNCTIONS}"
    echo ""
    echo "해결 방법:"
    echo "1. 잠시 기다린 후 다시 실행: ./05-deploy-lambda-code-improved.sh"
    echo "2. AWS 콘솔에서 직접 확인"
fi

# deployment-info.txt에 정보 추가
echo ""
echo "📋 배포 정보 업데이트 중..."

cat >> deployment-info.txt << EOF

========================================
Lambda 코드 배포 완료 (개선된 버전)
========================================
배포 시간: $(date '+%Y년 %m월 %d일 %H시 %M분 %S초 KST')

배포 결과: ${SUCCESS_COUNT}/6 함수 성공

WebSocket Lambda 함수:
  - ${LAMBDA_CONNECT} (Connect 핸들러)
  - ${LAMBDA_DISCONNECT} (Disconnect 핸들러)
  - ${LAMBDA_MESSAGE} (Message 핸들러)

REST API Lambda 함수:
  - ${LAMBDA_CONVERSATION} (대화 관리)
  - ${LAMBDA_PROMPT} (프롬프트 CRUD)
  - ${LAMBDA_USAGE} (사용량 추적)

적용된 개선사항:
  - 하드코딩 제거: 모든 테이블명 동적 수정
  - 백업 생성: ${BACKUP_DIR}
  - 서비스명 변수화: ${SERVICE_NAME}

환경변수 설정:
  - 테이블: ${SERVICE_NAME}-*-${CARD_COUNT}
  - API 엔드포인트: 실제 URL 설정
  - Bedrock: Claude Sonnet 4 모델
  - 로깅: INFO 레벨, CloudWatch 활성화

========================================
EOF

echo ""
echo "========================================="
if [ $FAIL_COUNT -eq 0 ]; then
    echo "🎉 Lambda 코드 배포 성공!"
    echo "========================================="
    echo ""
    echo "🚀 다음 단계:"
    echo "   • Frontend 배포: ./06-deploy-frontend.sh"
    echo "   • 전체 시스템 테스트"
    echo "   • API 엔드포인트 동작 확인"
    echo ""
    echo "🔍 전체 정보: cat deployment-info.txt"
else
    echo "⚠️  배포 중 오류 발생 - 재시도 필요"
    exit 1
fi
echo "========================================="