# CloudWatch Logs 조회 가이드

## 1. AWS CLI로 로그 조회

### 최근 30분 로그 실시간 보기
```bash
aws logs tail /aws/lambda/p2-two-websocket-message-two \
  --region us-east-1 \
  --since 30m \
  --follow
```

### 특정 시간대 로그 조회
```bash
aws logs tail /aws/lambda/p2-two-websocket-message-two \
  --region us-east-1 \
  --since 2025-11-21T07:00:00 \
  --until 2025-11-21T08:00:00
```

### 특정 키워드로 필터링
```bash
aws logs tail /aws/lambda/p2-two-websocket-message-two \
  --region us-east-1 \
  --since 1h \
  --filter-pattern "사용자 질문"
```

### 사용자별 대화 조회
```bash
aws logs tail /aws/lambda/p2-two-websocket-message-two \
  --region us-east-1 \
  --since 24h \
  --filter-pattern "user: b498b418-b0e1-70bc-3ab3-fd70cd0f7921"
```

### 에러 로그만 조회
```bash
aws logs tail /aws/lambda/p2-two-websocket-message-two \
  --region us-east-1 \
  --since 1h \
  --filter-pattern "ERROR"
```

## 2. AWS Console에서 조회

### 로그 그룹 접근
1. AWS Console → CloudWatch → Logs → Log groups
2. `/aws/lambda/p2-two-websocket-message-two` 선택

### Insights 쿼리로 대화 분석

#### 사용자별 대화 횟수
```
fields @timestamp, @message
| filter @message like /Processing message for/
| parse @message /user: (?<userId>[a-f0-9-]+)/
| stats count() by userId
| sort count desc
```

#### 엔진별 사용 통계
```
fields @timestamp, @message
| filter @message like /Processing message for (\d+)/
| parse @message /Processing message for (?<engine>\d+)/
| stats count() by engine
```

#### 평균 응답 시간
```
fields @timestamp, @message, @duration
| filter @message like /Streaming completed/
| stats avg(@duration) as avg_duration_ms,
        max(@duration) as max_duration_ms,
        min(@duration) as min_duration_ms
```

#### 캐시 히트율
```
fields @timestamp, @message
| filter @message like /Cache metrics/
| parse @message /read: (?<cache_read>\d+), write: (?<cache_write>\d+)/
| stats sum(cache_read) as total_cache_read,
        sum(cache_write) as total_cache_write,
        count() as total_requests
```

#### 웹 검색 사용 통계
```
fields @timestamp, @message
| filter @message like /Web search ENABLED/
| parse @message /Searching for: (?<query>.+)/
| stats count() by query
| sort count desc
| limit 20
```

#### 에러 분석
```
fields @timestamp, @message
| filter @message like /ERROR/ or @message like /Error/
| parse @message /(?<error_type>ValidationException|TimeoutError|ConnectionError)/
| stats count() by error_type
```

## 3. 로그 그룹별 용도

### 대화 처리
- `/aws/lambda/p2-two-websocket-message-two` - 실시간 대화, AI 응답
- `/aws/lambda/p2-two-conversation-api-two` - 대화 기록 조회

### 프롬프트 관리
- `/aws/lambda/p2-two-prompt-crud-two` - 프롬프트 CRUD

### 사용량 추적
- `/aws/lambda/p2-two-usage-handler-two` - 토큰 사용량, 비용

### 연결 관리
- `/aws/lambda/p2-two-websocket-connect-two` - WebSocket 연결
- `/aws/lambda/p2-two-websocket-disconnect-two` - 연결 종료

## 4. 로그에서 추출 가능한 정보

### 사용자 정보
- 사용자 ID
- 역할 (admin/user)
- 세션 ID

### 대화 정보
- 대화 ID
- 엔진 타입
- 사용자 질문
- AI 응답 (일부)
- 대화 컨텍스트 길이

