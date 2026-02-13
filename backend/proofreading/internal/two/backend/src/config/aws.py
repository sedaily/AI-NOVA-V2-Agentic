"""
AWS 서비스 설정
"""
import os

# AWS 기본 설정
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
AWS_ACCOUNT_ID = os.environ.get('AWS_ACCOUNT_ID', '')

# DynamoDB 테이블 설정
DYNAMODB_TABLES = {
    'conversations': 'nx-wt-prf-conversations',
    'prompts': 'nx-wt-prf-prompts',
    'files': 'nx-wt-prf-files',
    'usage': 'nx-wt-prf-usage'
}

# Bedrock 설정 - Claude Opus 4.1 모델 설정
BEDROCK_CONFIG = {
    'region_name': AWS_REGION,
    'opus_model_id': 'us.anthropic.claude-opus-4-1-20250805-v1:0',
    'max_tokens': 16384,
    'temperature': 0.02,  # 프롬프트 준수 최적화 (매우 낮은 값)
    'top_p': 0.15,        # 일관성 있는 선택
    'top_k': 10,          # 정확한 선택지
    'anthropic_version': 'bedrock-2023-05-31'
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