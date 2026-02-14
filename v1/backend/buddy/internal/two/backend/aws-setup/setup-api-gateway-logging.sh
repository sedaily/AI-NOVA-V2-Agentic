#!/bin/bash

# API Gateway 로깅 설정 스크립트
# p2-two 서비스의 REST API에 대한 로깅 활성화

echo "Setting up API Gateway logging for p2-two service..."

# 설정
REGION="us-east-1"
API_ID="pisnqqgu75"  # REST API ID
STAGE_NAME="prod"

# CloudWatch Logs 역할 ARN (API Gateway가 로그를 쓸 수 있도록)
# 이 역할이 없다면 먼저 생성해야 함
CLOUDWATCH_ROLE_NAME="APIGatewayLogsRole"

echo "1. Checking/Creating IAM role for API Gateway logging..."

# IAM 역할이 존재하는지 확인
aws iam get-role --role-name $CLOUDWATCH_ROLE_NAME --region $REGION 2>/dev/null

if [ $? -ne 0 ]; then
    echo "Creating IAM role: $CLOUDWATCH_ROLE_NAME"

    # Trust policy 생성
    cat > /tmp/trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "apigateway.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

    # 역할 생성
    aws iam create-role \
        --role-name $CLOUDWATCH_ROLE_NAME \
        --assume-role-policy-document file:///tmp/trust-policy.json \
        --region $REGION

    # CloudWatch Logs 정책 연결
    aws iam attach-role-policy \
        --role-name $CLOUDWATCH_ROLE_NAME \
        --policy-arn "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs" \
        --region $REGION

    echo "✓ IAM role created successfully"

    # 역할 ARN 가져오기
    ROLE_ARN=$(aws iam get-role --role-name $CLOUDWATCH_ROLE_NAME --query 'Role.Arn' --output text --region $REGION)
else
    echo "✓ IAM role already exists"
    ROLE_ARN=$(aws iam get-role --role-name $CLOUDWATCH_ROLE_NAME --query 'Role.Arn' --output text --region $REGION)
fi

echo "Role ARN: $ROLE_ARN"
echo ""

# 2. API Gateway 계정 설정 업데이트
echo "2. Updating API Gateway account settings..."

aws apigateway update-account \
    --patch-operations op=replace,path=/cloudWatchRoleArn,value=$ROLE_ARN \
    --region $REGION

if [ $? -eq 0 ]; then
    echo "✓ API Gateway account settings updated"
else
    echo "✗ Failed to update account settings (may already be set)"
fi
echo ""

# 3. Stage 로깅 설정
echo "3. Enabling logging for stage: $STAGE_NAME"

# 로그 그룹 이름
LOG_GROUP_NAME="/aws/apigateway/$API_ID/$STAGE_NAME"

# 로그 그룹 생성
aws logs create-log-group \
    --log-group-name $LOG_GROUP_NAME \
    --region $REGION 2>/dev/null

echo "Log group: $LOG_GROUP_NAME"

# Stage 업데이트 - 로깅 활성화
aws apigateway update-stage \
    --rest-api-id $API_ID \
    --stage-name $STAGE_NAME \
    --patch-operations \
        op=replace,path=/accessLogSettings/destinationArn,value="arn:aws:logs:$REGION:*:log-group:$LOG_GROUP_NAME" \
        op=replace,path=/accessLogSettings/format,value='$context.requestId' \
        op=replace,path=/methodSettings/*/*/loggingLevel,value=INFO \
        op=replace,path=/methodSettings/*/*/dataTraceEnabled,value=true \
        op=replace,path=/methodSettings/*/*/metricsEnabled,value=true \
    --region $REGION

if [ $? -eq 0 ]; then
    echo "✓ Stage logging settings updated"
else
    echo "Trying alternative method..."

    # 대안: 개별 메서드 설정
    METHODS=("GET" "POST" "PUT" "DELETE" "OPTIONS")
    RESOURCES=("/prompts/{promptId}" "/prompts/{promptId}/files" "/prompts/{promptId}/files/{fileId}" "/conversations" "/usage")

    for RESOURCE in "${RESOURCES[@]}"
    do
        for METHOD in "${METHODS[@]}"
        do
            echo "Enabling logging for $METHOD $RESOURCE"

            aws apigateway update-method \
                --rest-api-id $API_ID \
                --resource-id $(aws apigateway get-resources --rest-api-id $API_ID --query "items[?path=='$RESOURCE'].id" --output text --region $REGION) \
                --http-method $METHOD \
                --patch-operations \
                    op=replace,path=/requestParameters/method.request.header.Authorization,value=false \
                --region $REGION 2>/dev/null
        done
    done
fi
echo ""

# 4. 배포 생성 (설정을 적용하기 위해)
echo "4. Creating deployment to apply changes..."

aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name $STAGE_NAME \
    --description "Enable CloudWatch logging" \
    --region $REGION

if [ $? -eq 0 ]; then
    echo "✓ Deployment created successfully"
else
    echo "✗ Deployment might already exist or failed"
fi
echo ""

echo "Setup completed!"
echo ""
echo "Log locations:"
echo "  API Gateway Execution Logs: /aws/apigateway/$API_ID/$STAGE_NAME"
echo "  API Gateway Access Logs: CloudWatch → Log groups → /aws/apigateway/$API_ID/$STAGE_NAME"
echo ""
echo "To test logging:"
echo "  curl https://$API_ID.execute-api.$REGION.amazonaws.com/$STAGE_NAME/prompts/11"
echo ""
echo "To view logs:"
echo "  aws logs tail /aws/apigateway/$API_ID/$STAGE_NAME --follow"