#!/bin/bash

# 색상 설정
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}SEDAILY-COLUMN DYNAMODB SETUP${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""

# 설정
REGION="us-east-1"
PREFIX="sedaily-column"

# 테이블 목록
TABLES=(
    "${PREFIX}-conversations"
    "${PREFIX}-prompts"
    "${PREFIX}-usage"
    "${PREFIX}-websocket-connections"
    "${PREFIX}-files"
)

# 기존 테이블 삭제 (있는 경우)
echo -e "${YELLOW}기존 테이블 확인 및 삭제 중...${NC}"
for TABLE in "${TABLES[@]}"; do
    if aws dynamodb describe-table --table-name "$TABLE" --region $REGION 2>/dev/null; then
        echo -e "${YELLOW}Deleting existing table: $TABLE${NC}"
        aws dynamodb delete-table --table-name "$TABLE" --region $REGION 2>/dev/null
        aws dynamodb wait table-not-exists --table-name "$TABLE" --region $REGION
    fi
done

# 1. Conversations 테이블 생성
echo -e "${BLUE}Creating ${PREFIX}-conversations table...${NC}"
aws dynamodb create-table \
    --table-name "${PREFIX}-conversations" \
    --attribute-definitions \
        AttributeName=conversationId,AttributeType=S \
        AttributeName=userId,AttributeType=S \
        AttributeName=createdAt,AttributeType=S \
    --key-schema \
        AttributeName=conversationId,KeyType=HASH \
    --global-secondary-indexes \
        "[{
            \"IndexName\": \"userId-createdAt-index\",
            \"KeySchema\": [
                {\"AttributeName\":\"userId\",\"KeyType\":\"HASH\"},
                {\"AttributeName\":\"createdAt\",\"KeyType\":\"RANGE\"}
            ],
            \"Projection\": {\"ProjectionType\":\"ALL\"},
            \"ProvisionedThroughput\": {\"ReadCapacityUnits\":5,\"WriteCapacityUnits\":5}
        }]" \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region $REGION

echo -e "${GREEN}✅ Conversations table created${NC}"

# 2. Prompts 테이블 생성
echo -e "${BLUE}Creating ${PREFIX}-prompts table...${NC}"
aws dynamodb create-table \
    --table-name "${PREFIX}-prompts" \
    --attribute-definitions \
        AttributeName=promptId,AttributeType=S \
        AttributeName=userId,AttributeType=S \
        AttributeName=updatedAt,AttributeType=S \
    --key-schema \
        AttributeName=promptId,KeyType=HASH \
    --global-secondary-indexes \
        "[{
            \"IndexName\": \"userId-updatedAt-index\",
            \"KeySchema\": [
                {\"AttributeName\":\"userId\",\"KeyType\":\"HASH\"},
                {\"AttributeName\":\"updatedAt\",\"KeyType\":\"RANGE\"}
            ],
            \"Projection\": {\"ProjectionType\":\"ALL\"},
            \"ProvisionedThroughput\": {\"ReadCapacityUnits\":5,\"WriteCapacityUnits\":5}
        }]" \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region $REGION

echo -e "${GREEN}✅ Prompts table created${NC}"

# 3. Usage 테이블 생성
echo -e "${BLUE}Creating ${PREFIX}-usage table...${NC}"
aws dynamodb create-table \
    --table-name "${PREFIX}-usage" \
    --attribute-definitions \
        AttributeName=userId,AttributeType=S \
        AttributeName=usageDate,AttributeType=S \
        AttributeName="usageDate#engineType",AttributeType=S \
    --key-schema \
        AttributeName=userId,KeyType=HASH \
        AttributeName="usageDate#engineType",KeyType=RANGE \
    --global-secondary-indexes \
        "[{
            \"IndexName\": \"date-index\",
            \"KeySchema\": [
                {\"AttributeName\":\"usageDate\",\"KeyType\":\"HASH\"},
                {\"AttributeName\":\"userId\",\"KeyType\":\"RANGE\"}
            ],
            \"Projection\": {\"ProjectionType\":\"ALL\"},
            \"ProvisionedThroughput\": {\"ReadCapacityUnits\":5,\"WriteCapacityUnits\":5}
        }]" \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region $REGION

echo -e "${GREEN}✅ Usage table created${NC}"

