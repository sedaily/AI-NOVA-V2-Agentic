#!/bin/bash

# AWS Secrets Manager에 Anthropic API 키 설정
# 네이밍: regression

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}AWS Secrets Manager에 Anthropic API 키 설정 시작...${NC}"

# AWS 리전 설정
AWS_REGION=${AWS_REGION:-"us-east-1"}
SECRET_NAME="regression-v1"
API_KEY="${ANTHROPIC_API_KEY:-your-api-key-here}"

# 기존 시크릿이 있는지 확인
echo -e "${YELLOW}기존 시크릿 확인 중...${NC}"
if aws secretsmanager describe-secret --secret-id "$SECRET_NAME" --region "$AWS_REGION" 2>/dev/null; then
    echo -e "${YELLOW}기존 시크릿을 업데이트합니다...${NC}"
    aws secretsmanager update-secret \
        --secret-id "$SECRET_NAME" \
        --secret-string "{\"api_key\":\"$API_KEY\"}" \
        --region "$AWS_REGION"
else
    echo -e "${YELLOW}새 시크릿을 생성합니다...${NC}"
    aws secretsmanager create-secret \
        --name "$SECRET_NAME" \
        --description "Anthropic API Key for regression-v1 environment" \
        --secret-string "{\"api_key\":\"$API_KEY\"}" \
        --region "$AWS_REGION" \
        --tags "Key=Environment,Value=regression-v1" "Key=Service,Value=sedaily-column"
fi

echo -e "${GREEN}✅ Secrets Manager 설정 완료!${NC}"
echo -e "${GREEN}Secret Name: $SECRET_NAME${NC}"
echo -e "${GREEN}Region: $AWS_REGION${NC}"

# Lambda 함수들에 환경변수 추가를 위한 ARN 출력
SECRET_ARN=$(aws secretsmanager describe-secret --secret-id "$SECRET_NAME" --region "$AWS_REGION" --query 'ARN' --output text)
echo -e "${GREEN}Secret ARN: $SECRET_ARN${NC}"

echo -e "\n${YELLOW}Lambda 함수에 다음 환경변수를 추가하세요:${NC}"
echo "ANTHROPIC_SECRET_NAME=$SECRET_NAME"
echo "ANTHROPIC_SECRET_ARN=$SECRET_ARN"