#!/bin/bash

# =========================================
#   Lambda 함수 생성 스크립트 (6개 개별 함수)
#   - WebSocket용 3개 (connect, disconnect, message)
#   - REST API용 3개 (conversation, prompt, usage)
# =========================================

# 스크립트 실행 오류 발생시 중단
set -e

# 색상 코드 설정 (터미널 출력용)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 설정 파일 확인
if [ ! -f "config.sh" ]; then
    echo -e "${RED}❌ config.sh 파일이 없습니다. 먼저 ./init.sh를 실행하세요.${NC}"
    exit 1
fi

# 설정 불러오기
source config.sh

echo "========================================="
echo "   [2/4] Lambda 함수 생성"
echo "   스택: ${STACK_NAME}"
echo "========================================="
echo ""
echo "📌 Lambda란?"
echo "   서버를 관리하지 않고도 코드를 실행할 수 있는 AWS 서비스입니다."
echo "   요청이 올 때만 실행되어 비용이 효율적입니다."
echo ""

# ============================================================
# 변수 설정 섹션
# ============================================================
# DynamoDB 테이블 이름들 (데이터베이스)
CONVERSATIONS_TABLE="${SERVICE_NAME}-conversations-${CARD_COUNT}"  # 대화 내역
FILES_TABLE="${SERVICE_NAME}-files-${CARD_COUNT}"                  # 파일 정보
MESSAGES_TABLE="${SERVICE_NAME}-messages-${CARD_COUNT}"            # 메시지 내역
PROMPTS_TABLE="${SERVICE_NAME}-prompts-${CARD_COUNT}"              # 프롬프트 설정
USAGE_TABLE="${SERVICE_NAME}-usage-${CARD_COUNT}"                  # 사용량 기록
WEBSOCKET_TABLE="${SERVICE_NAME}-websocket-connections-${CARD_COUNT}" # 실시간 연결

# 6개의 개별 Lambda 함수 이름 (모두 CARD_COUNT 포함)
LAMBDA_WS_CONNECT="${SERVICE_NAME}-websocket-connect-${CARD_COUNT}"     # WebSocket 연결
LAMBDA_WS_DISCONNECT="${SERVICE_NAME}-websocket-disconnect-${CARD_COUNT}" # WebSocket 연결 해제
LAMBDA_WS_MESSAGE="${SERVICE_NAME}-websocket-message-${CARD_COUNT}"     # WebSocket 메시지
LAMBDA_API_CONVERSATION="${SERVICE_NAME}-conversation-api-${CARD_COUNT}" # 대화 관리 API
LAMBDA_API_PROMPT="${SERVICE_NAME}-prompt-crud-${CARD_COUNT}"           # 프롬프트 관리 API
LAMBDA_API_USAGE="${SERVICE_NAME}-usage-handler-${CARD_COUNT}"          # 사용량 관리 API

# IAM 역할 이름 (권한 관리)
IAM_ROLE="${SERVICE_NAME}-lambda-role-${CARD_COUNT}"

# ============================================================
# STEP 1: IAM 역할 생성
# ============================================================
# IAM 역할은 Lambda 함수가 다른 AWS 서비스를 사용할 수 있는 권한입니다.
# 예: DynamoDB 읽기/쓰기, S3 파일 접근 등

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 1/4: IAM 역할 생성"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔐 Lambda 함수가 AWS 서비스를 사용할 수 있는 권한을 만듭니다."
echo ""

# 기존 역할이 있는지 확인
if aws iam get-role --role-name "$IAM_ROLE" &>/dev/null; then
    echo "✅ IAM 역할이 이미 존재합니다: $IAM_ROLE"
    ROLE_EXISTS=true
else
    echo "🔨 새로운 IAM 역할을 생성합니다..."

    # Lambda가 이 역할을 사용할 수 있도록 신뢰 정책 생성
    # 이 JSON은 "Lambda 서비스가 이 역할을 사용할 수 있다"는 의미입니다
    cat > /tmp/trust-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

    # 역할 생성
    aws iam create-role \
        --role-name "$IAM_ROLE" \
        --assume-role-policy-document file:///tmp/trust-policy.json &>/dev/null

    echo "✅ IAM 역할 생성 완료: $IAM_ROLE"
    ROLE_EXISTS=false
