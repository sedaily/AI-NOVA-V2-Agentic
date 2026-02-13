#!/bin/bash

# CloudWatch Log Groups 생성 스크립트
# p2-two 서비스의 Lambda 함수들을 위한 로그 그룹 생성

echo "Creating CloudWatch Log Groups for p2-two service..."

# AWS 리전 설정
REGION="us-east-1"

# Lambda 함수 이름 목록
LAMBDA_FUNCTIONS=(
    "p2-two-prompt-handler"
    "p2-two-conversation-handler"
    "p2-two-usage-handler"
    "p2-two-prompt-api"
    "p2-two-conversation-api"
    "p2-two-usage-api"
)

# 각 Lambda 함수에 대한 로그 그룹 생성
for FUNCTION_NAME in "${LAMBDA_FUNCTIONS[@]}"
do
    LOG_GROUP="/aws/lambda/$FUNCTION_NAME"

    echo "Checking if log group exists: $LOG_GROUP"

    # 로그 그룹이 존재하는지 확인
    aws logs describe-log-groups \
        --log-group-name-prefix "$LOG_GROUP" \
        --region $REGION \
        --query "logGroups[?logGroupName=='$LOG_GROUP'].logGroupName" \
        --output text | grep -q "$LOG_GROUP"

    if [ $? -eq 0 ]; then
        echo "✓ Log group already exists: $LOG_GROUP"
    else
        echo "Creating log group: $LOG_GROUP"
        aws logs create-log-group \
            --log-group-name "$LOG_GROUP" \
            --region $REGION

        if [ $? -eq 0 ]; then
            echo "✓ Successfully created: $LOG_GROUP"

            # 로그 보관 기간 설정 (30일)
            aws logs put-retention-policy \
                --log-group-name "$LOG_GROUP" \
                --retention-in-days 30 \
                --region $REGION

            echo "✓ Set retention policy to 30 days"
        else
            echo "✗ Failed to create: $LOG_GROUP"
        fi
    fi
    echo ""
done

# API Gateway 로그 그룹 생성
echo "Creating API Gateway log groups..."

API_GATEWAY_LOG_GROUPS=(
    "/aws/api-gateway/p2-two-rest-api"
    "/aws/apigateway/p2-two"
)

for LOG_GROUP in "${API_GATEWAY_LOG_GROUPS[@]}"
do
    echo "Checking if log group exists: $LOG_GROUP"

    aws logs describe-log-groups \
        --log-group-name-prefix "$LOG_GROUP" \
        --region $REGION \
        --query "logGroups[?logGroupName=='$LOG_GROUP'].logGroupName" \
        --output text | grep -q "$LOG_GROUP"

    if [ $? -eq 0 ]; then
        echo "✓ Log group already exists: $LOG_GROUP"
    else
        echo "Creating log group: $LOG_GROUP"
        aws logs create-log-group \
            --log-group-name "$LOG_GROUP" \
            --region $REGION

        if [ $? -eq 0 ]; then
            echo "✓ Successfully created: $LOG_GROUP"

            # 로그 보관 기간 설정 (7일)
            aws logs put-retention-policy \
                --log-group-name "$LOG_GROUP" \
                --retention-in-days 7 \
                --region $REGION

            echo "✓ Set retention policy to 7 days"
        else
            echo "✗ Failed to create: $LOG_GROUP"
        fi
    fi
    echo ""
done

echo "Completed log group setup!"
echo ""
echo "To view logs:"
echo "  aws logs tail /aws/lambda/p2-two-prompt-handler --follow"
echo "  aws logs tail /aws/lambda/p2-two-conversation-handler --follow"
echo "  aws logs tail /aws/lambda/p2-two-usage-handler --follow"