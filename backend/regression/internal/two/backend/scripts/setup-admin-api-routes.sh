#!/bin/bash

# Admin Dashboard API Gateway 라우트 설정 스크립트

API_ID="t75vorhge1"
REGION="us-east-1"
PARENT_ID=$(aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path == '/'].id" --output text)
LAMBDA_URI="arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/arn:aws:lambda:$REGION:887078546492:function:sedaily-column-admin-dashboard/invocations"

echo "🔧 Admin API Routes 설정 시작..."
echo "  API ID: $API_ID"
echo "  Parent ID: $PARENT_ID"

# /admin 리소스 생성 또는 찾기
echo "📝 /admin 리소스 확인..."
ADMIN_ID=$(aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path == '/admin'].id" --output text)

if [ -z "$ADMIN_ID" ]; then
    echo "🆕 /admin 리소스 생성..."
    ADMIN_ID=$(aws apigateway create-resource \
        --rest-api-id $API_ID \
        --parent-id $PARENT_ID \
        --path-part "admin" \
        --region $REGION \
        --query "id" \
        --output text)
    echo "  Created: /admin ($ADMIN_ID)"
else
    echo "  Found: /admin ($ADMIN_ID)"
fi

# /admin/dashboard 리소스 생성
echo "📝 /admin/dashboard 리소스 확인..."
DASHBOARD_ID=$(aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path == '/admin/dashboard'].id" --output text)

if [ -z "$DASHBOARD_ID" ]; then
    echo "🆕 /admin/dashboard 리소스 생성..."
    DASHBOARD_ID=$(aws apigateway create-resource \
        --rest-api-id $API_ID \
        --parent-id $ADMIN_ID \
        --path-part "dashboard" \
        --region $REGION \
        --query "id" \
        --output text)
fi

# /admin/tenants 리소스 생성
echo "📝 /admin/tenants 리소스 확인..."
TENANTS_ID=$(aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path == '/admin/tenants'].id" --output text)

if [ -z "$TENANTS_ID" ]; then
    echo "🆕 /admin/tenants 리소스 생성..."
    TENANTS_ID=$(aws apigateway create-resource \
        --rest-api-id $API_ID \
        --parent-id $ADMIN_ID \
        --path-part "tenants" \
        --region $REGION \
        --query "id" \
        --output text)
fi

# /admin/users 리소스 생성
echo "📝 /admin/users 리소스 확인..."
USERS_ID=$(aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path == '/admin/users'].id" --output text)

if [ -z "$USERS_ID" ]; then
    echo "🆕 /admin/users 리소스 생성..."
    USERS_ID=$(aws apigateway create-resource \
        --rest-api-id $API_ID \
        --parent-id $ADMIN_ID \
        --path-part "users" \
        --region $REGION \
        --query "id" \
        --output text)
fi

# /admin/usage 리소스 생성
echo "📝 /admin/usage 리소스 확인..."
USAGE_ID=$(aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path == '/admin/usage'].id" --output text)

if [ -z "$USAGE_ID" ]; then
    echo "🆕 /admin/usage 리소스 생성..."
    USAGE_ID=$(aws apigateway create-resource \
        --rest-api-id $API_ID \
        --parent-id $ADMIN_ID \
        --path-part "usage" \
        --region $REGION \
        --query "id" \
        --output text)
fi

# 각 리소스에 대해 GET/PUT 메서드 설정
setup_methods() {
    local RESOURCE_ID=$1
    local RESOURCE_NAME=$2

    echo "  🔧 $RESOURCE_NAME 메서드 설정..."

    # OPTIONS 메서드 (CORS)
    aws apigateway put-method \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --authorization-type NONE \
        --region $REGION >/dev/null 2>&1

    aws apigateway put-integration \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --type MOCK \
        --integration-http-method OPTIONS \
        --request-templates '{"application/json":"{\"statusCode\": 200}"}' \
        --region $REGION >/dev/null 2>&1

    aws apigateway put-method-response \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{"method.response.header.Access-Control-Allow-Headers":false,"method.response.header.Access-Control-Allow-Methods":false,"method.response.header.Access-Control-Allow-Origin":false}' \
        --region $REGION >/dev/null 2>&1

    aws apigateway put-integration-response \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{"method.response.header.Access-Control-Allow-Headers":"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'","method.response.header.Access-Control-Allow-Methods":"'"'"'GET,POST,PUT,DELETE,OPTIONS'"'"'","method.response.header.Access-Control-Allow-Origin":"'"'"'*'"'"'"}' \
        --region $REGION >/dev/null 2>&1

    # GET 메서드
    aws apigateway put-method \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method GET \
        --authorization-type NONE \
        --region $REGION >/dev/null 2>&1

    aws apigateway put-integration \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method GET \
        --type AWS_PROXY \
        --integration-http-method POST \
        --uri $LAMBDA_URI \
        --region $REGION >/dev/null 2>&1

    # PUT 메서드 (update용)
    aws apigateway put-method \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method PUT \
        --authorization-type NONE \
        --region $REGION >/dev/null 2>&1

    aws apigateway put-integration \
        --rest-api-id $API_ID \
        --resource-id $RESOURCE_ID \
        --http-method PUT \
        --type AWS_PROXY \
        --integration-http-method POST \
        --uri $LAMBDA_URI \
        --region $REGION >/dev/null 2>&1

    echo "    ✅ $RESOURCE_NAME 설정 완료"
}

echo ""
echo "🔨 메서드 설정..."
setup_methods $DASHBOARD_ID "/admin/dashboard"
setup_methods $TENANTS_ID "/admin/tenants"
setup_methods $USERS_ID "/admin/users"
setup_methods $USAGE_ID "/admin/usage"

# API 배포
echo ""
echo "🚀 API Gateway 배포..."
aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name prod \
    --description "Admin Dashboard API deployment $(date)" \
    --region $REGION >/dev/null

echo ""
echo "========================================="
echo "✨ Admin API Routes 설정 완료!"
echo "========================================="
echo ""
echo "📋 생성된 엔드포인트:"
echo "  GET  https://$API_ID.execute-api.$REGION.amazonaws.com/prod/admin/dashboard"
echo "  GET  https://$API_ID.execute-api.$REGION.amazonaws.com/prod/admin/tenants"
echo "  GET  https://$API_ID.execute-api.$REGION.amazonaws.com/prod/admin/users"
echo "  GET  https://$API_ID.execute-api.$REGION.amazonaws.com/prod/admin/usage"
echo ""
echo "🔧 테스트:"
echo "  curl https://$API_ID.execute-api.$REGION.amazonaws.com/prod/admin/dashboard"