### 성능 메트릭
- 프롬프트 캐싱 히트/미스
- 토큰 사용량 (입력/출력/캐시)
- 응답 시간
- 웹 검색 시간

### 비용 최적화
- 캐시 절감 토큰
- 캐시 재사용률
- 엔진별 토큰 사용량

## 5. 로그 보존 정책

현재 설정 확인:
```bash
aws logs describe-log-groups \
  --region us-east-1 \
  --log-group-name-prefix "/aws/lambda/p2-two" \
  --query 'logGroups[].[logGroupName,retentionInDays]' \
  --output table
```

보존 기간 설정 (예: 30일):
```bash
aws logs put-retention-policy \
  --region us-east-1 \
  --log-group-name /aws/lambda/p2-two-websocket-message-two \
  --retention-in-days 30
```

## 6. 대화 기록 내보내기

### JSON 형식으로 내보내기
```bash
aws logs filter-log-events \
  --region us-east-1 \
  --log-group-name /aws/lambda/p2-two-websocket-message-two \
  --start-time $(date -u -d '1 day ago' +%s)000 \
  --filter-pattern "Processing message" \
  --output json > conversations_export.json
```

### CSV 형식으로 변환
```bash
aws logs filter-log-events \
  --region us-east-1 \
  --log-group-name /aws/lambda/p2-two-websocket-message-two \
  --start-time $(date -u -d '1 day ago' +%s)000 \
  --filter-pattern "Processing message" \
  --query 'events[].[timestamp,message]' \
  --output text > conversations_export.csv
```

## 7. 실시간 모니터링

### 대시보드 생성
CloudWatch Console → Dashboards → Create dashboard

추천 위젯:
1. **요청 수** (Line graph) - Lambda invocations
2. **에러율** (Number) - Error count / Total requests
3. **평균 응답 시간** (Line graph) - Duration metric
4. **캐시 히트율** (Number) - Cache read / (read + write)
5. **토큰 사용량** (Stacked area) - Input + Output tokens

### 알람 설정
```bash
# 에러율이 5% 이상일 때 알람
aws cloudwatch put-metric-alarm \
  --alarm-name p2-two-high-error-rate \
  --alarm-description "High error rate in p2-two" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=p2-two-websocket-message-two
```

## 8. 주요 로그 패턴

### 정상 대화 처리
```
Processing message for {engine}, user: {userId}, role: {role}
Processed message for conversation {conversationId}
Merged history length: {messageCount}
✅ Cache HIT for {engine}
Streaming response for engine {engine}
📊 Cache metrics - read: {tokens}, write: {tokens}, input: {tokens}
Streaming completed
```

### 에러 발생
```
[오류] AI 응답 생성 실패: {error_message}
Error in streaming: {error_details}
ValidationException: {validation_error}
```

### 웹 검색 사용
```
🔍 Web search ENABLED - Searching for: {query}
✅ Web search completed: {chars} chars
```

## 9. 비용 관리

### 로그 스토리지 비용 확인
```bash
aws cloudwatch get-metric-statistics \
  --region us-east-1 \
  --namespace AWS/Logs \
  --metric-name IncomingBytes \
  --dimensions Name=LogGroupName,Value=/aws/lambda/p2-two-websocket-message-two \
  --start-time $(date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Sum
```

### 로그 레벨 조정 (production 환경)
`.env` 파일에서:
```bash
LOG_LEVEL=WARNING  # INFO 대신 WARNING 사용
```

## 10. 보안 및 규정 준수

### 민감 정보 마스킹
로그에 다음 정보가 포함되지 않도록 주의:
- 사용자 개인정보
- 인증 토큰
- API 키
- 전체 대화 내용 (요약만)

### 감사 로그
관리자 작업 추적:
```
fields @timestamp, @message
| filter @message like /role: admin/
| sort @timestamp desc
```

## 참고
- CloudWatch Logs 요금: https://aws.amazon.com/cloudwatch/pricing/
- Log Insights 쿼리 문법: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax.html
