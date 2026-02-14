# 웹검색 기능 구현 가이드

다른 서비스에 Perplexity 기반 웹검색 기능을 적용할 때 참조하는 마스터 문서입니다.

---

## 1. 개요

### 기능 요약
- Perplexity Sonar API를 활용한 실시간 웹검색
- 검색 결과를 AI 응답에 통합하여 출처와 함께 제공
- 도메인 필터로 저품질 소스 제외
- 검색 진행 상황 시뮬레이션으로 UX 개선

### 아키텍처
```
[사용자 입력]
    ↓
[WebSocket Handler] → webSearchEnabled 확인
    ↓
[Perplexity API] → 웹검색 + AI 응답 생성
    ↓
[클라이언트] ← web_search_start (검색 시작 알림)
            ← web_search_results (출처 목록)
            ← ai_chunk (스트리밍 응답)
            ← chat_end (완료)
```

---

## 2. 백엔드 구현

### 2.1 환경 변수 설정

```bash
# .env 또는 Lambda 환경 변수
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 2.2 Perplexity 클라이언트 (핵심 코드)

**파일 위치:** `backend/lib/perplexity_client.py`

```python
"""
Perplexity Sonar API 클라이언트
실시간 웹검색 + AI 응답 생성
"""
import os
import json
import logging
import requests
from datetime import datetime
from typing import Optional, Generator, Dict, Any, List

logger = logging.getLogger(__name__)

# ===== 설정 =====
DEFAULT_MODEL = "sonar"  # 또는 "sonar-pro" (더 정확, 비용 높음)
API_URL = "https://api.perplexity.ai/chat/completions"

# 블랙리스트: 저품질 소스 제외 (- 접두사 필수)
EXCLUDED_DOMAINS = [
    '-blog.naver.com',    # 네이버 블로그
    '-tistory.com',       # 티스토리
    '-brunch.co.kr',      # 브런치
    '-cafe.naver.com',    # 네이버 카페
    '-cafe.daum.net',     # 다음 카페
    '-namu.wiki',         # 나무위키
    '-kin.naver.com',     # 지식인
]


