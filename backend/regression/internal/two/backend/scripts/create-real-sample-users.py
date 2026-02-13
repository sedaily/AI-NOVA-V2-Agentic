#!/usr/bin/env python3
"""
실제 Cognito와 DynamoDB에 샘플 사용자 생성 스크립트
- 전자신문 (digital-news): 30명
- 뉴시스 (newsis): 30명
"""

import boto3
import uuid
import random
import string
from datetime import datetime, timezone, timedelta
import json
import time

# AWS 클라이언트 초기화
cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Cognito User Pool ID
USER_POOL_ID = 'us-east-1_ohLOswurY'

# DynamoDB 테이블
tenants_table = dynamodb.Table('sedaily-column-tenants')
user_tenants_table = dynamodb.Table('sedaily-column-user-tenants')
usage_table = dynamodb.Table('sedaily-column-usage')

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
            'monthly_token_limit': 5000000
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
            'price_per_1k_tokens': 500,
            'spending_limit': 3000000  # 월 300만원 한도
        }
    }
]

# 이름 데이터
LAST_NAMES = ['김', '이', '박', '최', '정', '강', '조', '윤', '장', '임', '한', '오', '서', '신', '권']
FIRST_NAMES = ['민수', '영희', '지훈', '수진', '현우', '미경', '성호', '은주', '준호', '혜진',
                '동현', '지연', '태양', '수빈', '재현', '나연', '민재', '서연', '준서', '지우']
POSITIONS = ['기자', '선임기자', '부장', '차장', '팀장', '인턴', '에디터', '데스크']

def generate_password():
    """안전한 비밀번호 생성"""
    chars = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(random.choice(chars) for _ in range(12)) + "Aa1!"

def create_tenants():
    """테넌트 생성"""
    print("🏢 Creating new tenants...")

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
            print(f"  ✅ Created tenant: {tenant_data['tenant_name']} ({tenant_data['tenant_id']})")

        except Exception as e:
            print(f"  ⚠️ Error creating tenant {tenant_data['tenant_id']}: {e}")

def create_cognito_user(email, name, tenant_id, role='user', plan='basic'):
    """Cognito에 사용자 생성"""
    try:
        temp_password = generate_password()

        # Cognito 사용자 생성 (custom attributes 제거)
        response = cognito_client.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=email,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'email_verified', 'Value': 'true'},
                {'Name': 'name', 'Value': name}
            ],
            TemporaryPassword=temp_password,
            MessageAction='SUPPRESS'  # 이메일 발송 안함
        )

        # 비밀번호를 영구 비밀번호로 설정
        cognito_client.admin_set_user_password(
            UserPoolId=USER_POOL_ID,
            Username=email,
            Password=temp_password,
            Permanent=True
        )

        return response['User']['Username']  # Cognito sub ID

    except cognito_client.exceptions.UsernameExistsException:
        print(f"    User {email} already exists in Cognito")
        # 기존 사용자 정보 가져오기
        response = cognito_client.admin_get_user(
            UserPoolId=USER_POOL_ID,
            Username=email
        )
        for attr in response['UserAttributes']:
            if attr['Name'] == 'sub':
                return attr['Value']
        return str(uuid.uuid4())
    except Exception as e:
        print(f"    Error creating Cognito user {email}: {e}")
        return str(uuid.uuid4())  # 실패시 임의 ID 반환

def create_dynamodb_user(user_id, email, name, tenant_id, tenant_name, role, plan):
    """DynamoDB에 사용자 정보 저장"""
    try:
        item = {
            'userId': user_id,
            'email': email,
            'name': name,
            'tenant_id': tenant_id,
            'tenant_name': tenant_name,
            'role': role,
            'plan': plan,
            'status': 'active',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }

        user_tenants_table.put_item(Item=item)
        return True
    except Exception as e:
        print(f"    Error saving to DynamoDB: {e}")
        return False

