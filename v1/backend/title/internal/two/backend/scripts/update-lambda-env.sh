#!/bin/bash

# Script to update Lambda environment variables for new Anthropic API configuration
# This script should be run before deploying Lambda functions

set -e

# Configuration
SECRET_NAME="title-v1"
REGION="us-east-1"
STACK_PREFIX="nx-tt-dev-ver3"

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}===================================================${NC}"
echo -e "${GREEN}     Lambda Environment Variables Update          ${NC}"
echo -e "${GREEN}===================================================${NC}"
echo

# Lambda functions to update
LAMBDA_FUNCTIONS=(
    "${STACK_PREFIX}-websocket-connect"
    "${STACK_PREFIX}-websocket-message"
    "${STACK_PREFIX}-websocket-disconnect"
    "${STACK_PREFIX}-conversation-api"
    "${STACK_PREFIX}-prompt-crud"
    "${STACK_PREFIX}-usage-handler"
    "${STACK_PREFIX}-vector-populate"
)

echo -e "${BLUE}Updating Lambda environment variables...${NC}"
echo

for FUNCTION_NAME in "${LAMBDA_FUNCTIONS[@]}"; do
    echo -e "${YELLOW}Processing: ${FUNCTION_NAME}${NC}"
    
    # Check if function exists
    if ! aws lambda get-function --function-name "${FUNCTION_NAME}" --region "${REGION}" &>/dev/null; then
        echo -e "${YELLOW}  ⚠ Function not found, skipping${NC}"
        continue
    fi
    
    # Get current environment variables
    CURRENT_ENV=$(aws lambda get-function-configuration \
        --function-name "${FUNCTION_NAME}" \
        --region "${REGION}" \
        --query 'Environment.Variables' \
        --output json 2>/dev/null || echo '{}')
    
    # Update environment variables with new configuration
    # Preserve existing variables and add/update new ones
    UPDATED_ENV=$(echo "$CURRENT_ENV" | jq '. + {
        "ANTHROPIC_SECRET_NAME": "'${SECRET_NAME}'",
        "USE_ANTHROPIC_API": "true",
        "AI_PROVIDER": "anthropic_api",
        "ANTHROPIC_MODEL_ID": "claude-opus-4-5-20251101",
        "ANTHROPIC_MAX_TOKENS": "4096",
        "ANTHROPIC_TEMPERATURE": "0.7",
        "FALLBACK_TO_BEDROCK": "true"
    }')
    
    # Update Lambda function configuration
    aws lambda update-function-configuration \
        --function-name "${FUNCTION_NAME}" \
        --region "${REGION}" \
        --environment "Variables=${UPDATED_ENV}" \
        --no-cli-pager > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}  ✓ Environment variables updated${NC}"
    else
        echo -e "${RED}  ✗ Failed to update environment variables${NC}"
    fi
done

echo
echo -e "${GREEN}===================================================${NC}"
echo -e "${GREEN}         Environment Update Complete              ${NC}"
echo -e "${GREEN}===================================================${NC}"
echo
echo -e "${BLUE}Summary:${NC}"
echo -e "  Secret Name: ${YELLOW}${SECRET_NAME}${NC}"
echo -e "  Model: ${YELLOW}claude-opus-4-5-20251101${NC}"
echo -e "  Functions Updated: ${YELLOW}${#LAMBDA_FUNCTIONS[@]}${NC}"
echo
echo -e "${GREEN}✓ Lambda environment variables updated!${NC}"
echo
echo -e "${YELLOW}Next step: Run the Lambda deployment script${NC}"
echo "  cd backend && ./scripts/99-deploy-lambda.sh"