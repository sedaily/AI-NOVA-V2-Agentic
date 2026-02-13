#!/bin/bash

# API Gateway 라우트 설정 스크립트
# usage와 conversation 엔드포인트 추가

# 색상 설정
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[91m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}API GATEWAY ROUTES SETUP${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""

# API Gateway ID
API_ID="o96dgrd6ji"
REGION="us-east-1"

# Lambda 함수 ARN
USAGE_LAMBDA_ARN="arn:aws:lambda:${REGION}:887078546492:function:nx-tt-dev-ver3-usage-handler"
CONVERSATION_LAMBDA_ARN="arn:aws:lambda:${REGION}:887078546492:function:nx-tt-dev-ver3-conversation-api"

echo -e "${YELLOW}API Gateway ID: ${API_ID}${NC}"
echo ""

# 1. Usage Handler Integration 생성
echo -e "${BLUE}Creating integrations for usage-handler...${NC}"

USAGE_INTEGRATION_ID=$(aws apigatewayv2 create-integration \
    --api-id $API_ID \
    --integration-type AWS_PROXY \
    --integration-method POST \
    --integration-uri $USAGE_LAMBDA_ARN \
    --payload-format-version 2.0 \
    --region $REGION \
    --query 'IntegrationId' \
    --output text 2>/dev/null)

if [ -n "$USAGE_INTEGRATION_ID" ]; then
    echo -e "${GREEN}✅ Usage integration created: ${USAGE_INTEGRATION_ID}${NC}"
else
    # Integration이 이미 있을 수 있으므로 조회
    USAGE_INTEGRATION_ID=$(aws apigatewayv2 get-integrations \
        --api-id $API_ID \
        --region $REGION \
        --query "Items[?IntegrationUri=='${USAGE_LAMBDA_ARN}'].IntegrationId" \
        --output text | head -1)
    echo -e "${YELLOW}ℹ️  Using existing usage integration: ${USAGE_INTEGRATION_ID}${NC}"
fi

# 2. Conversation Handler Integration 생성
echo -e "${BLUE}Creating integrations for conversation-api...${NC}"

CONV_INTEGRATION_ID=$(aws apigatewayv2 create-integration \
    --api-id $API_ID \
    --integration-type AWS_PROXY \
    --integration-method POST \
    --integration-uri $CONVERSATION_LAMBDA_ARN \
    --payload-format-version 2.0 \
    --region $REGION \
    --query 'IntegrationId' \
    --output text 2>/dev/null)

if [ -n "$CONV_INTEGRATION_ID" ]; then
    echo -e "${GREEN}✅ Conversation integration created: ${CONV_INTEGRATION_ID}${NC}"
else
    # Integration이 이미 있을 수 있으므로 조회
    CONV_INTEGRATION_ID=$(aws apigatewayv2 get-integrations \
        --api-id $API_ID \
        --region $REGION \
        --query "Items[?IntegrationUri=='${CONVERSATION_LAMBDA_ARN}'].IntegrationId" \
        --output text | head -1)
    echo -e "${YELLOW}ℹ️  Using existing conversation integration: ${CONV_INTEGRATION_ID}${NC}"
fi

echo ""
echo -e "${BLUE}Creating routes...${NC}"

# Usage Routes
USAGE_ROUTES=(
    "GET /usage"
    "GET /usage/{userId}"
    "POST /usage"
    "PUT /usage/{userId}"
    "DELETE /usage/{userId}"
)

for ROUTE in "${USAGE_ROUTES[@]}"; do
    METHOD=$(echo $ROUTE | cut -d' ' -f1)
    PATH=$(echo $ROUTE | cut -d' ' -f2)
    
    echo -e "${YELLOW}Creating route: ${METHOD} ${PATH}${NC}"
    
    aws apigatewayv2 create-route \
        --api-id $API_ID \
        --route-key "$ROUTE" \
        --target "integrations/${USAGE_INTEGRATION_ID}" \
        --region $REGION \
        --output text > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}  ✅ Route created${NC}"
    else
        echo -e "${YELLOW}  ⚠️  Route might already exist${NC}"
    fi
