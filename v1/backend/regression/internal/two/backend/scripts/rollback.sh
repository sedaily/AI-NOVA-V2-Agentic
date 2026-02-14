#!/bin/bash

# API 롤백 스크립트
# Usage: ./rollback.sh [stage] [region] [deployment-id]

set -e

# 기본값 설정
STAGE=${1:-prod}
REGION=${2:-us-east-1}
DEPLOYMENT_ID=$3
API_ID="t75vorhge1"

# 색상 설정
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== API 롤백 시작 ===${NC}"
echo -e "API ID: ${YELLOW}$API_ID${NC}"
echo -e "Stage: ${YELLOW}$STAGE${NC}"
echo -e "Region: ${YELLOW}$REGION${NC}"

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

# 1. 현재 배포 정보 확인
echo -e "\n${BLUE}📊 현재 배포 정보 확인 중...${NC}"

CURRENT_DEPLOYMENT=$(aws apigateway get-stage \
    --rest-api-id "$API_ID" \
    --stage-name "$STAGE" \
    --region "$REGION" \
    --query 'deploymentId' \
    --output text 2>/dev/null || echo "")

if [ -z "$CURRENT_DEPLOYMENT" ]; then
    echo -e "${RED}❌ 현재 스테이지 정보를 가져올 수 없습니다.${NC}"
    exit 1
fi

echo -e "현재 배포 ID: ${YELLOW}$CURRENT_DEPLOYMENT${NC}"

# 2. 배포 히스토리 조회
echo -e "\n${BLUE}📋 배포 히스토리 조회 중...${NC}"

DEPLOYMENTS=$(aws apigateway get-deployments \
    --rest-api-id "$API_ID" \
    --region "$REGION" \
    --query 'items[*].[id,createdDate,description]' \
    --output table)

echo "$DEPLOYMENTS"

# 3. 롤백할 배포 ID 결정
if [ -z "$DEPLOYMENT_ID" ]; then
    echo -e "\n${YELLOW}롤백할 배포 ID를 선택하세요:${NC}"
    
    # 이전 배포 ID 자동 선택 (현재 배포 제외하고 가장 최근)
    PREVIOUS_DEPLOYMENT=$(aws apigateway get-deployments \
        --rest-api-id "$API_ID" \
        --region "$REGION" \
        --query "items[?id!=\`$CURRENT_DEPLOYMENT\`] | [0].id" \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$PREVIOUS_DEPLOYMENT" ] && [ "$PREVIOUS_DEPLOYMENT" != "None" ]; then
        echo -e "이전 배포 ID: ${YELLOW}$PREVIOUS_DEPLOYMENT${NC}"
        read -p "이 배포로 롤백하시겠습니까? (Y/n): " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            echo -e "${YELLOW}롤백을 취소했습니다.${NC}"
            exit 0
        fi
        
        DEPLOYMENT_ID=$PREVIOUS_DEPLOYMENT
    else
        echo -e "${RED}❌ 롤백할 이전 배포를 찾을 수 없습니다.${NC}"
        echo -e "수동으로 배포 ID를 지정해주세요: ${YELLOW}./rollback.sh $STAGE $REGION <deployment-id>${NC}"
        exit 1
    fi
else
    echo -e "\n${BLUE}지정된 배포 ID로 롤백: ${YELLOW}$DEPLOYMENT_ID${NC}"
fi

# 4. 배포 ID 유효성 확인
echo -e "\n${BLUE}🔍 배포 ID 유효성 확인 중...${NC}"

DEPLOYMENT_INFO=$(aws apigateway get-deployment \
    --rest-api-id "$API_ID" \
    --deployment-id "$DEPLOYMENT_ID" \
    --region "$REGION" 2>/dev/null || echo "")

if [ -z "$DEPLOYMENT_INFO" ]; then
    echo -e "${RED}❌ 유효하지 않은 배포 ID입니다: $DEPLOYMENT_ID${NC}"
    exit 1
fi

DEPLOYMENT_DATE=$(echo "$DEPLOYMENT_INFO" | jq -r '.createdDate // "Unknown"' 2>/dev/null || echo "Unknown")
DEPLOYMENT_DESC=$(echo "$DEPLOYMENT_INFO" | jq -r '.description // "No description"' 2>/dev/null || echo "No description")

echo -e "배포 날짜: ${YELLOW}$DEPLOYMENT_DATE${NC}"
echo -e "배포 설명: ${YELLOW}$DEPLOYMENT_DESC${NC}"

# 5. 최종 확인
echo -e "\n${RED}⚠️  롤백 확인${NC}"
echo -e "현재 배포: ${YELLOW}$CURRENT_DEPLOYMENT${NC}"
echo -e "롤백 대상: ${YELLOW}$DEPLOYMENT_ID${NC}"
echo -e "스테이지: ${YELLOW}$STAGE${NC}"

read -p "정말로 롤백하시겠습니까? (yes/no): " -r
if [ "$REPLY" != "yes" ]; then
    echo -e "${YELLOW}롤백을 취소했습니다.${NC}"
    exit 0
fi

# 6. 백업 생성 (현재 상태)
echo -e "\n${BLUE}💾 현재 상태 백업 중...${NC}"

BACKUP_FILE="backup-$STAGE-$CURRENT_DEPLOYMENT-$(date +%Y%m%d-%H%M%S).json"

aws apigateway get-deployment \
    --rest-api-id "$API_ID" \
    --deployment-id "$CURRENT_DEPLOYMENT" \
    --region "$REGION" > "$BACKUP_FILE"

echo -e "백업 파일: ${YELLOW}$BACKUP_FILE${NC}"

# 7. 롤백 실행
echo -e "\n${BLUE}🔄 롤백 실행 중...${NC}"

aws apigateway update-stage \
    --rest-api-id "$API_ID" \
    --stage-name "$STAGE" \
    --patch-ops op=replace,path=/deploymentId,value="$DEPLOYMENT_ID" \
    --region "$REGION" > /dev/null

echo -e "${GREEN}✅ 롤백 완료${NC}"

# 8. 롤백 검증
echo -e "\n${BLUE}🧪 롤백 검증 중...${NC}"

NEW_DEPLOYMENT=$(aws apigateway get-stage \
    --rest-api-id "$API_ID" \
    --stage-name "$STAGE" \
    --region "$REGION" \
    --query 'deploymentId' \
    --output text)

if [ "$NEW_DEPLOYMENT" = "$DEPLOYMENT_ID" ]; then
    echo -e "${GREEN}✅ 롤백 검증 성공${NC}"
else
    echo -e "${RED}❌ 롤백 검증 실패${NC}"
    echo -e "예상: $DEPLOYMENT_ID"
    echo -e "실제: $NEW_DEPLOYMENT"
    exit 1
fi

# 9. API 상태 확인
echo -e "\n${BLUE}🌐 API 상태 확인 중...${NC}"

API_URL="https://$API_ID.execute-api.$REGION.amazonaws.com/$STAGE"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/prompts" || echo "000")

if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "401" ]; then
    echo -e "${GREEN}✅ API 엔드포인트 정상 응답 (HTTP $HTTP_STATUS)${NC}"
