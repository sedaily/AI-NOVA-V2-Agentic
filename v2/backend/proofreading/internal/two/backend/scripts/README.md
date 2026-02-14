# Backend Scripts

백엔드 AWS 리소스 설정 및 배포 스크립트 모음

## 📁 스크립트 구조

```
scripts/
├── 01-setup-dynamodb.sh      # DynamoDB 테이블 생성
├── 02-setup-api-gateway.sh   # API Gateway 설정
├── 03-setup-api-routes.sh    # API 라우트 설정
└── 99-deploy-lambda.sh       # Lambda 함수 배포
```

## 🚀 실행 순서

### 1️⃣ 초기 설정 (최초 1회)
```bash
# DynamoDB 테이블 생성
./01-setup-dynamodb.sh

# API Gateway 설정
./02-setup-api-gateway.sh

# API 라우트 설정
./03-setup-api-routes.sh
```

### 2️⃣ 배포 (코드 변경 시마다)
```bash
# Lambda 함수 코드 배포
./99-deploy-lambda.sh
```

## 📝 스크립트 설명

### `01-setup-dynamodb.sh`
- **용도**: DynamoDB 테이블 생성
- **테이블**:
  - nexus-conversations
  - nexus-prompts
  - nexus-usage
  - nexus-websocket-connections

### `02-setup-api-gateway.sh`
- **용도**: REST API & WebSocket API 생성
- **API**:
  - REST API Gateway
  - WebSocket API Gateway

### `03-setup-api-routes.sh`
- **용도**: API 라우트 및 통합 설정
- **라우트**:
  - `/conversations`
  - `/prompts`
  - `/usage`
  - WebSocket routes

### `99-deploy-lambda.sh`
- **용도**: Lambda 함수 코드 배포
- **대상 함수**:
  - nx-wt-prf-conversation-api
  - nx-wt-prf-prompt-crud
  - nx-wt-prf-usage-handler
  - nx-wt-prf-websocket-message
- **특징**:
  - 자동 ZIP 패키징
  - 병렬 배포
  - 상태 확인

## ⚠️ 주의사항

1. **AWS CLI 설정 필요**
   ```bash
   aws configure
   ```

2. **권한 필요**
   - DynamoDB 생성/수정
   - API Gateway 관리
   - Lambda 함수 업데이트

3. **리전 설정**
   - 기본값: `us-east-1`
   - 변경 시 스크립트 내부 수정 필요

## 🔧 문제 해결

### 권한 오류
```bash
chmod +x *.sh
```

### AWS 인증 오류
```bash
aws sts get-caller-identity
```

### 배포 실패 시 롤백
```bash
git checkout -- .
```