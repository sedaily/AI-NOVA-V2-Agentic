#!/bin/bash

# Lambda 코드 배포

source "$(dirname "$0")/00-config.sh"

log_info "Lambda 코드 배포 시작..."

# 요구사항 설치
log_info "요구사항 패키지 설치 중..."
cd "$BACKEND_DIR"
pip install -r requirements.txt -t ./package --quiet

# 배포 패키지 생성
log_info "배포 패키지 생성 중..."
cd package
cp -r ../handlers .
cp -r ../services .
cp -r ../src .
cp -r ../lib .
cp -r ../utils .
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
zip -r ../deployment.zip . -q
cd ..

# Lambda 함수 업데이트 함수
update_lambda() {
    local function_name=$1
    
    log_info "$function_name 함수 코드 업데이트 중..."
    
    aws lambda update-function-code \
        --function-name "$function_name" \
        --zip-file fileb://deployment.zip \
        --region "$REGION" >/dev/null
    
    # 환경변수 업데이트 (tem1-messages 테이블 포함)
    aws lambda update-function-configuration \
        --function-name "$function_name" \
        --environment "Variables={
            PROMPTS_TABLE=$TABLE_PROMPTS,
            FILES_TABLE=$TABLE_FILES,
            CONVERSATIONS_TABLE=$TABLE_CONVERSATIONS,
            MESSAGES_TABLE=$TABLE_MESSAGES,
            USAGE_TABLE=$TABLE_USAGE,
            CONNECTIONS_TABLE=$TABLE_CONNECTIONS,
            WEBSOCKET_TABLE=$TABLE_CONNECTIONS,
            ENABLE_NEWS_SEARCH=true,
            WEBSOCKET_API_ID=$WS_API_ID
        }" \
        --region "$REGION" >/dev/null
    
    log_success "$function_name 코드 업데이트 완료"
}

# WebSocket API ID 가져오기
WS_API_ID=$(aws apigatewayv2 get-apis \
    --query "Items[?Name=='$WEBSOCKET_API_NAME'].ApiId" \
    --output text --region "$REGION")

# 모든 Lambda 함수 업데이트
update_lambda "$LAMBDA_CONNECT"
update_lambda "$LAMBDA_DISCONNECT"
update_lambda "$LAMBDA_MESSAGE"
update_lambda "$LAMBDA_CONVERSATION"
update_lambda "$LAMBDA_PROMPT"
update_lambda "$LAMBDA_USAGE"

# 정리
rm -rf package deployment.zip

log_success "모든 Lambda 함수 코드 배포 완료!"