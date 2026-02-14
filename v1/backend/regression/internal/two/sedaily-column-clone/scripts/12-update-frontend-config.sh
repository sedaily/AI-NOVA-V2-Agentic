#!/bin/bash

# 프론트엔드 설정 자동 업데이트 스크립트
# 마스킹된 **** 부분을 실제 서비스명과 AWS 리소스로 교체

source "$(dirname "$0")/00-config.sh"

log_info "프론트엔드 설정 업데이트 시작..."

# 엔진 타입 설정 (백엔드와 동일하게)
if [ -t 0 ]; then
    read -p "기본 엔진 타입 입력 [기본: 11]: " engine_type
    ENGINE_TYPE="${engine_type:-11}"
    read -p "보조 엔진 타입 입력 [기본: 22]: " engine_type2
    ENGINE_TYPE2="${engine_type2:-22}"
else
    ENGINE_TYPE="11"
    ENGINE_TYPE2="22"
fi

log_info "서비스명: $SERVICE_NAME"
log_info "엔진 타입: $ENGINE_TYPE, $ENGINE_TYPE2"

# AWS 리소스 ID 가져오기
REST_API_ID=$(aws apigateway get-rest-apis \
    --query "items[?name=='$REST_API_NAME'].id" \
    --output text --region "$REGION")

WS_API_ID=$(aws apigatewayv2 get-apis \
    --query "Items[?Name=='$WEBSOCKET_API_NAME'].ApiId" \
    --output text --region "$REGION")

log_info "REST API ID: $REST_API_ID"
log_info "WebSocket API ID: $WS_API_ID"

# config.js 업데이트
CONFIG_FILE="$FRONTEND_DIR/src/config.js"
if [ -f "$CONFIG_FILE" ]; then
    log_info "config.js 업데이트 중..."
    
    # API URL 교체
    sed -i '' "s|https://\*\*\*\*\*\*.execute-api.us-east-1.amazonaws.com/prod|https://${REST_API_ID}.execute-api.${REGION}.amazonaws.com/prod|g" "$CONFIG_FILE"
    sed -i '' "s|wss://\*\*\*\*\*\*.execute-api.us-east-1.amazonaws.com/prod|wss://${WS_API_ID}.execute-api.${REGION}.amazonaws.com/prod|g" "$CONFIG_FILE"
    
    # 엔진 타입 및 STORAGE_PREFIX 교체
    sed -i '' "s|DEFAULT_ENGINE = '\*\*\*\*'|DEFAULT_ENGINE = '${ENGINE_TYPE}'|g" "$CONFIG_FILE"
    sed -i '' "s|STORAGE_PREFIX = '\*\*\*\*_'|STORAGE_PREFIX = '${SERVICE_NAME}_'|g" "$CONFIG_FILE"
    
    log_success "config.js 업데이트 완료"
fi

# config.column.js 업데이트 (있는 경우)
COLUMN_CONFIG="$FRONTEND_DIR/src/config.column.js"
if [ -f "$COLUMN_CONFIG" ]; then
    log_info "config.column.js 업데이트 중..."
    
    # C1, C2, C3를 새 엔진 타입으로 교체
    sed -i '' "s/C1/${ENGINE_TYPE}/g" "$COLUMN_CONFIG"
    sed -i '' "s/C2/${ENGINE_TYPE2}/g" "$COLUMN_CONFIG"
    sed -i '' "s/C3/33/g" "$COLUMN_CONFIG"  # C3가 있다면 33으로
    
    log_success "config.column.js 업데이트 완료"
fi

# App.jsx 업데이트
APP_FILE="$FRONTEND_DIR/src/App.jsx"
if [ -f "$APP_FILE" ]; then
    log_info "App.jsx 업데이트 중..."
    
    # URL 경로에서 c1, c2 -> 새 엔진 타입으로
    sed -i '' "s|/c1|/${ENGINE_TYPE}|g" "$APP_FILE"
    sed -i '' "s|/c2|/${ENGINE_TYPE2}|g" "$APP_FILE"
    sed -i '' "s|'C1'|'${ENGINE_TYPE}'|g" "$APP_FILE"
    sed -i '' "s|'C2'|'${ENGINE_TYPE2}'|g" "$APP_FILE"
    sed -i '' "s|\"C1\"|\"${ENGINE_TYPE}\"|g" "$APP_FILE"
    sed -i '' "s|\"C2\"|\"${ENGINE_TYPE2}\"|g" "$APP_FILE"
    
    log_success "App.jsx 업데이트 완료"
fi

# 모든 컴포넌트에서 C1, C2, C7 교체
log_info "컴포넌트 파일들 업데이트 중..."

# src 디렉토리의 모든 .js, .jsx 파일에서 교체
find "$FRONTEND_DIR/src" -type f \( -name "*.js" -o -name "*.jsx" \) | while read file; do
    # C1, C2, C7을 새 엔진 타입으로 교체
    sed -i '' "s/'C1'/'${ENGINE_TYPE}'/g" "$file"
    sed -i '' "s/'C2'/'${ENGINE_TYPE2}'/g" "$file"
    sed -i '' "s/'C7'/'${ENGINE_TYPE}'/g" "$file"
    sed -i '' "s/\"C1\"/\"${ENGINE_TYPE}\"/g" "$file"
    sed -i '' "s/\"C2\"/\"${ENGINE_TYPE2}\"/g" "$file"
    sed -i '' "s/\"C7\"/\"${ENGINE_TYPE}\"/g" "$file"
    sed -i '' "s/C1:/${ENGINE_TYPE}:/g" "$file"
    sed -i '' "s/C2:/${ENGINE_TYPE2}:/g" "$file"
    sed -i '' "s/C7:/${ENGINE_TYPE}:/g" "$file"
done

log_success "컴포넌트 파일들 업데이트 완료"

# .env.production 파일 업데이트
ENV_FILE="$FRONTEND_DIR/.env.production"
log_info "프론트엔드 .env.production 파일 생성 중..."

cat > "$ENV_FILE" <<EOF
# API 엔드포인트
VITE_API_BASE_URL=https://${REST_API_ID}.execute-api.${REGION}.amazonaws.com/prod
VITE_WS_URL=wss://${WS_API_ID}.execute-api.${REGION}.amazonaws.com/prod

# 서비스 설정
VITE_APP_TITLE=${SERVICE_NAME}
VITE_APP_DESCRIPTION="AI 콘텐츠 생성 서비스"

# 기타 설정
VITE_ENABLE_NEWS_SEARCH=true
VITE_ENV=production
VITE_DEFAULT_ENGINE=${ENGINE_TYPE}
EOF

log_success ".env.production 파일 생성 완료"

log_success "프론트엔드 설정 업데이트 완료!"
echo ""
log_info "📋 업데이트된 설정:"
log_info "  • 서비스명: $SERVICE_NAME"
log_info "  • 엔진 타입: $ENGINE_TYPE, $ENGINE_TYPE2"
log_info "  • REST API: https://${REST_API_ID}.execute-api.${REGION}.amazonaws.com/prod"
log_info "  • WebSocket: wss://${WS_API_ID}.execute-api.${REGION}.amazonaws.com/prod"
echo ""
log_warning "🔄 프론트엔드를 다시 빌드하고 배포하려면 다음 명령을 실행하세요:"
log_info "bash scripts/09-deploy-frontend.sh $SERVICE_NAME $REGION"