done

# Conversation Routes
CONVERSATION_ROUTES=(
    "GET /conversations"
    "GET /conversations/{conversationId}"
    "POST /conversations"
    "PUT /conversations/{conversationId}"
    "PATCH /conversations/{conversationId}"
    "DELETE /conversations/{conversationId}"
    "GET /users/{userId}/conversations"
    "POST /conversations/{conversationId}/messages"
    "GET /conversations/{conversationId}/messages"
)

for ROUTE in "${CONVERSATION_ROUTES[@]}"; do
    METHOD=$(echo $ROUTE | cut -d' ' -f1)
    PATH=$(echo $ROUTE | cut -d' ' -f2)
    
    echo -e "${YELLOW}Creating route: ${METHOD} ${PATH}${NC}"
    
    aws apigatewayv2 create-route \
        --api-id $API_ID \
        --route-key "$ROUTE" \
        --target "integrations/${CONV_INTEGRATION_ID}" \
        --region $REGION \
        --output text > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}  ✅ Route created${NC}"
    else
        echo -e "${YELLOW}  ⚠️  Route might already exist${NC}"
    fi
done

# Lambda 권한 추가
echo ""
echo -e "${BLUE}Adding Lambda permissions...${NC}"

# Usage handler permission
aws lambda add-permission \
    --function-name nx-tt-dev-ver3-usage-handler \
    --statement-id apigateway-invoke-usage \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:${REGION}:887078546492:${API_ID}/*/*/*" \
    --region $REGION > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Usage handler permission added${NC}"
else
    echo -e "${YELLOW}ℹ️  Usage handler permission might already exist${NC}"
fi

# Conversation handler permission
aws lambda add-permission \
    --function-name nx-tt-dev-ver3-conversation-api \
    --statement-id apigateway-invoke-conversation \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:${REGION}:887078546492:${API_ID}/*/*/*" \
    --region $REGION > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Conversation handler permission added${NC}"
else
    echo -e "${YELLOW}ℹ️  Conversation handler permission might already exist${NC}"
fi

# CORS 설정
echo ""
echo -e "${BLUE}Configuring CORS...${NC}"

aws apigatewayv2 update-api \
    --api-id $API_ID \
    --cors-configuration \
        AllowOrigins="*",\
        AllowMethods="GET,POST,PUT,DELETE,PATCH,OPTIONS",\
        AllowHeaders="Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",\
        MaxAge=86400 \
    --region $REGION > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ CORS configured${NC}"
else
    echo -e "${RED}❌ Failed to configure CORS${NC}"
fi

# 배포 스테이지 업데이트
echo ""
echo -e "${BLUE}Deploying to production stage...${NC}"

aws apigatewayv2 create-deployment \
    --api-id $API_ID \
    --description "Added usage and conversation routes" \
    --region $REGION > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Deployment created${NC}"
else
    echo -e "${YELLOW}ℹ️  Using existing deployment${NC}"
fi

# 현재 라우트 확인
echo ""
echo -e "${CYAN}=================================${NC}"
echo -e "${GREEN}Route Setup Complete!${NC}"
echo -e "${CYAN}=================================${NC}"
echo ""
echo -e "${BLUE}Current routes:${NC}"

aws apigatewayv2 get-routes \
    --api-id $API_ID \
    --region $REGION \
    --query 'Items[].RouteKey' \
    --output text | tr '\t' '\n' | sort | uniq

echo ""
echo -e "${YELLOW}API Endpoint:${NC}"
echo "  https://${API_ID}.execute-api.${REGION}.amazonaws.com/production"
echo ""
echo -e "${GREEN}✅ All routes configured successfully!${NC}"