#!/bin/bash

# Conversation API Lambda 연결 수정

echo "Fixing Conversation API Lambda integration..."

API_ID="pisnqqgu75"
REGION="us-east-1"
ACCOUNT_ID="887078546492"

# 올바른 Lambda 함수명
LAMBDA_NAME="p2-two-conversation-api-two"
LAMBDA_ARN="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${LAMBDA_NAME}"

echo "Using Lambda: $LAMBDA_NAME"

# /conversations 리소스 ID 가져오기
CONVERSATIONS_RESOURCE=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --query "items[?path=='/conversations'].id" \
  --output text \
  --region $REGION)

echo "Conversations resource ID: $CONVERSATIONS_RESOURCE"

# /conversations/{conversationId} 리소스 ID
CONVERSATION_ID_RESOURCE=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --query "items[?path=='/conversations/{conversationId}'].id" \
  --output text \
  --region $REGION)

echo "ConversationId resource ID: $CONVERSATION_ID_RESOURCE"

# /conversations 메서드 업데이트
echo "Updating /conversations methods..."
for METHOD in GET POST PUT OPTIONS
do
  if [ "$METHOD" == "OPTIONS" ]; then
    # OPTIONS는 Mock 통합 유지
    continue
  fi

  echo "  Updating $METHOD..."
  aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $CONVERSATIONS_RESOURCE \
    --http-method $METHOD \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" \
    --region $REGION

  # Lambda 권한 추가
  aws lambda add-permission \
    --function-name $LAMBDA_NAME \
    --statement-id "p2-apigateway-${METHOD}-conversations" \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/${METHOD}/conversations" \
    --region $REGION 2>/dev/null
done

# /conversations/{conversationId} 메서드 업데이트
echo "Updating /conversations/{conversationId} methods..."
for METHOD in GET PUT DELETE PATCH OPTIONS
do
  if [ "$METHOD" == "OPTIONS" ]; then
    # OPTIONS는 Mock 통합 유지
    continue
  fi

  echo "  Updating $METHOD..."
  aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $CONVERSATION_ID_RESOURCE \
    --http-method $METHOD \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" \
    --region $REGION

  # Lambda 권한 추가
  aws lambda add-permission \
    --function-name $LAMBDA_NAME \
    --statement-id "p2-apigateway-${METHOD}-conversationId" \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/${METHOD}/conversations/{conversationId}" \
    --region $REGION 2>/dev/null
done

# CloudWatch 로그 그룹 생성
echo "Creating CloudWatch log group..."
aws logs create-log-group \
  --log-group-name /aws/lambda/$LAMBDA_NAME \
  --region $REGION 2>/dev/null

# API 배포
echo "Deploying API..."
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod \
  --description "Fixed Conversation API Lambda integration" \
  --region $REGION

echo ""
echo "✅ Conversation API fixed!"
echo ""
echo "Test the API:"
echo "  curl -X GET 'https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod/conversations?userId=test&engineType=11'"
echo "  curl -X POST 'https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod/conversations' -H 'Content-Type: application/json' -d '{\"userId\":\"test\",\"engineType\":\"11\"}'"