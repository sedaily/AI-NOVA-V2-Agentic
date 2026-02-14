#!/bin/bash

# Lambda 함수 이름들
LAMBDA_FUNCTIONS=(
    "p2-two-websocket-message-two"
    "p2-two-conversation-api-two"
    "p2-two-prompt-crud-two"
)

# 업데이트할 환경 변수
PROMPTS_TABLE="b1-prompts-v2"
FILES_TABLE="b1-files-v2"

echo "🔧 Updating Lambda environment variables for buddy tables..."

for FUNCTION_NAME in "${LAMBDA_FUNCTIONS[@]}"
do
    echo ""
    echo "📝 Updating $FUNCTION_NAME..."
    
    aws lambda update-function-configuration \
        --function-name "$FUNCTION_NAME" \
        --environment "Variables={PROMPTS_TABLE=$PROMPTS_TABLE,FILES_TABLE=$FILES_TABLE}" \
        --region us-east-1
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully updated $FUNCTION_NAME"
    else
        echo "❌ Failed to update $FUNCTION_NAME"
    fi
done

echo ""
echo "🎉 Lambda environment variables update completed!"
echo ""
echo "Updated variables:"
echo "  PROMPTS_TABLE=$PROMPTS_TABLE"
echo "  FILES_TABLE=$FILES_TABLE"
