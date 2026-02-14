#!/bin/bash

# AWS Bedrock Agents - Phase 1: Lambda 함수 배포
# 실행: bash deploy-lambda.sh

set -e

echo "🚀 Phase 1: Lambda 함수 배포 시작..."

# AWS Account ID 가져오기
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/BedrockAgentExecutionRole"

echo "📋 Account ID: $ACCOUNT_ID"
echo "📋 Role ARN: $ROLE_ARN"

# Lambda 함수 배포 함수
deploy_lambda() {
  local AGENT_NAME=$1
  local FUNCTION_NAME="bedrock-${AGENT_NAME}"
  
  echo ""
  echo "📦 ${AGENT_NAME} Lambda 배포 중..."
  
  cd ${AGENT_NAME}
  
  # ZIP 파일 생성
  zip -q -r function.zip lambda_function.py
  
  # Lambda 함수 생성
  aws lambda create-function \
    --function-name ${FUNCTION_NAME} \
    --runtime python3.11 \
    --role ${ROLE_ARN} \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://function.zip \
    --timeout 30 \
    --memory-size 256 \
    --description "Bedrock Agent: ${AGENT_NAME}" \
    --tags Project=AI-NOVA,Environment=Production \
    --region us-east-1 \
    > /dev/null 2>&1
  
  if [ $? -eq 0 ]; then
    echo "✅ ${FUNCTION_NAME} 생성 완료"
  else
    echo "⚠️  ${FUNCTION_NAME} 이미 존재 - 업데이트 중..."
    aws lambda update-function-code \
      --function-name ${FUNCTION_NAME} \
      --zip-file fileb://function.zip \
      --region us-east-1 \
      > /dev/null 2>&1
    echo "✅ ${FUNCTION_NAME} 업데이트 완료"
  fi
  
  # Lambda ARN 가져오기
  LAMBDA_ARN=$(aws lambda get-function --function-name ${FUNCTION_NAME} --query 'Configuration.FunctionArn' --output text)
  echo "📋 ARN: ${LAMBDA_ARN}"
  
  # ZIP 파일 정리
  rm function.zip
  
  cd ..
}

# 4개 Agent Lambda 배포
deploy_lambda "language-detector"
deploy_lambda "category-detector"
deploy_lambda "length-detector"
deploy_lambda "content-type-detector"

echo ""
echo "🎉 Phase 1 완료!"
echo ""
echo "생성된 Lambda 함수:"
aws lambda list-functions \
  --query 'Functions[?starts_with(FunctionName, `bedrock-`)].FunctionName' \
  --output table

echo ""
echo "다음 단계: Bedrock Agent 생성 (AWS Console 또는 create-agents.sh)"
