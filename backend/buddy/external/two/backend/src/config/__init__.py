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

from .aws import (
    BEDROCK_CONFIG,
    API_GATEWAY_CONFIG,
    LAMBDA_CONFIG,
    S3_CONFIG,
    CLOUDWATCH_CONFIG,
    COGNITO_CONFIG,
    GUARDRAIL_CONFIG
)

__all__ = [
    # Database
    'TABLES',
    'AWS_REGION',
    'DYNAMODB_CONFIG',
    'get_table_name',
    'get_table_config',
    # AWS Services
    'BEDROCK_CONFIG',
    'API_GATEWAY_CONFIG',
    'LAMBDA_CONFIG',
    'S3_CONFIG',
    'CLOUDWATCH_CONFIG',
    'COGNITO_CONFIG',
    'GUARDRAIL_CONFIG'
]