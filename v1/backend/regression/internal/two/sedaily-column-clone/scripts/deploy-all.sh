#!/bin/bash

# ==============================================
# TEM1 프로젝트 전체 배포 스크립트 (Enhanced Version)
# ==============================================
# 이 스크립트는 모든 인프라를 순차적으로 배포합니다.
# 기존 리소스는 건드리지 않고 필요한 것만 추가/수정합니다.
# ==============================================

set -e  # 오류 발생 시 중단

source "$(dirname "$0")/00-config.sh"

echo "======================================"
echo "TEM1 프로젝트 전체 배포 시작"
echo "======================================"
echo ""

# ==============================================
# 0. 사전 체크
# ==============================================
log_info "AWS CLI 설정 확인..."
aws sts get-caller-identity --region "$REGION" >/dev/null 2>&1
if [ $? -ne 0 ]; then
    log_error "AWS CLI가 제대로 설정되지 않았습니다."
    exit 1
fi
log_success "AWS CLI 설정 확인 완료"

# ==============================================
# 1. DynamoDB 테이블 및 GSI 생성
# ==============================================
log_info "Step 1: DynamoDB 테이블 설정"
./01-create-dynamodb.sh
echo ""

# ==============================================
# 2. Lambda 함수 생성
# ==============================================
log_info "Step 2: Lambda 함수 생성"
./02-create-lambda-functions.sh
echo ""

# ==============================================
# 3. REST API Gateway 설정 (Enhanced)
# ==============================================
log_info "Step 3: REST API Gateway 설정 (Enhanced with CORS)"
if [ -f "./03-setup-rest-api-enhanced.sh" ]; then
    ./03-setup-rest-api-enhanced.sh
else
    log_warning "Enhanced API 스크립트가 없습니다. 기본 스크립트 사용"
    ./03-setup-rest-api.sh
fi
echo ""

# ==============================================
# 4. WebSocket API 설정
# ==============================================
log_info "Step 4: WebSocket API 설정"
./04-setup-websocket-api.sh
echo ""

# ==============================================
# 5. Lambda 권한 설정
# ==============================================
log_info "Step 5: Lambda 권한 설정"
./05-setup-lambda-permissions.sh
echo ""

# ==============================================
# 6. Lambda 코드 배포
# ==============================================
log_info "Step 6: Lambda 코드 배포"
./06-deploy-lambda-code.sh
echo ""

# ==============================================
# 7. S3 버킷 생성 (프론트엔드용)
# ==============================================
log_info "Step 7: S3 버킷 설정"
./07-create-s3-bucket.sh
echo ""

# ==============================================
# 8. CloudFront 설정
# ==============================================
log_info "Step 8: CloudFront 배포"
./08-setup-cloudfront.sh
echo ""

# ==============================================
# 9. 프론트엔드 빌드 및 배포
# ==============================================
log_info "Step 9: 프론트엔드 배포"
./09-deploy-frontend.sh
echo ""

# ==============================================
# 10. 설정 파일 업데이트
# ==============================================
log_info "Step 10: 설정 파일 업데이트"
./10-update-config.sh
echo ""

# ==============================================
# 11. 백엔드 설정 업데이트
# ==============================================
log_info "Step 11: 백엔드 설정 업데이트"
./11-update-backend-config.sh
echo ""

# ==============================================
# 12. 프론트엔드 설정 업데이트
# ==============================================
log_info "Step 12: 프론트엔드 설정 업데이트"
./12-update-frontend-config.sh
echo ""

# ==============================================
# 13. Lambda 환경 변수 최종 업데이트
# ==============================================
log_info "Step 13: Lambda 환경 변수 최종 업데이트"
./13-update-lambda-env.sh
echo ""

# ==============================================
# 추가 검증 및 테스트
# ==============================================
log_info "배포 검증 시작..."

# DynamoDB 테이블 상태 확인
log_info "DynamoDB 테이블 상태:"
for table in $TABLE_CONVERSATIONS $TABLE_PROMPTS $TABLE_FILES $TABLE_MESSAGES $TABLE_USAGE $TABLE_CONNECTIONS; do
    STATUS=$(aws dynamodb describe-table --table-name "$table" --region "$REGION" \
        --query 'Table.TableStatus' --output text 2>/dev/null || echo "NOT_FOUND")
    echo "  - $table: $STATUS"
done
echo ""

# Lambda 함수 상태 확인
log_info "Lambda 함수 상태:"
for func in $LAMBDA_PROMPT $LAMBDA_CONVERSATION $LAMBDA_USAGE $LAMBDA_CONNECT $LAMBDA_DISCONNECT $LAMBDA_MESSAGE; do
    STATUS=$(aws lambda get-function --function-name "$func" --region "$REGION" \
        --query 'Configuration.LastUpdateStatus' --output text 2>/dev/null || echo "NOT_FOUND")
    echo "  - $func: $STATUS"
done
echo ""

# API 엔드포인트 테스트
if [ -n "$REST_API_ID" ]; then
    log_info "API 엔드포인트 테스트..."
    ENDPOINT="https://$REST_API_ID.execute-api.$REGION.amazonaws.com/prod"

    # 프롬프트 조회 테스트
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$ENDPOINT/prompts/11")
    if [ "$RESPONSE" = "200" ]; then
        log_success "API 테스트 성공 (HTTP $RESPONSE)"
    else
        log_warning "API 테스트 실패 (HTTP $RESPONSE)"
    fi
fi
echo ""

# ==============================================
# 배포 완료
# ==============================================
echo "======================================"
log_success "TEM1 프로젝트 배포 완료!"
echo "======================================"
echo ""

# 엔드포인트 정보 출력
if [ -f "$PROJECT_ROOT/endpoints.txt" ]; then
    log_info "배포된 엔드포인트:"
    cat "$PROJECT_ROOT/endpoints.txt"
    echo ""
fi

# CloudFront URL 출력
if [ -f "$PROJECT_ROOT/.cloudfront-url" ]; then
    CLOUDFRONT_URL=$(cat "$PROJECT_ROOT/.cloudfront-url")
    log_info "프론트엔드 URL: $CLOUDFRONT_URL"
    echo ""
fi

echo "다음 단계:"
echo "1. 브라우저에서 프론트엔드 접속하여 테스트"
echo "2. CloudWatch 로그 모니터링"
echo "3. 필요시 CloudFront 캐시 무효화:"
echo "   aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths '/*'"
echo ""

# 트러블슈팅 가이드 참조
log_info "문제 발생 시 TEM1_TROUBLESHOOTING_GUIDE.md 참조"