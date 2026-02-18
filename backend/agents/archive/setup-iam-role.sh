#!/bin/bash

# AWS Bedrock Agents - Phase 1: IAM Role 생성
# 실행: bash setup-iam-role.sh

set -e

echo "🚀 Phase 1: IAM Role 생성 시작..."

# 1. Trust Policy 파일 생성
cat > bedrock-trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

echo "✅ Trust Policy 파일 생성 완료"

# 2. IAM Role 생성
echo "📝 IAM Role 생성 중..."
aws iam create-role \
  --role-name BedrockAgentExecutionRole \
  --assume-role-policy-document file://bedrock-trust-policy.json \
  --description "Execution role for Bedrock Agents" \
  --tags Key=Project,Value=AI-NOVA Key=Environment,Value=Production

echo "✅ IAM Role 생성 완료"

# 3. Lambda 실행 권한 추가
echo "📝 Lambda 실행 권한 추가 중..."
aws iam attach-role-policy \
  --role-name BedrockAgentExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

echo "✅ Lambda 실행 권한 추가 완료"

# 4. Bedrock 모델 접근 권한 추가
cat > bedrock-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0"
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": "arn:aws:lambda:us-east-1:*:function:bedrock-*"
    }
  ]
}
EOF

echo "📝 Bedrock 정책 생성 중..."
aws iam put-role-policy \
  --role-name BedrockAgentExecutionRole \
  --policy-name BedrockAgentPolicy \
  --policy-document file://bedrock-policy.json

echo "✅ Bedrock 정책 추가 완료"

# 5. Role ARN 출력
ROLE_ARN=$(aws iam get-role --role-name BedrockAgentExecutionRole --query 'Role.Arn' --output text)
echo ""
echo "🎉 Phase 1 완료!"
echo "📋 Role ARN: $ROLE_ARN"
echo ""
echo "다음 단계: Lambda 함수 배포 (deploy-lambda.sh)"

# 정리
rm bedrock-trust-policy.json bedrock-policy.json
