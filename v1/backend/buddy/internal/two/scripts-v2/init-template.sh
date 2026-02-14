#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}==================================${NC}"
echo -e "${BLUE}  Nexus Template v2 초기화 마법사  ${NC}"
echo -e "${BLUE}==================================${NC}"
echo ""

# 서비스 이름 입력
read -p "서비스 이름을 입력하세요 (예: f2, w1, b1): " SERVICE_NAME
if [ -z "$SERVICE_NAME" ]; then
    echo -e "${RED}서비스 이름이 필요합니다.${NC}"
    exit 1
fi

# 카드 이름 입력
read -p "카드 식별자를 입력하세요 (예: one, two, three): " CARD_COUNT
if [ -z "$CARD_COUNT" ]; then
    echo -e "${RED}카드 식별자가 필요합니다.${NC}"
    exit 1
fi

# AWS 리전 입력 (기본값: us-east-1)
read -p "AWS 리전을 입력하세요 (기본값: us-east-1): " REGION
REGION=${REGION:-us-east-1}

# AWS 계정 ID 가져오기
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
if [ -z "$ACCOUNT_ID" ]; then
    echo -e "${RED}AWS 계정 ID를 가져올 수 없습니다. AWS CLI가 올바르게 구성되었는지 확인하세요.${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}=== 구성 확인 ===${NC}"
echo "서비스 이름: $SERVICE_NAME"
echo "카드 식별자: $CARD_COUNT"
echo "리전: $REGION"
echo "계정 ID: $ACCOUNT_ID"
echo ""

read -p "위 설정으로 진행하시겠습니까? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    echo "취소되었습니다."
    exit 0
fi

# config.sh 생성
echo -e "${YELLOW}config.sh 파일 생성 중...${NC}"
cat > config.sh << EOF
#!/bin/bash
export SERVICE_NAME="$SERVICE_NAME"
export CARD_COUNT="$CARD_COUNT"
export REGION="$REGION"
export ACCOUNT_ID=$ACCOUNT_ID

# 리소스 이름
export CONVERSATIONS_TABLE="${SERVICE_NAME}-conversations-${CARD_COUNT}"
export PROMPTS_TABLE="${SERVICE_NAME}-prompts-${CARD_COUNT}"
export USAGE_TABLE="${SERVICE_NAME}-usage-${CARD_COUNT}"
export LAMBDA_API="${SERVICE_NAME}-api-lambda-${CARD_COUNT}"
export LAMBDA_WS="${SERVICE_NAME}-websocket-lambda-${CARD_COUNT}"
export LAMBDA_CONVERSATION_API="${SERVICE_NAME}-conversation-api-${CARD_COUNT}"
export LAMBDA_WEBSOCKET_MESSAGE="${SERVICE_NAME}-websocket-message-${CARD_COUNT}"
export LAMBDA_PROMPT_API="${SERVICE_NAME}-prompt-api-${CARD_COUNT}"
export LAMBDA_USAGE_API="${SERVICE_NAME}-usage-api-${CARD_COUNT}"
export LAMBDA_WEBSOCKET_CONNECT="${SERVICE_NAME}-websocket-connect-${CARD_COUNT}"
export LAMBDA_WEBSOCKET_DISCONNECT="${SERVICE_NAME}-websocket-disconnect-${CARD_COUNT}"
export REST_API_NAME="${SERVICE_NAME}-rest-api-${CARD_COUNT}"
export WEBSOCKET_API_NAME="${SERVICE_NAME}-websocket-api-${CARD_COUNT}"
export S3_BUCKET="${SERVICE_NAME}-${CARD_COUNT}-frontend"
export STACK_NAME="${SERVICE_NAME}-${CARD_COUNT}"
EOF

echo -e "${GREEN}✓ config.sh 파일 생성 완료${NC}"

# 백엔드 코드에서 하드코딩된 값 수정
echo -e "${YELLOW}백엔드 코드 템플릿 준비 중...${NC}"

BACKEND_DIR="../backend"

