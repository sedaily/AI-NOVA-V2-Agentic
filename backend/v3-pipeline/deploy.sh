#!/bin/bash

# NOVA v3 Pipeline Lambda Deployment Script
# Uses AWS Bedrock with Claude 4.5 Sonnet

set -e

# Configuration
FUNCTION_NAME="nova-v3-pipeline"
REGION="ap-northeast-2"
BEDROCK_REGION="us-east-1"
RUNTIME="python3.11"
HANDLER="lambda_function.lambda_handler"
TIMEOUT=120
MEMORY=512
DYNAMODB_TABLE="nova-v3-pipeline"

# Role ARN (must have Bedrock + DynamoDB permissions)
ROLE_ARN="arn:aws:iam::887078546492:role/ainova-lambda-role-two"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================"
echo "  NOVA v3 Pipeline Lambda Deployment"
echo "  (AWS Bedrock + Claude 4.5 Sonnet)"
echo "========================================"
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Step 1: Create DynamoDB table if not exists
echo -e "${YELLOW}[1/5] Creating DynamoDB table...${NC}"

if aws dynamodb describe-table --table-name $DYNAMODB_TABLE --region $REGION 2>/dev/null; then
    echo "DynamoDB table '$DYNAMODB_TABLE' already exists."
else
    echo "Creating DynamoDB table..."
    aws dynamodb create-table \
        --table-name $DYNAMODB_TABLE \
        --attribute-definitions \
            AttributeName=pipelineId,AttributeType=S \
            AttributeName=userId,AttributeType=S \
            AttributeName=createdAt,AttributeType=S \
        --key-schema \
            AttributeName=pipelineId,KeyType=HASH \
        --global-secondary-indexes \
            "[{\"IndexName\":\"userId-index\",\"KeySchema\":[{\"AttributeName\":\"userId\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"createdAt\",\"KeyType\":\"RANGE\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}}]" \
        --billing-mode PAY_PER_REQUEST \
        --region $REGION \
        --output text > /dev/null

    echo "Waiting for table to be active..."
    aws dynamodb wait table-exists --table-name $DYNAMODB_TABLE --region $REGION
    echo -e "${GREEN}DynamoDB table created.${NC}"
fi
echo ""

# Step 2: Create deployment package
echo -e "${YELLOW}[2/5] Creating deployment package...${NC}"

# Create temp directory
rm -rf package
mkdir -p package

# Install dependencies
pip install -r requirements.txt -t package/ --quiet 2>/dev/null || pip3 install -r requirements.txt -t package/ --quiet

# Copy Lambda function
cp lambda_function.py package/

# Create zip
cd package
zip -r ../deployment.zip . -x "*.pyc" -x "__pycache__/*" --quiet
cd ..

echo -e "${GREEN}Deployment package created: deployment.zip${NC}"
echo ""

# Step 3: Check if Lambda exists
echo -e "${YELLOW}[3/5] Deploying Lambda function...${NC}"

if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION 2>/dev/null; then
    echo "Lambda function exists. Updating..."

    # Update function code
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://deployment.zip \
        --region $REGION \
        --output text > /dev/null

    # Wait for update to complete
    aws lambda wait function-updated --function-name $FUNCTION_NAME --region $REGION 2>/dev/null || sleep 5

    echo -e "${GREEN}Lambda function updated.${NC}"
else
    echo "Lambda function does not exist. Creating..."

    # Create function
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime $RUNTIME \
        --role $ROLE_ARN \
        --handler $HANDLER \
        --timeout $TIMEOUT \
        --memory-size $MEMORY \
        --zip-file fileb://deployment.zip \
        --region $REGION \
        --output text > /dev/null

    echo -e "${GREEN}Lambda function created.${NC}"
fi
echo ""

# Step 4: Update environment variables
echo -e "${YELLOW}[4/5] Setting environment variables...${NC}"

aws lambda update-function-configuration \
    --function-name $FUNCTION_NAME \
    --environment "Variables={PIPELINE_TABLE=$DYNAMODB_TABLE,BEDROCK_REGION=$BEDROCK_REGION}" \
    --region $REGION \
    --output text > /dev/null

# Wait for update
aws lambda wait function-updated --function-name $FUNCTION_NAME --region $REGION 2>/dev/null || sleep 3

echo -e "${GREEN}Environment variables updated.${NC}"
echo "  PIPELINE_TABLE=$DYNAMODB_TABLE"
echo "  BEDROCK_REGION=$BEDROCK_REGION"
echo ""

# Step 5: Create/Update API Gateway
echo -e "${YELLOW}[5/5] Setting up API Gateway...${NC}"

API_NAME="nova-v3-api"
API_ID=$(aws apigateway get-rest-apis --region $REGION \
    --query "items[?name=='$API_NAME'].id" --output text 2>/dev/null)

