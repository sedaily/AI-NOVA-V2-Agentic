"""
테넌트(Tenant) 리포지토리
테넌트 및 사용자-테넌트 매핑 데이터 관리
"""
import boto3
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import os

from ..models.tenant import Tenant, UserTenant

logger = logging.getLogger(__name__)


class TenantRepository:
    """테넌트 데이터 접근 계층"""

    def __init__(self, tenants_table: str = None, user_tenants_table: str = None, region: str = None):
        self.tenants_table_name = tenants_table or os.environ.get('TENANTS_TABLE', 'sedaily-column-tenants')
        self.user_tenants_table_name = user_tenants_table or os.environ.get('USER_TENANTS_TABLE', 'sedaily-column-user-tenants')
        region = region or os.environ.get('AWS_REGION', 'us-east-1')

        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.tenants_table = self.dynamodb.Table(self.tenants_table_name)
        self.user_tenants_table = self.dynamodb.Table(self.user_tenants_table_name)

        logger.info(f"TenantRepository initialized with tables: {self.tenants_table_name}, {self.user_tenants_table_name}")

    # ========== Tenant 관련 메서드 ==========

    def save_tenant(self, tenant: Tenant) -> Tenant:
        """테넌트 저장"""
        try:
            now = datetime.now().isoformat()
            if not tenant.created_at:
                tenant.created_at = now
            tenant.updated_at = now

            self.tenants_table.put_item(Item=tenant.to_dict())
            logger.info(f"Tenant saved: {tenant.tenant_id}")
            return tenant

        except Exception as e:
            logger.error(f"Error saving tenant: {str(e)}")
            raise

    def find_tenant_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """테넌트 ID로 조회"""
        try:
            response = self.tenants_table.get_item(
                Key={'tenantId': tenant_id}
            )

            if 'Item' in response:
                return Tenant.from_dict(response['Item'])

            return None

        except Exception as e:
            logger.error(f"Error finding tenant by id: {str(e)}")
            raise

    def update_tenant_usage(self, tenant_id: str, api_calls: int = 0, storage_gb: float = 0) -> bool:
        """테넌트 사용량 업데이트"""
        try:
            update_expr = []
            expr_values = {}

            if api_calls > 0:
                update_expr.append('apiCallCount = apiCallCount + :calls')
                expr_values[':calls'] = api_calls

            if storage_gb != 0:
                update_expr.append('storageUsageGb = storageUsageGb + :storage')
                expr_values[':storage'] = storage_gb

            if update_expr:
                update_expr.append('updatedAt = :updated')
                expr_values[':updated'] = datetime.now().isoformat()

                self.tenants_table.update_item(
                    Key={'tenantId': tenant_id},
                    UpdateExpression='SET ' + ', '.join(update_expr),
                    ExpressionAttributeValues=expr_values
                )

                logger.info(f"Tenant usage updated: {tenant_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error updating tenant usage: {str(e)}")
            raise

    def reset_monthly_usage(self, tenant_id: str) -> bool:
        """월간 사용량 초기화 (과금 주기 시작 시)"""
        try:
            self.tenants_table.update_item(
                Key={'tenantId': tenant_id},
                UpdateExpression='SET apiCallCount = :zero, billingCycleStart = :now, updatedAt = :updated',
                ExpressionAttributeValues={
                    ':zero': 0,
                    ':now': datetime.now().isoformat(),
                    ':updated': datetime.now().isoformat()
                }
            )

            logger.info(f"Monthly usage reset for tenant: {tenant_id}")
            return True

        except Exception as e:
            logger.error(f"Error resetting monthly usage: {str(e)}")
            raise

    # ========== UserTenant 관련 메서드 ==========

    def save_user_tenant(self, user_tenant: UserTenant) -> UserTenant:
        """사용자-테넌트 매핑 저장"""
        try:
            now = datetime.now().isoformat()
            if not user_tenant.created_at:
                user_tenant.created_at = now
            user_tenant.updated_at = now

            self.user_tenants_table.put_item(Item=user_tenant.to_dict())

            # 테넌트의 사용자 수 증가
            self._increment_user_count(user_tenant.tenant_id, 1)

            logger.info(f"UserTenant saved: {user_tenant.user_id} -> {user_tenant.tenant_id}")
            return user_tenant

        except Exception as e:
            logger.error(f"Error saving user tenant: {str(e)}")
            raise

    def find_user_tenant(self, user_id: str) -> Optional[UserTenant]:
        """사용자 ID로 테넌트 정보 조회"""
        try:
            response = self.user_tenants_table.get_item(
                Key={'userId': user_id}
            )

            if 'Item' in response:
                return UserTenant.from_dict(response['Item'])

            return None

        except Exception as e:
            logger.error(f"Error finding user tenant: {str(e)}")
            raise

    def find_users_by_tenant(self, tenant_id: str) -> List[UserTenant]:
        """테넌트에 속한 모든 사용자 조회"""
        try:
            response = self.user_tenants_table.query(
                IndexName='tenantId-index',  # GSI 필요
                KeyConditionExpression='tenantId = :tid',
                ExpressionAttributeValues={
                    ':tid': tenant_id
                }
            )

            users = []
            for item in response.get('Items', []):
                users.append(UserTenant.from_dict(item))

            return users

        except Exception as e:
            logger.error(f"Error finding users by tenant: {str(e)}")
            raise

    def update_user_role(self, user_id: str, new_role: str) -> bool:
        """사용자 역할 변경"""
        try:
            if new_role not in ['admin', 'user']:
                raise ValueError(f"Invalid role: {new_role}")

            self.user_tenants_table.update_item(
                Key={'userId': user_id},
                UpdateExpression='SET #role = :role, updatedAt = :updated',
                ExpressionAttributeNames={
                    '#role': 'role'  # role은 DynamoDB 예약어
                },
                ExpressionAttributeValues={
                    ':role': new_role,
                    ':updated': datetime.now().isoformat()
                }
            )

            logger.info(f"User role updated: {user_id} -> {new_role}")
            return True

        except Exception as e:
            logger.error(f"Error updating user role: {str(e)}")
            raise

    def update_user_status(self, user_id: str, status: str) -> bool:
        """사용자 상태 변경"""
        try:
            if status not in ['active', 'suspended', 'deleted']:
                raise ValueError(f"Invalid status: {status}")

            self.user_tenants_table.update_item(
                Key={'userId': user_id},
                UpdateExpression='SET #status = :status, updatedAt = :updated',
                ExpressionAttributeNames={
                    '#status': 'status'  # status도 예약어일 수 있음
                },
                ExpressionAttributeValues={
                    ':status': status,
                    ':updated': datetime.now().isoformat()
                }
            )

            logger.info(f"User status updated: {user_id} -> {status}")
            return True

        except Exception as e:
            logger.error(f"Error updating user status: {str(e)}")
            raise

    # ========== Private 헬퍼 메서드 ==========

    def _increment_user_count(self, tenant_id: str, count: int) -> None:
        """테넌트의 사용자 수 증감"""
        try:
            self.tenants_table.update_item(
                Key={'tenantId': tenant_id},
                UpdateExpression='SET userCount = userCount + :count, updatedAt = :updated',
                ExpressionAttributeValues={
                    ':count': count,
                    ':updated': datetime.now().isoformat()
                }
            )
        except Exception:
            # 테넌트가 없을 수도 있으므로 에러 무시
            pass