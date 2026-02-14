#!/bin/bash

# 백엔드 설정 자동 업데이트 스크립트
# 마스킹된 **** 부분을 실제 서비스명과 AWS 리소스로 교체

source "$(dirname "$0")/00-config.sh"

log_info "백엔드 설정 업데이트 시작..."

# 엔진 타입 설정 (사용자 입력 받기 또는 기본값 사용)
log_info "엔진 타입 설정"
if [ -t 0 ]; then
    # 대화형 모드
    read -p "기본 엔진 타입 입력 [기본: 11]: " engine_type
    ENGINE_TYPE="${engine_type:-11}"
    read -p "보조 엔진 타입 입력 [기본: 22]: " engine_type2
    ENGINE_TYPE2="${engine_type2:-22}"
else
    # 비대화형 모드 (기본값 사용)
    ENGINE_TYPE="11"
    ENGINE_TYPE2="22"
fi

log_info "서비스명: $SERVICE_NAME"
log_info "엔진 타입: $ENGINE_TYPE, $ENGINE_TYPE2"

# Python 파일들 업데이트
log_info "Python 파일들 업데이트 중..."

# database.py 업데이트
DATABASE_FILE="$BACKEND_DIR/src/config/database.py"
if [ -f "$DATABASE_FILE" ]; then
    sed -i '' "s/'\*\*\*\*-conversations'/'${SERVICE_NAME}-conversations-v2'/g" "$DATABASE_FILE"
    sed -i '' "s/'\*\*\*\*-prompts'/'${SERVICE_NAME}-prompts-v2'/g" "$DATABASE_FILE"
    sed -i '' "s/'\*\*\*\*-usage'/'${SERVICE_NAME}-usage'/g" "$DATABASE_FILE"
    sed -i '' "s/'\*\*\*\*-websocket-connections'/'${SERVICE_NAME}-websocket-connections'/g" "$DATABASE_FILE"
    sed -i '' "s/'\*\*\*\*-files'/'${SERVICE_NAME}-files'/g" "$DATABASE_FILE"
    log_success "database.py 업데이트 완료"
fi

# aws.py 업데이트
AWS_FILE="$BACKEND_DIR/src/config/aws.py"
if [ -f "$AWS_FILE" ]; then
    # CloudWatch namespace를 서비스명으로
    SERVICE_NAME_CAMEL="$(echo $SERVICE_NAME | sed 's/-//g' | sed 's/\b\(\w\)/\u\1/g')"
    sed -i '' "s/'\*\*\*\*'/'${SERVICE_NAME_CAMEL}'/g" "$AWS_FILE"
    sed -i '' "s|'/aws/lambda/\*\*\*\*'|'/aws/lambda/${SERVICE_NAME}'|g" "$AWS_FILE"
    log_success "aws.py 업데이트 완료"
fi

# Repository 파일들 업데이트
for repo_file in conversation_repository.py usage_repository.py prompt_repository.py; do
    REPO_PATH="$BACKEND_DIR/src/repositories/$repo_file"
    if [ -f "$REPO_PATH" ]; then
        sed -i '' "s/'\*\*\*\*-conversations'/'${SERVICE_NAME}-conversations-v2'/g" "$REPO_PATH"
        sed -i '' "s/'\*\*\*\*-prompts'/'${SERVICE_NAME}-prompts-v2'/g" "$REPO_PATH"
        sed -i '' "s/'\*\*\*\*-usage'/'${SERVICE_NAME}-usage'/g" "$REPO_PATH"
        sed -i '' "s/'\*\*\*\*-files'/'${SERVICE_NAME}-files'/g" "$REPO_PATH"
        log_success "$repo_file 업데이트 완료"
    fi
done

# websocket_service.py 업데이트
WS_SERVICE_FILE="$BACKEND_DIR/services/websocket_service.py"
if [ -f "$WS_SERVICE_FILE" ]; then
    sed -i '' "s/'\*\*\*\*-prompts'/'${SERVICE_NAME}-prompts-v2'/g" "$WS_SERVICE_FILE"
    sed -i '' "s/'\*\*\*\*-files'/'${SERVICE_NAME}-files'/g" "$WS_SERVICE_FILE"
    log_success "websocket_service.py 업데이트 완료"
fi

# Handler 파일들 업데이트
HANDLER_FILES=(
    "handlers/api/usage.py"
    "handlers/api/prompt.py"
    "handlers/api/conversation.py"
    "handlers/websocket/connect.py"
    "handlers/websocket/message.py"
    "handlers/websocket/conversation_manager.py"
)

for handler_file in "${HANDLER_FILES[@]}"; do
    HANDLER_PATH="$BACKEND_DIR/$handler_file"
    if [ -f "$HANDLER_PATH" ]; then
        # 테이블명 교체
        sed -i '' "s/'\*\*\*\*-conversations'/'${SERVICE_NAME}-conversations-v2'/g" "$HANDLER_PATH"
        sed -i '' "s/'\*\*\*\*-prompts'/'${SERVICE_NAME}-prompts-v2'/g" "$HANDLER_PATH"
        sed -i '' "s/'\*\*\*\*-usage'/'${SERVICE_NAME}-usage'/g" "$HANDLER_PATH"
        sed -i '' "s/'\*\*\*\*-websocket-connections'/'${SERVICE_NAME}-websocket-connections'/g" "$HANDLER_PATH"
        sed -i '' "s/'\*\*\*\*-files'/'${SERVICE_NAME}-files'/g" "$HANDLER_PATH"
        
        # 엔진 타입 교체
        sed -i '' "s/'\*\*\*\*'/'${ENGINE_TYPE}'/g" "$HANDLER_PATH"
        
        log_success "$(basename $handler_file) 업데이트 완료"
    fi
