# API 엔드포인트 명세서

## 📋 기본 정보

### Base URL

```
Production:  https://t75vorhge1.execute-api.us-east-1.amazonaws.com/prod
Staging:     https://t75vorhge1.execute-api.us-east-1.amazonaws.com/staging
Development: https://t75vorhge1.execute-api.us-east-1.amazonaws.com/dev
```

### 인증

- **Type**: Bearer Token (JWT)
- **Header**: `Authorization: Bearer <token>`
- **멀티테넌트**: Authorizer를 통한 테넌트 식별

### 공통 응답 형식

```json
{
  "statusCode": 200,
  "success": true,
  "data": { ... },
  "message": "Success"
}
```

### 에러 응답

```json
{
  "statusCode": 400,
  "success": false,
  "error": "Error message"
}
```

## 🎯 프롬프트 관리 API

### 1. 프롬프트 목록 조회

```http
GET /prompts
```

**응답 예시:**

```json
{
  "statusCode": 200,
  "success": true,
  "data": {
    "prompts": [
      {
        "promptId": "C1",
        "description": "일반 대화형 AI",
        "instruction": "사용자와 자연스러운 대화를 나누세요.",
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z"
      }
    ]
  }
}
```

### 2. 특정 프롬프트 조회

```http
GET /prompts/{promptId}
```

**Path Parameters:**

- `promptId` (string): 프롬프트 ID (예: C1, C2, C3)

**응답 예시:**

```json
{
  "statusCode": 200,
  "success": true,
  "data": {
    "prompt": {
      "promptId": "C1",
      "description": "일반 대화형 AI",
      "instruction": "사용자와 자연스러운 대화를 나누세요."
    },
    "files": [
      {
        "promptId": "C1",
        "fileId": "uuid-1234",
        "fileName": "example.txt",
        "fileContent": "파일 내용...",
        "createdAt": "2024-01-01T00:00:00Z"
      }
    ]
  }
}
```

### 3. 프롬프트 생성/업데이트

```http
POST /prompts
```

**Request Body:**

```json
{
  "engineType": "C1",
  "description": "새로운 프롬프트 설명",
  "instruction": "새로운 지시사항"
}
```

**응답 예시:**

```json
{
  "statusCode": 200,
  "success": true,
  "data": {
    "message": "Prompt created/updated successfully",
    "promptId": "C1"
  }
}
```

### 4. 프롬프트 수정

```http
PUT /prompts/{promptId}
```

**Path Parameters:**

- `promptId` (string): 프롬프트 ID

**Request Body:**

```json
{
  "description": "수정된 설명",
  "instruction": "수정된 지시사항"
}
```

## 📁 파일 관리 API

### 1. 파일 목록 조회

```http
GET /prompts/{promptId}/files
```

**응답 예시:**

```json
{
  "statusCode": 200,
  "success": true,
  "data": {
    "files": [
      {
        "promptId": "C1",
        "fileId": "uuid-1234",
        "fileName": "example.txt",
        "fileContent": "파일 내용...",
        "createdAt": "2024-01-01T00:00:00Z"
      }
    ]
  }
}
```

### 2. 파일 생성

```http
POST /prompts/{promptId}/files
```

**Request Body:**

```json
{
  "fileName": "new-file.txt",
  "fileContent": "새 파일의 내용입니다."
}
```

**응답 예시:**

```json
{
  "statusCode": 201,
  "success": true,
  "data": {
    "file": {
      "promptId": "C1",
      "fileId": "uuid-5678",
      "fileName": "new-file.txt",
      "fileContent": "새 파일의 내용입니다.",
      "createdAt": "2024-01-01T00:00:00Z"
    }
  }
}
```

### 3. 파일 수정

```http
PUT /prompts/{promptId}/files/{fileId}
```

**Request Body:**

```json
{
  "fileName": "updated-file.txt",
  "fileContent": "수정된 파일 내용입니다."
}
```

### 4. 파일 삭제

