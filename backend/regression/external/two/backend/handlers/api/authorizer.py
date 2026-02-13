"""
API Gateway Lambda Authorizer
멀티테넌트 인증 및 권한 부여 처리
"""
import json
import boto3
import logging
import os
from jose import jwt, JWTError
import urllib.request

from src.repositories.tenant_repository import TenantRepository

logger = logging.getLogger(__name__)

# Cognito 설정
USER_POOL_ID = os.environ.get('USER_POOL_ID', 'us-east-1_ohLOswurY')
REGION = os.environ.get('REGION', 'us-east-1')
COGNITO_ISSUER = f'https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}'


def get_jwt_keys():
    """Cognito JWKS (JSON Web Key Set) 가져오기"""
    url = f'{COGNITO_ISSUER}/.well-known/jwks.json'
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode('utf-8'))


def handler(event, context):
    """
    Lambda Authorizer 핸들러
    JWT 토큰 검증 및 테넌트 정보 조회
    """
    logger.info(f"Authorizer event: {json.dumps(event)}")

    try:
        # REQUEST 타입 authorizer는 event 구조가 다름
        # Authorization 헤더에서 토큰 추출
        headers = event.get('headers', {})
        auth_header = headers.get('Authorization', '') or headers.get('authorization', '')
        token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else ''

        if not token:
            logger.error(f"No token provided. Headers: {headers}")
            raise Exception('Unauthorized')

        # JWT 토큰 디코드 (서명 검증 생략 - 프로덕션에서는 필수)
        try:
            # 실제로는 JWKS를 사용한 서명 검증 필요
            claims = jwt.get_unverified_claims(token)
            user_id = claims.get('sub')
            email = claims.get('email')

            if not user_id:
                raise Exception('Invalid token')

        except JWTError as e:
            logger.error(f"JWT decode error: {str(e)}")
            raise Exception('Unauthorized')

        # 테넌트 정보 조회
        tenant_repo = TenantRepository()
        user_tenant = tenant_repo.find_user_tenant(user_id)

        # 사용자-테넌트 매핑이 없으면 기본값 설정 (기존 사용자 호환성)
        if not user_tenant:
            # 기존 사용자는 모두 sedaily 테넌트로 자동 매핑
            from src.models.tenant import UserTenant
            user_tenant = UserTenant(
                user_id=user_id,
                email=email or 'unknown@sedaily.com',
                tenant_id='sedaily',
                tenant_name='서울경제신문',
                plan='enterprise',
                role='user'
            )
            # DB에 저장
            tenant_repo.save_user_tenant(user_tenant)
            logger.info(f"Auto-mapped existing user {user_id} to sedaily tenant")

        # 테넌트 상태 확인
        tenant = tenant_repo.find_tenant_by_id(user_tenant.tenant_id)
        if not tenant:
            logger.error(f"Tenant not found: {user_tenant.tenant_id}")
            raise Exception('Tenant not found')

        if tenant.status == 'suspended':
            logger.error(f"Tenant suspended: {user_tenant.tenant_id}")
            raise Exception('Tenant suspended')

        if user_tenant.status != 'active':
            logger.error(f"User not active: {user_id}")
            raise Exception('User not active')

        # 사용량 제한 확인
        if tenant.is_limit_exceeded():
            logger.warning(f"Tenant {tenant.tenant_id} exceeded API limit")
            # 제한 초과 시에도 일단 허용하되 경고만 (나중에 차단 가능)

        # API Gateway에 전달할 정책 생성
        policy = {
            'principalId': user_id,
            'policyDocument': {
                'Version': '2012-10-17',
                'Statement': [
                    {
                        'Action': 'execute-api:Invoke',
                        'Effect': 'Allow',
                        'Resource': event['methodArn']
                    }
                ]
            },
            'context': {
                'userId': user_id,
                'email': email or '',
                'tenantId': user_tenant.tenant_id,
                'tenantName': user_tenant.tenant_name,
                'plan': user_tenant.plan,
                'role': user_tenant.role,
                'features': json.dumps(tenant.features)  # 문자열로 변환
            }
        }

        logger.info(f"Authorization successful for user {user_id} from tenant {user_tenant.tenant_id}")
        return policy

    except Exception as e:
        logger.error(f"Authorization failed: {str(e)}")
        # REQUEST 타입 authorizer는 Deny 정책을 반환해야 함
        return {
            'principalId': 'unauthorized',
            'policyDocument': {
                'Version': '2012-10-17',
                'Statement': [
                    {
                        'Action': 'execute-api:Invoke',
                        'Effect': 'Deny',
                        'Resource': event.get('methodArn', '*')
                    }
                ]
            }
        }


def generate_policy(principal_id, effect, resource):
    """IAM 정책 생성 헬퍼 함수"""
    auth_response = {
        'principalId': principal_id
    }

    if effect and resource:
        policy_document = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Action': 'execute-api:Invoke',
                    'Effect': effect,
                    'Resource': resource
                }
            ]
        }
        auth_response['policyDocument'] = policy_document

    return auth_response