def create_sample_usage(email, tenant_id, plan):
    """샘플 사용량 데이터 생성"""
    try:
        year_month = datetime.now(timezone.utc).strftime('%Y-%m')

        # 플랜별 토큰 한도
        plan_limits = {
            'enterprise': 500000,
            'pro': 200000,
            'basic': 100000,
            'free': 10000
        }

        limit = plan_limits.get(plan, 100000)

        # 랜덤 사용량 (0~95%)
        usage_percent = random.randint(5, 95)
        total_tokens = int(limit * (usage_percent / 100))

        pk = f"user#{email}"
        sk = f"engine#C1#{year_month}"

        item = {
            'PK': pk,
            'SK': sk,
            'userId': email,
            'engineType': 'C1',
            'yearMonth': year_month,
            'totalTokens': total_tokens,
            'inputTokens': int(total_tokens * 0.4),
            'outputTokens': int(total_tokens * 0.6),
            'messageCount': random.randint(10, 200),
            'createdAt': datetime.now(timezone.utc).isoformat(),
            'updatedAt': datetime.now(timezone.utc).isoformat(),
            'lastUsedAt': (datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 72))).isoformat()
        }

        usage_table.put_item(Item=item)
        return usage_percent
    except Exception as e:
        print(f"    Error creating usage data: {e}")
        return 0

def create_users_for_tenant(tenant_id, tenant_name, user_count=30):
    """특정 테넌트의 사용자 생성"""
    print(f"\n👥 Creating {user_count} users for {tenant_name}...")

    # 도메인 추출
    domain = NEW_TENANTS[0]['domain'] if tenant_id == 'digital-news' else NEW_TENANTS[1]['domain']
    domain = domain.split('.')[0] + '.com'  # 간단하게 변환

    # 플랜 결정
    tenant_plan = 'pro' if tenant_id == 'digital-news' else 'enterprise'

    created_count = 0

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
            email_prefix = f"admin{i+1}"
        # 나머지는 일반 사용자
        else:
            role = 'user'
            # 플랜 분배: 60% 기본 플랜, 30% pro, 10% basic
            rand = random.random()
            if rand < 0.6:
                plan = tenant_plan
            elif rand < 0.9:
                plan = 'pro' if tenant_plan == 'enterprise' else 'basic'
            else:
                plan = 'basic'

            email_prefix = f"{position.lower()}{i-2}"
            # 한글 제거하고 영문으로
            email_prefix = f"user{i-2}"

        email = f"{email_prefix}@{domain}"

        print(f"  Creating user {i+1}/{user_count}: {name} ({email})")

        # 1. Cognito에 사용자 생성
        user_id = create_cognito_user(email, name, tenant_id, role, plan)
        time.sleep(0.2)  # Rate limit 방지

        # 2. DynamoDB에 저장
        if create_dynamodb_user(user_id, email, name, tenant_id, tenant_name, role, plan):
            # 3. 샘플 사용량 데이터 생성
            usage_percent = create_sample_usage(email, tenant_id, plan)
            print(f"    ✅ Created: {name} - {position} - {plan} plan - {usage_percent}% usage")
            created_count += 1
        else:
            print(f"    ❌ Failed to create user")

    print(f"  Total created: {created_count}/{user_count}")
    return created_count

def main():
    print("=" * 60)
    print("🚀 실제 샘플 사용자 생성 시작")
    print("=" * 60)

    # 1. 테넌트 생성
    create_tenants()

    # 2. 전자신문 사용자 30명 생성
    digital_count = create_users_for_tenant('digital-news', '전자신문', 30)

    # 3. 뉴시스 사용자 30명 생성
    newsis_count = create_users_for_tenant('newsis', '뉴시스', 30)

    print("\n" + "=" * 60)
    print("✨ 생성 완료!")
    print("=" * 60)
    print(f"\n📋 생성 요약:")
    print(f"  - 테넌트: 2개 (전자신문, 뉴시스)")
    print(f"  - 전자신문 사용자: {digital_count}명")
    print(f"  - 뉴시스 사용자: {newsis_count}명")
    print(f"  - 총 사용자: {digital_count + newsis_count}명")
    print("\n📌 참고:")
    print("  - 전자신문: Pro 플랜 (정액제)")
    print("  - 뉴시스: Enterprise 플랜 (종량제 Pay-as-you-go)")
    print("  - 각 테넌트별 관리자 3명, 일반 사용자 27명")
    print("\n🔑 로그인 정보:")
    print("  - 모든 사용자 비밀번호는 자동 생성됨")
    print("  - Cognito 콘솔에서 비밀번호 재설정 가능")

if __name__ == "__main__":
    main()