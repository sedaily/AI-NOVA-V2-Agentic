"""
Prompt CRUD API Handler
프롬프트 관리 REST API 엔드포인트
"""
import json
import base64
import uuid
from datetime import datetime
from typing import Dict, Any, List
import os
import boto3
from boto3.dynamodb.conditions import Key

from utils.logger import setup_logger
from utils.response import APIResponse

logger = setup_logger(__name__)

# DynamoDB 테이블 초기화
logger = setup_logger(__name__)
logger.info("Initializing DynamoDB resources...")

try:
    dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
    prompts_table_name = os.environ.get('PROMPTS_TABLE', 'sedaily-column-prompts')
    files_table_name = os.environ.get('FILES_TABLE', 'sedaily-column-files')

    logger.info(f"Using prompts table: {prompts_table_name}")
    logger.info(f"Using files table: {files_table_name}")

    prompts_table = dynamodb.Table(prompts_table_name)
    files_table = dynamodb.Table(files_table_name)

    logger.info("DynamoDB tables initialized successfully")
except Exception as e:
    logger.error(f"Error initializing DynamoDB: {str(e)}", exc_info=True)


def handler(event, context):
    """Lambda 핸들러 - 프롬프트 관리 API
    멀티테넌트 지원 (하위 호환성 유지)
    """
    # 최소한의 로깅으로 변경 (OPTIONS 요청 시 오버헤드 감소)
    http_method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method')
    
    # OPTIONS 요청을 가장 먼저 처리 (빠른 응답)
    if http_method == 'OPTIONS':
        logger.info("OPTIONS request received - returning CORS headers")
        return APIResponse.cors_preflight()
    
    # OPTIONS가 아닌 경우만 상세 로깅
    logger.info(f"Prompt API Event: {json.dumps(event)}")

    # API Gateway v2 형식 처리
    if 'version' in event and event['version'] == '2.0':
        # API Gateway v2 (HTTP API)
        http_method = event.get('requestContext', {}).get('http', {}).get('method')
        path = event.get('requestContext', {}).get('http', {}).get('path')
        path_params = event.get('pathParameters', {})
    else:
        # API Gateway v1 (REST API) 또는 직접 호출
        http_method = event.get('httpMethod')
        path = event.get('path', '')
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
    
    try:
        # 요청 본문 파싱 (안전하게 처리 + Base64 디코딩)
        body = {}
        if event.get('body'):
            try:
                body_str = event['body']
                
                # Base64 인코딩된 경우 처리
                if event.get('isBase64Encoded'):
                    body_str = base64.b64decode(body_str).decode('utf-8')
                    logger.info(f"Decoded Base64 body")
                
                # JSON 파싱
                if isinstance(body_str, str) and body_str.strip():
                    body = json.loads(body_str)
                elif isinstance(body_str, dict):
                    body = body_str
                    
                logger.info(f"Request body parsed successfully")
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Failed to parse body: {e}, using empty body")
                body = {}
        
        logger.info(f"Method: {http_method}, Path: {path}, PathParams: {path_params}")
        
        # 라우팅 (멀티테넌트 정보 전달)
        if '/prompts' in path:
            if '/files' in path:
                # 파일 관련 작업
                return handle_files(http_method, path_params, body, tenant_id, user_role)
            else:
                # 프롬프트 관련 작업
                return handle_prompts(http_method, path_params, body, tenant_id, user_role)
        
        return APIResponse.error('Not Found', 404)
        
    except Exception as e:
        logger.error(f"Error in handler: {str(e)}", exc_info=True)
        return APIResponse.error(str(e))


def handle_prompts(method: str, path_params: Dict, body: Dict, tenant_id: str = 'sedaily', user_role: str = 'user') -> Dict:
    """프롬프트 (설명, 지침) CRUD 처리 - 멀티테넌트 지원"""

    # promptId와 engineType 둘 다 지원 (API Gateway 호환성)
    path_params = path_params or {}
    engine_type = path_params.get('promptId') or path_params.get('engineType')
    logger.info(f"handle_prompts called - method: {method}, engine_type: {engine_type}, tenant: {tenant_id}, role: {user_role}")

    if method == 'GET':
        # 특정 엔진의 프롬프트 조회
        if engine_type:
            try:
                response = prompts_table.get_item(Key={'promptId': engine_type})
                item = response.get('Item', {})
                
                # 해당 엔진의 파일들도 함께 조회
                try:
                    files_response = files_table.query(
                        KeyConditionExpression=Key('promptId').eq(engine_type)
                    )
                    files = files_response.get('Items', [])
                except Exception as e:
                    logger.warning(f"Error getting files for {engine_type}: {e}")
                    files = []
                
                return APIResponse.success({
                    'prompt': item,
                    'files': files
                })
            except Exception as e:
                logger.error(f"Error getting prompt {engine_type}: {e}")
                return APIResponse.error(str(e))
        else:
            # 모든 프롬프트 조회
            try:
                response = prompts_table.scan()
                return APIResponse.success({'prompts': response.get('Items', [])})
            except Exception as e:
                logger.error(f"Error scanning prompts: {e}")
                return APIResponse.error(str(e))
    
    elif method == 'POST':
        # 프롬프트 생성 또는 업데이트
        if not engine_type:
            return APIResponse.error('engineType is required', 400)

        try:
            # Upsert (없으면 생성, 있으면 업데이트)
            item = {
                'promptId': engine_type,
                'description': body.get('description', ''),
                'instruction': body.get('instruction', ''),
                'createdAt': datetime.utcnow().isoformat() + 'Z',
                'updatedAt': datetime.utcnow().isoformat() + 'Z'
            }
            prompts_table.put_item(Item=item)
            return APIResponse.success({'message': 'Prompt created/updated successfully', 'promptId': engine_type})
        except Exception as e:
            logger.error(f"Error creating prompt {engine_type}: {e}")
            return APIResponse.error(str(e))

    elif method == 'PUT':
        # 프롬프트 업데이트 (설명, 지침만)
        if not engine_type:
            return APIResponse.error('engineType is required', 400)
        
        try:
            logger.info(f"Updating prompt {engine_type} with body: {body}")

            update_expr = []
            expr_attr_values = {}

            if 'description' in body:
                update_expr.append('description = :desc')
                expr_attr_values[':desc'] = body['description']
                logger.info(f"Adding description update: {body['description'][:100]}...")

            if 'instruction' in body:
                update_expr.append('instruction = :inst')
                expr_attr_values[':inst'] = body['instruction']
                logger.info(f"Adding instruction update: {body['instruction'][:100]}...")

            if update_expr:
                update_expr.append('updatedAt = :updated')
                expr_attr_values[':updated'] = datetime.utcnow().isoformat() + 'Z'

                logger.info(f"Update expression: SET {', '.join(update_expr)}")
                logger.info(f"Expression attribute values: {list(expr_attr_values.keys())}")

