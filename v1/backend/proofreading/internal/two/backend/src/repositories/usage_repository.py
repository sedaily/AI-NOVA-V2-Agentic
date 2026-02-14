"""
사용량(Usage) 리포지토리
DynamoDB와의 모든 상호작용을 캡슐화
"""
import boto3
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from ..models import Usage, UsageSummary

logger = logging.getLogger(__name__)


class UsageRepository:
    """사용량 데이터 접근 계층"""
    
    def __init__(self, table_name: str = 'nexus-usage', region: str = 'us-east-1'):
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = self.dynamodb.Table(table_name)
        logger.info(f"UsageRepository initialized with table: {table_name}")
    
    def save(self, usage: Usage) -> Usage:
        """사용량 저장 또는 업데이트"""
        try:
            # 타임스탬프 업데이트
            now = datetime.now().isoformat()
            if not usage.created_at:
                usage.created_at = now
            usage.updated_at = now
            
            # DynamoDB에 저장
            self.table.put_item(Item=usage.to_dict())
            
            logger.info(f"Usage saved: {usage.user_id}#{usage.usage_date}#{usage.engine_type}")
            return usage
            
        except Exception as e:
            logger.error(f"Error saving usage: {str(e)}")
            raise
    
    def find_by_date(self, user_id: str, usage_date: str, engine_type: str) -> Optional[Usage]:
        """특정 날짜의 사용량 조회"""
        try:
            response = self.table.get_item(
                Key={
                    'userId': user_id,
                    'usageDate#engineType': f"{usage_date}#{engine_type}"
                }
            )
            
            if 'Item' in response:
                return Usage.from_dict(response['Item'])
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding usage by date: {str(e)}")
            raise
    
    def find_by_user(self, user_id: str, start_date: str, end_date: str) -> List[Usage]:
        """사용자의 기간별 사용량 조회"""
        try:
            response = self.table.query(
                KeyConditionExpression='userId = :userId AND usageDate#engineType BETWEEN :start AND :end',
                ExpressionAttributeValues={
                    ':userId': user_id,
                    ':start': start_date,
                    ':end': f"{end_date}#zzz"  # 모든 엔진 타입 포함
                }
            )
            
            usages = []
            for item in response.get('Items', []):
                usages.append(Usage.from_dict(item))
            
            return usages
            
        except Exception as e:
            logger.error(f"Error finding usage by user: {str(e)}")
            raise
    
    def increment_usage(
        self, 
        user_id: str, 
        engine_type: str,
        input_tokens: int,
        output_tokens: int,
        cost: Decimal
    ) -> Usage:
        """사용량 증가 (원자적 업데이트)"""
        try:
            usage_date = datetime.now().strftime('%Y-%m-%d')
            sort_key = f"{usage_date}#{engine_type}"
            
            response = self.table.update_item(
                Key={
                    'userId': user_id,
                    'usageDate#engineType': sort_key
                },
                UpdateExpression="""
                    SET requestCount = if_not_exists(requestCount, :zero) + :one,
                        totalInputTokens = if_not_exists(totalInputTokens, :zero) + :input,
                        totalOutputTokens = if_not_exists(totalOutputTokens, :zero) + :output,
                        totalTokens = if_not_exists(totalTokens, :zero) + :total,
                        estimatedCost = if_not_exists(estimatedCost, :zero_cost) + :cost,
                        updatedAt = :now,
                        engineType = :engine,
                        usageDate = :date
                """,
                ExpressionAttributeValues={
                    ':zero': 0,
                    ':one': 1,
                    ':input': input_tokens,
                    ':output': output_tokens,
                    ':total': input_tokens + output_tokens,
                    ':zero_cost': Decimal('0'),
                    ':cost': cost,
                    ':now': datetime.now().isoformat(),
                    ':engine': engine_type,
                    ':date': usage_date
                },
                ReturnValues='ALL_NEW'
            )
            
            return Usage.from_dict(response['Attributes'])
            
        except Exception as e:
            logger.error(f"Error incrementing usage: {str(e)}")
            raise
    
    def get_summary(self, user_id: str, period: str = 'monthly') -> UsageSummary:
        """사용량 요약 조회"""
        try:
            # 기간 계산
            end_date = datetime.now()
            if period == 'daily':
                start_date = end_date - timedelta(days=1)
            elif period == 'weekly':
                start_date = end_date - timedelta(weeks=1)
            else:  # monthly
                start_date = end_date - timedelta(days=30)
            
            # 사용량 조회
            usages = self.find_by_user(
                user_id,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            # 요약 생성
            summary = UsageSummary(
                user_id=user_id,
                period=period,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            by_engine = {}
            for usage in usages:
                summary.total_requests += usage.request_count
                summary.total_tokens += usage.total_tokens
                summary.total_cost += usage.estimated_cost
                
                # 엔진별 집계
                if usage.engine_type not in by_engine:
                    by_engine[usage.engine_type] = {
                        'requests': 0,
                        'tokens': 0,
                        'cost': Decimal('0')
                    }
                
                by_engine[usage.engine_type]['requests'] += usage.request_count
                by_engine[usage.engine_type]['tokens'] += usage.total_tokens
                by_engine[usage.engine_type]['cost'] += usage.estimated_cost
            
            # Decimal을 문자열로 변환
            for engine in by_engine:
                by_engine[engine]['cost'] = str(by_engine[engine]['cost'])
            
            summary.by_engine = by_engine
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting usage summary: {str(e)}")
            raise
    
    def get_top_users(self, limit: int = 10, period_days: int = 30) -> List[Dict[str, Any]]:
        """상위 사용자 조회"""
        try:
            # 기간 설정
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)
            
            # 전체 스캔 (실제 환경에서는 GSI 사용 권장)
            response = self.table.scan(
                FilterExpression='usageDate BETWEEN :start AND :end',
                ExpressionAttributeValues={
                    ':start': start_date.strftime('%Y-%m-%d'),
                    ':end': end_date.strftime('%Y-%m-%d')
                }
            )
            
            # 사용자별 집계
            user_totals = {}
            for item in response.get('Items', []):
                user_id = item['userId']
                if user_id not in user_totals:
                    user_totals[user_id] = {
                        'userId': user_id,
                        'totalRequests': 0,
                        'totalTokens': 0,
                        'totalCost': Decimal('0')
                    }
                
                user_totals[user_id]['totalRequests'] += item.get('requestCount', 0)
                user_totals[user_id]['totalTokens'] += item.get('totalTokens', 0)
                user_totals[user_id]['totalCost'] += Decimal(item.get('estimatedCost', '0'))
            
            # 정렬 및 상위 N개 반환
            sorted_users = sorted(
                user_totals.values(),
                key=lambda x: x['totalCost'],
                reverse=True
            )[:limit]
            
            # Decimal을 문자열로 변환
            for user in sorted_users:
                user['totalCost'] = str(user['totalCost'])
            
            return sorted_users
            
        except Exception as e:
            logger.error(f"Error getting top users: {str(e)}")
            raise
    
    def delete_old_records(self, days_to_keep: int = 90) -> int:
        """오래된 기록 삭제"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime('%Y-%m-%d')
            
            # 삭제할 항목 조회
            response = self.table.scan(
                FilterExpression='usageDate < :cutoff',
                ExpressionAttributeValues={':cutoff': cutoff_date}
            )
            
            deleted_count = 0
            with self.table.batch_writer() as batch:
                for item in response.get('Items', []):
                    batch.delete_item(
                        Key={
                            'userId': item['userId'],
                            'usageDate#engineType': item['usageDate#engineType']
                        }
                    )
                    deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} old usage records")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting old records: {str(e)}")
            raise