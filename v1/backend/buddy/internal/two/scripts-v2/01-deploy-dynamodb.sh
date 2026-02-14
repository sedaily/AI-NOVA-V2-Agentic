#!/bin/bash

# DynamoDB 테이블 생성 스크립트

# 설정 파일 확인
if [ ! -f "config.sh" ]; then
    echo "❌ config.sh 파일이 없습니다. 먼저 ./init.sh를 실행하세요."
    exit 1
fi

source config.sh

echo "========================================="
echo "   [1/4] DynamoDB 테이블 생성"
echo "   스택: ${STACK_NAME}"
echo "========================================="

# 테이블 이름 정의
CONVERSATIONS_TABLE="${SERVICE_NAME}-conversations-${CARD_COUNT}"
FILES_TABLE="${SERVICE_NAME}-files-${CARD_COUNT}"
MESSAGES_TABLE="${SERVICE_NAME}-messages-${CARD_COUNT}"
PROMPTS_TABLE="${SERVICE_NAME}-prompts-${CARD_COUNT}"
USAGE_TABLE="${SERVICE_NAME}-usage-${CARD_COUNT}"
WEBSOCKET_TABLE="${SERVICE_NAME}-websocket-connections-${CARD_COUNT}"

# 1. Conversations 테이블 (GSI 포함)
echo "📦 Creating ${CONVERSATIONS_TABLE}..."
if aws dynamodb describe-table --table-name "${CONVERSATIONS_TABLE}" --region ${REGION} &>/dev/null; then
    echo "✅ ${CONVERSATIONS_TABLE} - 이미 존재 (스킵)"
else
    aws dynamodb create-table \
        --table-name ${CONVERSATIONS_TABLE} \
        --attribute-definitions \
            AttributeName=userId,AttributeType=S \
            AttributeName=conversationId,AttributeType=S \
            AttributeName=createdAt,AttributeType=S \
        --key-schema \
            AttributeName=userId,KeyType=HASH \
            AttributeName=conversationId,KeyType=RANGE \
        --global-secondary-indexes \
            "IndexName=ConversationsByDate,KeySchema=[{AttributeName=userId,KeyType=HASH},{AttributeName=createdAt,KeyType=RANGE}],Projection={ProjectionType=ALL}" \
        --billing-mode PAY_PER_REQUEST \
        --region ${REGION} &>/dev/null && echo "✅ ${CONVERSATIONS_TABLE} - 생성 성공" || echo "❌ ${CONVERSATIONS_TABLE} - 생성 실패"
fi

# 2. Files 테이블
echo "📦 Creating ${FILES_TABLE}..."
if aws dynamodb describe-table --table-name "${FILES_TABLE}" --region ${REGION} &>/dev/null; then
    echo "✅ ${FILES_TABLE} - 이미 존재 (스킵)"
else
    aws dynamodb create-table \
        --table-name ${FILES_TABLE} \
        --attribute-definitions \
            AttributeName=promptId,AttributeType=S \
            AttributeName=fileId,AttributeType=S \
        --key-schema \
            AttributeName=promptId,KeyType=HASH \
            AttributeName=fileId,KeyType=RANGE \
        --billing-mode PAY_PER_REQUEST \
        --region ${REGION} &>/dev/null && echo "✅ ${FILES_TABLE} - 생성 성공" || echo "❌ ${FILES_TABLE} - 생성 실패"
fi

# 3. Messages 테이블
echo "📦 Creating ${MESSAGES_TABLE}..."
if aws dynamodb describe-table --table-name "${MESSAGES_TABLE}" --region ${REGION} &>/dev/null; then
    echo "✅ ${MESSAGES_TABLE} - 이미 존재 (스킵)"
else
    aws dynamodb create-table \
        --table-name ${MESSAGES_TABLE} \
        --attribute-definitions \
            AttributeName=conversationId,AttributeType=S \
            AttributeName=timestamp,AttributeType=S \
        --key-schema \
            AttributeName=conversationId,KeyType=HASH \
            AttributeName=timestamp,KeyType=RANGE \
        --billing-mode PAY_PER_REQUEST \
        --region ${REGION} &>/dev/null && echo "✅ ${MESSAGES_TABLE} - 생성 성공" || echo "❌ ${MESSAGES_TABLE} - 생성 실패"
fi

# 4. Prompts 테이블
echo "📦 Creating ${PROMPTS_TABLE}..."
if aws dynamodb describe-table --table-name "${PROMPTS_TABLE}" --region ${REGION} &>/dev/null; then
    echo "✅ ${PROMPTS_TABLE} - 이미 존재 (스킵)"