if [ -z "$API_ID" ] || [ "$API_ID" = "None" ]; then
    echo "Creating new API Gateway..."

    # Create API
    API_ID=$(aws apigateway create-rest-api \
        --name $API_NAME \
        --description "NOVA v3 Pipeline API (Bedrock)" \
        --endpoint-configuration types=REGIONAL \
        --region $REGION \
        --query 'id' --output text)

    echo "API created with ID: $API_ID"

    # Get root resource ID
    ROOT_ID=$(aws apigateway get-resources --rest-api-id $API_ID --region $REGION \
        --query 'items[?path==`/`].id' --output text)

    # Create /v3 resource
    V3_ID=$(aws apigateway create-resource \
        --rest-api-id $API_ID \
        --parent-id $ROOT_ID \
        --path-part "v3" \
        --region $REGION \
        --query 'id' --output text)

    # Lambda ARN
    LAMBDA_ARN="arn:aws:lambda:$REGION:887078546492:function:$FUNCTION_NAME"

    # Create endpoints
    for ENDPOINT in analyze draft proofread revise titles save; do
        RESOURCE_ID=$(aws apigateway create-resource \
            --rest-api-id $API_ID \
            --parent-id $V3_ID \
            --path-part $ENDPOINT \
            --region $REGION \
            --query 'id' --output text)

        # Add POST method
        aws apigateway put-method \
            --rest-api-id $API_ID \
            --resource-id $RESOURCE_ID \
            --http-method POST \
            --authorization-type NONE \
            --region $REGION > /dev/null

        # Add OPTIONS method for CORS
        aws apigateway put-method \
            --rest-api-id $API_ID \
            --resource-id $RESOURCE_ID \
            --http-method OPTIONS \
            --authorization-type NONE \
            --region $REGION > /dev/null

        # Setup Lambda integration for POST
        aws apigateway put-integration \
            --rest-api-id $API_ID \
            --resource-id $RESOURCE_ID \
            --http-method POST \
            --type AWS_PROXY \
            --integration-http-method POST \
            --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations" \
            --region $REGION > /dev/null

        # Setup CORS mock integration for OPTIONS
        aws apigateway put-integration \
            --rest-api-id $API_ID \
            --resource-id $RESOURCE_ID \
            --http-method OPTIONS \
            --type MOCK \
            --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
            --region $REGION > /dev/null

        # Setup OPTIONS method response
        aws apigateway put-method-response \
            --rest-api-id $API_ID \
            --resource-id $RESOURCE_ID \
            --http-method OPTIONS \
            --status-code 200 \
            --response-parameters '{"method.response.header.Access-Control-Allow-Headers":true,"method.response.header.Access-Control-Allow-Methods":true,"method.response.header.Access-Control-Allow-Origin":true}' \
            --region $REGION > /dev/null

        # Setup OPTIONS integration response
        aws apigateway put-integration-response \
            --rest-api-id $API_ID \
            --resource-id $RESOURCE_ID \
            --http-method OPTIONS \
            --status-code 200 \
            --response-parameters '{"method.response.header.Access-Control-Allow-Headers":"'"'"'Content-Type,Authorization'"'"'","method.response.header.Access-Control-Allow-Methods":"'"'"'POST,OPTIONS'"'"'","method.response.header.Access-Control-Allow-Origin":"'"'"'*'"'"'"}' \
            --region $REGION > /dev/null

        echo "  Created endpoint: /v3/$ENDPOINT"
    done

    # Create /v3/load/{id} resource for GET
    LOAD_ID=$(aws apigateway create-resource \
        --rest-api-id $API_ID \
        --parent-id $V3_ID \
        --path-part "load" \
        --region $REGION \
        --query 'id' --output text)

    LOAD_PARAM_ID=$(aws apigateway create-resource \
        --rest-api-id $API_ID \
        --parent-id $LOAD_ID \
        --path-part "{id}" \
        --region $REGION \
        --query 'id' --output text)

    # Add GET method for load
    aws apigateway put-method \
        --rest-api-id $API_ID \
        --resource-id $LOAD_PARAM_ID \
        --http-method GET \
        --authorization-type NONE \
        --request-parameters "method.request.path.id=true" \
        --region $REGION > /dev/null

    aws apigateway put-integration \
        --rest-api-id $API_ID \
        --resource-id $LOAD_PARAM_ID \
        --http-method GET \
        --type AWS_PROXY \
        --integration-http-method POST \
        --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations" \
        --region $REGION > /dev/null

    echo "  Created endpoint: /v3/load/{id}"

    # Deploy API
    aws apigateway create-deployment \
        --rest-api-id $API_ID \
        --stage-name prod \
        --region $REGION > /dev/null

    # Add Lambda permission
    aws lambda add-permission \
        --function-name $FUNCTION_NAME \
        --statement-id "apigateway-$API_ID" \
        --action lambda:InvokeFunction \
        --principal apigateway.amazonaws.com \
        --source-arn "arn:aws:execute-api:$REGION:887078546492:$API_ID/*/*/*" \
        --region $REGION 2>/dev/null || true

    echo -e "${GREEN}API Gateway created and deployed.${NC}"
else
    echo "API Gateway already exists: $API_ID"
    echo "Redeploying to apply any changes..."

    aws apigateway create-deployment \
        --rest-api-id $API_ID \
        --stage-name prod \
        --region $REGION > /dev/null || true

    echo -e "${GREEN}API Gateway redeployed.${NC}"
fi
echo ""

# Cleanup
rm -rf package deployment.zip

# Print API URL
API_URL="https://$API_ID.execute-api.$REGION.amazonaws.com/prod/v3"

echo "========================================"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo "========================================"
echo ""
echo -e "${BLUE}API Base URL:${NC} $API_URL"
echo ""
echo "Endpoints:"
echo "  POST $API_URL/analyze    - Phase 1: 소재 분석"
echo "  POST $API_URL/draft      - Phase 3: 초안 생성"
echo "  POST $API_URL/proofread  - Phase 4-1: 교열"
echo "  POST $API_URL/revise     - Phase 4-2: 퇴고"
echo "  POST $API_URL/titles     - Phase 5: 제목 생성"
echo "  POST $API_URL/save       - 파이프라인 상태 저장"
echo "  GET  $API_URL/load/{id}  - 파이프라인 상태 로드"
echo ""
echo -e "${YELLOW}Note: Lambda role must have Bedrock invoke permissions.${NC}"
echo "Required policy: bedrock:InvokeModel on us.anthropic.claude-sonnet-4-20250514-v1:0"
echo ""

# Save API URL to file
echo "$API_URL" > api-url.txt
echo "API URL saved to api-url.txt"
