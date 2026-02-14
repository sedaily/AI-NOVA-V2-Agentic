# Anthropic API Integration Guide for P2 Service

## 📌 개요

이 문서는 P2 서비스(b1.sedaily.ai)에서 AWS Bedrock과 Anthropic API를 병행 사용하는 방법을 설명합니다.

## 🏗️ 아키텍처

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Frontend  │────▶│  WebSocket   │────▶│  AI Provider    │
│ (React SPA) │     │   Handler    │     │    Selector     │
└─────────────┘     └──────────────┘     └─────────────────┘
                                                   │
                          ┌────────────────────────┴────────────────────────┐
                          │                                                  │
                    ┌─────▼─────┐                                    ┌──────▼──────┐
                    │ Anthropic │                                    │   Bedrock   │
                    │    API     │                                    │   Runtime   │
                    └───────────┘                                    └─────────────┘
                    Claude Opus 4.5                                  Claude Sonnet 3.5
```

## 🚀 빠른 시작

### 1. 기본 설정

```bash
# 설정 스크립트 실행
cd scripts
chmod +x configure-anthropic-api.sh
./configure-anthropic-api.sh
```

### 2. 수동 설정

#### Step 1: API 키 생성 및 저장

```bash
# Secrets Manager에 API 키 저장
aws secretsmanager create-secret \
    --name "anthropic-api-key" \
    --description "Anthropic API key for Claude" \
    --secret-string '{"api_key":"sk-ant-api03-..."}' \
    --region us-east-1
```

#### Step 2: Lambda 환경변수 설정

```bash
# 모든 Lambda 함수에 환경변수 추가
aws lambda update-function-configuration \
    --function-name p2-two-websocket-message \
    --environment Variables='{
        "AI_PROVIDER":"anthropic_api",
        "USE_ANTHROPIC_API":"true",
        "ANTHROPIC_SECRET_NAME":"anthropic-api-key",
        "ANTHROPIC_MODEL_ID":"claude-3-opus-20240229",
        "FALLBACK_TO_BEDROCK":"true"
    }' \
    --region us-east-1
```

#### Step 3: IAM 권한 추가

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": "arn:aws:secretsmanager:us-east-1:*:secret:anthropic-api-key*"
        }
    ]
}
```

## 🔧 구성 옵션

### 환경변수 설명

| 환경변수 | 설명 | 기본값 | 옵션 |
|---------|------|--------|------|
| `AI_PROVIDER` | AI 제공자 선택 | `bedrock` | `anthropic_api`, `bedrock` |
| `USE_ANTHROPIC_API` | Anthropic API 사용 여부 | `false` | `true`, `false` |
| `ANTHROPIC_SECRET_NAME` | API 키 시크릿 이름 | `anthropic-api-key` | 문자열 |
| `ANTHROPIC_MODEL_ID` | Anthropic 모델 ID | `claude-3-opus-20240229` | 모델 ID |
| `FALLBACK_TO_BEDROCK` | Bedrock 폴백 활성화 | `true` | `true`, `false` |
| `ANTHROPIC_FOR_INTERNAL` | 내부 사용자용 Anthropic | `false` | `true`, `false` |
| `ANTHROPIC_ENGINES` | Anthropic 사용 엔진 목록 | - | `C1,C2,H8` |

### 사용 모드

#### 1. Anthropic API 전용 모드
```bash
AI_PROVIDER=anthropic_api
USE_ANTHROPIC_API=true
FALLBACK_TO_BEDROCK=false
```
- 모든 요청을 Anthropic API로 처리
- Rate limit 발생 시 오류 반환
- 최고 품질, 높은 비용

#### 2. Bedrock 전용 모드
```bash
AI_PROVIDER=bedrock
USE_ANTHROPIC_API=false
FALLBACK_TO_BEDROCK=false
```
- 모든 요청을 AWS Bedrock으로 처리
- 안정적이고 빠른 응답
- 표준 품질, 낮은 비용

#### 3. Anthropic 우선 듀얼 모드
```bash
AI_PROVIDER=anthropic_api
USE_ANTHROPIC_API=true
FALLBACK_TO_BEDROCK=true
```
- Anthropic API 우선 사용
- Rate limit 시 Bedrock 자동 폴백
- 균형잡힌 품질과 안정성

#### 4. Bedrock 우선 듀얼 모드
```bash
AI_PROVIDER=bedrock
FALLBACK_TO_BEDROCK=true
ANTHROPIC_ENGINES=C1,C2
```
- Bedrock 기본 사용
- 특정 엔진만 Anthropic API 사용
- 비용 효율적

## 📊 비용 분석

### 모델별 가격 비교

| 제공자 | 모델 | 입력 토큰 | 출력 토큰 | 응답 속도 |
|--------|------|-----------|-----------|-----------|
| Anthropic API | Claude Opus 4.5 | $15/1M | $75/1M | 중간 |
| AWS Bedrock | Claude Sonnet 3.5 | $3/1M | $15/1M | 빠름 |

