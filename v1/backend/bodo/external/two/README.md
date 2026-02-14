# w1.sedaily.ai
AI Press Release Service - Claude Opus 4.5 based real-time press release writing assistant

Last Updated: 2025-12-21

## Overview
w1.sedaily.ai is an AI-powered press release writing assistant for Seoul Economic Daily journalists. It features real-time WebSocket communication, native web search integration, 12-step systematic prompts, and prompt caching for cost optimization.

Live: https://w1.sedaily.ai

## Features
- Real-time Streaming: WebSocket-based streaming responses
- Web Search: Anthropic's native web search integration (web_search_20250305)
- Prompt Caching: 90% cost reduction with ephemeral cache
- DynamoDB Caching: Permanent prompt cache in Lambda container
- Multiple AI Providers: Anthropic API primary, Bedrock fallback
- 12-Step System Prompt: Comprehensive journalist-focused prompt structure
- Multi-Engine Support: Multiple prompt templates (engine types 11, 22, 33)
- Korean Language: Optimized for Korean press release writing

## Architecture
```
Frontend (React)
  ↓
CloudFront (E10S6CKR5TLUBG)
  ↓
S3 (w1-frontend)

WebSocket Flow:
User → API Gateway WebSocket (prsebeg7ub) → Lambda (w1-websocket-message)
  ↓
Anthropic Claude Opus 4.5 (with web search)
  ↓
Streaming Response → User

REST API Flow:
User → API Gateway REST (16ayefk5lc) → Lambda (conversation/prompt/usage)
  ↓
DynamoDB (conversations, prompts, usage tracking)
```

## Project Structure
```
.
├── README.md
├── PROMPT_CACHING_OPTIMIZATION.md
├── backend/
│   ├── handlers/
│   │   ├── api/              # REST API handlers
│   │   └── websocket/        # WebSocket handlers
│   ├── lib/
│   │   ├── anthropic_client.py       # Anthropic API client
│   │   ├── bedrock_client.py         # Bedrock fallback
│   │   └── bedrock_client_enhanced.py # 12-step system prompt
│   ├── services/
│   │   └── websocket_service.py      # Main WebSocket service
│   ├── src/
│   │   ├── config/
│   │   ├── models/
│   │   └── repositories/
│   ├── utils/
│   └── requirements.txt
├── config/
├── frontend/
│   └── src/
└── w1-scripts/
    ├── config.sh             # Environment configuration
    ├── deploy-backend.sh     # Backend deployment
    └── deploy-frontend.sh    # Frontend deployment
```

## Quick Start

### Prerequisites
- AWS CLI configured
- Node.js 18+
- Python 3.11+
- AWS Account: 887078546492

### Deployment
```bash
# Backend deployment (Lambda functions)
cd w1-scripts
./deploy-backend.sh

# Frontend deployment (React app)
./deploy-frontend.sh
```

## Current Deployment
Status: Production Ready

Updated: 2025-12-20

## URLs
| Resource | URL |
|----------|-----|
| Primary Domain | https://w1.sedaily.ai |
| CloudFront | https://d9am5o27m55dc.cloudfront.net |
| REST API | https://16ayefk5lc.execute-api.us-east-1.amazonaws.com/prod |
| WebSocket API | wss://prsebeg7ub.execute-api.us-east-1.amazonaws.com/prod |

## AWS Resources (us-east-1)

### Lambda Functions
| Function | Purpose |
|----------|---------|
| w1-websocket-message | Main chat handler (Claude API + Web Search) |
| w1-websocket-connect | WebSocket connection handler |
| w1-websocket-disconnect | WebSocket disconnect handler |
| w1-conversation-api | Conversation CRUD |
| w1-prompt-crud | Prompt management |
| w1-usage-handler | Usage tracking |

### DynamoDB Tables
| Table | Purpose |
|-------|---------|
| w1-conversations | Chat history |
| w1-messages | Individual messages |
| w1-prompts | System prompts |
| w1-usage | API usage tracking |
| w1-connections | WebSocket connections |

### Other Resources
| Resource | Value |
|----------|-------|
| S3 Bucket | w1-frontend |
| CloudFront Distribution | E10S6CKR5TLUBG (d9am5o27m55dc.cloudfront.net) |
| Secrets Manager | bodo-v1 (Anthropic API key) |
| IAM Role | w1-lambda-execution-role |

## AI Configuration
| Setting | Value |
|---------|-------|
| Primary Provider | Anthropic API |
| Default Model | claude-opus-4-5-20251101 (Opus 4.5) |
| Available Models | Opus 4.5, Sonnet 4.5, Haiku 4.5 |
| Model Selection | UI 드롭다운으로 선택 가능 |
| Max Tokens | 4096 |
| Temperature | 0.3 |
| Fallback | AWS Bedrock |
| Web Search | Enabled (web_search_20250305) |
| Prompt Caching | Enabled |