```http
DELETE /prompts/{promptId}/files/{fileId}
```

## 💬 대화 관리 API

### 1. 대화 목록 조회

```http
GET /conversations?userId={userId}&engineType={engineType}
```

**Query Parameters:**

- `userId` (string): 사용자 ID (멀티테넌트 환경에서는 Authorizer에서 자동 추출)
- `engineType` (string, optional): 엔진 타입으로 필터링

**응답 예시:**

```json
{
  "statusCode": 200,
  "success": true,
  "data": {
    "conversations": [
      {
        "conversationId": "conv-uuid-1234",
        "userId": "user@example.com",
        "engineType": "C1",
        "title": "대화 제목",
        "messages": [
          {
            "role": "user",
            "content": "안녕하세요"
          },
          {
            "role": "assistant",
            "content": "안녕하세요! 무엇을 도와드릴까요?"
          }
        ],
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z"
      }
    ],
    "count": 1
  }
}
```

### 2. 특정 대화 조회

```http
GET /conversations/{conversationId}
```

**응답 예시:**

```json
{
  "statusCode": 200,
  "success": true,
  "data": {
    "conversationId": "conv-uuid-1234",
    "userId": "user@example.com",
    "engineType": "C1",
    "title": "대화 제목",
    "messages": [...],
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-01T00:00:00Z"
  }
}
```

### 3. 대화 생성/저장

```http
POST /conversations
```

**Request Body:**

```json
{
  "userId": "user@example.com",
  "conversationId": "conv-uuid-1234",
  "engineType": "C1",
  "title": "새로운 대화",
  "messages": [
    {
      "role": "user",
      "content": "안녕하세요"
    },
    {
      "role": "assistant",
      "content": "안녕하세요! 무엇을 도와드릴까요?"
    }
  ]
}
```

**응답 예시:**

```json
{
  "statusCode": 201,
  "success": true,
  "data": {
    "conversationId": "conv-uuid-1234",
    "userId": "user@example.com",
    "engineType": "C1",
    "title": "새로운 대화",
    "message": "Conversation created successfully"
  }
}
```

### 4. 대화 제목 수정

```http
PATCH /conversations/{conversationId}
```

**Request Body:**

```json
{
  "title": "수정된 대화 제목"
}
```

### 5. 대화 삭제

```http
DELETE /conversations/{conversationId}
```

## 📊 사용량 추적 API

### 1. 특정 엔진 사용량 조회

```http
GET /usage/{userId}/{engineType}
```

**Path Parameters:**

- `userId` (string): 사용자 ID (URL 인코딩 필요, 예: user%40example.com)
- `engineType` (string): 엔진 타입 (C1, C2, C3 등)

**응답 예시:**

```json
{
  "statusCode": 200,
  "success": true,
  "data": {
    "userId": "user@example.com",
    "engineType": "C1",
    "yearMonth": "2024-01",
    "totalTokens": 1500,
    "inputTokens": 800,
    "outputTokens": 700,
    "messageCount": 25
  }
}
```

### 2. 전체 사용량 조회

```http
GET /usage/{userId}/all
```

**응답 예시:**

```json
{
  "statusCode": 200,
  "success": true,
  "data": {
    "C1": [
      {
        "userId": "user@example.com",
        "engineType": "C1",
        "yearMonth": "2024-01",
        "totalTokens": 1500,
        "inputTokens": 800,
        "outputTokens": 700,
        "messageCount": 25
      }
    ],
    "C2": [
      {
        "userId": "user@example.com",
        "engineType": "C2",
        "yearMonth": "2024-01",
        "totalTokens": 800,
        "inputTokens": 400,
        "outputTokens": 400,
        "messageCount": 12
      }
    ]
  }
}
```

### 3. 사용량 업데이트

```http
POST /usage
```

**Request Body:**

```json
{
  "userId": "user@example.com",
  "engineType": "C1",
  "inputText": "사용자 입력 텍스트",
  "outputText": "AI 응답 텍스트",
  "userPlan": "free"
}
```

