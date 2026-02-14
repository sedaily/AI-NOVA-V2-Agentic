#!/bin/bash

# Bedrock 설정 스크립트

LAMBDA_FUNCTION="p2-two-websocket-message-two"

echo "🔧 Setting AWS Bedrock as AI provider..."

aws lambda update-function-configuration \
    --function-name "$LAMBDA_FUNCTION" \
    --environment "Variables={AI_PROVIDER=bedrock,PROMPTS_TABLE=b1-prompts-v2,FILES_TABLE=b1-files-v2,ENABLE_WEB_SEARCH=true}" \
    --region us-east-1

if [ $? -eq 0 ]; then
    echo "✅ Bedrock configured"
    echo ""
    echo "Settings:"
    echo "  AI_PROVIDER=bedrock"
    echo "  PROMPTS_TABLE=b1-prompts-v2"
    echo "  FILES_TABLE=b1-files-v2"
    echo "  ENABLE_WEB_SEARCH=true"
else
    echo "❌ Failed to update Lambda"
fi
