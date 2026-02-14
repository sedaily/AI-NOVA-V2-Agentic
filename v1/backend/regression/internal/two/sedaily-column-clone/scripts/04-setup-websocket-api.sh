#!/bin/bash

# WebSocket API Gateway 설정

source "$(dirname "$0")/00-config.sh"

log_info "WebSocket API Gateway 생성 시작..."

# WebSocket API 생성
WS_API_ID=$(aws apigatewayv2 create-api \
    --name "$WEBSOCKET_API_NAME" \
    --protocol-type WEBSOCKET \
    --route-selection-expression '\$request.body.action' \
    --region "$REGION" \
    --query 'ApiId' --output text)

log_success "WebSocket API 생성 완료: $WS_API_ID"

# 통합 생성 함수
create_integration() {
    local route=$1
    local function_name=$2
    
    log_info "$route 라우트 통합 생성 중..."
    
    local integration_id=$(aws apigatewayv2 create-integration \
        --api-id "$WS_API_ID" \
        --integration-type AWS_PROXY \
        --integration-uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/arn:aws:lambda:$REGION:$ACCOUNT_ID:function:$function_name/invocations" \
        --region "$REGION" \
        --query 'IntegrationId' --output text)
    
    echo "$integration_id"
}

# 라우트 생성 함수
create_route() {
    local route_key=$1
    local integration_id=$2
    
    log_info "$route_key 라우트 생성 중..."
    
    aws apigatewayv2 create-route \
        --api-id "$WS_API_ID" \
        --route-key "$route_key" \
        --target "integrations/$integration_id" \
        --region "$REGION" >/dev/null
}

# 통합 생성
CONNECT_INTEGRATION=$(create_integration "\$connect" "$LAMBDA_CONNECT")
DISCONNECT_INTEGRATION=$(create_integration "\$disconnect" "$LAMBDA_DISCONNECT")
DEFAULT_INTEGRATION=$(create_integration "\$default" "$LAMBDA_MESSAGE")

# 라우트 생성
create_route "\$connect" "$CONNECT_INTEGRATION"
create_route "\$disconnect" "$DISCONNECT_INTEGRATION"
create_route "\$default" "$DEFAULT_INTEGRATION"

# 배포 생성
DEPLOYMENT_ID=$(aws apigatewayv2 create-deployment \
    --api-id "$WS_API_ID" \
    --region "$REGION" \
    --query 'DeploymentId' --output text)

log_success "WebSocket API 배포 생성: $DEPLOYMENT_ID"

# 스테이지 생성
aws apigatewayv2 create-stage \
    --api-id "$WS_API_ID" \
    --stage-name prod \
    --deployment-id "$DEPLOYMENT_ID" \
    --region "$REGION" >/dev/null

log_success "WebSocket API 스테이지 생성 완료!"

# 엔드포인트 저장
echo "WEBSOCKET_API_ENDPOINT=wss://$WS_API_ID.execute-api.$REGION.amazonaws.com/prod" >> "$PROJECT_ROOT/endpoints.txt"

log_info "WebSocket API 엔드포인트: wss://$WS_API_ID.execute-api.$REGION.amazonaws.com/prod"