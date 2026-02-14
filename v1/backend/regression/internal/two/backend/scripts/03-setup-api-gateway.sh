#!/bin/bash

# 색상 설정
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}SEDAILY-COLUMN REST API GATEWAY SETUP${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""

# 설정
REGION="us-east-1"
PREFIX="sedaily-column"
STAGE_NAME="prod"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo -e "${YELLOW}Creating new REST API for ${PREFIX}${NC}"
echo -e "${YELLOW}Region: ${REGION}${NC}"
echo ""

# REST API 생성
echo -e "${BLUE}Creating REST API...${NC}"
API_NAME="${PREFIX}-rest-api"

# API 생성
API_ID=$(aws apigateway create-rest-api \
    --name "$API_NAME" \
    --description "Seoul Economic Daily Column Service REST API" \
    --endpoint-configuration types=REGIONAL \
    --region $REGION \
    --query 'id' \
    --output text)

echo -e "${GREEN}✅ REST API created: ${API_ID}${NC}"

# Root 리소스 ID 가져오기
ROOT_ID=$(aws apigateway get-resources \
    --rest-api-id $API_ID \
    --region $REGION \
    --query "items[?path=='/'].id" \
    --output text)

echo -e "${GREEN}✅ Root Resource ID: ${ROOT_ID}${NC}"

# ====================================
# 리소스 및 메소드 생성 함수
# ====================================
create_resource_with_methods() {
    local PARENT_ID=$1
    local PATH_PART=$2
    local LAMBDA_FUNCTION=$3
    local METHODS=$4

    echo -e "${YELLOW}Creating resource: /${PATH_PART}${NC}"

    # 리소스 생성
    RESOURCE_ID=$(aws apigateway create-resource \
        --rest-api-id $API_ID \
        --parent-id $PARENT_ID \
        --path-part "$PATH_PART" \
        --region $REGION \
        --query 'id' \
        --output text)

    echo -e "${GREEN}  ✓ Resource created: ${RESOURCE_ID}${NC}"

    # Lambda ARN
    LAMBDA_ARN="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${LAMBDA_FUNCTION}"

    # 각 HTTP 메소드 설정
    IFS=',' read -ra METHOD_ARRAY <<< "$METHODS"
    for METHOD in "${METHOD_ARRAY[@]}"; do
        echo -e "${YELLOW}  Setting up ${METHOD} method...${NC}"

        # 메소드 생성
        aws apigateway put-method \
            --rest-api-id $API_ID \
            --resource-id $RESOURCE_ID \
            --http-method $METHOD \
            --authorization-type NONE \
            --region $REGION >/dev/null 2>&1

        # Lambda 통합 설정
        aws apigateway put-integration \
            --rest-api-id $API_ID \
            --resource-id $RESOURCE_ID \
            --http-method $METHOD \
            --type AWS_PROXY \
            --integration-http-method POST \
            --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" \
            --region $REGION >/dev/null 2>&1

        # Lambda 권한 부여
        STATEMENT_ID="${API_ID}-${METHOD}-${PATH_PART}"
        aws lambda add-permission \
            --function-name $LAMBDA_FUNCTION \
            --statement-id "$STATEMENT_ID" \
            --action lambda:InvokeFunction \
            --principal apigateway.amazonaws.com \
            --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/${METHOD}/${PATH_PART}" \
            --region $REGION 2>/dev/null

        echo -e "${GREEN}    ✓ ${METHOD} configured${NC}"
    done

    # OPTIONS 메소드 (CORS)
    echo -e "${YELLOW}  Setting up OPTIONS (CORS)...${NC}"

    aws apigateway put-method \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --authorization-type NONE \
        --region $REGION >/dev/null 2>&1

    aws apigateway put-method-response \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{"method.response.header.Access-Control-Allow-Headers":true,"method.response.header.Access-Control-Allow-Methods":true,"method.response.header.Access-Control-Allow-Origin":true}' \
        --region $REGION >/dev/null 2>&1

    aws apigateway put-integration \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --type MOCK \
        --request-templates '{"application/json":"{\"statusCode\": 200}"}' \
        --region $REGION >/dev/null 2>&1

    aws apigateway put-integration-response \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{"method.response.header.Access-Control-Allow-Headers":"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'","method.response.header.Access-Control-Allow-Methods":"'"'"'GET,POST,PUT,DELETE,OPTIONS'"'"'","method.response.header.Access-Control-Allow-Origin":"'"'"'*'"'"'"}' \
        --region $REGION >/dev/null 2>&1

    echo -e "${GREEN}    ✓ CORS configured${NC}"
    echo $RESOURCE_ID
}

# ====================================
# API 리소스 생성
# ====================================
echo ""
echo -e "${BLUE}Creating API resources...${NC}"

# /prompts 리소스
PROMPTS_ID=$(create_resource_with_methods \
    "$ROOT_ID" \
    "prompts" \
    "${PREFIX}-prompt-crud" \
    "GET,POST")

# /prompts/{promptId} 리소스
echo -e "${YELLOW}Creating resource: /prompts/{promptId}${NC}"
PROMPT_ID_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $PROMPTS_ID \
    --path-part "{promptId}" \
    --region $REGION \
    --query 'id' \
    --output text)