class PerplexityClient:
    """Perplexity Sonar API 클라이언트"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('PERPLEXITY_API_KEY')
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY 환경 변수가 필요합니다")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def search(
        self,
        query: str,
        system_prompt: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        recency_filter: str = "day",      # day, week, month, year
        use_domain_filter: bool = True
    ) -> Dict[str, Any]:
        """
        웹검색 + AI 응답 (동기)

        Returns:
            {
                'success': bool,
                'content': str,           # AI 응답
                'citations': List[Dict],  # 출처 목록
                'model': str,
                'usage': Dict
            }
        """
        if not system_prompt:
            system_prompt = (
                "당신은 한국의 뉴스 전문 AI입니다. "
                "검색된 최신 정보를 바탕으로 정확하고 객관적인 답변을 제공합니다. "
                "출처가 있는 정보는 반드시 명시하세요."
            )

        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            "temperature": 0.2,
            "max_tokens": 4096,
            "search_recency_filter": recency_filter,
            "return_citations": True,
            "return_related_questions": False
        }

        # 도메인 필터 적용
        if use_domain_filter and EXCLUDED_DOMAINS:
            body["search_domain_filter"] = EXCLUDED_DOMAINS

        try:
            response = requests.post(
                API_URL,
                headers=self.headers,
                json=body,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()

            content = data['choices'][0]['message']['content']
            citations = self._extract_citations(data)

            return {
                'success': True,
                'content': content,
                'citations': citations,
                'display_query': query[:50] + ('...' if len(query) > 50 else ''),
                'model': model,
                'usage': data.get('usage', {})
            }

        except Exception as e:
            logger.error(f"Perplexity API 오류: {e}")
            return {
                'success': False,
                'error': str(e),
                'citations': []
            }

    def search_stream(
        self,
        query: str,
        system_prompt: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        recency_filter: str = "day",
        use_domain_filter: bool = True
    ) -> Generator[str, None, None]:
        """
        웹검색 + AI 응답 (스트리밍)

        주의: 스트리밍에서는 citations가 마지막에 한번만 옴
        last_web_search_result 속성으로 접근
        """
        if not system_prompt:
            system_prompt = (
                "당신은 한국의 뉴스 전문 AI입니다. "
                "검색된 최신 정보를 바탕으로 정확하고 객관적인 답변을 제공합니다."
            )

        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            "temperature": 0.2,
            "max_tokens": 4096,
            "stream": True,
            "search_recency_filter": recency_filter,
            "return_citations": True
        }

        if use_domain_filter and EXCLUDED_DOMAINS:
            body["search_domain_filter"] = EXCLUDED_DOMAINS

        try:
            response = requests.post(
                API_URL,
                headers=self.headers,
                json=body,
                stream=True,
                timeout=120
            )
            response.raise_for_status()

            citations = []

            for line in response.iter_lines():
                if not line:
                    continue

                line_str = line.decode('utf-8')
                if not line_str.startswith('data: '):
                    continue

                data_str = line_str[6:]
                if data_str == '[DONE]':
                    break

                try:
                    data = json.loads(data_str)

                    # citations 추출 (마지막 청크에서)
                    if 'citations' in data:
                        citations = self._extract_citations(data)

                    # 텍스트 청크
                    delta = data.get('choices', [{}])[0].get('delta', {})
                    if 'content' in delta:
                        yield delta['content']

                except json.JSONDecodeError:
                    continue

            # 스트리밍 완료 후 citations 저장
            self.last_web_search_result = {
                'success': True,
                'citations': citations,
                'display_query': query[:50] + ('...' if len(query) > 50 else '')
            }

        except Exception as e:
            logger.error(f"Perplexity 스트리밍 오류: {e}")
            self.last_web_search_result = {'success': False, 'citations': []}

    def _extract_citations(self, data: Dict) -> List[Dict]:
        """API 응답에서 citations 추출 및 정규화"""
        citations = data.get('citations', [])

        if not citations:
            return []

        normalized = []
        for i, citation in enumerate(citations):
            if isinstance(citation, str):
                # URL만 있는 경우
                normalized.append({
                    'index': i + 1,
                    'url': citation,
                    'title': self._extract_domain(citation),
                    'source': self._extract_domain(citation),
                    'date': None
                })
            elif isinstance(citation, dict):
                # 상세 정보가 있는 경우
                normalized.append({
                    'index': i + 1,
                    'url': citation.get('url', ''),
                    'title': citation.get('title', citation.get('name', '')),
                    'source': citation.get('source', self._extract_domain(citation.get('url', ''))),
                    'date': citation.get('published_date') or citation.get('date'),
                    'snippet': citation.get('snippet', '')
                })

        return normalized

    def _extract_domain(self, url: str) -> str:
        """URL에서 도메인 추출"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.replace('www.', '')
            return domain
        except:
            return url[:30] if url else 'Unknown'
```

### 2.3 WebSocket 핸들러 수정

**파일:** `backend/handlers/websocket/message.py`

```python
# 핸들러 함수 내에서 웹검색 처리

# 1. 웹검색 파라미터 추출
web_search_enabled = body.get('webSearchEnabled', False)

# 2. 검색 시작 알림 (웹검색 활성화 시)
if web_search_enabled:
    query_preview = user_message[:30] + ('...' if len(user_message) > 30 else '')
    send_message_to_client(connection_id, {
        'type': 'web_search_start',
        'message': f'"{query_preview}" 관련 정보를 검색하고 있습니다...',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }, apigateway_client)

# 3. 스트리밍 응답 전송 시 웹검색 결과 포함
for chunk in websocket_service.stream_response(
    user_message=user_message,
    # ... 기타 파라미터
    web_search_enabled=web_search_enabled
):
    # 첫 청크 전에 웹검색 결과 전송
    if not web_search_sent and web_search_enabled:
        web_search_result = getattr(websocket_service, 'last_web_search_result', None)

        if web_search_result and web_search_result.get('success'):
            citations = web_search_result.get('citations', [])
            display_query = web_search_result.get('display_query', query_preview)

            if citations:
                send_message_to_client(connection_id, {
                    'type': 'web_search_results',
                    'query': display_query,
                    'citations': citations,
                    'total_results': len(citations),
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }, apigateway_client)

        web_search_sent = True

    # 일반 청크 전송
    send_message_to_client(connection_id, {
        'type': 'ai_chunk',
        'chunk': chunk,
        'chunk_index': chunk_index,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }, apigateway_client)
