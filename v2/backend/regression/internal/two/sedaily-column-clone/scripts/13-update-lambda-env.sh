#!/bin/bash

# Lambda 환경변수 업데이트 스크립트
# 성공한 배포 구조에 맞춰 Lambda 함수들의 환경변수를 업데이트

source "$(dirname "$0")/00-config.sh"

log_info "Lambda 환경변수 업데이트 시작..."

# 환경변수 JSON 생성
create_env_json() {
    cat > /tmp/lambda-env.json << EOF
{
  "Variables": {
    "ENABLE_NEWS_SEARCH": "true",
    "PROMPTS_TABLE": "$TABLE_PROMPTS",
    "FILES_TABLE": "$TABLE_FILES",
    "CONVERSATIONS_TABLE": "$TABLE_CONVERSATIONS",
    "USAGE_TABLE": "$TABLE_USAGE",
    "WEBSOCKET_TABLE": "$TABLE_CONNECTIONS",
    "CONNECTIONS_TABLE": "$TABLE_CONNECTIONS"
  }
}
EOF
}

# Lambda 함수 환경변수 업데이트 함수
update_lambda_env() {
    local function_name=$1
    log_info "$function_name 환경변수 업데이트 중..."

    if aws lambda get-function --function-name "$function_name" --region "$REGION" >/dev/null 2>&1; then
        RESULT=$(aws lambda update-function-configuration \
            --function-name "$function_name" \
            --environment file:///tmp/lambda-env.json \
            --region "$REGION" \
            --output json 2>&1)

        if [ $? -eq 0 ]; then
            LAST_MODIFIED=$(echo "$RESULT" | jq -r '.LastModified')
            log_success "$function_name 업데이트 완료: $LAST_MODIFIED"
        else
            log_error "$function_name 업데이트 실패: $RESULT"
        fi
    else
        log_warning "$function_name 함수를 찾을 수 없습니다"
    fi
}

# 환경변수 JSON 생성
create_env_json

log_info "설정될 환경변수:"
cat /tmp/lambda-env.json | jq '.Variables'
echo ""

# 모든 Lambda 함수 업데이트
update_lambda_env "$LAMBDA_PROMPT"
update_lambda_env "$LAMBDA_CONVERSATION"
update_lambda_env "$LAMBDA_MESSAGE"
update_lambda_env "$LAMBDA_CONNECT"
update_lambda_env "$LAMBDA_DISCONNECT"
update_lambda_env "$LAMBDA_USAGE"

# 임시 파일 정리
rm -f /tmp/lambda-env.json

log_success "모든 Lambda 함수 환경변수 업데이트 완료!"
echo ""
log_info "📋 업데이트된 Lambda 함수들:"
log_info "  • $LAMBDA_PROMPT"
log_info "  • $LAMBDA_CONVERSATION"
log_info "  • $LAMBDA_MESSAGE"
log_info "  • $LAMBDA_CONNECT"
log_info "  • $LAMBDA_DISCONNECT"
log_info "  • $LAMBDA_USAGE"
echo ""
log_info "💡 테이블 설정:"
log_info "  • Prompts: $TABLE_PROMPTS"
log_info "  • Files: $TABLE_FILES"
log_info "  • Conversations: $TABLE_CONVERSATIONS"
log_info "  • Usage: $TABLE_USAGE"
log_info "  • WebSocket: $TABLE_CONNECTIONS"