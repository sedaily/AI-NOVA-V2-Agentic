#!/bin/bash

# Config 파일 업데이트 스크립트 - Frontend/Backend 환경변수 설정

# 설정 파일 확인
if [ ! -f "config.sh" ]; then
    echo "❌ config.sh 파일이 없습니다. 먼저 ./init.sh를 실행하세요."
    exit 1
fi

source config.sh

echo "========================================="
echo "   [4/4] Config 파일 업데이트"
echo "   스택: ${STACK_NAME}"
echo "========================================="

# deployment-info.txt에서 API ID 추출
if [ ! -f "deployment-info.txt" ]; then
    echo "❌ deployment-info.txt 파일이 없습니다. 03-deploy-api-gateway.sh를 먼저 실행하세요."
    exit 1
fi

echo "📖 API 엔드포인트 정보 추출 중..."

# API ID 추출 (deployment-info.txt에서)
REST_API_ID=$(grep "  - ID:" deployment-info.txt | head -1 | awk '{print $3}')
WEBSOCKET_API_ID=$(grep "  - ID:" deployment-info.txt | tail -1 | awk '{print $3}')

if [ -z "$REST_API_ID" ] || [ -z "$WEBSOCKET_API_ID" ]; then
    echo "❌ API ID를 찾을 수 없습니다. deployment-info.txt를 확인하세요."
    exit 1
fi

echo "✅ REST API ID: ${REST_API_ID}"
echo "✅ WebSocket API ID: ${WEBSOCKET_API_ID}"

# 엔드포인트 URL 생성
REST_API_URL="https://${REST_API_ID}.execute-api.${REGION}.amazonaws.com/prod"
WEBSOCKET_API_URL="wss://${WEBSOCKET_API_ID}.execute-api.${REGION}.amazonaws.com/prod"

echo "📝 생성될 엔드포인트:"
echo "   REST API: ${REST_API_URL}"
echo "   WebSocket: ${WEBSOCKET_API_URL}"
echo ""

# =============================================================================
# 1. Frontend .env 파일 생성
# =============================================================================

echo "🎨 [1/2] Frontend 환경변수 파일 생성 중..."

FRONTEND_ENV_FILE="../frontend/.env"

# 기존 .env 파일 백업
if [ -f "${FRONTEND_ENV_FILE}" ]; then
    echo "   💾 기존 .env 파일 백업: .env.backup.$(date +%Y%m%d_%H%M%S)"
    cp "${FRONTEND_ENV_FILE}" "${FRONTEND_ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
fi

# .env.production 파일도 동시에 업데이트 (Vite 프로덕션 빌드 우선순위)
FRONTEND_ENV_PRODUCTION="${FRONTEND_DIR}/.env.production"

# 기존 .env.production 파일 백업
if [ -f "${FRONTEND_ENV_PRODUCTION}" ]; then
    echo "   💾 기존 .env.production 파일 백업: .env.production.backup.$(date +%Y%m%d_%H%M%S)"
    cp "${FRONTEND_ENV_PRODUCTION}" "${FRONTEND_ENV_PRODUCTION}.backup.$(date +%Y%m%d_%H%M%S)"
fi

# .env.production 파일 생성 (프로덕션 빌드 시 우선 적용됨)
cat > "${FRONTEND_ENV_PRODUCTION}" << EOF
# API 엔드포인트 (${SERVICE_NAME}-${CARD_COUNT})
VITE_API_BASE_URL=${REST_API_URL}
VITE_WS_URL=${WEBSOCKET_API_URL}

# 서비스 설정
VITE_APP_TITLE=${SERVICE_NAME}-${CARD_COUNT}
VITE_APP_DESCRIPTION="AI 콘텐츠 생성 서비스"

# 기타 설정
VITE_ENABLE_NEWS_SEARCH=true
VITE_ENV=production
EOF

echo "✅ Frontend .env.production 파일 생성 완료: ${FRONTEND_ENV_PRODUCTION}"

# 새로운 .env 파일 생성
cat > "${FRONTEND_ENV_FILE}" << EOF
# ${SERVICE_NAME} ${CARD_COUNT} SERVICE CONFIGURATION
# Generated: $(date '+%Y년 %m월 %d일 %H시 %M분 %S초 KST')

# API 설정 - ${SERVICE_NAME} 서비스
VITE_API_BASE_URL=${REST_API_URL}
VITE_WS_URL=${WEBSOCKET_API_URL}

