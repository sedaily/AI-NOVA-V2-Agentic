#!/bin/bash

# Enhanced REST API Gateway 설정 (CORS 및 전체 리소스 구조 포함)

source "$(dirname "$0")/00-config.sh"

log_info "Enhanced REST API Gateway 설정 시작..."

# API ID 확인 (기존 API 사용 또는 새로 생성)
if [ -n "$REST_API_ID" ]; then
    API_ID="$REST_API_ID"
    log_info "기존 REST API 사용: $API_ID"
else
    # 새 REST API 생성
    API_ID=$(aws apigateway create-rest-api \
        --name "$REST_API_NAME" \
        --description "REST API for $SERVICE_NAME" \
        --region "$REGION" \
        --query 'id' --output text)

    log_success "REST API 생성 완료: $API_ID"
fi

# 리소스 ID 가져오기
ROOT_ID=$(aws apigateway get-resources \
    --rest-api-id "$API_ID" \
    --region "$REGION" \
    --query 'items[?path==`/`].id' --output text)

# CORS 설정 함수
add_cors() {
    local resource_id=$1
    local methods=$2

    log_info "리소스 $resource_id에 CORS 추가..."

    # OPTIONS 메서드가 이미 존재하는지 확인
    METHOD_EXISTS=$(aws apigateway get-method \
        --rest-api-id "$API_ID" \
        --resource-id "$resource_id" \
        --http-method OPTIONS \
        --region "$REGION" 2>/dev/null || echo "")

    if [ -z "$METHOD_EXISTS" ]; then
        # OPTIONS 메서드 생성
        aws apigateway put-method \
            --rest-api-id "$API_ID" \
            --resource-id "$resource_id" \
            --http-method OPTIONS \
            --authorization-type NONE \
            --region "$REGION" >/dev/null

        # 메서드 응답 추가
        aws apigateway put-method-response \
            --rest-api-id "$API_ID" \
            --resource-id "$resource_id" \
            --http-method OPTIONS \
            --status-code 200 \
            --response-models '{"application/json":"Empty"}' \
            --response-parameters '{"method.response.header.Access-Control-Allow-Headers":false,"method.response.header.Access-Control-Allow-Methods":false,"method.response.header.Access-Control-Allow-Origin":false}' \
            --region "$REGION" >/dev/null

        # MOCK 통합 추가
        aws apigateway put-integration \
            --rest-api-id "$API_ID" \
            --resource-id "$resource_id" \
            --http-method OPTIONS \
            --type MOCK \
            --request-templates '{"application/json":"{\"statusCode\":200}"}' \
            --region "$REGION" >/dev/null

        # 통합 응답 추가 (CORS 헤더 포함)
        aws apigateway put-integration-response \
            --rest-api-id "$API_ID" \
            --resource-id "$resource_id" \
            --http-method OPTIONS \
            --status-code 200 \
            --response-parameters "{\"method.response.header.Access-Control-Allow-Headers\":\"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'\",\"method.response.header.Access-Control-Allow-Methods\":\"'$methods'\",\"method.response.header.Access-Control-Allow-Origin\":\"'*'\"}" \
            --region "$REGION" >/dev/null

        log_success "CORS OPTIONS 메서드 추가 완료"
    fi
}

# 메서드 추가 함수
add_method() {
    local resource_id=$1
    local method=$2
    local lambda_func=$3

    log_info "$method 메서드 추가..."

    # 메서드 생성
    aws apigateway put-method \
        --rest-api-id "$API_ID" \
        --resource-id "$resource_id" \
        --http-method "$method" \
        --authorization-type NONE \
        --region "$REGION" >/dev/null 2>&1

    # Lambda 통합
    aws apigateway put-integration \
        --rest-api-id "$API_ID" \
        --resource-id "$resource_id" \
        --http-method "$method" \
        --type AWS_PROXY \
        --integration-http-method POST \
        --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/arn:aws:lambda:$REGION:$ACCOUNT_ID:function:$lambda_func/invocations" \
        --region "$REGION" >/dev/null 2>&1
}

# 리소스 생성 또는 가져오기 함수
get_or_create_resource() {
    local parent_id=$1
    local path_part=$2

    # 기존 리소스 확인
    local existing_id=$(aws apigateway get-resources \
        --rest-api-id "$API_ID" \
        --region "$REGION" \
        --query "items[?pathPart=='$path_part' && parentId=='$parent_id'].id" \
        --output text 2>/dev/null)

    if [ -n "$existing_id" ]; then
        log_info "기존 리소스 사용: /$path_part"
        echo "$existing_id"
    else
        # 새 리소스 생성
        local resource_id=$(aws apigateway create-resource \
            --rest-api-id "$API_ID" \
            --parent-id "$parent_id" \
            --path-part "$path_part" \
            --region "$REGION" \
            --query 'id' --output text)

        log_success "새 리소스 생성: /$path_part"
        echo "$resource_id"
    fi
}

# =============================================
# 1. /conversations 리소스 구조
# =============================================
log_info "Conversations API 구조 설정..."

