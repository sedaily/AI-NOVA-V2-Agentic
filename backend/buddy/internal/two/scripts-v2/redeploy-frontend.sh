#!/bin/bash

# ===================================================
# f2 Frontend 재배포 스크립트
# ===================================================
# API 엔드포인트 변경이나 코드 수정 후
# Frontend를 빠르게 재배포하기 위한 스크립트
# ===================================================

set -e

# 색상 설정
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 현재 시간 (한국 시간)
TIMESTAMP=$(TZ='Asia/Seoul' date '+%Y년 %m월 %d일 %H시 %M분 %S초 KST')

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}f2 Frontend 재배포 스크립트${NC}"
echo -e "${BLUE}실행 시간: ${TIMESTAMP}${NC}"
echo -e "${BLUE}========================================${NC}"

# 설정 변수
SERVICE_NAME="f2-two"
REGION="us-east-1"
S3_BUCKET="${SERVICE_NAME}-frontend"
FRONTEND_DIR="../frontend"

# 스크립트 실행 위치 확인
if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}❌ Frontend 디렉토리를 찾을 수 없습니다: ${FRONTEND_DIR}${NC}"
    echo -e "${YELLOW}scripts-v2 디렉토리에서 실행해주세요.${NC}"
    exit 1
fi

# 환경 변수 확인
echo -e "\n${YELLOW}1. 환경 변수 확인 중...${NC}"

if [ -f "$FRONTEND_DIR/.env.production" ]; then
    echo -e "${GREEN}✓ .env.production 파일 확인${NC}"
    echo -e "${BLUE}현재 설정:${NC}"
    grep "VITE_API_BASE_URL\|VITE_WS_URL\|VITE_APP_TITLE" $FRONTEND_DIR/.env.production | head -3
else
    echo -e "${RED}❌ .env.production 파일이 없습니다${NC}"
    exit 1
fi

# API 엔드포인트 확인
echo -e "\n${YELLOW}2. API Gateway 상태 확인 중...${NC}"

REST_API_ID=$(aws apigateway get-rest-apis --query "items[?name=='${SERVICE_NAME}-api'].id" --output text 2>/dev/null || echo "")
WS_API_ID=$(aws apigatewayv2 get-apis --query "Items[?Name=='${SERVICE_NAME}-websocket'].ApiId" --output text 2>/dev/null || echo "")

if [ -n "$REST_API_ID" ]; then
    echo -e "${GREEN}✓ REST API: https://${REST_API_ID}.execute-api.${REGION}.amazonaws.com/prod${NC}"
else
    echo -e "${YELLOW}⚠ REST API를 찾을 수 없습니다${NC}"
fi

if [ -n "$WS_API_ID" ]; then
    echo -e "${GREEN}✓ WebSocket: wss://${WS_API_ID}.execute-api.${REGION}.amazonaws.com/prod${NC}"
else
    echo -e "${YELLOW}⚠ WebSocket API를 찾을 수 없습니다${NC}"
fi

# 환경 변수 업데이트 확인
if [ -n "$REST_API_ID" ] && [ -n "$WS_API_ID" ]; then
    echo -e "\n${YELLOW}환경 변수를 최신 API 엔드포인트로 업데이트하시겠습니까? (y/n)${NC}"
    read -r UPDATE_ENV

    if [ "$UPDATE_ENV" = "y" ]; then
        # .env 업데이트
        if [ -f "$FRONTEND_DIR/.env" ]; then
            cp $FRONTEND_DIR/.env $FRONTEND_DIR/.env.backup
            sed -i.bak "s|VITE_API_BASE_URL=.*|VITE_API_BASE_URL=https://${REST_API_ID}.execute-api.${REGION}.amazonaws.com/prod|" $FRONTEND_DIR/.env
            sed -i.bak "s|VITE_WS_URL=.*|VITE_WS_URL=wss://${WS_API_ID}.execute-api.${REGION}.amazonaws.com/prod|" $FRONTEND_DIR/.env

            # 모든 API URL 관련 변수 업데이트
            sed -i.bak "s|VITE_API_URL=.*|VITE_API_URL=https://${REST_API_ID}.execute-api.${REGION}.amazonaws.com/prod|" $FRONTEND_DIR/.env
            sed -i.bak "s|VITE_PROMPT_API_URL=.*|VITE_PROMPT_API_URL=https://${REST_API_ID}.execute-api.${REGION}.amazonaws.com/prod|" $FRONTEND_DIR/.env
            sed -i.bak "s|VITE_WEBSOCKET_URL=.*|VITE_WEBSOCKET_URL=wss://${WS_API_ID}.execute-api.${REGION}.amazonaws.com/prod|" $FRONTEND_DIR/.env
            sed -i.bak "s|VITE_USAGE_API_URL=.*|VITE_USAGE_API_URL=https://${REST_API_ID}.execute-api.${REGION}.amazonaws.com/prod|" $FRONTEND_DIR/.env
            sed -i.bak "s|VITE_CONVERSATION_API_URL=.*|VITE_CONVERSATION_API_URL=https://${REST_API_ID}.execute-api.${REGION}.amazonaws.com/prod|" $FRONTEND_DIR/.env

            echo -e "${GREEN}✓ .env 업데이트 완료${NC}"
        fi

        # .env.production 업데이트
        if [ -f "$FRONTEND_DIR/.env.production" ]; then
            cp $FRONTEND_DIR/.env.production $FRONTEND_DIR/.env.production.backup
            sed -i.bak "s|VITE_API_BASE_URL=.*|VITE_API_BASE_URL=https://${REST_API_ID}.execute-api.${REGION}.amazonaws.com/prod|" $FRONTEND_DIR/.env.production
            sed -i.bak "s|VITE_WS_URL=.*|VITE_WS_URL=wss://${WS_API_ID}.execute-api.${REGION}.amazonaws.com/prod|" $FRONTEND_DIR/.env.production
            echo -e "${GREEN}✓ .env.production 업데이트 완료${NC}"
        fi
    fi
