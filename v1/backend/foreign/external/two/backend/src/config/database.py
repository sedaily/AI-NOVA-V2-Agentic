"""
데이터베이스 설정
"""
import os
from typing import Dict, Any

# DynamoDB 테이블 설정
TABLES = {
    'conversations': {
        'name': os.environ.get('CONVERSATIONS_TABLE', 'f1-conversations-two'),
        'partition_key': 'conversationId',
        'indexes': {
            'userId-createdAt-index': {
                'partition_key': 'userId',
                'sort_key': 'createdAt'
            }
        }
    },
    'prompts': {
        'name': os.environ.get('PROMPTS_TABLE', 'f1-prompts-two'),
        'partition_key': 'promptId',
        'indexes': {
            'userId-index': {
                'partition_key': 'userId',
                'sort_key': 'updatedAt'
            }
        }
    },
    'usage': {
        'name': os.environ.get('USAGE_TABLE', 'f1-usage-two'),
        'partition_key': 'userId',
        'sort_key': 'usageDate#engineType',
        'indexes': {
            'date-index': {
                'partition_key': 'usageDate',
                'sort_key': 'userId'
            }
        }
    },
    'websocket_connections': {
        'name': os.environ.get('WEBSOCKET_TABLE', 'f1-websocket-connections-two'),
        'partition_key': 'connectionId'
    },
    'files': {
        'name': os.environ.get('FILES_TABLE', 'f1-files-two'),
        'partition_key': 'promptId',
        'sort_key': 'fileId'
    }
}

# AWS 리전 설정
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# DynamoDB 설정
DYNAMODB_CONFIG = {
    'region_name': AWS_REGION,
    'max_retries': 3,
    'timeout': 10
}

def get_table_name(table_type: str) -> str:
    """테이블 이름 조회"""
    if table_type not in TABLES:
        raise ValueError(f"Unknown table type: {table_type}")
    return TABLES[table_type]['name']

def get_table_config(table_type: str) -> Dict[str, Any]:
    """테이블 설정 조회"""
    if table_type not in TABLES:
        raise ValueError(f"Unknown table type: {table_type}")
    return TABLES[table_type]