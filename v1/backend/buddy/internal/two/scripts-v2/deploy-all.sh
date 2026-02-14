#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}==================================${NC}"
echo -e "${BLUE}  Nexus Template v2 전체 배포     ${NC}"
echo -e "${BLUE}==================================${NC}"
echo ""

# config.sh 존재 확인
if [ ! -f "config.sh" ]; then
    echo -e "${RED}config.sh 파일이 없습니다.${NC}"
    echo "먼저 ./init-template.sh를 실행하여 초기화하세요."
    exit 1
fi

# 설정 로드
source ./config.sh

echo "서비스: ${SERVICE_NAME}-${CARD_COUNT}"
echo "리전: ${REGION}"
echo ""

# 각 단계 실행 함수
run_step() {
    local STEP_NUM=$1
    local SCRIPT_NAME=$2
    local DESCRIPTION=$3

    echo ""
    echo -e "${YELLOW}[$STEP_NUM/7] $DESCRIPTION${NC}"
    echo "스크립트: $SCRIPT_NAME"
    echo ""

    if [ -f "$SCRIPT_NAME" ]; then
        chmod +x "$SCRIPT_NAME"
        if ./"$SCRIPT_NAME"; then
            echo -e "${GREEN}✓ $DESCRIPTION 완료${NC}"
            return 0
        else
            echo -e "${RED}✗ $DESCRIPTION 실패${NC}"
            return 1
        fi
    else
        echo -e "${RED}스크립트를 찾을 수 없음: $SCRIPT_NAME${NC}"
        return 1
    fi
}

# 시작 시간 기록
START_TIME=$(date +%s)

# 배포 시작
echo -e "${BLUE}배포를 시작합니다...${NC}"

# Step 1: DynamoDB 테이블 생성
if ! run_step 1 "01-deploy-dynamodb.sh" "DynamoDB 테이블 생성"; then
    echo -e "${RED}DynamoDB 테이블 생성 실패. 배포를 중단합니다.${NC}"
    exit 1
fi

# Step 2: Lambda 함수 생성
if ! run_step 2 "02-deploy-lambda.sh" "Lambda 함수 생성"; then
    echo -e "${RED}Lambda 함수 생성 실패. 배포를 중단합니다.${NC}"
    exit 1
fi

# Step 3: API Gateway 설정
if ! run_step 3 "03-deploy-api-gateway-final.sh" "API Gateway 설정"; then
    echo -e "${RED}API Gateway 설정 실패. 배포를 중단합니다.${NC}"
    exit 1
fi

# Step 4: 환경 변수 업데이트
if ! run_step 4 "04-update-config.sh" "환경 변수 업데이트"; then
    echo -e "${YELLOW}환경 변수 업데이트 실패. 계속 진행합니다.${NC}"
fi

# Step 5: Lambda 코드 배포
if [ -f "05-deploy-lambda-code-fixed.sh" ]; then
    if ! run_step 5 "05-deploy-lambda-code-fixed.sh" "Lambda 코드 배포 (수정된 버전)"; then
        echo -e "${RED}Lambda 코드 배포 실패. 배포를 중단합니다.${NC}"
        exit 1
    fi
else
    if ! run_step 5 "05-deploy-lambda-code.sh" "Lambda 코드 배포"; then
        echo -e "${RED}Lambda 코드 배포 실패. 배포를 중단합니다.${NC}"
        exit 1
    fi
fi

# Step 6: 프론트엔드 배포
if ! run_step 6 "06-deploy-frontend.sh" "프론트엔드 배포"; then
    echo -e "${YELLOW}프론트엔드 배포 실패. CloudFront URL을 확인하세요.${NC}"
fi

