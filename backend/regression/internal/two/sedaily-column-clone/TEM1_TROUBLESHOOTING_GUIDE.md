# TEM1 프로젝트 트러블슈팅 가이드

## 프로젝트 개요
TEM1은 SEDAILY 칼럼 서비스의 클론 프로젝트로, AWS 기반 서버리스 아키텍처를 사용하여 AI 칼럼 생성 서비스를 제공합니다.

## 발생한 주요 문제와 해결 방법

### 1. 대화 저장 실패 문제
**증상**:
- 사용자 질문은 저장되나 AI 응답이 저장되지 않음
- POST /conversations 엔드포인트에서 500 Internal Server Error 발생

**원인**:
- DynamoDB 테이블 스키마 불일치
- GSI(Global Secondary Index) 누락
- Lambda 함수에서 AI 응답 저장 로직 누락

**해결책**:
```bash
# 1. DynamoDB 테이블 스키마 수정
# tem1-conversations-v2 테이블에 userId-createdAt-index GSI 추가
aws dynamodb update-table \
    --table-name tem1-conversations-v2 \
    --attribute-definitions \
        AttributeName=userId,AttributeType=S \
        AttributeName=createdAt,AttributeType=S \
    --global-secondary-index-updates \
        '[{
            "Create": {
                "IndexName": "userId-createdAt-index",
                "KeySchema": [
                    {"AttributeName": "userId", "KeyType": "HASH"},
                    {"AttributeName": "createdAt", "KeyType": "RANGE"}
                ],
                "Projection": {"ProjectionType": "ALL"}
            }
        }]'

# 2. message.py에 AI 응답 저장 로직 추가
# handlers/websocket/message.py 파일에서 스트리밍 완료 후 저장 코드 추가
```

### 2. CORS 정책 오류
**증상**:
```
Access to fetch at 'https://8u7vben959.execute-api.us-east-1.amazonaws.com/prod/prompts/11'
from origin 'https://d2kglkjg8iharz.cloudfront.net' has been blocked by CORS policy
```

**원인**:
- API Gateway에 OPTIONS 메서드 누락
- Lambda 함수가 CORS 헤더를 반환하지 않음
- API Gateway 리소스 구조 불완전

**해결책**:
1. API Gateway에 모든 리소스와 메서드 추가
2. 각 리소스에 OPTIONS 메서드와 MOCK 통합 추가
3. Lambda 함수에서 APIResponse 클래스 사용하여 CORS 헤더 포함

### 3. DynamoDB 테이블 구조 문제
**발견된 문제들**:

#### tem1-prompts-v2 테이블
- **문제**: GSI 누락으로 조회 실패
- **해결**: userId-index GSI 추가

#### tem1-files 테이블
- **문제**: promptId-uploadedAt-index GSI 누락
- **해결**: GSI 추가로 파일 조회 성능 향상

#### tem1-messages 테이블
- **문제**: 테이블 자체가 없음
- **해결**: 복합 키(conversationId + timestamp) 구조로 생성

### 4. Lambda 환경 변수 불일치
**문제**:
- 하드코딩된 테이블 이름 사용
- tem- 접두사와 tem1- 접두사 혼용

**해결**:
```python
# 모든 Lambda 함수에서 환경 변수 사용
PROMPTS_TABLE = os.environ.get('PROMPTS_TABLE', 'tem1-prompts-v2')
FILES_TABLE = os.environ.get('FILES_TABLE', 'tem1-files')
CONVERSATIONS_TABLE = os.environ.get('CONVERSATIONS_TABLE', 'tem1-conversations-v2')
```

### 5. WebSocket API 라우트 누락
**문제**:
- $connect, $disconnect, sendMessage 라우트만 존재
- $default 라우트 누락으로 메시지 처리 실패

**해결**:
```bash
# $default 라우트 추가
aws apigatewayv2 create-route \
    --api-id mq9a6wf3oj \
    --route-key '$default' \
    --target "integrations/${INTEGRATION_ID}"
```

### 6. IAM 권한 문제
**문제**:
- Lambda 함수가 DynamoDB 접근 불가
- API Gateway 호출 권한 없음

**해결**:
- tem1-dynamodb-policy 생성 및 연결
- tem1-apigateway-policy 생성 및 연결

## 아키텍처 구조

