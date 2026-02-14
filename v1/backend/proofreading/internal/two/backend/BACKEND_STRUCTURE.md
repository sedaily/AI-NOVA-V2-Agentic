# 🏗️ Backend 폴더 구조 (최종)

## 📂 디렉토리 구조

```
backend/
├── handlers/                 # Lambda 함수 진입점
│   ├── api/                 # REST API 핸들러
│   │   ├── conversation.py  # 대화 관리 API
│   │   ├── prompt.py        # 프롬프트 CRUD API
│   │   └── usage.py         # 사용량 조회 API
│   │
│   └── websocket/           # WebSocket 핸들러
│       ├── connect.py       # 연결 처리
│       ├── disconnect.py    # 연결 해제 처리
│       ├── message.py       # 메시지 처리
│       └── conversation_manager.py  # 대화 상태 관리
│
├── src/                     # 핵심 비즈니스 로직 (3-Tier)
│   ├── __init__.py
│   │
│   ├── models/              # 도메인 모델 (Data Models)
│   │   ├── __init__.py
│   │   ├── conversation.py # 대화 모델
│   │   ├── prompt.py       # 프롬프트 모델
│   │   └── usage.py        # 사용량 모델
│   │
│   ├── repositories/        # 데이터 접근 계층 (Data Access)
│   │   ├── __init__.py
│   │   ├── conversation_repository.py
│   │   ├── prompt_repository.py
│   │   └── usage_repository.py
│   │
│   ├── services/           # 비즈니스 로직 계층 (Business Logic)
│   │   ├── __init__.py
│   │   ├── conversation_service.py
│   │   ├── prompt_service.py
│   │   └── usage_service.py
│   │
│   └── config/            # 런타임 설정 (Configuration)
│       ├── __init__.py
│       ├── aws.py         # AWS 서비스 설정
│       └── database.py    # 데이터베이스 설정
│
├── lib/                   # 외부 서비스 클라이언트
│   └── bedrock_client_enhanced.py  # Bedrock AI 클라이언트
│
├── utils/                 # 공통 유틸리티
│   ├── logger.py         # 로깅 설정
│   └── response.py       # HTTP 응답 헬퍼
│
├── scripts/              # 배포 및 설정 스크립트
│   ├── 01-setup-dynamodb.sh      # DynamoDB 테이블 생성
│   ├── 02-setup-api-gateway.sh   # API Gateway 생성
│   ├── 03-setup-api-routes.sh    # API 라우트 설정
│   ├── 99-deploy-lambda.sh       # Lambda 함수 배포
│   └── README.md                 # 스크립트 사용법
│
└── requirements.txt      # Python 의존성
```

## 🎯 각 폴더의 역할

### 1. `handlers/` - Lambda 진입점

- **목적**: AWS Lambda가 직접 호출하는 함수들
- **특징**:
  - 최소한의 로직만 포함
  - 요청 파싱 및 응답 포맷팅
  - 실제 로직은 `src/services/`에 위임

```python
# 예: handlers/api/conversation.py
def handler(event, context):
    # 1. 요청 파싱
    # 2. 서비스 호출
    # 3. 응답 반환
```

### 2. `src/models/` - 도메인 모델

- **목적**: 비즈니스 엔티티 정의
- **특징**:
  - 데이터 구조 정의
  - 유효성 검증 로직
  - DynamoDB 변환 메서드

```python
# 예: src/models/conversation.py
@dataclass
class Conversation:
    conversation_id: str
    user_id: str
    messages: List[Message]
```

### 3. `src/repositories/` - 데이터 접근 계층

- **목적**: DynamoDB와의 모든 상호작용
- **특징**:
  - CRUD 작업
  - 쿼리 로직
  - 데이터베이스 추상화

```python
# 예: src/repositories/conversation_repository.py
class ConversationRepository:
    def save(self, conversation: Conversation)
    def find_by_id(self, id: str)
    def delete(self, id: str)
```

### 4. `src/services/` - 비즈니스 로직

- **목적**: 핵심 비즈니스 규칙 구현
- **특징**:
  - 복잡한 비즈니스 로직
  - 트랜잭션 관리
  - 여러 리포지토리 조합

```python
# 예: src/services/conversation_service.py
class ConversationService:
    def create_conversation(self, user_id, engine_type)
    def add_message(self, conversation_id, message)
    def generate_title(self, messages)
```

### 5. `src/config/` - 설정 관리

- **목적**: 런타임 설정 중앙화
- **특징**:
  - 환경 변수 관리
  - AWS 리소스 이름
  - 설정 유효성 검증

### 6. `lib/` - 외부 서비스 클라이언트

- **목적**: AWS 서비스 또는 외부 API 클라이언트
- **특징**:
  - Bedrock AI 클라이언트
  - S3 클라이언트 (필요시)
  - 기타 AWS 서비스 래퍼

### 7. `utils/` - 공통 유틸리티

- **목적**: 프로젝트 전반에서 사용되는 헬퍼
- **특징**:
  - 로깅 설정
  - 응답 포맷터
  - 에러 핸들러

## 🔄 요청 흐름

```
1. API Gateway → Lambda Handler
2. Handler → Service Layer
3. Service → Repository Layer
4. Repository → DynamoDB
5. Response 역순으로 반환
```

## ✅ 3-Tier Architecture 준수

### Presentation Tier (Frontend)

- React 앱 (S3/CloudFront)

### Logic Tier (Backend)

- **handlers/**: 요청 처리
- **src/services/**: 비즈니스 로직
- **lib/**: 외부 서비스 통합

### Data Tier

- **src/repositories/**: 데이터 접근
- **DynamoDB**: 실제 데이터 저장

## 📝 명명 규칙

1. **파일명**: snake_case (예: `conversation_service.py`)
2. **클래스명**: PascalCase (예: `ConversationService`)
3. **함수명**: snake_case (예: `get_conversation`)
4. **상수**: UPPER_SNAKE_CASE (예: `MAX_RETRIES`)

## 🚀 배포 시 포함되는 파일

Lambda 배포 패키지에 포함:

- `handlers/` - 모든 핸들러
- `src/` - 비즈니스 로직
- `lib/` - 외부 클라이언트
- `utils/` - 유틸리티
- `requirements.txt` - 의존성

배포 시 제외:

- `scripts/` - 배포 스크립트
- `*.md` - 문서 파일
- `__pycache__/` - Python 캐시
- `.git/` - Git 메타데이터

## 💡 Best Practices

1. **관심사 분리**: 각 계층은 자신의 책임만 처리
2. **의존성 방향**: Handler → Service → Repository → Model
3. **테스트 가능성**: 각 계층을 독립적으로 테스트 가능
4. **재사용성**: 서비스와 리포지토리는 여러 핸들러에서 재사용
5. **확장성**: 새 기능 추가 시 기존 구조 유지

## 🔧 개발 워크플로우

1. 모델 정의 (`src/models/`)
2. 리포지토리 구현 (`src/repositories/`)
3. 서비스 로직 작성 (`src/services/`)
4. 핸들러 연결 (`handlers/`)
5. 테스트 및 배포 (`scripts/`)
