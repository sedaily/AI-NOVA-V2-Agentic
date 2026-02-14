"""
Conversation API Handler
대화 관리 REST API 엔드포인트
"""
import json
import base64
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
    멀티테넌트 지원 (하위 호환성 유지)
    """
    # OPTIONS 요청을 가장 먼저 처리
    http_method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method')
    
    if http_method == 'OPTIONS':
        logger.info("OPTIONS request received - returning CORS headers")
        return APIResponse.cors_preflight()
    
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

    # 멀티테넌트: Authorizer Context 추출 (신규)
    request_context = event.get('requestContext', {})
    authorizer_context = request_context.get('authorizer', {})

    # Authorizer가 있으면 사용, 없으면 기존 방식 (하위 호환성)
    auth_user_id = None
    tenant_id = 'sedaily'  # 기본값
    user_role = 'user'  # 기본값

    if authorizer_context:
        # 멀티테넌트 방식 (Authorizer 사용)
        auth_user_id = authorizer_context.get('userId') or authorizer_context.get('principalId')
        tenant_id = authorizer_context.get('tenantId', 'sedaily')
        user_role = authorizer_context.get('role', 'user')
        logger.info(f"Multi-tenant mode: tenant={tenant_id}, user={auth_user_id}, role={user_role}")
    
    # OPTIONS 요청 처리 (CORS)
    if http_method == 'OPTIONS':
        return APIResponse.cors_preflight()
    
    try:
        # Body 파싱 (Base64 디코딩 포함) - 모든 메서드 처리 전에 먼저 디코딩
        raw_body = event.get('body', '{}')
        if raw_body and event.get('isBase64Encoded'):
            raw_body = base64.b64decode(raw_body).decode('utf-8')
            logger.info("Decoded Base64 body")

        # Service 초기화
        conversation_service = ConversationService()
        
        # GET /conversations - 목록 조회
        if http_method == 'GET' and not path_params:
            # 쿼리 파라미터에서 userId와 engineType 추출
            query_params = event.get('queryStringParameters', {}) or {}
            engine_type = query_params.get('engineType') or query_params.get('engine')

            # 멀티테넌트: Authorizer에서 userId 가져오거나 쿼리 파라미터 사용
            if auth_user_id:
                # Authorizer가 있는 경우 (멀티테넌트)
                user_id = auth_user_id
                logger.info(f"Using userId from authorizer: {user_id}")
            else:
                # 기존 방식 (쿼리 파라미터)
                user_id = query_params.get('userId')
                logger.info(f"Using userId from query params: {user_id}")

            if not user_id:
                return APIResponse.error('userId is required', 400)
            
            # get_user_conversations 메서드 사용
            conversations = conversation_service.get_user_conversations(user_id, limit=1000)
            
            # engine_type으로 필터링이 필요한 경우
            if engine_type:
                conversations = [c for c in conversations if c.engine_type == engine_type]
            
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
            body = json.loads(raw_body)

            # 멀티테넌트: Authorizer에서 userId 가져오거나 body에서 사용
            if auth_user_id:
                # Authorizer가 있는 경우 (멀티테넌트)
                user_id = auth_user_id
                logger.info(f"Using userId from authorizer: {user_id}")
            else:
                # 기존 방식 (body에서)
                user_id = body.get('userId')
                logger.info(f"Using userId from body: {user_id}")

            conversation_id = body.get('conversationId')
            engine_type = body.get('engineType', 'C1')
            title = body.get('title')
            messages = body.get('messages', [])
            initial_message = messages[0].get('content') if messages else None

            if not user_id:
                return APIResponse.error('userId is required', 400)
            
            # conversationId가 있으면 기존 대화가 있는지 확인
            if conversation_id:
                existing = conversation_service.get_conversation(conversation_id)
                if existing:
                    # 기존 대화가 있으면 무시 (이미 저장됨)
                    logger.info(f"Conversation {conversation_id} already exists, skipping save")
                    return APIResponse.success({
                        'conversationId': conversation_id,
                        'userId': user_id,
                        'engineType': engine_type,
                        'title': existing.title if existing else title,
                        'message': 'Conversation already exists'
                    }, 200)
            
            # 새 대화 생성 (멀티테넌트 지원)
            saved = conversation_service.create_conversation(
                user_id=user_id,
                engine_type=engine_type,
                title=title,
                initial_message=initial_message,
                tenant_id=tenant_id  # 멀티테넌트 지원
            )
            
            # to_dict 메서드로 변환하여 반환
            return APIResponse.success(saved.to_dict(), 201)
        
        # PATCH/PUT /conversations/{conversationId} - 대화 부분 업데이트 (제목 수정 등)
        elif http_method in ['PATCH', 'PUT'] and 'conversationId' in path_params:
            body = json.loads(raw_body)
            conversation_id = path_params['conversationId']
            
            if 'title' in body:
                success = conversation_service.update_title(conversation_id, body['title'])
                if success:
                    return APIResponse.success({'message': 'Conversation updated'})
                else:
                    return APIResponse.error('Failed to update conversation', 500)
            else:
                return APIResponse.error('No title field to update', 400)
        
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