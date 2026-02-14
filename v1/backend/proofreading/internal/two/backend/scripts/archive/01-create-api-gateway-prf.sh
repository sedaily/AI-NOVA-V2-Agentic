
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
API_NAME="nx-wt-prf-api"
API_DESCRIPTION="Nexus Writer PRF REST API Gateway"
STAGE_NAME="prod"
PROJECT_PREFIX="nx-wt-prf"

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}   새 API Gateway 생성 - ${PROJECT_PREFIX}   ${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# 1. 새 REST API 생성
echo -e "${BLUE}1. REST API 생성 중...${NC}"
API_ID=$(aws apigateway create-rest-api \
    --name "$API_NAME" \
    --description "$API_DESCRIPTION" \
    --endpoint-configuration types=REGIONAL \
    --region $REGION \
    --query 'id' \
    --output text)

if [ -z "$API_ID" ]; then
    echo -e "${RED}❌ API 생성 실패${NC}"
    exit 1
fi

echo -e "${GREEN}✅ API 생성 완료: $API_ID${NC}"

# 2. Root 리소스 ID 가져오기
ROOT_ID=$(aws apigateway get-resources \
    --rest-api-id $API_ID \
    --region $REGION \
    --query "items[?path=='/'].id" \
    --output text)

echo -e "${GREEN}✅ Root ID: $ROOT_ID${NC}"

# 3. 리소스 생성 함수
create_resource() {
    local parent_id=$1
    local path_part=$2
    
    local resource_id=$(aws apigateway create-resource \
        --rest-api-id $API_ID \
        --parent-id $parent_id \
        --path-part "$path_part" \
        --region $REGION \
        --query 'id' \
        --output text)
    
    echo "$resource_id"
}

# 4. 메소드 및 통합 설정 함수
setup_method() {
    local resource_id=$1
    local http_method=$2
    local lambda_function=$3
    local request_params=$4
    
    # 메소드 생성
    aws apigateway put-method \
        --rest-api-id $API_ID \
        --resource-id $resource_id \
        --http-method $http_method \
        --authorization-type NONE \
        $request_params \
        --region $REGION > /dev/null 2>&1
    
    # Lambda 통합 설정
    local lambda_arn="arn:aws:lambda:$REGION:$(aws sts get-caller-identity --query Account --output text):function:$lambda_function"
    
    aws apigateway put-integration \
        --rest-api-id $API_ID \
        --resource-id $resource_id \
        --http-method $http_method \
        --type AWS_PROXY \
        --integration-http-method POST \
        --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/$lambda_arn/invocations" \
        --region $REGION > /dev/null 2>&1
    
    echo -e "  ${GREEN}✓${NC} $http_method 메소드 설정 완료"
}

# 5. CORS 설정 함수
setup_cors() {
    local resource_id=$1
    local allowed_methods=$2
    
    # OPTIONS 메소드 생성
    aws apigateway put-method \
        --rest-api-id $API_ID \
        --resource-id $resource_id \
        --http-method OPTIONS \
        --authorization-type NONE \
        --region $REGION > /dev/null 2>&1
    
    # OPTIONS 메소드 응답 설정
    aws apigateway put-method-response \
        --rest-api-id $API_ID \
        --resource-id $resource_id \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{"method.response.header.Access-Control-Allow-Headers":true,"method.response.header.Access-Control-Allow-Methods":true,"method.response.header.Access-Control-Allow-Origin":true}' \
        --region $REGION > /dev/null 2>&1
    
    # Mock 통합 설정
    aws apigateway put-integration \
        --rest-api-id $API_ID \
        --resource-id $resource_id \
        --http-method OPTIONS \
        --type MOCK \
        --request-templates '{"application/json":"{\"statusCode\": 200}"}' \
        --region $REGION > /dev/null 2>&1
    
    # 통합 응답 설정
    aws apigateway put-integration-response \
        --rest-api-id $API_ID \
        --resource-id $resource_id \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters "{\"method.response.header.Access-Control-Allow-Headers\":\"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'\",\"method.response.header.Access-Control-Allow-Methods\":\"'$allowed_methods'\",\"method.response.header.Access-Control-Allow-Origin\":\"'*'\"}" \
        --region $REGION > /dev/null 2>&1
    
    echo -e "  ${GREEN}✓${NC} CORS 설정 완료"
}

# 6. 리소스 및 메소드 생성
echo -e "\n${BLUE}2. API 리소스 생성 중...${NC}"

# /conversations 리소스
echo -e "\n${CYAN}📌 /conversations 리소스 설정${NC}"
CONV_ID=$(create_resource $ROOT_ID "conversations")
setup_method $CONV_ID "GET" "${PROJECT_PREFIX}-conversation-api" ""
setup_method $CONV_ID "POST" "${PROJECT_PREFIX}-conversation-api" ""
setup_cors $CONV_ID "GET,POST,OPTIONS"

# /conversations/{id} 리소스
echo -e "\n${CYAN}📌 /conversations/{id} 리소스 설정${NC}"
CONV_ITEM_ID=$(create_resource $CONV_ID "{id}")
setup_method $CONV_ITEM_ID "GET" "${PROJECT_PREFIX}-conversation-api" '--request-parameters "method.request.path.id=true"'
setup_method $CONV_ITEM_ID "PUT" "${PROJECT_PREFIX}-conversation-api" '--request-parameters "method.request.path.id=true"'
setup_method $CONV_ITEM_ID "DELETE" "${PROJECT_PREFIX}-conversation-api" '--request-parameters "method.request.path.id=true"'
setup_cors $CONV_ITEM_ID "GET,PUT,DELETE,OPTIONS"

# /prompts 리소스
echo -e "\n${CYAN}📌 /prompts 리소스 설정${NC}"
PROMPTS_ID=$(create_resource $ROOT_ID "prompts")
setup_method $PROMPTS_ID "GET" "${PROJECT_PREFIX}-prompt-crud" ""
setup_method $PROMPTS_ID "POST" "${PROJECT_PREFIX}-prompt-crud" ""
setup_cors $PROMPTS_ID "GET,POST,OPTIONS"

# /prompts/{promptId} 리소스
echo -e "\n${CYAN}📌 /prompts/{promptId} 리소스 설정${NC}"
PROMPT_ITEM_ID=$(create_resource $PROMPTS_ID "{promptId}")
setup_method $PROMPT_ITEM_ID "GET" "${PROJECT_PREFIX}-prompt-crud" '--request-parameters "method.request.path.promptId=true"'
setup_method $PROMPT_ITEM_ID "PUT" "${PROJECT_PREFIX}-prompt-crud" '--request-parameters "method.request.path.promptId=true"'
setup_method $PROMPT_ITEM_ID "DELETE" "${PROJECT_PREFIX}-prompt-crud" '--request-parameters "method.request.path.promptId=true"'
setup_cors $PROMPT_ITEM_ID "GET,PUT,DELETE,OPTIONS"

# /prompts/{promptId}/files 리소스
echo -e "\n${CYAN}📌 /prompts/{promptId}/files 리소스 설정${NC}"
FILES_ID=$(create_resource $PROMPT_ITEM_ID "files")
setup_method $FILES_ID "GET" "${PROJECT_PREFIX}-prompt-crud" '--request-parameters "method.request.path.promptId=true"'
setup_method $FILES_ID "POST" "${PROJECT_PREFIX}-prompt-crud" '--request-parameters "method.request.path.promptId=true"'
setup_cors $FILES_ID "GET,POST,OPTIONS"

# /prompts/{promptId}/files/{fileId} 리소스
echo -e "\n${CYAN}📌 /prompts/{promptId}/files/{fileId} 리소스 설정${NC}"
FILE_ITEM_ID=$(create_resource $FILES_ID "{fileId}")
setup_method $FILE_ITEM_ID "DELETE" "${PROJECT_PREFIX}-prompt-crud" '--request-parameters "method.request.path.promptId=true,method.request.path.fileId=true"'
setup_cors $FILE_ITEM_ID "DELETE,OPTIONS"

# /usage 리소스
echo -e "\n${CYAN}📌 /usage 리소스 설정${NC}"
USAGE_ID=$(create_resource $ROOT_ID "usage")
setup_method $USAGE_ID "GET" "${PROJECT_PREFIX}-usage-handler" ""
setup_cors $USAGE_ID "GET,OPTIONS"

# 7. Stage 생성 및 배포
echo -e "\n${BLUE}3. API 배포 중...${NC}"
DEPLOYMENT_ID=$(aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name $STAGE_NAME \
    --stage-description "Production stage for $PROJECT_PREFIX" \
    --description "Initial deployment" \
    --region $REGION \
    --query 'id' \
    --output text)

if [ -z "$DEPLOYMENT_ID" ]; then
    echo -e "${RED}❌ 배포 실패${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 배포 완료: $DEPLOYMENT_ID${NC}"

# 8. Stage 설정 업데이트 (로깅, 스로틀링 등)
echo -e "\n${BLUE}4. Stage 설정 중...${NC}"
aws apigateway update-stage \
    --rest-api-id $API_ID \
    --stage-name $STAGE_NAME \
    --patch-operations \
        op=replace,path=/throttle/burstLimit,value=500 \
        op=replace,path=/throttle/rateLimit,value=1000 \
    --region $REGION > /dev/null 2>&1

echo -e "${GREEN}✅ Stage 설정 완료${NC}"

# 9. 결과 출력
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   ✅ API Gateway 생성 완료!   ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${CYAN}📋 API 정보:${NC}"
echo -e "  • API ID: ${YELLOW}$API_ID${NC}"
echo -e "  • API Name: ${YELLOW}$API_NAME${NC}"
echo -e "  • Stage: ${YELLOW}$STAGE_NAME${NC}"
echo -e "  • Region: ${YELLOW}$REGION${NC}"
echo -e "  • Endpoint: ${YELLOW}https://$API_ID.execute-api.$REGION.amazonaws.com/$STAGE_NAME${NC}"
echo ""
echo -e "${CYAN}📌 다음 단계:${NC}"
echo -e "  1. Lambda 함수 생성 (${PROJECT_PREFIX}-conversation-api, ${PROJECT_PREFIX}-prompt-crud, ${PROJECT_PREFIX}-usage-handler)"
echo -e "  2. Lambda 실행 권한 설정 (02-setup-lambda-permissions-prf.sh 실행)"
echo -e "  3. WebSocket API 생성 (필요시)"
echo ""

# API ID를 파일로 저장
echo "$API_ID" > api_gateway_id.txt
echo -e "${CYAN}💾 API ID가 api_gateway_id.txt 파일에 저장되었습니다.${NC}"