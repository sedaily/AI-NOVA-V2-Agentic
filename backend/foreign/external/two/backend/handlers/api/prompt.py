"""
Prompt CRUD API Handler
프롬프트 관리 REST API 엔드포인트
"""
import json
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
    prompts_table_name = os.environ.get('PROMPTS_TABLE', 'f1-prompts-two')
    files_table_name = os.environ.get('FILES_TABLE', 'f1-files-two')

    logger.info(f"Using prompts table: {prompts_table_name}")
    logger.info(f"Using files table: {files_table_name}")

    prompts_table = dynamodb.Table(prompts_table_name)
    files_table = dynamodb.Table(files_table_name)

    logger.info("DynamoDB tables initialized successfully")
except Exception as e:
    logger.error(f"Error initializing DynamoDB: {str(e)}", exc_info=True)


def handler(event, context):
    """Lambda 핸들러 - 프롬프트 관리 API"""
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
        
        # 라우팅
        if '/prompts' in path:
            if '/files' in path:
                # 파일 관련 작업
                return handle_files(http_method, path_params, body)
            else:
                # 프롬프트 관련 작업
                return handle_prompts(http_method, path_params, body)
        
        return APIResponse.error('Not Found', 404)
        
    except Exception as e:
        logger.error(f"Error in handler: {str(e)}", exc_info=True)
        return APIResponse.error(str(e))


def handle_prompts(method: str, path_params: Dict, body: Dict) -> Dict:
    """프롬프트 (설명, 지침) CRUD 처리"""

    # promptId와 engineType 둘 다 지원 (API Gateway 호환성)
    engine_type = path_params.get('promptId') or path_params.get('engineType')
    logger.info(f"handle_prompts called - method: {method}, engine_type: {engine_type}")

    if method == 'GET':
        # 특정 엔진의 프롬프트 조회
        if engine_type:
            try:
                # DynamoDB 복합 키 사용: engineType (HASH) + promptId (RANGE)
                response = prompts_table.get_item(Key={'engineType': engine_type, 'promptId': engine_type})
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
                items = response.get('Items', [])
                # 중복 제거 (engineType과 promptId가 같은 경우)
                unique_prompts = {item.get('engineType', item.get('promptId')): item for item in items}
                return APIResponse.success({'prompts': list(unique_prompts.values())})
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
                'engineType': engine_type,  # HASH key
                'promptId': engine_type,     # RANGE key
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

                # 기존 아이템 가져오기 (복합 키 사용)
                existing_response = prompts_table.get_item(Key={'engineType': engine_type, 'promptId': engine_type})
                existing_item = existing_response.get('Item', {})
                logger.info(f"Existing item: {existing_item.keys()}")

                # 전체 아이템 재작성
                updated_item = existing_item.copy()
                if 'description' in body:
                    updated_item['description'] = body['description']
                if 'instruction' in body:
                    updated_item['instruction'] = body['instruction']
                updated_item['updatedAt'] = datetime.utcnow().isoformat() + 'Z'
                updated_item['engineType'] = engine_type  # HASH 키
                updated_item['promptId'] = engine_type     # RANGE 키

                logger.info(f"Putting updated item: {list(updated_item.keys())}")
                prompts_table.put_item(Item=updated_item)
                logger.info(f"Update successful for {engine_type}")

            return APIResponse.success({'message': 'Prompt updated successfully'})
        except Exception as e:
            logger.error(f"Error updating prompt {engine_type}: {e}", exc_info=True)
            return APIResponse.error(str(e))
    
    return APIResponse.error('Method not allowed', 405)


def handle_files(method: str, path_params: Dict, body: Dict) -> Dict:
    """파일 CRUD 처리"""
    
    # promptId와 engineType 둘 다 지원 (API Gateway 호환성)
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