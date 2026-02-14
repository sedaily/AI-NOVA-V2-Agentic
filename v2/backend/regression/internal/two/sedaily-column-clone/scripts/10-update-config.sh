#!/bin/bash

# 환경설정 및 최종 정보 업데이트

source "$(dirname "$0")/00-config.sh"

log_info "환경설정 및 최종 정보 업데이트 시작..."

# API 엔드포인트 정보 가져오기
REST_API_ID=$(aws apigateway get-rest-apis \
    --query "items[?name=='$REST_API_NAME'].id" \
    --output text --region "$REGION")

WS_API_ID=$(aws apigatewayv2 get-apis \
    --query "Items[?Name=='$WEBSOCKET_API_NAME'].ApiId" \
    --output text --region "$REGION")

CF_DOMAIN=$(grep "CLOUDFRONT_DOMAIN" "$PROJECT_ROOT/endpoints.txt" | cut -d'=' -f2 || echo "")
CF_DISTRIBUTION_ID=$(grep "CLOUDFRONT_DISTRIBUTION_ID" "$PROJECT_ROOT/endpoints.txt" | cut -d'=' -f2 || echo "")

# 최종 엔드포인트 정보 파일 생성 (JSON)
log_info "엔드포인트 정보 파일 생성 중..."

cat > "$PROJECT_ROOT/endpoints.json" <<EOF
{
    "service": "$SERVICE_NAME",
    "region": "$REGION",
    "accountId": "$ACCOUNT_ID",
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "endpoints": {
        "rest_api": {
            "id": "$REST_API_ID",
            "url": "https://${REST_API_ID}.execute-api.${REGION}.amazonaws.com/prod",
            "stage": "prod"
        },
        "websocket_api": {
            "id": "$WS_API_ID",
            "url": "wss://${WS_API_ID}.execute-api.${REGION}.amazonaws.com/prod",
            "stage": "prod"
        },
        "cloudfront": {
            "distributionId": "$CF_DISTRIBUTION_ID",
            "domain": "$CF_DOMAIN",
            "url": "https://$CF_DOMAIN"
        },
        "s3": {
            "bucket": "$S3_BUCKET",
            "region": "$REGION"
        }
    },
    "lambda_functions": {
        "connect": "$LAMBDA_CONNECT",
        "disconnect": "$LAMBDA_DISCONNECT",
        "message": "$LAMBDA_MESSAGE",
        "conversation": "$LAMBDA_CONVERSATION",
        "prompt": "$LAMBDA_PROMPT",
        "usage": "$LAMBDA_USAGE"
    },
    "dynamodb_tables": {
        "conversations": "$TABLE_CONVERSATIONS",
        "prompts": "$TABLE_PROMPTS",
        "usage": "$TABLE_USAGE",
        "connections": "$TABLE_CONNECTIONS"
    }
}
EOF

log_success "엔드포인트 정보 파일 생성 완료: endpoints.json"

# README 파일 생성
log_info "README 파일 생성 중..."

cat > "$PROJECT_ROOT/DEPLOYMENT_INFO.md" <<EOF
# ${SERVICE_NAME} 배포 정보

## 배포 정보
- **서비스명**: ${SERVICE_NAME}
- **리전**: ${REGION}
- **배포 시간**: $(date)

## 주요 URL
- **웹사이트**: https://${CF_DOMAIN}
- **REST API**: https://${REST_API_ID}.execute-api.${REGION}.amazonaws.com/prod
- **WebSocket API**: wss://${WS_API_ID}.execute-api.${REGION}.amazonaws.com/prod

## 배포 명령어

### 전체 배포 (새 서비스)
\`\`\`bash
./deploy-new-service.sh [service-name]
\`\`\`

### 개별 컴포넌트 배포
\`\`\`bash
# Lambda 코드만 업데이트
bash scripts/06-deploy-lambda-code.sh ${SERVICE_NAME} ${REGION}

# 프론트엔드만 배포
bash scripts/09-deploy-frontend.sh ${SERVICE_NAME} ${REGION}
\`\`\`

## 로그 확인
\`\`\`bash
# Lambda 함수 로그
aws logs tail /aws/lambda/${LAMBDA_MESSAGE} --follow

# API Gateway 로그
aws logs tail API-Gateway-Execution-Logs_${REST_API_ID}/prod --follow
\`\`\`

## 리소스 삭제 (주의!)
\`\`\`bash
# DynamoDB 테이블 삭제
aws dynamodb delete-table --table-name ${TABLE_CONVERSATIONS}
aws dynamodb delete-table --table-name ${TABLE_PROMPTS}
aws dynamodb delete-table --table-name ${TABLE_USAGE}
aws dynamodb delete-table --table-name ${TABLE_CONNECTIONS}

# Lambda 함수 삭제
aws lambda delete-function --function-name ${LAMBDA_CONNECT}
aws lambda delete-function --function-name ${LAMBDA_DISCONNECT}
aws lambda delete-function --function-name ${LAMBDA_MESSAGE}
aws lambda delete-function --function-name ${LAMBDA_CONVERSATION}
aws lambda delete-function --function-name ${LAMBDA_PROMPT}
aws lambda delete-function --function-name ${LAMBDA_USAGE}

# S3 버킷 삭제
aws s3 rb s3://${S3_BUCKET} --force
\`\`\`

## 문의사항
문제가 발생하면 endpoints.json 파일의 정보를 확인해주세요.
EOF

log_success "DEPLOYMENT_INFO.md 파일 생성 완료"

# 권한 설정
chmod +x "$PROJECT_ROOT/deploy-new-service.sh"
chmod +x "$PROJECT_ROOT/scripts/"*.sh

log_success "환경설정 및 최종 정보 업데이트 완료!"

# 최종 정보 출력
echo ""
log_info "$======================================="
log_info "🎉 모든 설정이 완료되었습니다!"
log_info "======================================="
echo ""
log_success "🌐 웹사이트 URL: https://$CF_DOMAIN"
log_success "📦 REST API: https://${REST_API_ID}.execute-api.${REGION}.amazonaws.com/prod"
log_success "🔌 WebSocket: wss://${WS_API_ID}.execute-api.${REGION}.amazonaws.com/prod"
echo ""
log_info "📄 자세한 정보는 다음 파일을 확인하세요:"
log_info "  - endpoints.json: 엔드포인트 정보"
log_info "  - DEPLOYMENT_INFO.md: 배포 가이드"
echo ""