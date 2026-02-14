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

# ========================================
# 통합 크레딧 시스템 테이블 (2026-01-01)
# ========================================
credits_table = dynamodb.Table('nexus-unified-credits')
transactions_table = dynamodb.Table('nexus-credit-transactions')

# 서비스 식별자
SERVICE_ID = 'title'
SERVICE_NAME = '제목'

# 기본 크레딧 상수
DEFAULT_INITIAL_CREDIT = Decimal('50000')  # 50,000 NC = 50,000원


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


def update_usage(user_id, engine_type, input_text, output_text, user_plan='free',
                 model_id=None, input_tokens=None, output_tokens=None, credits_used=None):
    """
    사용량 업데이트 (크레딧 시스템 지원)

    Args:
        user_id: 사용자 ID
        engine_type: 엔진 타입 (T5, H8 등)
        input_text: 입력 텍스트 (토큰 추정용, input_tokens가 없을 때 사용)
        output_text: 출력 텍스트 (토큰 추정용, output_tokens가 없을 때 사용)
        user_plan: 사용자 플랜 (free, basic, premium)
        model_id: Claude 모델 ID (크레딧 계산용)
        input_tokens: 실제 입력 토큰 수 (API 응답에서 가져온 값)
        output_tokens: 실제 출력 토큰 수 (API 응답에서 가져온 값)
        credits_used: 미리 계산된 크레딧 (없으면 자동 계산)
    """
    try:
        # 토큰 계산 (실제 값이 없으면 추정)
        if input_tokens is None:
            input_tokens = estimate_tokens(input_text)
        if output_tokens is None:
            output_tokens = estimate_tokens(output_text)
        total_tokens = input_tokens + output_tokens

        # 크레딧 계산 (미리 계산된 값이 없으면 계산)
        if credits_used is None and model_id:
            from lib.anthropic_client import calculate_credits
            credit_info = calculate_credits(
                {'input_tokens': input_tokens, 'output_tokens': output_tokens},
                model_id
            )
            credits_used = credit_info['total_credits']
        elif credits_used is None:
            credits_used = 0

        year_month = datetime.now(timezone.utc).strftime('%Y-%m')
        pk = f"user#{user_id}"
        sk = f"engine#{engine_type}#{year_month}"

        # 먼저 레코드 확인/생성
        get_or_create_usage(user_id, engine_type)

        # 업데이트 (크레딧 필드 추가)
        response = usage_table.update_item(
            Key={'PK': pk, 'SK': sk},
            UpdateExpression="""
                ADD totalTokens :total,
                    inputTokens :input,
                    outputTokens :output,
                    messageCount :one,
                    creditsUsed :credits
                SET updatedAt = :timestamp,
                    lastUsedAt = :timestamp,
                    lastModelId = :model_id
            """,
            ExpressionAttributeValues={
                ':total': Decimal(str(total_tokens)),
                ':input': Decimal(str(input_tokens)),
                ':output': Decimal(str(output_tokens)),
                ':one': Decimal('1'),
                ':credits': Decimal(str(round(credits_used, 2))),
                ':timestamp': datetime.now(timezone.utc).isoformat(),
                ':model_id': model_id or 'claude-opus-4-5-20251101'
            },
            ReturnValues='ALL_NEW'
        )

        updated_item = decimal_to_float(response['Attributes'])

        # 플랜별 월간 크레딧 한도 설정 (NC 기준)
        plan_limits = {
            'free': 10000,      # 10,000 NC = 10,000원
            'basic': 100000,    # 100,000 NC = 100,000원
            'premium': 500000   # 500,000 NC = 500,000원
        }

        monthly_limit = plan_limits.get(user_plan, 10000)
        total_credits_used = updated_item.get('creditsUsed', 0)
        percentage = min(100, (total_credits_used / monthly_limit) * 100)

        return {
            'success': True,
            'usage': updated_item,
            'tokensUsed': total_tokens,
            'creditsUsed': round(credits_used, 2),
            'totalCreditsUsed': round(total_credits_used, 2),
            'percentage': round(percentage, 1),
            'remaining': max(0, monthly_limit - total_credits_used),
            'modelId': model_id or 'claude-opus-4-5-20251101'
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


# ============================================================
# 크레딧 잔액 관련 함수
# ============================================================

def get_user_credits(user_id):
    """
    사용자 크레딧 잔액 조회 (통합 크레딧 테이블)
    - 없으면 자동으로 50,000 NC 생성 + 트랜잭션 기록
    """
    try:
        response = credits_table.get_item(
            Key={'userId': user_id}
        )

        if 'Item' in response:
            item = decimal_to_float(response['Item'])
            logger.info(f"💳 크레딧 조회 성공: {user_id} - 잔액: {item.get('balance', 0)} NC")
            return item

        # 없으면 새로 생성 (50,000 NC) - 통합 테이블 스키마
        now = datetime.now(timezone.utc).isoformat()
        new_item = {
            'userId': user_id,
            'balance': DEFAULT_INITIAL_CREDIT,
            'totalUsed': Decimal('0'),
            'totalCharged': DEFAULT_INITIAL_CREDIT,
            'plan': 'free',
            'createdAt': now,
            'updatedAt': now
        }

        credits_table.put_item(Item=new_item)
        logger.info(f"💳 새 사용자 크레딧 생성: {user_id} - 50,000 NC")

        # 초기 지급 트랜잭션 기록
        _record_transaction(
            user_id=user_id,
            tx_type='charge',
            amount=float(DEFAULT_INITIAL_CREDIT),
            service_id='system',
            service_name='시스템',
            description='신규 사용자 초기 크레딧 지급'
        )

        return decimal_to_float(new_item)

    except ClientError as e:
        logger.error(f"크레딧 조회 실패: {e}")
        return None


def _record_transaction(user_id, tx_type, amount, service_id, service_name,
                        model_id=None, input_tokens=0, output_tokens=0, description=None):
    """
    트랜잭션 기록 (통합 트랜잭션 테이블)

    Args:
        user_id: 사용자 ID
        tx_type: 트랜잭션 타입 (usage, charge, refund, adjustment)
        amount: 금액 (usage는 음수, charge는 양수)
        service_id: 서비스 ID
        service_name: 서비스 이름
        model_id: AI 모델 ID (usage 시)
        input_tokens: 입력 토큰 수
        output_tokens: 출력 토큰 수
        description: 설명
    """
    try:
        import uuid
        now = datetime.now(timezone.utc).isoformat()

        transaction_item = {
            'transactionId': str(uuid.uuid4()),
            'userId': user_id,
            'type': tx_type,
            'amount': Decimal(str(round(amount, 2))),
            'serviceId': service_id,
            'serviceName': service_name,
            'createdAt': now
        }

        if model_id:
            transaction_item['modelId'] = model_id
        if input_tokens > 0:
            transaction_item['inputTokens'] = input_tokens
        if output_tokens > 0:
            transaction_item['outputTokens'] = output_tokens
        if description:
            transaction_item['description'] = description

        transactions_table.put_item(Item=transaction_item)
        logger.info(f"📝 트랜잭션 기록: {tx_type} {amount} NC for {user_id} ({service_id})")

    except Exception as e:
        logger.error(f"트랜잭션 기록 실패: {e}")


def deduct_credits(user_id, amount, model_id=None, input_tokens=0, output_tokens=0):
    """
    사용자 크레딧 차감 (통합 크레딧 시스템)

    Args:
        user_id: 사용자 ID
        amount: 차감할 크레딧 (NC)
        model_id: 사용된 모델 ID
        input_tokens: 입력 토큰 수
        output_tokens: 출력 토큰 수

    Returns:
        업데이트된 크레딧 정보 또는 None
    """
    try:
        # 먼저 현재 잔액 확인 (없으면 생성)
        current = get_user_credits(user_id)
        if not current:
            logger.error(f"크레딧 차감 실패: 사용자를 찾을 수 없음 - {user_id}")
            return None

        current_balance = Decimal(str(current.get('balance', 0)))
        deduct_amount = Decimal(str(round(amount, 2)))

        # 잔액 부족 체크
        if current_balance < deduct_amount:
            logger.warning(f"⚠️ 잔액 부족: {user_id} - 현재: {current_balance} NC, 필요: {deduct_amount} NC")
            # 잔액 부족해도 일단 0까지 차감 (나중에 정책 변경 가능)
            deduct_amount = current_balance

        # 크레딧 차감 (통합 테이블 스키마)
        response = credits_table.update_item(
            Key={'userId': user_id},
            UpdateExpression="""
                SET balance = balance - :amount,
                    totalUsed = if_not_exists(totalUsed, :zero) + :amount,
                    updatedAt = :timestamp
            """,
            ExpressionAttributeValues={
                ':amount': deduct_amount,
                ':zero': Decimal('0'),
                ':timestamp': datetime.now(timezone.utc).isoformat()
            },
            ReturnValues='ALL_NEW'
        )

        updated_item = decimal_to_float(response['Attributes'])
        logger.info(f"💳 크레딧 차감 완료: {user_id} - {float(deduct_amount)} NC 차감, 잔액: {updated_item.get('balance', 0)} NC")

        # 트랜잭션 기록 (usage - 음수로 기록)
        _record_transaction(
            user_id=user_id,
            tx_type='usage',
            amount=-float(deduct_amount),  # 사용은 음수
            service_id=SERVICE_ID,
            service_name=SERVICE_NAME,
            model_id=model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            description=f'{SERVICE_NAME} 서비스 사용'
        )

        return updated_item

    except ClientError as e:
        logger.error(f"크레딧 차감 실패: {e}")
        return None


def add_credits(user_id, amount, reason="충전"):
    """
    사용자 크레딧 추가 (충전) - 통합 크레딧 시스템

    Args:
        user_id: 사용자 ID
        amount: 추가할 크레딧 (NC)
        reason: 충전 사유

    Returns:
        업데이트된 크레딧 정보 또는 None
    """
    try:
        # 먼저 현재 잔액 확인 (없으면 생성)
        current = get_user_credits(user_id)
        if not current:
            logger.error(f"크레딧 추가 실패: 사용자를 찾을 수 없음 - {user_id}")
            return None

        add_amount = Decimal(str(round(amount, 2)))

        # 크레딧 추가 (통합 테이블 스키마)
        response = credits_table.update_item(
            Key={'userId': user_id},
            UpdateExpression="""
                SET balance = balance + :amount,
                    totalCharged = if_not_exists(totalCharged, :zero) + :amount,
                    updatedAt = :timestamp
            """,
            ExpressionAttributeValues={
                ':amount': add_amount,
                ':zero': Decimal('0'),
                ':timestamp': datetime.now(timezone.utc).isoformat()
            },
            ReturnValues='ALL_NEW'
        )

        updated_item = decimal_to_float(response['Attributes'])
        logger.info(f"💳 크레딧 충전 완료: {user_id} - {float(add_amount)} NC 추가, 잔액: {updated_item.get('balance', 0)} NC")

        # 트랜잭션 기록 (charge - 양수로 기록)
        _record_transaction(
            user_id=user_id,
            tx_type='charge',
            amount=float(add_amount),  # 충전은 양수
            service_id='system',
            service_name='시스템',
            description=reason
        )

        return updated_item

    except ClientError as e:
        logger.error(f"크레딧 추가 실패: {e}")
        return None


# ============================================================
# 기존 사용량 추적 함수
# ============================================================

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


def credits_handler(event, context):
    """
    크레딧 잔액 API Lambda 핸들러

    Routes:
        GET /credits/{userId} - 크레딧 잔액 조회
        POST /credits/deduct - 크레딧 차감
        POST /credits/add - 크레딧 추가 (충전)
    """
    try:
        logger.info(f"Credits API Event: {json.dumps(event)}")

        # API Gateway v2 형식 처리
        if 'version' in event and event['version'] == '2.0':
            http_method = event.get('requestContext', {}).get('http', {}).get('method')
            path_params = event.get('pathParameters', {})
            raw_path = event.get('rawPath', '')
        else:
            http_method = event.get('httpMethod')
            path_params = event.get('pathParameters', {})
            raw_path = event.get('path', '')

        # OPTIONS 요청 처리 (CORS preflight)
        if http_method == 'OPTIONS':
            return APIResponse.cors_preflight()

        body = event.get('body')

        # GET /credits/{userId} - 잔액 조회
        if http_method == 'GET':
            user_id = path_params.get('userId')

            if user_id:
                user_id = unquote(user_id)

            if not user_id:
                return APIResponse.error('userId 필수', 400)

            data = get_user_credits(user_id)
            if data:
                return APIResponse.success({
                    'success': True,
                    'userId': user_id,
                    'balance': data.get('balance', 0),
                    'initialCredit': data.get('initialCredit', 50000),
                    'totalUsed': data.get('totalUsed', 0),
                    'createdAt': data.get('createdAt'),
                    'updatedAt': data.get('updatedAt')
                })
            else:
                return APIResponse.error('크레딧 조회 실패', 500)

        # POST /credits/deduct - 크레딧 차감
        elif http_method == 'POST' and ('deduct' in raw_path):
            if not body:
                return APIResponse.error('Request body 필수', 400)

            data = json.loads(body) if isinstance(body, str) else body
            user_id = data.get('userId')
            amount = data.get('amount', 0)
            model_id = data.get('modelId')
            input_tokens = data.get('inputTokens', 0)
            output_tokens = data.get('outputTokens', 0)

            if not user_id:
                return APIResponse.error('userId 필수', 400)

            if amount <= 0:
                return APIResponse.error('amount는 0보다 커야 함', 400)

            result = deduct_credits(user_id, amount, model_id, input_tokens, output_tokens)
            if result:
                return APIResponse.success({
                    'success': True,
                    'userId': user_id,
                    'deducted': amount,
                    'balance': result.get('balance', 0),
                    'totalUsed': result.get('totalUsed', 0)
                })
            else:
                return APIResponse.error('크레딧 차감 실패', 500)

        # POST /credits/add - 크레딧 추가 (충전)
        elif http_method == 'POST' and ('add' in raw_path):
            if not body:
                return APIResponse.error('Request body 필수', 400)

            data = json.loads(body) if isinstance(body, str) else body
            user_id = data.get('userId')
            amount = data.get('amount', 0)
            reason = data.get('reason', '충전')

            if not user_id:
                return APIResponse.error('userId 필수', 400)

            if amount <= 0:
                return APIResponse.error('amount는 0보다 커야 함', 400)

            result = add_credits(user_id, amount, reason)
            if result:
                return APIResponse.success({
                    'success': True,
                    'userId': user_id,
                    'added': amount,
                    'balance': result.get('balance', 0),
                    'reason': reason
                })
            else:
                return APIResponse.error('크레딧 추가 실패', 500)

        else:
            return APIResponse.error('지원하지 않는 HTTP 메서드 또는 경로', 405)

    except Exception as e:
        logger.error(f"Credits API 핸들러 오류: {e}", exc_info=True)
        return APIResponse.error('서버 내부 오류', 500)


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