### DynamoDB 테이블 구조
```
tem1-conversations-v2
├── Primary Key: conversationId (S)
└── GSI: userId-createdAt-index
    ├── Partition Key: userId (S)
    └── Sort Key: createdAt (S)

tem1-prompts-v2
├── Primary Key: promptId (S)
└── GSI: userId-index
    └── Partition Key: userId (S)

tem1-files
├── Composite Primary Key:
│   ├── Partition Key: promptId (S)
│   └── Sort Key: fileId (S)
└── GSI: promptId-uploadedAt-index
    ├── Partition Key: promptId (S)
    └── Sort Key: uploadedAt (S)

tem1-messages
├── Composite Primary Key:
│   ├── Partition Key: conversationId (S)
│   └── Sort Key: timestamp (S)
└── TTL: ttl attribute

tem1-usage
└── Primary Key: id (S)

tem1-websocket-connections
├── Primary Key: connectionId (S)
└── TTL: ttl attribute (24시간)
```

### API Gateway 구조
```
REST API (8u7vben959):
/conversations
├── GET, POST, PUT, OPTIONS
└── /{conversationId}
    └── GET, PUT, DELETE, OPTIONS

/prompts
├── GET, POST, OPTIONS
├── /{promptId}
│   ├── GET, POST, PUT, OPTIONS
│   └── /files
│       ├── GET, POST, OPTIONS
│       └── /{fileId}
│           └── GET, PUT, DELETE, OPTIONS

/usage
├── GET, POST, OPTIONS
└── /{userId}
    └── /{engineType}
        └── GET, POST, OPTIONS

WebSocket API (mq9a6wf3oj):
├── $connect → tem1-websocket-connect
├── $disconnect → tem1-websocket-disconnect
├── $default → tem1-websocket-message
└── sendMessage → tem1-websocket-message
```

## 배포 프로세스

### 1. DynamoDB 테이블 생성
```bash
./scripts/01-setup-dynamodb-column.sh
```

### 2. Lambda 함수 생성 및 배포
```bash
./scripts/02-create-lambda-functions.sh
./scripts/05-deploy-lambda.sh
```

### 3. API Gateway 설정
```bash
./scripts/03-setup-api-gateway.sh
./scripts/04-setup-websocket.sh
```

### 4. 프론트엔드 배포
```bash
cd frontend
npm run build
aws s3 sync dist/ s3://sedaily-column-frontend/
aws cloudfront create-invalidation --distribution-id E1M65VE5L8AL9H --paths "/*"
```

## 테스트 방법

### API 엔드포인트 테스트
```bash
# CORS 헤더 확인
curl -i -X GET "https://8u7vben959.execute-api.us-east-1.amazonaws.com/prod/prompts/11" \
  -H "Origin: https://d2kglkjg8iharz.cloudfront.net"

# 대화 생성 테스트
curl -X POST "https://8u7vben959.execute-api.us-east-1.amazonaws.com/prod/conversations" \
  -H "Content-Type: application/json" \
  -d '{"userId":"test-user","engineType":"11","title":"Test"}'
```

### WebSocket 연결 테스트
```javascript
const ws = new WebSocket('wss://mq9a6wf3oj.execute-api.us-east-1.amazonaws.com/prod');
ws.onopen = () => console.log('Connected');
ws.send(JSON.stringify({
  action: 'sendMessage',
  engineType: '11',
  userId: 'test-user',
  conversationId: 'test-conv',
  message: 'Test message'
}));
```

## 주의사항

1. **테이블 이름 일관성**: 모든 서비스에서 tem1- 접두사 사용
2. **GSI 생성 시간**: GSI 생성은 몇 분 소요될 수 있음
3. **Lambda 재배포**: 코드 수정 후 반드시 모든 관련 함수 재배포
4. **CORS 설정**: API Gateway와 Lambda 양쪽 모두에서 CORS 처리 필요

## 모니터링

### CloudWatch 로그 확인
```bash
# Lambda 로그 확인
aws logs tail /aws/lambda/tem1-websocket-message --follow

# API Gateway 로그 확인
aws logs tail API-Gateway-Execution-Logs_8u7vben959/prod --follow
```

### DynamoDB 데이터 확인
```bash
# 대화 목록 확인
aws dynamodb scan --table-name tem1-conversations-v2 \
  --query 'Items[*].[conversationId.S, userId.S, title.S]' \
  --output table

# 메시지 확인
aws dynamodb query --table-name tem1-messages \
  --key-condition-expression "conversationId = :cid" \
  --expression-attribute-values '{":cid":{"S":"CONVERSATION_ID"}}'
```

## 문제 발생 시 체크리스트

- [ ] Lambda 환경 변수 확인
- [ ] DynamoDB 테이블 존재 및 GSI 확인
- [ ] IAM 권한 확인
- [ ] API Gateway 라우트 설정 확인
- [ ] CORS 헤더 반환 확인
- [ ] CloudWatch 로그 확인
- [ ] 프론트엔드 .env 파일 확인