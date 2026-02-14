#!/bin/bash

# API Gateway에 Prompt 관련 라우트 생성 스크립트

echo "Setting up API Gateway routes for Prompt API..."

# 설정
API_ID="pisnqqgu75"
REGION="us-east-1"
LAMBDA_ARN="arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:p2-two-prompt-handler"

# 1. 먼저 계정 ID 가져오기
echo "Getting AWS Account ID..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "Account ID: $ACCOUNT_ID"

# Lambda ARN 업데이트
LAMBDA_ARN="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:p2-two-prompt-handler"
echo "Lambda ARN: $LAMBDA_ARN"

# 2. /prompts 리소스 ID 가져오기
echo "Getting /prompts resource ID..."
PROMPTS_RESOURCE_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --query "items[?path=='/prompts'].id" \
  --output text \
  --region $REGION)

echo "Prompts Resource ID: $PROMPTS_RESOURCE_ID"

# 3. /prompts/{promptId} 리소스 생성
echo "Creating /prompts/{promptId} resource..."
PROMPT_ID_RESOURCE=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $PROMPTS_RESOURCE_ID \
  --path-part "{promptId}" \
  --region $REGION 2>/dev/null)

if [ $? -eq 0 ]; then
  PROMPT_ID_RESOURCE_ID=$(echo $PROMPT_ID_RESOURCE | python -c "import sys, json; print(json.load(sys.stdin)['id'])")
  echo "Created resource /prompts/{promptId} with ID: $PROMPT_ID_RESOURCE_ID"
else
  # 이미 존재하는 경우
  PROMPT_ID_RESOURCE_ID=$(aws apigateway get-resources \
    --rest-api-id $API_ID \
    --query "items[?path=='/prompts/{promptId}'].id" \
    --output text \
    --region $REGION)
  echo "Resource /prompts/{promptId} already exists with ID: $PROMPT_ID_RESOURCE_ID"
fi

# 4. /prompts/{promptId}에 메서드 추가
METHODS=("GET" "PUT" "OPTIONS")

for METHOD in "${METHODS[@]}"
do
  echo "Adding $METHOD method to /prompts/{promptId}..."

  # 메서드 생성
  aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $PROMPT_ID_RESOURCE_ID \
    --http-method $METHOD \
    --authorization-type NONE \
    --region $REGION 2>/dev/null

  if [ "$METHOD" == "OPTIONS" ]; then
    # OPTIONS 메서드는 Mock 통합
    aws apigateway put-integration \
      --rest-api-id $API_ID \
      --resource-id $PROMPT_ID_RESOURCE_ID \
      --http-method OPTIONS \
      --type MOCK \
      --integration-http-method OPTIONS \
      --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
      --region $REGION

    # OPTIONS 응답 설정
    aws apigateway put-method-response \
      --rest-api-id $API_ID \
      --resource-id $PROMPT_ID_RESOURCE_ID \
      --http-method OPTIONS \
      --status-code 200 \
      --response-parameters '{
        "method.response.header.Access-Control-Allow-Headers": true,
        "method.response.header.Access-Control-Allow-Methods": true,
        "method.response.header.Access-Control-Allow-Origin": true
      }' \
      --region $REGION

    aws apigateway put-integration-response \
      --rest-api-id $API_ID \
      --resource-id $PROMPT_ID_RESOURCE_ID \
      --http-method OPTIONS \
      --status-code 200 \
      --response-parameters '{
        "method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'\''",
        "method.response.header.Access-Control-Allow-Methods": "'\''GET,PUT,OPTIONS'\''",
        "method.response.header.Access-Control-Allow-Origin": "'\''*'\''"
      }' \
      --region $REGION
  else
    # GET, PUT은 Lambda 통합
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
      --function-name p2-two-prompt-handler \
      --statement-id "apigateway-${METHOD}-promptId" \
      --action lambda:InvokeFunction \
      --principal apigateway.amazonaws.com \
      --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/${METHOD}/prompts/{promptId}" \
      --region $REGION 2>/dev/null
  fi

  echo "✓ $METHOD method added"
done

# 5. /prompts/{promptId}/files 리소스 생성
echo "Creating /prompts/{promptId}/files resource..."
FILES_RESOURCE=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $PROMPT_ID_RESOURCE_ID \
  --path-part "files" \
  --region $REGION 2>/dev/null)

if [ $? -eq 0 ]; then
  FILES_RESOURCE_ID=$(echo $FILES_RESOURCE | python -c "import sys, json; print(json.load(sys.stdin)['id'])")
  echo "Created resource /prompts/{promptId}/files with ID: $FILES_RESOURCE_ID"
else
  FILES_RESOURCE_ID=$(aws apigateway get-resources \
    --rest-api-id $API_ID \
    --query "items[?path=='/prompts/{promptId}/files'].id" \
    --output text \
    --region $REGION)
  echo "Resource /prompts/{promptId}/files already exists with ID: $FILES_RESOURCE_ID"
fi

# 6. /prompts/{promptId}/files에 메서드 추가
FILE_METHODS=("GET" "POST" "OPTIONS")