fi

# ============================================================
# STEP 2: 필요한 권한 연결
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 2/4: 권한 정책 연결"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Lambda 함수가 필요한 서비스들에 접근할 수 있도록 권한을 부여합니다."
echo ""

# 2-1. 기본 Lambda 실행 권한 (CloudWatch 로그 쓰기 등)
echo "  1️⃣ 기본 실행 권한 연결 중..."
aws iam attach-role-policy \
    --role-name "$IAM_ROLE" \
    --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole" &>/dev/null || true

# 2-2. VPC 네트워크 접근 권한 (필요시)
echo "  2️⃣ 네트워크 접근 권한 연결 중..."
aws iam attach-role-policy \
    --role-name "$IAM_ROLE" \
    --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole" &>/dev/null || true

# 2-3. Bedrock AI 서비스 접근 권한
echo "  3️⃣ AI 서비스(Bedrock) 접근 권한 연결 중..."
aws iam attach-role-policy \
    --role-name "$IAM_ROLE" \
    --policy-arn "arn:aws:iam::aws:policy/AmazonBedrockFullAccess" &>/dev/null || true

echo "✅ 기본 권한 정책 연결 완료"
echo ""

# 2-4. 커스텀 정책 생성 (DynamoDB, API Gateway, S3 접근)
echo "📝 커스텀 권한 정책 생성 중..."
echo "  이 권한들은 우리 서비스에 맞춤 제작된 권한입니다."
echo ""

# DynamoDB 접근 권한
echo "  4️⃣ DynamoDB 데이터베이스 접근 권한 생성 중..."
cat > /tmp/dynamodb-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:PutItem",
                "dynamodb:GetItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem",
                "dynamodb:Query",
                "dynamodb:Scan",
                "dynamodb:BatchGetItem",
                "dynamodb:BatchWriteItem"
            ],
            "Resource": [
                "arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/${SERVICE_NAME}-*",
                "arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/${SERVICE_NAME}-*/index/*"
            ]
        }
    ]
}
EOF

aws iam put-role-policy \
    --role-name "$IAM_ROLE" \
    --policy-name "DynamoDBAccess" \
    --policy-document file:///tmp/dynamodb-policy.json &>/dev/null || true

# API Gateway 관리 권한 (WebSocket 연결 관리용)
echo "  5️⃣ API Gateway 접근 권한 생성 중..."
cat > /tmp/apigateway-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "execute-api:ManageConnections",
                "execute-api:Invoke"
            ],
            "Resource": "*"
        }
    ]
}
EOF

aws iam put-role-policy \
    --role-name "$IAM_ROLE" \
    --policy-name "APIGatewayAccess" \
    --policy-document file:///tmp/apigateway-policy.json &>/dev/null || true

# S3 접근 권한 (파일 업로드/다운로드용)
echo "  6️⃣ S3 파일 저장소 접근 권한 생성 중..."
cat > /tmp/s3-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::${SERVICE_NAME}-*",
                "arn:aws:s3:::${SERVICE_NAME}-*/*"
            ]
        }
    ]
}
EOF

aws iam put-role-policy \
    --role-name "$IAM_ROLE" \
    --policy-name "S3Access" \
    --policy-document file:///tmp/s3-policy.json &>/dev/null || true

echo "✅ 모든 권한 설정 완료"

# 권한 적용 대기
echo ""
echo "⏳ 권한이 적용되도록 10초 대기 중..."
sleep 10

# ============================================================
# STEP 3: Lambda Layer 생성 (공통 라이브러리)
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 3/4: Lambda Layer 생성"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 Lambda 함수가 사용할 공통 라이브러리를 준비합니다."
echo "   (Python 패키지들: AWS SDK, HTTP 요청 라이브러리 등)"
echo ""

# Layer 디렉토리 생성
rm -rf /tmp/lambda-layer
mkdir -p /tmp/lambda-layer/python

# requirements.txt 생성 (필요한 라이브러리 목록)
cat > /tmp/lambda-layer/requirements.txt <<EOF
boto3
botocore
requests
python-dateutil
EOF

# 라이브러리 설치
echo "📥 필요한 라이브러리 다운로드 중..."
pip install -r /tmp/lambda-layer/requirements.txt -t /tmp/lambda-layer/python --quiet

