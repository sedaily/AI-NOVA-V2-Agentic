#!/bin/bash
# ============================================================
# BODO Internal Service - Frontend Configuration
# ============================================================
# Internal press release AI service (No login, No sidebar)
# Backend is shared with w1.sedaily.ai, only frontend is separate
#
# Comparison:
#   - external/two (w1.sedaily.ai): Public, with login/sidebar
#   - internal/one (this service): Internal, direct to chat
#
# Last Updated: 2026-01-24
# ============================================================

# AWS Configuration (Frontend deployed to ap-northeast-2)
export AWS_REGION="ap-northeast-2"
export AWS_ACCOUNT_ID="887078546492"

# Service Identification
export SERVICE_NAME="bodo-internal"
export DOMAIN="d2emwatb21j743.cloudfront.net"

# ============================================================
# SHARED BACKEND RESOURCES (Same as w1.sedaily.ai)
# ============================================================
# API Gateway IDs (us-east-1)
export REST_API_ID="16ayefk5lc"
export WS_API_ID="prsebeg7ub"

# Lambda Functions (us-east-1)
export LAMBDA_FUNCTIONS=(
    "w1-websocket-message"
    "w1-websocket-connect"
    "w1-websocket-disconnect"
    "w1-conversation-api"
    "w1-usage-handler"
    "w1-prompt-crud"
)

# DynamoDB Tables (us-east-1)
export DYNAMODB_TABLES=(
    "w1-conversations"
    "w1-messages"
    "w1-prompts"
    "w1-usage"
    "w1-connections"
)

# IAM & Secrets (us-east-1)
export LAMBDA_ROLE="w1-lambda-execution-role"
export SECRET_NAME="bodo-v1"
export PERPLEXITY_SECRET_NAME="nexus/perplexity-api-key"

# ============================================================
# FRONTEND RESOURCES (internal/one only - ap-northeast-2)
# ============================================================
# S3 Bucket
export FRONTEND_BUCKET="bodo-frontend-20251204-230645dc"

# CloudFront Distribution
export CLOUDFRONT_ID="EDF1H6DB796US"

# AI Configuration (Bedrock + Perplexity)
export ANTHROPIC_MODEL="claude-opus-4-5-20251101"
export ANTHROPIC_MAX_TOKENS="4096"
export ANTHROPIC_TEMPERATURE="0.3"
export ENABLE_NATIVE_WEB_SEARCH="true"

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