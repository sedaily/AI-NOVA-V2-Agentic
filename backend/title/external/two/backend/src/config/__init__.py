"""
설정 패키지
"""
from .database import (
    TABLES,
    AWS_REGION,
    DYNAMODB_CONFIG,
    get_table_name,
    get_table_config
)

__all__ = [
    'TABLES',
    'AWS_REGION',
    'DYNAMODB_CONFIG',
    'get_table_name',
    'get_table_config'
]
