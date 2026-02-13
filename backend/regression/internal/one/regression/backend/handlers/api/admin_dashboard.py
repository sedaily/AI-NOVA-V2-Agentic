"""
관리 대시보드 API Handler
멀티테넌트 관리 기능
"""

import json
import boto3
from datetime import datetime, timezone
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr

from utils.logger import setup_logger
from utils.response import APIResponse

# 로깅 설정
logger = setup_logger(__name__)

# DynamoDB 초기화
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
tenants_table = dynamodb.Table('sedaily-column-tenants')
user_tenants_table = dynamodb.Table('sedaily-column-user-tenants')
usage_table = dynamodb.Table('sedaily-column-usage')

def decimal_to_float(obj):
    """DynamoDB Decimal을 float로 변환"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(v) for v in obj]
    return obj

def handler(event, context):
    """Lambda 핸들러 - 관리 대시보드 API"""

    logger.info(f"Admin Dashboard Event: {json.dumps(event)}")

    # HTTP 메서드 추출
    http_method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method')
    path = event.get('path', '')
    path_params = event.get('pathParameters', {}) or {}
    query_params = event.get('queryStringParameters', {}) or {}

    # CORS preflight
    if http_method == 'OPTIONS':
        return APIResponse.cors_preflight()

    try:
        # 라우팅
        if '/admin/tenants' in path:
            if http_method == 'GET':
                return get_tenants()
            elif http_method == 'PUT' and path_params.get('tenantId'):
                body = json.loads(event.get('body', '{}'))
                return update_tenant(path_params['tenantId'], body)

        elif '/admin/users' in path:
            if http_method == 'GET':
                tenant_id = query_params.get('tenantId')
                return get_users(tenant_id)
            elif http_method == 'PUT' and path_params.get('userId'):
                body = json.loads(event.get('body', '{}'))
                return update_user(path_params['userId'], body)

        elif '/admin/usage' in path:
            if http_method == 'GET':
                tenant_id = query_params.get('tenantId')
                return get_usage_stats(tenant_id)

        elif '/admin/dashboard' in path:
            if http_method == 'GET':
                return get_dashboard_data()

        return APIResponse.error('Not found', 404)

    except Exception as e:
        logger.error(f"Error in admin dashboard: {e}", exc_info=True)
        return APIResponse.error(str(e), 500)

def get_tenants():
    """모든 테넌트 조회"""
    try:
        response = tenants_table.scan()
        tenants = response.get('Items', [])

        # settings JSON 파싱
        for tenant in tenants:
            if 'settings' in tenant and isinstance(tenant['settings'], str):
                tenant['settings'] = json.loads(tenant['settings'])

        return APIResponse.success({
            'tenants': decimal_to_float(tenants),
            'count': len(tenants)
        })
    except Exception as e:
        logger.error(f"Error getting tenants: {e}")
        return APIResponse.error(str(e), 500)

def get_users(tenant_id=None):
    """사용자 조회 (테넌트별 필터링 가능)"""
    try:
        if tenant_id:
            # 특정 테넌트의 사용자만
            response = user_tenants_table.scan(
                FilterExpression=Attr('tenant_id').eq(tenant_id)
            )
        else:
            # 모든 사용자
            response = user_tenants_table.scan()

        users = response.get('Items', [])

        # 각 사용자의 사용량 정보 추가
        year_month = datetime.now(timezone.utc).strftime('%Y-%m')

        for user in users:
            # 사용량 조회 시도
            try:
                pk = f"user#{user['email']}"
                sk = f"engine#C1#{year_month}"

                usage_response = usage_table.get_item(
                    Key={'PK': pk, 'SK': sk}
                )

                if 'Item' in usage_response:
                    usage_item = usage_response['Item']
                    # 플랜별 한도
                    plan_limits = {
                        'enterprise': 500000,
                        'pro': 200000,
                        'basic': 100000,
                        'free': 10000
                    }
                    limit = plan_limits.get(user.get('plan', 'basic'), 100000)
                    tokens_used = float(usage_item.get('totalTokens', 0))
                    user['usage_percentage'] = min(100, (tokens_used / limit) * 100)
                    user['tokens_used'] = tokens_used
                    user['tokens_limit'] = limit
                else:
                    user['usage_percentage'] = 0
                    user['tokens_used'] = 0
                    user['tokens_limit'] = plan_limits.get(user.get('plan', 'basic'), 100000)

            except Exception as e:
                logger.warning(f"Could not get usage for {user.get('email')}: {e}")
                user['usage_percentage'] = 0
                user['tokens_used'] = 0

        return APIResponse.success({
            'users': decimal_to_float(users),
            'count': len(users)
        })
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return APIResponse.error(str(e), 500)

def update_tenant(tenant_id, data):
    """테넌트 정보 업데이트"""
    try:
        update_expr = []
        expr_attr_values = {}

        if 'status' in data:
            update_expr.append('status = :status')
            expr_attr_values[':status'] = data['status']

        if 'plan' in data:
            update_expr.append('plan = :plan')
            expr_attr_values[':plan'] = data['plan']

        if 'billing_type' in data:
            update_expr.append('billing_type = :billing_type')
            expr_attr_values[':billing_type'] = data['billing_type']

        if 'settings' in data:
            update_expr.append('settings = :settings')
            expr_attr_values[':settings'] = json.dumps(data['settings'])

        if update_expr:
            update_expr.append('updated_at = :updated')
            expr_attr_values[':updated'] = datetime.now(timezone.utc).isoformat()

            tenants_table.update_item(
                Key={'tenantId': tenant_id},
                UpdateExpression='SET ' + ', '.join(update_expr),
                ExpressionAttributeValues=expr_attr_values
            )

        return APIResponse.success({'message': 'Tenant updated successfully'})

    except Exception as e:
        logger.error(f"Error updating tenant: {e}")
        return APIResponse.error(str(e), 500)

def update_user(user_id, data):
    """사용자 정보 업데이트 (차단, 플랜 변경 등)"""
    try:
        update_expr = []
        expr_attr_values = {}

        if 'status' in data:
            update_expr.append('status = :status')
            expr_attr_values[':status'] = data['status']

        if 'plan' in data:
            update_expr.append('plan = :plan')
            expr_attr_values[':plan'] = data['plan']

        if 'role' in data:
            update_expr.append('#role = :role')
            expr_attr_names = {'#role': 'role'}  # role은 예약어
            expr_attr_values[':role'] = data['role']
        else:
            expr_attr_names = None

        if update_expr:
            update_expr.append('updated_at = :updated')
            expr_attr_values[':updated'] = datetime.now(timezone.utc).isoformat()

            kwargs = {
                'Key': {'userId': user_id},
                'UpdateExpression': 'SET ' + ', '.join(update_expr),
                'ExpressionAttributeValues': expr_attr_values
            }

            if expr_attr_names:
                kwargs['ExpressionAttributeNames'] = expr_attr_names

            user_tenants_table.update_item(**kwargs)

        return APIResponse.success({'message': 'User updated successfully'})

    except Exception as e:
        logger.error(f"Error updating user: {e}")
        return APIResponse.error(str(e), 500)

def get_usage_stats(tenant_id=None):
    """사용량 통계 조회"""
    try:
        # 현재 월 기준
        year_month = datetime.now(timezone.utc).strftime('%Y-%m')

        # 모든 사용자의 사용량 조회
        if tenant_id:
            # 특정 테넌트 사용자만
            users_response = user_tenants_table.scan(
                FilterExpression=Attr('tenant_id').eq(tenant_id)
            )
        else:
            users_response = user_tenants_table.scan()

        users = users_response.get('Items', [])

        # 통계 집계
        stats = {
            'total_users': len(users),
            'total_tokens': 0,
            'high_usage_users': [],
            'by_plan': {},
            'by_tenant': {}
        }

        for user in users:
            email = user.get('email')
            plan = user.get('plan', 'basic')
            tenant = user.get('tenant_id')

            # 사용량 조회
            try:
                pk = f"user#{email}"
                sk = f"engine#C1#{year_month}"

                usage_response = usage_table.get_item(
                    Key={'PK': pk, 'SK': sk}
                )

                if 'Item' in usage_response:
                    tokens = float(usage_response['Item'].get('totalTokens', 0))
                    stats['total_tokens'] += tokens

                    # 플랜별 집계
                    if plan not in stats['by_plan']:
                        stats['by_plan'][plan] = {'users': 0, 'tokens': 0}
                    stats['by_plan'][plan]['users'] += 1
                    stats['by_plan'][plan]['tokens'] += tokens

                    # 테넌트별 집계
                    if tenant not in stats['by_tenant']:
                        stats['by_tenant'][tenant] = {'users': 0, 'tokens': 0}
                    stats['by_tenant'][tenant]['users'] += 1
                    stats['by_tenant'][tenant]['tokens'] += tokens

                    # 높은 사용량 사용자 (80% 이상)
                    plan_limits = {
                        'enterprise': 500000,
                        'pro': 200000,
                        'basic': 100000,
                        'free': 10000
                    }
                    limit = plan_limits.get(plan, 100000)
                    usage_pct = (tokens / limit) * 100

                    if usage_pct >= 80:
                        stats['high_usage_users'].append({
                            'email': email,
                            'name': user.get('name'),
                            'tenant': user.get('tenant_name'),
                            'usage_percentage': usage_pct,
                            'tokens_used': tokens
                        })

            except Exception as e:
                logger.warning(f"Could not get usage for {email}: {e}")

        # 높은 사용량 사용자 정렬
        stats['high_usage_users'].sort(key=lambda x: x['usage_percentage'], reverse=True)

        return APIResponse.success(decimal_to_float(stats))

    except Exception as e:
        logger.error(f"Error getting usage stats: {e}")
        return APIResponse.error(str(e), 500)

def get_dashboard_data():
    """대시보드 전체 데이터 조회"""
    try:
        # 모든 데이터를 한 번에 가져오기
        tenants_response = get_tenants()
        users_response = get_users()
        usage_response = get_usage_stats()

        # 응답 데이터 추출
        tenants = json.loads(tenants_response['body'])['tenants'] if tenants_response['statusCode'] == 200 else []
        users = json.loads(users_response['body'])['users'] if users_response['statusCode'] == 200 else []
        usage = json.loads(usage_response['body']) if usage_response['statusCode'] == 200 else {}

        # 통합 데이터
        dashboard_data = {
            'tenants': tenants,
            'users': users,
            'usage_stats': usage,
            'summary': {
                'total_tenants': len(tenants),
                'total_users': len(users),
                'active_users': len([u for u in users if u.get('status') == 'active']),
                'blocked_users': len([u for u in users if u.get('status') == 'blocked']),
                'warning_users': len([u for u in users if u.get('usage_percentage', 0) >= 80]),
                'total_tokens_used': usage.get('total_tokens', 0)
            }
        }

        return APIResponse.success(dashboard_data)

    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return APIResponse.error(str(e), 500)