# Layer ZIP 파일 생성
echo "📦 라이브러리 압축 중..."
cd /tmp/lambda-layer
zip -r layer.zip python -q
cd - > /dev/null

# Layer 생성 또는 확인
LAYER_NAME="${SERVICE_NAME}-deps-${CARD_COUNT}"
if aws lambda get-layer-version-by-name --layer-name $LAYER_NAME --version-number 1 --region $REGION &>/dev/null; then
    echo "✅ Lambda Layer가 이미 존재합니다: $LAYER_NAME"
    LAYER_VERSION=1
else
    echo "📤 Lambda Layer 업로드 중..."
    LAYER_VERSION=$(aws lambda publish-layer-version \
        --layer-name $LAYER_NAME \
        --description "Dependencies for ${SERVICE_NAME}" \
        --zip-file fileb:///tmp/lambda-layer/layer.zip \
        --compatible-runtimes python3.9 \
        --region $REGION \
        --query 'Version' \
        --output text)
    echo "✅ Lambda Layer 생성 완료: $LAYER_NAME (버전 $LAYER_VERSION)"
fi

LAYER_ARN="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:layer:${LAYER_NAME}:${LAYER_VERSION}"

# ============================================================
# STEP 4: Lambda 함수 생성 (6개 개별 함수)
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 4/4: Lambda 함수 생성 (6개)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 실제 코드가 실행될 Lambda 함수들을 생성합니다."
echo ""

# 초기 Lambda 코드 생성 (나중에 실제 코드로 교체됨)
cat > /tmp/lambda_function.py <<EOF
import json
import boto3
import os
from datetime import datetime

def handler(event, context):
    """
    Lambda 함수의 메인 실행 코드
    event: 요청 정보
    context: Lambda 실행 환경 정보
    """
    print(f"Event: {json.dumps(event)}")

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'message': 'Lambda function is working',
            'service': os.environ.get('SERVICE_NAME', 'unknown'),
            'timestamp': datetime.utcnow().isoformat()
        })
    }
EOF

# Python 코드를 ZIP으로 압축
cd /tmp && zip lambda_function.zip lambda_function.py -q
cd - > /dev/null

# Lambda 함수 생성 헬퍼 함수
create_lambda_function() {
    local FUNCTION_NAME=$1
    local HANDLER=$2
    local DESCRIPTION=$3
    local TIMEOUT=$4
    local MEMORY=$5

    echo "📌 $DESCRIPTION"
    echo "   함수명: $FUNCTION_NAME"
    echo "   핸들러: $HANDLER"
    echo "   메모리: ${MEMORY}MB, 타임아웃: ${TIMEOUT}초"

    if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" &>/dev/null; then
        echo "   ✅ 이미 존재 (스킵)"
    else
        aws lambda create-function \
            --function-name "$FUNCTION_NAME" \
            --runtime python3.9 \
            --role "arn:aws:iam::${ACCOUNT_ID}:role/${IAM_ROLE}" \
            --handler "$HANDLER" \
            --description "$DESCRIPTION" \
            --timeout $TIMEOUT \
            --memory-size $MEMORY \
            --zip-file fileb:///tmp/lambda_function.zip \
            --layers "$LAYER_ARN" \
            --environment "Variables={
                SERVICE_NAME=${SERVICE_NAME},
                CARD_COUNT=${CARD_COUNT},
                PROMPTS_TABLE=${PROMPTS_TABLE},
                CONVERSATIONS_TABLE=${CONVERSATIONS_TABLE},
                FILES_TABLE=${FILES_TABLE},
                MESSAGES_TABLE=${MESSAGES_TABLE},
                USAGE_TABLE=${USAGE_TABLE},
                WEBSOCKET_TABLE=${WEBSOCKET_TABLE},
                ENABLE_NEWS_SEARCH=true
            }" \
            --region "$REGION" &>/dev/null
        echo "   ✅ 생성 완료"
    fi
    echo ""
}

echo "🌐 WebSocket Lambda 함수들 (3개)"
echo "─────────────────────────────────"

# WebSocket 함수들 생성 (높은 메모리, 긴 타임아웃)
create_lambda_function "$LAMBDA_WS_CONNECT" \
    "handlers.websocket.connect.handler" \
    "WebSocket 연결 처리" \
    30 \
    512

