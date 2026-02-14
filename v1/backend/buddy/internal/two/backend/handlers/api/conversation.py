"""
Conversation API Handler
대화 관리 REST API 엔드포인트
"""
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal

from src.services.conversation_service import ConversationService
from utils.response import APIResponse
from utils.logger import setup_logger

# 로깅 설정
logger = setup_logger(__name__)




def handler(event, context):
    """
    Lambda 핸들러 - 대화 관리 API
    """
    logger.info(f"Event: {json.dumps(event)}")
    
    # API Gateway v2 형식 처리
    if 'version' in event and event['version'] == '2.0':
        # API Gateway v2 (HTTP API)
        http_method = event.get('requestContext', {}).get('http', {}).get('method')
        path_params = event.get('pathParameters', {})
    else:
        # API Gateway v1 (REST API) 또는 직접 호출
        http_method = event.get('httpMethod')
        path_params = event.get('pathParameters', {})
    
    # OPTIONS 요청 처리 (CORS)
    if http_method == 'OPTIONS':
        return APIResponse.cors_preflight()
    
    try:
        
        # Service 초기화
        conversation_service = ConversationService()
        
        # GET /conversations - 목록 조회
        if http_method == 'GET' and not path_params:
            # 쿼리 파라미터에서 userId와 engineType 추출
            query_params = event.get('queryStringParameters', {}) or {}
            user_id = query_params.get('userId')
            engine_type = query_params.get('engineType') or query_params.get('engine')
            
            if not user_id:
                return APIResponse.error('userId is required', 400)
            
            # get_user_conversations 메서드 사용
            conversations = conversation_service.get_user_conversations(user_id, limit=1000)

            # engine_type으로 필터링이 필요한 경우
            if engine_type:
                conversations = [c for c in conversations if c.engine_type == engine_type]

            # updatedAt 기준으로 내림차순 정렬 (최신이 위로)
            conversations.sort(key=lambda x: x.updated_at or x.created_at or '', reverse=True)

            # to_dict 메서드로 변환
            conversations_dict = [conv.to_dict() for conv in conversations]

            return APIResponse.success({
                'conversations': conversations_dict,
                'count': len(conversations_dict)
            })
        
        # GET /conversations/{conversationId} - 상세 조회
        elif http_method == 'GET' and 'conversationId' in path_params:
            conversation = conversation_service.get_conversation(
                path_params['conversationId']
            )
            if conversation:
                return APIResponse.success(conversation.to_dict())
            else:
                return APIResponse.error('Conversation not found', 404)
        
        # POST /conversations - 대화 저장
        elif http_method == 'POST':
            body = json.loads(event.get('body', '{}'))

            # 필수 필드 확인
            user_id = body.get('userId')
            conversation_id = body.get('conversationId')
            engine_type = body.get('engineType', '11')
            title = body.get('title')
            messages = body.get('messages', [])
            initial_message = messages[0].get('content') if messages else None

            if not user_id:
                return APIResponse.error('userId is required', 400)

            # conversationId가 있으면 기존 대화가 있는지 확인
            if conversation_id:
                existing = conversation_service.get_conversation(conversation_id)
                if existing:
                    # 기존 대화가 있으면 메시지 업데이트
                    logger.info(f"Conversation {conversation_id} exists, updating messages")

                    # 메시지가 있으면 업데이트
                    if messages and len(messages) > 0:
                        from src.models import Message
                        message_objects = []
                        for msg in messages:
                            message_objects.append(Message(
                                role=msg.get('type', msg.get('role', 'user')),  # type을 role로 매핑
                                content=msg.get('content'),
                                timestamp=msg.get('timestamp'),
                                metadata=msg.get('metadata', {})
                            ))

                        success = conversation_service.repository.update_messages(
                            conversation_id,
                            message_objects
                        )

                        if success:
                            logger.info(f"Successfully updated {len(messages)} messages for {conversation_id}")
                        else:
                            logger.error(f"Failed to update messages for {conversation_id}")

                    return APIResponse.success({
                        'conversationId': conversation_id,
                        'userId': user_id,
                        'engineType': engine_type,
                        'title': existing.title if existing else title,
                        'message': 'Conversation updated'
                    }, 200)

            # 새 대화 생성
            saved = conversation_service.create_conversation(
                user_id=user_id,
                engine_type=engine_type,
                title=title,
                initial_message=initial_message
            )

            # to_dict 메서드로 변환하여 반환
            return APIResponse.success(saved.to_dict(), 201)
        
        # PATCH /conversations/{conversationId} - 대화 부분 업데이트 (제목 수정 등)
        elif http_method == 'PATCH' and 'conversationId' in path_params:
            body = json.loads(event.get('body', '{}'))
            conversation_id = path_params['conversationId']
            
            logger.info(f"PATCH request for conversation: {conversation_id}")
            logger.info(f"Request body: {body}")
            
            if 'title' in body:
                new_title = body['title']
                logger.info(f"Attempting to update title to: {new_title}")
                
                success = conversation_service.update_title(conversation_id, new_title)
                
                logger.info(f"Update result: {success}")
                
                if success:
                    logger.info(f"Successfully updated conversation {conversation_id}")
                    return APIResponse.success({'message': 'Conversation updated'})
                else:
                    logger.error(f"Failed to update conversation {conversation_id}")
                    return APIResponse.error('Failed to update conversation', 500)
            else:
                logger.warning("No title field in request body")
                return APIResponse.error('No title field to update', 400)
        
        # PUT /conversations/{conversationId} - 대화 업데이트 (메시지 저장)
        elif http_method == 'PUT' and 'conversationId' in path_params:
            body = json.loads(event.get('body', '{}'))
            conversation_id = path_params['conversationId']

            logger.info(f"PUT request for conversation: {conversation_id}")
            logger.info(f"Request body keys: {body.keys()}")

            # 메시지 배열이 있는 경우 업데이트
            if 'messages' in body:
                messages = body['messages']
                logger.info(f"Updating {len(messages)} messages for conversation {conversation_id}")

                # Repository의 update_messages 메서드 호출
                from src.models import Message
                message_objects = []
                for msg in messages:
                    message_objects.append(Message(
                        role=msg.get('role'),
                        content=msg.get('content'),
                        timestamp=msg.get('timestamp'),
                        metadata=msg.get('metadata', {})
                    ))

                success = conversation_service.repository.update_messages(
                    conversation_id,
                    message_objects
                )

                if success:
                    logger.info(f"Successfully updated messages for {conversation_id}")
                    return APIResponse.success({'message': 'Messages updated'})
                else:
                    logger.error(f"Failed to update messages for {conversation_id}")
                    return APIResponse.error('Failed to update messages', 500)

            # 다른 필드 업데이트 (title, metadata 등)
            else:
                logger.warning("No messages field in PUT request")
                return APIResponse.error('No messages to update', 400)

        # DELETE /conversations/{conversationId} - 대화 삭제
        elif http_method == 'DELETE' and 'conversationId' in path_params:
            success = conversation_service.delete_conversation(
                path_params['conversationId']
            )
            if success:
                return APIResponse.success({'message': 'Conversation deleted'})
            else:
                return APIResponse.error('Failed to delete conversation', 500)
        
        else:
            return APIResponse.error('Method not allowed', 405)
            
    except Exception as e:
        logger.error(f"Error in conversation handler: {e}", exc_info=True)
        return APIResponse.error(str(e), 500)