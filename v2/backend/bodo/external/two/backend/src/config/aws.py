"""
AWS 서비스 설정
"""
import os

# AWS 기본 설정
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
AWS_ACCOUNT_ID = os.environ.get('AWS_ACCOUNT_ID', '')

# Bedrock 설정
BEDROCK_CONFIG = {
    'region_name': AWS_REGION,
    'model_id': os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-opus-4-6-v1:0'),
    'opus_model_id': os.environ.get('BEDROCK_OPUS_MODEL_ID', 'anthropic.claude-opus-4-6-v1:0'),
    'max_tokens': int(os.environ.get('BEDROCK_MAX_TOKENS', '16384')),
    'temperature': float(os.environ.get('BEDROCK_TEMPERATURE', '0.81')),
    # 'top_p': float(os.environ.get('BEDROCK_TOP_P', '0.9')),  # ❌ Claude Sonnet 4는 temperature와 함께 사용 불가
    'top_k': int(os.environ.get('BEDROCK_TOP_K', '50')),
    'anthropic_version': os.environ.get('ANTHROPIC_VERSION', 'bedrock-2023-05-31')
}

# API Gateway 설정
API_GATEWAY_CONFIG = {
    'rest_api_url': os.environ.get('REST_API_URL', ''),
    'websocket_api_url': os.environ.get('WEBSOCKET_API_URL', ''),
    'stage': os.environ.get('API_STAGE', 'prod')
}

# Lambda 설정
LAMBDA_CONFIG = {
    'timeout': int(os.environ.get('LAMBDA_TIMEOUT', '30')),
    'memory': int(os.environ.get('LAMBDA_MEMORY', '512')),
    'log_level': os.environ.get('LOG_LEVEL', 'INFO')
}

# DynamoDB 테이블 설정
DYNAMODB_TABLES = {
    'conversations': os.environ.get('CONVERSATIONS_TABLE', 'w1-conversations-v2'),
    'prompts': os.environ.get('PROMPTS_TABLE', 'w1-prompts-v2'),
    'files': os.environ.get('FILES_TABLE', 'w1-files'),
    'usage': os.environ.get('USAGE_TABLE', 'w1-usage'),
    'connections': os.environ.get('CONNECTIONS_TABLE', 'w1-websocket-connections')
}

# 엔진 타입 설정
ENGINE_CONFIG = {
    'default': os.environ.get('DEFAULT_ENGINE_TYPE', '11'),
    'secondary': os.environ.get('SECONDARY_ENGINE_TYPE', '22'),
    'available': os.environ.get('AVAILABLE_ENGINES', '11,22,33').split(',')
}