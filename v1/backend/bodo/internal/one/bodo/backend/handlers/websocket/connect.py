"""
WebSocket 연결 핸들러
"""
import json
import boto3
from datetime import datetime
from src.config.database import get_table_name
from utils.logger import get_logger
from utils.response import create_response

logger = get_logger(__name__)
dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    """WebSocket 연결 시 처리"""
    try:
        connection_id = event['requestContext']['connectionId']
        
        # 쿼리 파라미터에서 사용자 정보 추출
        query_params = event.get('queryStringParameters', {}) or {}
        user_id = query_params.get('userId', 'anonymous')
        engine_type = query_params.get('engineType', '11')
        
        # 연결 정보 저장
        table = dynamodb.Table(get_table_name('websocket_connections'))
        table.put_item(
            Item={
                'connectionId': connection_id,
                'userId': user_id,
                'engineType': engine_type,
                'connectedAt': datetime.utcnow().isoformat(),
                'ttl': int(datetime.utcnow().timestamp()) + 86400  # 24시간
            }
        )
        
        logger.info(f"WebSocket connected: {connection_id} for user {user_id}")
        return create_response(200, {'message': 'Connected'})
        
    except Exception as e:
        logger.error(f"Connection error: {str(e)}")
        return create_response(500, {'error': str(e)})