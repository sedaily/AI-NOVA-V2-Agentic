#!/bin/bash

# API Gateway 설정
API_ID="qyfams2iva"
REGION="us-east-1"
STAGE_NAME="prod"
LAMBDA_FUNCTION="nx-tt-dev-ver3-prompt-crud"

echo "🚀 API Gateway에 /prompts 경로 추가 중..."

# Root 리소스 ID 가져오기
ROOT_ID=$(aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path=='/'].id" --output text)
echo "Root ID: $ROOT_ID"

# /prompts 리소스 생성
echo "📌 /prompts 리소스 생성..."
PROMPTS_ID=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $ROOT_ID \
    --path-part "prompts" \
    --region $REGION \
    --query "id" \
    --output text)
echo "Prompts Resource ID: $PROMPTS_ID"

# /prompts/{promptId} 리소스 생성
echo "📌 /prompts/{promptId} 리소스 생성..."
PROMPT_ID_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $PROMPTS_ID \
    --path-part "{promptId}" \
    --region $REGION \
    --query "id" \
    --output text)
echo "Prompt ID Resource: $PROMPT_ID_RESOURCE"

# /prompts/{promptId}/files 리소스 생성
echo "📌 /prompts/{promptId}/files 리소스 생성..."
FILES_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $PROMPT_ID_RESOURCE \
    --path-part "files" \
    --region $REGION \
    --query "id" \
    --output text)
echo "Files Resource ID: $FILES_RESOURCE"

# /prompts/{promptId}/files/{fileId} 리소스 생성
echo "📌 /prompts/{promptId}/files/{fileId} 리소스 생성..."
FILE_ID_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $FILES_RESOURCE \
    --path-part "{fileId}" \
    --region $REGION \
    --query "id" \
    --output text)
echo "File ID Resource: $FILE_ID_RESOURCE"

# Lambda ARN 구성
LAMBDA_ARN="arn:aws:lambda:$REGION:$(aws sts get-caller-identity --query Account --output text):function:$LAMBDA_FUNCTION"
echo "Lambda ARN: $LAMBDA_ARN"

# /prompts GET 메소드 설정
echo "🔧 /prompts GET 메소드 설정..."
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $PROMPTS_ID \
    --http-method GET \
    --authorization-type NONE \
    --region $REGION

aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $PROMPTS_ID \
    --http-method GET \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations" \
    --region $REGION

# /prompts/{promptId} GET 메소드 설정
echo "🔧 /prompts/{promptId} GET 메소드 설정..."
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $PROMPT_ID_RESOURCE \
    --http-method GET \
    --authorization-type NONE \
    --request-parameters "method.request.path.promptId=true" \
    --region $REGION

aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $PROMPT_ID_RESOURCE \
    --http-method GET \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations" \
    --region $REGION

# /prompts/{promptId} PUT 메소드 설정
echo "🔧 /prompts/{promptId} PUT 메소드 설정..."
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $PROMPT_ID_RESOURCE \
    --http-method PUT \
    --authorization-type NONE \
    --request-parameters "method.request.path.promptId=true" \
    --region $REGION

aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $PROMPT_ID_RESOURCE \
    --http-method PUT \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations" \
    --region $REGION

# /prompts/{promptId}/files GET 메소드 설정
echo "🔧 /prompts/{promptId}/files GET 메소드 설정..."
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $FILES_RESOURCE \
    --http-method GET \
    --authorization-type NONE \
    --request-parameters "method.request.path.promptId=true" \
    --region $REGION

aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $FILES_RESOURCE \
    --http-method GET \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations" \
    --region $REGION

# /prompts/{promptId}/files POST 메소드 설정
echo "🔧 /prompts/{promptId}/files POST 메소드 설정..."
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $FILES_RESOURCE \
    --http-method POST \
    --authorization-type NONE \
    --request-parameters "method.request.path.promptId=true" \
    --region $REGION

aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $FILES_RESOURCE \
    --http-method POST \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations" \
    --region $REGION

# CORS OPTIONS 메소드 설정
echo "🌐 CORS 설정 중..."

# /prompts OPTIONS
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $PROMPTS_ID \
    --http-method OPTIONS \
    --authorization-type NONE \
    --region $REGION

aws apigateway put-method-response \
    --rest-api-id $API_ID \
    --resource-id $PROMPTS_ID \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{"method.response.header.Access-Control-Allow-Headers":true,"method.response.header.Access-Control-Allow-Methods":true,"method.response.header.Access-Control-Allow-Origin":true}' \
    --region $REGION

aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $PROMPTS_ID \
    --http-method OPTIONS \
    --type MOCK \
    --request-templates '{"application/json":"{\"statusCode\": 200}"}' \
    --region $REGION

aws apigateway put-integration-response \
    --rest-api-id $API_ID \
    --resource-id $PROMPTS_ID \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{"method.response.header.Access-Control-Allow-Headers":"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'","method.response.header.Access-Control-Allow-Methods":"'"'"'GET,OPTIONS'"'"'","method.response.header.Access-Control-Allow-Origin":"'"'"'*'"'"'"}' \
    --region $REGION

# /prompts/{promptId} OPTIONS
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $PROMPT_ID_RESOURCE \
    --http-method OPTIONS \
    --authorization-type NONE \
    --region $REGION

aws apigateway put-method-response \
    --rest-api-id $API_ID \
    --resource-id $PROMPT_ID_RESOURCE \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{"method.response.header.Access-Control-Allow-Headers":true,"method.response.header.Access-Control-Allow-Methods":true,"method.response.header.Access-Control-Allow-Origin":true}' \
    --region $REGION

aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $PROMPT_ID_RESOURCE \
    --http-method OPTIONS \
    --type MOCK \
    --request-templates '{"application/json":"{\"statusCode\": 200}"}' \
    --region $REGION

aws apigateway put-integration-response \
    --rest-api-id $API_ID \
    --resource-id $PROMPT_ID_RESOURCE \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{"method.response.header.Access-Control-Allow-Headers":"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'","method.response.header.Access-Control-Allow-Methods":"'"'"'GET,PUT,OPTIONS'"'"'","method.response.header.Access-Control-Allow-Origin":"'"'"'*'"'"'"}' \
    --region $REGION

# /prompts/{promptId}/files OPTIONS
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $FILES_RESOURCE \
    --http-method OPTIONS \
    --authorization-type NONE \
    --region $REGION

aws apigateway put-method-response \
    --rest-api-id $API_ID \
    --resource-id $FILES_RESOURCE \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{"method.response.header.Access-Control-Allow-Headers":true,"method.response.header.Access-Control-Allow-Methods":true,"method.response.header.Access-Control-Allow-Origin":true}' \
    --region $REGION

aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $FILES_RESOURCE \
    --http-method OPTIONS \
    --type MOCK \
    --request-templates '{"application/json":"{\"statusCode\": 200}"}' \
    --region $REGION

aws apigateway put-integration-response \
    --rest-api-id $API_ID \
    --resource-id $FILES_RESOURCE \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{"method.response.header.Access-Control-Allow-Headers":"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'","method.response.header.Access-Control-Allow-Methods":"'"'"'GET,POST,OPTIONS'"'"'","method.response.header.Access-Control-Allow-Origin":"'"'"'*'"'"'"}' \
    --region $REGION

# Lambda 권한 추가
echo "🔐 Lambda 실행 권한 추가..."
aws lambda add-permission \
    --function-name $LAMBDA_FUNCTION \
    --statement-id "api-gateway-prompts-get" \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:$REGION:$(aws sts get-caller-identity --query Account --output text):$API_ID/*/GET/prompts" \
    --region $REGION 2>/dev/null || true

aws lambda add-permission \
    --function-name $LAMBDA_FUNCTION \
    --statement-id "api-gateway-prompt-get" \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:$REGION:$(aws sts get-caller-identity --query Account --output text):$API_ID/*/GET/prompts/*" \
    --region $REGION 2>/dev/null || true

aws lambda add-permission \
    --function-name $LAMBDA_FUNCTION \
    --statement-id "api-gateway-prompt-put" \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:$REGION:$(aws sts get-caller-identity --query Account --output text):$API_ID/*/PUT/prompts/*" \
    --region $REGION 2>/dev/null || true

aws lambda add-permission \
    --function-name $LAMBDA_FUNCTION \
    --statement-id "api-gateway-files-get" \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:$REGION:$(aws sts get-caller-identity --query Account --output text):$API_ID/*/GET/prompts/*/files" \
    --region $REGION 2>/dev/null || true

aws lambda add-permission \
    --function-name $LAMBDA_FUNCTION \
    --statement-id "api-gateway-files-post" \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:$REGION:$(aws sts get-caller-identity --query Account --output text):$API_ID/*/POST/prompts/*/files" \
    --region $REGION 2>/dev/null || true

# API 배포
echo "🚀 API 배포 중..."
aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name $STAGE_NAME \
    --region $REGION

echo "✅ API Gateway 설정 완료!"
echo "📍 Endpoint: https://$API_ID.execute-api.$REGION.amazonaws.com/$STAGE_NAME/prompts"