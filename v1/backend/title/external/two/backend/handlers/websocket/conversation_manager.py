"""
대화 관리자 - DynamoDB에 대화 내역 저장/조회
"""
import boto3
import json
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

# DynamoDB 설정
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
conversations_table = dynamodb.Table('nx-tt-dev-ver3-conversations')

class ConversationManager:
    """대화 내역을 DynamoDB에서 관리"""
    
    @staticmethod
    def save_message(conversation_id: str, role: str, content: str, engine_type: str = 'T5', user_id: str = None):
        """개별 메시지 저장"""
        try:
            timestamp = datetime.utcnow().isoformat() + 'Z'
            message_id = str(uuid.uuid4())
            
            # 기존 대화 조회
            response = conversations_table.get_item(
                Key={'conversationId': conversation_id}
            )
            
            if 'Item' in response:
                # 기존 대화에 메시지 추가
                item = response['Item']
                messages = item.get('messages', [])
                messages.append({
                    'id': message_id,
                    'type': 'user' if role == 'user' else 'assistant',  # 프론트엔드 호환성
                    'role': role,  # 백워드 호환성
                    'content': content,
                    'timestamp': timestamp
                })
                
                # 최근 50개 메시지만 유지 (메모리 관리)
                if len(messages) > 50:
                    messages = messages[-50:]
                
                # 업데이트 (userId가 없으면 추가)
                update_expr = 'SET messages = :msgs, updatedAt = :updated'
                expr_values = {
                    ':msgs': messages,
                    ':updated': timestamp
                }
                
                # userId가 없는 경우 추가
                if user_id and not item.get('userId'):
                    update_expr += ', userId = :uid'
                    expr_values[':uid'] = user_id
                
                conversations_table.update_item(
                    Key={'conversationId': conversation_id},
                    UpdateExpression=update_expr,
                    ExpressionAttributeValues=expr_values
                )
            else:
                # 새 대화 생성
                item = {
                    'conversationId': conversation_id,
                    'engineType': engine_type,
                    'messages': [{
                        'id': message_id,
                        'type': 'user' if role == 'user' else 'assistant',  # 프론트엔드 호환성
                        'role': role,  # 백워드 호환성
                        'content': content,
                        'timestamp': timestamp
                    }],
                    'createdAt': timestamp,
                    'updatedAt': timestamp,
                    'title': content[:50] if role == 'user' else 'New Conversation'
                }
                
                # userId 추가
                if user_id:
                    item['userId'] = user_id
                
                conversations_table.put_item(Item=item)
            
            logger.info(f"Message saved: {conversation_id} - {role}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")
            return False
    
    @staticmethod
    def get_conversation_history(conversation_id: str, limit: int = 20):
        """대화 히스토리 조회"""
        try:
            response = conversations_table.get_item(
                Key={'conversationId': conversation_id}
            )
            
            if 'Item' in response:
                messages = response['Item'].get('messages', [])
                # 최근 N개만 반환
                return messages[-limit:] if len(messages) > limit else messages
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []
    
    @staticmethod
    def create_or_update_conversation(conversation_id: str, engine_type: str = 'T5', title: str = None):
        """대화 생성 또는 메타데이터 업데이트"""
        try:
            timestamp = datetime.utcnow().isoformat() + 'Z'
            
            # 기존 대화 확인
            response = conversations_table.get_item(
                Key={'conversationId': conversation_id}
            )
            
            if 'Item' in response:
                # 업데이트
                update_expr = 'SET updatedAt = :updated'
                expr_values = {':updated': timestamp}
                
                if title:
                    update_expr += ', title = :title'
                    expr_values[':title'] = title
                
                conversations_table.update_item(
                    Key={'conversationId': conversation_id},
                    UpdateExpression=update_expr,
                    ExpressionAttributeValues=expr_values
                )
            else:
                # 새로 생성
                conversations_table.put_item(
                    Item={
                        'conversationId': conversation_id,
                        'engineType': engine_type,
                        'messages': [],
                        'title': title or 'New Conversation',
                        'createdAt': timestamp,
                        'updatedAt': timestamp
                    }
                )
            
            logger.info(f"Conversation created/updated: {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating/updating conversation: {str(e)}")
            return False