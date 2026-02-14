# 웹검색 기능 구현 가이드

## 개요
Perplexity Sonar API를 활용한 실시간 웹검색 기능 구현 가이드입니다.
PROOF 서비스에서 구현 완료되었으며, 다른 서비스(ONE 등)에 적용 시 참고하세요.

---

## 수정 파일 목록

### 백엔드 (Lambda)
| 파일 | 역할 |
|------|------|
| `backend/services/perplexity_client.py` | Perplexity API 호출 클라이언트 |
| `backend/services/websocket_service.py` | WebSocket 메시지에서 `webSearchEnabled` 파싱 및 처리 |
| `backend/lib/message.py` | 메시지 모델에 `web_search` 필드 추가 |

### 프론트엔드
| 파일 | 수정 내용 |
|------|----------|
| `frontend/src/features/chat/services/websocketService.js` | `sendMessage`에 `webSearchEnabled` 파라미터 추가 |
| `frontend/src/features/chat/components/ChatPage.jsx` | 3곳의 `sendChatMessage` 호출에 `webSearchEnabled` 전달 |
| `frontend/src/features/chat/components/ChatInput.jsx` | `sendChatMessage` 호출 시 `webSearchEnabled` 전달 |

---

## 핵심 코드 변경

### 1. websocketService.js - sendMessage 메서드
```javascript
sendMessage(
  message,
  engineType = "Basic",
  conversationId = null,
  conversationHistory = null,
  idempotencyKey = null,
  selectedModel = "claude-opus-4-5-20251101",
  webSearchEnabled = false  // 추가
)
```

### 2. websocketService.js - payload 구성
```javascript
const payload = {
  action: "sendMessage",
  message: message,
  engineType: engineType,
  conversationId: conversationId,
  // ... 기타 필드
  webSearchEnabled: webSearchEnabled,  // 추가
  timestamp: new Date().toISOString(),
  conversationHistory: processedHistory,
};
```

### 3. websocketService.js - export 함수
```javascript
export const sendChatMessage = (
  message,
  engineType,
  conversationHistory,
  conversationId,
  idempotencyKey,
  selectedModel,
  webSearchEnabled = false  // 추가
) =>
  webSocketService.sendMessage(
    message,
    engineType,
    conversationId,
    conversationHistory,
    idempotencyKey,
    selectedModel,
    webSearchEnabled  // 추가
  );
```

### 4. ChatPage.jsx - sendChatMessage 호출 (3곳)
```javascript
// 예시: 일반 메시지 전송
await sendChatMessage(
  messageContent,
  selectedEngine,
  conversationHistory,
  currentConversationId,
  userMessage.idempotencyKey,
  null, // selectedModel
  webSearchEnabled  // 추가
);
```

---

## 시행착오 및 주의사항

### 문제 1: 파라미터가 전달되지 않음
- **증상**: Lambda 로그에 `web_search: False`가 계속 출력
- **원인**: `sendChatMessage`를 호출하는 곳이 여러 군데 있음
- **해결**: Grep으로 모든 호출 위치 파악 후 전부 수정

```bash
# 모든 sendChatMessage 호출 위치 찾기
grep -rn "sendChatMessage" frontend/src/
```

### 문제 2: ChatInput.jsx만 수정하면 안됨
- `ChatPage.jsx`에서 직접 `sendChatMessage`를 호출하는 곳이 3곳 있음
- 모든 호출 위치에서 `webSearchEnabled` 파라미터를 전달해야 함

---

## 테스트 방법

### 1. Perplexity API 직접 테스트 (curl)
```bash
# API 키 가져오기
API_KEY=$(aws secretsmanager get-secret-value \
  --secret-id nexus/perplexity-api-key \
  --region us-east-1 \
  --query SecretString --output text | jq -r '.PERPLEXITY_API_KEY')

# API 호출
curl -X POST "https://api.perplexity.ai/chat/completions" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sonar",
    "messages": [{"role": "user", "content": "오늘 코스피 소식"}],
    "search_recency_filter": "day"
  }'
```

### 2. Lambda 로그 확인
```bash
# CloudWatch Logs에서 web_search 상태 확인
aws logs filter-log-events \
  --log-group-name /aws/lambda/nx-wt-prf-websocket-message \
  --filter-pattern "web_search"
```

### 3. 프론트엔드 테스트
1. 페이지 강력 새로고침 (Ctrl+Shift+R / Cmd+Shift+R)
2. 웹검색 토글 활성화
3. "오늘 코스피 소식" 같은 실시간 정보 질문

---

## 배포 순서

```bash
# 1. 백엔드 배포 (Lambda)
./deploy-anthropic.sh

# 2. 프론트엔드 배포 (S3/CloudFront)
./deploy-frontend.sh
```

---

## AWS 리소스 정보 (PROOF)

| 리소스 | 값 |
|--------|-----|
| Lambda 함수 prefix | `nx-wt-prf-*` |
| Secrets Manager | `proof-v1` (Anthropic), `nexus/perplexity-api-key` (Perplexity) |
| S3 버킷 | `nexus-multi-frontend-20251204` |
| CloudFront Distribution | `E1O9OA8UA34Z49` |
| CloudFront 도메인 | `d1zig3y52jaq1s.cloudfront.net` |

---

## 다음 서비스(ONE) 적용 시 체크리스트

- [ ] 백엔드 `perplexity_client.py` 복사/수정
- [ ] 백엔드 `websocket_service.py`에 webSearchEnabled 파싱 추가
- [ ] 백엔드 `message.py`에 web_search 필드 추가
- [ ] 프론트엔드 `websocketService.js` 수정
- [ ] 프론트엔드 `sendChatMessage` 호출하는 **모든 위치** 수정
- [ ] Secrets Manager에 Perplexity API 키 등록 확인
- [ ] Lambda IAM 역할에 Secrets Manager 권한 추가
- [ ] 배포 스크립트의 리소스 ID 확인 (버킷, CloudFront, Lambda 함수명)

---

## 작성일
2026-01-24
