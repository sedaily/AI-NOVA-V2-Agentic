# Claude 4.5 Opus API 마이그레이션 가이드

## 📋 개요
이 문서는 P2 서비스를 AWS Bedrock에서 Claude 4.5 Opus Direct API로 전환하는 과정을 설명합니다.

---

## 🔐 1. AWS Secrets Manager 설정

### 1.1 API 키 저장
```bash
# buddy-v1 이름으로 API 키 저장 (us-east-1 리전)
aws secretsmanager create-secret \
  --name "buddy-v1" \
  --description "Anthropic API key for Buddy v1 service" \
  --secret-string '{"api_key":"YOUR_ANTHROPIC_API_KEY"}' \
  --region us-east-1
```

### 1.2 Lambda IAM 권한 추가
```bash
# Lambda 역할에 Secrets Manager 접근 권한 부여
cat > /tmp/secret-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret"
            ],
            "Resource": [
                "arn:aws:secretsmanager:us-east-1:887078546492:secret:buddy-v1*"
            ]
        }
    ]
}
EOF

aws iam put-role-policy \
    --role-name "p2-two-lambda-role-two" \
    --policy-name "SecretsManagerAccess" \
    --policy-document file:///tmp/secret-policy.json \
    --region us-east-1
```

---

## 🔧 2. Lambda 환경변수 업데이트

### 2.1 모든 Lambda 함수 환경변수 일괄 업데이트
```bash
#!/bin/bash
# update-lambda-env.sh

FUNCTIONS=(
    "p2-two-websocket-message-two"
    "p2-two-conversation-api-two"
    "p2-two-prompt-crud-two"
    "p2-two-websocket-connect-two"
    "p2-two-websocket-disconnect-two"
    "p2-two-usage-handler-two"
)

# Claude 4.5 Opus 모델 ID
OPUS_45_MODEL="claude-opus-4-5-20251101"

for func in "${FUNCTIONS[@]}"; do
    echo "Updating $func..."
    
    # 현재 환경변수 가져오기
    aws lambda get-function-configuration \
        --function-name "$func" \
        --region us-east-1 \
        --query "Environment" \
        --output json > /tmp/env-$func.json
    
    # Claude 4.5 Opus 설정 추가
    jq '.Variables += {
        "ANTHROPIC_MODEL_ID": "'$OPUS_45_MODEL'",
        "USE_OPUS_MODEL": "true",
        "ANTHROPIC_SECRET_NAME": "buddy-v1",
        "USE_ANTHROPIC_API": "true",
        "AI_PROVIDER": "anthropic_api"
    }' /tmp/env-$func.json > /tmp/env-updated-$func.json
    
    # 환경변수 적용
    aws lambda update-function-configuration \
        --function-name "$func" \
        --region us-east-1 \
        --environment file:///tmp/env-updated-$func.json \
        --output text > /dev/null
    
    echo "✅ $func updated"
    sleep 2
done
```

---

## 📝 3. 코드 수정 사항

### 3.1 anthropic_client.py 주요 변경사항

#### 모델 설정
```python
# Claude 4.5 Opus 모델 ID
OPUS_MODEL = os.environ.get('ANTHROPIC_MODEL_ID', 'claude-opus-4-5-20251101')
```

#### API 호출 파라미터 (중요!)
```python
# Claude 4.5 Opus는 temperature와 top_p를 동시에 사용할 수 없음
body = {
    "model": self.model_id,
    "max_tokens": MAX_TOKENS,
    "temperature": TEMPERATURE,  # temperature만 사용 (top_p 제거)
    "messages": messages,
    "system": system,
    "stream": stream
}

# top_k는 선택적으로 추가
if TOP_K > 0:
    body["top_k"] = TOP_K
```

#### Secret Manager 통합
```python
def _get_api_key(self) -> str:
    """AWS Secrets Manager에서 API 키 가져오기"""
    secret_name = os.environ.get('ANTHROPIC_SECRET_NAME', 'buddy-v1')
    response = secrets_client.get_secret_value(SecretId=secret_name)
    secret = json.loads(response['SecretString'])
    api_key = secret.get('api_key')
    return api_key
```

---

## 🚀 4. Lambda 코드 배포

