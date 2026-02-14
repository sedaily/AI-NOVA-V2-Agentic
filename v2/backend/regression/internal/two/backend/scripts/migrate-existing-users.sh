#!/bin/bash

# 기존 Cognito 사용자를 안전하게 sedaily 테넌트로 마이그레이션하는 스크립트
# 원본 데이터는 유지하면서 새로운 멀티테넌트 구조에 복사

REGION="us-east-1"
USER_POOL_ID="us-east-1_ohLOswurY"
PROFILE="default"

echo "🔄 Safe migration: Copying existing users to multi-tenant structure..."
echo "✅ Original Cognito User Pool data will remain untouched"
echo ""

# 백업 플래그 (기존 데이터 백업)
BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 1. 모든 사용자 목록 가져오기
echo "📋 Step 1: Fetching all users from Cognito User Pool..."
users=$(aws cognito-idp list-users \
    --user-pool-id $USER_POOL_ID \
    --region $REGION \
    --profile $PROFILE \
    --query 'Users[].{Username:Username, Email:Attributes[?Name==`email`].Value|[0], Sub:Attributes[?Name==`sub`].Value|[0], Status:UserStatus, Created:UserCreateDate}' \
    --output json)

TOTAL_USERS=$(echo $users | jq length)
echo "✅ Found $TOTAL_USERS users in Cognito"
echo ""

# 2. 마이그레이션 로그 파일 생성
LOG_FILE="migration_log_${BACKUP_TIMESTAMP}.json"
echo "📝 Creating migration log: $LOG_FILE"
echo "[]" > $LOG_FILE

# 3. 각 사용자를 user-tenants 테이블에 추가 (기존 Cognito 데이터는 유지)
echo "📝 Step 2: Migrating users to multi-tenant structure..."
echo "Note: This will NOT modify existing Cognito users"
echo ""

SUCCESS_COUNT=0
SKIP_COUNT=0
ERROR_COUNT=0

echo "$users" | jq -c '.[]' | while read user; do
    username=$(echo $user | jq -r '.Username')
    email=$(echo $user | jq -r '.Email // "no-email@sedaily.com"')
    sub=$(echo $user | jq -r '.Sub')
    status=$(echo $user | jq -r '.Status')
    created=$(echo $user | jq -r '.Created')

    echo "  Processing user: $email (sub: $sub)"

    # 사용자 상태를 멀티테넌트 상태로 변환
    if [ "$status" = "CONFIRMED" ]; then
        user_status="active"
    elif [ "$status" = "FORCE_CHANGE_PASSWORD" ]; then
        user_status="active"
    else
        user_status="suspended"
    fi

    # DynamoDB에 사용자-테넌트 매핑 추가 (조건부 - 이미 존재하면 스킵)
    result=$(aws dynamodb put-item \
        --table-name sedaily-column-user-tenants \
        --item "{
            \"userId\": {\"S\": \"$sub\"},
            \"email\": {\"S\": \"$email\"},
            \"tenantId\": {\"S\": \"sedaily\"},
            \"tenantName\": {\"S\": \"서울경제신문\"},
            \"plan\": {\"S\": \"enterprise\"},
            \"role\": {\"S\": \"user\"},
            \"status\": {\"S\": \"$user_status\"},
            \"createdAt\": {\"S\": \"$created\"},
            \"updatedAt\": {\"S\": \"$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)\"},
            \"metadata\": {\"M\": {
                \"source\": {\"S\": \"cognito_migration\"},
                \"original_username\": {\"S\": \"$username\"},
                \"migration_date\": {\"S\": \"$BACKUP_TIMESTAMP\"}
            }}
        }" \
        --condition-expression "attribute_not_exists(userId)" \
        --return-values ALL_OLD \
        --region $REGION \
        --profile $PROFILE 2>&1)

    if [ $? -eq 0 ]; then
        echo "    ✅ Migrated successfully"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))

        # 로그에 기록
        echo "$user" | jq --arg status "success" '. + {migration_status: $status}' >> $LOG_FILE
    elif echo "$result" | grep -q "ConditionalCheckFailedException"; then
        echo "    ⏭️  Already exists (skipped)"
        SKIP_COUNT=$((SKIP_COUNT + 1))

        # 로그에 기록
        echo "$user" | jq --arg status "skipped" '. + {migration_status: $status}' >> $LOG_FILE
    else
        echo "    ❌ Error occurred"
        ERROR_COUNT=$((ERROR_COUNT + 1))

        # 로그에 기록
        echo "$user" | jq --arg status "error" --arg err "$result" '. + {migration_status: $status, error: $err}' >> $LOG_FILE
    fi
