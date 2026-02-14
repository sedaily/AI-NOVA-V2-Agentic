#!/bin/bash

# Bedrock Agent 배포 스크립트
# 사용법: ./deploy-agents.sh YOUR_ACCOUNT_ID

ACCOUNT_ID=$1
REGION="us-east-1"

if [ -z "$ACCOUNT_ID" ]; then
    echo "Usage: ./deploy-agents.sh YOUR_ACCOUNT_ID"
    exit 1
fi

echo "🚀 Bedrock Agents 배포 시작"
echo "Account ID: $ACCOUNT_ID"
echo "Region: $REGION"

# 1. Lambda 함수 배포
echo ""
echo "📦 Step 1: Lambda 함수 배포"

# Language Detector
cd language-detector
zip -r function.zip lambda_function.py
aws lambda create-function \
  --function-name language-detector \
  --runtime python3.11 \
  --role arn:aws:iam::${ACCOUNT_ID}:role/lambda-execution-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip \
  --region $REGION
cd ..

# Category Detector
cd category-detector
zip -r function.zip lambda_function.py
aws lambda create-function \
  --function-name category-detector \
  --runtime python3.11 \
  --role arn:aws:iam::${ACCOUNT_ID}:role/lambda-execution-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip \
  --region $REGION
cd ..

# Length Detector
cd length-detector
zip -r function.zip lambda_function.py
aws lambda create-function \
  --function-name length-detector \
  --runtime python3.11 \
  --role arn:aws:iam::${ACCOUNT_ID}:role/lambda-execution-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip \
  --region $REGION
cd ..

echo "✅ Lambda 함수 배포 완료"

# 2. Bedrock Agent 생성
echo ""
echo "🤖 Step 2: Bedrock Agents 생성"

# Language Agent
echo "Creating Language Detection Agent..."
LANG_AGENT_ID=$(aws bedrock-agent create-agent \
  --agent-name language-detection-agent \
  --foundation-model anthropic.claude-3-sonnet-20240229-v1:0 \
  --instruction "당신은 텍스트의 언어를 감지하는 전문가입니다." \
  --agent-resource-role-arn arn:aws:iam::${ACCOUNT_ID}:role/AmazonBedrockExecutionRoleForAgents \
  --region $REGION \
  --query 'agent.agentId' \
  --output text)

echo "Language Agent ID: $LANG_AGENT_ID"

# Category Agent
echo "Creating Category Detection Agent..."
CAT_AGENT_ID=$(aws bedrock-agent create-agent \
  --agent-name category-detection-agent \
  --foundation-model anthropic.claude-3-sonnet-20240229-v1:0 \
  --instruction "당신은 기사의 카테고리를 분류하는 전문가입니다." \
  --agent-resource-role-arn arn:aws:iam::${ACCOUNT_ID}:role/AmazonBedrockExecutionRoleForAgents \
  --region $REGION \
  --query 'agent.agentId' \
  --output text)

echo "Category Agent ID: $CAT_AGENT_ID"

# Length Agent
echo "Creating Length Detection Agent..."
LEN_AGENT_ID=$(aws bedrock-agent create-agent \
  --agent-name length-detection-agent \
  --foundation-model anthropic.claude-3-sonnet-20240229-v1:0 \
  --instruction "당신은 텍스트의 길이를 분석하는 전문가입니다." \
  --agent-resource-role-arn arn:aws:iam::${ACCOUNT_ID}:role/AmazonBedrockExecutionRoleForAgents \
  --region $REGION \
  --query 'agent.agentId' \
  --output text)

echo "Length Agent ID: $LEN_AGENT_ID"

echo "✅ Bedrock Agents 생성 완료"

# 3. Action Groups 추가
echo ""
echo "🔧 Step 3: Action Groups 추가"

# Language Agent Action Group
aws bedrock-agent create-agent-action-group \
  --agent-id $LANG_AGENT_ID \
  --agent-version DRAFT \
  --action-group-name language-detection \
  --action-group-executor lambda=arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:language-detector \
  --region $REGION

# Category Agent Action Group
aws bedrock-agent create-agent-action-group \
  --agent-id $CAT_AGENT_ID \
  --agent-version DRAFT \
  --action-group-name category-detection \
  --action-group-executor lambda=arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:category-detector \
  --region $REGION

# Length Agent Action Group
aws bedrock-agent create-agent-action-group \
  --agent-id $LEN_AGENT_ID \
  --agent-version DRAFT \
  --action-group-name length-detection \
  --action-group-executor lambda=arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:length-detector \
  --region $REGION

echo "✅ Action Groups 추가 완료"

# 4. Agent Alias 생성
echo ""
echo "🏷️ Step 4: Agent Aliases 생성"

aws bedrock-agent create-agent-alias \
  --agent-id $LANG_AGENT_ID \
  --agent-alias-name prod \
  --region $REGION

aws bedrock-agent create-agent-alias \
  --agent-id $CAT_AGENT_ID \
  --agent-alias-name prod \
  --region $REGION

aws bedrock-agent create-agent-alias \
  --agent-id $LEN_AGENT_ID \
  --agent-alias-name prod \
  --region $REGION

echo "✅ Agent Aliases 생성 완료"

echo ""
echo "🎉 배포 완료!"
echo ""
echo "Agent IDs:"
echo "  Language: $LANG_AGENT_ID"
echo "  Category: $CAT_AGENT_ID"
echo "  Length: $LEN_AGENT_ID"
