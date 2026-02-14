#!/bin/bash

# sedaily-column API 배포 스크립트
# Usage: ./deploy.sh [stage] [region]

set -e

# 기본값 설정
STAGE=${1:-prod}
REGION=${2:-us-east-1}
API_ID="t75vorhge1"

# 색상 설정
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== sedaily-column API 배포 시작 ===${NC}"
echo -e "Stage: ${YELLOW}$STAGE${NC}"
echo -e "Region: ${YELLOW}$REGION${NC}"
echo -e "API ID: ${YELLOW}$API_ID${NC}"

# 현재 디렉토리 확인
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ requirements.txt를 찾을 수 없습니다. backend 디렉토리에서 실행해주세요.${NC}"
    exit 1
fi

# AWS CLI 설치 확인
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI가 설치되지 않았습니다.${NC}"
    exit 1
fi

# AWS 자격 증명 확인
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS 자격 증명이 설정되지 않았습니다.${NC}"
    exit 1
fi

echo -e "\n${GREEN}✅ 사전 검사 완료${NC}"

# 1. 의존성 설치
echo -e "\n${BLUE}📦 의존성 설치 중...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt -t ./packages/
    echo -e "${GREEN}✅ 의존성 설치 완료${NC}"
fi

# 2. Lambda 함수 배포
echo -e "\n${BLUE}🚀 Lambda 함수 배포 중...${NC}"

FUNCTIONS=(
    "sedaily-column-prompt-crud:handlers/api/prompt.py"
    "sedaily-column-conversation-api:handlers/api/conversation.py"
    "sedaily-column-usage-handler:handlers/api/usage.py"
    "sedaily-column-authorizer:handlers/api/authorizer.py"
)

for FUNCTION_INFO in "${FUNCTIONS[@]}"; do
    IFS=':' read -r FUNCTION_NAME HANDLER_PATH <<< "$FUNCTION_INFO"
    
    echo -e "\n${YELLOW}배포 중: $FUNCTION_NAME${NC}"
    
    # 배포 패키지 생성
    TEMP_DIR=$(mktemp -d)
    
    # 핸들러 파일 복사
    cp -r handlers/ "$TEMP_DIR/"
    cp -r src/ "$TEMP_DIR/" 2>/dev/null || true
    cp -r utils/ "$TEMP_DIR/" 2>/dev/null || true
    
    # 의존성 복사
    if [ -d "packages" ]; then
        cp -r packages/* "$TEMP_DIR/"
    fi
    
    # ZIP 파일 생성
    cd "$TEMP_DIR"
    zip -r "../${FUNCTION_NAME}.zip" . > /dev/null
    cd - > /dev/null
    
    # Lambda 함수 업데이트
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file "fileb://${TEMP_DIR}/../${FUNCTION_NAME}.zip" \
        --region "$REGION" > /dev/null
    
    # 환경 변수 업데이트
    aws lambda update-function-configuration \
        --function-name "$FUNCTION_NAME" \
        --environment Variables="{
            AWS_REGION=$REGION,
            STAGE=$STAGE,
            PROMPTS_TABLE=sedaily-column-prompts,
            FILES_TABLE=sedaily-column-files,
            CONVERSATIONS_TABLE=sedaily-column-conversations,
            USAGE_TABLE=sedaily-column-usage,
            DEFAULT_TENANT_ID=sedaily
        }" \
        --region "$REGION" > /dev/null
    
    # 정리
    rm -rf "$TEMP_DIR" "${TEMP_DIR}/../${FUNCTION_NAME}.zip"
    
    echo -e "${GREEN}  ✅ $FUNCTION_NAME 배포 완료${NC}"
done

# 3. API Gateway 권한 설정
echo -e "\n${BLUE}🔐 API Gateway 권한 설정 중...${NC}"

LAMBDA_FUNCTIONS=(
    "sedaily-column-prompt-crud"
    "sedaily-column-conversation-api"
    "sedaily-column-usage-handler"
    "sedaily-column-authorizer"
)

for FUNCTION in "${LAMBDA_FUNCTIONS[@]}"; do
    # 기존 권한 제거 (에러 무시)
    aws lambda remove-permission \
        --function-name "$FUNCTION" \
        --statement-id "apigateway-invoke-$STAGE" \
        --region "$REGION" 2>/dev/null || true
    
    # 새 권한 추가
    aws lambda add-permission \
        --function-name "$FUNCTION" \
        --statement-id "apigateway-invoke-$STAGE" \
        --action lambda:InvokeFunction \
        --principal apigateway.amazonaws.com \
        --source-arn "arn:aws:execute-api:$REGION:*:$API_ID/*" \
        --region "$REGION" > /dev/null
done

echo -e "${GREEN}✅ API Gateway 권한 설정 완료${NC}"

# 4. API 배포
echo -e "\n${BLUE}🌐 API Gateway 배포 중...${NC}"

DEPLOYMENT_ID=$(aws apigateway create-deployment \
    --rest-api-id "$API_ID" \
    --stage-name "$STAGE" \
    --description "Deployed on $(date)" \
    --region "$REGION" \
    --query 'id' \
    --output text)

echo -e "${GREEN}✅ API 배포 완료 (Deployment ID: $DEPLOYMENT_ID)${NC}"

# 5. 배포 검증
echo -e "\n${BLUE}🧪 배포 검증 중...${NC}"

API_URL="https://$API_ID.execute-api.$REGION.amazonaws.com/$STAGE"

# Health check (프롬프트 목록 조회)
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/prompts" || echo "000")

if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "401" ]; then
    echo -e "${GREEN}✅ API 엔드포인트 정상 응답${NC}"
else
    echo -e "${YELLOW}⚠️  API 엔드포인트 응답 확인 필요 (HTTP $HTTP_STATUS)${NC}"
fi

# 6. 정리
echo -e "\n${BLUE}🧹 정리 중...${NC}"
rm -rf packages/ 2>/dev/null || true

# 7. 배포 완료 메시지
echo -e "\n${GREEN}🎉 배포 완료!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "📍 API URL: ${YELLOW}$API_URL${NC}"
echo -e "🏷️  Stage: ${YELLOW}$STAGE${NC}"
echo -e "🌍 Region: ${YELLOW}$REGION${NC}"
echo -e "📊 Deployment ID: ${YELLOW}$DEPLOYMENT_ID${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 8. 테스트 명령어 제안
echo -e "\n${BLUE}🧪 테스트 명령어:${NC}"
echo -e "curl -X GET \"$API_URL/prompts\""
echo -e "curl -X GET \"$API_URL/conversations?userId=test@example.com\""
echo -e "curl -X GET \"$API_URL/usage/test@example.com/all\""

# 9. 모니터링 링크
echo -e "\n${BLUE}📊 모니터링:${NC}"
echo -e "CloudWatch: https://console.aws.amazon.com/cloudwatch/home?region=$REGION#logsV2:log-groups"
echo -e "API Gateway: https://console.aws.amazon.com/apigateway/home?region=$REGION#/apis/$API_ID"

echo -e "\n${GREEN}배포가 성공적으로 완료되었습니다! 🚀${NC}"