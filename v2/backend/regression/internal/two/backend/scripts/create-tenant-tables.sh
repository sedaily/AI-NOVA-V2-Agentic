#!/bin/bash

# 멀티테넌트를 위한 DynamoDB 테이블 생성 스크립트

REGION="us-east-1"
PROFILE="default"  # AWS 프로파일 필요시 변경

echo "🚀 Creating multi-tenant DynamoDB tables..."

# 1. Tenants 테이블 생성
echo "📊 Creating sedaily-column-tenants table..."
aws dynamodb create-table \
    --table-name sedaily-column-tenants \
    --attribute-definitions \
        AttributeName=tenantId,AttributeType=S \
    --key-schema \
        AttributeName=tenantId,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region $REGION \
    --profile $PROFILE 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Tenants table created successfully"
else
    echo "⚠️  Tenants table already exists or failed to create"
fi

# 2. User-Tenants 테이블 생성
echo "📊 Creating sedaily-column-user-tenants table..."
aws dynamodb create-table \
    --table-name sedaily-column-user-tenants \
    --attribute-definitions \
        AttributeName=userId,AttributeType=S \
        AttributeName=tenantId,AttributeType=S \
    --key-schema \
        AttributeName=userId,KeyType=HASH \
    --global-secondary-indexes \
        '[{
            "IndexName": "tenantId-index",
            "Keys": [
                {"AttributeName": "tenantId", "KeyType": "HASH"}
            ],
            "Projection": {"ProjectionType": "ALL"},
            "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
        }]' \
    --billing-mode PAY_PER_REQUEST \
    --region $REGION \
    --profile $PROFILE 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ User-Tenants table created successfully"
else
    echo "⚠️  User-Tenants table already exists or failed to create"
fi

# 3. 초기 테넌트 데이터 삽입 (서울경제신문)
echo "📝 Creating initial tenant data for Seoul Economic Daily..."
aws dynamodb put-item \
    --table-name sedaily-column-tenants \
    --item '{
        "tenantId": {"S": "sedaily"},
        "tenantName": {"S": "서울경제신문"},
        "plan": {"S": "enterprise"},
        "status": {"S": "active"},
        "apiCallLimit": {"N": "100000"},
        "apiCallCount": {"N": "0"},
        "storageLimitGb": {"N": "100"},
        "storageUsageGb": {"N": "0"},
        "userLimit": {"N": "500"},
        "userCount": {"N": "30"},
        "features": {"L": [
            {"S": "C7_ENGINE"},
            {"S": "TRANSCRIBE"},
            {"S": "ADVANCED_ANALYTICS"}
        ]},
        "settings": {"M": {
            "allowSignup": {"BOOL": true},
            "requireApproval": {"BOOL": false}
        }},
        "createdAt": {"S": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'"},
        "updatedAt": {"S": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'"}
    }' \
    --region $REGION \
    --profile $PROFILE 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Initial tenant data created"
else
    echo "⚠️  Failed to create initial tenant data"
fi

echo ""
echo "🎉 Multi-tenant tables setup completed!"
echo ""
echo "📋 Created tables:"
echo "  - sedaily-column-tenants (테넌트 정보)"
echo "  - sedaily-column-user-tenants (사용자-테넌트 매핑)"
echo ""
echo "⚡ Next steps:"
echo "  1. Run migration script to map existing users to sedaily tenant"
echo "  2. Update Lambda functions to use tenant context"
echo "  3. Configure Cognito Pre Token Generation trigger"