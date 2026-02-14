#!/bin/bash

# DynamoDB 테이블 생성 스크립트

# 공통 설정 로드
source "$(dirname "$0")/00-config.sh"

log_info "DynamoDB 테이블 생성 시작..."

# 테이블 생성 함수
create_table() {
    local table_name=$1
    local primary_key=$2
    local sort_key=$3

    if check_resource_exists "dynamodb" "$table_name"; then
        log_warning "$table_name 테이블이 이미 존재합니다"
        return 0
    fi

    log_info "$table_name 테이블 생성 중..."

    if [ -z "$sort_key" ]; then
        # Primary Key만 있는 경우
        aws dynamodb create-table \
            --table-name "$table_name" \
            --attribute-definitions \
                AttributeName="$primary_key",AttributeType=S \
            --key-schema \
                AttributeName="$primary_key",KeyType=HASH \
            --billing-mode PAY_PER_REQUEST \
            --region "$REGION" >/dev/null
    else
        # Sort Key도 있는 경우
        aws dynamodb create-table \
            --table-name "$table_name" \
            --attribute-definitions \
                AttributeName="$primary_key",AttributeType=S \
                AttributeName="$sort_key",AttributeType=S \
            --key-schema \
                AttributeName="$primary_key",KeyType=HASH \
                AttributeName="$sort_key",KeyType=RANGE \
            --billing-mode PAY_PER_REQUEST \
            --region "$REGION" >/dev/null
    fi

    if [ $? -eq 0 ]; then
        log_success "$table_name 테이블 생성 완료"
    else
        log_error "$table_name 테이블 생성 실패"
        return 1
    fi
}

# 테이블 생성 (성공한 배포 구조 반영)
create_table "$TABLE_CONVERSATIONS" "conversationId"
create_table "$TABLE_PROMPTS" "promptId"
create_table "$TABLE_USAGE" "userId" "period"
create_table "$TABLE_CONNECTIONS" "connectionId"

# WebSocket 테이블에 TTL 설정 추가
log_info "WebSocket 테이블에 TTL 설정 중..."
aws dynamodb update-time-to-live \
    --table-name "$TABLE_CONNECTIONS" \
    --time-to-live-specification "AttributeName=ttl,Enabled=true" \
    --region "$REGION" >/dev/null 2>&1
log_success "TTL 설정 완료"
create_table "$TABLE_FILES" "promptId" "fileId"

# Messages 테이블 생성 (복합 키)
log_info "Messages 테이블 생성 중..."
if ! check_resource_exists "dynamodb" "$TABLE_MESSAGES"; then
    create_table "$TABLE_MESSAGES" "conversationId" "timestamp"

    # Messages 테이블에 TTL 설정
    aws dynamodb update-time-to-live \
        --table-name "$TABLE_MESSAGES" \
        --time-to-live-specification "AttributeName=ttl,Enabled=true" \
        --region "$REGION" >/dev/null 2>&1
    log_success "Messages 테이블 생성 및 TTL 설정 완료"
else
    log_info "Messages 테이블이 이미 존재합니다"
fi

# 테이블이 활성화될 때까지 대기
log_info "테이블 활성화 대기 중..."
for table in "$TABLE_CONVERSATIONS" "$TABLE_PROMPTS" "$TABLE_USAGE" "$TABLE_CONNECTIONS" "$TABLE_FILES" "$TABLE_MESSAGES"; do
    if check_resource_exists "dynamodb" "$table"; then
        aws dynamodb wait table-exists --table-name "$table" --region "$REGION"
        log_success "$table 활성화 완료"
    fi
done

