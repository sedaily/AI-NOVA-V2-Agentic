#!/bin/bash

# Usage API 설정

echo "Setting up Usage API..."

API_ID="pisnqqgu75"
REGION="us-east-1"
ACCOUNT_ID="887078546492"

# Usage Lambda 함수
LAMBDA_NAME="p2-two-usage-handler-two"
LAMBDA_ARN="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${LAMBDA_NAME}"

echo "Using Lambda: $LAMBDA_NAME"

# /usage 리소스 확인 및 생성
echo "Checking /usage resource..."
USAGE_RESOURCE=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --query "items[?path=='/usage'].id" \
  --output text \
  --region $REGION)

if [ -z "$USAGE_RESOURCE" ]; then
  echo "Creating /usage resource..."
  ROOT_RESOURCE=$(aws apigateway get-resources \
    --rest-api-id $API_ID \
    --query "items[?path=='/'].id" \
    --output text \
    --region $REGION)

  USAGE_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $ROOT_RESOURCE \
    --path-part "usage" \
    --region $REGION \
    --query "id" \
    --output text)
  echo "Created /usage resource: $USAGE_RESOURCE"
else
  echo "Usage resource exists: $USAGE_RESOURCE"
fi

# /usage 메서드 추가
echo "Adding methods to /usage..."
for METHOD in GET POST OPTIONS
do
  echo "  Adding $METHOD..."

  # 메서드 생성
  aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $USAGE_RESOURCE \
    --http-method $METHOD \
    --authorization-type NONE \
    --region $REGION 2>/dev/null

  if [ "$METHOD" == "OPTIONS" ]; then
    # OPTIONS - Mock 통합
    aws apigateway put-integration \
      --rest-api-id $API_ID \
      --resource-id $USAGE_RESOURCE \
      --http-method OPTIONS \
      --type MOCK \
      --integration-http-method OPTIONS \
      --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
      --region $REGION

    aws apigateway put-method-response \
      --rest-api-id $API_ID \
      --resource-id $USAGE_RESOURCE \
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
      --resource-id $USAGE_RESOURCE \
      --http-method OPTIONS \
      --status-code 200 \
      --response-parameters '{
        "method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'\''",
        "method.response.header.Access-Control-Allow-Methods": "'\''GET,POST,OPTIONS'\''",
        "method.response.header.Access-Control-Allow-Origin": "'\''*'\''"
      }' \
      --region $REGION
  else
    # GET, POST - Lambda 통합
    aws apigateway put-integration \
      --rest-api-id $API_ID \
      --resource-id $USAGE_RESOURCE \
      --http-method $METHOD \
      --type AWS_PROXY \
      --integration-http-method POST \
      --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" \
      --region $REGION

    # Lambda 권한 추가
    aws lambda add-permission \
      --function-name $LAMBDA_NAME \
      --statement-id "p2-apigateway-${METHOD}-usage" \
      --action lambda:InvokeFunction \
      --principal apigateway.amazonaws.com \
      --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/${METHOD}/usage" \
      --region $REGION 2>/dev/null
  fi
done

# /usage/{userId} 리소스 생성
echo "Creating /usage/{userId} resource..."
USER_ID_RESOURCE=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --query "items[?path=='/usage/{userId}'].id" \
  --output text \
  --region $REGION)

if [ -z "$USER_ID_RESOURCE" ]; then
  USER_ID_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $USAGE_RESOURCE \
    --path-part "{userId}" \
    --region $REGION \
    --query "id" \
    --output text)
  echo "Created /usage/{userId} resource: $USER_ID_RESOURCE"
else
  echo "Resource exists: $USER_ID_RESOURCE"
fi

# /usage/{userId}/{engineType} 리소스 생성
echo "Creating /usage/{userId}/{engineType} resource..."
ENGINE_TYPE_RESOURCE=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --query "items[?path=='/usage/{userId}/{engineType}'].id" \
  --output text \
  --region $REGION)

if [ -z "$ENGINE_TYPE_RESOURCE" ]; then
  ENGINE_TYPE_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $USER_ID_RESOURCE \
    --path-part "{engineType}" \
    --region $REGION \
    --query "id" \
    --output text)
  echo "Created /usage/{userId}/{engineType} resource: $ENGINE_TYPE_RESOURCE"
else
  echo "Resource exists: $ENGINE_TYPE_RESOURCE"
fi

# /usage/{userId}/{engineType}/update 리소스 생성
echo "Creating /usage/{userId}/{engineType}/update resource..."
UPDATE_RESOURCE=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --query "items[?path=='/usage/{userId}/{engineType}/update'].id" \
  --output text \
  --region $REGION)

if [ -z "$UPDATE_RESOURCE" ]; then
  UPDATE_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $ENGINE_TYPE_RESOURCE \
    --path-part "update" \
    --region $REGION \
    --query "id" \
    --output text)
  echo "Created update resource: $UPDATE_RESOURCE"
else
  echo "Resource exists: $UPDATE_RESOURCE"
fi

# /usage/{userId}/{engineType} 메서드 추가
echo "Adding methods to /usage/{userId}/{engineType}..."
for METHOD in GET OPTIONS
do
  echo "  Adding $METHOD..."

  aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $ENGINE_TYPE_RESOURCE \
    --http-method $METHOD \
    --authorization-type NONE \
    --region $REGION 2>/dev/null

  if [ "$METHOD" == "OPTIONS" ]; then
    # OPTIONS - Mock
    aws apigateway put-integration \
      --rest-api-id $API_ID \
      --resource-id $ENGINE_TYPE_RESOURCE \
      --http-method OPTIONS \
      --type MOCK \
      --integration-http-method OPTIONS \
      --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
      --region $REGION

    aws apigateway put-method-response \
      --rest-api-id $API_ID \
      --resource-id $ENGINE_TYPE_RESOURCE \
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
      --resource-id $ENGINE_TYPE_RESOURCE \
      --http-method OPTIONS \
      --status-code 200 \
      --response-parameters '{
        "method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'\''",
        "method.response.header.Access-Control-Allow-Methods": "'\''GET,OPTIONS'\''",
        "method.response.header.Access-Control-Allow-Origin": "'\''*'\''"
      }' \
      --region $REGION
  else
    # Lambda 통합
    aws apigateway put-integration \
      --rest-api-id $API_ID \
      --resource-id $ENGINE_TYPE_RESOURCE \
      --http-method $METHOD \
      --type AWS_PROXY \
      --integration-http-method POST \
      --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" \
      --region $REGION

    aws lambda add-permission \
      --function-name $LAMBDA_NAME \
      --statement-id "p2-apigateway-${METHOD}-usage-engineType" \
      --action lambda:InvokeFunction \
      --principal apigateway.amazonaws.com \
      --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/${METHOD}/usage/{userId}/{engineType}" \
      --region $REGION 2>/dev/null
  fi
done

# /usage/{userId}/{engineType}/update PUT 메서드 추가
echo "Adding PUT method to /update..."
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $UPDATE_RESOURCE \
  --http-method PUT \
  --authorization-type NONE \
  --region $REGION 2>/dev/null

aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $UPDATE_RESOURCE \
  --http-method PUT \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" \
  --region $REGION

aws lambda add-permission \
  --function-name $LAMBDA_NAME \
  --statement-id "p2-apigateway-PUT-usage-update" \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/PUT/usage/{userId}/{engineType}/update" \
  --region $REGION 2>/dev/null

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
  --description "Added Usage API routes" \
  --region $REGION

echo ""
echo "✅ Usage API setup completed!"
echo ""
echo "Test the API:"
echo "  curl -X GET 'https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod/usage/test-user/11'"