else
    echo -e "${YELLOW}⚠️  API 엔드포인트 응답 확인 필요 (HTTP $HTTP_STATUS)${NC}"
fi

# 10. Lambda 함수 버전 확인 (선택사항)
echo -e "\n${BLUE}🔍 Lambda 함수 상태 확인${NC}"

LAMBDA_FUNCTIONS=(
    "sedaily-column-prompt-crud"
    "sedaily-column-conversation-api"
    "sedaily-column-usage-handler"
    "sedaily-column-authorizer"
)

for FUNCTION in "${LAMBDA_FUNCTIONS[@]}"; do
    LAST_MODIFIED=$(aws lambda get-function \
        --function-name "$FUNCTION" \
        --region "$REGION" \
        --query 'Configuration.LastModified' \
        --output text 2>/dev/null || echo "Unknown")
    
    echo -e "   ${FUNCTION}: ${YELLOW}$LAST_MODIFIED${NC}"
done

# 11. 롤백 완료 메시지
echo -e "\n${GREEN}🎉 롤백 완료!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "📍 API URL: ${YELLOW}$API_URL${NC}"
echo -e "🏷️  Stage: ${YELLOW}$STAGE${NC}"
echo -e "🔄 이전 배포: ${YELLOW}$CURRENT_DEPLOYMENT${NC}"
echo -e "✅ 현재 배포: ${YELLOW}$DEPLOYMENT_ID${NC}"
echo -e "💾 백업 파일: ${YELLOW}$BACKUP_FILE${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 12. 다음 단계 안내
echo -e "\n${BLUE}📋 다음 단계:${NC}"
echo -e "1. API 테스트: ${YELLOW}./test-api.sh $STAGE $REGION${NC}"
echo -e "2. 모니터링 확인: CloudWatch 로그 및 메트릭"
echo -e "3. 문제 발생 시 재배포: ${YELLOW}./deploy.sh $STAGE $REGION${NC}"

# 13. 모니터링 링크
echo -e "\n${BLUE}📊 모니터링:${NC}"
echo -e "CloudWatch: https://console.aws.amazon.com/cloudwatch/home?region=$REGION#logsV2:log-groups"
echo -e "API Gateway: https://console.aws.amazon.com/apigateway/home?region=$REGION#/apis/$API_ID"

# 14. 롤백 로그 기록
echo -e "\n${BLUE}📝 롤백 로그 기록 중...${NC}"

LOG_FILE="rollback-log-$(date +%Y%m%d-%H%M%S).txt"
cat > "$LOG_FILE" << EOF
=== API 롤백 로그 ===
날짜: $(date)
API ID: $API_ID
Stage: $STAGE
Region: $REGION
이전 배포: $CURRENT_DEPLOYMENT
현재 배포: $DEPLOYMENT_ID
백업 파일: $BACKUP_FILE
실행자: $(whoami)
상태: 성공
EOF

echo -e "롤백 로그: ${YELLOW}$LOG_FILE${NC}"

echo -e "\n${GREEN}롤백이 성공적으로 완료되었습니다! 🔄${NC}"