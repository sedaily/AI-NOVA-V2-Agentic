# TEM1 서비스 배포 체크리스트

## ✅ CORS 설정 완료 상태

### API Gateway CORS 설정
- ✅ 모든 리소스에 OPTIONS 메서드 추가
- ✅ CORS 헤더 설정 완료
  - Access-Control-Allow-Origin: *
  - Access-Control-Allow-Headers: Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token
  - Access-Control-Allow-Methods: GET,POST,PUT,DELETE,OPTIONS,PATCH

### Lambda 함수 CORS 응답
- ✅ APIResponse 클래스에서 CORS 헤더 자동 포함
- ✅ 모든 Lambda 함수가 utils/response.py 사용

### 현재 API 구조 (완벽히 구성됨)
```
/
├── /conversations
│   ├── Methods: GET, POST, PUT, OPTIONS ✅
│   └── /{conversationId}
│       └── Methods: GET, PUT, DELETE, OPTIONS ✅
├── /prompts
│   ├── Methods: GET, POST, OPTIONS ✅
│   └── /{promptId}
│       ├── Methods: GET, POST, PUT, OPTIONS ✅
│       └── /files
│           ├── Methods: GET, POST, OPTIONS ✅
│           └── /{fileId}
│               └── Methods: GET, PUT, DELETE, OPTIONS ✅
└── /usage
    ├── Methods: GET, POST, OPTIONS ✅
    └── /{userId}
        └── /{engineType}
            └── Methods: GET, POST, OPTIONS ✅
```

## ✅ DynamoDB 테이블 및 GSI

### 테이블 구조
1. **tem1-conversations-v2**
   - Primary Key: conversationId (S)
   - GSI: userId-createdAt-index ✅

2. **tem1-prompts-v2**
   - Primary Key: promptId (S)
   - GSI: userId-index ✅

3. **tem1-files**
   - Composite Key: promptId (HASH), fileId (RANGE)
   - GSI: promptId-uploadedAt-index ✅

4. **tem1-messages**
   - Composite Key: conversationId (HASH), timestamp (RANGE)
   - TTL: enabled ✅

5. **tem1-usage**
   - Composite Key: userId (HASH), period (RANGE)

6. **tem1-websocket-connections**
   - Primary Key: connectionId (S)
   - TTL: enabled ✅

## ✅ Lambda 함수 환경 변수

모든 Lambda 함수에 설정된 환경 변수:
- PROMPTS_TABLE=tem1-prompts-v2
- FILES_TABLE=tem1-files
- CONVERSATIONS_TABLE=tem1-conversations-v2
- MESSAGES_TABLE=tem1-messages
- USAGE_TABLE=tem1-usage
- CONNECTIONS_TABLE=tem1-websocket-connections
- WEBSOCKET_TABLE=tem1-websocket-connections
- ENABLE_NEWS_SEARCH=true

## 📁 스크립트 구조 (정리 완료)

### 핵심 스크립트
```bash
scripts/
├── 00-config.sh                 # 공통 설정 (REST_API_ID, WS_API_ID 포함)
├── 01-create-dynamodb.sh        # DynamoDB + GSI 생성 개선됨
├── 02-create-lambda-functions.sh
├── 03-setup-rest-api.sh         # CORS 완벽 지원 버전으로 교체됨
├── 04-setup-websocket-api.sh
├── 05-setup-lambda-permissions.sh
├── 06-deploy-lambda-code.sh     # 환경 변수 업데이트 포함
├── 07-create-s3-bucket.sh
├── 08-setup-cloudfront.sh
├── 09-deploy-frontend.sh
├── 10-update-config.sh
├── 11-update-backend-config.sh
├── 12-update-frontend-config.sh
├── 13-update-lambda-env.sh
└── deploy-all.sh                # 전체 배포 마스터 스크립트 (구 99번)
```

### 삭제된 중복 파일
- ❌ deploy-new-service.sh (deploy-all.sh로 통합)
- ❌ 03-setup-rest-api-enhanced.sh (03-setup-rest-api.sh로 통합)
- ❌ fix-all-tem1-issues.sh (기능이 각 스크립트에 통합됨)

## 🚀 배포 명령어

### 전체 배포
```bash
cd scripts
./deploy-all.sh
```

### 개별 수정
```bash
# DynamoDB GSI 추가
./01-create-dynamodb.sh

# API Gateway CORS 수정
./03-setup-rest-api.sh

# Lambda 코드 재배포
./06-deploy-lambda-code.sh
```

## ✅ 검증 완료

### API 테스트 결과
```bash
# GET /prompts/11 - 200 OK ✅
# POST /conversations - 201 Created ✅
# CORS 헤더 정상 반환 ✅
```

### WebSocket
- $connect ✅
- $disconnect ✅
- $default ✅
- sendMessage ✅

## 📊 현재 상태

| 항목 | 상태 | 비고 |
|------|------|------|
| DynamoDB 테이블 | ✅ | 모든 테이블 및 GSI 생성 완료 |
| Lambda 함수 | ✅ | 6개 함수 모두 배포 완료 |
| REST API Gateway | ✅ | CORS 설정 포함 완료 |
| WebSocket API | ✅ | 모든 라우트 설정 완료 |
| 프론트엔드 | ✅ | CloudFront 배포 완료 |
| 환경 변수 | ✅ | 모든 설정 동기화 완료 |

## 🎯 우수 사례와 비교

성공한 배포 구조와 100% 일치:
- ✅ 동일한 테이블 스키마
- ✅ 동일한 GSI 구조
- ✅ 동일한 API 리소스 구조
- ✅ 동일한 CORS 설정
- ✅ 동일한 Lambda 환경 변수

## 📝 문제 발생 시

TEM1_TROUBLESHOOTING_GUIDE.md 참조