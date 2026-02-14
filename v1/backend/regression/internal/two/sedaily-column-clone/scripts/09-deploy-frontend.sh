#!/bin/bash

# 프론트엔드 빌드 및 배포

source "$(dirname "$0")/00-config.sh"

log_info "프론트엔드 빌드 및 배포 시작..."

# API 엔드포인트 가져오기
REST_API_ID=$(aws apigateway get-rest-apis \
    --query "items[?name=='$REST_API_NAME'].id" \
    --output text --region "$REGION")

WS_API_ID=$(aws apigatewayv2 get-apis \
    --query "Items[?Name=='$WEBSOCKET_API_NAME'].ApiId" \
    --output text --region "$REGION")

CF_DOMAIN=$(grep "CLOUDFRONT_DOMAIN" "$PROJECT_ROOT/endpoints.txt" | cut -d'=' -f2)
CF_DISTRIBUTION_ID=$(grep "CLOUDFRONT_DISTRIBUTION_ID" "$PROJECT_ROOT/endpoints.txt" | cut -d'=' -f2)

# 프론트엔드 디렉토리로 이동
cd "$FRONTEND_DIR"

# .env 파일 생성
log_info "환경변수 파일 생성 중..."

cat > .env.production <<EOF
# API 엔드포인트
VITE_API_BASE_URL=https://${REST_API_ID}.execute-api.${REGION}.amazonaws.com/prod
VITE_WS_URL=wss://${WS_API_ID}.execute-api.${REGION}.amazonaws.com/prod

# 서비스 설정
VITE_APP_TITLE=${SERVICE_NAME}
VITE_APP_DESCRIPTION="AI 콘텐츠 생성 서비스"

# 기타 설정
VITE_ENABLE_NEWS_SEARCH=true
VITE_ENV=production
EOF

log_success "환경변수 파일 생성 완료"

# 종속성 설치
log_info "NPM 패키지 설치 중..."
npm install --silent

if [ $? -ne 0 ]; then
    log_error "NPM 패키지 설치 실패"
    exit 1
fi

# 프론트엔드 빌드
log_info "프론트엔드 빌드 중..."
npm run build

if [ $? -ne 0 ]; then
    log_error "프론트엔드 빌드 실패"
    exit 1
fi

log_success "프론트엔드 빌드 완료"

# S3로 배포
log_info "S3로 파일 업로드 중..."

# 기존 파일 삭제
aws s3 rm "s3://$S3_BUCKET" --recursive --region "$REGION" >/dev/null 2>&1

# 새 파일 업로드
aws s3 sync dist/ "s3://$S3_BUCKET" \
    --delete \
    --cache-control "public, max-age=31536000" \
    --exclude "index.html" \
    --region "$REGION"

# index.html은 캐싱 안함
aws s3 cp dist/index.html "s3://$S3_BUCKET/index.html" \
    --cache-control "no-cache, no-store, must-revalidate" \
    --content-type "text/html" \
    --region "$REGION"

log_success "S3 업로드 완료"

# CloudFront 캐시 무효화
if [ ! -z "$CF_DISTRIBUTION_ID" ]; then
    log_info "CloudFront 캐시 무효화 중..."
    
    aws cloudfront create-invalidation \
        --distribution-id "$CF_DISTRIBUTION_ID" \
        --paths "/*" \
        --region "$REGION" >/dev/null
    
    log_success "CloudFront 캐시 무효화 요청 완료"
fi

log_success "프론트엔드 배포 완료!"
log_info "접속 URL: https://$CF_DOMAIN"