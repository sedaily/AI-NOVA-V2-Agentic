"""
WebSocket 연결 해제 핸들러
"""
import boto3
from src.config.database import get_table_name
from utils.logger import setup_logger
from utils.response import APIResponse

logger = setup_logger(__name__)
dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    """WebSocket 연결 해제 시 처리"""
    try:
        connection_id = event['requestContext']['connectionId']
        
        # 연결 정보 삭제
        table = dynamodb.Table(get_table_name('websocket_connections'))
        table.delete_item(
            Key={'connectionId': connection_id}
        )
        
        logger.info(f"WebSocket disconnected: {connection_id}")
        return APIResponse.success({'message': 'Disconnected'})
        
    except Exception as e:
        logger.error(f"Disconnect error: {str(e)}")
        return APIResponse.error(str(e), 500)