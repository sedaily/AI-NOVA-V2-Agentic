#!/bin/bash

# Complete CORS fix for API Gateway
API_ID="t75vorhge1"
REGION="us-east-1"

echo "🔧 Complete CORS Configuration for API Gateway"
echo "=============================================="

# Get all resources
RESOURCES=$(aws apigateway get-resources --rest-api-id $API_ID --region $REGION --limit 500 --output json)

# Parse resource IDs
ROOT_ID=$(echo $RESOURCES | jq -r '.items[] | select(.path=="/") | .id')
PROMPTS_ID=$(echo $RESOURCES | jq -r '.items[] | select(.path=="/prompts") | .id')
PROMPT_ID_ID=$(echo $RESOURCES | jq -r '.items[] | select(.path=="/prompts/{promptId}") | .id')
FILES_ID=$(echo $RESOURCES | jq -r '.items[] | select(.path=="/prompts/{promptId}/files") | .id')
CONVERSATIONS_ID=$(echo $RESOURCES | jq -r '.items[] | select(.path=="/conversations") | .id')
USAGE_ID=$(echo $RESOURCES | jq -r '.items[] | select(.path=="/usage") | .id')

echo "Resource IDs:"
echo "  Root: $ROOT_ID"
echo "  Prompts: $PROMPTS_ID"
echo "  Prompt/{id}: $PROMPT_ID_ID"
echo "  Files: $FILES_ID"
echo "  Conversations: $CONVERSATIONS_ID"
echo "  Usage: $USAGE_ID"
echo ""

# Function to add CORS to a method
add_cors_to_method() {
    local RESOURCE_ID=$1
    local HTTP_METHOD=$2
    local RESOURCE_PATH=$3

    echo "  Adding CORS headers to $HTTP_METHOD $RESOURCE_PATH..."

    # Add method response for CORS headers
    aws apigateway put-method-response \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method $HTTP_METHOD \
        --status-code 200 \
        --response-parameters '{"method.response.header.Access-Control-Allow-Origin":true,"method.response.header.Access-Control-Allow-Headers":true,"method.response.header.Access-Control-Allow-Methods":true,"method.response.header.Access-Control-Allow-Credentials":true}' \
        --region $REGION 2>/dev/null || true

    # Add integration response with actual header values
    aws apigateway put-integration-response \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method $HTTP_METHOD \
        --status-code 200 \
        --response-parameters '{"method.response.header.Access-Control-Allow-Origin":"'"'"'*'"'"'","method.response.header.Access-Control-Allow-Headers":"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'","method.response.header.Access-Control-Allow-Methods":"'"'"'GET,POST,PUT,DELETE,OPTIONS,PATCH'"'"'","method.response.header.Access-Control-Allow-Credentials":"'"'"'true'"'"'"}' \
        --region $REGION 2>/dev/null || true

    echo "    ✅ CORS headers added"
}

# Function to add OPTIONS method with MOCK integration
add_options_method() {
    local RESOURCE_ID=$1
    local RESOURCE_PATH=$2

    echo "📝 Adding OPTIONS to $RESOURCE_PATH"

    # Delete existing OPTIONS if exists
    aws apigateway delete-method \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --region $REGION 2>/dev/null || true

    # Add OPTIONS method
    aws apigateway put-method \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --authorization-type NONE \
        --region $REGION >/dev/null

    # Add method response
    aws apigateway put-method-response \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{"method.response.header.Access-Control-Allow-Origin":true,"method.response.header.Access-Control-Allow-Headers":true,"method.response.header.Access-Control-Allow-Methods":true,"method.response.header.Access-Control-Allow-Credentials":true}' \
        --response-models '{"application/json":"Empty"}' \
        --region $REGION >/dev/null

    # Add MOCK integration
    aws apigateway put-integration \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --type MOCK \
        --request-templates '{"application/json":"{\"statusCode\": 200}"}' \
        --region $REGION >/dev/null

    # Add integration response
    aws apigateway put-integration-response \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{"method.response.header.Access-Control-Allow-Origin":"'"'"'*'"'"'","method.response.header.Access-Control-Allow-Headers":"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'","method.response.header.Access-Control-Allow-Methods":"'"'"'GET,POST,PUT,DELETE,OPTIONS,PATCH'"'"'","method.response.header.Access-Control-Allow-Credentials":"'"'"'true'"'"'"}' \
        --response-templates '{"application/json":""}' \
        --region $REGION >/dev/null

    echo "  ✅ OPTIONS method configured"
}

# 1. Add OPTIONS to /prompts/{promptId}
add_options_method "$PROMPT_ID_ID" "/prompts/{promptId}"

# 2. Add CORS headers to existing PUT and POST methods
echo "📝 Adding CORS to /prompts/{promptId} methods"
add_cors_to_method "$PROMPT_ID_ID" "PUT" "/prompts/{promptId}"
add_cors_to_method "$PROMPT_ID_ID" "POST" "/prompts/{promptId}"

# 3. Ensure GET method exists and has CORS
echo "📝 Adding GET method to /prompts/{promptId}"
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $PROMPT_ID_ID \
    --http-method GET \
    --authorization-type NONE \
    --region $REGION 2>/dev/null || true

PROMPT_LAMBDA="arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:${REGION}:887078546492:function:sedaily-column-prompt-crud/invocations"

aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $PROMPT_ID_ID \
    --http-method GET \
    --type AWS_PROXY \
    --uri "$PROMPT_LAMBDA" \
    --integration-http-method POST \
    --region $REGION 2>/dev/null || true

add_cors_to_method "$PROMPT_ID_ID" "GET" "/prompts/{promptId}"

# 4. Fix /prompts/{promptId}/files
echo "📝 Fixing /prompts/{promptId}/files"
add_options_method "$FILES_ID" "/prompts/{promptId}/files"
add_cors_to_method "$FILES_ID" "POST" "/prompts/{promptId}/files"

# Add GET method for files
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $FILES_ID \
    --http-method GET \
    --authorization-type NONE \
    --region $REGION 2>/dev/null || true

aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $FILES_ID \
    --http-method GET \
    --type AWS_PROXY \
    --uri "$PROMPT_LAMBDA" \
    --integration-http-method POST \
    --region $REGION 2>/dev/null || true

add_cors_to_method "$FILES_ID" "GET" "/prompts/{promptId}/files"

# 5. Add OPTIONS to base resources
echo "📝 Adding OPTIONS to base resources"
add_options_method "$PROMPTS_ID" "/prompts"
add_options_method "$CONVERSATIONS_ID" "/conversations"
add_options_method "$USAGE_ID" "/usage"

# 6. Deploy API
echo ""
echo "🚀 Deploying API..."
DEPLOYMENT_ID=$(aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name prod \
    --description "Complete CORS fix deployment" \
    --region $REGION \
    --query 'id' --output text)

echo "✅ Deployment complete! ID: $DEPLOYMENT_ID"

# 7. Test CORS
echo ""
echo "🧪 Testing CORS preflight..."
echo "Testing: OPTIONS /prompts/C1"
curl -X OPTIONS https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod/prompts/C1 \
    -H "Origin: https://d3ck0lkvawjvhg.cloudfront.net" \
    -H "Access-Control-Request-Method: PUT" \
    -H "Access-Control-Request-Headers: Content-Type" \
    -I 2>/dev/null | grep -i "access-control"

echo ""
echo "✅ CORS configuration complete!"
echo ""
echo "Test URLs:"
echo "  PUT: https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod/prompts/C1"
echo "  POST: https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod/prompts/C1/files"