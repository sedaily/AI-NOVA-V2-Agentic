#!/bin/bash
# W1.SEDAILY.AI Service Configuration
# ====================================
# This file contains all configuration for w1.sedaily.ai service ONLY

# AWS Configuration
export AWS_REGION="us-east-1"
export AWS_ACCOUNT_ID="887078546492"

# Service Identification
export SERVICE_NAME="w1"
export DOMAIN="w1.sedaily.ai"

# API Gateway IDs (DO NOT CHANGE - These are production IDs)
export REST_API_ID="16ayefk5lc"
export WS_API_ID="prsebeg7ub"

# Lambda Functions (w1 prefix only)
export LAMBDA_FUNCTIONS=(
    "w1-websocket-message"
    "w1-websocket-connect"
    "w1-websocket-disconnect"
    "w1-conversation-api"
    "w1-usage-handler"
    "w1-prompt-crud"
)

# DynamoDB Tables
export DYNAMODB_TABLES=(
    "w1-conversations"
    "w1-messages"
    "w1-prompts"
    "w1-usage"
    "w1-connections"
)

# S3 Buckets
export FRONTEND_BUCKET="w1-sedaily-frontend-bucket"

# CloudFront Distribution
export CLOUDFRONT_ID="d9am5o27m55dc"

# IAM Configuration
export LAMBDA_ROLE="w1-lambda-execution-role"

# Secrets Manager
export SECRET_NAME="bodo-v1"

# API Configuration
export ANTHROPIC_MODEL="claude-opus-4-5-20251101"
export ANTHROPIC_MAX_TOKENS="4096"
export ANTHROPIC_TEMPERATURE="0.7"

# Paths
export BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/backend"
export FRONTEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/frontend"
export SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
export RED='\033[0;31m'
export GREEN='\033[0;32m'
export YELLOW='\033[1;33m'
export NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}