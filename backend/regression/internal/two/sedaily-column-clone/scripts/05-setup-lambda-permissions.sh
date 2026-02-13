#!/bin/bash

# Lambda 함수 권한 설정

source "$(dirname "$0")/00-config.sh"

log_info "Lambda 함수 권한 설정 시작..."

# REST API ID 및 WebSocket API ID 가져오기
REST_API_ID=$(aws apigateway get-rest-apis \
    --query "items[?name=='$REST_API_NAME'].id" \
    --output text --region "$REGION")

WS_API_ID=$(aws apigatewayv2 get-apis \
    --query "Items[?Name=='$WEBSOCKET_API_NAME'].ApiId" \
    --output text --region "$REGION")

log_info "REST API ID: $REST_API_ID"
log_info "WebSocket API ID: $WS_API_ID"

# Lambda 권한 추가 함수
add_lambda_permission() {
    local function_name=$1
    local statement_id=$2
    local source_arn=$3
    
    log_info "$function_name 함수에 권한 추가 중..."
    
    # 기존 권한 삭제 (있으면)
    aws lambda remove-permission \
        --function-name "$function_name" \
        --statement-id "$statement_id" \
        --region "$REGION" 2>/dev/null || true
    
    # 새 권한 추가
    aws lambda add-permission \
        --function-name "$function_name" \
        --statement-id "$statement_id" \
        --action lambda:InvokeFunction \
        --principal apigateway.amazonaws.com \
        --source-arn "$source_arn" \
        --region "$REGION" >/dev/null
    
    log_success "$function_name 권한 설정 완료"
}

# REST API Lambda 권한
log_info "REST API Lambda 권한 설정 중..."
add_lambda_permission "$LAMBDA_PROMPT" "rest-api-invoke" \
    "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$REST_API_ID/*/*"

add_lambda_permission "$LAMBDA_CONVERSATION" "rest-api-invoke" \
    "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$REST_API_ID/*/*"

add_lambda_permission "$LAMBDA_USAGE" "rest-api-invoke" \
    "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$REST_API_ID/*/*"

# WebSocket API Lambda 권한
log_info "WebSocket API Lambda 권한 설정 중..."
add_lambda_permission "$LAMBDA_CONNECT" "websocket-api-invoke" \
    "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$WS_API_ID/*/*"

add_lambda_permission "$LAMBDA_DISCONNECT" "websocket-api-invoke" \
    "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$WS_API_ID/*/*"

add_lambda_permission "$LAMBDA_MESSAGE" "websocket-api-invoke" \
    "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$WS_API_ID/*/*"

log_success "모든 Lambda 함수 권한 설정 완료!"