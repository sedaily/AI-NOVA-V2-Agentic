#!/usr/bin/env python3
"""
멀티테넌트 시연용 샘플 데이터 생성 스크립트
"""

import boto3
import uuid
from datetime import datetime, timezone
import json

# DynamoDB 초기화
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
tenants_table = dynamodb.Table('sedaily-column-tenants')
user_tenants_table = dynamodb.Table('sedaily-column-user-tenants')

# 샘플 신문사 데이터
SAMPLE_TENANTS = [
    {
        'tenant_id': 'sedaily',
        'tenant_name': '서울경제신문',
        'domain': 'sedaily.ai',
        'status': 'active',
        'plan': 'enterprise',
        'settings': {
            'max_users': 100,
            'features': ['c1', 'c2', 'c7'],
            'monthly_token_limit': 10000000
        }
    },
    {
        'tenant_id': 'chosun',
        'tenant_name': '조선일보',
        'domain': 'chosun.ai',
        'status': 'active',
        'plan': 'pro',
        'settings': {
            'max_users': 50,
            'features': ['c1', 'c7'],
            'monthly_token_limit': 5000000
        }
    },
    {
        'tenant_id': 'hankyung',
        'tenant_name': '한국경제신문',
        'domain': 'hankyung.ai',
        'status': 'active',
        'plan': 'pro',
        'settings': {
            'max_users': 50,
            'features': ['c1', 'c7'],
            'monthly_token_limit': 5000000
        }
    },
    {
        'tenant_id': 'joongang',
        'tenant_name': '중앙일보',
        'domain': 'joongang.ai',
        'status': 'active',
        'plan': 'basic',
        'settings': {
            'max_users': 20,
            'features': ['c1'],
            'monthly_token_limit': 1000000
        }
    },
    {
        'tenant_id': 'demo',
        'tenant_name': '데모신문사',
        'domain': 'demo.ai',
        'status': 'trial',
        'plan': 'free',
        'settings': {
            'max_users': 5,
            'features': ['c1'],
            'monthly_token_limit': 100000
        }
    }
]

# 샘플 사용자 데이터 (각 신문사별)
SAMPLE_USERS = {
    'sedaily': [
        {'email': 'admin@sedaily.com', 'role': 'admin', 'plan': 'enterprise', 'name': '김관리'},
        {'email': 'writer1@sedaily.com', 'role': 'user', 'plan': 'pro', 'name': '이기자'},
        {'email': 'writer2@sedaily.com', 'role': 'user', 'plan': 'pro', 'name': '박기자'},
        {'email': 'writer3@sedaily.com', 'role': 'user', 'plan': 'basic', 'name': '최기자'},
        {'email': 'intern@sedaily.com', 'role': 'user', 'plan': 'free', 'name': '정인턴'}
    ],
    'chosun': [
        {'email': 'admin@chosun.com', 'role': 'admin', 'plan': 'pro', 'name': '조관리'},
        {'email': 'senior@chosun.com', 'role': 'user', 'plan': 'pro', 'name': '선임기자'},
        {'email': 'writer@chosun.com', 'role': 'user', 'plan': 'basic', 'name': '일반기자'}
    ],
    'hankyung': [
        {'email': 'admin@hankyung.com', 'role': 'admin', 'plan': 'pro', 'name': '한관리'},
        {'email': 'economy@hankyung.com', 'role': 'user', 'plan': 'pro', 'name': '경제부'},
        {'email': 'stock@hankyung.com', 'role': 'user', 'plan': 'pro', 'name': '증권부'}
    ],
    'joongang': [
        {'email': 'admin@joongang.com', 'role': 'admin', 'plan': 'basic', 'name': '중관리'},
        {'email': 'writer@joongang.com', 'role': 'user', 'plan': 'basic', 'name': '기자'}
    ],
    'demo': [
        {'email': 'demo@demo.ai', 'role': 'admin', 'plan': 'free', 'name': '데모관리자'},
        {'email': 'test@demo.ai', 'role': 'user', 'plan': 'free', 'name': '테스트사용자'}
    ]
}

def create_tenants():
    """테넌트 생성"""
    print("🏢 Creating tenants...")

    for tenant_data in SAMPLE_TENANTS:
        try:
            item = {
                'tenantId': tenant_data['tenant_id'],  # DynamoDB 키
                'tenant_name': tenant_data['tenant_name'],
                'domain': tenant_data['domain'],
                'status': tenant_data['status'],
                'plan': tenant_data['plan'],
                'settings': json.dumps(tenant_data['settings']),
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }

            tenants_table.put_item(Item=item)
            print(f"  ✅ Created tenant: {tenant_data['tenant_name']} ({tenant_data['tenant_id']})")

        except Exception as e:
            print(f"  ⚠️ Error creating tenant {tenant_data['tenant_id']}: {e}")