## Change History

### Phase 10: Claude Model Selection Feature (2026-01-01)
- **모델 선택 드롭다운 추가**: Opus 4.5, Sonnet 4.5, Haiku 4.5 선택 가능
- Frontend 업데이트:
  - `ChatInput.jsx`: 모델 선택 드롭다운 UI 추가 (showModelSelector prop)
  - `ChatPage.jsx`: 모델 선택 상태 관리 및 드롭다운 추가
  - `MainContent.jsx`: showModelSelector={true} 전달
  - `useWebSocketChat.js`: selectedModel 파라미터 지원
  - `websocketService.js`: modelId를 WebSocket 메시지에 포함
- Backend 업데이트:
  - `anthropic_client.py`: stream_response()에 model_id 파라미터 추가
  - `websocket_service.py`: model_id 파라미터 전달
  - `message.py`: WebSocket 메시지에서 modelId 추출
- 드롭다운 위치: 아래쪽 우측 (top-full mt-2 right-0)
- localStorage에 선택된 모델 저장 (세션 유지)
- 참조 구현: services/foreign/external/two

### Phase 9: Final Testing & Deployment Verification (2025-12-21)
- **Production deployment verified** - All components tested and working
- Backend: 6/6 Lambda functions deployed successfully
- Frontend: S3 + CloudFront deployment complete (72 files)
- Authentication: Cognito login verified
- HTTP Status: 200 OK
- Fixed `deploy-frontend.sh` to support non-interactive execution (`-y` flag)
- All deployment scripts tested and verified

### Phase 8: Cost Optimization & Code Cleanup (2025-12-20)
- Deployed Anthropic API prompt caching to all Lambda functions
- 90% cost reduction on cache hits ($0.50/1M vs $5.00/1M)
- Fixed Anthropic API to use 12-step `create_enhanced_system_prompt()`
- Previously used simple `_build_system_prompt()` method
- Removed unused configs from aws.py:
  - `S3_CONFIG`, `CLOUDWATCH_CONFIG`, `COGNITO_CONFIG`, `GUARDRAIL_CONFIG`
- Deleted unused backend modules:
  - `src/services/prompt_service.py`, `usage_service.py`
  - `src/repositories/prompt_repository.py`, `usage_repository.py`
  - `src/models/prompt.py`, `usage.py`
- Removed deprecated `_build_system_prompt()` method from websocket_service.py
- Created work-logs/ directory for development tracking
- Added comprehensive .gitignore
- Deleted test files: `test_current_issues.py`, `test_prompt_caching.py`, `test_web_search.py`
- Deleted outdated: `upgrade-scripts/`, `SCRIPT_STATUS_SUMMARY.md`
- README restructured to reference format with full change history

### Phase 7: Web Search Feature (2025-12-14)
- Added Anthropic native web_search_20250305 tool
- Implemented citation formatting with trust icons
- Enhanced date handling for search results
- Web search engine: Brave Search
- Max uses: 5 per request
- All Lambda functions updated with new code

### Phase 6: Claude Opus 4.5 Migration (2024-11)
- Migrated from AWS Bedrock to Anthropic Direct API
- Model: `claude-opus-4-5-20251101` (Claude Opus 4.5)
- Added dual AI provider support:
  - Primary: Anthropic API (direct)
  - Fallback: AWS Bedrock (claude-sonnet-4)
- Integrated Secrets Manager for API key storage
- Added `anthropic_client.py`:
  - Streaming response support
  - Secrets Manager integration
  - Web search tool configuration
- Updated `bedrock_client_enhanced.py` as fallback

### Phase 5: 12-Step System Prompt (2024-10)
- Created `create_enhanced_system_prompt()` function
- CoT-based 12-step systematic prompt structure:
  1. IDENTITY & MISSION - Role and goal definition
  2. SECURITY RULES - Input validation and safety
  3. CORE PROCESS - 5-step execution workflow
  4. JOURNALIST FEATURES - Press release specific
  5. KOREAN LANGUAGE RULES - Language optimization
  6. OUTPUT RULES - Format guidelines
  7. TIME-SENSITIVE HANDLING - Current events
  8. ETHICS - Journalism ethics
  9. WEB SEARCH CITATION - Source formatting
  10. QUALITY CHECK - Output validation
  11. NEVER DO THIS - Prohibited actions
  12. REMEMBER - Key reminders
- Engine type support: 11, 22, 33 variants

### Phase 4: WebSocket Real-time Chat (2024-10)
- Implemented WebSocket API via API Gateway
- Created WebSocket Lambda handlers:
  - `connect.py` - Connection management
  - `message.py` - Chat message processing
  - `disconnect.py` - Cleanup on disconnect
  - `conversation_manager.py` - Conversation state
