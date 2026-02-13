#!/bin/bash

# WebSocket Lambda 권한 수정 스크립트

set -e

REGION="us-east-1"
WEBSOCKET_API_ID="p062xh167h"
ACCOUNT_ID="887078546492"

echo "=========================================="
echo "WebSocket Lambda 권한 설정"
echo "=========================================="

# 1. sendMessage 라우트 권한 추가
echo "1. sendMessage 라우트 권한 추가..."
aws lambda add-permission \
  --function-name nx-wt-prf-websocket-message \
  --statement-id websocket-sendMessage-route \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${WEBSOCKET_API_ID}/*/sendMessage" \
  --region ${REGION} \
  --no-cli-pager 2>/dev/null || echo "   - sendMessage 권한 이미 존재"

# 2. $default 라우트 권한 추가
echo "2. \$default 라우트 권한 추가..."
aws lambda add-permission \
  --function-name nx-wt-prf-websocket-message \
  --statement-id websocket-default-route \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${WEBSOCKET_API_ID}/*/$default" \
  --region ${REGION} \
  --no-cli-pager 2>/dev/null || echo "   - \$default 권한 이미 존재"

# 3. 전체 API 권한 추가 (fallback)
echo "3. WebSocket API 전체 권한 추가..."
aws lambda add-permission \
  --function-name nx-wt-prf-websocket-message \
  --statement-id websocket-api-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${WEBSOCKET_API_ID}/*/*" \
  --region ${REGION} \
  --no-cli-pager 2>/dev/null || echo "   - API 전체 권한 이미 존재"

# 4. Connect 핸들러 권한
echo "4. Connect 핸들러 권한..."
aws lambda add-permission \
  --function-name nx-wt-prf-websocket-connect \
  --statement-id websocket-connect-route \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${WEBSOCKET_API_ID}/*/$connect" \
  --region ${REGION} \
  --no-cli-pager 2>/dev/null || echo "   - Connect 권한 이미 존재"

# 5. Disconnect 핸들러 권한
echo "5. Disconnect 핸들러 권한..."
aws lambda add-permission \
  --function-name nx-wt-prf-websocket-disconnect \
  --statement-id websocket-disconnect-route \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${WEBSOCKET_API_ID}/*/$disconnect" \
  --region ${REGION} \
  --no-cli-pager 2>/dev/null || echo "   - Disconnect 권한 이미 존재"

echo ""
echo "6. 현재 Lambda 권한 확인..."
echo "   Message Handler:"
aws lambda get-policy --function-name nx-wt-prf-websocket-message --region ${REGION} --query 'Policy' --output text 2>/dev/null | python3 -m json.tool | grep -E '"Sid"|"Resource"' | head -10 || echo "   권한 조회 실패"

# 7. WebSocket API 재배포
echo ""
echo "7. WebSocket API 재배포..."
DEPLOYMENT_ID=$(aws apigatewayv2 create-deployment \
  --api-id ${WEBSOCKET_API_ID} \
  --stage-name prod \
  --region ${REGION} \
  --query 'DeploymentId' \
  --output text 2>/dev/null) || echo "   배포 실패 또는 이미 배포됨"

if [ ! -z "$DEPLOYMENT_ID" ]; then
  echo "   ✓ 배포 완료 (Deployment ID: ${DEPLOYMENT_ID})"
fi

echo ""
echo "=========================================="
echo "✅ WebSocket Lambda 권한 설정 완료!"
echo "WebSocket URL: wss://${WEBSOCKET_API_ID}.execute-api.${REGION}.amazonaws.com/prod"
echo "=========================================="