# 임시 우회: PUT_ITEM 사용
                logger.info(f"Attempting PutItem as workaround for {engine_type}")

                # 기존 아이템 가져오기
                existing_response = prompts_table.get_item(Key={'promptId': engine_type})
                existing_item = existing_response.get('Item', {})
                logger.info(f"Existing item: {existing_item.keys()}")

                # 전체 아이템 재작성
                updated_item = existing_item.copy()
                if 'description' in body:
                    updated_item['description'] = body['description']
                if 'instruction' in body:
                    updated_item['instruction'] = body['instruction']
                updated_item['updatedAt'] = datetime.utcnow().isoformat() + 'Z'
                updated_item['promptId'] = engine_type  # 키 확실히 보장

                logger.info(f"Putting updated item: {list(updated_item.keys())}")
                prompts_table.put_item(Item=updated_item)
                logger.info(f"Update successful for {engine_type}")

            return APIResponse.success({'message': 'Prompt updated successfully'})
        except Exception as e:
            logger.error(f"Error updating prompt {engine_type}: {e}", exc_info=True)
            return APIResponse.error(str(e))
    
    return APIResponse.error('Method not allowed', 405)


def handle_files(method: str, path_params: Dict, body: Dict, tenant_id: str = 'sedaily', user_role: str = 'user') -> Dict:
    """파일 CRUD 처리"""

    # promptId와 engineType 둘 다 지원 (API Gateway 호환성)
    path_params = path_params or {}
    engine_type = path_params.get('promptId') or path_params.get('engineType')
    file_id = path_params.get('fileId')
    
    if method == 'GET':
        # 특정 엔진의 파일 목록 조회
        if engine_type:
            try:
                response = files_table.query(
                    KeyConditionExpression=Key('promptId').eq(engine_type)
                )
                return APIResponse.success({'files': response.get('Items', [])})
            except Exception as e:
                logger.error(f"Error getting files for {engine_type}: {e}")
                return APIResponse.error(str(e))
    
    elif method == 'POST':
        # 새 파일 추가
        if not engine_type:
            return APIResponse.error('engineType is required', 400)
        
        try:
            new_file_id = str(uuid.uuid4())
            item = {
                'promptId': engine_type,
                'fileId': new_file_id,
                'fileName': body.get('fileName', 'untitled.txt'),
                'fileContent': body.get('fileContent', ''),
                'createdAt': datetime.utcnow().isoformat() + 'Z'
            }
            
            files_table.put_item(Item=item)
            
            return APIResponse.success({'file': item}, 201)
        except Exception as e:
            logger.error(f"Error creating file for {engine_type}: {e}")
            return APIResponse.error(str(e))
    
    elif method == 'PUT':
        # 파일 수정
        if not engine_type or not file_id:
            return APIResponse.error('engineType and fileId are required', 400)
        
        try:
            update_expr = []
            expr_attr_values = {}
            
            if 'fileName' in body:
                update_expr.append('fileName = :name')
                expr_attr_values[':name'] = body['fileName']
            
            if 'fileContent' in body:
                update_expr.append('fileContent = :content')
                expr_attr_values[':content'] = body['fileContent']
            
            if update_expr:
                update_expr.append('updatedAt = :updated')
                expr_attr_values[':updated'] = datetime.utcnow().isoformat() + 'Z'
                
                files_table.update_item(
                    Key={'promptId': engine_type, 'fileId': file_id},
                    UpdateExpression='SET ' + ', '.join(update_expr),
                    ExpressionAttributeValues=expr_attr_values
                )
            
            return APIResponse.success({'message': 'File updated successfully'})
        except Exception as e:
            logger.error(f"Error updating file {file_id} for {engine_type}: {e}")
            return APIResponse.error(str(e))
    
    elif method == 'DELETE':
        # 파일 삭제
        if not engine_type or not file_id:
            return APIResponse.error('engineType and fileId are required', 400)
        
        try:
            files_table.delete_item(
                Key={'promptId': engine_type, 'fileId': file_id}
            )
            
            return APIResponse.success({'message': 'File deleted successfully'})
        except Exception as e:
            logger.error(f"Error deleting file {file_id} for {engine_type}: {e}")
            return APIResponse.error(str(e))
    
    return APIResponse.error('Method not allowed', 405)