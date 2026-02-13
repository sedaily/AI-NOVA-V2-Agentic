#!/bin/bash

# ============================================
# 서비스 배포 마스터 스크립트
# ============================================
# 사용법: ./deploy-service.sh [서비스접두사] [인스턴스번호]
# 예시: ./deploy-service.sh g 2  → g2 서비스 생성
#      ./deploy-service.sh tt 1 → tt1 서비스 생성
#      ./deploy-service.sh prf 3 → prf3 서비스 생성
# ============================================

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 파라미터 처리
SERVICE_PREFIX=${1}
SERVICE_INSTANCE=${2:-1}
REGION=${3:-us-east-1}

if [ -z "$SERVICE_PREFIX" ]; then
    echo -e "${RED}❌ 에러: 서비스 접두사를 입력하세요${NC}"
    echo ""
    echo "사용법: $0 [서비스접두사] [인스턴스번호]"
    echo ""
    echo "예시:"
    echo "  $0 g 2     # g2 서비스"
    echo "  $0 tt 1    # tt1 서비스"
    echo "  $0 prf 3   # prf3 서비스"
    echo "  $0 tem 1   # tem1 서비스"
    echo ""
    echo "서비스 접두사:"
    echo "  tem - 템플릿"
    echo "  tt  - 제목 서비스"
    echo "  prf - 교열 서비스"
    echo "  col - 칼럼 서비스"
    echo "  nws - 뉴스 서비스"
    exit 1
fi

SERVICE_NAME="${SERVICE_PREFIX}${SERVICE_INSTANCE}"

echo -e "${BLUE}============================================"
echo "🚀 서비스 배포 시작"
echo "============================================${NC}"
echo "서비스: ${GREEN}$SERVICE_NAME${NC}"
echo "리전: $REGION"
echo ""

# 확인
echo -e "${YELLOW}다음 리소스가 생성됩니다:${NC}"
echo "• DynamoDB: ${SERVICE_NAME}-conversations-v2, ${SERVICE_NAME}-prompts-v2, ..."
echo "• Lambda: ${SERVICE_NAME}-websocket-connect, ${SERVICE_NAME}-prompt-crud, ..."
echo "• S3: ${SERVICE_NAME}-frontend"
echo "• API Gateway: ${SERVICE_NAME}-rest-api, ${SERVICE_NAME}-websocket-api"
echo ""

read -p "계속하시겠습니까? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "취소되었습니다."
    exit 1
fi

# 환경변수 파일 준비
echo -e "${BLUE}📝 환경변수 파일 생성...${NC}"

# Backend .env
if [ -f "backend/.env.template" ]; then
    sed "s/SERVICE_NAME/$SERVICE_NAME/g" backend/.env.template > backend/.env

    # 가드레일 ID 처리 (있으면 사용, 없으면 기본값)
    if [ -z "$GUARDRAIL_ID" ]; then
        sed -i.bak "s/YOUR_GUARDRAIL_ID/ycwjnmzxut7k/g" backend/.env
    fi

    echo -e "${GREEN}✅ Backend .env 생성 완료${NC}"
fi

# Frontend .env (임시)
if [ -f "frontend/.env.template" ]; then
    cp frontend/.env.template frontend/.env
    echo -e "${GREEN}✅ Frontend .env 생성 완료${NC}"
fi

# 스크립트 디렉토리로 이동
cd scripts

# Phase 1: 인프라 구축
echo ""
echo -e "${BLUE}============================================"
echo "Phase 1: 인프라 구축"
echo "============================================${NC}"

./deploy-phase1-infra.sh "$SERVICE_NAME" "$REGION"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Phase 1 실패${NC}"
    exit 1
fi

# API ID 추출 및 Frontend .env 업데이트
if [ -f "../.api-ids" ]; then
    source ../.api-ids

    if [ -n "$REST_API_ID" ] && [ -n "$WS_API_ID" ]; then
        echo -e "${BLUE}📝 Frontend .env API ID 업데이트...${NC}"

        cd ..
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s/YOUR_API_ID/$REST_API_ID/g" frontend/.env
            sed -i '' "s/YOUR_WS_API_ID/$WS_API_ID/g" frontend/.env
        else
            # Linux
            sed -i "s/YOUR_API_ID/$REST_API_ID/g" frontend/.env
            sed -i "s/YOUR_WS_API_ID/$WS_API_ID/g" frontend/.env
        fi
        cd scripts

        echo -e "${GREEN}✅ API ID 업데이트 완료${NC}"
    fi
fi

# Phase 2: 코드 배포
echo ""
echo -e "${BLUE}============================================"
echo "Phase 2: 코드 배포"
echo "============================================${NC}"

./deploy-phase2-code.sh "$SERVICE_NAME" "$REGION"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Phase 2 실패${NC}"
    exit 1
fi

# 결과 출력
echo ""
echo -e "${GREEN}============================================"
echo "🎉 배포 완료!"
echo "============================================${NC}"
echo ""

# 엔드포인트 정보
if [ -f "../endpoints.txt" ]; then
    echo -e "${BLUE}📍 엔드포인트:${NC}"
    cat ../endpoints.txt | grep "$SERVICE_NAME" || cat ../endpoints.txt
    echo ""
fi

# CloudFront URL
if [ -f "../.cloudfront-url" ]; then
    CLOUDFRONT_URL=$(cat ../.cloudfront-url)
    echo -e "${BLUE}🌐 프론트엔드:${NC} $CLOUDFRONT_URL"
    echo ""
fi

# API 정보
if [ -n "$REST_API_ID" ]; then
    echo -e "${BLUE}🔌 REST API:${NC} https://$REST_API_ID.execute-api.$REGION.amazonaws.com/prod"
fi

if [ -n "$WS_API_ID" ]; then
    echo -e "${BLUE}🔌 WebSocket:${NC} wss://$WS_API_ID.execute-api.$REGION.amazonaws.com/prod"
fi

echo ""
echo -e "${GREEN}서비스 $SERVICE_NAME이 성공적으로 배포되었습니다!${NC}"
echo ""
echo "테스트:"
echo "1. 브라우저에서 CloudFront URL 접속"
echo "2. API 테스트: curl https://$REST_API_ID.execute-api.$REGION.amazonaws.com/prod/prompts/11"
echo "3. 로그 확인: aws logs tail /aws/lambda/${SERVICE_NAME}-prompt-crud --follow"