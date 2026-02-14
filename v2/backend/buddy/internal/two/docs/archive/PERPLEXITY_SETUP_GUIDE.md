# Perplexity API 설정 가이드

## 개요

이 프로젝트는 Perplexity API를 사용하여 실시간 웹 검색 기능을 제공합니다. 사용자가 질문하면 Perplexity로 최신 정보를 검색하고, 그 결과를 Claude AI와 함께 활용하여 더 정확한 답변을 생성합니다.

## 1. Perplexity API 키 발급

1. [Perplexity API 콘솔](https://www.perplexity.ai/settings/api)에 접속
2. API 키 생성 (`pplx-` 로 시작하는 키)
3. 키를 안전한 곳에 보관

## 2. 환경변수 설정

### 로컬 개발 환경

```bash
# backend/.env 파일에 추가
PERPLEXITY_API_KEY=pplx-your-actual-api-key-here
```

### AWS Lambda 배포

다음 중 하나의 방법을 선택하세요:

#### 방법 1: 자동 스크립트 사용 (권장)

```bash
# Perplexity API 키를 모든 Lambda 함수에 자동 설정
./scripts/update-perplexity-env.sh w1 us-east-1 pplx-your-api-key-here
```

#### 방법 2: 배포 스크립트 수정

```bash
# 환경변수 설정 후 배포
export PERPLEXITY_API_KEY=pplx-your-api-key-here
./scripts/13-update-lambda-env-enhanced.sh
```

#### 방법 3: AWS CLI 직접 사용

```bash
# 특정 Lambda 함수에만 설정
aws lambda update-function-configuration \
    --function-name w1-websocket-message \
    --environment Variables='{"PERPLEXITY_API_KEY":"pplx-your-api-key-here","CONVERSATIONS_TABLE":"w1-conversations-v2",...}' \
    --region us-east-1
```

## 3. 설정 확인

### Lambda 환경변수 확인

```bash
aws lambda get-function-configuration \
    --function-name w1-websocket-message \
    --region us-east-1 \
    --query 'Environment.Variables.PERPLEXITY_API_KEY'
```

### CloudWatch 로그 확인

```bash
# Perplexity 검색 로그 실시간 모니터링
aws logs tail /aws/lambda/w1-websocket-message --follow
```

로그에서 다음과 같은 메시지를 확인할 수 있습니다:

```
PerplexityClient initialized with API key: Yes
🔍 Web search ENABLED - Searching for: 사용자 질문...
✅ Perplexity search success - Result length: 1234 chars
```

## 4. 기능 테스트

### 프론트엔드에서 테스트

1. 웹 애플리케이션 접속
2. 최신 정보가 필요한 질문 입력 (예: "오늘 주요 뉴스는?")
3. AI 응답에 최신 웹 검색 결과가 포함되는지 확인

### API 직접 테스트

```bash
# WebSocket 연결 테스트
wscat -c wss://your-websocket-api-id.execute-api.us-east-1.amazonaws.com/prod

# 메시지 전송
{"action":"sendMessage","message":"최신 AI 뉴스 알려줘","conversationId":"test123"}
```

## 5. 문제 해결

### API 키가 설정되지 않은 경우

```
PerplexityClient initialized with API key: No
🔍 Web search DISABLED - Skipping Perplexity search
```

→ 환경변수 `PERPLEXITY_API_KEY`가 설정되지 않음

### API 호출 실패

```
❌ Perplexity API error: 401
Response content: {"error":"Invalid API key"}
```

→ API 키가 잘못되었거나 만료됨

### 네트워크 오류

```
Error calling Perplexity API: Connection timeout
```

→ Lambda 함수의 VPC 설정이나 인터넷 게이트웨이 확인

## 6. 비용 관리

### Perplexity API 사용량 모니터링

- [Perplexity 대시보드](https://www.perplexity.ai/settings/api)에서 사용량 확인
- 월 사용 한도 설정 권장

### Lambda 비용 최적화

- 웹 검색이 필요하지 않은 경우 `ENABLE_NEWS_SEARCH=false` 설정
- CloudWatch 로그 보존 기간 조정 (현재 30일)

## 7. 보안 고려사항

### API 키 보안

- API 키를 코드에 하드코딩하지 말 것
- AWS Systems Manager Parameter Store 사용 고려
- 정기적인 API 키 로테이션

### 접근 제어

- Lambda 함수의 IAM 역할 최소 권한 원칙 적용
- VPC 내부에서만 접근 가능하도록 설정 고려

## 8. 모니터링 및 알림

### CloudWatch 메트릭

- Perplexity API 호출 횟수
- 응답 시간
- 오류율

### 알림 설정

```bash
# Perplexity API 오류 알림 설정
aws cloudwatch put-metric-alarm \
    --alarm-name "PerplexityAPIErrors" \
    --alarm-description "Perplexity API 오류 발생" \
    --metric-name "Errors" \
    --namespace "AWS/Lambda" \
    --statistic "Sum" \
    --period 300 \
    --threshold 5 \
    --comparison-operator "GreaterThanThreshold"
```

## 9. 업데이트 및 유지보수

### API 키 업데이트

```bash
# 새로운 API 키로 일괄 업데이트
./scripts/update-perplexity-env.sh w1 us-east-1 pplx-new-api-key-here
```

### 기능 비활성화

```bash
# 웹 검색 기능 임시 비활성화
aws lambda update-function-configuration \
    --function-name w1-websocket-message \
    --environment Variables='{"ENABLE_NEWS_SEARCH":"false",...}' \
    --region us-east-1
```

---

## 요약

1. **API 키 발급**: Perplexity 콘솔에서 API 키 생성
2. **환경변수 설정**: `./scripts/update-perplexity-env.sh` 스크립트 실행
3. **설정 확인**: CloudWatch 로그에서 "API key: Yes" 메시지 확인
4. **기능 테스트**: 프론트엔드에서 최신 정보 질문으로 테스트
5. **모니터링**: 사용량과 비용 정기 확인

이제 Perplexity API가 제대로 설정되어 AI 응답에 실시간 웹 검색 결과가 포함됩니다!
