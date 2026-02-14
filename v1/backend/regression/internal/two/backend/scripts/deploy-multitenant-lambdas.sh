#!/bin/bash

# 멀티테넌트 지원 Lambda 함수 배포 스크립트

REGION="us-east-1"
PROFILE="default"

echo "🚀 Deploying Multi-tenant Lambda Functions..."
echo ""

# 작업 디렉토리
PROJECT_DIR="/Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/칼럼/sedaily_ column/backend"
WORK_DIR="/tmp/lambda-deploy-$(date +%s)"

mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# 1. conversation-api 배포
echo "📦 1. Deploying sedaily-column-conversation-api..."

# 패키지 생성
mkdir -p conversation-package
cd conversation-package

# 필요한 파일 복사
cp -r "$PROJECT_DIR/handlers" ./
cp -r "$PROJECT_DIR/src" ./
cp -r "$PROJECT_DIR/utils" ./
cp -r "$PROJECT_DIR/lib" ./

# __init__.py 파일 확인
find . -type d -exec touch {}/__init__.py \;

# ZIP 생성
zip -r ../conversation.zip . -q

cd ..

# Lambda 업데이트
aws lambda update-function-code \
    --function-name sedaily-column-conversation-api \
    --zip-file fileb://conversation.zip \
    --region $REGION \
    --profile $PROFILE >/dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ conversation-api updated successfully"
else
    echo "⚠️  conversation-api update failed or function doesn't exist"
fi

# 2. prompt-crud 배포
echo "📦 2. Deploying sedaily-column-prompt-crud..."

# 패키지 생성 (동일한 구조 사용)
cp conversation.zip prompt.zip

# Lambda 업데이트
aws lambda update-function-code \
    --function-name sedaily-column-prompt-crud \
    --zip-file fileb://prompt.zip \
    --region $REGION \
    --profile $PROFILE >/dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ prompt-crud updated successfully"
else
    echo "⚠️  prompt-crud update failed or function doesn't exist"
fi

# 3. usage-handler 배포
echo "📦 3. Deploying sedaily-column-usage-handler..."

# 패키지 생성 (동일한 구조 사용)
cp conversation.zip usage.zip

# Lambda 업데이트
aws lambda update-function-code \
    --function-name sedaily-column-usage-handler \
    --zip-file fileb://usage.zip \
    --region $REGION \
    --profile $PROFILE >/dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ usage-handler updated successfully"
else
    echo "⚠️  usage-handler update failed or function doesn't exist"
fi

# 4. Authorizer 재배포 (코드 변경이 있었으므로)
echo "📦 4. Re-deploying sedaily-column-authorizer..."

# Authorizer 패키지 생성
mkdir -p authorizer-package
cd authorizer-package

# 필요한 파일 복사
mkdir -p handlers/api
cp "$PROJECT_DIR/handlers/api/authorizer.py" handlers/api/

mkdir -p src/models
cp "$PROJECT_DIR/src/models/tenant.py" src/models/

mkdir -p src/repositories
cp "$PROJECT_DIR/src/repositories/tenant_repository.py" src/repositories/

# __init__.py 파일 생성
find . -type d -exec touch {}/__init__.py \;

# ZIP 생성
zip -r ../authorizer.zip . -q

cd ..

# Lambda 업데이트
aws lambda update-function-code \
    --function-name sedaily-column-authorizer \
    --zip-file fileb://authorizer.zip \
    --region $REGION \
    --profile $PROFILE >/dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ authorizer updated successfully"
else
    echo "⚠️  authorizer update failed"
fi

# 5. 배포 확인
echo ""
echo "📊 Verifying deployments..."

# 각 함수의 최근 업데이트 시간 확인
for func in sedaily-column-conversation-api sedaily-column-prompt-crud sedaily-column-usage-handler sedaily-column-authorizer; do
    LAST_MODIFIED=$(aws lambda get-function \
        --function-name $func \
        --region $REGION \
        --profile $PROFILE \
        --query 'Configuration.LastModified' \
        --output text 2>/dev/null)

    if [ $? -eq 0 ]; then
        echo "  $func: Last updated $LAST_MODIFIED"
    else
        echo "  $func: Not found"
    fi
done

# 정리
echo ""
echo "🧹 Cleaning up..."
rm -rf "$WORK_DIR"

echo ""
echo "========================================="
echo "✨ Lambda Deployment Complete!"
echo "========================================="
echo ""
echo "📋 Deployed functions:"
echo "  - sedaily-column-conversation-api (multi-tenant ready)"
echo "  - sedaily-column-prompt-crud (multi-tenant ready)"
echo "  - sedaily-column-usage-handler (multi-tenant ready)"
echo "  - sedaily-column-authorizer (updated)"
echo ""
echo "⚡ Next steps:"
echo "  1. Test with existing users (backward compatibility)"
echo "  2. Test with Authorizer enabled endpoints"
echo "  3. Monitor CloudWatch logs for any errors"
echo ""
echo "🔧 Test commands:"
echo "  # Without Authorizer (existing method)"
echo "  curl https://t75vorhge1.execute-api.us-east-1.amazonaws.com/prod/conversations?userId=test"
echo ""
echo "  # With Authorizer (new method)"
echo "  curl https://t75vorhge1.execute-api.us-east-1.amazonaws.com/prod/conversations \\"
echo "    -H 'Authorization: Bearer YOUR_JWT_TOKEN'"