### 4.1 배포 패키지 생성 및 배포
```bash
#!/bin/bash
# deploy-lambda-code.sh

cd /path/to/backend

# 배포 패키지 생성
echo "Creating deployment package..."
rm -f lambda-deployment.zip
zip -r lambda-deployment.zip . \
  -x "*.pyc" \
  -x "*__pycache__*" \
  -x "*.zip" \
  -x ".env*" \
  -x "backup_*/*" \
  -x "package/*" \
  -x "aws-setup/*" \
  -x "test_*.py"

# Lambda 함수 업데이트
FUNCTIONS=(
    "p2-two-websocket-message-two"
    "p2-two-conversation-api-two"
    "p2-two-prompt-crud-two"
    "p2-two-websocket-connect-two"
    "p2-two-websocket-disconnect-two"
    "p2-two-usage-handler-two"
)

for func in "${FUNCTIONS[@]}"; do
    echo "Deploying to $func..."
    
    aws lambda update-function-code \
        --function-name "$func" \
        --zip-file fileb://lambda-deployment.zip \
        --region us-east-1 \
        --output json > /dev/null
    
    echo "✅ $func deployed"
    sleep 2
done

echo "✨ Deployment complete!"
```

---

## 🔍 5. 로그 확인 및 디버깅

### 5.1 CloudWatch 로그 확인
```bash
# 최근 로그 스트림 확인
aws logs describe-log-streams \
    --log-group-name /aws/lambda/p2-two-websocket-message-two \
    --region us-east-1 \
    --order-by LastEventTime \
    --descending \
    --limit 1

# Anthropic API 관련 로그 검색
aws logs filter-log-events \
    --log-group-name /aws/lambda/p2-two-websocket-message-two \
    --region us-east-1 \
    --start-time $(($(date +%s) - 3600))000 \
    --filter-pattern "Anthropic OR buddy OR API key OR Secret"
```

### 5.2 환경변수 확인
```bash
# Lambda 환경변수 확인
aws lambda get-function-configuration \
    --function-name "p2-two-websocket-message-two" \
    --region us-east-1 \
    --query "Environment.Variables.[ANTHROPIC_MODEL_ID,USE_OPUS_MODEL,ANTHROPIC_SECRET_NAME,USE_ANTHROPIC_API]" \
    --output json
```

---

## ⚠️ 주의사항

1. **API 파라미터 제한**
   - Claude 4.5 Opus는 `temperature`와 `top_p`를 동시에 사용할 수 없음
   - `temperature`만 사용하거나 `top_p`만 사용해야 함

2. **모델 ID**
   - 정확한 모델 ID 사용: `claude-opus-4-5-20251101`
   - 구버전 (`claude-3-opus-20240229`) 사용 금지

3. **리전 일치**
   - Lambda와 Secrets Manager는 같은 리전 사용 권장
   - 현재 설정: us-east-1

4. **IAM 권한**
   - Lambda 역할에 Secrets Manager 읽기 권한 필수
   - 정책 이름: `SecretsManagerAccess`

---

## 📊 환경변수 전체 목록

| 변수명 | 값 | 설명 |
|--------|-----|------|
| `ANTHROPIC_MODEL_ID` | `claude-opus-4-5-20251101` | Claude 4.5 Opus 모델 ID |
| `USE_OPUS_MODEL` | `true` | Opus 모델 사용 여부 |
| `ANTHROPIC_SECRET_NAME` | `buddy-v1` | Secrets Manager 시크릿 이름 |
| `USE_ANTHROPIC_API` | `true` | Anthropic API 사용 여부 |
| `AI_PROVIDER` | `anthropic_api` | AI 제공자 선택 |
| `MAX_TOKENS` | `4096` | 최대 토큰 수 |
| `TEMPERATURE` | `0.3` | 창의성 수준 (0-1) |
| `TOP_K` | `40` | Top-K 샘플링 값 |

---

## 🧪 테스트 방법

1. **웹 애플리케이션에서 테스트**
   - 채팅 메시지 전송
   - 응답 확인

2. **Claude Console 확인**
   - https://console.anthropic.com 접속
   - API 호출 로그 확인
   - 모델명이 `claude-opus-4-5-20251101`인지 확인

3. **CloudWatch 로그 확인**
   - 오류 메시지 확인
   - API 호출 성공 여부 확인

---

## 📞 문의사항

문제 발생 시 다음 정보와 함께 문의:
- Lambda 함수 이름
- CloudWatch 로그
- 오류 메시지 전문
- 발생 시각

---

마지막 업데이트: 2024-12-02