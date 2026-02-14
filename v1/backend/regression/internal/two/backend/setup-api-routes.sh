#!/bin/bash

# API Gateway 라우트 설정 스크립트
API_ID="t75vorhge1"
REGION="us-east-1"

echo "=== Setting up API Gateway Routes for sedaily-column ==="

# 색상 설정
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 루트 리소스 ID 가져오기
ROOT_ID=$(aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query 'items[?path==`/`].id' --output text)
echo "Root Resource ID: $ROOT_ID"

# 기존 리소스 정리
echo -e "\n${YELLOW}Cleaning up existing resources...${NC}"
EXISTING=$(aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query 'items[?path!=`/`].id' --output text)
for resource_id in $EXISTING; do
    aws apigateway delete-resource --rest-api-id $API_ID --resource-id $resource_id --region $REGION 2>/dev/null
done

# Lambda ARN 설정
PROMPT_LAMBDA_ARN="arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:${REGION}:887078546492:function:sedaily-column-prompt-crud/invocations"
CONVERSATION_LAMBDA_ARN="arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:${REGION}:887078546492:function:sedaily-column-conversation-api/invocations"
USAGE_LAMBDA_ARN="arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:${REGION}:887078546492:function:sedaily-column-usage-handler/invocations"

# 리소스 및 메소드 생성 함수
create_resource_with_methods() {
    local PARENT_ID=$1
    local PATH_PART=$2
    local LAMBDA_ARN=$3
    local METHODS=$4

    echo -e "\n${BLUE}Creating resource: /${PATH_PART}${NC}"

    # 리소스 생성
    RESOURCE_ID=$(aws apigateway create-resource \
        --rest-api-id $API_ID \
        --parent-id $PARENT_ID \
        --path-part "$PATH_PART" \
        --region $REGION \
        --query 'id' --output text)

    echo "  Created resource: $RESOURCE_ID"

    # OPTIONS 메소드 추가 (CORS)
    aws apigateway put-method \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --authorization-type NONE \
        --region $REGION >/dev/null

    aws apigateway put-method-response \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{"method.response.header.Access-Control-Allow-Origin":true,"method.response.header.Access-Control-Allow-Headers":true,"method.response.header.Access-Control-Allow-Methods":true}' \
        --region $REGION >/dev/null

    aws apigateway put-integration \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --type MOCK \
        --request-templates '{"application/json":"{\"statusCode\": 200}"}' \
        --region $REGION >/dev/null

    aws apigateway put-integration-response \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{"method.response.header.Access-Control-Allow-Origin":"'"'"'*'"'"'","method.response.header.Access-Control-Allow-Headers":"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'","method.response.header.Access-Control-Allow-Methods":"'"'"'GET,POST,PUT,DELETE,OPTIONS'"'"'"}' \
        --region $REGION >/dev/null

    echo "  ✅ OPTIONS method added"

    # 지정된 메소드들 추가
    for METHOD in $METHODS; do
        aws apigateway put-method \
            --rest-api-id $API_ID \
            --resource-id $RESOURCE_ID \
            --http-method $METHOD \
            --authorization-type NONE \
            --region $REGION >/dev/null

        aws apigateway put-integration \
            --rest-api-id $API_ID \
            --resource-id $RESOURCE_ID \
            --http-method $METHOD \
            --type AWS_PROXY \
            --uri "$LAMBDA_ARN" \
            --integration-http-method POST \
            --region $REGION >/dev/null

        echo "  ✅ $METHOD method added"
    done

    echo $RESOURCE_ID
}

# 1. /prompts 리소스
echo -e "\n${GREEN}=== Setting up /prompts routes ===${NC}"
PROMPTS_ID=$(create_resource_with_methods $ROOT_ID "prompts" "$PROMPT_LAMBDA_ARN" "GET POST")

# 2. /prompts/{promptId} 리소스
PROMPT_ID_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $PROMPTS_ID \
    --path-part "{promptId}" \
    --region $REGION \
    --query 'id' --output text)

