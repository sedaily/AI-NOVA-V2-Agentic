# AI 자동 라우팅 시스템 (Agentic Orchestration)

## 개요

AI NOVA에 **자동 라우팅 시스템**을 추가하여, 사용자가 입력한 텍스트를 분석해 자동으로 최적의 서비스(버디)로 라우팅합니다.

## 아키텍처

```
사용자 입력
    ↓
💎 AI 버튼 클릭
    ↓
┌─────────────────────────────────────┐
│  Supervisor Agent (오케스트레이터)   │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Step 1: 빠른 언어 체크 (무료)       │
│  - 한글 비율 30% 이상 → 한글         │
│  - 그 외 → 외국어                    │
└─────────────────────────────────────┘
    ↓
    ├─ 외국어 → Language Agent → f1 (외신)
    │
    └─ 한글 ↓
         ┌──────────────────────────────┐
         │  Content Type Agent          │
         │  - 보도자료 감지              │
         │  - 공공/기업 분류             │
         └──────────────────────────────┘
              ↓
              ├─ 보도자료 → w1 (보도자료 서비스)
              │
              └─ 일반 기사 ↓
                   ┌──────────────────────┐
                   │  Category Agent      │
                   │  - 경제/사회/일반    │
                   └──────────────────────┘
                        ↓
                   ┌──────────────────────┐
                   │  Length Agent        │
                   │  - 단문/장문         │
                   └──────────────────────┘
                        ↓
                   최종 라우팅: b1 → p1 → r1
```

## 구현된 Agent들

### 1. Language Detector Agent
**위치**: `backend/agents/language-detector/`

**기능**: 텍스트 언어 감지
- 한글, 영어, 일본어 구분
- 외신 서비스 필요 여부 판단

**응답 예시**:
```json
{
  "language": "korean",
  "needsForeignAgent": false,
  "confidence": "high"
}
```

### 2. Category Detector Agent
**위치**: `backend/agents/category-detector/`

**기능**: 기사 카테고리 분류
- 경제, 사회, 일반 분류
- 교열 서비스 프롬프트 선택에 사용

**응답 예시**:
```json
{
  "category": "economy",
  "confidence": "high"
}
```

### 3. Length Detector Agent
**위치**: `backend/agents/length-detector/`

**기능**: 텍스트 길이 분석
- 600자 기준으로 단문/장문 구분
- 퇴고 서비스 프롬프트 선택에 사용

**응답 예시**:
```json
{
  "charCount": 450,
  "isLongForm": false,
  "lengthType": "short"
}
```

### 4. Content Type Detector Agent
**위치**: `backend/agents/content-type-detector/`

**기능**: 콘텐츠 타입 감지
- 보도자료 vs 일반 기사 구분
- 보도자료인 경우 공공/기업 분류

**응답 예시**:
```json
{
  "isPressRelease": true,
  "pressType": "corporate",
  "writerConfig": {
    "serviceCode": "w1",
    "promptType": "corporate",
    "engineType": "11",
    "contentType": "press_corporate"
  }
}
```

### 5. Supervisor Agent (오케스트레이터)
**위치**: `backend/agents/supervisor/`

**기능**: 전체 라우팅 플로우 관리
- 4개 Agent 순차 호출
- 최종 라우팅 결정
- 비용 최적화 (빠른 언어 체크)

**응답 예시**:
```json
{
  "routing": {
    "primary": {
      "serviceCode": "b1",
      "promptType": "article",
      "engineType": "22"
    },
    "proofreading": {
      "serviceCode": "p1",
      "promptType": "economy",
      "engineType": "22"
    },
    "regression": {
      "serviceCode": "r1",
      "promptType": "short",
      "engineType": "22"
    },
    "pipeline": ["b1", "p1", "r1"]
  },
  "orchestration": {
    "steps": [...],
    "agents_called": ["content-type-detector", "category-detector", "length-detector"]
  }
}
```

## 라우팅 규칙

### 외국어 → f1 (외신)
- 영어 또는 일본어 감지 시
- `serviceCode: "f1"`
- `promptType: "english" | "japanese"`

### 보도자료 → w1 (보도자료)
- 보도자료 키워드 감지 시
- 공공: `promptType: "public"`, `engineType: "22"`
- 기업: `promptType: "corporate"`, `engineType: "11"`

### 일반 기사 → b1 → p1 → r1 (파이프라인)
- **b1 (기사버디)**: 기사 작성
- **p1 (교열)**: 카테고리별 교열 (economy/society/general)
- **r1 (퇴고)**: 길이별 퇴고 (short/long)

## 테스트 환경

### 테스트 서버
**위치**: `frontend/agent-test-server.py`

**실행**:
```bash
cd frontend
pip install flask flask-cors
python agent-test-server.py
```