done

echo ""
echo "📊 Step 3: Setting up admin users..."

# 4. 특정 사용자를 admin으로 승격 (선택적)
# 관리자 이메일 목록 - 필요시 수정하세요
ADMIN_EMAILS=("admin@sedaily.com" "editor@sedaily.com")

for admin_email in "${ADMIN_EMAILS[@]}"; do
    echo "👑 Checking for admin user: $admin_email"

    # 이메일로 사용자 찾기
    user_sub=$(aws cognito-idp list-users \
        --user-pool-id $USER_POOL_ID \
        --region $REGION \
        --profile $PROFILE \
        --filter "email = \"$admin_email\"" \
        --query 'Users[0].Attributes[?Name==`sub`].Value|[0]' \
        --output text 2>/dev/null)

    if [ ! -z "$user_sub" ] && [ "$user_sub" != "None" ]; then
        # admin 역할로 업데이트
        aws dynamodb update-item \
            --table-name sedaily-column-user-tenants \
            --key "{\"userId\": {\"S\": \"$user_sub\"}}" \
            --update-expression "SET #role = :role, updatedAt = :updated" \
            --expression-attribute-names '{"#role": "role"}' \
            --expression-attribute-values "{
                \":role\": {\"S\": \"admin\"},
                \":updated\": {\"S\": \"$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)\"}
            }" \
            --region $REGION \
            --profile $PROFILE 2>/dev/null

        if [ $? -eq 0 ]; then
            echo "  ✅ Promoted to admin"
        else
            echo "  ⚠️  User not found in migration or update failed"
        fi
    else
        echo "  ℹ️  User not found in Cognito"
    fi
done

# 5. 검증: 마이그레이션된 사용자 수 확인
echo ""
echo "📊 Step 4: Verifying migration..."

MIGRATED_COUNT=$(aws dynamodb scan \
    --table-name sedaily-column-user-tenants \
    --select COUNT \
    --filter-expression "tenantId = :tid" \
    --expression-attribute-values '{":tid": {"S": "sedaily"}}' \
    --region $REGION \
    --profile $PROFILE \
    --query 'Count' \
    --output text)

echo "✅ Total users in user-tenants table: $MIGRATED_COUNT"

# 6. 최종 보고서
echo ""
echo "========================================="
echo "🎉 Migration Report"
echo "========================================="
echo "📊 Summary:"
echo "  - Total Cognito users: $TOTAL_USERS"
echo "  - Successfully migrated: $SUCCESS_COUNT"
echo "  - Already existed (skipped): $SKIP_COUNT"
echo "  - Errors: $ERROR_COUNT"
echo "  - Users in tenant table: $MIGRATED_COUNT"
echo ""
echo "📁 Migration log saved to: $LOG_FILE"
echo ""
echo "✅ Original Cognito User Pool remains unchanged"
echo "✅ All users mapped to 'sedaily' tenant"
echo "✅ Default role: 'user' (with selected admins)"
echo "✅ Default plan: 'enterprise'"
echo ""
echo "⚡ Next steps:"
echo "  1. Review migration log: cat $LOG_FILE | jq"
echo "  2. Deploy the Lambda Authorizer"
echo "  3. Test authentication with both old and new structure"
echo "  4. Gradually switch to multi-tenant structure"
echo ""
echo "🔄 Rollback option:"
echo "  Simply ignore the new tables and continue using Cognito as before"
echo "  No changes were made to existing Cognito users or configuration"