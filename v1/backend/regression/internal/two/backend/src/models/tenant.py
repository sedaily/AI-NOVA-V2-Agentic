"""
테넌트(Tenant) 도메인 모델
멀티테넌트 구조를 위한 회사/조직 정보 관리
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class UserTenant:
    """사용자-테넌트 매핑 모델"""
    user_id: str  # Cognito sub
    email: str
    tenant_id: str
    tenant_name: str
    plan: str  # 'free', 'pro', 'enterprise'
    role: str  # 'admin', 'user'
    status: str = 'active'  # 'active', 'suspended', 'deleted'
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """DynamoDB 저장용 딕셔너리 변환"""
        return {
            'userId': self.user_id,
            'email': self.email,
            'tenantId': self.tenant_id,
            'tenantName': self.tenant_name,
            'plan': self.plan,
            'role': self.role,
            'status': self.status,
            'createdAt': self.created_at or datetime.now().isoformat(),
            'updatedAt': self.updated_at or datetime.now().isoformat(),
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserTenant':
        """DynamoDB 데이터에서 모델 생성"""
        return cls(
            user_id=data['userId'],
            email=data['email'],
            tenant_id=data['tenantId'],
            tenant_name=data['tenantName'],
            plan=data['plan'],
            role=data['role'],
            status=data.get('status', 'active'),
            created_at=data.get('createdAt'),
            updated_at=data.get('updatedAt'),
            metadata=data.get('metadata', {})
        )


@dataclass
class Tenant:
    """테넌트(회사/조직) 모델"""
    tenant_id: str  # 'sedaily', 'chosun', etc
    tenant_name: str  # '서울경제신문', '조선일보', etc
    plan: str  # 'free', 'pro', 'enterprise'
    status: str = 'active'  # 'active', 'suspended', 'trial'

    # 사용량 제한
    api_call_limit: int = 10000  # 월 API 호출 제한
    api_call_count: int = 0  # 현재 월 API 호출 수
    storage_limit_gb: int = 10  # 스토리지 제한 (GB)
    storage_usage_gb: float = 0.0  # 현재 사용량 (GB)
    user_limit: int = 100  # 사용자 수 제한
    user_count: int = 0  # 현재 사용자 수

    # 기능 플래그
    features: List[str] = field(default_factory=list)  # ['C7_ENGINE', 'TRANSCRIBE', 'ADVANCED_ANALYTICS']

    # 설정
    settings: Dict[str, Any] = field(default_factory=dict)

    # 시간 정보
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    billing_cycle_start: Optional[str] = None  # 과금 주기 시작일
    trial_ends_at: Optional[str] = None  # 체험판 종료일

    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """DynamoDB 저장용 딕셔너리 변환"""
        return {
            'tenantId': self.tenant_id,
            'tenantName': self.tenant_name,
            'plan': self.plan,
            'status': self.status,
            'apiCallLimit': self.api_call_limit,
            'apiCallCount': self.api_call_count,
            'storageLimitGb': self.storage_limit_gb,
            'storageUsageGb': self.storage_usage_gb,
            'userLimit': self.user_limit,
            'userCount': self.user_count,
            'features': self.features,
            'settings': self.settings,
            'createdAt': self.created_at or datetime.now().isoformat(),
            'updatedAt': self.updated_at or datetime.now().isoformat(),
            'billingCycleStart': self.billing_cycle_start,
            'trialEndsAt': self.trial_ends_at,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tenant':
        """DynamoDB 데이터에서 모델 생성"""
        return cls(
            tenant_id=data['tenantId'],
            tenant_name=data['tenantName'],
            plan=data['plan'],
            status=data.get('status', 'active'),
            api_call_limit=data.get('apiCallLimit', 10000),
            api_call_count=data.get('apiCallCount', 0),
            storage_limit_gb=data.get('storageLimitGb', 10),
            storage_usage_gb=data.get('storageUsageGb', 0.0),
            user_limit=data.get('userLimit', 100),
            user_count=data.get('userCount', 0),
            features=data.get('features', []),
            settings=data.get('settings', {}),
            created_at=data.get('createdAt'),
            updated_at=data.get('updatedAt'),
            billing_cycle_start=data.get('billingCycleStart'),
            trial_ends_at=data.get('trialEndsAt'),
            metadata=data.get('metadata', {})
        )

    def is_limit_exceeded(self) -> bool:
        """사용량 제한 초과 여부 확인"""
        return self.api_call_count >= self.api_call_limit

    def has_feature(self, feature: str) -> bool:
        """특정 기능 사용 가능 여부 확인"""
        return feature in self.features