#!/bin/bash

# 색상 설정
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}   DynamoDB 인덱스 생성   ${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

REGION="us-east-1"

# 1. conversations 테이블에 GSI 추가
echo -e "${BLUE}1. conversations 테이블 인덱스 생성 중...${NC}"
aws dynamodb update-table \
    --table-name nx-wt-prf-conversations \
    --attribute-definitions \
        AttributeName=userId,AttributeType=S \
        AttributeName=createdAt,AttributeType=S \
    --global-secondary-index-updates \
        "[{\"Create\":{\"IndexName\":\"userId-createdAt-index\",\"Keys\":[{\"AttributeName\":\"userId\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"createdAt\",\"KeyType\":\"RANGE\"}],\"Projection\":{\"ProjectionType\":\"ALL\"},\"ProvisionedThroughput\":{\"ReadCapacityUnits\":5,\"WriteCapacityUnits\":5}}}]" \
    --region $REGION 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ conversations 테이블 인덱스 생성 시작${NC}"
else
    echo -e "${YELLOW}⚠ conversations 테이블 인덱스가 이미 존재하거나 오류 발생${NC}"
fi

# 인덱스 생성 완료 대기
echo -e "${YELLOW}인덱스 생성 대기 중 (최대 5분)...${NC}"
aws dynamodb wait table-exists --table-name nx-wt-prf-conversations --region $REGION

# 테이블 상태 확인
TABLE_STATUS=$(aws dynamodb describe-table \
    --table-name nx-wt-prf-conversations \
    --region $REGION \
    --query "Table.TableStatus" \
    --output text)

echo -e "${GREEN}테이블 상태: $TABLE_STATUS${NC}"

# 2. 인덱스 목록 확인
echo -e "\n${BLUE}2. 테이블 인덱스 확인${NC}"
aws dynamodb describe-table \
    --table-name nx-wt-prf-conversations \
    --region $REGION \
    --query "Table.GlobalSecondaryIndexes[*].[IndexName,IndexStatus]" \
    --output table

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   ✅ 인덱스 설정 완료!   ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# API 테스트
echo -e "${BLUE}3. API 테스트${NC}"
curl -s -X GET "https://gda9ojk5c7.execute-api.us-east-1.amazonaws.com/prod/conversations?userId=test&engineType=T5" \
    -H "Content-Type: application/json" | jq '.' 2>/dev/null | head -10

echo ""