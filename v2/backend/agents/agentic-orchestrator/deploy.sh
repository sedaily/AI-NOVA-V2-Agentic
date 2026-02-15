#!/bin/bash
# AI NOVA Agentic Orchestrator 배포 스크립트

set -e

REGION="us-east-1"
FUNCTION_NAME="nova-agentic-orchestrator"
ROLE_NAME="ainova-lambda-role-two"

echo "🤖 AI NOVA Agentic Orchestrator 배포"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 계정 ID 가져오기
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

echo "리전: $REGION"
echo "계정: $ACCOUNT_ID"
echo "함수: $FUNCTION_NAME"
echo ""

# Lambda 패키징
echo "📦 Lambda 패키징..."
cd "$(dirname "$0")"
zip -r function.zip lambda_function.py

# Lambda 배포 (업데이트 또는 생성)
echo "🚀 Lambda 배포..."
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION 2>/dev/null; then
    echo "  기존 함수 업데이트..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://function.zip \
        --region $REGION
else
    echo "  새 함수 생성..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime python3.11 \
        --handler lambda_function.lambda_handler \
        --role $ROLE_ARN \
        --zip-file fileb://function.zip \
        --timeout 120 \
        --memory-size 512 \
        --region $REGION
fi

# 정리
rm function.zip

echo ""
echo "✅ 배포 완료!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 API Gateway 연동 필요:"
echo ""
echo "1. API Gateway 콘솔에서 리소스 추가: /agentic"
echo "2. POST 메서드 추가 → Lambda: $FUNCTION_NAME"
echo "3. OPTIONS 메서드 추가 (CORS)"
echo "4. API 배포"
echo ""
echo "또는 AWS CLI:"
echo ""
echo "API_ID=\"ieec2gpr0c\""
echo "aws apigateway create-resource --rest-api-id \$API_ID --parent-id <ROOT_ID> --path-part agentic"
echo "aws apigateway put-method --rest-api-id \$API_ID --resource-id <RESOURCE_ID> --http-method POST --authorization-type NONE"
echo ""
