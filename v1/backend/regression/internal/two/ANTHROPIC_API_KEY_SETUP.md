# Anthropic API Key 설정 가이드

## 개요
AWS Secrets Manager를 사용하여 Anthropic API 키를 안전하게 관리합니다.
- **Secret Name**: `regression-v1`
- **Environment**: regression-v1
- **Secret ARN**: `arn:aws:secretsmanager:us-east-1:887078546492:secret:regression-v1-1mpNN1`

## 설정 단계

### 1. AWS Secrets Manager에 API 키 저장
```bash
cd backend/scripts
./setup-anthropic-api-key.sh
```

이 스크립트는:
- AWS Secrets Manager에 `regression-v1` 시크릿 생성
- API 키를 JSON 형식으로 저장: `{"api_key": "sk-ant-api03-..."}`
- 환경 태그 추가 (Environment: regression-v1, Service: sedaily-column)

### 2. Lambda 함수 환경변수 및 권한 업데이트
```bash
cd backend/scripts
./update-lambda-anthropic-key.sh
```

이 스크립트는:
- 모든 관련 Lambda 함수에 환경변수 추가
  - `ANTHROPIC_SECRET_NAME`: regression-v1
  - `ANTHROPIC_SECRET_ARN`: 시크릿 ARN
- Lambda 실행 역할에 Secrets Manager 읽기 권한 추가

### 3. 코드에서 API 키 사용

#### Python에서 사용 예시:
```python
from lib.anthropic_client import get_anthropic_client

# 클라이언트 초기화
client = get_anthropic_client()

# API 키 가져오기
api_key = client.get_api_key()

# API 헤더 가져오기
headers = client.get_headers()
```

#### 직접 Secrets Manager 접근:
```python
import boto3
import json

secrets_client = boto3.client('secretsmanager', region_name='us-east-1')
response = secrets_client.get_secret_value(SecretId='regression-v1')
secret = json.loads(response['SecretString'])
api_key = secret['api_key']
```

## 보안 고려사항

1. **API 키 하드코딩 금지**: 절대 코드에 API 키를 직접 입력하지 마세요
2. **IAM 권한 최소화**: Lambda 함수는 해당 시크릿에만 접근 가능하도록 설정
3. **정기적인 키 순환**: 주기적으로 API 키를 업데이트하세요
4. **접근 로깅**: CloudTrail을 통해 시크릿 접근 내역 모니터링

## 문제 해결

### API 키를 찾을 수 없는 경우
```bash
aws secretsmanager get-secret-value \
  --secret-id regression-v1 \
  --region us-east-1
```

### Lambda 함수 권한 확인
```bash
aws lambda get-function-configuration \
  --function-name sedaily-column-conversation \
  --region us-east-1 \
  --query 'Environment.Variables'
```

### 수동으로 API 키 업데이트
```bash
aws secretsmanager update-secret \
  --secret-id regression-v1 \
  --secret-string '{"api_key":"new-api-key-here"}' \
  --region us-east-1
```

## 관련 파일
- `/backend/scripts/setup-anthropic-api-key.sh` - Secrets Manager 설정
- `/backend/scripts/update-lambda-anthropic-key.sh` - Lambda 함수 업데이트
- `/backend/lib/anthropic_client.py` - Anthropic API 클라이언트

## 주의사항
⚠️ **중요**: 제공된 API 키는 예시입니다. 실제 운영 환경에서는 반드시 유효한 API 키를 사용하세요.