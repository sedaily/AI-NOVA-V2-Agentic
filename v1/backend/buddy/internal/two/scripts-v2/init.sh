#!/bin/bash

# 초기화 스크립트 - 서비스명과 카드 개수 입력
set -e

echo "========================================="
echo "   서비스 템플릿 초기화"
echo "========================================="

# 서비스 설정
read -p "서비스명 입력 (예: w2, demo1): " SERVICE_NAME

# 카드 개수
echo ""
read -p "카드 개수 입력 (예: one, two, three, five): " CARD_COUNT

# 입력값 검증 (영문 소문자만 허용)
if [[ ! "$CARD_COUNT" =~ ^[a-z]+$ ]]; then
    echo "❌ 카드 개수는 영문 소문자만 사용 가능합니다."
    exit 1
fi

# 리전 선택
echo ""
read -p "AWS 리전 입력 (기본값: us-east-1): " INPUT_REGION
REGION=${INPUT_REGION:-us-east-1}

# 설정 파일 생성
cat > config.sh << EOF
#!/bin/bash
export SERVICE_NAME="${SERVICE_NAME}"
export CARD_COUNT="${CARD_COUNT}"
export REGION="${REGION}"
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# 리소스 이름
export CONVERSATIONS_TABLE="${SERVICE_NAME}-conversations-${CARD_COUNT}"
export PROMPTS_TABLE="${SERVICE_NAME}-prompts-${CARD_COUNT}"
export USAGE_TABLE="${SERVICE_NAME}-usage-${CARD_COUNT}"
export LAMBDA_API="${SERVICE_NAME}-api-lambda"
export LAMBDA_WS="${SERVICE_NAME}-websocket-lambda"
export REST_API_NAME="${SERVICE_NAME}-rest-api"
export WEBSOCKET_API_NAME="${SERVICE_NAME}-websocket-api"
export S3_BUCKET="${SERVICE_NAME}-${CARD_COUNT}-frontend"
export STACK_NAME="${SERVICE_NAME}-${CARD_COUNT}"
EOF

echo ""
echo "✅ 설정 완료"
echo "스택 이름: ${SERVICE_NAME}-${CARD_COUNT}"
echo "리전: ${REGION}"
echo ""
echo "프론트엔드 배포: ./deploy-frontend.sh"