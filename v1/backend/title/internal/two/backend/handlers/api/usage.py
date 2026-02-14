"""
Usage API Handler
사용량 추적 REST API 엔드포인트
"""

import json
import boto3
from datetime import datetime, timezone
from decimal import Decimal
import logging
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
import os
from urllib.parse import unquote

from utils.logger import setup_logger
from utils.response import APIResponse

# 로깅 설정
logger = setup_logger(__name__)

# DynamoDB 초기화
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
usage_table = dynamodb.Table('nx-tt-dev-ver3-usage-tracking')


def decimal_to_float(obj):
    """DynamoDB Decimal을 float로 변환"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(v) for v in obj]
    return obj


def estimate_tokens(text):
    """토큰 추정 (한글/영어 구분)"""
    if not text:
        return 0
    
    # 문자 타입별 카운트
    korean_chars = 0
    english_chars = 0
    numbers = 0
    spaces = 0
    
    for char in text:
        if '가' <= char <= '힣':
            korean_chars += 1
        elif char.isalpha() and char.isascii():
            english_chars += 1
        elif char.isdigit():
            numbers += 1
        elif char.isspace():
            spaces += 1
    
    # 나머지 특수문자
    special_chars = len(text) - korean_chars - english_chars - numbers - spaces
    
    # 토큰 계산 (경험적 수치)
    # Claude 기준 근사치
    korean_tokens = korean_chars / 2.5  # 한글 2.5자당 1토큰
    english_tokens = english_chars / 4  # 영어 4자당 1토큰  
    number_tokens = numbers / 3.5       # 숫자 3.5자당 1토큰
    space_tokens = spaces / 4           # 공백 4개당 1토큰
    special_tokens = special_chars / 3  # 특수문자 3자당 1토큰
    
    total_tokens = (korean_tokens + english_tokens + 
                   number_tokens + space_tokens + special_tokens)
    
    return max(1, int(total_tokens))


def get_or_create_usage(user_id, engine_type):
    """사용량 조회 또는 생성"""
    year_month = datetime.now(timezone.utc).strftime('%Y-%m')
    pk = f"user#{user_id}"
    sk = f"engine#{engine_type}#{year_month}"
    
    try:
        # 먼저 조회
        response = usage_table.get_item(
            Key={'PK': pk, 'SK': sk}
        )
        
        if 'Item' in response:
            return response['Item']
        
        # 없으면 새로 생성
        new_item = {
            'PK': pk,
            'SK': sk,
            'userId': user_id,
            'engineType': engine_type,
            'yearMonth': year_month,
            'totalTokens': Decimal('0'),
            'inputTokens': Decimal('0'),
            'outputTokens': Decimal('0'),
            'messageCount': Decimal('0'),
            'createdAt': datetime.now(timezone.utc).isoformat(),
            'updatedAt': datetime.now(timezone.utc).isoformat()
        }
        
        usage_table.put_item(Item=new_item)
        return new_item
        
    except ClientError as e:
        logger.error(f"Error getting/creating usage: {e}")
        raise


def update_usage(user_id, engine_type, input_text, output_text, user_plan='free'):
    """사용량 업데이트 (간단 버전)"""
    try:
        # 토큰 계산
        input_tokens = estimate_tokens(input_text)
        output_tokens = estimate_tokens(output_text)
        total_tokens = input_tokens + output_tokens
        
        year_month = datetime.now(timezone.utc).strftime('%Y-%m')
        pk = f"user#{user_id}"
        sk = f"engine#{engine_type}#{year_month}"
        
        # 먼저 레코드 확인/생성
        get_or_create_usage(user_id, engine_type)
        
        # 간단한 업데이트 (ADD 사용으로 원자적 증가)
        response = usage_table.update_item(
            Key={'PK': pk, 'SK': sk},
            UpdateExpression="""
                ADD totalTokens :total,
                    inputTokens :input,
                    outputTokens :output,
                    messageCount :one
                SET updatedAt = :timestamp,
                    lastUsedAt = :timestamp
            """,
            ExpressionAttributeValues={
                ':total': Decimal(str(total_tokens)),
                ':input': Decimal(str(input_tokens)),
                ':output': Decimal(str(output_tokens)),
                ':one': Decimal('1'),
                ':timestamp': datetime.now(timezone.utc).isoformat()
            },
            ReturnValues='ALL_NEW'
        )
        
        updated_item = decimal_to_float(response['Attributes'])
        
        # 플랜별 월간 한도 설정
        plan_limits = {
            'free': 10000,
            'basic': 100000,
            'premium': 500000
        }
        
        monthly_limit = plan_limits.get(user_plan, 10000)
        percentage = min(100, (updated_item['totalTokens'] / monthly_limit) * 100)
        
        return {
            'success': True,
            'usage': updated_item,
            'tokensUsed': total_tokens,
            'percentage': round(percentage, 1),
            'remaining': max(0, monthly_limit - updated_item['totalTokens'])
        }
        
    except ClientError as e:
        logger.error(f"사용량 업데이트 실패: {e}")
        return {'success': False, 'error': str(e)}


def get_usage(user_id, engine_type):
    """사용량 조회"""
    try:
        year_month = datetime.now(timezone.utc).strftime('%Y-%m')
        pk = f"user#{user_id}"
        sk = f"engine#{engine_type}#{year_month}"
        
        response = usage_table.get_item(
            Key={'PK': pk, 'SK': sk}
        )
        
        if 'Item' in response:
            return decimal_to_float(response['Item'])
        
        # 없으면 기본값 반환
        return {
            'userId': user_id,
            'engineType': engine_type,
            'yearMonth': year_month,
            'totalTokens': 0,
            'inputTokens': 0,
            'outputTokens': 0,
            'messageCount': 0
        }
        
    except ClientError as e:
        logger.error(f"사용량 조회 실패: {e}")
        return None


def get_all_usage(user_id):
    """모든 엔진의 사용량 조회"""
    try:
        pk = f"user#{user_id}"
        
        # Key 조건 사용 (GPT 피드백 반영)
        response = usage_table.query(
            KeyConditionExpression=Key('PK').eq(pk)
        )
        
        items = [decimal_to_float(item) for item in response.get('Items', [])]
        
        # 엔진별로 정리
        usage_by_engine = {}
        for item in items:
            engine_type = item.get('engineType', 'unknown')
            year_month = item.get('yearMonth', '')
            
            if engine_type not in usage_by_engine:
                usage_by_engine[engine_type] = []
            
            usage_by_engine[engine_type].append(item)
        
        # 각 엔진별로 월별 정렬
        for engine in usage_by_engine:
            usage_by_engine[engine].sort(key=lambda x: x.get('yearMonth', ''), reverse=True)
        
        return usage_by_engine
        
    except ClientError as e:
        logger.error(f"전체 사용량 조회 실패: {e}")
        return {}


def handler(event, context):
    """Lambda 메인 핸들러"""
    try:
        logger.info(f"Usage API Event: {json.dumps(event)}")
        
        # API Gateway v2 형식 처리
        if 'version' in event and event['version'] == '2.0':
            # API Gateway v2 (HTTP API)
            http_method = event.get('requestContext', {}).get('http', {}).get('method')
            path_params = event.get('pathParameters', {})
        else:
            # API Gateway v1 (REST API) 또는 직접 호출
            http_method = event.get('httpMethod')
            path_params = event.get('pathParameters', {})
        
        # OPTIONS 요청 처리 (CORS preflight)
        if http_method == 'OPTIONS':
            return APIResponse.cors_preflight()
        
        body = event.get('body')
        
        if http_method == 'GET':
            user_id = path_params.get('userId')
            engine_type_or_all = path_params.get('engineType')
            
            # URL 디코딩 처리 (이메일의 @ 등)
            if user_id:
                user_id = unquote(user_id)
            
            if not user_id:
                return APIResponse.error('userId 필수', 400)
            
            if engine_type_or_all == 'all':
                # 전체 사용량 조회
                data = get_all_usage(user_id)
                return APIResponse.success({'success': True, 'data': data})
            else:
                # 특정 엔진 사용량 조회
                data = get_usage(user_id, engine_type_or_all)
                return APIResponse.success({'success': True, 'data': data})
        
        elif http_method == 'POST':
            if not body:
                return APIResponse.error('Request body 필수', 400)
            
            data = json.loads(body) if isinstance(body, str) else body
            user_id = data.get('userId')
            engine_type = data.get('engineType')
            input_text = data.get('inputText', '')
            output_text = data.get('outputText', '')
            user_plan = data.get('userPlan', 'free')  # 플랜 정보 추가
            
            if not all([user_id, engine_type]):
                return APIResponse.error('userId, engineType 필수', 400)
            
            result = update_usage(user_id, engine_type, input_text, output_text, user_plan)
            
            return APIResponse.success(result)
        
        else:
            return APIResponse.error('지원하지 않는 HTTP 메서드', 405)
            
    except Exception as e:
        logger.error(f"Lambda 핸들러 오류: {e}", exc_info=True)
        return APIResponse.error('서버 내부 오류', 500)