# AWS API Gateway - ${SERVICE_NAME} 서비스 엔드포인트
VITE_API_URL=${REST_API_URL}
VITE_PROMPT_API_URL=${REST_API_URL}
VITE_WEBSOCKET_URL=${WEBSOCKET_API_URL}
VITE_USAGE_API_URL=${REST_API_URL}
VITE_CONVERSATION_API_URL=${REST_API_URL}

# AWS Cognito 설정 (필요시 업데이트)
VITE_AWS_REGION=${REGION}
VITE_COGNITO_USER_POOL_ID=YOUR_USER_POOL_ID
VITE_COGNITO_CLIENT_ID=YOUR_CLIENT_ID

# PDF.js CDN
VITE_PDFJS_CDN_URL=https://cdnjs.cloudflare.com/ajax/libs/pdf.js

# 개발/테스트 설정
VITE_USE_MOCK=false

# Service Type
VITE_SERVICE_TYPE=${CARD_COUNT}

# Organization Settings
VITE_ADMIN_EMAIL=admin@example.com
VITE_COMPANY_DOMAIN=@example.com
EOF

echo "✅ Frontend .env 파일 생성 완료: ${FRONTEND_ENV_FILE}"

# =============================================================================
# 2. Backend .env 파일 생성
# =============================================================================

echo "🔧 [2/2] Backend 환경변수 파일 생성 중..."

BACKEND_ENV_FILE="../backend/.env"

# 기존 .env 파일 백업
if [ -f "${BACKEND_ENV_FILE}" ]; then
    echo "   💾 기존 .env 파일 백업: .env.backup.$(date +%Y%m%d_%H%M%S)"
    cp "${BACKEND_ENV_FILE}" "${BACKEND_ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
fi

# 테이블명 정의 (DynamoDB 스크립트와 동일)
CONVERSATIONS_TABLE="${SERVICE_NAME}-conversations-${CARD_COUNT}"
FILES_TABLE="${SERVICE_NAME}-files-${CARD_COUNT}"
MESSAGES_TABLE="${SERVICE_NAME}-messages-${CARD_COUNT}"
PROMPTS_TABLE="${SERVICE_NAME}-prompts-${CARD_COUNT}"
USAGE_TABLE="${SERVICE_NAME}-usage-${CARD_COUNT}"
WEBSOCKET_TABLE="${SERVICE_NAME}-websocket-connections-${CARD_COUNT}"

# 새로운 .env 파일 생성
cat > "${BACKEND_ENV_FILE}" << EOF
# AWS 설정
AWS_REGION=${REGION}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID}

# DynamoDB 테이블 - ${SERVICE_NAME} ${CARD_COUNT} 스택
CONVERSATIONS_TABLE=${CONVERSATIONS_TABLE}
PROMPTS_TABLE=${PROMPTS_TABLE}
USAGE_TABLE=${USAGE_TABLE}
WEBSOCKET_TABLE=${WEBSOCKET_TABLE}
CONNECTIONS_TABLE=${WEBSOCKET_TABLE}
FILES_TABLE=${FILES_TABLE}
MESSAGES_TABLE=${MESSAGES_TABLE}

# API Gateway - ${SERVICE_NAME} ${CARD_COUNT} 서비스
REST_API_URL=${REST_API_URL}
WEBSOCKET_API_URL=${WEBSOCKET_API_URL}
WEBSOCKET_API_ID=${WEBSOCKET_API_ID}
API_STAGE=prod

# Lambda 설정
LAMBDA_TIMEOUT=120
LAMBDA_MEMORY=1024
LOG_LEVEL=INFO

# Bedrock 설정
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
BEDROCK_OPUS_MODEL_ID=us.anthropic.claude-opus-4-1-20250805-v1:0
BEDROCK_MAX_TOKENS=16384
BEDROCK_TEMPERATURE=0.7
BEDROCK_TOP_P=0.9
BEDROCK_TOP_K=40
ANTHROPIC_VERSION=bedrock-2023-05-31

# 가드레일 설정 (필요시 업데이트)
GUARDRAIL_ID=YOUR_GUARDRAIL_ID
GUARDRAIL_VERSION=1
GUARDRAIL_ENABLED=true