done

# usage_service.py 특별 처리 (엔진 타입 매핑)
USAGE_SERVICE_FILE="$BACKEND_DIR/src/services/usage_service.py"
if [ -f "$USAGE_SERVICE_FILE" ]; then
    sed -i '' "s/'\*\*\*\*'/'${ENGINE_TYPE}'/g" "$USAGE_SERVICE_FILE"
    sed -i '' "s/'\*\*\*\*2'/'${ENGINE_TYPE2}'/g" "$USAGE_SERVICE_FILE"
    log_success "usage_service.py 업데이트 완료"
fi

# deploy-fixed.sh 업데이트
DEPLOY_SCRIPT="$BACKEND_DIR/deploy-fixed.sh"
if [ -f "$DEPLOY_SCRIPT" ]; then
    sed -i '' "s/\*\*\*\* LAMBDA DEPLOYMENT/${SERVICE_NAME^^} LAMBDA DEPLOYMENT/g" "$DEPLOY_SCRIPT"
    sed -i '' "s/\"\*\*\*\*-websocket-connect\"/\"${LAMBDA_CONNECT}\"/g" "$DEPLOY_SCRIPT"
    sed -i '' "s/\"\*\*\*\*-websocket-disconnect\"/\"${LAMBDA_DISCONNECT}\"/g" "$DEPLOY_SCRIPT"
    sed -i '' "s/\"\*\*\*\*-websocket-message\"/\"${LAMBDA_MESSAGE}\"/g" "$DEPLOY_SCRIPT"
    sed -i '' "s/\"\*\*\*\*-conversation-api\"/\"${LAMBDA_CONVERSATION}\"/g" "$DEPLOY_SCRIPT"
    sed -i '' "s/\"\*\*\*\*-prompt-crud\"/\"${LAMBDA_PROMPT}\"/g" "$DEPLOY_SCRIPT"
    sed -i '' "s/\"\*\*\*\*-usage-handler\"/\"${LAMBDA_USAGE}\"/g" "$DEPLOY_SCRIPT"
    log_success "deploy-fixed.sh 업데이트 완료"
fi

# .env 파일 생성 (백엔드용)
log_info "백엔드 .env 파일 생성 중..."

# AWS 리소스 ID 가져오기
REST_API_ID=$(aws apigateway get-rest-apis \
    --query "items[?name=='$REST_API_NAME'].id" \
    --output text --region "$REGION")

WS_API_ID=$(aws apigatewayv2 get-apis \
    --query "Items[?Name=='$WEBSOCKET_API_NAME'].ApiId" \
    --output text --region "$REGION")

cat > "$BACKEND_DIR/.env" <<EOF
# AWS 설정
AWS_REGION=$REGION
AWS_ACCOUNT_ID=$ACCOUNT_ID

# DynamoDB 테이블
CONVERSATIONS_TABLE=$TABLE_CONVERSATIONS
PROMPTS_TABLE=$TABLE_PROMPTS
USAGE_TABLE=$TABLE_USAGE
WEBSOCKET_TABLE=$TABLE_CONNECTIONS
CONNECTIONS_TABLE=$TABLE_CONNECTIONS
FILES_TABLE=${SERVICE_NAME}-files

# API Gateway
REST_API_URL=https://${REST_API_ID}.execute-api.${REGION}.amazonaws.com/prod
WEBSOCKET_API_URL=wss://${WS_API_ID}.execute-api.${REGION}.amazonaws.com/prod
WEBSOCKET_API_ID=$WS_API_ID
API_STAGE=prod

# Lambda 설정
LAMBDA_TIMEOUT=120
LAMBDA_MEMORY=1024
LOG_LEVEL=INFO

# Bedrock 설정
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
BEDROCK_MAX_TOKENS=16384
BEDROCK_TEMPERATURE=0.81
BEDROCK_TOP_P=0.9
BEDROCK_TOP_K=50

# 가드레일 설정
GUARDRAIL_ID=ycwjnmzxut7k
GUARDRAIL_VERSION=1
GUARDRAIL_ENABLED=true

# CloudWatch
CLOUDWATCH_NAMESPACE=${SERVICE_NAME_CAMEL}
LOG_GROUP=/aws/lambda/${SERVICE_NAME}
METRICS_ENABLED=true

# 뉴스 검색 활성화
ENABLE_NEWS_SEARCH=true

# 엔진 타입
DEFAULT_ENGINE_TYPE=$ENGINE_TYPE
SECONDARY_ENGINE_TYPE=$ENGINE_TYPE2
EOF

log_success "백엔드 .env 파일 생성 완료"

log_success "백엔드 설정 업데이트 완료!"
echo ""
log_info "📋 업데이트된 설정:"
log_info "  • 서비스명: $SERVICE_NAME"
log_info "  • 엔진 타입: $ENGINE_TYPE, $ENGINE_TYPE2"
log_info "  • DynamoDB 테이블: ${SERVICE_NAME}-*"
log_info "  • Lambda 함수: ${SERVICE_NAME}-*"
log_info "  • REST API: $REST_API_ID"
log_info "  • WebSocket API: $WS_API_ID"
echo ""
log_warning "🔄 Lambda 코드를 재배포하려면 다음 명령을 실행하세요:"
log_info "bash scripts/06-deploy-lambda-code.sh $SERVICE_NAME $REGION"