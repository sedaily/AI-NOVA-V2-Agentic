#!/bin/bash

# API Gateway CORS 설정 스크립트
# REST API에 CORS 활성화

set -e

API_ID="wxwdb89w4m"
REGION="us-east-1"
STAGE="prod"

echo "=========================================="
echo "API Gateway CORS 설정 시작"
echo "API ID: ${API_ID}"
echo "Region: ${REGION}"
echo "=========================================="

# 모든 리소스 조회
echo "1. 리소스 목록 조회..."
RESOURCES=$(aws apigateway get-resources \
    --rest-api-id ${API_ID} \
    --region ${REGION} \
    --query "items[*].[id, path]" \
    --output json)

echo "찾은 리소스:"
echo "$RESOURCES" | jq -r '.[] | "\(.[0]): \(.[1])"'

# 각 리소스에 OPTIONS 메서드 추가
echo -e "\n2. OPTIONS 메서드 추가..."
echo "$RESOURCES" | jq -r '.[] | .[0]' | while read RESOURCE_ID; do
    RESOURCE_PATH=$(echo "$RESOURCES" | jq -r --arg id "$RESOURCE_ID" '.[] | select(.[0] == $id) | .[1]')
    echo "   - 리소스: ${RESOURCE_PATH} (${RESOURCE_ID})"
    
    # OPTIONS 메서드가 이미 있는지 확인
    OPTIONS_EXISTS=$(aws apigateway get-method \
        --rest-api-id ${API_ID} \
        --resource-id ${RESOURCE_ID} \
        --http-method OPTIONS \
        --region ${REGION} 2>/dev/null || echo "NOT_EXISTS")
    
    if [ "$OPTIONS_EXISTS" = "NOT_EXISTS" ]; then
        # OPTIONS 메서드 추가
        aws apigateway put-method \
            --rest-api-id ${API_ID} \
            --resource-id ${RESOURCE_ID} \
            --http-method OPTIONS \
            --authorization-type NONE \
            --region ${REGION} \
            --no-cli-pager > /dev/null 2>&1 || true
        
        # Mock Integration 설정
        aws apigateway put-integration \
            --rest-api-id ${API_ID} \
            --resource-id ${RESOURCE_ID} \
            --http-method OPTIONS \
            --type MOCK \
            --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
            --region ${REGION} \
            --no-cli-pager > /dev/null 2>&1 || true
        
        # Integration Response 설정
        aws apigateway put-integration-response \
            --rest-api-id ${API_ID} \
            --resource-id ${RESOURCE_ID} \
            --http-method OPTIONS \
            --status-code 200 \
            --response-parameters '{
                "method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'\''",
                "method.response.header.Access-Control-Allow-Methods": "'\''GET,POST,PUT,DELETE,OPTIONS,PATCH'\''",
                "method.response.header.Access-Control-Allow-Origin": "'\''*'\''"
            }' \
            --response-templates '{"application/json": ""}' \
            --region ${REGION} \
            --no-cli-pager > /dev/null 2>&1 || true
        
        # Method Response 설정
        aws apigateway put-method-response \
            --rest-api-id ${API_ID} \
            --resource-id ${RESOURCE_ID} \
            --http-method OPTIONS \
            --status-code 200 \
            --response-parameters '{
                "method.response.header.Access-Control-Allow-Headers": false,
                "method.response.header.Access-Control-Allow-Methods": false,
                "method.response.header.Access-Control-Allow-Origin": false
            }' \
            --region ${REGION} \
            --no-cli-pager > /dev/null 2>&1 || true
        
        echo "     ✓ OPTIONS 메서드 추가됨"
    else
        echo "     - OPTIONS 메서드 이미 존재"
    fi
done

# GET, POST, PUT, DELETE 메서드에 CORS 헤더 추가
echo -e "\n3. 기존 메서드에 CORS 헤더 추가..."
for METHOD in GET POST PUT DELETE PATCH; do
    echo "   ${METHOD} 메서드 처리 중..."
    
    echo "$RESOURCES" | jq -r '.[] | .[0]' | while read RESOURCE_ID; do
        RESOURCE_PATH=$(echo "$RESOURCES" | jq -r --arg id "$RESOURCE_ID" '.[] | select(.[0] == $id) | .[1]')
        
        # 메서드가 존재하는지 확인
        METHOD_EXISTS=$(aws apigateway get-method \
            --rest-api-id ${API_ID} \
            --resource-id ${RESOURCE_ID} \
            --http-method ${METHOD} \
            --region ${REGION} 2>/dev/null || echo "NOT_EXISTS")
        
        if [ "$METHOD_EXISTS" != "NOT_EXISTS" ]; then
            echo "     - ${RESOURCE_PATH}: ${METHOD} 메서드 CORS 헤더 추가"
            
            # Method Response에 CORS 헤더 추가
            aws apigateway put-method-response \
                --rest-api-id ${API_ID} \
                --resource-id ${RESOURCE_ID} \
                --http-method ${METHOD} \
                --status-code 200 \
                --response-parameters '{
                    "method.response.header.Access-Control-Allow-Origin": false,
                    "method.response.header.Access-Control-Allow-Headers": false,
                    "method.response.header.Access-Control-Allow-Methods": false
                }' \
                --region ${REGION} \
                --no-cli-pager > /dev/null 2>&1 || true
        fi
    done
done

# API 배포
echo -e "\n4. API 배포..."
DEPLOYMENT_ID=$(aws apigateway create-deployment \
    --rest-api-id ${API_ID} \
    --stage-name ${STAGE} \
    --description "CORS 설정 배포 $(date +%Y-%m-%d_%H:%M:%S)" \
    --region ${REGION} \
    --query 'id' \
    --output text)

echo "   ✓ 배포 완료 (Deployment ID: ${DEPLOYMENT_ID})"

# API 엔드포인트 확인
echo -e "\n=========================================="
echo "CORS 설정 완료!"
echo "API Endpoint: https://${API_ID}.execute-api.${REGION}.amazonaws.com/${STAGE}"
echo "=========================================="

# CORS 테스트
echo -e "\n5. CORS 테스트..."
echo "   테스트 명령어:"
echo "   curl -X OPTIONS https://${API_ID}.execute-api.${REGION}.amazonaws.com/${STAGE}/prompts/T5 -I"