fi

# Frontend 빌드
echo -e "\n${YELLOW}3. Frontend 빌드 중...${NC}"

cd $FRONTEND_DIR

# 이전 빌드 삭제
if [ -d "dist" ]; then
    rm -rf dist
    echo -e "${GREEN}✓ 이전 빌드 제거 완료${NC}"
fi

# npm 빌드
npm run build

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 빌드 성공${NC}"
else
    echo -e "${RED}❌ 빌드 실패${NC}"
    exit 1
fi

# S3 업로드
echo -e "\n${YELLOW}4. S3에 업로드 중...${NC}"

# S3 버킷 존재 확인
S3_EXISTS=$(aws s3 ls s3://${S3_BUCKET} 2>/dev/null || echo "")

if [ -z "$S3_EXISTS" ]; then
    echo -e "${RED}❌ S3 버킷을 찾을 수 없습니다: ${S3_BUCKET}${NC}"
    exit 1
fi

# 파일 업로드
aws s3 sync dist/ s3://${S3_BUCKET} --delete \
    --cache-control "public, max-age=31536000" \
    --exclude "index.html" \
    --exclude "*.json"

# index.html과 JSON 파일은 캐시하지 않음
aws s3 cp dist/index.html s3://${S3_BUCKET}/index.html \
    --cache-control "no-cache, no-store, must-revalidate" \
    --content-type "text/html"

aws s3 sync dist/ s3://${S3_BUCKET} \
    --exclude "*" \
    --include "*.json" \
    --cache-control "no-cache, no-store, must-revalidate"

echo -e "${GREEN}✓ S3 업로드 완료${NC}"

# CloudFront 캐시 무효화
echo -e "\n${YELLOW}5. CloudFront 캐시 무효화 중...${NC}"

# CloudFront Distribution ID 찾기
CF_DIST_ID=$(aws cloudfront list-distributions \
    --query "DistributionList.Items[?contains(Comment,'${SERVICE_NAME}')].Id" \
    --output text 2>/dev/null | head -1)

if [ -n "$CF_DIST_ID" ]; then
    INVALIDATION_ID=$(aws cloudfront create-invalidation \
        --distribution-id $CF_DIST_ID \
        --paths "/*" \
        --query "Invalidation.Id" \
        --output text)

    echo -e "${GREEN}✓ CloudFront 캐시 무효화 시작 (ID: ${INVALIDATION_ID})${NC}"

    # CloudFront URL 가져오기
    CF_DOMAIN=$(aws cloudfront get-distribution \
        --id $CF_DIST_ID \
        --query "Distribution.DomainName" \
        --output text)

    echo -e "${BLUE}CloudFront URL: https://${CF_DOMAIN}${NC}"
else
    echo -e "${YELLOW}⚠ CloudFront 배포를 찾을 수 없습니다${NC}"
fi

# 배포 정보 저장
echo -e "\n${YELLOW}6. 배포 정보 저장 중...${NC}"

cat > deployment-log.txt << EOF
========================================
Frontend 재배포 완료
========================================
배포 시간: ${TIMESTAMP}
서비스: ${SERVICE_NAME}

S3 버킷: ${S3_BUCKET}
CloudFront ID: ${CF_DIST_ID:-"N/A"}
CloudFront URL: https://${CF_DOMAIN:-"N/A"}

API 엔드포인트:
- REST API: https://${REST_API_ID}.execute-api.${REGION}.amazonaws.com/prod
- WebSocket: wss://${WS_API_ID}.execute-api.${REGION}.amazonaws.com/prod

캐시 무효화 ID: ${INVALIDATION_ID:-"N/A"}
========================================
EOF

echo -e "${GREEN}"
cat deployment-log.txt
echo -e "${NC}"

# 빌드 크기 정보
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}빌드 크기 정보${NC}"
echo -e "${BLUE}========================================${NC}"
du -sh dist/* | sort -h | tail -10

# 완료 메시지
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Frontend 재배포 완료!${NC}"
echo -e "${GREEN}========================================${NC}"

if [ -n "$CF_DOMAIN" ]; then
    echo -e "${YELLOW}CloudFront 캐시 무효화는 5-10분 정도 소요됩니다.${NC}"
    echo -e "${BLUE}접속 URL: https://${CF_DOMAIN}${NC}"
fi

# CORS 테스트 제안
echo -e "\n${YELLOW}CORS 동작 확인을 위해 다음 명령을 실행해보세요:${NC}"
echo -e "${BLUE}curl -X OPTIONS https://${REST_API_ID}.execute-api.${REGION}.amazonaws.com/prod/prompts -v${NC}"