- DynamoDB tables for WebSocket:
  - `w1-connections` - Active connections
  - `w1-conversations` - Chat history
- Streaming response support for real-time AI output
- Connection state management with DynamoDB

### Phase 3: REST API Development (2024-09)
- Created REST API handlers:
  - `conversation.py` - Conversation CRUD operations
  - `prompt.py` - System prompt management
  - `usage.py` - Usage tracking and analytics
- DynamoDB tables:
  - `w1-prompts` - System prompts storage
  - `w1-usage` - API usage metrics
  - `w1-messages` - Message history
- API Gateway REST API configuration
- CORS configuration for frontend

### Phase 2: Frontend Development (2024-09)
- React application setup
- TypeScript configuration
- Tailwind CSS styling
- Chat UI components
- WebSocket client integration

### Phase 1: Infrastructure Setup (2024-09)
- AWS infrastructure provisioning
- S3 bucket: `w1-frontend`
- CloudFront distribution: `d9am5o27m55dc`
- Custom domain: `w1.sedaily.ai`
- SSL certificate configuration
- API Gateway setup (REST + WebSocket)
- Lambda function deployment
- DynamoDB table creation
- IAM role configuration

## Deployment Guide

### Deploy Scripts
```bash
cd w1-scripts

# Backend deployment (Lambda functions)
./deploy-backend.sh

# Frontend deployment (React app)
./deploy-frontend.sh
```

### Environment Configuration
Settings managed in `w1-scripts/config.sh`:
- AWS resource IDs
- Lambda function names
- API Gateway endpoints
- S3/CloudFront configuration

### Log Monitoring
```bash
# Real-time Lambda logs
aws logs tail /aws/lambda/w1-websocket-message --follow
```

## Cost Optimization

### Prompt Caching (90% savings)
- System prompt cached with ephemeral TTL
- Cache hit: $0.50/1M tokens vs $5.00/1M tokens
- Beta header: `anthropic-beta: prompt-caching-2024-07-31`

### DynamoDB Caching
- Permanent in-memory cache in Lambda container
- DB queries only on cold start
- Cache management: `clear_prompt_cache()`, `get_cache_stats()`

### Estimated Monthly Cost
| Service | Cost |
|---------|------|
| Anthropic Claude | ~$50-100 |
| Lambda | ~$15 |
| DynamoDB | ~$5 |
| S3/CloudFront | ~$5 |
| **Total** | **~$75-125/month** |

## Tech Stack

### Backend
- Python 3.11
- AWS Lambda
- Anthropic Claude Opus 4.5
- DynamoDB
- API Gateway (REST + WebSocket)
- AWS Bedrock (fallback)

### Frontend
- React
- TypeScript
- Tailwind CSS
- S3 + CloudFront

### Infrastructure
- AWS (us-east-1)
- Secrets Manager
- CloudWatch
- IAM

## Monitoring

### CloudWatch Metrics
- Lambda invocations and errors
- API Gateway request count
- DynamoDB read/write capacity
- WebSocket connection count

### Key Log Messages
```
Cache HIT for [engine] - DB query skipped (permanent cache)
Cache MISS for [engine] - fetching from DB
API Cost: $X.XXXXXX | input: X, output: X, cache_read: X, cache_write: X
Permanently cached prompt for [engine]
```

### Cost Tracking
AWS Cost Explorer with tag: `w1`

## Troubleshooting

### Common Issues

1. **WebSocket not connecting**
   - Check Lambda logs: `./monitor-logs.sh websocket`
   - Verify API Gateway WebSocket stage is deployed
   - Check connection table in DynamoDB

2. **AI responses not working**
   - Check Anthropic API key in Secrets Manager (bodo-v1)
   - Verify Lambda environment variables
   - Check fallback to Bedrock is working

3. **Frontend not updating**
   - Run CloudFront cache invalidation
   - Check S3 bucket sync
   - Clear browser cache

4. **Prompt cache not working**
   - Verify `ENABLE_PROMPT_CACHING=true`
   - Check cache_control in API request
   - Review Lambda logs for cache hit/miss

### Rollback
```bash
# Redeploy previous version
git checkout <commit-hash> -- backend/
cd w1-scripts && ./deploy-backend.sh
```

## Security Notes
- **Safe Prefix**: Only modify w1-* resources
- **Forbidden**: Never modify f1, p2, g2, b1 resources
- **API Keys**: Managed via AWS Secrets Manager (bodo-v1)
- **IAM Role**: w1-lambda-execution-role

## Documentation
- [Prompt Caching Optimization](PROMPT_CACHING_OPTIMIZATION.md)

## License
Proprietary - Seoul Economic Daily
