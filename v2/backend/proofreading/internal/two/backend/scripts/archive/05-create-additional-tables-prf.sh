#!/bin/bash

# 색상 설정
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}   추가 DynamoDB 테이블 생성 - nx-wt-prf   ${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

REGION="us-east-1"

# 1. Conversations 테이블 생성
echo -e "${BLUE}1. Conversations 테이블 생성 중...${NC}"
aws dynamodb create-table \
    --table-name nx-wt-prf-conversations \
    --attribute-definitions \
        AttributeName=userId,AttributeType=S \
        AttributeName=conversationId,AttributeType=S \
    --key-schema \
        AttributeName=userId,KeyType=HASH \
        AttributeName=conversationId,KeyType=RANGE \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region $REGION 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Conversations 테이블 생성 완료${NC}"
else
    echo -e "${YELLOW}⚠ Conversations 테이블이 이미 존재하거나 생성 실패${NC}"
fi

# 2. Usage Tracking 테이블 생성
echo -e "\n${BLUE}2. Usage Tracking 테이블 생성 중...${NC}"
aws dynamodb create-table \
    --table-name nx-wt-prf-usage-tracking \
    --attribute-definitions \
        AttributeName=PK,AttributeType=S \
        AttributeName=SK,AttributeType=S \
    --key-schema \
        AttributeName=PK,KeyType=HASH \
        AttributeName=SK,KeyType=RANGE \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region $REGION 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Usage Tracking 테이블 생성 완료${NC}"
else
    echo -e "${YELLOW}⚠ Usage Tracking 테이블이 이미 존재하거나 생성 실패${NC}"
fi

# 3. WebSocket Connections 테이블 생성
echo -e "\n${BLUE}3. WebSocket Connections 테이블 생성 중...${NC}"
aws dynamodb create-table \
    --table-name nx-wt-prf-websocket-connections \
    --attribute-definitions \
        AttributeName=connectionId,AttributeType=S \
    --key-schema \
        AttributeName=connectionId,KeyType=HASH \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region $REGION 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ WebSocket Connections 테이블 생성 완료${NC}"
else
    echo -e "${YELLOW}⚠ WebSocket Connections 테이블이 이미 존재하거나 생성 실패${NC}"
fi

# 4. Usage (월별 사용량) 테이블 생성 - 필요시
echo -e "\n${BLUE}4. Usage 테이블 생성 중...${NC}"
aws dynamodb create-table \
    --table-name nx-wt-prf-usage \
    --attribute-definitions \
        AttributeName=userId,AttributeType=S \
        AttributeName=yearMonth,AttributeType=S \
    --key-schema \
        AttributeName=userId,KeyType=HASH \
        AttributeName=yearMonth,KeyType=RANGE \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region $REGION 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Usage 테이블 생성 완료${NC}"
else
    echo -e "${YELLOW}⚠ Usage 테이블이 이미 존재하거나 생성 실패${NC}"
fi

# 테이블 생성 확인
echo -e "\n${BLUE}5. 테이블 생성 확인 중...${NC}"
sleep 5

# 모든 nx-wt-prf 테이블 목록 확인
echo -e "\n${CYAN}📋 생성된 테이블 목록:${NC}"
aws dynamodb list-tables --region $REGION --query "TableNames[?starts_with(@, 'nx-wt-prf')]" --output json | jq -r '.[]' | while read table; do
    echo -e "  ${GREEN}✓${NC} $table"
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   ✅ 추가 테이블 생성 완료!   ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""