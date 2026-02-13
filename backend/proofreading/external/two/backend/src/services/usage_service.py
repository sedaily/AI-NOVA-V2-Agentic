"""
사용량(Usage) 비즈니스 로직
"""
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta
import logging

from ..models import Usage, UsageSummary
from ..repositories import UsageRepository

logger = logging.getLogger(__name__)


class UsageService:
    """사용량 관련 비즈니스 로직"""
    
    # 토큰당 예상 비용 (USD)
    COST_PER_1K_INPUT_TOKENS = {
        'T5': Decimal('0.003'),   # Claude Sonnet 입력 토큰 비용
        'H8': Decimal('0.015')    # Claude Opus 입력 토큰 비용
    }
    
    COST_PER_1K_OUTPUT_TOKENS = {
        'T5': Decimal('0.015'),   # Claude Sonnet 출력 토큰 비용
        'H8': Decimal('0.075')    # Claude Opus 출력 토큰 비용
    }
    
    def __init__(self, repository: Optional[UsageRepository] = None):
        self.repository = repository or UsageRepository()
    
    def track_usage(
        self,
        user_id: str,
        engine_type: str,
        input_tokens: int,
        output_tokens: int
    ) -> Usage:
        """사용량 추적"""
        try:
            # 비용 계산
            cost = self.calculate_cost(engine_type, input_tokens, output_tokens)
            
            # 사용량 증가 (원자적 업데이트)
            usage = self.repository.increment_usage(
                user_id=user_id,
                engine_type=engine_type,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost
            )
            
            logger.info(
                f"Usage tracked for {user_id}: {input_tokens} input, "
                f"{output_tokens} output tokens, cost: ${cost}"
            )
            
            return usage
            
        except Exception as e:
            logger.error(f"Error tracking usage: {str(e)}")
            raise
    
    def calculate_cost(
        self,
        engine_type: str,
        input_tokens: int,
        output_tokens: int
    ) -> Decimal:
        """토큰 사용량에 따른 비용 계산"""
        try:
            # 입력 토큰 비용
            input_cost_rate = self.COST_PER_1K_INPUT_TOKENS.get(
                engine_type, 
                Decimal('0.003')
            )
            input_cost = (Decimal(input_tokens) / 1000) * input_cost_rate
            
            # 출력 토큰 비용
            output_cost_rate = self.COST_PER_1K_OUTPUT_TOKENS.get(
                engine_type,
                Decimal('0.015')
            )
            output_cost = (Decimal(output_tokens) / 1000) * output_cost_rate
            
            total_cost = input_cost + output_cost
            
            # 소수점 4자리까지 반올림
            return total_cost.quantize(Decimal('0.0001'))
            
        except Exception as e:
            logger.error(f"Error calculating cost: {str(e)}")
            return Decimal('0.0000')
    
    def get_usage_by_date(
        self,
        user_id: str,
        date: str,
        engine_type: str
    ) -> Optional[Usage]:
        """특정 날짜의 사용량 조회"""
        try:
            return self.repository.find_by_date(user_id, date, engine_type)
        except Exception as e:
            logger.error(f"Error getting usage by date: {str(e)}")
            raise
    
    def get_usage_history(
        self,
        user_id: str,
        days: int = 30
    ) -> List[Usage]:
        """사용량 이력 조회"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            return self.repository.find_by_user(
                user_id=user_id,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
        except Exception as e:
            logger.error(f"Error getting usage history: {str(e)}")
            raise
    
    def get_usage_summary(
        self,
        user_id: str,
        period: str = 'monthly'
    ) -> UsageSummary:
        """사용량 요약 조회"""
        try:
            if period not in ['daily', 'weekly', 'monthly']:
                period = 'monthly'
            
            return self.repository.get_summary(user_id, period)
            
        except Exception as e:
            logger.error(f"Error getting usage summary: {str(e)}")
            raise
    
    def get_current_month_usage(self, user_id: str) -> Dict[str, Any]:
        """현재 월 사용량 조회"""
        try:
            # 이번 달 시작일
            now = datetime.now()
            start_date = datetime(now.year, now.month, 1)
            
            # 사용량 조회
            usages = self.repository.find_by_user(
                user_id=user_id,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=now.strftime('%Y-%m-%d')
            )
            
            # 집계
            result = {
                'month': now.strftime('%Y-%m'),
                'total_requests': 0,
                'total_tokens': 0,
                'total_cost': Decimal('0'),
                'by_engine': {},
                'daily_usage': []
            }
            
            by_date = {}
            for usage in usages:
                # 전체 집계
                result['total_requests'] += usage.request_count
                result['total_tokens'] += usage.total_tokens
                result['total_cost'] += usage.estimated_cost
                
                # 엔진별 집계
                engine = usage.engine_type
                if engine not in result['by_engine']:
                    result['by_engine'][engine] = {
                        'requests': 0,
                        'tokens': 0,
                        'cost': Decimal('0')
                    }
                
                result['by_engine'][engine]['requests'] += usage.request_count
                result['by_engine'][engine]['tokens'] += usage.total_tokens
                result['by_engine'][engine]['cost'] += usage.estimated_cost
                
                # 일별 집계
                date = usage.usage_date
                if date not in by_date:
                    by_date[date] = {
                        'date': date,
                        'requests': 0,
                        'tokens': 0,
                        'cost': Decimal('0')
                    }
                
                by_date[date]['requests'] += usage.request_count
                by_date[date]['tokens'] += usage.total_tokens
                by_date[date]['cost'] += usage.estimated_cost
            
            # 일별 데이터 정렬
            result['daily_usage'] = sorted(
                by_date.values(),
                key=lambda x: x['date']
            )
            
            # Decimal을 문자열로 변환
            result['total_cost'] = str(result['total_cost'])
            for engine in result['by_engine']:
                result['by_engine'][engine]['cost'] = str(
                    result['by_engine'][engine]['cost']
                )
            for daily in result['daily_usage']:
                daily['cost'] = str(daily['cost'])
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting current month usage: {str(e)}")
            raise
    
    def get_usage_limits(self, user_id: str) -> Dict[str, Any]:
        """사용자의 사용량 제한 조회"""
        try:
            # 기본 제한 (추후 사용자별 커스텀 제한 구현 가능)
            limits = {
                'daily': {
                    'requests': 1000,
                    'tokens': 1000000,
                    'cost': '100.00'
                },
                'monthly': {
                    'requests': 30000,
                    'tokens': 30000000,
                    'cost': '3000.00'
                }
            }
            
            # 현재 사용량 포함
            current = self.get_current_month_usage(user_id)
            
            return {
                'limits': limits,
                'current_usage': {
                    'requests': current['total_requests'],
                    'tokens': current['total_tokens'],
                    'cost': current['total_cost']
                },
                'remaining': {
                    'requests': limits['monthly']['requests'] - current['total_requests'],
                    'tokens': limits['monthly']['tokens'] - current['total_tokens'],
                    'cost': str(
                        Decimal(limits['monthly']['cost']) - Decimal(current['total_cost'])
                    )
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting usage limits: {str(e)}")
            raise
    
    def check_usage_limit(
        self,
        user_id: str,
        estimated_tokens: int
    ) -> bool:
        """사용량 제한 확인"""
        try:
            limits = self.get_usage_limits(user_id)
            
            # 토큰 제한 확인
            if limits['remaining']['tokens'] < estimated_tokens:
                logger.warning(f"User {user_id} exceeded token limit")
                return False
            
            # 비용 제한 확인
            if Decimal(limits['remaining']['cost']) <= 0:
                logger.warning(f"User {user_id} exceeded cost limit")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking usage limit: {str(e)}")
            return True  # 에러 시 일단 허용
    
    def get_top_users(
        self,
        limit: int = 10,
        period_days: int = 30
    ) -> List[Dict[str, Any]]:
        """상위 사용자 조회"""
        try:
            return self.repository.get_top_users(limit, period_days)
        except Exception as e:
            logger.error(f"Error getting top users: {str(e)}")
            raise
    
    def cleanup_old_records(self, days_to_keep: int = 90) -> int:
        """오래된 사용량 기록 정리"""
        try:
            deleted = self.repository.delete_old_records(days_to_keep)
            logger.info(f"Cleaned up {deleted} old usage records")
            return deleted
        except Exception as e:
            logger.error(f"Error cleaning up old records: {str(e)}")
            raise