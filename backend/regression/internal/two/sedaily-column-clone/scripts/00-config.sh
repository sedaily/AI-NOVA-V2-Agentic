#!/bin/bash

# ============================================
# 공통 설정 파일
# 모든 스크립트에서 source로 불러와서 사용
# ============================================

# 색상 설정
export RED='\033[0;31m'
export GREEN='\033[0;32m'
export YELLOW='\033[1;33m'
export BLUE='\033[0;34m'
export CYAN='\033[0;36m'
export NC='\033[0m'

# 서비스 설정
export SERVICE_NAME=${1:-sedaily-new-service}
export REGION=${2:-us-east-1}
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# 리소스 이름 생성 함수
get_resource_name() {
    local resource_type=$1
    echo "${SERVICE_NAME}-${resource_type}"
}

# Lambda 함수 이름들
export LAMBDA_CONNECT="$(get_resource_name websocket-connect)"
export LAMBDA_DISCONNECT="$(get_resource_name websocket-disconnect)"
export LAMBDA_MESSAGE="$(get_resource_name websocket-message)"
export LAMBDA_CONVERSATION="$(get_resource_name conversation-api)"
export LAMBDA_PROMPT="$(get_resource_name prompt-crud)"
export LAMBDA_USAGE="$(get_resource_name usage-handler)"

# DynamoDB 테이블 이름들 (성공한 배포 구조 반영)
export TABLE_CONVERSATIONS="$(get_resource_name conversations-v2)"
export TABLE_PROMPTS="$(get_resource_name prompts-v2)"
export TABLE_USAGE="$(get_resource_name usage)"
export TABLE_CONNECTIONS="$(get_resource_name websocket-connections)"
export TABLE_FILES="$(get_resource_name files)"
export TABLE_MESSAGES="$(get_resource_name messages)"

# S3 버킷 이름
export S3_BUCKET="$(get_resource_name frontend)"

# IAM 역할 이름
export IAM_ROLE="$(get_resource_name lambda-execution-role)"

# API Gateway 이름
export REST_API_NAME="$(get_resource_name rest-api)"
export WEBSOCKET_API_NAME="$(get_resource_name websocket-api)"

# 기존 API ID (tem1 서비스용)
export REST_API_ID="8u7vben959"
export WS_API_ID="mq9a6wf3oj"

# 로그 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 리소스 존재 확인 함수
check_resource_exists() {
    local resource_type=$1
    local resource_name=$2

    case $resource_type in
        "dynamodb")
            aws dynamodb describe-table --table-name "$resource_name" --region "$REGION" >/dev/null 2>&1
            ;;
        "lambda")
            aws lambda get-function --function-name "$resource_name" --region "$REGION" >/dev/null 2>&1
            ;;
        "s3")
            aws s3 ls "s3://$resource_name" >/dev/null 2>&1
            ;;
        *)
            return 1
            ;;
    esac

    return $?
}

# 프로젝트 경로
export PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
export BACKEND_DIR="$PROJECT_ROOT/backend"
export FRONTEND_DIR="$PROJECT_ROOT/frontend"

log_info "설정 로드 완료"
log_info "서비스명: $SERVICE_NAME"
log_info "리전: $REGION"
log_info "계정 ID: $ACCOUNT_ID"