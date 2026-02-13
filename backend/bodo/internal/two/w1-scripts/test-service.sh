#!/bin/bash
# Test W1.SEDAILY.AI Service
# ===========================

source "$(dirname "$0")/config.sh"

echo "========================================="
echo "   W1 Service Health Check"
echo "========================================="

PASS_COUNT=0
FAIL_COUNT=0

# Test function
test_endpoint() {
    local name=$1
    local url=$2
    local expected=${3:-200}
    
    echo -n "Testing ${name}... "
    local status=$(curl -s -o /dev/null -w "%{http_code}" "${url}")
    
    if [ "$status" == "$expected" ]; then
        echo "✅ (HTTP ${status})"
        ((PASS_COUNT++))
    else
        echo "❌ (HTTP ${status}, expected ${expected})"
        ((FAIL_COUNT++))
    fi
}

# Test WebSocket connection
test_websocket() {
    local ws_url="wss://prsebeg7ub.execute-api.us-east-1.amazonaws.com/prod"
    echo -n "Testing WebSocket connection... "
    
    # Simple WebSocket test using Python
    python3 -c "
import websocket
import json
import sys

try:
    ws = websocket.create_connection('${ws_url}')
    ws.close()
    print('✅ Connected')
    sys.exit(0)
except Exception as e:
    print(f'❌ Failed: {e}')
    sys.exit(1)
" && ((PASS_COUNT++)) || ((FAIL_COUNT++))
}

# Test Secret Manager access
test_secret() {
    echo -n "Testing Secret Manager access... "
    
    if aws secretsmanager get-secret-value \
        --secret-id "${SECRET_NAME}" \
        --region "${AWS_REGION}" \
        --query 'SecretString' > /dev/null 2>&1; then
        echo "✅"
        ((PASS_COUNT++))
    else
        echo "❌"
        ((FAIL_COUNT++))
    fi
}

# Test Lambda functions
test_lambda() {
    echo ""
    echo "Lambda Function Status:"
    echo "-----------------------"
    
    for function in "${LAMBDA_FUNCTIONS[@]}"; do
        echo -n "  ${function}: "
        
        local status=$(aws lambda get-function \
            --function-name "${function}" \
            --region "${AWS_REGION}" \
            --query 'Configuration.State' \
            --output text 2>/dev/null)
        
        if [ "$status" == "Active" ]; then
            echo "✅ Active"
            ((PASS_COUNT++))
        else
            echo "❌ ${status:-Not found}"
            ((FAIL_COUNT++))
        fi
    done
}

# Test DynamoDB tables
test_dynamodb() {
    echo ""
    echo "DynamoDB Table Status:"
    echo "----------------------"
    
    for table in "${DYNAMODB_TABLES[@]}"; do
        echo -n "  ${table}: "
        
        local status=$(aws dynamodb describe-table \
            --table-name "${table}" \
            --region "${AWS_REGION}" \
            --query 'Table.TableStatus' \
            --output text 2>/dev/null)
        
        if [ "$status" == "ACTIVE" ]; then
            echo "✅ Active"
            ((PASS_COUNT++))
        else
            echo "❌ ${status:-Not found}"
            ((FAIL_COUNT++))
        fi
    done
}

# Main execution
echo ""
echo "1. Testing Frontend:"
echo "--------------------"
test_endpoint "Homepage" "https://w1.sedaily.ai" 200
test_endpoint "CloudFront" "https://d9am5o27m55dc.cloudfront.net" 200

echo ""
echo "2. Testing APIs:"
echo "----------------"
test_endpoint "REST API" "https://api.w1.sedaily.ai/prod/health" 200
test_endpoint "Direct API" "https://16ayefk5lc.execute-api.us-east-1.amazonaws.com/prod/health" 200
test_websocket

echo ""
echo "3. Testing AWS Resources:"
echo "-------------------------"
test_secret
test_lambda
test_dynamodb

echo ""
echo "========================================="
echo "Test Results:"
echo "  ✅ Passed: ${PASS_COUNT}"
echo "  ❌ Failed: ${FAIL_COUNT}"
echo "========================================="

if [ $FAIL_COUNT -eq 0 ]; then
    echo "🎉 All tests passed!"
    exit 0
else
    echo "⚠️  Some tests failed. Check the logs for details."
    exit 1
fi