for METHOD in "${FILE_METHODS[@]}"
do
  echo "Adding $METHOD method to /prompts/{promptId}/files..."

  aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $FILES_RESOURCE_ID \
    --http-method $METHOD \
    --authorization-type NONE \
    --region $REGION 2>/dev/null

  if [ "$METHOD" == "OPTIONS" ]; then
    # OPTIONS - Mock 통합
    aws apigateway put-integration \
      --rest-api-id $API_ID \
      --resource-id $FILES_RESOURCE_ID \
      --http-method OPTIONS \
      --type MOCK \
      --integration-http-method OPTIONS \
      --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
      --region $REGION

    aws apigateway put-method-response \
      --rest-api-id $API_ID \
      --resource-id $FILES_RESOURCE_ID \
      --http-method OPTIONS \
      --status-code 200 \
      --response-parameters '{
        "method.response.header.Access-Control-Allow-Headers": true,
        "method.response.header.Access-Control-Allow-Methods": true,
        "method.response.header.Access-Control-Allow-Origin": true
      }' \
      --region $REGION

    aws apigateway put-integration-response \
      --rest-api-id $API_ID \
      --resource-id $FILES_RESOURCE_ID \
      --http-method OPTIONS \
      --status-code 200 \
      --response-parameters '{
        "method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'\''",
        "method.response.header.Access-Control-Allow-Methods": "'\''GET,POST,OPTIONS'\''",
        "method.response.header.Access-Control-Allow-Origin": "'\''*'\''"
      }' \
      --region $REGION
  else
    # Lambda 통합
    aws apigateway put-integration \
      --rest-api-id $API_ID \
      --resource-id $FILES_RESOURCE_ID \
      --http-method $METHOD \
      --type AWS_PROXY \
      --integration-http-method POST \
      --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" \
      --region $REGION

    aws lambda add-permission \
      --function-name p2-two-prompt-handler \
      --statement-id "apigateway-${METHOD}-files" \
      --action lambda:InvokeFunction \
      --principal apigateway.amazonaws.com \
      --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/${METHOD}/prompts/{promptId}/files" \
      --region $REGION 2>/dev/null
  fi

  echo "✓ $METHOD method added"
done

# 7. /prompts/{promptId}/files/{fileId} 리소스 생성
echo "Creating /prompts/{promptId}/files/{fileId} resource..."
FILE_ID_RESOURCE=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $FILES_RESOURCE_ID \
  --path-part "{fileId}" \
  --region $REGION 2>/dev/null)

if [ $? -eq 0 ]; then
  FILE_ID_RESOURCE_ID=$(echo $FILE_ID_RESOURCE | python -c "import sys, json; print(json.load(sys.stdin)['id'])")
  echo "Created resource /prompts/{promptId}/files/{fileId} with ID: $FILE_ID_RESOURCE_ID"
else
  FILE_ID_RESOURCE_ID=$(aws apigateway get-resources \
    --rest-api-id $API_ID \
    --query "items[?path=='/prompts/{promptId}/files/{fileId}'].id" \
    --output text \
    --region $REGION)
  echo "Resource already exists with ID: $FILE_ID_RESOURCE_ID"
fi

# 8. /prompts/{promptId}/files/{fileId}에 메서드 추가
FILE_ID_METHODS=("GET" "PUT" "DELETE" "OPTIONS")

for METHOD in "${FILE_ID_METHODS[@]}"
do
  echo "Adding $METHOD method to /prompts/{promptId}/files/{fileId}..."

  aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $FILE_ID_RESOURCE_ID \
    --http-method $METHOD \
    --authorization-type NONE \
    --region $REGION 2>/dev/null

  if [ "$METHOD" == "OPTIONS" ]; then
    # OPTIONS - Mock 통합
    aws apigateway put-integration \
      --rest-api-id $API_ID \
      --resource-id $FILE_ID_RESOURCE_ID \
      --http-method OPTIONS \
      --type MOCK \
      --integration-http-method OPTIONS \
      --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
      --region $REGION

    aws apigateway put-method-response \
      --rest-api-id $API_ID \
      --resource-id $FILE_ID_RESOURCE_ID \
      --http-method OPTIONS \
      --status-code 200 \
      --response-parameters '{
        "method.response.header.Access-Control-Allow-Headers": true,
        "method.response.header.Access-Control-Allow-Methods": true,
        "method.response.header.Access-Control-Allow-Origin": true
      }' \
      --region $REGION

    aws apigateway put-integration-response \
      --rest-api-id $API_ID \
      --resource-id $FILE_ID_RESOURCE_ID \
      --http-method OPTIONS \
      --status-code 200 \
      --response-parameters '{
        "method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'\''",
        "method.response.header.Access-Control-Allow-Methods": "'\''GET,PUT,DELETE,OPTIONS'\''",
        "method.response.header.Access-Control-Allow-Origin": "'\''*'\''"
      }' \
      --region $REGION
  else
    # Lambda 통합
    aws apigateway put-integration \
      --rest-api-id $API_ID \
      --resource-id $FILE_ID_RESOURCE_ID \
      --http-method $METHOD \
      --type AWS_PROXY \
      --integration-http-method POST \
      --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" \
      --region $REGION

    aws lambda add-permission \
      --function-name p2-two-prompt-handler \
      --statement-id "apigateway-${METHOD}-fileId" \
      --action lambda:InvokeFunction \
      --principal apigateway.amazonaws.com \
      --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/${METHOD}/prompts/{promptId}/files/{fileId}" \
      --region $REGION 2>/dev/null
  fi

  echo "✓ $METHOD method added"
done

# 9. API 배포
echo "Deploying API to prod stage..."
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod \
  --description "Added prompt routes" \
  --region $REGION

echo ""
echo "✅ Setup completed!"
echo ""
echo "Test the API:"
echo "  curl https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod/prompts/11"
echo ""
echo "Note: Make sure the Lambda function 'p2-two-prompt-handler' exists and handles these routes."