### 월간 예상 비용 (10만 요청 기준)

```
Anthropic API 전용: ~$500-800
Bedrock 전용: ~$100-200
듀얼 모드 (20/80): ~$200-300
```

## 🔍 모니터링

### CloudWatch 로그 확인

```bash
# WebSocket 핸들러 로그
aws logs tail /aws/lambda/p2-two-websocket-message --follow

# 특정 패턴 검색
aws logs filter-log-events \
    --log-group-name /aws/lambda/p2-two-websocket-message \
    --filter-pattern "AI Provider"
```

### 주요 로그 메시지

```
🎯 AI Provider: Anthropic API        # Anthropic 사용
🎯 AI Provider: AWS Bedrock         # Bedrock 사용
🔄 Falling back to Bedrock...       # 폴백 발생
✅ Rate limit recovered             # Rate limit 복구
```

## 🧪 테스트

### 로컬 테스트

```bash
# 테스트 스크립트 실행
python test-anthropic-api.py

# 환경만 체크
python test-anthropic-api.py --env-only

# 클라이언트만 테스트
python test-anthropic-api.py --client-only
```

### WebSocket 테스트

```javascript
// 브라우저 콘솔에서 테스트
const ws = new WebSocket('wss://dwc2m51as4.execute-api.us-east-1.amazonaws.com/prod');

ws.onopen = () => {
    ws.send(JSON.stringify({
        action: 'sendMessage',
        message: '안녕하세요',
        engineType: 'C1',
        userId: 'test@example.com'
    }));
};

ws.onmessage = (event) => {
    console.log('Response:', JSON.parse(event.data));
};
```

## 🚨 트러블슈팅

### 1. API 키 오류

**증상**: "API key not found" 오류

**해결**:
```bash
# 시크릿 확인
aws secretsmanager get-secret-value \
    --secret-id anthropic-api-key \
    --query SecretString \
    --output text | jq .

# 시크릿 업데이트
aws secretsmanager update-secret \
    --secret-id anthropic-api-key \
    --secret-string '{"api_key":"sk-ant-api03-NEW_KEY"}'
```

### 2. Rate Limit 오류

**증상**: 429 오류, "Rate limit exceeded"

**해결**:
- `FALLBACK_TO_BEDROCK=true` 설정 확인
- Rate limit 증가 요청 (Anthropic 콘솔)
- 요청 간격 조정

### 3. Import 오류

**증상**: "No module named 'anthropic_client'"

**해결**:
```bash
# Lambda 패키지 재배포
cd backend
./deploy-service.sh
```

### 4. 권한 오류

**증상**: "Access denied to secret"

**해결**:
```bash
# Lambda 역할에 정책 추가
aws iam attach-role-policy \
    --role-name p2-two-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite
```

## 📈 성능 최적화

### 1. 캐싱 전략

```python
# 프롬프트 캐싱 (5분)
CACHE_TTL = 300

# Anthropic API 자동 캐싱
# 동일한 system prompt는 자동으로 캐싱됨
```

### 2. Rate Limit 관리

```python
# 요청 간 최소 대기 시간
RATE_LIMIT_DELAY = 1.0  

# 재시도 전략
MAX_RETRIES = 3
RETRY_DELAY = 60  # 초
```

### 3. 토큰 최적화

- 불필요한 컨텍스트 제거
- 대화 히스토리 20개로 제한
- 시스템 프롬프트 최적화

## 🔄 롤백 절차

### Bedrock 전용 모드로 복원

```bash
# 환경변수를 Bedrock으로 변경
./scripts/configure-anthropic-api.sh
# 옵션 2 선택 (Bedrock only)
```

### 수동 롤백

```bash
aws lambda update-function-configuration \
    --function-name p2-two-websocket-message \
    --environment Variables='{
        "AI_PROVIDER":"bedrock",
        "USE_ANTHROPIC_API":"false"
    }'
```

## 📝 체크리스트

### 배포 전
- [ ] API 키 생성 및 Secrets Manager 저장
- [ ] IAM 권한 확인
- [ ] 환경변수 설정
- [ ] 로컬 테스트 완료

### 배포 후
- [ ] CloudWatch 로그 모니터링
- [ ] WebSocket 연결 테스트
- [ ] 응답 품질 확인
- [ ] Rate limit 모니터링
- [ ] 비용 추적 설정

## 🔗 참고 자료

- [Anthropic API Documentation](https://docs.anthropic.com)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock)
- [P2 Service Architecture](./PROJECT_STRUCTURE_ANALYSIS.md)
- [Deployment Guide](./DEPLOYMENT_GUIDE.md)

---

**마지막 업데이트**: 2024-11-30  
**작성자**: Backend Team  
**버전**: 1.0.0