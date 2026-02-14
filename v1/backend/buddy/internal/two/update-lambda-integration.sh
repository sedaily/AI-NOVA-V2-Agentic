#!/bin/bash

# 올바른 Lambda 함수로 API Gateway 통합 업데이트

echo "Updating Lambda integration to correct function..."

API_ID="pisnqqgu75"
REGION="us-east-1"
ACCOUNT_ID="887078546492"
LAMBDA_NAME="p2-two-prompt-crud-two"
LAMBDA_ARN="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${LAMBDA_NAME}"

echo "Using Lambda: $LAMBDA_NAME"
echo "Lambda ARN: $LAMBDA_ARN"

# 리소스 ID 가져오기
PROMPT_ID_RESOURCE_ID="1eovbd"
FILES_RESOURCE_ID="wjwsxc"
FILE_ID_RESOURCE_ID="u25ep0"

# /prompts/{promptId} 메서드 업데이트
echo "Updating /prompts/{promptId} methods..."
for METHOD in GET PUT
do
  echo "  Updating $METHOD..."
  aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $PROMPT_ID_RESOURCE_ID \
    --http-method $METHOD \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" \
    --region $REGION

  # Lambda 권한 추가
  aws lambda add-permission \
    --function-name $LAMBDA_NAME \
    --statement-id "p2-apigateway-${METHOD}-promptId" \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/${METHOD}/prompts/{promptId}" \
    --region $REGION 2>/dev/null
done

# /prompts/{promptId}/files 메서드 업데이트
echo "Updating /prompts/{promptId}/files methods..."
for METHOD in GET POST
do
  echo "  Updating $METHOD..."
  aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $FILES_RESOURCE_ID \
    --http-method $METHOD \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" \
    --region $REGION

  aws lambda add-permission \
    --function-name $LAMBDA_NAME \
    --statement-id "p2-apigateway-${METHOD}-files" \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/${METHOD}/prompts/{promptId}/files" \
    --region $REGION 2>/dev/null
done

# /prompts/{promptId}/files/{fileId} 메서드 업데이트
echo "Updating /prompts/{promptId}/files/{fileId} methods..."
for METHOD in GET PUT DELETE
do
  echo "  Updating $METHOD..."
  aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $FILE_ID_RESOURCE_ID \
    --http-method $METHOD \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" \
    --region $REGION

  aws lambda add-permission \
    --function-name $LAMBDA_NAME \
    --statement-id "p2-apigateway-${METHOD}-fileId" \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/${METHOD}/prompts/{promptId}/files/{fileId}" \
    --region $REGION 2>/dev/null
done

# API 재배포
echo "Deploying API..."
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod \
  --description "Updated Lambda integration to p2-two-prompt-crud-two" \
  --region $REGION

echo ""
echo "✅ Integration updated!"
echo ""
echo "Test the API:"
echo "  curl https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod/prompts/11"