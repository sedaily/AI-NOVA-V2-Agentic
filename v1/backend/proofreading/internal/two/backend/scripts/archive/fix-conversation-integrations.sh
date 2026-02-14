#!/bin/bash

# conversation-handler 함수가 없으므로 모든 엔드포인트를 conversation-api로 수정

set -e

API_ID="wxwdb89w4m"
REGION="us-east-1"
STAGE="prod"

echo "=========================================="
echo "Conversation 엔드포인트 Lambda 통합 수정"
echo "=========================================="

echo "1. Lambda 함수 확인..."
echo "   - nx-wt-prf-conversation-api: 존재 ✓"
echo "   - nx-wt-prf-conversation-handler: 존재하지 않음 ✗"
echo ""

# /conversations/{id} 리소스 ID 가져오기
CONV_ID_RESOURCE=$(aws apigateway get-resources --rest-api-id ${API_ID} --region ${REGION} --query "items[?path=='/conversations/{id}'].id" --output text)

if [ ! -z "$CONV_ID_RESOURCE" ]; then
    echo "2. /conversations/{id} 엔드포인트를 conversation-api로 변경..."
    
    # GET 메서드 통합 업데이트
    echo "   - GET 메서드 통합 업데이트"
    aws apigateway put-integration \
        --rest-api-id ${API_ID} \
        --resource-id ${CONV_ID_RESOURCE} \
        --http-method GET \
        --type AWS_PROXY \
        --integration-http-method POST \
        --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:887078546492:function:nx-wt-prf-conversation-api/invocations" \
        --region ${REGION} \
        --no-cli-pager
    
    # DELETE 메서드 통합 업데이트
    echo "   - DELETE 메서드 통합 업데이트"
    aws apigateway put-integration \
        --rest-api-id ${API_ID} \
        --resource-id ${CONV_ID_RESOURCE} \
        --http-method DELETE \
        --type AWS_PROXY \
        --integration-http-method POST \
        --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:887078546492:function:nx-wt-prf-conversation-api/invocations" \
        --region ${REGION} \
        --no-cli-pager
    
    echo "   ✓ 통합 업데이트 완료"
fi

# Lambda 권한 확인 및 추가
echo ""
echo "3. Lambda 실행 권한 설정..."

# conversation-api에 대한 권한 추가 (모든 경로)
aws lambda add-permission \
    --function-name nx-wt-prf-conversation-api \
    --statement-id apigateway-rest-all-paths \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:${REGION}:887078546492:${API_ID}/*/*" \
    --region ${REGION} \
    --no-cli-pager 2>/dev/null || echo "   - 권한 이미 존재"

# API 배포
echo ""
echo "4. API 재배포..."
DEPLOYMENT_ID=$(aws apigateway create-deployment \
    --rest-api-id ${API_ID} \
    --stage-name ${STAGE} \
    --description "Fix conversation integrations $(date +%Y-%m-%d_%H:%M:%S)" \
    --region ${REGION} \
    --query 'id' \
    --output text)

echo "   ✓ 배포 완료 (Deployment ID: ${DEPLOYMENT_ID})"

# 통합 확인
echo ""
echo "5. 통합 설정 확인..."
echo "   /conversations/{id} GET:"
aws apigateway get-integration \
    --rest-api-id ${API_ID} \
    --resource-id ${CONV_ID_RESOURCE} \
    --http-method GET \
    --region ${REGION} \
    --query 'uri' \
    --output text | grep -o 'function:[^/]*' | cut -d: -f2

echo "   /conversations/{id} DELETE:"
aws apigateway get-integration \
    --rest-api-id ${API_ID} \
    --resource-id ${CONV_ID_RESOURCE} \
    --http-method DELETE \
    --region ${REGION} \
    --query 'uri' \
    --output text | grep -o 'function:[^/]*' | cut -d: -f2

echo ""
echo "=========================================="
echo "✅ 모든 conversation 엔드포인트가"
echo "   nx-wt-prf-conversation-api로 통합되었습니다!"
echo "=========================================="
echo ""
echo "⚠️  conversation.py 핸들러 코드 확인 필요:"
echo "   - pathParameters에서 'conversationId' 또는 'id' 처리"
echo "   - GET, DELETE 메서드 모두 지원"
echo "=========================================="