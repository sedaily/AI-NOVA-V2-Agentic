#!/bin/bash

# ===================================================
# p2 API Gateway CORS 문제 해결 스크립트
# ===================================================
# 이 스크립트는 API Gateway의 Lambda 통합이 누락되거나
# CORS 설정이 잘못되었을 때 API를 재배포합니다
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

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}p2 API Gateway CORS 수정 스크립트${NC}"
echo -e "${BLUE}실행 시간: ${TIMESTAMP}${NC}"
echo -e "${BLUE}======================================${NC}"

# 설정 변수
SERVICE_NAME="p2-two"
REGION="us-east-1"
STAGE="prod"
ACCOUNT_ID="887078546492"

# 현재 API 정보 가져오기
echo -e "\n${YELLOW}현재 API Gateway 정보 확인 중...${NC}"
CURRENT_REST_API=$(aws apigateway get-rest-apis --query "items[?name=='${SERVICE_NAME}-api'].id" --output text 2>/dev/null || echo "")
CURRENT_WS_API=$(aws apigatewayv2 get-apis --query "Items[?Name=='${SERVICE_NAME}-websocket'].ApiId" --output text 2>/dev/null || echo "")

if [ -n "$CURRENT_REST_API" ]; then
    echo -e "${GREEN}✓ 현재 REST API ID: ${CURRENT_REST_API}${NC}"
    echo -e "${GREEN}✓ 현재 WebSocket API ID: ${CURRENT_WS_API}${NC}"

    # CORS 헤더 설정
    echo -e "\n${YELLOW}CORS 헤더 설정 중...${NC}"

    # 모든 리소스 가져오기
    RESOURCES=$(aws apigateway get-resources --rest-api-id $CURRENT_REST_API --query 'items[*]' --output json)

    # 각 리소스에 대해 OPTIONS 메서드 설정
    echo "$RESOURCES" | jq -c '.[]' | while read resource; do
        RESOURCE_ID=$(echo $resource | jq -r '.id')
        RESOURCE_PATH=$(echo $resource | jq -r '.path')

        echo -e "${YELLOW}처리 중: ${RESOURCE_PATH}${NC}"

        # OPTIONS 메서드가 있는지 확인
        METHODS=$(echo $resource | jq -r '.resourceMethods // {} | keys[]' 2>/dev/null || echo "")

        if [ -n "$METHODS" ]; then
            # OPTIONS 메서드 추가/업데이트
            aws apigateway put-method \
                --rest-api-id $CURRENT_REST_API \
                --resource-id $RESOURCE_ID \
                --http-method OPTIONS \
                --authorization-type NONE \
                --region $REGION 2>/dev/null || true

            # MOCK 통합 설정
            aws apigateway put-integration \
                --rest-api-id $CURRENT_REST_API \
                --resource-id $RESOURCE_ID \
                --http-method OPTIONS \
                --type MOCK \
                --request-templates '{"application/json":"{\"statusCode\":200}"}' \
                --region $REGION 2>/dev/null || true

            # Method Response 설정
            aws apigateway put-method-response \
                --rest-api-id $CURRENT_REST_API \
                --resource-id $RESOURCE_ID \
                --http-method OPTIONS \
                --status-code 200 \
                --response-parameters '{"method.response.header.Access-Control-Allow-Origin":false,"method.response.header.Access-Control-Allow-Headers":false,"method.response.header.Access-Control-Allow-Methods":false}' \
                --region $REGION 2>/dev/null || true

            # Integration Response 설정
            aws apigateway put-integration-response \
                --rest-api-id $CURRENT_REST_API \
                --resource-id $RESOURCE_ID \
                --http-method OPTIONS \
                --status-code 200 \
                --response-parameters '{"method.response.header.Access-Control-Allow-Origin":"'"'"'*'"'"'","method.response.header.Access-Control-Allow-Headers":"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'","method.response.header.Access-Control-Allow-Methods":"'"'"'GET,POST,PUT,DELETE,OPTIONS,PATCH'"'"'"}' \
                --region $REGION 2>/dev/null || true

            # 다른 메서드들에 대한 CORS 헤더 설정
            for METHOD in $METHODS; do
                if [ "$METHOD" != "OPTIONS" ]; then
                    # Method Response에 CORS 헤더 추가
                    aws apigateway put-method-response \
                        --rest-api-id $CURRENT_REST_API \
                        --resource-id $RESOURCE_ID \
                        --http-method $METHOD \
                        --status-code 200 \
                        --response-parameters '{"method.response.header.Access-Control-Allow-Origin":false}' \
                        --region $REGION 2>/dev/null || true

                    # Integration Response에 CORS 헤더 추가
                    aws apigateway put-integration-response \
                        --rest-api-id $CURRENT_REST_API \
                        --resource-id $RESOURCE_ID \
                        --http-method $METHOD \
                        --status-code 200 \
                        --response-parameters '{"method.response.header.Access-Control-Allow-Origin":"'"'"'*'"'"'"}' \
                        --region $REGION 2>/dev/null || true
                fi
            done
        fi
    done

    # API 재배포
    echo -e "\n${YELLOW}API 재배포 중...${NC}"
    aws apigateway create-deployment \
        --rest-api-id $CURRENT_REST_API \
        --stage-name $STAGE \
        --description "CORS configuration update" \
        --region $REGION

    echo -e "${GREEN}✓ CORS 설정 완료${NC}"

    # 환경 변수 업데이트
    echo -e "\n${YELLOW}Frontend 환경 변수 업데이트 중...${NC}"

    # 올바른 API 엔드포인트 설정
    REST_ENDPOINT="https://${CURRENT_REST_API}.execute-api.${REGION}.amazonaws.com/${STAGE}"
    WS_ENDPOINT="wss://${CURRENT_WS_API}.execute-api.${REGION}.amazonaws.com/${STAGE}"

    # Frontend .env 업데이트
    ENV_FILE="../frontend/.env"
    ENV_PROD_FILE="../frontend/.env.production"

    if [ -f "$ENV_FILE" ]; then
        # 백업 생성
        cp $ENV_FILE "${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"

        # 환경 변수 업데이트
        sed -i '' "s|VITE_API_BASE_URL=.*|VITE_API_BASE_URL=${REST_ENDPOINT}|" $ENV_FILE
        sed -i '' "s|VITE_WS_URL=.*|VITE_WS_URL=${WS_ENDPOINT}|" $ENV_FILE
        sed -i '' "s|VITE_API_URL=.*|VITE_API_URL=${REST_ENDPOINT}|" $ENV_FILE
        sed -i '' "s|VITE_PROMPT_API_URL=.*|VITE_PROMPT_API_URL=${REST_ENDPOINT}|" $ENV_FILE
        sed -i '' "s|VITE_WEBSOCKET_URL=.*|VITE_WEBSOCKET_URL=${WS_ENDPOINT}|" $ENV_FILE
        sed -i '' "s|VITE_USAGE_API_URL=.*|VITE_USAGE_API_URL=${REST_ENDPOINT}|" $ENV_FILE
        sed -i '' "s|VITE_CONVERSATION_API_URL=.*|VITE_CONVERSATION_API_URL=${REST_ENDPOINT}|" $ENV_FILE

        echo -e "${GREEN}✓ .env 업데이트 완료${NC}"
    fi

    if [ -f "$ENV_PROD_FILE" ]; then
        # 백업 생성
        cp $ENV_PROD_FILE "${ENV_PROD_FILE}.backup.$(date +%Y%m%d_%H%M%S)"

        # 환경 변수 업데이트
        sed -i '' "s|VITE_API_BASE_URL=.*|VITE_API_BASE_URL=${REST_ENDPOINT}|" $ENV_PROD_FILE
        sed -i '' "s|VITE_WS_URL=.*|VITE_WS_URL=${WS_ENDPOINT}|" $ENV_PROD_FILE

        echo -e "${GREEN}✓ .env.production 업데이트 완료${NC}"
    fi

    # 정보 출력
    echo -e "\n${GREEN}======================================${NC}"
    echo -e "${GREEN}✅ p2 API Gateway CORS 설정 완료!${NC}"
    echo -e "${GREEN}======================================${NC}"
    echo -e "${BLUE}생성 시간: ${TIMESTAMP}${NC}"
    echo -e "${BLUE}스택: ${SERVICE_NAME}${NC}"
    echo -e ""
    echo -e "${GREEN}REST API:${NC}"
    echo -e "  ID: ${CURRENT_REST_API}"
    echo -e "  Endpoint: ${REST_ENDPOINT}"
    echo -e ""
    echo -e "${GREEN}WebSocket API:${NC}"
    echo -e "  ID: ${CURRENT_WS_API}"
    echo -e "  Endpoint: ${WS_ENDPOINT}"
    echo -e ""
    echo -e "${YELLOW}다음 단계:${NC}"
    echo -e "  1. Frontend 재빌드: cd ../frontend && npm run build"
    echo -e "  2. S3 배포: aws s3 sync dist/ s3://p2-two-frontend --delete"
    echo -e "  3. CloudFront 캐시 무효화: aws cloudfront create-invalidation --distribution-id [DIST_ID] --paths '/*'"
    echo -e "${GREEN}======================================${NC}"

    # CORS 테스트
    echo -e "\n${YELLOW}CORS 헤더 테스트 중...${NC}"
    TEST_URL="${REST_ENDPOINT}/prompts"

    echo -e "테스트 URL: ${TEST_URL}"

    # OPTIONS 요청 테스트
    CORS_TEST=$(curl -s -X OPTIONS $TEST_URL -H "Origin: https://example.com" -I 2>/dev/null | grep -i "access-control" || echo "")

    if [ -n "$CORS_TEST" ]; then
        echo -e "${GREEN}✓ CORS 헤더 확인됨:${NC}"
        echo "$CORS_TEST"
    else
        echo -e "${YELLOW}⚠ API Gateway CORS 헤더를 확인할 수 없습니다. Lambda 응답에서 설정되는지 확인하세요.${NC}"
    fi

else
    echo -e "${RED}❌ API가 존재하지 않습니다. 먼저 API를 배포하세요.${NC}"
    exit 1
fi