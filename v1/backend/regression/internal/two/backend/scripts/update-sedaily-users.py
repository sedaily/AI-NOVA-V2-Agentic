#!/usr/bin/env python3
"""
기존 서울경제 사용자들의 tenant_id 업데이트
"""

import boto3
from datetime import datetime, timezone

# DynamoDB 초기화
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
user_tenants_table = dynamodb.Table('sedaily-column-user-tenants')

def update_sedaily_users():
    """tenant_id가 없는 @sedaily.com 사용자들을 서울경제 테넌트로 업데이트"""

    print("🔍 tenant_id가 없는 사용자 검색 중...")

    # 전체 스캔
    response = user_tenants_table.scan()
    items = response.get('Items', [])

    # 페이지네이션 처리
    while 'LastEvaluatedKey' in response:
        response = user_tenants_table.scan(
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        items.extend(response.get('Items', []))

    # 업데이트 대상 찾기
    users_to_update = []
    for item in items:
        # tenant_id가 없거나 비어있는 경우
        if not item.get('tenant_id') or item.get('tenant_id') == '':
            email = item.get('email', '')
            # @sedaily.com 이메일인 경우
            if '@sedaily.com' in email:
                users_to_update.append(item)

    print(f"📋 업데이트 대상: {len(users_to_update)}명")

    if not users_to_update:
        print("✅ 업데이트할 사용자가 없습니다.")
        return

    # 사용자 목록 출력
    print("\n업데이트할 사용자:")
    for user in users_to_update[:5]:  # 처음 5명만 표시
        print(f"  - {user.get('email')} ({user.get('name', 'N/A')})")
    if len(users_to_update) > 5:
        print(f"  ... 외 {len(users_to_update) - 5}명")

    # 확인
    confirm = input("\n이 사용자들을 서울경제신문 테넌트로 업데이트하시겠습니까? (yes/no): ")
    if confirm.lower() != 'yes':
        print("취소되었습니다.")
        return

    # 업데이트 실행
    success_count = 0
    fail_count = 0

    print("\n🔄 업데이트 시작...")
    for user in users_to_update:
        try:
            user_id = user['userId']

            # 업데이트
            user_tenants_table.update_item(
                Key={'userId': user_id},
                UpdateExpression='SET tenant_id = :tid, tenant_name = :tname, updated_at = :updated',
                ExpressionAttributeValues={
                    ':tid': 'sedaily',
                    ':tname': '서울경제신문',
                    ':updated': datetime.now(timezone.utc).isoformat()
                }
            )

            success_count += 1
            if success_count % 10 == 0:
                print(f"  진행 중... {success_count}/{len(users_to_update)}")

        except Exception as e:
            print(f"  ❌ 오류: {user.get('email')} - {e}")
            fail_count += 1

    print("\n" + "=" * 50)
    print("✨ 업데이트 완료!")
    print("=" * 50)
    print(f"  성공: {success_count}명")
    print(f"  실패: {fail_count}명")
    print(f"\n📊 서울경제신문 총 사용자: {success_count + 5}명 (기존 5명 + 신규 {success_count}명)")

def check_current_status():
    """현재 상태 확인"""
    print("\n📊 현재 테넌트별 사용자 분포:")

    # 전체 스캔
    response = user_tenants_table.scan()
    items = response.get('Items', [])

    # 페이지네이션 처리
    while 'LastEvaluatedKey' in response:
        response = user_tenants_table.scan(
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        items.extend(response.get('Items', []))

    # 테넌트별 집계
    tenant_counts = {}
    no_tenant = 0

    for item in items:
        tenant_id = item.get('tenant_id', '')
        if tenant_id:
            tenant_name = item.get('tenant_name', tenant_id)
            if tenant_name not in tenant_counts:
                tenant_counts[tenant_name] = 0
            tenant_counts[tenant_name] += 1
        else:
            no_tenant += 1

    # 출력
    for tenant, count in sorted(tenant_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {tenant}: {count}명")

    if no_tenant > 0:
        print(f"  - [테넌트 없음]: {no_tenant}명")

    print(f"\n  총 사용자: {len(items)}명")

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 서울경제신문 사용자 테넌트 업데이트")
    print("=" * 50)

    # 현재 상태 확인
    check_current_status()

    # 업데이트 실행
    update_sedaily_users()

    # 업데이트 후 상태 확인
    print("\n")
    check_current_status()