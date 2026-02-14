#!/usr/bin/env python3
"""
DynamoDB에 실제 테넌트와 사용자 데이터 생성
"""

import boto3
import uuid
import random
from datetime import datetime, timezone
import json

# DynamoDB 초기화
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
tenants_table = dynamodb.Table('sedaily-column-tenants')
user_tenants_table = dynamodb.Table('sedaily-column-user-tenants')

# 새로운 테넌트 정의
NEW_TENANTS = [
    {
        'tenant_id': 'digital-news',
        'tenant_name': '전자신문',
        'domain': 'digital-news.co.kr',
        'status': 'active',
        'plan': 'pro',
        'billing_type': 'fixed',
        'settings': {
            'max_users': 50,
            'features': ['c1', 'c7'],
            'monthly_token_limit': 5000000,
            'monthly_price': 2000000  # 월 200만원
        }
    },
    {
        'tenant_id': 'newsis',
        'tenant_name': '뉴시스',
        'domain': 'newsis.com',
        'status': 'active',
        'plan': 'enterprise',
        'billing_type': 'pay_as_you_go',
        'settings': {
            'max_users': 100,
            'features': ['c1', 'c2', 'c7'],
            'price_per_1k_tokens': 500,  # 1000토큰당 500원
            'spending_limit': 3000000  # 월 300만원 한도
        }
    }
]

# 이름 데이터
LAST_NAMES = ['김', '이', '박', '최', '정', '강', '조', '윤', '장', '임']
FIRST_NAMES = ['민수', '영희', '지훈', '수진', '현우', '미경', '성호', '은주', '준호', '혜진']
POSITIONS = ['기자', '선임기자', '부장', '차장', '팀장', '인턴', '에디터', '데스크']

def create_tenants():
    """테넌트 생성"""
    print("🏢 Creating tenants...")
    created = []

    for tenant_data in NEW_TENANTS:
        try:
            item = {
                'tenantId': tenant_data['tenant_id'],
                'tenant_name': tenant_data['tenant_name'],
                'domain': tenant_data['domain'],
                'status': tenant_data['status'],
                'plan': tenant_data['plan'],
                'billing_type': tenant_data['billing_type'],
                'settings': json.dumps(tenant_data['settings']),
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }

            tenants_table.put_item(Item=item)
            print(f"  ✅ Created: {tenant_data['tenant_name']} ({tenant_data['billing_type']})")
            created.append(tenant_data)

        except Exception as e:
            if "ConditionalCheckFailedException" in str(e) or "already exists" in str(e):
                print(f"  ℹ️ Tenant {tenant_data['tenant_id']} already exists")
            else:
                print(f"  ⚠️ Error: {e}")

    return created

def create_users_for_tenant(tenant_info, user_count=30):
    """테넌트별 사용자 생성"""
    tenant_id = tenant_info['tenant_id']
    tenant_name = tenant_info['tenant_name']
    tenant_plan = tenant_info['plan']

    print(f"\n👥 Creating {user_count} users for {tenant_name}...")

    # 도메인 설정
    domain = tenant_info['domain'].replace('.co.kr', '.com').replace('.com', '') + '.com'
    created_users = []

    for i in range(user_count):
        # 사용자 정보 생성
        last_name = random.choice(LAST_NAMES)
        first_name = random.choice(FIRST_NAMES)
        name = f"{last_name}{first_name}"
        position = random.choice(POSITIONS)

        # 첫 3명은 관리자
        if i < 3:
            role = 'admin'
            plan = tenant_plan
            email = f"admin{i+1}@{domain}"
        else:
            role = 'user'
            # 플랜 분배
            rand = random.random()
            if rand < 0.5:
                plan = tenant_plan
            elif rand < 0.8:
                plan = 'pro' if tenant_plan == 'enterprise' else 'basic'
            else:
                plan = 'basic'

            email = f"user{i-2}@{domain}"

        # UUID 생성 (Cognito sub 대체)
        user_id = str(uuid.uuid4())

        # DynamoDB에 저장
        try:
            item = {
                'userId': user_id,
                'email': email,
                'name': f"{name} ({position})",
                'tenant_id': tenant_id,
                'tenant_name': tenant_name,
                'role': role,
                'plan': plan,
                'status': 'active',
                'position': position,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }

            user_tenants_table.put_item(Item=item)
            created_users.append(item)

            # 진행 상황 표시
            if (i + 1) % 10 == 0:
                print(f"    Created {i + 1}/{user_count} users...")

        except Exception as e:
            print(f"    Error creating user {email}: {e}")

    print(f"  ✅ Created {len(created_users)} users for {tenant_name}")
    return created_users

def display_summary(tenants, all_users):
    """생성 결과 요약"""
    print("\n" + "=" * 60)
    print("📊 생성 완료 요약")
    print("=" * 60)

    for tenant in tenants:
        tenant_users = [u for u in all_users if u['tenant_id'] == tenant['tenant_id']]
        admins = [u for u in tenant_users if u['role'] == 'admin']
        users = [u for u in tenant_users if u['role'] == 'user']

        print(f"\n📌 {tenant['tenant_name']} ({tenant['tenant_id']})")
        print(f"   - 요금제: {tenant['plan']} ({tenant['billing_type']})")
        print(f"   - 사용자: 총 {len(tenant_users)}명 (관리자 {len(admins)}명, 일반 {len(users)}명)")

        if tenant['billing_type'] == 'pay_as_you_go':
            settings = tenant['settings'] if isinstance(tenant['settings'], dict) else json.loads(tenant['settings'])
            print(f"   - 종량제: 1000토큰당 {settings['price_per_1k_tokens']}원")
            print(f"   - 월 한도: {settings['spending_limit']:,}원")
        else:
            settings = tenant['settings'] if isinstance(tenant['settings'], dict) else json.loads(tenant['settings'])
            print(f"   - 정액제: 월 {settings.get('monthly_price', 2000000):,}원")
            print(f"   - 토큰 한도: {settings['monthly_token_limit']:,}개")

def main():
    print("=" * 60)
    print("🚀 실제 테넌트 및 사용자 데이터 생성")
    print("=" * 60)

    # 1. 테넌트 생성
    tenants = create_tenants()

    # 2. 각 테넌트별 사용자 생성
    all_users = []
    for tenant in NEW_TENANTS:
        users = create_users_for_tenant(tenant, 30)
        all_users.extend(users)

    # 3. 요약 표시
    display_summary(NEW_TENANTS, all_users)

    print("\n✨ 모든 데이터가 DynamoDB에 생성되었습니다!")
    print("\n📝 참고:")
    print("  - 전자신문: Pro 플랜 (정액제 - 월 200만원)")
    print("  - 뉴시스: Enterprise 플랜 (종량제 - 사용량 기반)")
    print("  - 각 테넌트: 관리자 3명, 일반 사용자 27명")

if __name__ == "__main__":
    main()