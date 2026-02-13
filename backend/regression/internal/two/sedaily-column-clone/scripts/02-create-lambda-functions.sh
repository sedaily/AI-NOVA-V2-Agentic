#!/bin/bash

# Lambda 함수 및 IAM 역할 생성

source "$(dirname "$0")/00-config.sh"

log_info "Lambda 함수 생성 시작..."

# IAM 역할 생성
create_iam_role() {
    log_info "IAM 역할 생성 중..."

    # 역할이 이미 있는지 확인
    if aws iam get-role --role-name "$IAM_ROLE" --region "$REGION" >/dev/null 2>&1; then
        log_warning "IAM 역할이 이미 존재합니다: $IAM_ROLE"
        return 0
    fi

    # Trust Policy 생성
    cat > /tmp/trust-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

    # 역할 생성
    aws iam create-role \
        --role-name "$IAM_ROLE" \
        --assume-role-policy-document file:///tmp/trust-policy.json \
        --region "$REGION" >/dev/null

    # 기본 실행 정책 연결
    aws iam attach-role-policy \
        --role-name "$IAM_ROLE" \
        --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole" \
        --region "$REGION"

    # Bedrock 접근 정책 연결
    aws iam attach-role-policy \
        --role-name "$IAM_ROLE" \
        --policy-arn "arn:aws:iam::aws:policy/AmazonBedrockFullAccess" \
        --region "$REGION"

    # DynamoDB 정책 생성
    cat > /tmp/dynamodb-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:PutItem",
                "dynamodb:GetItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem",
                "dynamodb:Query",
                "dynamodb:Scan"
            ],
            "Resource": [
                "arn:aws:dynamodb:$REGION:$ACCOUNT_ID:table/${SERVICE_NAME}-*"
            ]
        }
    ]
}
EOF

    aws iam put-role-policy \
        --role-name "$IAM_ROLE" \
        --policy-name "DynamoDBAccess" \
        --policy-document file:///tmp/dynamodb-policy.json \
        --region "$REGION"

    # API Gateway 관리 정책
    cat > /tmp/apigateway-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "execute-api:ManageConnections",
                "execute-api:Invoke"
            ],
            "Resource": "*"
        }
    ]
}
EOF

    aws iam put-role-policy \
        --role-name "$IAM_ROLE" \
        --policy-name "APIGatewayAccess" \
        --policy-document file:///tmp/apigateway-policy.json \
        --region "$REGION"

    log_success "IAM 역할 생성 완료: $IAM_ROLE"

    # 역할이 사용 가능해질 때까지 대기
    sleep 10
}

# Lambda 함수 생성
create_lambda_function() {
    local function_name=$1
    local handler=$2
    local description=$3

    if aws lambda get-function --function-name "$function_name" --region "$REGION" >/dev/null 2>&1; then
        log_warning "$function_name 함수가 이미 존재합니다"
        return 0
    fi

    log_info "$function_name 함수 생성 중..."

    # 초기 코드 ZIP 파일 생성
    echo "def handler(event, context): return {'statusCode': 200}" > /tmp/lambda_function.py
    cd /tmp && zip lambda_function.zip lambda_function.py >/dev/null

    aws lambda create-function \
        --function-name "$function_name" \
        --runtime python3.9 \
        --role "arn:aws:iam::$ACCOUNT_ID:role/$IAM_ROLE" \
        --handler "$handler" \
        --description "$description" \
        --timeout 120 \
        --memory-size 1024 \
        --zip-file fileb:///tmp/lambda_function.zip \
        --environment "Variables={
            PROMPTS_TABLE=$TABLE_PROMPTS,
            CONVERSATIONS_TABLE=$TABLE_CONVERSATIONS,
            USAGE_TABLE=$TABLE_USAGE,
            CONNECTIONS_TABLE=$TABLE_CONNECTIONS,
            WEBSOCKET_TABLE=$TABLE_CONNECTIONS,
            ENABLE_NEWS_SEARCH=true
        }" \
        --region "$REGION" >/dev/null

    if [ $? -eq 0 ]; then
        log_success "$function_name 함수 생성 완료"
    else
        log_error "$function_name 함수 생성 실패"
        return 1
    fi
}

# IAM 역할 생성
create_iam_role

# Lambda 함수들 생성
create_lambda_function "$LAMBDA_CONNECT" "handlers.websocket.connect.handler" "WebSocket 연결 처리"
create_lambda_function "$LAMBDA_DISCONNECT" "handlers.websocket.disconnect.handler" "WebSocket 연결 해제 처리"
create_lambda_function "$LAMBDA_MESSAGE" "handlers.websocket.message.handler" "WebSocket 메시지 처리"
create_lambda_function "$LAMBDA_CONVERSATION" "handlers.api.conversation.handler" "대화 관리 API"
create_lambda_function "$LAMBDA_PROMPT" "handlers.api.prompt.handler" "프롬프트 관리 API"
create_lambda_function "$LAMBDA_USAGE" "handlers.api.usage.handler" "사용량 관리 API"

log_success "모든 Lambda 함수 생성 완료!"