#!/bin/bash

# DynamoDB 테이블 생성 스크립트
# Usage: ./create-tables.sh [region]

set -e

REGION=${1:-us-east-1}

# 색상 설정
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== DynamoDB 테이블 생성 시작 ===${NC}"
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

# 테이블 존재 확인 함수
check_table_exists() {
    local table_name=$1
    aws dynamodb describe-table --table-name "$table_name" --region "$REGION" &> /dev/null
}

# 테이블 생성 대기 함수
wait_for_table() {
    local table_name=$1
    echo -e "${YELLOW}  테이블 생성 대기 중: $table_name${NC}"
    aws dynamodb wait table-exists --table-name "$table_name" --region "$REGION"
    echo -e "${GREEN}  ✅ $table_name 테이블 생성 완료${NC}"
}

# 1. Prompts 테이블 생성
echo -e "\n${BLUE}📝 Prompts 테이블 생성 중...${NC}"
TABLE_NAME="sedaily-column-prompts"

if check_table_exists "$TABLE_NAME"; then
    echo -e "${YELLOW}⚠️  $TABLE_NAME 테이블이 이미 존재합니다.${NC}"
else
    aws dynamodb create-table \
        --table-name "$TABLE_NAME" \
        --attribute-definitions \
            AttributeName=promptId,AttributeType=S \
        --key-schema \
            AttributeName=promptId,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION" > /dev/null
    
    wait_for_table "$TABLE_NAME"
fi

# 2. Files 테이블 생성
echo -e "\n${BLUE}📁 Files 테이블 생성 중...${NC}"
TABLE_NAME="sedaily-column-files"

if check_table_exists "$TABLE_NAME"; then
    echo -e "${YELLOW}⚠️  $TABLE_NAME 테이블이 이미 존재합니다.${NC}"
else
    aws dynamodb create-table \
        --table-name "$TABLE_NAME" \
        --attribute-definitions \
            AttributeName=promptId,AttributeType=S \
            AttributeName=fileId,AttributeType=S \
        --key-schema \
            AttributeName=promptId,KeyType=HASH \
            AttributeName=fileId,KeyType=RANGE \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION" > /dev/null
    
    wait_for_table "$TABLE_NAME"
fi

# 3. Conversations 테이블 생성
echo -e "\n${BLUE}💬 Conversations 테이블 생성 중...${NC}"
TABLE_NAME="sedaily-column-conversations"

if check_table_exists "$TABLE_NAME"; then
    echo -e "${YELLOW}⚠️  $TABLE_NAME 테이블이 이미 존재합니다.${NC}"
else
    aws dynamodb create-table \
        --table-name "$TABLE_NAME" \
        --attribute-definitions \
            AttributeName=conversationId,AttributeType=S \
            AttributeName=userId,AttributeType=S \
            AttributeName=createdAt,AttributeType=S \
        --key-schema \
            AttributeName=conversationId,KeyType=HASH \
        --global-secondary-indexes \
            IndexName=userId-createdAt-index,KeySchema=[{AttributeName=userId,KeyType=HASH},{AttributeName=createdAt,KeyType=RANGE}],Projection={ProjectionType=ALL} \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION" > /dev/null
    
    wait_for_table "$TABLE_NAME"
fi

# 4. Usage 테이블 생성
echo -e "\n${BLUE}📊 Usage 테이블 생성 중...${NC}"
TABLE_NAME="sedaily-column-usage"

if check_table_exists "$TABLE_NAME"; then
    echo -e "${YELLOW}⚠️  $TABLE_NAME 테이블이 이미 존재합니다.${NC}"
else
    aws dynamodb create-table \
        --table-name "$TABLE_NAME" \
        --attribute-definitions \
            AttributeName=PK,AttributeType=S \
            AttributeName=SK,AttributeType=S \
        --key-schema \
            AttributeName=PK,KeyType=HASH \
            AttributeName=SK,KeyType=RANGE \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION" > /dev/null
    
    wait_for_table "$TABLE_NAME"
fi