# Repository 파일들 수정
fix_repository_files() {
    # conversation_repository.py
    if [ -f "${BACKEND_DIR}/src/repositories/conversation_repository.py" ]; then
        sed -i.bak "s/'[^']*-conversations-[^']*'/'${CONVERSATIONS_TABLE}'/g" \
            "${BACKEND_DIR}/src/repositories/conversation_repository.py"
        echo "✓ conversation_repository.py 수정"
    fi

    # prompt_repository.py
    if [ -f "${BACKEND_DIR}/src/repositories/prompt_repository.py" ]; then
        sed -i.bak "s/'[^']*-prompts-[^']*'/'${PROMPTS_TABLE}'/g" \
            "${BACKEND_DIR}/src/repositories/prompt_repository.py"
        echo "✓ prompt_repository.py 수정"
    fi

    # usage_repository.py
    if [ -f "${BACKEND_DIR}/src/repositories/usage_repository.py" ]; then
        sed -i.bak "s/'[^']*-usage[^']*'/'${USAGE_TABLE}'/g" \
            "${BACKEND_DIR}/src/repositories/usage_repository.py"
        echo "✓ usage_repository.py 수정"
    fi

    # conversation_manager.py
    if [ -f "${BACKEND_DIR}/handlers/websocket/conversation_manager.py" ]; then
        sed -i.bak "s/'[^']*-conversations-[^']*'/'${CONVERSATIONS_TABLE}'/g" \
            "${BACKEND_DIR}/handlers/websocket/conversation_manager.py"
        echo "✓ conversation_manager.py 수정"
    fi

    # websocket_service.py의 프롬프트 테이블 수정
    if [ -f "${BACKEND_DIR}/services/websocket_service.py" ]; then
        sed -i.bak "s/'[^']*-prompts-[^']*'/'${PROMPTS_TABLE}'/g" \
            "${BACKEND_DIR}/services/websocket_service.py"
        echo "✓ websocket_service.py 수정"
    fi

    # 백업 파일 삭제
    find "${BACKEND_DIR}" -name "*.bak" -delete
}

fix_repository_files

# 프론트엔드 config 생성
echo -e "${YELLOW}프론트엔드 설정 템플릿 생성 중...${NC}"

FRONTEND_DIR="../frontend"
if [ -d "$FRONTEND_DIR" ]; then
    # config.js.template 생성
    cat > "${FRONTEND_DIR}/src/config.js.template" << 'EOF'
// API 엔드포인트
export const API_BASE_URL = "{{API_BASE_URL}}";
export const WS_URL = "{{WS_URL}}";

// 애플리케이션 설정
export const APP_NAME = "{{SERVICE_NAME}} AI Assistant";
export const APP_VERSION = "2.0.0";

// 기능 플래그
export const FEATURES = {
  MULTI_ENGINE: true,
  FILE_UPLOAD: true,
  CONVERSATION_HISTORY: true,
  USAGE_TRACKING: true,
  ADMIN_PANEL: false
};

// 엔진 설정
export const ENGINES = {
  "11": {
    name: "Claude 3.5 Sonnet",
    description: "가장 강력한 AI 모델",
    maxTokens: 100000,
    icon: "🚀"
  },
  "22": {
    name: "GPT-4 Turbo",
    description: "OpenAI의 최신 모델",
    maxTokens: 128000,
    icon: "⚡"
  },
  "33": {
    name: "Gemini Pro",
    description: "Google의 멀티모달 AI",
    maxTokens: 32000,
    icon: "💫"
  }
};

export default {
  API_BASE_URL,
  WS_URL,
  APP_NAME,
  APP_VERSION,
  FEATURES,
  ENGINES
};
EOF
    echo -e "${GREEN}✓ 프론트엔드 config 템플릿 생성 완료${NC}"
fi

# 실행 권한 부여
chmod +x *.sh

echo ""
echo -e "${GREEN}==================================${NC}"
echo -e "${GREEN}      초기화 완료!               ${NC}"
echo -e "${GREEN}==================================${NC}"
echo ""
echo "생성된 파일:"
echo "  - config.sh: 환경 변수 설정"
echo "  - frontend/src/config.js.template: 프론트엔드 설정 템플릿"
echo ""
echo "수정된 백엔드 파일:"
echo "  - src/repositories/*.py: 테이블명 수정"
echo "  - handlers/websocket/conversation_manager.py: 테이블명 수정"
echo ""
echo -e "${YELLOW}다음 단계:${NC}"
echo "1. 인프라 배포: ./01-deploy-dynamodb.sh"
echo "2. Lambda 함수 생성: ./02-deploy-lambda.sh"
echo "3. API Gateway 설정: ./03-deploy-api-gateway-final.sh"
echo "4. Lambda 코드 배포: ./05-deploy-lambda-code-fixed.sh"
echo "5. 프론트엔드 배포: ./06-deploy-frontend.sh"
echo ""
echo -e "${BLUE}전체 배포 실행: ./deploy-all.sh${NC}"