# promptId 파라미터가 있는 메소드 설정
for METHOD in GET PUT DELETE; do
    aws apigateway put-method \
        --rest-api-id $API_ID \
        --resource-id $PROMPT_ID_RESOURCE \
        --http-method $METHOD \
        --authorization-type NONE \
        --request-parameters "method.request.path.promptId=true" \
        --region $REGION >/dev/null 2>&1

    aws apigateway put-integration \
        --rest-api-id $API_ID \
        --resource-id $PROMPT_ID_RESOURCE \
        --http-method $METHOD \
        --type AWS_PROXY \
        --integration-http-method POST \
        --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${PREFIX}-prompt-crud/invocations" \
        --region $REGION >/dev/null 2>&1
done

echo -e "${GREEN}  ✓ /prompts/{promptId} configured${NC}"

# /conversations 리소스
CONVERSATIONS_ID=$(create_resource_with_methods \
    "$ROOT_ID" \
    "conversations" \
    "${PREFIX}-conversation-api" \
    "GET,POST")

# /conversations/{conversationId} 리소스
echo -e "${YELLOW}Creating resource: /conversations/{conversationId}${NC}"
CONVERSATION_ID_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $CONVERSATIONS_ID \
    --path-part "{conversationId}" \
    --region $REGION \
    --query 'id' \
    --output text)

for METHOD in GET PUT DELETE; do
    aws apigateway put-method \
        --rest-api-id $API_ID \
        --resource-id $CONVERSATION_ID_RESOURCE \
        --http-method $METHOD \
        --authorization-type NONE \
        --request-parameters "method.request.path.conversationId=true" \
        --region $REGION >/dev/null 2>&1

    aws apigateway put-integration \
        --rest-api-id $API_ID \
        --resource-id $CONVERSATION_ID_RESOURCE \
        --http-method $METHOD \
        --type AWS_PROXY \
        --integration-http-method POST \
        --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${PREFIX}-conversation-api/invocations" \
        --region $REGION >/dev/null 2>&1
done

echo -e "${GREEN}  ✓ /conversations/{conversationId} configured${NC}"

# /usage 리소스
USAGE_ID=$(create_resource_with_methods \
    "$ROOT_ID" \
    "usage" \
    "${PREFIX}-usage-handler" \
    "GET,POST")

# /usage/{userId} 리소스
echo -e "${YELLOW}Creating resource: /usage/{userId}${NC}"
USER_ID_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $USAGE_ID \
    --path-part "{userId}" \
    --region $REGION \
    --query 'id' \
    --output text)

for METHOD in GET PUT DELETE; do
    aws apigateway put-method \
        --rest-api-id $API_ID \
        --resource-id $USER_ID_RESOURCE \
        --http-method $METHOD \
        --authorization-type NONE \
        --request-parameters "method.request.path.userId=true" \
        --region $REGION >/dev/null 2>&1

    aws apigateway put-integration \
        --rest-api-id $API_ID \
        --resource-id $USER_ID_RESOURCE \
        --http-method $METHOD \
        --type AWS_PROXY \
        --integration-http-method POST \
        --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${PREFIX}-usage-handler/invocations" \
        --region $REGION >/dev/null 2>&1
done

echo -e "${GREEN}  ✓ /usage/{userId} configured${NC}"

# ====================================
# API 배포
# ====================================
echo ""
echo -e "${BLUE}Deploying API...${NC}"

aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name $STAGE_NAME \
    --stage-description "Production stage for ${PREFIX}" \
    --description "Initial deployment" \
    --region $REGION >/dev/null

echo -e "${GREEN}✅ API deployed to stage: ${STAGE_NAME}${NC}"

# API URL 출력
API_URL="https://${API_ID}.execute-api.${REGION}.amazonaws.com/${STAGE_NAME}"

echo ""
echo -e "${GREEN}=================================${NC}"
echo -e "${GREEN}✅ REST API GATEWAY CREATED!${NC}"
echo -e "${GREEN}=================================${NC}"
echo ""
echo -e "${BLUE}API Details:${NC}"
echo -e "  ${GREEN}✓${NC} API ID: ${API_ID}"
echo -e "  ${GREEN}✓${NC} API URL: ${API_URL}"
echo ""
echo -e "${BLUE}Endpoints:${NC}"
echo -e "  ${GREEN}✓${NC} Prompts:       ${API_URL}/prompts"
echo -e "  ${GREEN}✓${NC} Conversations: ${API_URL}/conversations"
echo -e "  ${GREEN}✓${NC} Usage:         ${API_URL}/usage"
echo ""
echo -e "${YELLOW}Save this API ID for frontend configuration:${NC}"
echo -e "${GREEN}${API_ID}${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Run ${BLUE}04-setup-websocket.sh${NC} to create WebSocket API"
echo -e "  2. Run ${BLUE}05-deploy-lambda.sh${NC} to deploy Lambda code"