#!/bin/bash

# ============================================
# t1.sedaily.ai 메인 배포 스크립트
# ============================================
# 이 스크립트는 t1.sedaily.ai 서비스의 전체/부분 배포를 관리합니다.
# 최종 업데이트: 2025-12-03

set -e

# Configuration
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONFIG_FILE="$PROJECT_ROOT/config/t1-production.env"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$PROJECT_ROOT/logs/deploy_${TIMESTAMP}.log"

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Create logs directory
mkdir -p "$PROJECT_ROOT/logs"

# Logging function
log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

# Error handling
handle_error() {
    log "${RED}❌ 오류 발생: $1${NC}"
    log "${YELLOW}로그 파일: $LOG_FILE${NC}"
    exit 1
}

# Load environment configuration
load_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        handle_error "설정 파일을 찾을 수 없습니다: $CONFIG_FILE"
    fi
    
    # Export all variables from config file
    set -a
    source "$CONFIG_FILE"
    set +a
    
    log "${GREEN}✓ 설정 파일 로드 완료${NC}"
}

# Pre-deployment checks
pre_deployment_checks() {
    log "${MAGENTA}사전 검사 중...${NC}"
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        handle_error "AWS CLI가 설치되지 않았습니다"
    fi
    log "${GREEN}✓ AWS CLI 확인${NC}"
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        handle_error "AWS 자격 증명이 구성되지 않았습니다"
    fi
    
    # Verify AWS account
    CURRENT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
    if [ "$CURRENT_ACCOUNT" != "$AWS_ACCOUNT_ID" ]; then
        handle_error "잘못된 AWS 계정입니다. 예상: $AWS_ACCOUNT_ID, 현재: $CURRENT_ACCOUNT"
    fi
    log "${GREEN}✓ AWS 계정 확인: $AWS_ACCOUNT_ID${NC}"
    
    # Check Node.js for frontend deployment
    if [ "$DEPLOY_FRONTEND" = "true" ]; then
        if ! command -v node &> /dev/null; then
            handle_error "Node.js가 설치되지 않았습니다"
        fi
        log "${GREEN}✓ Node.js 확인${NC}"
    fi
    
    # Check Python for backend deployment
    if [ "$DEPLOY_BACKEND" = "true" ]; then
        if ! command -v python3 &> /dev/null; then
            handle_error "Python3가 설치되지 않았습니다"
        fi
        log "${GREEN}✓ Python3 확인${NC}"
    fi
}

