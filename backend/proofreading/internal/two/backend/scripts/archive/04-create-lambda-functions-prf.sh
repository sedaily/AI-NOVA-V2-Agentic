#!/bin/bash

# 색상 설정
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 설정
REGION="us-east-1"
PROJECT_PREFIX="nx-wt-prf"
RUNTIME="python3.11"
TIMEOUT=30
MEMORY_SIZE=512

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}   Lambda 함수 생성 - ${PROJECT_PREFIX}   ${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# AWS 계정 ID 가져오기
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✅ AWS Account ID: $ACCOUNT_ID${NC}"

# Lambda 실행 역할 ARN
LAMBDA_ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/lambda-execution-role"

# Lambda 실행 역할 확인 및 생성
echo -e "\n${BLUE}1. Lambda 실행 역할 확인...${NC}"
aws iam get-role --role-name lambda-execution-role --region $REGION > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Lambda 실행 역할이 없습니다. 생성 중...${NC}"
    
    # Trust policy 생성
    cat > trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
    
    # 역할 생성
    aws iam create-role \
        --role-name lambda-execution-role \
        --assume-role-policy-document file://trust-policy.json \
        --region $REGION > /dev/null 2>&1
    
    # 정책 연결
    aws iam attach-role-policy \
        --role-name lambda-execution-role \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
        --region $REGION > /dev/null 2>&1
    
    aws iam attach-role-policy \
        --role-name lambda-execution-role \
        --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess \
        --region $REGION > /dev/null 2>&1
    
    aws iam attach-role-policy \
        --role-name lambda-execution-role \
        --policy-arn arn:aws:iam::aws:policy/AmazonAPIGatewayInvokeFullAccess \
        --region $REGION > /dev/null 2>&1
    
    aws iam attach-role-policy \
        --role-name lambda-execution-role \
        --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess \
        --region $REGION > /dev/null 2>&1
    
    # Bedrock 정책 생성
    cat > bedrock-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": "*"
        }
    ]
}
EOF
    
    aws iam put-role-policy \
        --role-name lambda-execution-role \
        --policy-name BedrockInvokePolicy \
        --policy-document file://bedrock-policy.json \
        --region $REGION > /dev/null 2>&1
    
    rm -f trust-policy.json bedrock-policy.json
    
    echo -e "${GREEN}✅ Lambda 실행 역할 생성 완료${NC}"
    
    # 역할이 전파될 때까지 대기
    echo -e "${YELLOW}역할 전파 대기 중 (10초)...${NC}"
    sleep 10
else
    echo -e "${GREEN}✅ Lambda 실행 역할 확인 완료${NC}"
fi

# 스크립트 디렉토리
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
cd $BACKEND_DIR

# 초기 배포 패키지 생성
echo -e "\n${BLUE}2. 초기 배포 패키지 생성 중...${NC}"
echo "def handler(event, context): return {'statusCode': 200, 'body': 'OK'}" > lambda_function.py
zip init_lambda.zip lambda_function.py > /dev/null 2>&1
rm lambda_function.py

# Lambda 함수 생성 함수
create_lambda_function() {
    local function_name=$1
    local handler=$2
    local description=$3
    
    # 함수 존재 확인
    aws lambda get-function --function-name $function_name --region $REGION > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "  ${YELLOW}⚠${NC} $function_name: 이미 존재함 (건너뛰기)"
    else
        # 함수 생성
        aws lambda create-function \
            --function-name $function_name \
            --runtime $RUNTIME \
            --role $LAMBDA_ROLE_ARN \
            --handler $handler \
            --zip-file fileb://init_lambda.zip \
            --timeout $TIMEOUT \
            --memory-size $MEMORY_SIZE \
            --description "$description" \
            --environment "Variables={REGION=$REGION}" \
            --region $REGION > /dev/null 2>&1
        
        if [ $? -eq 0 ]; then
            echo -e "  ${GREEN}✓${NC} $function_name: 생성 완료"
        else
            echo -e "  ${RED}✗${NC} $function_name: 생성 실패"
        fi
    fi
}

# Lambda 함수 생성
echo -e "\n${BLUE}3. Lambda 함수 생성 중...${NC}"

# REST API Lambda 함수
echo -e "\n${CYAN}📌 REST API Lambda 함수${NC}"
create_lambda_function \
    "${PROJECT_PREFIX}-conversation-api" \
    "handlers.api.conversation.handler" \
    "Conversation management API for $PROJECT_PREFIX"

create_lambda_function \
    "${PROJECT_PREFIX}-prompt-crud" \
    "handlers.api.prompt.handler" \
    "Prompt CRUD operations for $PROJECT_PREFIX"

create_lambda_function \
    "${PROJECT_PREFIX}-usage-handler" \
    "handlers.api.usage.handler" \
    "Usage tracking handler for $PROJECT_PREFIX"

# WebSocket Lambda 함수
echo -e "\n${CYAN}📌 WebSocket Lambda 함수${NC}"
create_lambda_function \
    "${PROJECT_PREFIX}-websocket-connect" \
    "handlers.websocket.connect.handler" \
    "WebSocket connection handler for $PROJECT_PREFIX"

create_lambda_function \
    "${PROJECT_PREFIX}-websocket-disconnect" \
    "handlers.websocket.disconnect.handler" \
    "WebSocket disconnection handler for $PROJECT_PREFIX"

create_lambda_function \
    "${PROJECT_PREFIX}-websocket-message" \
    "handlers.websocket.message.handler" \
    "WebSocket message handler for $PROJECT_PREFIX"

# 정리
rm -f init_lambda.zip

# 함수 상태 확인
echo -e "\n${BLUE}4. Lambda 함수 상태 확인${NC}"
LAMBDA_FUNCTIONS=(
    "${PROJECT_PREFIX}-conversation-api"
    "${PROJECT_PREFIX}-prompt-crud"
    "${PROJECT_PREFIX}-usage-handler"
    "${PROJECT_PREFIX}-websocket-connect"
    "${PROJECT_PREFIX}-websocket-disconnect"
    "${PROJECT_PREFIX}-websocket-message"
)

for func in "${LAMBDA_FUNCTIONS[@]}"; do
    STATUS=$(aws lambda get-function --function-name $func --region $REGION --query 'Configuration.State' --output text 2>/dev/null)
    
    if [ -n "$STATUS" ]; then
        if [ "$STATUS" = "Active" ]; then
            echo -e "  ${GREEN}✓${NC} $func: $STATUS"
        else
            echo -e "  ${YELLOW}⚠${NC} $func: $STATUS"
        fi
    else
        echo -e "  ${RED}✗${NC} $func: 함수가 존재하지 않음"
    fi
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   ✅ Lambda 함수 생성 완료!   ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${CYAN}📌 다음 단계:${NC}"
echo -e "  1. Lambda 함수 코드 배포 (99-deploy-lambda.sh 실행)"
echo -e "  2. API Gateway Lambda 권한 설정 (02-setup-lambda-permissions-prf.sh 재실행)"
echo -e "  3. WebSocket Lambda 권한 설정"
echo ""