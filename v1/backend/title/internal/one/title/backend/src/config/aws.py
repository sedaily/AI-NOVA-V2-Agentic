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
    'model_id': os.environ.get('BEDROCK_MODEL_ID', 'us.anthropic.claude-sonnet-4-20250514-v1:0'),
    'max_tokens': int(os.environ.get('BEDROCK_MAX_TOKENS', '16384')),
    'temperature': float(os.environ.get('BEDROCK_TEMPERATURE', '0.81')),
    'top_p': float(os.environ.get('BEDROCK_TOP_P', '0.9')),
    'top_k': int(os.environ.get('BEDROCK_TOP_K', '50'))
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

# S3 설정 (파일 업로드용)
S3_CONFIG = {
    'bucket': os.environ.get('S3_BUCKET', ''),
    'region': AWS_REGION,
    'max_file_size': int(os.environ.get('MAX_FILE_SIZE', '10485760'))  # 10MB
}

# CloudWatch 설정
CLOUDWATCH_CONFIG = {
    'namespace': os.environ.get('CLOUDWATCH_NAMESPACE', 'Nexus'),
    'log_group': os.environ.get('LOG_GROUP', '/aws/lambda/nexus'),
    'metrics_enabled': os.environ.get('METRICS_ENABLED', 'true').lower() == 'true'
}

# Cognito 설정
COGNITO_CONFIG = {
    'user_pool_id': os.environ.get('COGNITO_USER_POOL_ID', ''),
    'client_id': os.environ.get('COGNITO_CLIENT_ID', ''),
    'region': AWS_REGION
}

# 가드레일 설정
GUARDRAIL_CONFIG = {
    'identifier': os.environ.get('GUARDRAIL_ID', 'ycwjnmzxut7k'),
    'version': os.environ.get('GUARDRAIL_VERSION', '1'),
    'enabled': os.environ.get('GUARDRAIL_ENABLED', 'true').lower() == 'true'
}