CONVERSATIONS_ID=$(get_or_create_resource "$ROOT_ID" "conversations")
add_method "$CONVERSATIONS_ID" "GET" "$LAMBDA_CONVERSATION"
add_method "$CONVERSATIONS_ID" "POST" "$LAMBDA_CONVERSATION"
add_method "$CONVERSATIONS_ID" "PUT" "$LAMBDA_CONVERSATION"
add_cors "$CONVERSATIONS_ID" "GET,POST,PUT,OPTIONS"

# /conversations/{conversationId}
CONVERSATION_ITEM_ID=$(get_or_create_resource "$CONVERSATIONS_ID" "{conversationId}")
add_method "$CONVERSATION_ITEM_ID" "GET" "$LAMBDA_CONVERSATION"
add_method "$CONVERSATION_ITEM_ID" "PUT" "$LAMBDA_CONVERSATION"
add_method "$CONVERSATION_ITEM_ID" "DELETE" "$LAMBDA_CONVERSATION"
add_cors "$CONVERSATION_ITEM_ID" "GET,PUT,DELETE,OPTIONS"

# =============================================
# 2. /prompts 리소스 구조
# =============================================
log_info "Prompts API 구조 설정..."

PROMPTS_ID=$(get_or_create_resource "$ROOT_ID" "prompts")
add_method "$PROMPTS_ID" "GET" "$LAMBDA_PROMPT"
add_method "$PROMPTS_ID" "POST" "$LAMBDA_PROMPT"
add_cors "$PROMPTS_ID" "GET,POST,OPTIONS"

# /prompts/{promptId}
PROMPT_ITEM_ID=$(get_or_create_resource "$PROMPTS_ID" "{promptId}")
add_method "$PROMPT_ITEM_ID" "GET" "$LAMBDA_PROMPT"
add_method "$PROMPT_ITEM_ID" "POST" "$LAMBDA_PROMPT"
add_method "$PROMPT_ITEM_ID" "PUT" "$LAMBDA_PROMPT"
add_cors "$PROMPT_ITEM_ID" "GET,POST,PUT,OPTIONS"

# /prompts/{promptId}/files
FILES_ID=$(get_or_create_resource "$PROMPT_ITEM_ID" "files")
add_method "$FILES_ID" "GET" "$LAMBDA_PROMPT"
add_method "$FILES_ID" "POST" "$LAMBDA_PROMPT"
add_cors "$FILES_ID" "GET,POST,OPTIONS"

# /prompts/{promptId}/files/{fileId}
FILE_ITEM_ID=$(get_or_create_resource "$FILES_ID" "{fileId}")
add_method "$FILE_ITEM_ID" "GET" "$LAMBDA_PROMPT"
add_method "$FILE_ITEM_ID" "PUT" "$LAMBDA_PROMPT"
add_method "$FILE_ITEM_ID" "DELETE" "$LAMBDA_PROMPT"
add_cors "$FILE_ITEM_ID" "GET,PUT,DELETE,OPTIONS"

# =============================================
# 3. /usage 리소스 구조
# =============================================
log_info "Usage API 구조 설정..."

USAGE_ID=$(get_or_create_resource "$ROOT_ID" "usage")
add_method "$USAGE_ID" "GET" "$LAMBDA_USAGE"
add_method "$USAGE_ID" "POST" "$LAMBDA_USAGE"
add_cors "$USAGE_ID" "GET,POST,OPTIONS"

# /usage/{userId}
USER_ID=$(get_or_create_resource "$USAGE_ID" "{userId}")

# /usage/{userId}/{engineType}
ENGINE_ID=$(get_or_create_resource "$USER_ID" "{engineType}")
add_method "$ENGINE_ID" "GET" "$LAMBDA_USAGE"
add_method "$ENGINE_ID" "POST" "$LAMBDA_USAGE"
add_cors "$ENGINE_ID" "GET,POST,OPTIONS"

# =============================================
# API 배포
# =============================================
log_info "API 배포 중..."

aws apigateway create-deployment \
    --rest-api-id "$API_ID" \
    --stage-name prod \
    --description "Enhanced deployment with full CORS support" \
    --region "$REGION" >/dev/null

log_success "Enhanced REST API 배포 완료!"

# 엔드포인트 저장
echo "REST_API_ENDPOINT=https://$API_ID.execute-api.$REGION.amazonaws.com/prod" >> "$PROJECT_ROOT/endpoints.txt"

log_info "REST API 엔드포인트: https://$API_ID.execute-api.$REGION.amazonaws.com/prod"
log_info "API ID 저장: $API_ID"

# Lambda 권한 추가 (API Gateway 호출 허용)
log_info "Lambda 권한 설정 중..."

for FUNC in "$LAMBDA_PROMPT" "$LAMBDA_CONVERSATION" "$LAMBDA_USAGE"; do
    aws lambda add-permission \
        --function-name "$FUNC" \
        --statement-id "apigateway-$API_ID-$(date +%s)" \
        --action lambda:InvokeFunction \
        --principal apigateway.amazonaws.com \
        --source-arn "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*/*/*" \
        --region "$REGION" >/dev/null 2>&1 || true
done

log_success "모든 REST API 설정 완료!"