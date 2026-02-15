#!/bin/bash
# AI NOVA Agent v2 배포 스크립트
# Claude Opus 4.5 기반 고품질 Agent 시스템

set -e

REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "🚀 AI NOVA Agent v2 배포 시작"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "리전: $REGION"
echo "계정: $ACCOUNT_ID"
echo ""

# 1. Intelligent Analyzer Lambda 배포
echo "📦 1/3: Intelligent Analyzer Lambda 배포..."
cd intelligent-analyzer
zip -r function.zip lambda_function.py
aws lambda update-function-code \
    --function-name nova-intelligent-analyzer \
    --zip-file fileb://function.zip \
    --region $REGION \
    2>/dev/null || \
aws lambda create-function \
    --function-name nova-intelligent-analyzer \
    --runtime python3.11 \
    --handler lambda_function.lambda_handler \
    --role arn:aws:iam::$ACCOUNT_ID:role/lambda-bedrock-role \
    --zip-file fileb://function.zip \
    --timeout 60 \
    --memory-size 256 \
    --region $REGION

rm function.zip
cd ..
echo "✅ Intelligent Analyzer 배포 완료"
echo ""

# 2. API Gateway Lambda v2 배포
echo "📦 2/3: API Gateway Lambda v2 배포..."
cd api-gateway
cp lambda_function_v2.py lambda_function.py
zip -r function.zip lambda_function.py
aws lambda update-function-code \
    --function-name nova-api-gateway-v2 \
    --zip-file fileb://function.zip \
    --region $REGION \
    2>/dev/null || \
aws lambda create-function \
    --function-name nova-api-gateway-v2 \
    --runtime python3.11 \
    --handler lambda_function.lambda_handler \
    --role arn:aws:iam::$ACCOUNT_ID:role/lambda-bedrock-role \
    --zip-file fileb://function.zip \
    --timeout 90 \
    --memory-size 512 \
    --region $REGION

rm function.zip
cd ..
echo "✅ API Gateway Lambda v2 배포 완료"
echo ""

# 3. Bedrock Agent 업데이트 안내
echo "📋 3/3: Bedrock Agent 수동 설정 필요"
echo ""
echo "AWS Console에서 다음 작업을 수행하세요:"
echo ""
echo "1. Bedrock > Agents > 기존 Agent 선택"
echo "2. Model 변경:"
echo "   - 현재: anthropic.claude-3-sonnet-20240229-v1:0"
echo "   - 변경: us.anthropic.claude-opus-4-5-20251101-v1:0"
echo ""
echo "3. Instructions 업데이트:"
echo "   - supervisor/agent-config-v2.json 참고"
echo ""
echo "4. Action Group 업데이트:"
echo "   - Lambda: nova-intelligent-analyzer"
echo "   - API Schema: intelligent-analyzer/agent-config.json"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 배포 완료!"
echo ""
echo "테스트:"
echo "curl -X POST https://YOUR_API_GATEWAY_URL/prod/invoke-agent \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"message\": \"삼성전자가 HBM4를 발표했다\"}'"
