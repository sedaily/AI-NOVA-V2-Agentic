#!/bin/bash

# Anthropic API로 전환하는 스크립트

LAMBDA_FUNCTION="p2-two-websocket-message-two"

echo "🔧 Switching to Anthropic API..."

aws lambda update-function-configuration \
    --function-name "$LAMBDA_FUNCTION" \
    --environment "Variables={AI_PROVIDER=anthropic_api,PROMPTS_TABLE=b1-prompts-v2,FILES_TABLE=b1-files-v2,ENABLE_WEB_SEARCH=true,FALLBACK_TO_BEDROCK=true}" \
    --region us-east-1

if [ $? -eq 0 ]; then
    echo "✅ Successfully switched to Anthropic API"
    echo ""
    echo "Current settings:"
    echo "  AI_PROVIDER=anthropic_api"
    echo "  PROMPTS_TABLE=b1-prompts-v2"
    echo "  FILES_TABLE=b1-files-v2"
    echo "  ENABLE_WEB_SEARCH=true"
    echo "  FALLBACK_TO_BEDROCK=true"
else
    echo "❌ Failed to update Lambda"
fi