```

### 2.4 WebSocket 메시지 타입 정리

| 타입 | 방향 | 설명 |
|------|------|------|
| `web_search_start` | Server→Client | 검색 시작 알림 |
| `web_search_results` | Server→Client | 출처 목록 (citations) |
| `ai_chunk` | Server→Client | AI 응답 청크 |
| `chat_end` | Server→Client | 응답 완료 |

---

## 3. 프론트엔드 구현

### 3.1 WebSocket 메시지 핸들러

```javascript
// WebSocket 메시지 수신 처리
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch (data.type) {
    case 'web_search_start':
      // 검색 시작 UI 표시
      setWebSearchStatus(data.message);
      break;

    case 'web_search_results':
      // 출처 목록 저장
      setWebSearchResults({
        query: data.query,
        citations: data.citations,
        totalResults: data.total_results
      });
      setWebSearchStatus(null);  // 검색 상태 초기화
      break;

    case 'ai_chunk':
      // 스트리밍 텍스트 추가
      setStreamingText(prev => prev + data.chunk);
      break;

    case 'chat_end':
      // 스트리밍 완료
      setIsStreaming(false);
      break;
  }
};
```

### 3.2 검색 진행 시뮬레이션 (UX 개선)

```javascript
// 검색 중 메시지 회전 (3~5초 대기 동안 자연스러운 피드백)
const SEARCH_MESSAGES = [
  "관련 뉴스를 찾고 있습니다...",
  "최신 기사를 수집하고 있습니다...",
  "출처를 확인하고 있습니다...",
  "정보를 정리하고 있습니다...",
];

const [searchMessageIndex, setSearchMessageIndex] = useState(0);

useEffect(() => {
  if (!webSearchStatus) {
    setSearchMessageIndex(0);
    return;
  }

  const interval = setInterval(() => {
    setSearchMessageIndex((prev) => (prev + 1) % SEARCH_MESSAGES.length);
  }, 1500);  // 1.5초 간격

  return () => clearInterval(interval);
}, [webSearchStatus]);