else
    aws dynamodb create-table \
        --table-name ${PROMPTS_TABLE} \
        --attribute-definitions \
            AttributeName=engineType,AttributeType=S \
            AttributeName=promptId,AttributeType=S \
        --key-schema \
            AttributeName=engineType,KeyType=HASH \
            AttributeName=promptId,KeyType=RANGE \
        --billing-mode PAY_PER_REQUEST \
        --region ${REGION} &>/dev/null && echo "✅ ${PROMPTS_TABLE} - 생성 성공" || echo "❌ ${PROMPTS_TABLE} - 생성 실패"
fi

# 5. Usage 테이블 (GSI 포함)
echo "📦 Creating ${USAGE_TABLE}..."
if aws dynamodb describe-table --table-name "${USAGE_TABLE}" --region ${REGION} &>/dev/null; then
    echo "✅ ${USAGE_TABLE} - 이미 존재 (스킵)"
else
    aws dynamodb create-table \
        --table-name ${USAGE_TABLE} \
        --attribute-definitions \
            AttributeName=userId,AttributeType=S \
            AttributeName=date,AttributeType=S \
            AttributeName=engineType,AttributeType=S \
        --key-schema \
            AttributeName=userId,KeyType=HASH \
            AttributeName=date,KeyType=RANGE \
        --global-secondary-indexes \
            "IndexName=ByEngineType,KeySchema=[{AttributeName=engineType,KeyType=HASH},{AttributeName=date,KeyType=RANGE}],Projection={ProjectionType=ALL}" \
        --billing-mode PAY_PER_REQUEST \
        --region ${REGION} &>/dev/null && echo "✅ ${USAGE_TABLE} - 생성 성공" || echo "❌ ${USAGE_TABLE} - 생성 실패"
fi

# 6. WebSocket Connections 테이블
echo "📦 Creating ${WEBSOCKET_TABLE}..."
if aws dynamodb describe-table --table-name "${WEBSOCKET_TABLE}" --region ${REGION} &>/dev/null; then
    echo "✅ ${WEBSOCKET_TABLE} - 이미 존재 (스킵)"
else
    aws dynamodb create-table \
        --table-name ${WEBSOCKET_TABLE} \
        --attribute-definitions \
            AttributeName=connectionId,AttributeType=S \
        --key-schema \
            AttributeName=connectionId,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region ${REGION} &>/dev/null && echo "✅ ${WEBSOCKET_TABLE} - 생성 성공" || echo "❌ ${WEBSOCKET_TABLE} - 생성 실패"
fi

# TTL 설정 (WebSocket 연결용)
echo ""
echo "⏰ WebSocket 테이블에 TTL 설정..."
aws dynamodb update-time-to-live \
    --table-name "${WEBSOCKET_TABLE}" \
    --time-to-live-specification "AttributeName=ttl,Enabled=true" \
    --region ${REGION} &>/dev/null || echo "TTL 설정 스킵"

# 테이블 안정화 대기
echo ""
echo "⏳ 테이블 안정화 대기 중..."
sleep 5

# 최종 확인
echo ""
echo "========================================="
echo "   DynamoDB 테이블 최종 상태"
echo "========================================="
echo ""

SUCCESS_COUNT=0
FAIL_COUNT=0
FAILED_TABLES=""

for table in "${CONVERSATIONS_TABLE}" "${FILES_TABLE}" "${MESSAGES_TABLE}" "${PROMPTS_TABLE}" "${USAGE_TABLE}" "${WEBSOCKET_TABLE}"; do
    if aws dynamodb describe-table --table-name $table --region ${REGION} &>/dev/null; then
        echo "✅ $table"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo "❌ $table"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        FAILED_TABLES="${FAILED_TABLES} $table"
    fi
done

echo ""
echo "========================================="
if [ $FAIL_COUNT -eq 0 ]; then
    echo "✅ 모든 테이블 생성 완료! (${SUCCESS_COUNT}/6)"
    echo "========================================="
    echo ""
    echo "다음 단계: ./02-deploy-lambda.sh"
else
    echo "⚠️  일부 테이블 생성 실패"
    echo "========================================="
    echo "성공: ${SUCCESS_COUNT}개, 실패: ${FAIL_COUNT}개"
    echo ""
    echo "실패한 테이블:${FAILED_TABLES}"
    echo ""
    echo "해결 방법:"
    echo "1. 잠시 기다린 후 다시 실행: ./01-deploy-dynamodb.sh"
    echo "2. AWS 콘솔에서 직접 확인"
    exit 1
fi