# Step 7: 테스트 데이터 초기화 (선택적)
echo ""
echo -e "${YELLOW}[7/7] 테스트 데이터 초기화${NC}"
read -p "테스트 프롬프트를 생성하시겠습니까? (y/n): " CREATE_TEST_DATA
if [ "$CREATE_TEST_DATA" == "y" ]; then
    echo "테스트 프롬프트 생성 중..."

    # 기본 프롬프트 생성
    aws dynamodb put-item \
        --table-name "${PROMPTS_TABLE}" \
        --item '{
            "promptId": {"S": "11"},
            "title": {"S": "Claude Assistant"},
            "instruction": {"S": "You are a helpful AI assistant."},
            "description": {"S": "General purpose AI assistant"},
            "createdAt": {"S": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"},
            "updatedAt": {"S": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"}
        }' \
        --region "${REGION}" \
        --output text > /dev/null 2>&1

    echo -e "${GREEN}✓ 테스트 프롬프트 생성 완료${NC}"
fi

# 종료 시간 계산
END_TIME=$(date +%s)
ELAPSED_TIME=$((END_TIME - START_TIME))
MINUTES=$((ELAPSED_TIME / 60))
SECONDS=$((ELAPSED_TIME % 60))

echo ""
echo -e "${GREEN}==================================${NC}"
echo -e "${GREEN}      배포 완료!                  ${NC}"
echo -e "${GREEN}==================================${NC}"
echo ""
echo "소요 시간: ${MINUTES}분 ${SECONDS}초"
echo ""
echo -e "${YELLOW}배포된 리소스:${NC}"
echo "• DynamoDB 테이블:"
echo "  - ${CONVERSATIONS_TABLE}"
echo "  - ${PROMPTS_TABLE}"
echo "  - ${USAGE_TABLE}"
echo ""
echo "• Lambda 함수:"
echo "  - ${LAMBDA_CONVERSATION_API}"
echo "  - ${LAMBDA_WEBSOCKET_MESSAGE}"
echo "  - ${LAMBDA_PROMPT_API}"
echo "  - ${LAMBDA_USAGE_API}"
echo ""

# API 엔드포인트 출력
echo -e "${YELLOW}API 엔드포인트:${NC}"

# REST API URL 가져오기
REST_API_ID=$(aws apigateway get-rest-apis --region ${REGION} \
    --query "items[?name=='${REST_API_NAME}'].id" \
    --output text | head -1)
if [ -n "$REST_API_ID" ]; then
    echo "REST API: https://${REST_API_ID}.execute-api.${REGION}.amazonaws.com/prod"
fi

# WebSocket API URL 가져오기
WS_API_ID=$(aws apigatewayv2 get-apis --region ${REGION} \
    --query "Items[?Name=='${WEBSOCKET_API_NAME}'].ApiId" \
    --output text | head -1)
if [ -n "$WS_API_ID" ]; then
    echo "WebSocket: wss://${WS_API_ID}.execute-api.${REGION}.amazonaws.com/prod"
fi

# CloudFront URL 가져오기
CF_DISTRIBUTION=$(aws cloudfront list-distributions \
    --query "DistributionList.Items[?Comment=='${SERVICE_NAME}-${CARD_COUNT} frontend'].DomainName" \
    --output text | head -1)
if [ -n "$CF_DISTRIBUTION" ]; then
    echo ""
    echo -e "${YELLOW}프론트엔드 URL:${NC}"
    echo "https://${CF_DISTRIBUTION}"
fi

echo ""
echo -e "${BLUE}테스트 명령어:${NC}"
echo "# DynamoDB 확인"
echo "aws dynamodb scan --table-name ${CONVERSATIONS_TABLE} --region ${REGION} --max-items 1"
echo ""
echo "# Lambda 테스트"
echo "aws lambda invoke --function-name ${LAMBDA_CONVERSATION_API} --region ${REGION} /tmp/test.json"
echo ""

# 문제 해결 가이드 참조
if [ -d "pro-sol" ]; then
    echo -e "${YELLOW}문제 해결 가이드:${NC}"
    echo "pro-sol/ 디렉토리의 문서를 참조하세요."
    ls -la pro-sol/*.md 2>/dev/null
fi

echo ""
echo -e "${GREEN}배포가 완료되었습니다!${NC}"