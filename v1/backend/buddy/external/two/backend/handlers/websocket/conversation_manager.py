"""
대화 관리자 - DynamoDB에 대화 내역 저장/조회
"""
import boto3
import json
import logging
from datetime import datetime
import uuid
import os

logger = logging.getLogger(__name__)

# DynamoDB 설정
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
conversations_table = dynamodb.Table(os.environ.get('CONVERSATIONS_TABLE', 'p2-two-conversations-two'))

class ConversationManager:
    """대화 내역을 DynamoDB에서 관리"""
    
    @staticmethod
    def save_message(conversation_id: str, role: str, content: str, engine_type: str = '11', user_id: str = None):
        """개별 메시지 저장"""
        try:
            timestamp = datetime.utcnow().isoformat() + 'Z'
            message_id = str(uuid.uuid4())

            # conversationId-index GSI를 사용하여 기존 대화 조회
            gsi_response = conversations_table.query(
                IndexName='conversationId-index',
                KeyConditionExpression='conversationId = :cid',
                ExpressionAttributeValues={':cid': conversation_id},
                Limit=1
            )

            if gsi_response.get('Items'):
                # 기존 대화가 있으면 원본 키로 조회하여 업데이트
                existing_item = gsi_response['Items'][0]
                existing_user_id = existing_item.get('userId')
                user_id = user_id or existing_user_id  # user_id 우선, 없으면 기존 사용
                
                response = conversations_table.get_item(
                    Key={'userId': existing_user_id, 'conversationId': conversation_id}
                )
            else:
                response = None
            
            if response and 'Item' in response:
                # 기존 대화에 메시지 추가
                item = response['Item']
                messages = item.get('messages', [])
                
                # 중복 메시지 확인 - 개선된 알고리즘
                # 1. 최근 5개 메시지에서 확인 (기존 3개에서 확장)
                recent_messages = messages[-5:] if len(messages) > 5 else messages
                is_duplicate = False
                current_timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                
                for msg in recent_messages:
                    # 내용과 역할이 정확히 일치하고, 시간 차이가 30초 이내인 경우만 중복으로 판단
                    if (msg.get('content') == content and 
                        msg.get('role') == role):
                        try:
                            msg_timestamp = datetime.fromisoformat(msg.get('timestamp', '').replace('Z', '+00:00'))
                            time_diff = abs((current_timestamp - msg_timestamp).total_seconds())
                            
                            # 30초 이내에 동일한 내용이면 중복으로 판단
                            if time_diff <= 30:
                                logger.info(f"Duplicate message detected (same content & role within 30s), skipping: {content[:50]}")
                                is_duplicate = True
                                break
                            else:
                                logger.info(f"Similar message found but time diff is {time_diff}s, allowing")
                        except Exception as e:
                            # 타임스탬프 파싱 실패 시 기존 방식으로 판단
                            logger.warning(f"Timestamp parsing failed: {e}, using basic duplicate check")
                            if msg.get('content') == content and msg.get('role') == role:
                                is_duplicate = True
                                break
                
                if not is_duplicate:
                    messages.append({
                        'id': message_id,
                        'type': 'user' if role == 'user' else 'assistant',  # 프론트엔드 호환성
                        'role': role,  # 백워드 호환성
                        'content': content,
                        'timestamp': timestamp
                    })
                else:
                    logger.info(f"Skipping duplicate message for conversation {conversation_id}")
                    return True  # 중복이지만 성공으로 처리
                
                # 최근 50개 메시지만 유지 (메모리 관리)
                if len(messages) > 50:
                    messages = messages[-50:]
                
                # 업데이트 (userId가 없으면 추가)
                update_expr = 'SET messages = :msgs, updatedAt = :updated'
                expr_values = {
                    ':msgs': messages,
                    ':updated': timestamp
                }
                

                conversations_table.update_item(
                    Key={'userId': item['userId'], 'conversationId': conversation_id},
                    UpdateExpression=update_expr,
                    ExpressionAttributeValues=expr_values
                )
            else:
                # 새 대화 생성 - userId는 필수
                if not user_id:
                    logger.error(f"Cannot create conversation without userId for {conversation_id}")
                    return False

                item = {
                    'userId': user_id,  # 필수 키
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
            # conversationId-index GSI 사용하여 효율적으로 조회
            response = conversations_table.query(
                IndexName='conversationId-index',
                KeyConditionExpression='conversationId = :cid',
                ExpressionAttributeValues={':cid': conversation_id},
                Limit=1
            )

            if response.get('Items'):
                item = response['Items'][0]
                messages = item.get('messages', [])
                # 최근 N개만 반환
                return messages[-limit:] if len(messages) > limit else messages
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []
    
    @staticmethod
    def create_or_update_conversation(conversation_id: str, engine_type: str = '11', title: str = None, user_id: str = None):
        """대화 생성 또는 메타데이터 업데이트"""
        try:
            timestamp = datetime.utcnow().isoformat() + 'Z'

            # conversationId-index GSI를 사용하여 기존 대화 조회
            gsi_response = conversations_table.query(
                IndexName='conversationId-index',
                KeyConditionExpression='conversationId = :cid',
                ExpressionAttributeValues={':cid': conversation_id},
                Limit=1
            )

            if gsi_response.get('Items'):
                # 기존 대화가 있으면 원본 키로 조회하여 업데이트
                existing_item = gsi_response['Items'][0]
                existing_user_id = existing_item.get('userId')
                user_id = user_id or existing_user_id  # user_id 우선, 없으면 기존 사용
                
                response = conversations_table.get_item(
                    Key={'userId': existing_user_id, 'conversationId': conversation_id}
                )
            else:
                response = {}
            
            if 'Item' in response:
                # 업데이트
                update_expr = 'SET updatedAt = :updated'
                expr_values = {':updated': timestamp}
                
                if title:
                    update_expr += ', title = :title'
                    expr_values[':title'] = title
                
                conversations_table.update_item(
                    Key={'userId': response['Item']['userId'], 'conversationId': conversation_id},
                    UpdateExpression=update_expr,
                    ExpressionAttributeValues=expr_values
                )
            else:
                # 새로 생성 (user_id 필요)
                if not user_id:
                    logger.error(f"Cannot create conversation without userId")
                    return False

                conversations_table.put_item(
                    Item={
                        'userId': user_id,
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