echo -e "\n${BLUE}Creating /prompts/{promptId}${NC}"
for METHOD in GET PUT DELETE OPTIONS; do
    if [ "$METHOD" == "OPTIONS" ]; then
        aws apigateway put-method \
            --rest-api-id $API_ID \
            --resource-id $PROMPT_ID_RESOURCE \
            --http-method OPTIONS \
            --authorization-type NONE \
            --region $REGION >/dev/null

        aws apigateway put-integration \
            --rest-api-id $API_ID \
            --resource-id $PROMPT_ID_RESOURCE \
            --http-method OPTIONS \
            --type MOCK \
            --request-templates '{"application/json":"{\"statusCode\": 200}"}' \
            --region $REGION >/dev/null
    else
        aws apigateway put-method \
            --rest-api-id $API_ID \
            --resource-id $PROMPT_ID_RESOURCE \
            --http-method $METHOD \
            --authorization-type NONE \
            --region $REGION >/dev/null

        aws apigateway put-integration \
            --rest-api-id $API_ID \
            --resource-id $PROMPT_ID_RESOURCE \
            --http-method $METHOD \
            --type AWS_PROXY \
            --uri "$PROMPT_LAMBDA_ARN" \
            --integration-http-method POST \
            --region $REGION >/dev/null
    fi
    echo "  ✅ $METHOD method added"
done

# 3. /prompts/{promptId}/files 리소스
FILES_ID=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $PROMPT_ID_RESOURCE \
    --path-part "files" \
    --region $REGION \
    --query 'id' --output text)

echo -e "\n${BLUE}Creating /prompts/{promptId}/files${NC}"
for METHOD in GET POST OPTIONS; do
    if [ "$METHOD" == "OPTIONS" ]; then
        aws apigateway put-method \
            --rest-api-id $API_ID \
            --resource-id $FILES_ID \
            --http-method OPTIONS \
            --authorization-type NONE \
            --region $REGION >/dev/null

        aws apigateway put-integration \
            --rest-api-id $API_ID \
            --resource-id $FILES_ID \
            --http-method OPTIONS \
            --type MOCK \
            --request-templates '{"application/json":"{\"statusCode\": 200}"}' \
            --region $REGION >/dev/null
    else
        aws apigateway put-method \
            --rest-api-id $API_ID \
            --resource-id $FILES_ID \
            --http-method $METHOD \
            --authorization-type NONE \
            --region $REGION >/dev/null

        aws apigateway put-integration \
            --rest-api-id $API_ID \
            --resource-id $FILES_ID \
            --http-method $METHOD \
            --type AWS_PROXY \
            --uri "$PROMPT_LAMBDA_ARN" \
            --integration-http-method POST \
            --region $REGION >/dev/null
    fi
    echo "  ✅ $METHOD method added"
done

# 4. /prompts/{promptId}/files/{fileId} 리소스
FILE_ID_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $FILES_ID \
    --path-part "{fileId}" \
    --region $REGION \
    --query 'id' --output text)

echo -e "\n${BLUE}Creating /prompts/{promptId}/files/{fileId}${NC}"
for METHOD in GET PUT DELETE OPTIONS; do
    if [ "$METHOD" == "OPTIONS" ]; then
        aws apigateway put-method \
            --rest-api-id $API_ID \
            --resource-id $FILE_ID_RESOURCE \
            --http-method OPTIONS \
            --authorization-type NONE \
            --region $REGION >/dev/null

        aws apigateway put-integration \
            --rest-api-id $API_ID \
            --resource-id $FILE_ID_RESOURCE \
            --http-method OPTIONS \
            --type MOCK \
            --request-templates '{"application/json":"{\"statusCode\": 200}"}' \
            --region $REGION >/dev/null
    else
        aws apigateway put-method \
            --rest-api-id $API_ID \
            --resource-id $FILE_ID_RESOURCE \
            --http-method $METHOD \
            --authorization-type NONE \
            --region $REGION >/dev/null

        aws apigateway put-integration \
            --rest-api-id $API_ID \
            --resource-id $FILE_ID_RESOURCE \
            --http-method $METHOD \
            --type AWS_PROXY \
            --uri "$PROMPT_LAMBDA_ARN" \
            --integration-http-method POST \
            --region $REGION >/dev/null
    fi
    echo "  ✅ $METHOD method added"