# CloudWatch
CLOUDWATCH_NAMESPACE=${SERVICE_NAME}-${CARD_COUNT}
LOG_GROUP=/aws/lambda/${SERVICE_NAME}-${CARD_COUNT}
METRICS_ENABLED=true

# 뉴스 검색 활성화
ENABLE_NEWS_SEARCH=true

# 엔진 타입
DEFAULT_ENGINE_TYPE=11
SECONDARY_ENGINE_TYPE=22
AVAILABLE_ENGINES=11,22,33
EOF

echo "✅ Backend .env 파일 생성 완료: ${BACKEND_ENV_FILE}"

# =============================================================================
# 3. 최종 검증
# =============================================================================

echo ""
echo "========================================="
echo "   Configuration 검증"
echo "========================================="

# Frontend .env 검증
if [ -f "${FRONTEND_ENV_FILE}" ]; then
    echo "✅ Frontend .env 파일 존재"
    echo "   📍 API Base URL: $(grep VITE_API_BASE_URL ${FRONTEND_ENV_FILE} | cut -d'=' -f2)"
    echo "   📍 WebSocket URL: $(grep VITE_WS_URL ${FRONTEND_ENV_FILE} | cut -d'=' -f2)"
else
    echo "❌ Frontend .env 파일 생성 실패"
fi

# Backend .env 검증
if [ -f "${BACKEND_ENV_FILE}" ]; then
    echo "✅ Backend .env 파일 존재"
    echo "   📍 Conversations Table: $(grep CONVERSATIONS_TABLE ${BACKEND_ENV_FILE} | cut -d'=' -f2)"
    echo "   📍 REST API URL: $(grep REST_API_URL ${BACKEND_ENV_FILE} | cut -d'=' -f2)"
else
    echo "❌ Backend .env 파일 생성 실패"
fi

# =============================================================================
# 4. 요약 정보 업데이트
# =============================================================================

echo ""
echo "📋 최종 배포 정보를 deployment-info.txt에 추가 중..."

cat >> deployment-info.txt << EOF

========================================
Configuration 파일 업데이트 완료
========================================
업데이트 시간: $(date '+%Y년 %m월 %d일 %H시 %M분 %S초 KST')

Frontend (.env):
  - VITE_API_BASE_URL=${REST_API_URL}
  - VITE_WS_URL=${WEBSOCKET_API_URL}
  - Service Type: ${CARD_COUNT}

Frontend (.env.production) - 프로덕션 빌드 우선순위:
  - VITE_API_BASE_URL=${REST_API_URL}
  - VITE_WS_URL=${WEBSOCKET_API_URL}
  - VITE_ENV=production

Backend (.env):
  - 테이블 접두사: ${SERVICE_NAME}-*-${CARD_COUNT}
  - Conversations: ${CONVERSATIONS_TABLE}
  - Messages: ${MESSAGES_TABLE}
  - Prompts: ${PROMPTS_TABLE}
  - Usage: ${USAGE_TABLE}
  - Files: ${FILES_TABLE}
  - WebSocket: ${WEBSOCKET_TABLE}

========================================
⚠️  중요: 환경변수 파일 우선순위
========================================
Vite 빌드 시 환경변수 우선순위:
1. .env.production (최우선 - 프로덕션 빌드 시)
2. .env (기본)

프로덕션 배포 시 반드시 .env.production 파일 확인!
- REST API URL이 올바른지 확인
- WebSocket URL이 올바른지 확인

========================================
🎉 전체 인프라 구축 완료!
========================================

다음 단계:
1. Frontend 빌드 및 배포: ./05-deploy-lambda-code.sh
2. Lambda 함수 코드 업데이트: ./06-deploy-frontend.sh
3. 테스트 및 검증

인프라 스택: ${STACK_NAME}
생성 완료 시간: $(date '+%Y년 %m월 %d일 %H시 %M분 %S초 KST')
========================================

EOF

echo ""
echo "========================================="
echo "✅ Configuration 업데이트 완료!"
echo "========================================="
echo ""
echo "🎯 생성된 파일:"
echo "   • ${FRONTEND_ENV_FILE}"
echo "   • ${BACKEND_ENV_FILE}"
echo ""
echo "🚀 다음 단계:"
echo "   • Frontend 배포: ./deploy-frontend.sh"
echo "   • Lambda 코드 업데이트"
echo "   • 서비스 테스트"
echo ""
echo "🔍 전체 정보 확인: cat deployment-info.txt"
echo "========================================="