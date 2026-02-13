# 📚 SEDAILY-COLUMN 백엔드 배포 가이드

## 🎯 개요
이 가이드는 Seoul Economic Daily Column 서비스의 백엔드 인프라를 AWS에 배포하는 방법을 설명합니다.

## 🔧 사전 요구사항

### 1. AWS CLI 설치 및 설정
```bash
# AWS CLI 설치 확인
aws --version

# AWS 자격 증명 설정
aws configure
```

### 2. Python 3.9+ 설치
```bash
python3 --version
```

### 3. 필요한 권한
- DynamoDB 테이블 생성/수정
- Lambda 함수 생성/수정
- API Gateway 생성/수정
- IAM 역할 및 정책 생성

## 📁 스크립트 구조

```
backend/scripts/
├── 01-setup-dynamodb-column.sh      # DynamoDB 테이블 생성
├── 02-create-lambda-functions.sh    # Lambda 함수 및 IAM 설정
├── 03-setup-api-gateway.sh          # REST API Gateway 생성
├── 04-setup-websocket.sh            # WebSocket API 생성
├── 05-deploy-lambda.sh              # Lambda 코드 배포
└── deploy-all-column.sh             # 전체 통합 배포
```

## 🚀 배포 방법

### 방법 1: 전체 자동 배포 (권장)
```bash
cd backend/scripts
./deploy-all-column.sh
```

### 방법 2: 개별 스크립트 실행
```bash
cd backend/scripts

# Step 1: DynamoDB 테이블 생성
./01-setup-dynamodb-column.sh

# Step 2: Lambda 함수 및 IAM 역할 생성
./02-create-lambda-functions.sh

# Step 3: REST API Gateway 생성
./03-setup-api-gateway.sh

# Step 4: WebSocket API 생성
./04-setup-websocket.sh

# Step 5: Lambda 코드 배포
./05-deploy-lambda.sh
```

## 📋 생성되는 AWS 리소스

### DynamoDB 테이블 (5개)
- `sedaily-column-conversations` - 대화 세션 저장
- `sedaily-column-prompts` - 프롬프트 템플릿 저장
- `sedaily-column-usage` - 사용량 추적
- `sedaily-column-websocket-connections` - WebSocket 연결 관리
- `sedaily-column-files` - 파일 메타데이터 저장

### Lambda 함수 (6개)
- `sedaily-column-conversation-api` - 대화 API 핸들러
- `sedaily-column-prompt-crud` - 프롬프트 CRUD 작업
- `sedaily-column-usage-handler` - 사용량 처리
- `sedaily-column-websocket-message` - WebSocket 메시지 처리
- `sedaily-column-websocket-connect` - WebSocket 연결 처리
- `sedaily-column-websocket-disconnect` - WebSocket 연결 해제 처리

### API Gateway
- **REST API**: `sedaily-column-rest-api`
  - `/prompts` - 프롬프트 관리
  - `/conversations` - 대화 관리
  - `/usage` - 사용량 조회

- **WebSocket API**: `sedaily-column-websocket-api`
  - `$connect` - 연결 라우트
  - `$disconnect` - 연결 해제 라우트
  - `$default` - 기본 메시지 라우트
  - `sendMessage` - 메시지 전송 라우트

### IAM 역할 및 정책
- `sedaily-column-lambda-execution-role` - Lambda 실행 역할
- `sedaily-column-dynamodb-policy` - DynamoDB 액세스 정책
- `sedaily-column-bedrock-policy` - Bedrock 액세스 정책
- `sedaily-column-apigateway-policy` - API Gateway 액세스 정책

## 🔍 배포 확인

### 1. DynamoDB 테이블 확인
```bash
aws dynamodb list-tables --region us-east-1 | grep sedaily-column
```

### 2. Lambda 함수 확인
```bash
aws lambda list-functions --region us-east-1 | grep sedaily-column
```

### 3. API Gateway 확인
```bash
# REST API
aws apigateway get-rest-apis --region us-east-1

# WebSocket API
aws apigatewayv2 get-apis --region us-east-1
```

## 🔗 프론트엔드 연동

배포 완료 후 출력되는 API URL들을 프론트엔드 `.env` 파일에 추가:

```env
# frontend/.env
VITE_API_URL=https://[REST_API_ID].execute-api.us-east-1.amazonaws.com/prod
VITE_WEBSOCKET_URL=wss://[WS_API_ID].execute-api.us-east-1.amazonaws.com/prod
```

## 🧪 API 테스트

### REST API 테스트
```bash
# 프롬프트 목록 조회
curl https://[REST_API_ID].execute-api.us-east-1.amazonaws.com/prod/prompts

# 대화 생성
curl -X POST https://[REST_API_ID].execute-api.us-east-1.amazonaws.com/prod/conversations \
  -H "Content-Type: application/json" \
  -d '{"userId":"test-user","title":"Test Conversation"}'
```

### WebSocket 테스트
```javascript
// JavaScript 예제
const ws = new WebSocket('wss://[WS_API_ID].execute-api.us-east-1.amazonaws.com/prod');

ws.onopen = () => {
  console.log('Connected');
  ws.send(JSON.stringify({
    action: 'sendMessage',
    message: 'Hello'
  }));
};

ws.onmessage = (event) => {
  console.log('Received:', event.data);
};
```

## ⚠️ 문제 해결

### 권한 오류
```bash
# 스크립트 실행 권한 부여
chmod +x *.sh
```

### AWS 인증 오류
```bash
# AWS 자격 증명 확인
aws sts get-caller-identity
```

### Lambda 배포 실패
```bash
# Python 의존성 설치
pip install -r ../requirements.txt
```

### DynamoDB 테이블이 이미 존재하는 경우
기존 테이블을 삭제하거나 스크립트를 수정하여 다른 이름을 사용

## 📝 유지보수

### Lambda 코드 업데이트
```bash
# 코드 수정 후
./05-deploy-lambda.sh
```

### API Gateway 설정 변경
AWS Console에서 직접 수정하거나 스크립트를 재실행

### DynamoDB 테이블 백업
AWS Console에서 Point-in-Time Recovery 활성화 권장

## 🆘 지원

문제 발생 시:
1. CloudWatch 로그 확인
2. AWS Console에서 리소스 상태 확인
3. 스크립트 로그 메시지 검토

## 📌 중요 참고사항

- **리전**: 모든 리소스는 `us-east-1` 리전에 생성됩니다
- **비용**: AWS 프리티어를 초과할 경우 비용이 발생할 수 있습니다
- **보안**: 프로덕션 환경에서는 추가 보안 설정이 필요합니다
- **접두사**: 모든 리소스는 `sedaily-column` 접두사를 사용합니다

---
*Last updated: 2024*