**엔드포인트**:
- `POST /api/test-language` - Language Agent 테스트
- `POST /api/test-category` - Category Agent 테스트
- `POST /api/test-length` - Length Agent 테스트
- `POST /api/test-content-type` - Content Type Agent 테스트
- `POST /api/test-supervisor` - Supervisor 전체 플로우 테스트

### 테스트 UI
**위치**: `frontend/src/features/chat/components/AgentTestPanel.jsx`

**기능**:
- 각 Agent 개별 테스트
- Supervisor 전체 플로우 테스트
- 실시간 결과 확인

## 프론트엔드 통합

### 💎 AI 버튼
**위치**: `frontend/src/features/chat/components/ChatInput.jsx`

**위치**: 채팅 입력창 하단, 파일 업로드 버튼과 웹검색 버튼 옆

**동작**:
1. 사용자가 텍스트 입력
2. 💎 AI 버튼 클릭
3. Supervisor Agent가 자동으로 최적의 서비스 선택
4. 토스트로 라우팅 결과 표시

**코드**:
```jsx
<button
  onClick={async () => {
    const response = await fetch('http://localhost:3001/api/test-supervisor', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: message })
    });
    const result = await response.json();
    // 라우팅 결과 처리
  }}
  disabled={!message.trim()}
>
  💎 AI
</button>
```

## 비용 최적화

### 빠른 언어 체크 (무료)
```python
korean_chars = sum(1 for c in text if '가' <= c <= '힣')
total_chars = len(text.replace(' ', '').replace('\n', ''))
korean_ratio = korean_chars / total_chars
quick_lang = 'korean' if korean_ratio > 0.3 else 'foreign'
```

- **한글 30% 이상**: Language Agent 호출 안 함 → 비용 절약
- **외국어**: Language Agent 호출 → 정확한 언어 감지

### Agent 호출 최소화
- 한글 텍스트: 3개 Agent 호출 (Content Type, Category, Length)
- 외국어 텍스트: 1개 Agent 호출 (Language)
- 보도자료: 1개 Agent 호출 (Content Type)

## 테스트 케이스

### 1. 일반 기사 (한글)
**입력**: "삼성전자 주가가 오늘 5% 상승했다."

**결과**:
```json
{
  "routing": {
    "pipeline": ["b1", "p1", "r1"],
    "primary": { "serviceCode": "b1" },
    "proofreading": { "serviceCode": "p1", "promptType": "economy" },
    "regression": { "serviceCode": "r1", "promptType": "short" }
  }
}
```

### 2. 공공기관 보도자료
**입력**: "정부는 오늘 새로운 경제 정책을 발표했다. 보도자료..."

**결과**:
```json
{
  "routing": {
    "serviceCode": "w1",
    "promptType": "public",
    "engineType": "22"
  }
}
```

### 3. 기업 보도자료
**입력**: "삼성전자는 HBM4를 양산 출하한다고 발표했다. 보도자료..."

**결과**:
```json
{
  "routing": {
    "serviceCode": "w1",
    "promptType": "corporate",
    "engineType": "11"
  }
}
```

### 4. 영어 외신
**입력**: "Samsung Electronics announced today..."

**결과**:
```json
{
  "routing": {
    "serviceCode": "f1",
    "promptType": "english",
    "engineType": "22"
  }
}
```

## 다음 단계

### Phase 1: 로컬 테스트 (완료 ✅)
- [x] 4개 Agent 구현
- [x] Supervisor Agent 구현
- [x] 테스트 서버 구현
- [x] 프론트엔드 통합 (💎 AI 버튼)

### Phase 2: AWS 배포 (예정)
- [ ] Lambda 함수 배포
- [ ] API Gateway 설정
- [ ] DynamoDB 테이블 생성
- [ ] 프론트엔드 엔드포인트 변경

### Phase 3: 실제 서비스 통합 (예정)
- [ ] WebSocket 메시지에 라우팅 정보 포함
- [ ] 자동 서비스 전환
- [ ] 사용자 피드백 수집

## 파일 구조

```
Agentic-Nexus/
├── backend/
│   └── agents/
│       ├── language-detector/
│       │   ├── lambda_function.py
│       │   └── agent-config.json
│       ├── category-detector/
│       │   ├── lambda_function.py
│       │   └── agent-config.json
│       ├── length-detector/
│       │   ├── lambda_function.py
│       │   └── agent-config.json
│       ├── content-type-detector/
│       │   └── lambda_function.py
│       ├── supervisor/
│       │   ├── lambda_function.py
│       │   └── agent-config.json
│       ├── test_agents.py
│       └── README.md
│
└── frontend/
    ├── agent-test-server.py          # Flask 테스트 서버
    └── src/
        └── features/
            └── chat/
                └── components/
                    ├── ChatInput.jsx          # 💎 AI 버튼
                    └── AgentTestPanel.jsx     # Agent 테스트 UI
```

## 참고

- **서비스 코드 매핑**: `README.md` 참고
- **AWS 리소스**: `README.md` 참고
- **배포 가이드**: `backend/agents/README.md` 참고