done

# 5. /conversations 리소스
echo -e "\n${GREEN}=== Setting up /conversations routes ===${NC}"
CONVERSATIONS_ID=$(create_resource_with_methods $ROOT_ID "conversations" "$CONVERSATION_LAMBDA_ARN" "GET POST")

# 6. /conversations/{conversationId} 리소스
CONVERSATION_ID_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $CONVERSATIONS_ID \
    --path-part "{conversationId}" \
    --region $REGION \
    --query 'id' --output text)

echo -e "\n${BLUE}Creating /conversations/{conversationId}${NC}"
for METHOD in GET PUT DELETE OPTIONS; do
    if [ "$METHOD" == "OPTIONS" ]; then
        aws apigateway put-method \
            --rest-api-id $API_ID \
            --resource-id $CONVERSATION_ID_RESOURCE \
            --http-method OPTIONS \
            --authorization-type NONE \
            --region $REGION >/dev/null

        aws apigateway put-integration \
            --rest-api-id $API_ID \
            --resource-id $CONVERSATION_ID_RESOURCE \
            --http-method OPTIONS \
            --type MOCK \
            --request-templates '{"application/json":"{\"statusCode\": 200}"}' \
            --region $REGION >/dev/null
    else
        aws apigateway put-method \
            --rest-api-id $API_ID \
            --resource-id $CONVERSATION_ID_RESOURCE \
            --http-method $METHOD \
            --authorization-type NONE \
            --region $REGION >/dev/null

        aws apigateway put-integration \
            --rest-api-id $API_ID \
            --resource-id $CONVERSATION_ID_RESOURCE \
            --http-method $METHOD \
            --type AWS_PROXY \
            --uri "$CONVERSATION_LAMBDA_ARN" \
            --integration-http-method POST \
            --region $REGION >/dev/null
    fi
    echo "  ✅ $METHOD method added"
done

# 7. /usage 리소스
echo -e "\n${GREEN}=== Setting up /usage routes ===${NC}"
USAGE_ID=$(create_resource_with_methods $ROOT_ID "usage" "$USAGE_LAMBDA_ARN" "GET POST")

# CORS 응답 설정
echo -e "\n${YELLOW}Setting up CORS integration responses...${NC}"
for RESOURCE_ID in $PROMPT_ID_RESOURCE $FILES_ID $FILE_ID_RESOURCE $CONVERSATION_ID_RESOURCE; do
    aws apigateway put-integration-response \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{"method.response.header.Access-Control-Allow-Origin":"'"'"'*'"'"'","method.response.header.Access-Control-Allow-Headers":"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'","method.response.header.Access-Control-Allow-Methods":"'"'"'GET,POST,PUT,DELETE,OPTIONS'"'"'"}' \
        --region $REGION >/dev/null 2>&1
done

# API 배포
echo -e "\n${GREEN}Deploying API...${NC}"
DEPLOYMENT_ID=$(aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name prod \
    --region $REGION \
    --query 'id' --output text)

echo -e "${GREEN}✅ API Deployed! Deployment ID: $DEPLOYMENT_ID${NC}"

# 리소스 구조 확인
echo -e "\n${BLUE}=== Final Resource Structure ===${NC}"
aws apigateway get-resources --rest-api-id $API_ID --region $REGION --output json | \
    jq -r '.items[] | "\(.path)"' | sort

echo -e "\n${GREEN}✅ API Gateway setup complete!${NC}"
echo -e "API Endpoint: https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod"