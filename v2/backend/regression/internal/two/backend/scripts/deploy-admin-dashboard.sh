#!/bin/bash

# Admin Dashboard Lambda 함수 생성 및 배포 스크립트

REGION="us-east-1"
FUNCTION_NAME="sedaily-column-admin-dashboard"
ROLE_ARN="arn:aws:iam::887078546492:role/sedaily-column-lambda-execution-role"
API_ID="t75vorhge1"

echo "🚀 Admin Dashboard Lambda 배포 시작..."

# 작업 디렉토리 설정
PROJECT_DIR="/Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/칼럼/sedaily_ column/backend"
WORK_DIR="/tmp/admin-dashboard-deploy-$(date +%s)"

mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

echo "📦 패키지 생성 중..."

# 필요한 파일 복사
cp -r "$PROJECT_DIR/handlers" ./
cp -r "$PROJECT_DIR/src" ./
cp -r "$PROJECT_DIR/utils" ./
cp -r "$PROJECT_DIR/lib" ./

# __init__.py 파일 생성
find . -type d -exec touch {}/__init__.py \;

# ZIP 생성
zip -r admin-dashboard.zip . -q

echo "🔧 Lambda 함수 확인 중..."

# 함수가 존재하는지 확인
aws lambda get-function --function-name $FUNCTION_NAME --region $REGION >/dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "📝 기존 함수 업데이트..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://admin-dashboard.zip \
        --region $REGION >/dev/null 2>&1
else
    echo "🆕 새 함수 생성..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime python3.12 \
        --role $ROLE_ARN \
        --handler handlers.api.admin_dashboard.handler \
        --zip-file fileb://admin-dashboard.zip \
        --timeout 30 \
        --memory-size 256 \
        --environment Variables="{
            AWS_REGION=$REGION,
            TENANTS_TABLE=sedaily-column-tenants,
            USER_TENANTS_TABLE=sedaily-column-user-tenants,
            USAGE_TABLE=sedaily-column-usage
        }" \
        --region $REGION >/dev/null 2>&1
fi

if [ $? -eq 0 ]; then
    echo "✅ Lambda 함수 배포 성공!"
else
    echo "❌ Lambda 함수 배포 실패"
    exit 1
fi

# API Gateway 권한 추가
echo "🔐 API Gateway 권한 설정..."

aws lambda add-permission \
    --function-name $FUNCTION_NAME \
    --statement-id "apigateway-admin-$(date +%s)" \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:$REGION:887078546492:$API_ID/*/*" \
    --region $REGION >/dev/null 2>&1

# 정리
rm -rf "$WORK_DIR"

echo ""
echo "========================================="
echo "✨ Admin Dashboard 배포 완료!"
echo "========================================="
echo ""
echo "📋 배포 정보:"
echo "  - Lambda 함수: $FUNCTION_NAME"
echo "  - Region: $REGION"
echo "  - Handler: handlers.api.admin_dashboard.handler"
echo ""
echo "🔧 다음 단계:"
echo "  1. API Gateway에 라우트 추가"
echo "  2. CORS 설정"
echo "  3. 대시보드에서 API 연결"