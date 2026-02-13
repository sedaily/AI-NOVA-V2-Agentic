# Nexus AI Title Generation Service

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Backend Architecture](#backend-architecture)
6. [Frontend Architecture](#frontend-architecture)
7. [Infrastructure Components](#infrastructure-components)
8. [Environment Variables](#environment-variables)
9. [API Documentation](#api-documentation)
10. [Deployment Guide](#deployment-guide)
11. [Monitoring & Logging](#monitoring--logging)
12. [Security](#security)
13. [Performance Optimization](#performance-optimization)
14. [Contributing](#contributing)
15. [License](#license)

## Overview

Nexus는 AI 기반 제목 생성 서비스로, AWS Bedrock Claude Sonnet 모델을 활용한 실시간 대화형 인터페이스를 제공합니다. 3-Tier 아키텍처를 기반으로 구축되어 확장성, 유지보수성, 보안성을 보장합니다.

### Key Features

- **실시간 AI 대화**: WebSocket 기반 스트리밍 응답
- **다중 엔진 지원**: T5, H8 모델
- **프롬프트 관리**: 관리자 커스터마이징 프롬프트(실시간 성능 업데이트) CRUD
- **사용량 추적**: 토큰 사용량 및 비용 모니터링
- **엔터프라이즈 보안**: AWS Cognito 인증

## System Architecture

### 3-Tier Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Tier                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  React SPA (S3 + CloudFront)                        │   │
│  │  - Component-Based UI                               │   │
│  │  - Container-Presenter Pattern                      │   │
│  │  - WebSocket Client                                 │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       Logic Tier                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  API Gateway (REST + WebSocket)                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                              │                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Lambda Functions                                   │   │
│  │  - Conversation Handler                             │   │
│  │  - Prompt CRUD Handler                              │   │
│  │  - Usage Tracker                                    │   │
│  │  - WebSocket Handlers                               │   │
│  └─────────────────────────────────────────────────────┘   │
│                              │                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  External Services                                  │   │
│  │  - Bedrock AI (Claude Sonnet)                       │   │
│  │  - Cognito (Authentication)                         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        Data Tier                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  DynamoDB Tables                                    │   │
│  │  - conversations                                    │   │
│  │  - prompts                                          │   │
│  │  - usage                                            │   │
│  │  - websocket-connections                            │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Request Flow Diagram

```
User Request → CloudFront → S3 (React App)
                    │
                    ▼
            API Gateway (REST/WS)
                    │
          ┌─────────┴──────────┐
          │                    │
    Lambda Function      WebSocket Handler
          │                    │
    Service Layer        Bedrock Streaming
          │                    │
    Repository Layer           │
          │                    │
      DynamoDB ← ─ ─ ─ ─ ─ ─ ─┘
```

## Technology Stack

### Frontend

- **Framework**: React 18.2
- **Build Tool**: Vite 4.4
- **Styling**: Tailwind CSS 3.3
- **State Management**: React Context API
- **WebSocket**: Native WebSocket API
- **Authentication**: AWS Amplify Auth
- **UI Components**: Heroicons, Lucide React
- **Animation**: Framer Motion
- **Charts**: Recharts

### Backend

- **Runtime**: Python 3.9
- **Framework**: AWS Lambda (Serverless)
- **API**: AWS API Gateway (REST + WebSocket)
- **AI Model**: AWS Bedrock Claude Sonnet 4
- **Database**: DynamoDB
- **Authentication**: AWS Cognito
- **Monitoring**: CloudWatch

### Infrastructure

- **IaC**: Shell Scripts (Future: Terraform/CDK)
- **CDN**: CloudFront
- **Storage**: S3
- **DNS**: Route 53
- **SSL**: AWS Certificate Manager

## Project Structure

```
nexus_0822/
├── frontend/                   # Presentation Layer
│   ├── src/
│   │   ├── components/        # UI Components
│   │   │   ├── common/       # Shared Components
│   │   │   └── chat/         # Chat-specific Components
│   │   ├── features/         # Feature Modules
│   │   │   └── chat/
│   │   │       ├── containers/  # Smart Components
│   │   │       └── presenters/  # Dumb Components
│   │   ├── services/         # API & WebSocket Services
│   │   ├── hooks/           # Custom React Hooks
│   │   ├── utils/           # Utility Functions
│   │   └── styles/          # Global Styles
│   └── scripts/             # Deployment Scripts
│
├── backend/                    # Logic Layer
│   ├── handlers/              # Lambda Entry Points
│   │   ├── api/              # REST API Handlers
│   │   └── websocket/        # WebSocket Handlers
│   ├── src/                  # Core Business Logic
│   │   ├── models/           # Domain Models
│   │   ├── repositories/    # Data Access Layer
│   │   ├── services/        # Business Logic Layer
│   │   └── config/          # Configuration
│   ├── lib/                 # External Service Clients
│   ├── utils/               # Shared Utilities
│   └── scripts/             # Deployment Scripts
│
└── infrastructure/             # Infrastructure Layer
    ├── aws/                   # AWS Service Configurations
    │   ├── api-gateway/      # API Definitions
    │   ├── bedrock/          # AI Model Config
    │   ├── cloudfront/       # CDN Config
    │   ├── cognito/          # Auth Config
    │   ├── dynamodb/         # Database Schema
    │   ├── iam/              # Permissions
    │   ├── lambda/           # Function Config
    │   ├── route53/          # DNS Config
    │   └── s3/               # Storage Config
    └── scripts/              # Infrastructure Scripts
```

## Backend Architecture

### Domain Models

```python
# src/models/conversation.py
@dataclass
class Message:
    role: str  # 'user' | 'assistant'
    content: str
    timestamp: str
    token_count: Optional[int]

@dataclass
class Conversation:
    conversation_id: str
    user_id: str
    engine_type: str  # 'T5' | 'H8'
    title: Optional[str]
    messages: List[Message]
    created_at: str
    updated_at: str
    total_tokens: int
```

### Service Layer Pattern

```python
# src/services/conversation_service.py
class ConversationService:
    def __init__(self):
        self.repository = ConversationRepository()
        self.bedrock_client = BedrockClient()

    def create_conversation(self, user_id: str, engine_type: str)
    def add_message(self, conversation_id: str, message: Message)
    def generate_ai_response(self, messages: List[Message])
    def calculate_usage(self, conversation: Conversation)
```

### Repository Pattern

```python
# src/repositories/conversation_repository.py
class ConversationRepository:
    def save(self, conversation: Conversation) -> Conversation
    def find_by_id(self, conversation_id: str) -> Optional[Conversation]
    def find_by_user(self, user_id: str) -> List[Conversation]
    def delete(self, conversation_id: str) -> bool
    def update(self, conversation: Conversation) -> Conversation
```

## Frontend Architecture

### Component Hierarchy

```
App
├── AuthProvider
├── Router
│   ├── PublicRoute
│   │   └── LoginPage
│   └── PrivateRoute
│       ├── ChatLayout
│       │   ├── Sidebar
│       │   │   ├── ConversationList
│       │   │   └── EngineSelector
│       │   └── ChatContainer
│       │       ├── ChatPresenter
│       │       │   ├── MessageList
│       │       │   ├── InputArea
│       │       │   └── TypingIndicator
│       │       └── ChatContainer (Logic)
│       └── SettingsPage
```

### Service Architecture

```javascript
// services/websocket.js
class WebSocketService {
    constructor(url, options) {
        this.url = url;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    connect(token, conversationId)
    send(action, data)
    onMessage(callback)
    reconnect()
    disconnect()
}
```

## Infrastructure Components

### AWS Services Configuration

#### DynamoDB Tables

| Table                 | Partition Key   | Sort Key | GSI        | TTL       |
| --------------------- | --------------- | -------- | ---------- | --------- |
| conversations         | conversation_id | -        | user-index | -         |
| prompts               | prompt_id       | -        | user-index | -         |
| usage                 | user_id         | date     | -          | -         |
| websocket-connections | connection_id   | -        | user-index | ttl (24h) |

#### Lambda Functions

| Function             | Memory  | Timeout | Trigger     | Purpose             |
| -------------------- | ------- | ------- | ----------- | ------------------- |
| conversation-api     | 512 MB  | 30s     | API Gateway | Conversation CRUD   |
| prompt-crud          | 512 MB  | 30s     | API Gateway | Prompt management   |
| usage-handler        | 256 MB  | 30s     | API Gateway | Usage tracking      |
| websocket-connect    | 256 MB  | 10s     | WebSocket   | Connection handling |
| websocket-disconnect | 256 MB  | 10s     | WebSocket   | Cleanup             |
| websocket-message    | 1024 MB | 300s    | WebSocket   | AI streaming        |

#### API Gateway Endpoints

**REST API**

```
GET    /conversations
POST   /conversations
GET    /conversations/{id}
PUT    /conversations/{id}
DELETE /conversations/{id}

GET    /prompts
POST   /prompts
GET    /prompts/{id}
PUT    /prompts/{id}
DELETE /prompts/{id}

GET    /usage
```

**WebSocket API**

```
$connect    - Connection establishment
$disconnect - Connection cleanup
$default    - Message routing
sendMessage - User message handling
```

## Environment Variables

### Backend Environment Variables

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=887078546492

# DynamoDB Tables
CONVERSATIONS_TABLE=nexus-conversations
PROMPTS_TABLE=nexus-prompts
USAGE_TABLE=nexus-usage
WEBSOCKET_TABLE=nexus-websocket-connections

# Bedrock Configuration
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
BEDROCK_MAX_TOKENS=16384
BEDROCK_TEMPERATURE=0.81
BEDROCK_TOP_P=0.9
BEDROCK_TOP_K=50

# API Gateway
REST_API_URL=https://api.nexus.com
WEBSOCKET_API_URL=wss://ws.nexus.com

# Cognito
COGNITO_USER_POOL_ID=us-east-
COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxx

# Monitoring
LOG_LEVEL=INFO
METRICS_ENABLED=true
```

### Frontend Environment Variables

```bash
# API Configuration
VITE_API_BASE_URL=https://api.nexus.com
VITE_WS_URL=wss://ws.nexus.com

# Authentication
VITE_COGNITO_USER_POOL_ID=us-east-
VITE_COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxx
VITE_AWS_REGION=us-east-1

# Feature Flags
VITE_ENABLE_DEBUG=false
VITE_ENABLE_ANALYTICS=true
```

## API Documentation

### REST API

#### Create Conversation

```http
POST /conversations
Content-Type: application/json

{
    "userId": "user123",
    "engineType": "T5",
    "title": "New Conversation"
}

Response: 201 Created
{
    "conversationId": "conv_abc123",
    "userId": "user123",
    "engineType": "T5",
    "title": "New Conversation",
    "messages": [],
    "createdAt": "2024-01-01T00:00:00Z"
}
```

### WebSocket API

#### Send Message

```javascript
{
    "action": "sendMessage",
    "conversationId": "conv_abc123",
    "message": {
        "role": "user",
        "content": "Hello AI"
    },
    "engineType": "T5"
}
```

#### Receive Stream

```javascript
{
    "type": "stream",
    "conversationId": "conv_abc123",
    "chunk": "Hello! How can I",
    "isComplete": false
}
```

## Deployment Guide

### Quick Start

```bash
# Clone repository
git clone https://github.com/your-org/nexus.git
cd nexus

# Deploy infrastructure
cd infrastructure/scripts
./deploy-all.sh nexus nexus.com production

# Deploy backend
cd ../../backend/scripts
./99-deploy-lambda.sh

# Deploy frontend
cd ../../frontend
npm install
npm run build
aws s3 sync dist/ s3://nexus-frontend
```

### Production Deployment

1. **Infrastructure Setup**

   ```bash
   infrastructure/scripts/deploy-all.sh [service-name] [domain] [environment]
   ```

2. **Backend Deployment**

   ```bash
   backend/scripts/99-deploy-lambda.sh
   ```

3. **Frontend Deployment**
   ```bash
   frontend/scripts/03-deploy-to-s3.sh
   frontend/scripts/04-create-cloudfront.sh
   ```

## Monitoring & Logging

### CloudWatch Dashboards

- **API Gateway Metrics**: 4XX/5XX errors, latency, request count
- **Lambda Metrics**: Invocations, errors, duration, concurrent executions
- **DynamoDB Metrics**: Read/Write capacity, throttles, user errors
- **WebSocket Metrics**: Active connections, message rate, connection duration

### Log Groups

```
/aws/lambda/nexus-conversation-api
/aws/lambda/nexus-websocket-message
/aws/apigateway/nexus-rest-api
/aws/apigateway/nexus-websocket-api
```

### Alarms

- API Error Rate > 5%
- Lambda Error Rate > 1%
- Lambda Duration > 80% of timeout
- DynamoDB Throttling > 0
- WebSocket Connections > 1000

## Security

### Authentication & Authorization

- **User Authentication**: AWS Cognito User Pools
- **API Authorization**: JWT tokens via Cognito
- **WebSocket Auth**: Query parameter token validation

### Data Protection

- **Encryption at Rest**: DynamoDB encryption enabled
- **Encryption in Transit**: HTTPS/WSS only
- **Content Filtering**: Bedrock Guardrails enabled
- **Input Validation**: API Gateway request validators

### Network Security

- **CDN**: CloudFront with Origin Access Identity
- **API**: Regional endpoints with throttling
- **CORS**: Restrictive origin policies

### Compliance

- **Data Retention**: TTL on temporary data
- **Audit Logging**: CloudTrail enabled
- **Access Control**: IAM least privilege principle

## Performance Optimization

### Frontend Optimization

- **Code Splitting**: Route-based lazy loading
- **Bundle Optimization**: Tree shaking, minification
- **Caching Strategy**: CloudFront caching headers
- **Image Optimization**: WebP format, lazy loading

### Backend Optimization

- **Lambda Optimization**: Memory tuning, provisioned concurrency
- **DynamoDB Optimization**: On-demand vs provisioned capacity
- **API Gateway Caching**: Response caching for GET requests
- **Connection Pooling**: Reuse database connections

### Cost Optimization

- **Auto Scaling**: DynamoDB auto-scaling
- **Reserved Capacity**: Lambda savings plans
- **S3 Lifecycle**: Archive old data
- **CloudWatch Logs**: Retention policies

## Contributing

### Development Setup

```bash
# Backend development
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend development
cd frontend
npm install
npm run dev
```

### Code Standards

- **Python**: PEP 8 compliance
- **JavaScript**: ESLint + Prettier
- **Git**: Conventional commits
- **Testing**: Unit tests required

### Pull Request Process

1. Fork repository
2. Create feature branch
3. Implement changes
4. Add tests
5. Update documentation
6. Submit pull request

## License

MIT License - See [LICENSE](LICENSE) file for details

---

**Version**: 1.0.0  
**Last Updated**: 2024-09-05  
**Maintainers**: Backend Team, Frontend Team  
**Contact**: support@nexus.com