// 렌더링 시
{webSearchStatus && (
  <span className="text-sm text-text-300">
    {SEARCH_MESSAGES[searchMessageIndex]}
  </span>
)}
```

### 3.3 웹검색 결과 UI 컴포넌트

```jsx
// 토글 가능한 출처 카드
const WebSearchResultsToggle = ({ query, citations }) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!citations || citations.length === 0) return null;

  return (
    <div className="mb-4 border border-gray-200 rounded-lg overflow-hidden">
      {/* 헤더 (클릭 시 토글) */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100"
      >
        <div className="flex items-center gap-2">
          <Globe size={16} className="text-blue-500" />
          <span className="font-medium">{query}</span>
          <span className="text-xs text-gray-500">
            {citations.length}개 출처
          </span>
        </div>
        <ChevronDown
          size={16}
          className={`transition-transform ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      {/* 출처 목록 */}
      {isOpen && (
        <div className="p-3 space-y-2 max-h-64 overflow-y-auto">
          {citations.map((citation, idx) => (
            <a
              key={idx}
              href={citation.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block p-2 hover:bg-gray-50 rounded"
            >
              <div className="font-medium text-sm text-blue-600 truncate">
                {citation.title || citation.source}
              </div>
              <div className="text-xs text-gray-500 flex items-center gap-2">
                <span>{citation.source}</span>
                {citation.date && (
                  <>
                    <span>•</span>
                    <span>{formatDate(citation.date)}</span>
                  </>
                )}
              </div>
            </a>
          ))}
        </div>
      )}
    </div>
  );
};
```

### 3.4 스트리밍 컴포넌트에 웹검색 UI 통합

```jsx
// StreamingAssistantMessage.jsx
const StreamingAssistantMessage = ({
  content,
  isStreaming,
  webSearchStatus,      // 검색 상태 메시지
  webSearchResultsUI,   // 웹검색 결과 컴포넌트
}) => {
  return (
    <div className="assistant-message">
      {/* 스트리밍 중이고 아직 응답이 없을 때 */}
      {isStreaming && !content ? (
        webSearchStatus ? (
          <span className="text-sm text-gray-500">{webSearchStatus}</span>
        ) : (
          <span className="text-sm text-gray-500">답변 생성 중...</span>
        )
      ) : (
        <div className="response-content">
          {/* 웹검색 결과 토글 (AI 응답 위에) */}
          {webSearchResultsUI}

          {/* AI 응답 */}
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      )}
    </div>
  );
};
```

---

## 4. 도메인 필터 설정

### 블랙리스트 방식 (현재 사용)

저품질 소스만 제외하고, 나머지는 모두 허용:

```python
EXCLUDED_DOMAINS = [
    '-blog.naver.com',    # 네이버 블로그
    '-tistory.com',       # 티스토리
    '-brunch.co.kr',      # 브런치
    '-cafe.naver.com',    # 네이버 카페
    '-cafe.daum.net',     # 다음 카페
    '-namu.wiki',         # 나무위키
    '-kin.naver.com',     # 지식인
]
```

### 화이트리스트 방식 (필요시)

신뢰할 수 있는 소스만 허용:

```python
TRUSTED_DOMAINS = [
    'reuters.com',
    'bloomberg.com',
    'yonhapnews.co.kr',
    'mk.co.kr',
    'sedaily.com',
    # ... 더 추가
]
```

---

## 5. 적용 체크리스트

### 백엔드
- [ ] `PERPLEXITY_API_KEY` 환경 변수 설정
- [ ] `perplexity_client.py` 복사 및 경로 수정
- [ ] WebSocket 핸들러에 `webSearchEnabled` 파라미터 추가
- [ ] `web_search_start`, `web_search_results` 메시지 전송 로직 추가
- [ ] 기존 AI 응답 스트리밍 로직과 통합

### 프론트엔드
- [ ] WebSocket 메시지 타입 핸들러 추가 (`web_search_start`, `web_search_results`)
- [ ] 웹검색 상태 state 추가 (`webSearchStatus`, `webSearchResults`)
- [ ] 검색 시뮬레이션 메시지 구현
- [ ] 웹검색 결과 토글 UI 컴포넌트 추가
- [ ] 스트리밍 컴포넌트에 웹검색 UI 통합
- [ ] 웹검색 토글 스위치 UI 추가 (사용자가 on/off)

### 테스트
- [ ] 웹검색 on/off 동작 확인
- [ ] 출처 목록 표시 확인
- [ ] 스트리밍 중 UI 깜빡임 없는지 확인
- [ ] 도메인 필터 작동 확인

---

## 6. 비용 및 성능

### Perplexity API 비용 (2024년 기준)
- **sonar**: $5/1M tokens (입력), $15/1M tokens (출력)
- **sonar-pro**: $3/1M tokens (입력), $15/1M tokens (출력) + 검색 요청당 $5

### 응답 시간
- 일반적으로 3~5초 (검색 + AI 생성)
- 스트리밍으로 체감 속도 개선

### 최적화 팁
- 불필요한 쿼리 최적화 API 호출 제거 (Perplexity가 자체적으로 의도 분석)
- `search_recency_filter`를 목적에 맞게 설정 (day/week/month)
- 도메인 필터로 검색 범위 조정

---

## 7. 참고 자료

- [Perplexity Sonar API 문서](https://docs.perplexity.ai/api-reference)
- 현재 구현: `backend/lib/perplexity_client.py`
- 프론트엔드 예시: `frontend/src/features/chat/components/ChatPage.jsx`

---

*Last Updated: 2026-01-24*