# Deploy frontend
deploy_frontend() {
    log ""
    log "${CYAN}=== 프론트엔드 배포 시작 ===${NC}"
    
    cd "$PROJECT_ROOT/frontend"
    
    # Install dependencies
    log "${BLUE}의존성 설치...${NC}"
    npm install >> "$LOG_FILE" 2>&1 || handle_error "npm install 실패"
    
    # Build
    log "${BLUE}빌드 중...${NC}"
    npm run build >> "$LOG_FILE" 2>&1 || handle_error "빌드 실패"
    
    # Deploy to S3
    log "${BLUE}S3 업로드 중...${NC}"
    aws s3 sync build/ "s3://${S3_BUCKET}" \
        --delete \
        --cache-control "public, max-age=31536000" \
        --exclude "index.html" \
        --exclude "*.json" >> "$LOG_FILE" 2>&1
    
    # Upload index.html with no-cache
    aws s3 cp build/index.html "s3://${S3_BUCKET}/index.html" \
        --cache-control "no-cache, no-store, must-revalidate" >> "$LOG_FILE" 2>&1
    
    # Upload manifest and service worker with appropriate cache
    aws s3 cp build/manifest.json "s3://${S3_BUCKET}/manifest.json" \
        --cache-control "public, max-age=3600" >> "$LOG_FILE" 2>&1 || true
    
    log "${GREEN}✓ S3 업로드 완료${NC}"
    
    # Invalidate CloudFront cache
    if [ "$INVALIDATE_CACHE" = "true" ]; then
        log "${BLUE}CloudFront 캐시 무효화...${NC}"
        INVALIDATION_ID=$(aws cloudfront create-invalidation \
            --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" \
            --paths "/*" \
            --query 'Invalidation.Id' \
            --output text)
        log "${GREEN}✓ 캐시 무효화 시작: $INVALIDATION_ID${NC}"
    fi
    
    cd "$PROJECT_ROOT"
}

# Package Lambda function
package_lambda() {
    log ""
    log "${CYAN}=== Lambda 패키징 시작 ===${NC}"
    
    cd "$PROJECT_ROOT/backend"
    
    # Clean up old packages
    rm -rf package lambda-deployment.zip
    
    # Create package directory
    mkdir -p package
    
    # Install dependencies
    log "${BLUE}의존성 설치...${NC}"
    pip install -r requirements.txt -t package/ >> "$LOG_FILE" 2>&1
    
    # Copy application code
    log "${BLUE}애플리케이션 코드 복사...${NC}"
    cp -r handlers lib *.py package/ 2>/dev/null || true
    
    # Create deployment package
    log "${BLUE}ZIP 파일 생성...${NC}"
    cd package
    zip -r ../lambda-deployment.zip . -q
    cd ..
    
    # Verify package size
    PACKAGE_SIZE=$(ls -lh lambda-deployment.zip | awk '{print $5}')
    log "${GREEN}✓ Lambda 패키지 생성 완료: $PACKAGE_SIZE${NC}"
    
    cd "$PROJECT_ROOT"
}

# Deploy Lambda functions
deploy_lambda() {
    log ""
    log "${CYAN}=== Lambda 함수 배포 시작 ===${NC}"
    
    # Lambda functions to update
    LAMBDA_FUNCTIONS=(
        "$LAMBDA_WS_CONNECT"
        "$LAMBDA_WS_MESSAGE"
        "$LAMBDA_WS_DISCONNECT"
        "$LAMBDA_CONVERSATION"
        "$LAMBDA_PROMPT"
        "$LAMBDA_USAGE"
    )
    
    for func_name in "${LAMBDA_FUNCTIONS[@]}"; do
        log "${BLUE}배포: $func_name${NC}"
        
        # Update function code
        aws lambda update-function-code \
            --function-name "$func_name" \
            --zip-file "fileb://$PROJECT_ROOT/backend/lambda-deployment.zip" \
            --region "$AWS_REGION" >> "$LOG_FILE" 2>&1 || {
                log "${YELLOW}⚠ $func_name 배포 실패 (함수가 없을 수 있음)${NC}"
                continue
            }
        
        # Wait for update to complete
        aws lambda wait function-updated \
            --function-name "$func_name" \
            --region "$AWS_REGION" 2>/dev/null || true
        
        log "${GREEN}✓ $func_name 배포 완료${NC}"
    done
}

# Update Lambda environment variables
update_lambda_env() {
    log ""
    log "${CYAN}=== Lambda 환경변수 업데이트 ===${NC}"
    
    # Common environment variables
    ENV_VARS=$(cat <<EOF
{
    "Variables": {
        "ENV": "$ENV",
        "SERVICE_NAME": "$SERVICE_NAME",
        "WEBSOCKET_API_URL": "$WEBSOCKET_API_URL",
        "USE_ANTHROPIC_API": "$USE_ANTHROPIC_API",
        "ANTHROPIC_SECRET_NAME": "$ANTHROPIC_SECRET_NAME",
        "ANTHROPIC_MODEL_ID": "$ANTHROPIC_MODEL_ID",
        "AI_PROVIDER": "$AI_PROVIDER",
        "FALLBACK_TO_BEDROCK": "$FALLBACK_TO_BEDROCK",
        "ANTHROPIC_MAX_TOKENS": "$ANTHROPIC_MAX_TOKENS",
        "ANTHROPIC_TEMPERATURE": "$ANTHROPIC_TEMPERATURE",
        "USE_RAG": "$USE_RAG",
        "RAG_TOP_K": "$RAG_TOP_K",
        "RAG_MIN_SIMILARITY": "$RAG_MIN_SIMILARITY",
        "LOG_LEVEL": "$LOG_LEVEL"
    }
}
EOF
)
    
    # Update each Lambda function
    LAMBDA_FUNCTIONS=(
        "$LAMBDA_WS_MESSAGE"
        "$LAMBDA_CONVERSATION"
    )
    
    for func_name in "${LAMBDA_FUNCTIONS[@]}"; do
        log "${BLUE}환경변수 업데이트: $func_name${NC}"
        
        aws lambda update-function-configuration \
            --function-name "$func_name" \
            --environment "$ENV_VARS" \
            --region "$AWS_REGION" >> "$LOG_FILE" 2>&1 || {
                log "${YELLOW}⚠ $func_name 환경변수 업데이트 실패${NC}"
                continue
            }
        
        log "${GREEN}✓ $func_name 환경변수 업데이트 완료${NC}"
    done
}

# Deploy backend
deploy_backend() {
    package_lambda
    deploy_lambda
    update_lambda_env
}

# Verify deployment
verify_deployment() {
    log ""
    log "${CYAN}=== 배포 검증 ===${NC}"
    
    # Check Lambda function states
    log "${BLUE}Lambda 함수 상태 확인...${NC}"
    
    LAMBDA_FUNCTIONS=(
        "$LAMBDA_WS_MESSAGE"
        "$LAMBDA_CONVERSATION"
    )
    
    ALL_ACTIVE=true
    for func_name in "${LAMBDA_FUNCTIONS[@]}"; do
        STATE=$(aws lambda get-function \
            --function-name "$func_name" \
            --region "$AWS_REGION" \
            --query 'Configuration.State' \
            --output text 2>/dev/null) || STATE="NOT_FOUND"
        
        if [ "$STATE" = "Active" ]; then
            log "${GREEN}  ✓ $func_name: Active${NC}"
        else
            log "${RED}  ✗ $func_name: $STATE${NC}"
            ALL_ACTIVE=false
        fi
    done
    
    # Check CloudFront distribution
    if [ "$DEPLOY_FRONTEND" = "true" ]; then
        log "${BLUE}CloudFront 배포 상태 확인...${NC}"
        CF_STATUS=$(aws cloudfront get-distribution \
            --id "$CLOUDFRONT_DISTRIBUTION_ID" \
            --query 'Distribution.Status' \
            --output text 2>/dev/null) || CF_STATUS="NOT_FOUND"
        
        if [ "$CF_STATUS" = "Deployed" ]; then
            log "${GREEN}  ✓ CloudFront: Deployed${NC}"
        else
            log "${YELLOW}  ⚠ CloudFront: $CF_STATUS${NC}"
        fi
    fi
    
    if [ "$ALL_ACTIVE" = true ]; then
        log "${GREEN}✅ 배포 검증 완료${NC}"
    else
        log "${YELLOW}⚠ 일부 리소스 상태를 확인해주세요${NC}"
    fi
}

# Show deployment menu
show_menu() {
    clear
    log "${CYAN}============================================${NC}"
    log "${CYAN}     t1.sedaily.ai 배포 스크립트           ${NC}"
    log "${CYAN}============================================${NC}"
    log ""
    log "${YELLOW}배포 옵션을 선택하세요:${NC}"
    log ""
    log "  ${BLUE}1)${NC} 전체 배포 (프론트엔드 + 백엔드)"
    log "  ${BLUE}2)${NC} 프론트엔드만 배포"
    log "  ${BLUE}3)${NC} 백엔드만 배포"
    log "  ${BLUE}4)${NC} Lambda 패키징만"
    log "  ${BLUE}5)${NC} Lambda 환경변수만 업데이트"
    log "  ${BLUE}6)${NC} CloudFront 캐시 무효화만"
    log "  ${BLUE}0)${NC} 종료"
    log ""
}

# Main execution
main() {
    show_menu
    read -p "선택 [0-6]: " choice
    
    case $choice in
        1)
            log "${CYAN}전체 배포를 시작합니다...${NC}"
            load_config
            pre_deployment_checks
            DEPLOY_FRONTEND=true
            DEPLOY_BACKEND=true
            deploy_frontend
            deploy_backend
            verify_deployment
            ;;
        2)
            log "${CYAN}프론트엔드 배포를 시작합니다...${NC}"
            load_config
            pre_deployment_checks
            DEPLOY_FRONTEND=true
            DEPLOY_BACKEND=false
            deploy_frontend
            verify_deployment
            ;;
        3)
            log "${CYAN}백엔드 배포를 시작합니다...${NC}"
            load_config
            pre_deployment_checks
            DEPLOY_FRONTEND=false
            DEPLOY_BACKEND=true
            deploy_backend
            verify_deployment
            ;;
        4)
            log "${CYAN}Lambda 패키징을 시작합니다...${NC}"
            load_config
            package_lambda
            ;;
        5)
            log "${CYAN}Lambda 환경변수 업데이트를 시작합니다...${NC}"
            load_config
            update_lambda_env
            ;;
        6)
            log "${CYAN}CloudFront 캐시 무효화를 시작합니다...${NC}"
            load_config
            log "${BLUE}CloudFront 캐시 무효화...${NC}"
            INVALIDATION_ID=$(aws cloudfront create-invalidation \
                --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" \
                --paths "/*" \
                --query 'Invalidation.Id' \
                --output text)
            log "${GREEN}✓ 캐시 무효화 시작: $INVALIDATION_ID${NC}"
            ;;
        0)
            log "${CYAN}배포 스크립트를 종료합니다.${NC}"
            exit 0
            ;;
        *)
            log "${RED}잘못된 선택입니다.${NC}"
            exit 1
            ;;
    esac
    
    # Summary
    log ""
    log "${CYAN}============================================${NC}"
    log "${CYAN}              배포 완료!                    ${NC}"
    log "${CYAN}============================================${NC}"
    log ""
    log "${BLUE}📊 배포 요약:${NC}"
    log "  • 서비스: ${YELLOW}${CUSTOM_DOMAIN}${NC}"
    log "  • CloudFront: ${YELLOW}${CLOUDFRONT_DOMAIN}${NC}"
    log "  • REST API: ${YELLOW}${REST_API_URL}${NC}"
    log "  • WebSocket: ${YELLOW}${WEBSOCKET_API_URL}${NC}"
    log "  • 로그 파일: ${YELLOW}$LOG_FILE${NC}"
    log ""
    log "${CYAN}다음 단계:${NC}"
    log "1. 웹사이트에서 기능 테스트: ${YELLOW}${CUSTOM_DOMAIN}${NC}"
    log "2. CloudWatch 로그 확인:"
    log "   ${YELLOW}aws logs tail /aws/lambda/${LAMBDA_WS_MESSAGE} --follow${NC}"
    log ""
    log "${BLUE}종료 시간: $(date)${NC}"
}

# Run main function
main "$@"