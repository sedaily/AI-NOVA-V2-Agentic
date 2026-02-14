#!/bin/bash

# 색상 설정
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}SEDAILY-COLUMN WEBSOCKET API SETUP${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""

# 설정
REGION="us-east-1"
PREFIX="sedaily-column"
STAGE_NAME="prod"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo -e "${YELLOW}Creating WebSocket API for ${PREFIX}${NC}"
echo -e "${YELLOW}Region: ${REGION}${NC}"
echo ""

# WebSocket API 생성
echo -e "${BLUE}Creating WebSocket API...${NC}"
WS_API_NAME="${PREFIX}-websocket-api"

# WebSocket API 생성
WS_API_ID=$(aws apigatewayv2 create-api \
    --name "$WS_API_NAME" \
    --protocol-type WEBSOCKET \
    --route-selection-expression '$request.body.action' \
    --description "Seoul Economic Daily Column Service WebSocket API" \
    --region $REGION \
    --query 'ApiId' \
    --output text)

echo -e "${GREEN}✅ WebSocket API created: ${WS_API_ID}${NC}"

# ====================================
# Lambda 통합 생성
# ====================================
echo ""
echo -e "${BLUE}Creating Lambda integrations...${NC}"

# Connect 통합
echo -e "${YELLOW}Creating $connect integration...${NC}"
CONNECT_INTEGRATION_ID=$(aws apigatewayv2 create-integration \
    --api-id $WS_API_ID \
    --integration-type AWS_PROXY \
    --integration-method POST \
    --integration-uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${PREFIX}-websocket-connect/invocations" \
    --payload-format-version "1.0" \
    --region $REGION \
    --query 'IntegrationId' \
    --output text)
echo -e "${GREEN}  ✓ Connect integration: ${CONNECT_INTEGRATION_ID}${NC}"

# Disconnect 통합
echo -e "${YELLOW}Creating $disconnect integration...${NC}"
DISCONNECT_INTEGRATION_ID=$(aws apigatewayv2 create-integration \
    --api-id $WS_API_ID \
    --integration-type AWS_PROXY \
    --integration-method POST \
    --integration-uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${PREFIX}-websocket-disconnect/invocations" \
    --payload-format-version "1.0" \
    --region $REGION \
    --query 'IntegrationId' \
    --output text)
echo -e "${GREEN}  ✓ Disconnect integration: ${DISCONNECT_INTEGRATION_ID}${NC}"

# Message 통합 (default)
echo -e "${YELLOW}Creating message integration...${NC}"
MESSAGE_INTEGRATION_ID=$(aws apigatewayv2 create-integration \
    --api-id $WS_API_ID \
    --integration-type AWS_PROXY \
    --integration-method POST \
    --integration-uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${PREFIX}-websocket-message/invocations" \
    --payload-format-version "1.0" \
    --region $REGION \
    --query 'IntegrationId' \
    --output text)
echo -e "${GREEN}  ✓ Message integration: ${MESSAGE_INTEGRATION_ID}${NC}"

# ====================================
# 라우트 생성
# ====================================
echo ""
echo -e "${BLUE}Creating routes...${NC}"

# $connect 라우트
echo -e "${YELLOW}Creating \$connect route...${NC}"
aws apigatewayv2 create-route \
    --api-id $WS_API_ID \
    --route-key '$connect' \
    --target "integrations/${CONNECT_INTEGRATION_ID}" \
    --region $REGION >/dev/null
echo -e "${GREEN}  ✓ \$connect route created${NC}"

# $disconnect 라우트
echo -e "${YELLOW}Creating \$disconnect route...${NC}"
aws apigatewayv2 create-route \
    --api-id $WS_API_ID \
    --route-key '$disconnect' \
    --target "integrations/${DISCONNECT_INTEGRATION_ID}" \
    --region $REGION >/dev/null
echo -e "${GREEN}  ✓ \$disconnect route created${NC}"

# $default 라우트
echo -e "${YELLOW}Creating \$default route...${NC}"
aws apigatewayv2 create-route \
    --api-id $WS_API_ID \
    --route-key '$default' \
    --target "integrations/${MESSAGE_INTEGRATION_ID}" \
    --region $REGION >/dev/null
echo -e "${GREEN}  ✓ \$default route created${NC}"

# sendMessage 라우트
echo -e "${YELLOW}Creating sendMessage route...${NC}"
aws apigatewayv2 create-route \
    --api-id $WS_API_ID \
    --route-key 'sendMessage' \
    --target "integrations/${MESSAGE_INTEGRATION_ID}" \
    --region $REGION >/dev/null
echo -e "${GREEN}  ✓ sendMessage route created${NC}"

# ====================================
# 스테이지 생성 및 배포
# ====================================
echo ""
echo -e "${BLUE}Creating and deploying stage...${NC}"

# 배포 생성
DEPLOYMENT_ID=$(aws apigatewayv2 create-deployment \
    --api-id $WS_API_ID \
    --description "Initial deployment for ${PREFIX}" \
    --region $REGION \
    --query 'DeploymentId' \
    --output text)
echo -e "${GREEN}  ✓ Deployment created: ${DEPLOYMENT_ID}${NC}"

# 스테이지 생성
aws apigatewayv2 create-stage \
    --api-id $WS_API_ID \
    --stage-name $STAGE_NAME \
    --deployment-id $DEPLOYMENT_ID \
    --description "Production stage for ${PREFIX}" \
    --default-route-settings '{
        "ThrottleRateLimit": 10000,
        "ThrottleBurstLimit": 5000
    }' \
    --region $REGION >/dev/null
echo -e "${GREEN}  ✓ Stage created: ${STAGE_NAME}${NC}"

# ====================================
# Lambda 권한 설정
# ====================================
echo ""
echo -e "${BLUE}Setting Lambda permissions...${NC}"

# Connect Lambda 권한
echo -e "${YELLOW}Setting permissions for connect function...${NC}"
aws lambda add-permission \
    --function-name "${PREFIX}-websocket-connect" \
    --statement-id "websocket-connect-permission" \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${WS_API_ID}/*" \
    --region $REGION 2>/dev/null
echo -e "${GREEN}  ✓ Connect permissions set${NC}"

# Disconnect Lambda 권한
echo -e "${YELLOW}Setting permissions for disconnect function...${NC}"
aws lambda add-permission \
    --function-name "${PREFIX}-websocket-disconnect" \
    --statement-id "websocket-disconnect-permission" \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${WS_API_ID}/*" \
    --region $REGION 2>/dev/null
echo -e "${GREEN}  ✓ Disconnect permissions set${NC}"

# Message Lambda 권한
echo -e "${YELLOW}Setting permissions for message function...${NC}"
aws lambda add-permission \
    --function-name "${PREFIX}-websocket-message" \
    --statement-id "websocket-message-permission" \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${WS_API_ID}/*" \
    --region $REGION 2>/dev/null
echo -e "${GREEN}  ✓ Message permissions set${NC}"

# WebSocket 연결 URL
WS_URL="wss://${WS_API_ID}.execute-api.${REGION}.amazonaws.com/${STAGE_NAME}"

# WebSocket 관리 API Endpoint 환경변수 업데이트
echo ""
echo -e "${BLUE}Updating Lambda environment variables...${NC}"

# WebSocket Message Lambda에 API Gateway 엔드포인트 추가
aws lambda update-function-configuration \
    --function-name "${PREFIX}-websocket-message" \
    --environment "Variables={
        AWS_REGION=${REGION},
        CONVERSATIONS_TABLE=${PREFIX}-conversations,
        PROMPTS_TABLE=${PREFIX}-prompts,
        USAGE_TABLE=${PREFIX}-usage,
        WEBSOCKET_TABLE=${PREFIX}-websocket-connections,
        FILES_TABLE=${PREFIX}-files,
        BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0,
        LOG_LEVEL=INFO,
        WEBSOCKET_API_ENDPOINT=https://${WS_API_ID}.execute-api.${REGION}.amazonaws.com/${STAGE_NAME}
    }" \
    --region $REGION >/dev/null

echo -e "${GREEN}✅ Environment variables updated${NC}"

echo ""
echo -e "${GREEN}=================================${NC}"
echo -e "${GREEN}✅ WEBSOCKET API CREATED!${NC}"
echo -e "${GREEN}=================================${NC}"
echo ""
echo -e "${BLUE}WebSocket API Details:${NC}"
echo -e "  ${GREEN}✓${NC} API ID: ${WS_API_ID}"
echo -e "  ${GREEN}✓${NC} WebSocket URL: ${WS_URL}"
echo ""
echo -e "${BLUE}Routes configured:${NC}"
echo -e "  ${GREEN}✓${NC} \$connect    -> ${PREFIX}-websocket-connect"
echo -e "  ${GREEN}✓${NC} \$disconnect -> ${PREFIX}-websocket-disconnect"
echo -e "  ${GREEN}✓${NC} \$default    -> ${PREFIX}-websocket-message"
echo -e "  ${GREEN}✓${NC} sendMessage -> ${PREFIX}-websocket-message"
echo ""
echo -e "${YELLOW}Save this WebSocket URL for frontend configuration:${NC}"
echo -e "${GREEN}${WS_URL}${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Run ${BLUE}05-deploy-lambda.sh${NC} to deploy Lambda code"
echo -e "  2. Update frontend .env with API URLs"