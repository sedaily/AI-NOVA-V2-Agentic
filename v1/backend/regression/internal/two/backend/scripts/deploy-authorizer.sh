#!/bin/bash

# Lambda Authorizer 배포 스크립트

REGION="us-east-1"
FUNCTION_NAME="sedaily-column-authorizer"
LAYER_NAME="sedaily-authorizer-deps"

echo "🚀 Deploying Multi-tenant Lambda Authorizer..."
echo ""

# 1. 작업 디렉토리 생성
WORK_DIR="/tmp/lambda-authorizer-deploy"
rm -rf $WORK_DIR
mkdir -p $WORK_DIR
cd $WORK_DIR

echo "📦 Step 1: Preparing Lambda function package..."

# 2. 필요한 파일들 복사
PROJECT_DIR="/Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/칼럼/sedaily_ column/backend"

# 디렉토리 구조 생성
mkdir -p handlers/api
mkdir -p src/models
mkdir -p src/repositories

# 파일 복사
cp "$PROJECT_DIR/handlers/api/authorizer.py" handlers/api/
cp "$PROJECT_DIR/src/models/tenant.py" src/models/
cp "$PROJECT_DIR/src/repositories/tenant_repository.py" src/repositories/

# __init__.py 파일 생성
touch handlers/__init__.py
touch handlers/api/__init__.py
touch src/__init__.py
touch src/models/__init__.py
touch src/repositories/__init__.py

# 3. ZIP 파일 생성
echo "📦 Creating deployment package..."
zip -r authorizer.zip . -q

echo "✅ Package created: authorizer.zip"

# 4. Lambda Layer 생성 (의존성)
echo ""
echo "📦 Step 2: Creating Lambda Layer for dependencies..."

mkdir -p layer/python
cat > requirements.txt <<EOF
python-jose[cryptography]==3.3.0
cryptography==41.0.5
EOF

pip install -r requirements.txt -t layer/python --quiet

cd layer
zip -r ../layer.zip . -q
cd ..

# Layer 생성 또는 업데이트
echo "Publishing Lambda Layer..."
LAYER_VERSION=$(aws lambda publish-layer-version \
    --layer-name $LAYER_NAME \
    --description "Dependencies for sedaily authorizer" \
    --zip-file fileb://layer.zip \
    --compatible-runtimes python3.11 python3.10 python3.9 \
    --region $REGION \
    --query 'Version' \
    --output text 2>/dev/null)

if [ $? -eq 0 ]; then
    echo "✅ Layer published: Version $LAYER_VERSION"
    LAYER_ARN="arn:aws:lambda:$REGION:887078546492:layer:$LAYER_NAME:$LAYER_VERSION"
else
    echo "⚠️  Layer creation failed, continuing without layer"
    LAYER_ARN=""
fi

# 5. IAM Role 확인/생성
echo ""
echo "🔐 Step 3: Setting up IAM role..."

ROLE_NAME="sedaily-authorizer-role"
ROLE_ARN="arn:aws:iam::887078546492:role/$ROLE_NAME"

# Role이 있는지 확인
aws iam get-role --role-name $ROLE_NAME --region $REGION >/dev/null 2>&1

if [ $? -ne 0 ]; then
    echo "Creating IAM role..."

    # Trust policy
    cat > trust-policy.json <<EOF
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

    # Role 생성
    aws iam create-role \
        --role-name $ROLE_NAME \
        --assume-role-policy-document file://trust-policy.json \
        --region $REGION >/dev/null 2>&1

    # 기본 Lambda 실행 권한 추가
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
        --region $REGION

    # DynamoDB 권한 추가
    cat > dynamodb-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:Query",
        "dynamodb:UpdateItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:$REGION:887078546492:table/sedaily-column-tenants",
        "arn:aws:dynamodb:$REGION:887078546492:table/sedaily-column-user-tenants",
        "arn:aws:dynamodb:$REGION:887078546492:table/sedaily-column-user-tenants/index/*"
      ]
    }
  ]
}
EOF

    aws iam put-role-policy \
        --role-name $ROLE_NAME \
        --policy-name DynamoDBAccess \
        --policy-document file://dynamodb-policy.json \
        --region $REGION

    echo "✅ IAM role created"

    # Role 생성 후 잠시 대기 (AWS 전파 시간)
    echo "Waiting for IAM role to propagate..."
    sleep 10
else
    echo "✅ Using existing IAM role"
fi

# 6. Lambda 함수 생성 또는 업데이트
echo ""
echo "🚀 Step 4: Deploying Lambda function..."

# 함수 존재 여부 확인
aws lambda get-function --function-name $FUNCTION_NAME --region $REGION >/dev/null 2>&1

if [ $? -ne 0 ]; then
    # 함수 생성
    echo "Creating new Lambda function..."

    if [ -n "$LAYER_ARN" ]; then
        LAYER_PARAM="--layers $LAYER_ARN"
    else
        LAYER_PARAM=""
    fi

    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime python3.11 \
        --role $ROLE_ARN \
        --handler handlers.api.authorizer.handler \
        --zip-file fileb://authorizer.zip \
        --timeout 10 \
        --memory-size 256 \
        --environment Variables="{
            USER_POOL_ID=us-east-1_ohLOswurY,
            AWS_REGION=us-east-1,
            TENANTS_TABLE=sedaily-column-tenants,
            USER_TENANTS_TABLE=sedaily-column-user-tenants
        }" \
        $LAYER_PARAM \
        --region $REGION

    if [ $? -eq 0 ]; then
        echo "✅ Lambda function created successfully"
    else
        echo "❌ Failed to create Lambda function"
        exit 1
    fi
else
    # 함수 업데이트
    echo "Updating existing Lambda function..."

    # 코드 업데이트
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://authorizer.zip \
        --region $REGION >/dev/null

    # 설정 업데이트
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --environment Variables="{
            USER_POOL_ID=us-east-1_ohLOswurY,
            AWS_REGION=us-east-1,
            TENANTS_TABLE=sedaily-column-tenants,
            USER_TENANTS_TABLE=sedaily-column-user-tenants
        }" \
        --timeout 10 \
        --memory-size 256 \
        --region $REGION >/dev/null

    # Layer 업데이트
    if [ -n "$LAYER_ARN" ]; then
        aws lambda update-function-configuration \
            --function-name $FUNCTION_NAME \
            --layers $LAYER_ARN \
            --region $REGION >/dev/null
    fi

    echo "✅ Lambda function updated successfully"
fi

# 7. 함수 정보 출력
echo ""
echo "📊 Function Details:"
FUNCTION_ARN=$(aws lambda get-function --function-name $FUNCTION_NAME --region $REGION --query 'Configuration.FunctionArn' --output text)
echo "  Name: $FUNCTION_NAME"
echo "  ARN: $FUNCTION_ARN"
echo "  Region: $REGION"
if [ -n "$LAYER_ARN" ]; then
    echo "  Layer: $LAYER_ARN"
fi

# 8. 정리
echo ""
echo "🧹 Cleaning up temporary files..."
rm -rf $WORK_DIR

echo ""
echo "========================================="
echo "✨ Lambda Authorizer Deployment Complete!"
echo "========================================="
echo ""
echo "📋 Next Steps:"
echo "  1. Go to API Gateway console"
echo "  2. Create a new Authorizer with this Lambda function"
echo "  3. Apply the Authorizer to your API endpoints"
echo ""
echo "🔧 Lambda Function ARN for API Gateway:"
echo "  $FUNCTION_ARN"
echo ""
echo "📝 Test command:"
echo "  aws lambda invoke \\"
echo "    --function-name $FUNCTION_NAME \\"
echo "    --payload '{\"authorizationToken\": \"Bearer YOUR_JWT_TOKEN\", \"methodArn\": \"arn:aws:execute-api:us-east-1:*:*/GET/*\"}' \\"
echo "    response.json"