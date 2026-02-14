#!/bin/bash

# AWS Transcribe 설정 스크립트
# S3 버킷 생성 및 Lambda 함수 배포

echo "==================================="
echo "AWS Transcribe Setup Script"
echo "==================================="

# 환경 변수 설정
AWS_REGION=${AWS_REGION:-"us-east-1"}
BUCKET_NAME="sedaily-column-transcribe"
LAMBDA_FUNCTION_NAME="sedaily-column-transcribe"
API_GATEWAY_NAME="sedaily-column-api"

echo "Region: $AWS_REGION"
echo "Bucket: $BUCKET_NAME"
echo ""

# 1. S3 버킷 생성
echo "1. Creating S3 bucket for Transcribe..."
if aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
    echo "   Bucket $BUCKET_NAME already exists"
else
    if [ "$AWS_REGION" = "us-east-1" ]; then
        aws s3api create-bucket \
            --bucket "$BUCKET_NAME" \
            --region "$AWS_REGION"
    else
        aws s3api create-bucket \
            --bucket "$BUCKET_NAME" \
            --region "$AWS_REGION" \
            --create-bucket-configuration LocationConstraint="$AWS_REGION"
    fi
    echo "   ✓ Bucket created successfully"
fi

# 2. S3 버킷 정책 설정
echo ""
echo "2. Setting S3 bucket policy..."
cat > /tmp/bucket-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "transcribe.amazonaws.com"
            },
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": "arn:aws:s3:::${BUCKET_NAME}/*"
        },
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::${BUCKET_NAME}/*"
        }
    ]
}
EOF

aws s3api put-bucket-policy \
    --bucket "$BUCKET_NAME" \
    --policy file:///tmp/bucket-policy.json

echo "   ✓ Bucket policy configured"

# 3. Lambda 실행 역할 생성/업데이트
echo ""
echo "3. Creating/Updating Lambda execution role..."

ROLE_NAME="sedaily-column-transcribe-role"

# 역할이 있는지 확인
if aws iam get-role --role-name "$ROLE_NAME" 2>/dev/null; then
    echo "   Role $ROLE_NAME already exists"
else
    # Trust policy 생성
    cat > /tmp/trust-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

    aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document file:///tmp/trust-policy.json

    echo "   ✓ Role created"
fi

# 4. IAM 정책 연결
echo ""
echo "4. Attaching IAM policies..."

# Transcribe 정책
cat > /tmp/transcribe-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "transcribe:StartTranscriptionJob",
                "transcribe:GetTranscriptionJob",
                "transcribe:DeleteTranscriptionJob"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::${BUCKET_NAME}/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "*"
        }
    ]
}
EOF

# 정책 생성 또는 업데이트
POLICY_NAME="SedailyColumnTranscribePolicy"
POLICY_ARN="arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/$POLICY_NAME"

if aws iam get-policy --policy-arn "$POLICY_ARN" 2>/dev/null; then
    # 정책이 있으면 새 버전 생성
    aws iam create-policy-version \
        --policy-arn "$POLICY_ARN" \
        --policy-document file:///tmp/transcribe-policy.json \
        --set-as-default
    echo "   ✓ Policy updated"
else
    # 정책 생성
    aws iam create-policy \
        --policy-name "$POLICY_NAME" \
        --policy-document file:///tmp/transcribe-policy.json
    echo "   ✓ Policy created"
fi

# 역할에 정책 연결
aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "$POLICY_ARN" 2>/dev/null || true

aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole" 2>/dev/null || true

echo "   ✓ Policies attached"

# 5. Lambda 함수 배포
echo ""
echo "5. Deploying Lambda function..."

# Lambda 패키지 준비
cd ../
zip -r /tmp/lambda-transcribe.zip . -x "*.git*" "*.sh" "scripts/*" "__pycache__/*" "*.pyc"

# Lambda 함수 생성 또는 업데이트
if aws lambda get-function --function-name "$LAMBDA_FUNCTION_NAME" --region "$AWS_REGION" 2>/dev/null; then
    echo "   Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name "$LAMBDA_FUNCTION_NAME" \
        --zip-file fileb:///tmp/lambda-transcribe.zip \
        --region "$AWS_REGION"

    aws lambda update-function-configuration \
        --function-name "$LAMBDA_FUNCTION_NAME" \
        --handler "handlers.api.transcribe.lambda_handler" \
        --timeout 120 \
        --memory-size 512 \
        --environment "Variables={S3_BUCKET=$BUCKET_NAME,TRANSCRIBE_REGION=$AWS_REGION}" \
        --region "$AWS_REGION"
else
    echo "   Creating new Lambda function..."
    aws lambda create-function \
        --function-name "$LAMBDA_FUNCTION_NAME" \
        --runtime python3.9 \
        --role "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/$ROLE_NAME" \
        --handler "handlers.api.transcribe.lambda_handler" \
        --timeout 120 \
        --memory-size 512 \
        --zip-file fileb:///tmp/lambda-transcribe.zip \
        --environment "Variables={S3_BUCKET=$BUCKET_NAME,TRANSCRIBE_REGION=$AWS_REGION}" \
        --region "$AWS_REGION"
fi

echo "   ✓ Lambda function deployed"

# 6. API Gateway 경로 추가
echo ""
echo "6. Adding API Gateway route..."

# REST API ID 가져오기
REST_API_ID=$(aws apigateway get-rest-apis \
    --query "items[?name=='$API_GATEWAY_NAME'].id" \
    --output text \
    --region "$AWS_REGION")

if [ -n "$REST_API_ID" ]; then
    # /transcribe 리소스 생성
    PARENT_ID=$(aws apigateway get-resources \
        --rest-api-id "$REST_API_ID" \
        --query "items[?path=='/'].id" \
        --output text \
        --region "$AWS_REGION")

    # 리소스가 이미 있는지 확인
    RESOURCE_ID=$(aws apigateway get-resources \
        --rest-api-id "$REST_API_ID" \
        --query "items[?path=='/transcribe'].id" \
        --output text \
        --region "$AWS_REGION")

    if [ -z "$RESOURCE_ID" ]; then
        RESOURCE_ID=$(aws apigateway create-resource \
            --rest-api-id "$REST_API_ID" \
            --parent-id "$PARENT_ID" \
            --path-part "transcribe" \
            --region "$AWS_REGION" \
            --query "id" \
            --output text)
        echo "   ✓ Resource /transcribe created"
    else
        echo "   Resource /transcribe already exists"
    fi

    # POST 메서드 생성
    aws apigateway put-method \
        --rest-api-id "$REST_API_ID" \
        --resource-id "$RESOURCE_ID" \
        --http-method POST \
        --authorization-type NONE \
        --region "$AWS_REGION" 2>/dev/null || true

    # Lambda 통합 설정
    aws apigateway put-integration \
        --rest-api-id "$REST_API_ID" \
        --resource-id "$RESOURCE_ID" \
        --http-method POST \
        --type AWS_PROXY \
        --integration-http-method POST \
        --uri "arn:aws:apigateway:$AWS_REGION:lambda:path/2015-03-31/functions/arn:aws:lambda:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):function:$LAMBDA_FUNCTION_NAME/invocations" \
        --region "$AWS_REGION"

    # Lambda 권한 추가
    aws lambda add-permission \
        --function-name "$LAMBDA_FUNCTION_NAME" \
        --statement-id "apigateway-invoke-transcribe" \
        --action "lambda:InvokeFunction" \
        --principal "apigateway.amazonaws.com" \
        --source-arn "arn:aws:execute-api:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):$REST_API_ID/*/POST/transcribe" \
        --region "$AWS_REGION" 2>/dev/null || true

    # CORS 설정
    aws apigateway put-method \
        --rest-api-id "$REST_API_ID" \
        --resource-id "$RESOURCE_ID" \
        --http-method OPTIONS \
        --authorization-type NONE \
        --region "$AWS_REGION" 2>/dev/null || true

    aws apigateway put-integration \
        --rest-api-id "$REST_API_ID" \
        --resource-id "$RESOURCE_ID" \
        --http-method OPTIONS \
        --type MOCK \
        --request-templates '{"application/json":"{\"statusCode\":200}"}' \
        --region "$AWS_REGION"

    aws apigateway put-integration-response \
        --rest-api-id "$REST_API_ID" \
        --resource-id "$RESOURCE_ID" \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{"method.response.header.Access-Control-Allow-Headers":"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'","method.response.header.Access-Control-Allow-Methods":"'"'"'GET,POST,OPTIONS'"'"'","method.response.header.Access-Control-Allow-Origin":"'"'"'*'"'"'"}' \
        --region "$AWS_REGION" 2>/dev/null || true

    aws apigateway put-method-response \
        --rest-api-id "$REST_API_ID" \
        --resource-id "$RESOURCE_ID" \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{"method.response.header.Access-Control-Allow-Headers":true,"method.response.header.Access-Control-Allow-Methods":true,"method.response.header.Access-Control-Allow-Origin":true}' \
        --region "$AWS_REGION" 2>/dev/null || true

    # API 배포
    aws apigateway create-deployment \
        --rest-api-id "$REST_API_ID" \
        --stage-name "prod" \
        --region "$AWS_REGION"

    echo "   ✓ API Gateway configured"

    # API URL 출력
    echo ""
    echo "==================================="
    echo "Setup completed!"
    echo "API Endpoint: https://$REST_API_ID.execute-api.$AWS_REGION.amazonaws.com/prod/transcribe"
    echo "==================================="
else
    echo "   ⚠ API Gateway not found. Please create API Gateway first."
fi

# 정리
rm -f /tmp/bucket-policy.json
rm -f /tmp/trust-policy.json
rm -f /tmp/transcribe-policy.json
rm -f /tmp/lambda-transcribe.zip

echo ""
echo "✓ AWS Transcribe setup completed!"