def create_users():
    """사용자 생성"""
    print("\n👥 Creating users...")

    for tenant_id, users in SAMPLE_USERS.items():
        tenant_name = next(t['tenant_name'] for t in SAMPLE_TENANTS if t['tenant_id'] == tenant_id)

        for user_data in users:
            try:
                # 가상의 user_id (Cognito sub 대체)
                user_id = str(uuid.uuid4())

                item = {
                    'userId': user_id,  # DynamoDB 키
                    'email': user_data['email'],
                    'tenant_id': tenant_id,
                    'tenant_name': tenant_name,
                    'role': user_data['role'],
                    'plan': user_data['plan'],
                    'status': 'active',
                    'name': user_data['name'],
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }

                user_tenants_table.put_item(Item=item)
                print(f"  ✅ Created user: {user_data['name']} ({user_data['email']}) - {tenant_name}")

            except Exception as e:
                print(f"  ⚠️ Error creating user {user_data['email']}: {e}")

def create_sample_usage_data():
    """샘플 사용량 데이터 생성"""
    print("\n📊 Creating sample usage data...")

    usage_table = dynamodb.Table('sedaily-column-usage')
    year_month = datetime.now(timezone.utc).strftime('%Y-%m')

    # 각 사용자의 사용량 데이터 생성
    usage_samples = [
        {'email': 'writer1@sedaily.com', 'tokens': 45000, 'messages': 120},  # 45% 사용
        {'email': 'writer2@sedaily.com', 'tokens': 80000, 'messages': 200},  # 80% 사용
        {'email': 'intern@sedaily.com', 'tokens': 9500, 'messages': 50},    # 95% 사용 (곧 한계)
        {'email': 'senior@chosun.com', 'tokens': 35000, 'messages': 90},     # 35% 사용
        {'email': 'economy@hankyung.com', 'tokens': 60000, 'messages': 150}, # 60% 사용
        {'email': 'demo@demo.ai', 'tokens': 95000, 'messages': 300},         # 95% 사용 (거의 한계)
    ]

    for sample in usage_samples:
        try:
            # 사용자 찾기
            response = user_tenants_table.scan(
                FilterExpression='email = :email',
                ExpressionAttributeValues={':email': sample['email']}
            )

            if response['Items']:
                user = response['Items'][0]
                pk = f"user#{user['email']}"
                sk = f"engine#C1#{year_month}"

                item = {
                    'PK': pk,
                    'SK': sk,
                    'userId': user['email'],
                    'engineType': 'C1',
                    'yearMonth': year_month,
                    'totalTokens': sample['tokens'],
                    'inputTokens': int(sample['tokens'] * 0.4),
                    'outputTokens': int(sample['tokens'] * 0.6),
                    'messageCount': sample['messages'],
                    'createdAt': datetime.now(timezone.utc).isoformat(),
                    'updatedAt': datetime.now(timezone.utc).isoformat()
                }

                usage_table.put_item(Item=item)
                percentage = (sample['tokens'] / get_plan_limit(user['plan'])) * 100
                print(f"  ✅ Created usage for {sample['email']}: {percentage:.1f}% used")

        except Exception as e:
            print(f"  ⚠️ Error creating usage for {sample['email']}: {e}")

def get_plan_limit(plan):
    """플랜별 토큰 한도"""
    limits = {
        'enterprise': 500000,
        'pro': 200000,
        'basic': 100000,
        'free': 10000
    }
    return limits.get(plan, 10000)

def main():
    print("=" * 60)
    print("🚀 멀티테넌트 시연 데이터 생성 시작")
    print("=" * 60)

    # 테넌트 생성
    create_tenants()

    # 사용자 생성
    create_users()

    # 사용량 데이터 생성
    create_sample_usage_data()

    print("\n" + "=" * 60)
    print("✨ 데이터 생성 완료!")
    print("=" * 60)

    print("\n📋 생성된 데이터 요약:")
    print(f"  - 테넌트: {len(SAMPLE_TENANTS)}개")
    print(f"  - 사용자: {sum(len(users) for users in SAMPLE_USERS.values())}명")
    print("\n🎯 시연 시나리오:")
    print("  1. 서울경제 - Enterprise 플랜 (모든 기능)")
    print("  2. 조선/한경 - Pro 플랜 (일부 기능)")
    print("  3. 중앙 - Basic 플랜 (기본 기능)")
    print("  4. 데모 - Free 플랜 (체험판)")
    print("\n⚠️ 주요 테스트 케이스:")
    print("  - intern@sedaily.com: 95% 사용 (곧 한계)")
    print("  - demo@demo.ai: 95% 사용 (Free 플랜 한계)")

if __name__ == "__main__":
    main()