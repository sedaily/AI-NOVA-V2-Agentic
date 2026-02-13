"""
대화(Conversation) 리포지토리
DynamoDB와의 모든 상호작용을 캡슐화
"""
import boto3
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import logging
import os

from ..models import Conversation, Message

logger = logging.getLogger(__name__)


class ConversationRepository:
    """대화 데이터 접근 계층"""

    def __init__(self, table_name: str = None, region: str = None):
        table_name = table_name or os.environ.get('CONVERSATIONS_TABLE', 'f1-conversations-two')
        region = region or os.environ.get('AWS_REGION', 'us-east-1')
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = self.dynamodb.Table(table_name)
        logger.info(f"ConversationRepository initialized with table: {table_name}")
    
    def save(self, conversation: Conversation) -> Conversation:
        """대화 저장"""
        try:
            # ID가 없으면 생성
            if not conversation.conversation_id:
                conversation.conversation_id = str(uuid.uuid4())
            
            # 타임스탬프 업데이트
            now = datetime.now().isoformat()
            if not conversation.created_at:
                conversation.created_at = now
            conversation.updated_at = now
            
            # DynamoDB에 저장
            self.table.put_item(Item=conversation.to_dict())
            
            logger.info(f"Conversation saved: {conversation.conversation_id}")
            return conversation
            
        except Exception as e:
            logger.error(f"Error saving conversation: {str(e)}")
            raise
    
    def find_by_id(self, conversation_id: str, user_id: str = None) -> Optional[Conversation]:
        """ID로 대화 조회"""
        try:
            # user_id가 제공되지 않은 경우 조회
            if not user_id:
                # conversation_id로 먼저 스캔해서 실제 데이터를 찾음
                response = self.table.scan(
                    FilterExpression='conversationId = :cid',
                    ExpressionAttributeValues={':cid': conversation_id}
                )
                if response.get('Items'):
                    return Conversation.from_dict(response['Items'][0])
                return None

            # user_id가 제공된 경우 직접 조회
            response = self.table.get_item(
                Key={
                    'userId': user_id,
                    'conversationId': conversation_id
                }
            )

            if 'Item' in response:
                return Conversation.from_dict(response['Item'])

            return None

        except Exception as e:
            logger.error(f"Error finding conversation by id: {str(e)}")
            raise
    
    def find_by_user(self, user_id: str, limit: int = 1000) -> List[Conversation]:
        """사용자별 대화 목록 조회 - 모든 대화 반환"""
        try:
            conversations = []
            last_evaluated_key = None
            
            # 인덱스가 없는 경우 Scan 사용 (임시 해결책)
            while True:
                scan_params = {
                    'FilterExpression': 'userId = :userId',
                    'ExpressionAttributeValues': {
                        ':userId': user_id
                    }
                }

                # limit이 지정되면 해당 개수만큼만 조회
                if limit and limit < 1000:
                    scan_params['Limit'] = limit * 10  # Scan은 필터링 후 적용되므로 더 많이 가져옴

                # 다음 페이지가 있으면 계속 조회
                if last_evaluated_key:
                    scan_params['ExclusiveStartKey'] = last_evaluated_key

                response = self.table.scan(**scan_params)
                
                # 현재 페이지의 결과 추가
                for item in response.get('Items', []):
                    conversations.append(Conversation.from_dict(item))
                
                # limit에 도달했거나 더 이상 페이지가 없으면 종료
                if limit and len(conversations) >= limit:
                    return conversations[:limit]
                
                last_evaluated_key = response.get('LastEvaluatedKey')
                if not last_evaluated_key:
                    break
            
            return conversations
            
        except Exception as e:
            logger.error(f"Error finding conversations by user: {str(e)}")
            raise
    
    def update_messages(self, conversation_id: str, messages: List[Message]) -> bool:
        """대화의 메시지 업데이트"""
        try:
            # user_id를 먼저 찾음
            response = self.table.scan(
                FilterExpression='conversationId = :cid',
                ExpressionAttributeValues={':cid': conversation_id}
            )

            if not response.get('Items'):
                logger.error(f"Conversation not found: {conversation_id}")
                return False

            user_id = response['Items'][0].get('userId')

            messages_data = [
                {
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.timestamp or datetime.now().isoformat(),
                    'metadata': msg.metadata
                }
                for msg in messages
            ]

            self.table.update_item(
                Key={
                    'userId': user_id,
                    'conversationId': conversation_id
                },
                UpdateExpression='SET messages = :messages, updatedAt = :updatedAt',
                ExpressionAttributeValues={
                    ':messages': messages_data,
                    ':updatedAt': datetime.now().isoformat()
                }
            )

            logger.info(f"Messages updated for conversation: {conversation_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating messages: {str(e)}")
            raise
    
    def update_title(self, conversation_id: str, title: str, user_id: str = None) -> bool:
        """대화 제목 업데이트"""
        try:
            logger.info(f"Attempting to update title for conversation: {conversation_id} to: {title}")

            # user_id가 제공되지 않은 경우 조회
            if not user_id:
                # conversation_id로 먼저 스캔해서 실제 userId를 찾음
                response = self.table.scan(
                    FilterExpression='conversationId = :cid',
                    ExpressionAttributeValues={':cid': conversation_id}
                )

                if not response.get('Items'):
                    logger.error(f"Conversation not found: {conversation_id}")
                    return False

                user_id = response['Items'][0].get('userId')
                logger.info(f"Found userId: {user_id} for conversation: {conversation_id}")

            response = self.table.update_item(
                Key={
                    'userId': user_id,
                    'conversationId': conversation_id
                },
                UpdateExpression='SET title = :title, updatedAt = :updatedAt',
                ExpressionAttributeValues={
                    ':title': title,
                    ':updatedAt': datetime.now().isoformat()
                },
                ReturnValues='UPDATED_NEW'
            )

            logger.info(f"DynamoDB update response: {response}")
            logger.info(f"Title successfully updated for conversation: {conversation_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating title for {conversation_id}: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            raise
    
    def delete(self, conversation_id: str, user_id: str = None) -> bool:
        """대화 삭제"""
        try:
            # user_id가 제공되지 않은 경우 조회
            if not user_id:
                # conversation_id로 먼저 스캔해서 실제 userId를 찾음
                response = self.table.scan(
                    FilterExpression='conversationId = :cid',
                    ExpressionAttributeValues={':cid': conversation_id}
                )

                if not response.get('Items'):
                    logger.error(f"Conversation not found: {conversation_id}")
                    return False

                user_id = response['Items'][0].get('userId')
                logger.info(f"Found userId: {user_id} for conversation: {conversation_id}")

            self.table.delete_item(
                Key={
                    'userId': user_id,
                    'conversationId': conversation_id
                }
            )

            logger.info(f"Conversation deleted: {conversation_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting conversation: {str(e)}")
            raise
    
    def find_recent(self, user_id: str, engine_type: Optional[str] = None, days: int = 30) -> List[Conversation]:
        """최근 대화 조회"""
        try:
            from datetime import timedelta
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            filter_expression = 'updatedAt > :cutoff'
            expression_values = {
                ':userId': user_id,
                ':cutoff': cutoff_date
            }
            
            if engine_type:
                filter_expression += ' AND engineType = :engineType'
                expression_values[':engineType'] = engine_type
            
            response = self.table.query(
                IndexName='userId-createdAt-index',
                KeyConditionExpression='userId = :userId',
                FilterExpression=filter_expression,
                ExpressionAttributeValues=expression_values,
                ScanIndexForward=False
            )
            
            conversations = []
            for item in response.get('Items', []):
                conversations.append(Conversation.from_dict(item))
            
            return conversations
            
        except Exception as e:
            logger.error(f"Error finding recent conversations: {str(e)}")
            raise