# GSI 생성 함수
create_gsi() {
    local table_name=$1
    local index_name=$2
    local hash_key=$3
    local range_key=$4

    # GSI 존재 확인
    GSI_EXISTS=$(aws dynamodb describe-table --table-name "$table_name" --region "$REGION" \
        --query "Table.GlobalSecondaryIndexes[?IndexName=='$index_name'].IndexName" \
        --output text 2>/dev/null || echo "")

    if [ -z "$GSI_EXISTS" ]; then
        log_info "$table_name 테이블에 $index_name GSI 생성 중..."

        if [ -z "$range_key" ]; then
            # Hash Key만 있는 GSI
            aws dynamodb update-table \
                --table-name "$table_name" \
                --attribute-definitions \
                    AttributeName="$hash_key",AttributeType=S \
                --global-secondary-index-updates "[{
                    \"Create\": {
                        \"IndexName\": \"$index_name\",
                        \"KeySchema\": [
                            {\"AttributeName\": \"$hash_key\", \"KeyType\": \"HASH\"}
                        ],
                        \"Projection\": {\"ProjectionType\": \"ALL\"}
                    }
                }]" \
                --region "$REGION" >/dev/null 2>&1 || log_warning "$index_name GSI 생성 중 오류 (이미 존재할 수 있음)"
        else
            # Hash Key와 Range Key가 있는 GSI
            aws dynamodb update-table \
                --table-name "$table_name" \
                --attribute-definitions \
                    AttributeName="$hash_key",AttributeType=S \
                    AttributeName="$range_key",AttributeType=S \
                --global-secondary-index-updates "[{
                    \"Create\": {
                        \"IndexName\": \"$index_name\",
                        \"KeySchema\": [
                            {\"AttributeName\": \"$hash_key\", \"KeyType\": \"HASH\"},
                            {\"AttributeName\": \"$range_key\", \"KeyType\": \"RANGE\"}
                        ],
                        \"Projection\": {\"ProjectionType\": \"ALL\"}
                    }
                }]" \
                --region "$REGION" >/dev/null 2>&1 || log_warning "$index_name GSI 생성 중 오류 (이미 존재할 수 있음)"
        fi

        # GSI 활성화 대기
        local max_wait=60
        local wait_count=0
        while [ $wait_count -lt $max_wait ]; do
            GSI_STATUS=$(aws dynamodb describe-table \
                --table-name "$table_name" \
                --region "$REGION" \
                --query "Table.GlobalSecondaryIndexes[?IndexName=='$index_name'].IndexStatus" \
                --output text 2>/dev/null)

            if [ "$GSI_STATUS" = "ACTIVE" ]; then
                log_success "$index_name GSI 활성화 완료"
                break
            elif [ "$GSI_STATUS" = "CREATING" ]; then
                sleep 5
                wait_count=$((wait_count + 5))
            else
                break
            fi
        done
    else
        log_info "$table_name 테이블에 $index_name GSI가 이미 존재합니다"
    fi
}

# 모든 필요한 GSI 생성
create_gsi "$TABLE_CONVERSATIONS" "userId-createdAt-index" "userId" "createdAt"
create_gsi "$TABLE_PROMPTS" "userId-index" "userId"
create_gsi "$TABLE_FILES" "promptId-uploadedAt-index" "promptId" "uploadedAt"

# 초기 프롬프트 데이터 추가
log_info "초기 프롬프트 데이터 추가 중..."
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

aws dynamodb put-item \
    --table-name "$TABLE_PROMPTS" \
    --item "{
        \"promptId\": {\"S\": \"11\"},
        \"engineType\": {\"S\": \"11\"},
        \"description\": {\"S\": \"C1 엔진 - 기본 칼럼 작성\"},
        \"instructions\": {\"S\": \"칼럼을 작성해주세요.\"},
        \"files\": {\"L\": []},
        \"createdAt\": {\"S\": \"$TIMESTAMP\"},
        \"updatedAt\": {\"S\": \"$TIMESTAMP\"}
    }" \
    --region "$REGION" >/dev/null

aws dynamodb put-item \
    --table-name "$TABLE_PROMPTS" \
    --item "{
        \"promptId\": {\"S\": \"22\"},
        \"engineType\": {\"S\": \"22\"},
        \"description\": {\"S\": \"C2 엔진 - 고급 칼럼 작성\"},
        \"instructions\": {\"S\": \"전문적인 칼럼을 작성해주세요.\"},
        \"files\": {\"L\": []},
        \"createdAt\": {\"S\": \"$TIMESTAMP\"},
        \"updatedAt\": {\"S\": \"$TIMESTAMP\"}
    }" \
    --region "$REGION" >/dev/null

log_success "초기 데이터 추가 완료"
log_success "모든 DynamoDB 테이블 생성 완료!"