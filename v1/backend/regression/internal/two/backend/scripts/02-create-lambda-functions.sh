#!/bin/bash

# 색상 설정
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}SEDAILY-COLUMN LAMBDA SETUP${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""

# 설정
REGION="us-east-1"
PREFIX="sedaily-column"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
RUNTIME="python3.9"

echo -e "${YELLOW}AWS Account ID: ${ACCOUNT_ID}${NC}"
echo -e "${YELLOW}Region: ${REGION}${NC}"
echo ""

# ====================================
# IAM 역할 생성
# ====================================
echo -e "${BLUE}Creating IAM roles...${NC}"

# Lambda 실행 역할 생성
ROLE_NAME="${PREFIX}-lambda-execution-role"
echo -e "${YELLOW}Creating IAM role: ${ROLE_NAME}${NC}"

# Trust policy
TRUST_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": [
          "lambda.amazonaws.com",
          "apigateway.amazonaws.com"
        ]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}'

# 역할 생성
aws iam create-role \
    --role-name "$ROLE_NAME" \
    --assume-role-policy-document "$TRUST_POLICY" \
    --region $REGION 2>/dev/null || echo -e "${YELLOW}Role already exists${NC}"

# 기본 Lambda 실행 정책 연결
aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole" \
    2>/dev/null

# DynamoDB 전체 액세스 정책 생성 및 연결
POLICY_NAME="${PREFIX}-dynamodb-policy"
echo -e "${YELLOW}Creating DynamoDB policy: ${POLICY_NAME}${NC}"

DYNAMODB_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:BatchGetItem",
        "dynamodb:BatchWriteItem",
        "dynamodb:DescribeTable",
        "dynamodb:DescribeStream",
        "dynamodb:GetRecords",
        "dynamodb:GetShardIterator",
        "dynamodb:ListStreams"
      ],
      "Resource": [
        "arn:aws:dynamodb:'$REGION':'$ACCOUNT_ID':table/'$PREFIX'-*",
        "arn:aws:dynamodb:'$REGION':'$ACCOUNT_ID':table/'$PREFIX'-*/index/*"
      ]
    }
  ]
}'

aws iam create-policy \
    --policy-name "$POLICY_NAME" \
    --policy-document "$DYNAMODB_POLICY" \
    --region $REGION 2>/dev/null || echo -e "${YELLOW}Policy already exists${NC}"

aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}" \
    2>/dev/null

# Bedrock 액세스 정책
BEDROCK_POLICY_NAME="${PREFIX}-bedrock-policy"
echo -e "${YELLOW}Creating Bedrock policy: ${BEDROCK_POLICY_NAME}${NC}"

BEDROCK_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:'$REGION':'$ACCOUNT_ID':*"
    }
  ]
}'

aws iam create-policy \
    --policy-name "$BEDROCK_POLICY_NAME" \
    --policy-document "$BEDROCK_POLICY" \
    --region $REGION 2>/dev/null || echo -e "${YELLOW}Policy already exists${NC}"

aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "arn:aws:iam::${ACCOUNT_ID}:policy/${BEDROCK_POLICY_NAME}" \
    2>/dev/null

# API Gateway 실행 정책
APIGATEWAY_POLICY_NAME="${PREFIX}-apigateway-policy"
echo -e "${YELLOW}Creating API Gateway policy: ${APIGATEWAY_POLICY_NAME}${NC}"

APIGATEWAY_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "execute-api:ManageConnections",
        "execute-api:Invoke"
      ],
      "Resource": "arn:aws:execute-api:'$REGION':'$ACCOUNT_ID':*"
    }
  ]
}'

aws iam create-policy \
    --policy-name "$APIGATEWAY_POLICY_NAME" \
    --policy-document "$APIGATEWAY_POLICY" \
    --region $REGION 2>/dev/null || echo -e "${YELLOW}Policy already exists${NC}"

aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "arn:aws:iam::${ACCOUNT_ID}:policy/${APIGATEWAY_POLICY_NAME}" \
    2>/dev/null

# 역할 ARN 가져오기
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"
echo -e "${GREEN}✅ IAM Role created: ${ROLE_ARN}${NC}"

# 역할이 생성될 때까지 대기
sleep 10

# ====================================
# Lambda 함수 생성
# ====================================
echo ""
echo -e "${BLUE}Creating Lambda functions...${NC}"