create_lambda_function "$LAMBDA_WS_DISCONNECT" \
    "handlers.websocket.disconnect.handler" \
    "WebSocket 연결 해제 처리" \
    30 \
    512

create_lambda_function "$LAMBDA_WS_MESSAGE" \
    "handlers.websocket.message.handler" \
    "WebSocket 메시지 처리 (AI 응답)" \
    120 \
    2048

echo "🔧 REST API Lambda 함수들 (3개)"
echo "─────────────────────────────────"

# REST API 함수들 생성
create_lambda_function "$LAMBDA_API_CONVERSATION" \
    "handlers.api.conversation.handler" \
    "대화 관리 API" \
    30 \
    1024

create_lambda_function "$LAMBDA_API_PROMPT" \
    "handlers.api.prompt.handler" \
    "프롬프트 관리 API" \
    30 \
    512

create_lambda_function "$LAMBDA_API_USAGE" \
    "handlers.api.usage.handler" \
    "사용량 관리 API" \
    30 \
    512

# 임시 파일 정리
echo "🧹 임시 파일 정리 중..."
rm -f /tmp/lambda_function.py /tmp/lambda_function.zip
rm -f /tmp/trust-policy.json /tmp/dynamodb-policy.json
rm -f /tmp/apigateway-policy.json /tmp/s3-policy.json
rm -rf /tmp/lambda-layer

# ============================================================
# 최종 확인
# ============================================================
echo ""
echo "========================================="
echo "   Lambda 함수 생성 결과"
echo "========================================="

# 각 함수 상태 확인
check_lambda() {
    local FUNCTION_NAME=$1
    local DESCRIPTION=$2

    if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" &>/dev/null; then
        CONFIG=$(aws lambda get-function-configuration \
            --function-name "$FUNCTION_NAME" \
            --region "$REGION" \
            --query '[State,Runtime,MemorySize,Timeout]' \
            --output text)
        STATE=$(echo $CONFIG | awk '{print $1}')
        RUNTIME=$(echo $CONFIG | awk '{print $2}')
        MEMORY=$(echo $CONFIG | awk '{print $3}')
        TIMEOUT=$(echo $CONFIG | awk '{print $4}')

        echo "✅ $FUNCTION_NAME"
        echo "   상태: $STATE"
        echo "   런타임: $RUNTIME"
        echo "   메모리: ${MEMORY}MB"
        echo "   타임아웃: ${TIMEOUT}초"
        echo ""
    else
        echo "❌ $FUNCTION_NAME - 생성 실패"
        echo ""
    fi
}

echo "🌐 WebSocket 함수 상태"
echo "─────────────────────────────────"
check_lambda "$LAMBDA_WS_CONNECT" "WebSocket Connect"
check_lambda "$LAMBDA_WS_DISCONNECT" "WebSocket Disconnect"
check_lambda "$LAMBDA_WS_MESSAGE" "WebSocket Message"

echo "🔧 REST API 함수 상태"
echo "─────────────────────────────────"
check_lambda "$LAMBDA_API_CONVERSATION" "Conversation API"
check_lambda "$LAMBDA_API_PROMPT" "Prompt API"
check_lambda "$LAMBDA_API_USAGE" "Usage API"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 생성된 리소스 요약"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔐 IAM 역할: $IAM_ROLE"
echo "📦 Lambda Layer: $LAYER_NAME (버전 $LAYER_VERSION)"
echo ""
echo "🌐 WebSocket Lambda 함수:"
echo "   - $LAMBDA_WS_CONNECT"
echo "   - $LAMBDA_WS_DISCONNECT"
echo "   - $LAMBDA_WS_MESSAGE"
echo ""
echo "🔧 REST API Lambda 함수:"
echo "   - $LAMBDA_API_CONVERSATION"
echo "   - $LAMBDA_API_PROMPT"
echo "   - $LAMBDA_API_USAGE"
echo ""

echo "========================================="
echo "✅ Lambda 함수 생성 완료!"
echo "========================================="
echo ""
echo "💡 다음 단계: ./03-deploy-api-gateway.sh"
echo "   API Gateway를 생성하여 Lambda 함수를 인터넷에 연결합니다."
echo ""