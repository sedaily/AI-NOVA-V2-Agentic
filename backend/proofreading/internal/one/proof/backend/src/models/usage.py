"""
사용량(Usage) 도메인 모델
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime
from decimal import Decimal


@dataclass
class Usage:
    """사용량 모델"""
    user_id: str
    usage_date: str  # YYYY-MM-DD format
    engine_type: str  # 'T5' or 'H8'
    request_count: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: Decimal = Decimal('0.00')
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """DynamoDB 저장용 딕셔너리 변환"""
        return {
            'userId': self.user_id,
            'usageDate': self.usage_date,
            'engineType': self.engine_type,
            'requestCount': self.request_count,
            'totalInputTokens': self.total_input_tokens,
            'totalOutputTokens': self.total_output_tokens,
            'totalTokens': self.total_tokens,
            'estimatedCost': str(self.estimated_cost),
            'metadata': self.metadata,
            'createdAt': self.created_at or datetime.now().isoformat(),
            'updatedAt': self.updated_at or datetime.now().isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Usage':
        """DynamoDB 데이터에서 모델 생성"""
        return cls(
            user_id=data['userId'],
            usage_date=data['usageDate'],
            engine_type=data.get('engineType', 'unknown'),
            request_count=data.get('requestCount', 0),
            total_input_tokens=data.get('totalInputTokens', 0),
            total_output_tokens=data.get('totalOutputTokens', 0),
            total_tokens=data.get('totalTokens', 0),
            estimated_cost=Decimal(data.get('estimatedCost', '0.00')),
            metadata=data.get('metadata', {}),
            created_at=data.get('createdAt'),
            updated_at=data.get('updatedAt')
        )
    
    def add_usage(self, input_tokens: int, output_tokens: int, cost: Decimal) -> None:
        """사용량 추가"""
        self.request_count += 1
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_tokens += (input_tokens + output_tokens)
        self.estimated_cost += cost
        self.updated_at = datetime.now().isoformat()


@dataclass
class UsageSummary:
    """사용량 요약 모델"""
    user_id: str
    period: str  # 'daily', 'weekly', 'monthly'
    start_date: str
    end_date: str
    total_requests: int = 0
    total_tokens: int = 0
    total_cost: Decimal = Decimal('0.00')
    by_engine: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            'userId': self.user_id,
            'period': self.period,
            'startDate': self.start_date,
            'endDate': self.end_date,
            'totalRequests': self.total_requests,
            'totalTokens': self.total_tokens,
            'totalCost': str(self.total_cost),
            'byEngine': self.by_engine
        }