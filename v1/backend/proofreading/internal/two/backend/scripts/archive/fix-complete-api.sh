#!/bin/bash

# 완전한 API 수정 스크립트

set -e

API_ID="wxwdb89w4m"
REGION="us-east-1"
STAGE="prod"

echo "=========================================="
echo "완전한 API 설정 수정"
echo "=========================================="

# 1. DELETE 메서드 추가
echo "1. /conversations/{id} DELETE 메서드 추가..."
CONV_ID_RESOURCE=$(aws apigateway get-resources --rest-api-id ${API_ID} --region ${REGION} --query "items[?path=='/conversations/{id}'].id" --output text)

if [ ! -z "$CONV_ID_RESOURCE" ]; then
    # DELETE 메서드 추가
    aws apigateway put-method \
        --rest-api-id ${API_ID} \
        --resource-id ${CONV_ID_RESOURCE} \
        --http-method DELETE \
        --authorization-type NONE \
        --region ${REGION} \
        --no-cli-pager 2>/dev/null || echo "   DELETE method already exists"
    
    # Lambda Integration
    aws apigateway put-integration \
        --rest-api-id ${API_ID} \
        --resource-id ${CONV_ID_RESOURCE} \
        --http-method DELETE \
        --type AWS_PROXY \
        --integration-http-method POST \
        --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:887078546492:function:nx-wt-prf-conversation-handler/invocations" \
        --region ${REGION} \
        --no-cli-pager 2>/dev/null || true
    
    # Method Response
    aws apigateway put-method-response \
        --rest-api-id ${API_ID} \
        --resource-id ${CONV_ID_RESOURCE} \
        --http-method DELETE \
        --status-code 200 \
        --response-parameters '{
            "method.response.header.Access-Control-Allow-Origin": false
        }' \
        --region ${REGION} \
        --no-cli-pager 2>/dev/null || true
    
    # OPTIONS 메서드 업데이트 (DELETE 포함)
    aws apigateway put-integration-response \
        --rest-api-id ${API_ID} \
        --resource-id ${CONV_ID_RESOURCE} \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{
            "method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'\''",
            "method.response.header.Access-Control-Allow-Methods": "'\''GET,DELETE,OPTIONS'\''",
            "method.response.header.Access-Control-Allow-Origin": "'\''*'\''"
        }' \
        --region ${REGION} \
        --no-cli-pager 2>/dev/null || true
    
    echo "   ✓ DELETE 메서드 설정 완료"
fi

# 2. Lambda 함수 재배포가 필요한지 확인
echo -e "\n2. Lambda 함수 상태 확인..."
for func in nx-wt-prf-conversation-api nx-wt-prf-conversation-handler; do
    echo "   - $func:"
    aws lambda get-function-configuration \
        --function-name $func \
        --region ${REGION} \
        --query '{State: State, LastModified: LastModified, Runtime: Runtime}' \
        --output json 2>/dev/null || echo "     함수를 찾을 수 없음"
done

# 3. Lambda 권한 재설정
echo -e "\n3. Lambda 권한 설정..."

# conversation-api 권한
aws lambda add-permission \
    --function-name nx-wt-prf-conversation-api \
    --statement-id apigateway-rest-all \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:${REGION}:887078546492:${API_ID}/*/*" \
    --region ${REGION} \
    --no-cli-pager 2>/dev/null || echo "   - conversation-api 권한 이미 존재"

# conversation-handler 권한 (conversations/{id} 용)
aws lambda add-permission \
    --function-name nx-wt-prf-conversation-handler \
    --statement-id apigateway-rest-conv-id \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:${REGION}:887078546492:${API_ID}/*/*" \
    --region ${REGION} \
    --no-cli-pager 2>/dev/null || echo "   - conversation-handler 권한 이미 존재"

# 4. API 배포
echo -e "\n4. API 재배포..."
DEPLOYMENT_ID=$(aws apigateway create-deployment \
    --rest-api-id ${API_ID} \
    --stage-name ${STAGE} \
    --description "Complete API fix $(date +%Y-%m-%d_%H:%M:%S)" \
    --region ${REGION} \
    --query 'id' \
    --output text)

echo "   ✓ 배포 완료 (Deployment ID: ${DEPLOYMENT_ID})"

# 5. 리소스 및 메서드 확인
echo -e "\n5. 설정된 리소스 및 메서드:"
aws apigateway get-resources \
    --rest-api-id ${API_ID} \
    --region ${REGION} \
    --output json | jq -r '.items[] | "\(.path) -> \(if .resourceMethods then (.resourceMethods | keys | join(", ")) else "no methods" end)"' | sort

echo ""
echo "=========================================="
echo "✅ API 설정 완료!"
echo "=========================================="
echo ""
echo "⚠️  Lambda 함수가 500 에러를 반환하는 경우:"
echo "   1. Lambda 함수 코드 재배포가 필요할 수 있습니다"
echo "   2. DynamoDB 권한 확인이 필요할 수 있습니다"
echo "   3. 환경 변수 설정을 확인하세요"
echo "=========================================="