# 5. 테이블 목록 확인
echo -e "\n${BLUE}📋 생성된 테이블 목록:${NC}"
aws dynamodb list-tables --region "$REGION" --query 'TableNames[?starts_with(@, `sedaily-column`)]' --output table

# 6. 테이블 상태 확인
echo -e "\n${BLUE}🔍 테이블 상태 확인:${NC}"
TABLES=(
    "sedaily-column-prompts"
    "sedaily-column-files"
    "sedaily-column-conversations"
    "sedaily-column-usage"
)

for TABLE in "${TABLES[@]}"; do
    STATUS=$(aws dynamodb describe-table --table-name "$TABLE" --region "$REGION" --query 'Table.TableStatus' --output text 2>/dev/null || echo "NOT_FOUND")
    if [ "$STATUS" = "ACTIVE" ]; then
        echo -e "${GREEN}✅ $TABLE: $STATUS${NC}"
    else
        echo -e "${RED}❌ $TABLE: $STATUS${NC}"
    fi
done

# 7. 샘플 데이터 삽입 (선택사항)
echo -e "\n${BLUE}💾 샘플 데이터 삽입 여부를 선택하세요:${NC}"
read -p "샘플 데이터를 삽입하시겠습니까? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}📝 샘플 프롬프트 데이터 삽입 중...${NC}"
    
    # 샘플 프롬프트 데이터
    aws dynamodb put-item \
        --table-name "sedaily-column-prompts" \
        --item '{
            "promptId": {"S": "C1"},
            "description": {"S": "일반 대화형 AI"},
            "instruction": {"S": "사용자와 자연스럽고 도움이 되는 대화를 나누세요. 정확하고 유용한 정보를 제공하되, 모르는 것은 모른다고 솔직히 말하세요."},
            "createdAt": {"S": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"},
            "updatedAt": {"S": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}
        }' \
        --region "$REGION"
    
    aws dynamodb put-item \
        --table-name "sedaily-column-prompts" \
        --item '{
            "promptId": {"S": "C2"},
            "description": {"S": "코딩 도우미 AI"},
            "instruction": {"S": "프로그래밍 관련 질문에 대해 정확하고 실용적인 답변을 제공하세요. 코드 예시를 포함하고, 모범 사례를 제안하세요."},
            "createdAt": {"S": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"},
            "updatedAt": {"S": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}
        }' \
        --region "$REGION"
    
    aws dynamodb put-item \
        --table-name "sedaily-column-prompts" \
        --item '{
            "promptId": {"S": "C3"},
            "description": {"S": "창작 도우미 AI"},
            "instruction": {"S": "창의적인 글쓰기와 아이디어 발상을 도와주세요. 사용자의 창작 의도를 파악하고 구체적이고 실용적인 제안을 제공하세요."},
            "createdAt": {"S": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"},
            "updatedAt": {"S": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}
        }' \
        --region "$REGION"
    
    echo -e "${GREEN}✅ 샘플 데이터 삽입 완료${NC}"
fi

# 8. 완료 메시지
echo -e "\n${GREEN}🎉 DynamoDB 테이블 생성 완료!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "🌍 Region: ${YELLOW}$REGION${NC}"
echo -e "📊 생성된 테이블: ${YELLOW}4개${NC}"
echo -e "💰 Billing Mode: ${YELLOW}PAY_PER_REQUEST${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 9. 다음 단계 안내
echo -e "\n${BLUE}📋 다음 단계:${NC}"
echo -e "1. Lambda 함수 배포: ${YELLOW}./deploy.sh${NC}"
echo -e "2. API Gateway 설정: ${YELLOW}./setup-api-routes.sh${NC}"
echo -e "3. API 테스트: ${YELLOW}./test-api.sh${NC}"

# 10. 모니터링 링크
echo -e "\n${BLUE}📊 DynamoDB 콘솔:${NC}"
echo -e "https://console.aws.amazon.com/dynamodb/home?region=$REGION#tables:"

echo -e "\n${GREEN}테이블 생성이 성공적으로 완료되었습니다! 🚀${NC}"