# 임시 배포 패키지 생성 (빈 함수)
mkdir -p /tmp/lambda-deploy
cat > /tmp/lambda-deploy/lambda_function.py << 'EOF'
def handler(event, context):
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
        },
        'body': '{"message": "Lambda function placeholder"}'
    }
EOF

cd /tmp/lambda-deploy
zip -q deployment.zip lambda_function.py

# Lambda 함수 정의
declare -A LAMBDA_FUNCTIONS=(
    ["${PREFIX}-conversation-api"]="512,30"
    ["${PREFIX}-prompt-crud"]="512,30"
    ["${PREFIX}-usage-handler"]="256,30"
    ["${PREFIX}-websocket-message"]="1024,300"
    ["${PREFIX}-websocket-connect"]="256,30"
    ["${PREFIX}-websocket-disconnect"]="256,30"
)

# 각 Lambda 함수 생성
for FUNCTION_NAME in "${!LAMBDA_FUNCTIONS[@]}"; do
    IFS=',' read -r MEMORY TIMEOUT <<< "${LAMBDA_FUNCTIONS[$FUNCTION_NAME]}"

    echo -e "${YELLOW}Creating Lambda function: ${FUNCTION_NAME}${NC}"
    echo -e "  Memory: ${MEMORY}MB, Timeout: ${TIMEOUT}s"

    # 환경 변수 설정
    ENV_VARS='{"Variables":{'
    ENV_VARS+='"AWS_REGION":"'$REGION'",'
    ENV_VARS+='"CONVERSATIONS_TABLE":"'$PREFIX'-conversations",'
    ENV_VARS+='"PROMPTS_TABLE":"'$PREFIX'-prompts",'
    ENV_VARS+='"USAGE_TABLE":"'$PREFIX'-usage",'
    ENV_VARS+='"WEBSOCKET_TABLE":"'$PREFIX'-websocket-connections",'
    ENV_VARS+='"FILES_TABLE":"'$PREFIX'-files",'
    ENV_VARS+='"BEDROCK_MODEL_ID":"anthropic.claude-3-sonnet-20240229-v1:0",'
    ENV_VARS+='"LOG_LEVEL":"INFO"'
    ENV_VARS+='}}'

    aws lambda create-function \
        --function-name "$FUNCTION_NAME" \
        --runtime "$RUNTIME" \
        --role "$ROLE_ARN" \
        --handler "lambda_function.handler" \
        --memory-size "$MEMORY" \
        --timeout "$TIMEOUT" \
        --environment "$ENV_VARS" \
        --zip-file "fileb:///tmp/lambda-deploy/deployment.zip" \
        --region $REGION 2>/dev/null

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Created: ${FUNCTION_NAME}${NC}"
    else
        echo -e "${YELLOW}⚠️  Function already exists or error: ${FUNCTION_NAME}${NC}"
        # 함수가 이미 있으면 환경 변수 업데이트
        aws lambda update-function-configuration \
            --function-name "$FUNCTION_NAME" \
            --environment "$ENV_VARS" \
            --memory-size "$MEMORY" \
            --timeout "$TIMEOUT" \
            --region $REGION 2>/dev/null
        echo -e "${GREEN}✅ Updated configuration: ${FUNCTION_NAME}${NC}"
    fi
done

# 정리
rm -rf /tmp/lambda-deploy

echo ""
echo -e "${GREEN}=================================${NC}"
echo -e "${GREEN}✅ LAMBDA FUNCTIONS CREATED!${NC}"
echo -e "${GREEN}=================================${NC}"
echo ""
echo -e "${BLUE}Created Lambda functions:${NC}"
for FUNCTION_NAME in "${!LAMBDA_FUNCTIONS[@]}"; do
    echo -e "  ${GREEN}✓${NC} $FUNCTION_NAME"
done
echo ""
echo -e "${BLUE}IAM Resources:${NC}"
echo -e "  ${GREEN}✓${NC} Role: $ROLE_NAME"
echo -e "  ${GREEN}✓${NC} Policies: DynamoDB, Bedrock, API Gateway"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Run ${BLUE}03-setup-api-gateway.sh${NC} to create API Gateway"
echo -e "  2. Run ${BLUE}04-setup-websocket.sh${NC} to create WebSocket API"
echo -e "  3. Run ${BLUE}05-deploy-lambda.sh${NC} to deploy actual Lambda code"