**응답 예시:**

```json
{
  "statusCode": 200,
  "success": true,
  "data": {
    "success": true,
    "usage": {
      "userId": "user@example.com",
      "engineType": "C1",
      "yearMonth": "2024-01",
      "totalTokens": 1520,
      "inputTokens": 810,
      "outputTokens": 710,
      "messageCount": 26
    },
    "tokensUsed": 20,
    "percentage": 15.2,
    "remaining": 8480
  }
}
```

## 🔐 인증 및 권한

### JWT 토큰 구조

```json
{
  "userId": "user@example.com",
  "tenantId": "sedaily",
  "role": "user",
  "plan": "free",
  "features": ["BASIC_CHAT", "FILE_UPLOAD"],
  "exp": 1640995200,
  "iat": 1640908800
}
```

### 권한 레벨

- **user**: 일반 사용자 권한
- **admin**: 관리자 권한 (모든 테넌트 데이터 접근 가능)

### 플랜별 제한

```json
{
  "free": {
    "monthlyTokenLimit": 10000,
    "features": ["BASIC_CHAT"]
  },
  "basic": {
    "monthlyTokenLimit": 100000,
    "features": ["BASIC_CHAT", "FILE_UPLOAD"]
  },
  "premium": {
    "monthlyTokenLimit": 500000,
    "features": ["BASIC_CHAT", "FILE_UPLOAD", "ADVANCED_FEATURES"]
  }
}
```

## 🌐 CORS 설정

모든 엔드포인트는 다음 CORS 헤더를 지원합니다:

```http
Access-Control-Allow-Origin: *
Access-Control-Allow-Headers: Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token
Access-Control-Allow-Methods: GET,POST,PUT,DELETE,OPTIONS
```

## 📝 에러 코드

| 상태 코드 | 설명                 | 예시                      |
| --------- | -------------------- | ------------------------- |
| 200       | 성공                 | 정상 처리                 |
| 201       | 생성됨               | 리소스 생성 성공          |
| 400       | 잘못된 요청          | 필수 파라미터 누락        |
| 401       | 인증 실패            | 유효하지 않은 토큰        |
| 403       | 권한 없음            | 접근 권한 부족            |
| 404       | 찾을 수 없음         | 리소스가 존재하지 않음    |
| 405       | 허용되지 않는 메서드 | 지원하지 않는 HTTP 메서드 |
| 429       | 요청 한도 초과       | 사용량 한도 초과          |
| 500       | 서버 오류            | 내부 서버 오류            |

## 🧪 테스트 예시

### cURL 예시

```bash
# 프롬프트 목록 조회
curl -X GET "https://t75vorhge1.execute-api.us-east-1.amazonaws.com/prod/prompts" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"

# 대화 생성
curl -X POST "https://t75vorhge1.execute-api.us-east-1.amazonaws.com/prod/conversations" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user@example.com",
    "engineType": "C1",
    "title": "새로운 대화",
    "messages": [
      {"role": "user", "content": "안녕하세요"}
    ]
  }'

# 사용량 조회
curl -X GET "https://t75vorhge1.execute-api.us-east-1.amazonaws.com/prod/usage/user%40example.com/all" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

### JavaScript 예시

```javascript
const baseURL = "https://t75vorhge1.execute-api.us-east-1.amazonaws.com/prod";
const token = "YOUR_JWT_TOKEN";

// 프롬프트 목록 조회
const getPrompts = async () => {
  const response = await fetch(`${baseURL}/prompts`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });
  return response.json();
};

// 대화 생성
const createConversation = async (conversationData) => {
  const response = await fetch(`${baseURL}/conversations`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(conversationData),
  });
  return response.json();
};
```

## 📚 추가 리소스

- [API 배포 가이드](./API_DEPLOYMENT_GUIDE.md)
- [API Gateway 설정 가이드](./API_GATEWAY_SETUP.md)
- [멀티테넌트 아키텍처 문서](./MULTITENANT_ARCHITECTURE.md)
