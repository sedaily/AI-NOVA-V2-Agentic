#!/bin/bash

# ============================================
# Lambda 환경변수 업데이트 스크립트
# ============================================

set -e

PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONFIG_FILE="$PROJECT_ROOT/config/t1-production.env"

# Load configuration
source "$CONFIG_FILE"

echo "🔧 Lambda 환경변수 업데이트..."

# Environment variables
ENV_VARS=$(cat <<EOF
{
    "Variables": {
        "ENV": "$ENV",
        "SERVICE_NAME": "$SERVICE_NAME",
        "WEBSOCKET_API_URL": "$WEBSOCKET_API_URL",
        "USE_ANTHROPIC_API": "$USE_ANTHROPIC_API",
        "ANTHROPIC_SECRET_NAME": "$ANTHROPIC_SECRET_NAME",
        "ANTHROPIC_MODEL_ID": "$ANTHROPIC_MODEL_ID",
        "AI_PROVIDER": "$AI_PROVIDER",
        "FALLBACK_TO_BEDROCK": "$FALLBACK_TO_BEDROCK",
        "ANTHROPIC_MAX_TOKENS": "$ANTHROPIC_MAX_TOKENS",
        "ANTHROPIC_TEMPERATURE": "$ANTHROPIC_TEMPERATURE",
        "USE_RAG": "$USE_RAG",
        "LOG_LEVEL": "$LOG_LEVEL"
    }
}
EOF
)

# Update Lambda functions
LAMBDA_FUNCTIONS=(
    "$LAMBDA_WS_MESSAGE"
    "$LAMBDA_CONVERSATION"
)

for func in "${LAMBDA_FUNCTIONS[@]}"; do
    echo "🔄 업데이트: $func"
    aws lambda update-function-configuration \
        --function-name "$func" \
        --environment "$ENV_VARS" \
        --region "$AWS_REGION" \
        --output text > /dev/null 2>&1 || echo "⚠️  $func 건너뜀"
done

echo "✅ 환경변수 업데이트 완료!"