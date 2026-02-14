#!/bin/bash

# Conversation API에 누락된 메서드 추가

echo "Adding missing methods to Conversation API..."

API_ID="pisnqqgu75"
REGION="us-east-1"
ACCOUNT_ID="887078546492"

# Conversation Lambda 함수 찾기
LAMBDA_NAME="p2-two-conversation-crud-two"
LAMBDA_ARN="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${LAMBDA_NAME}"

echo "Using Lambda: $LAMBDA_NAME"

# /conversations/{conversationId} 리소스 ID 가져오기
echo "Getting /conversations/{conversationId} resource ID..."
CONVERSATION_ID_RESOURCE=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --query "items[?path=='/conversations/{conversationId}'].id" \
  --output text \
  --region $REGION)

echo "Resource ID: $CONVERSATION_ID_RESOURCE"

# DELETE 메서드 추가
echo "Adding DELETE method..."
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $CONVERSATION_ID_RESOURCE \
  --http-method DELETE \
  --authorization-type NONE \
  --region $REGION

# DELETE Lambda 통합
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $CONVERSATION_ID_RESOURCE \
  --http-method DELETE \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" \
  --region $REGION

# Lambda 권한 추가
aws lambda add-permission \
  --function-name $LAMBDA_NAME \
  --statement-id "p2-apigateway-DELETE-conversationId" \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/DELETE/conversations/{conversationId}" \
  --region $REGION 2>/dev/null

echo "✓ DELETE method added"

# PATCH 메서드 추가
echo "Adding PATCH method..."
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $CONVERSATION_ID_RESOURCE \
  --http-method PATCH \
  --authorization-type NONE \
  --region $REGION

# PATCH Lambda 통합
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $CONVERSATION_ID_RESOURCE \
  --http-method PATCH \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" \
  --region $REGION

# Lambda 권한 추가
aws lambda add-permission \
  --function-name $LAMBDA_NAME \
  --statement-id "p2-apigateway-PATCH-conversationId" \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/PATCH/conversations/{conversationId}" \
  --region $REGION 2>/dev/null

echo "✓ PATCH method added"

# OPTIONS 메서드 업데이트 (DELETE, PATCH 추가)
echo "Updating OPTIONS response to include DELETE and PATCH..."
aws apigateway put-integration-response \
  --rest-api-id $API_ID \
  --resource-id $CONVERSATION_ID_RESOURCE \
  --http-method OPTIONS \
  --status-code 200 \
  --response-parameters '{
    "method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'\''",
    "method.response.header.Access-Control-Allow-Methods": "'\''GET,PUT,DELETE,PATCH,OPTIONS'\''",
    "method.response.header.Access-Control-Allow-Origin": "'\''*'\''"
  }' \
  --region $REGION

echo "✓ OPTIONS updated"

# API 배포
echo "Deploying API..."
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod \
  --description "Added DELETE and PATCH methods to conversations" \
  --region $REGION

echo ""
echo "✅ Completed!"
echo "Added DELETE and PATCH methods to /conversations/{conversationId}"