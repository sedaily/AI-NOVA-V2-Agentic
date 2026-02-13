"""
Prompt CRUD API Handler
프롬프트 관리 REST API 엔드포인트
"""
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List
import boto3
from boto3.dynamodb.conditions import Key

from utils.logger import setup_logger
from utils.response import APIResponse

logger = setup_logger(__name__)

# DynamoDB 테이블 초기화
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
prompts_table = dynamodb.Table('nx-tt-dev-ver3-prompts')
files_table = dynamodb.Table('nx-tt-dev-ver3-files')


def handler(event, context):
    """Lambda 핸들러 - 프롬프트 관리 API"""
    logger.info(f"Prompt API Event: {json.dumps(event)}")
    
    # API Gateway v2 형식 처리
    if 'version' in event and event['version'] == '2.0':
        # API Gateway v2 (HTTP API)
        http_method = event.get('requestContext', {}).get('http', {}).get('method')
        path = event.get('requestContext', {}).get('http', {}).get('path')
        path_params = event.get('pathParameters') or {}
    else:
        # API Gateway v1 (REST API) 또는 직접 호출
        http_method = event.get('httpMethod')
        path = event.get('path', '')
        path_params = event.get('pathParameters') or {}
    
    # OPTIONS 요청 처리 (CORS preflight)
    if http_method == 'OPTIONS':
        return APIResponse.cors_preflight()
    
    try:
        # 요청 본문 파싱
        body = {}
        if event.get('body'):
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
            logger.info(f"Request body: {body}")
        
        logger.info(f"Method: {http_method}, Path: {path}, PathParams: {path_params}")
        
        # path_params가 None인 경우 빈 딕셔너리로 처리
        if path_params is None:
            path_params = {}

        # 쿼리 파라미터 추출
        query_params = event.get('queryStringParameters', {}) or {}

        # 라우팅
        if '/prompts' in path:
            if '/files' in path:
                # 파일 관련 작업
                return handle_files(http_method, path_params, body, query_params)
            else:
                # 프롬프트 관련 작업
                return handle_prompts(http_method, path_params, body, query_params)
        
        return APIResponse.error('Not Found', 404)
        
    except Exception as e:
        logger.error(f"Error in handler: {str(e)}", exc_info=True)
        return APIResponse.error(str(e))


def handle_prompts(method: str, path_params: Dict, body: Dict, query_params: Dict = None) -> Dict:
    """프롬프트 (설명, 지침) CRUD 처리"""

    if query_params is None:
        query_params = {}

    # promptId와 engineType 둘 다 지원 (API Gateway 호환성)
    # path_params에서 먼저 찾고, 없으면 query_params에서 찾음
    engine_type = path_params.get('promptId') or path_params.get('engineType') or query_params.get('engineType')
    
    if method == 'GET':
        # 특정 엔진의 프롬프트 조회
        if engine_type:
            try:
                response = prompts_table.get_item(Key={'id': engine_type})
                item = response.get('Item', {})
                
                # 해당 엔진의 파일들도 함께 조회
                files_response = files_table.query(
                    KeyConditionExpression=Key('promptId').eq(engine_type)
                )
                files = files_response.get('Items', [])
                
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
    
    elif method == 'PUT':
        # 프롬프트 업데이트 (설명, 지침만)
        if not engine_type:
            return APIResponse.error('engineType is required', 400)
        
        try:
            update_expr = []
            expr_attr_values = {}
            
            if 'description' in body:
                update_expr.append('description = :desc')
                expr_attr_values[':desc'] = body['description']
            
            if 'instruction' in body:
                update_expr.append('instruction = :inst')
                expr_attr_values[':inst'] = body['instruction']
            
            if update_expr:
                update_expr.append('updatedAt = :updated')
                expr_attr_values[':updated'] = datetime.utcnow().isoformat() + 'Z'
                
                prompts_table.update_item(
                    Key={'id': engine_type},
                    UpdateExpression='SET ' + ', '.join(update_expr),
                    ExpressionAttributeValues=expr_attr_values
                )
            
            return APIResponse.success({'message': 'Prompt updated successfully'})
        except Exception as e:
            logger.error(f"Error updating prompt {engine_type}: {e}")
            return APIResponse.error(str(e))
    
    return APIResponse.error('Method not allowed', 405)


def handle_files(method: str, path_params: Dict, body: Dict, query_params: Dict = None) -> Dict:
    """파일 CRUD 처리"""

    if query_params is None:
        query_params = {}

    # promptId와 engineType 둘 다 지원 (API Gateway 호환성)
    # path_params에서 먼저 찾고, 없으면 query_params에서 찾음
    engine_type = path_params.get('promptId') or path_params.get('engineType') or query_params.get('engineType')
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