# 4. WebSocket Connections 테이블 생성
echo -e "${BLUE}Creating ${PREFIX}-websocket-connections table...${NC}"
aws dynamodb create-table \
    --table-name "${PREFIX}-websocket-connections" \
    --attribute-definitions \
        AttributeName=connectionId,AttributeType=S \
    --key-schema \
        AttributeName=connectionId,KeyType=HASH \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region $REGION

echo -e "${GREEN}✅ WebSocket connections table created${NC}"

# 5. Files 테이블 생성
echo -e "${BLUE}Creating ${PREFIX}-files table...${NC}"
aws dynamodb create-table \
    --table-name "${PREFIX}-files" \
    --attribute-definitions \
        AttributeName=promptId,AttributeType=S \
        AttributeName=fileId,AttributeType=S \
    --key-schema \
        AttributeName=promptId,KeyType=HASH \
        AttributeName=fileId,KeyType=RANGE \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region $REGION

echo -e "${GREEN}✅ Files table created${NC}"

# 테이블 생성 확인
echo -e "${BLUE}Waiting for tables to be active...${NC}"
for TABLE in "${TABLES[@]}"; do
    aws dynamodb wait table-exists --table-name "$TABLE" --region $REGION
    echo -e "${GREEN}✅ $TABLE is active${NC}"
done

# 초기 데이터 삽입
echo -e "${BLUE}Inserting initial data...${NC}"

# Column 서비스용 초기 프롬프트 데이터
aws dynamodb put-item \
    --table-name "${PREFIX}-prompts" \
    --item '{
        "promptId": {"S": "COLUMN-C1"},
        "userId": {"S": "system"},
        "title": {"S": "칼럼 기본형"},
        "description": {"S": "칼럼 작성을 위한 기본 템플릿"},
        "instruction": {"S": "제공된 내용을 바탕으로 전문적인 칼럼을 작성하세요. 논리적 구조와 설득력 있는 논거를 포함해야 합니다."},
        "createdAt": {"S": "'$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")'"},
        "updatedAt": {"S": "'$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")'"},
        "isActive": {"BOOL": true}
    }' \
    --region $REGION

aws dynamodb put-item \
    --table-name "${PREFIX}-prompts" \
    --item '{
        "promptId": {"S": "COLUMN-C2"},
        "userId": {"S": "system"},
        "title": {"S": "오피니언 칼럼형"},
        "description": {"S": "시사 이슈에 대한 전문가 의견 제시"},
        "instruction": {"S": "현재 이슈에 대해 전문가적 시각으로 분석하고, 독창적인 관점과 해결책을 제시하는 오피니언 칼럼을 작성하세요."},
        "createdAt": {"S": "'$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")'"},
        "updatedAt": {"S": "'$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")'"},
        "isActive": {"BOOL": true}
    }' \
    --region $REGION

aws dynamodb put-item \
    --table-name "${PREFIX}-prompts" \
    --item '{
        "promptId": {"S": "COLUMN-C3"},
        "userId": {"S": "system"},
        "title": {"S": "경제 분석 칼럼형"},
        "description": {"S": "경제 동향 및 시장 분석 전문 칼럼"},
        "instruction": {"S": "경제 데이터와 시장 동향을 분석하여, 일반 독자가 이해하기 쉽게 설명하는 경제 분석 칼럼을 작성하세요."},
        "createdAt": {"S": "'$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")'"},
        "updatedAt": {"S": "'$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")'"},
        "isActive": {"BOOL": true}
    }' \
    --region $REGION

echo -e "${GREEN}✅ Initial data inserted${NC}"

echo ""
echo -e "${GREEN}=================================${NC}"
echo -e "${GREEN}✅ DYNAMODB SETUP COMPLETED!${NC}"
echo -e "${GREEN}=================================${NC}"
echo ""
echo -e "${BLUE}Created tables:${NC}"
for TABLE in "${TABLES[@]}"; do
    echo -e "  ${GREEN}✓${NC} $TABLE"
done
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Run ${BLUE}02-create-lambda-functions.sh${NC} to create Lambda functions"
echo -e "  2. Run ${BLUE}03-setup-api-gateway.sh${NC} to set up API Gateway"
echo -e "  3. Run ${BLUE}04-deploy-lambda.sh${NC} to deploy Lambda code"