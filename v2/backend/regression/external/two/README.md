# r1.sedaily.ai
AI Column Writing Service - Claude Opus 4.5 based real-time column generation with prompt caching

Last Updated: 2026-01-01

## Overview
SEDAILY-COLUMN is an AI-powered column writing service for Seoul Economic Daily. Built on Anthropic Claude Opus 4.5 with real-time WebSocket streaming and prompt caching for cost optimization.

Live: https://r1.sedaily.ai

## Features
- Real-time Chat: WebSocket-based streaming responses
- **Dynamic Model Selection: Switch between Claude 4.5 models per message**
- **Prompt Caching: 67% cost reduction with Anthropic ephemeral cache**
- DynamoDB Caching: Permanent prompt cache in Lambda container
- Multiple AI Providers: Anthropic API primary, Bedrock fallback
- Multiple Engines: C1 (Basic), C2 (Opinion), C7 (Creative) column styles
- PDF/Audio Upload: Document processing support

## Architecture
```
Frontend (React + Vite)
  |
CloudFront (CDN)
  |
S3 (Static Hosting)

WebSocket Flow:
User -> API Gateway WebSocket -> Lambda (message handler)
  |
Anthropic Claude Opus 4.5
  |
Streaming Response -> User

REST API Flow:
User -> API Gateway REST -> Lambda (conversation/prompt/usage)
  |
DynamoDB (conversations, prompts, usage tracking)
```

## Project Structure
```
.
├── README.md
├── AWS_INFRASTRUCTURE_MAP.md
├── deploy-backend.sh          # Backend deployment
├── deploy-column-frontend.sh  # Frontend deployment
├── backend/
│   ├── handlers/              # Lambda handlers
│   │   ├── api/              # REST API handlers
│   │   └── websocket/        # WebSocket handlers
│   ├── lib/                  # anthropic_client, bedrock_client
│   ├── services/             # websocket_service
│   ├── src/                  # Core business logic
│   │   ├── models/
│   │   ├── repositories/
│   │   └── services/
│   ├── utils/
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── features/         # auth, chat, dashboard
    │   ├── shared/
    │   └── config.js
    ├── public/
    ├── package.json
    └── vite.config.js
```

## Quick Start

### Prerequisites
- AWS CLI configured
- Node.js 18+
- Python 3.11+
- AWS Account: 887078546492

### Deployment
```bash
# Full deployment (frontend + backend)
./deploy-backend.sh && ./deploy-column-frontend.sh

# Frontend only
./deploy-column-frontend.sh

# Backend only
./deploy-backend.sh
```

## Current Deployment
Status: Production Ready

Updated: 2025-12-21

## URLs
| Resource | URL |
|----------|-----|
| Primary Domain | https://r1.sedaily.ai |
| REST API | https://t75vorhge1.execute-api.us-east-1.amazonaws.com/prod |
| WebSocket API | wss://ebqodb8ax9.execute-api.us-east-1.amazonaws.com/production |

## AWS Resources (us-east-1)

### Lambda Functions
| Function | Purpose |
|----------|---------|
| sedaily-column-websocket-connect | WebSocket connection handler |
| sedaily-column-websocket-message | Main chat handler (Claude API) |
| sedaily-column-websocket-disconnect | WebSocket disconnect handler |
| sedaily-column-conversation-api | Conversation CRUD |
| sedaily-column-prompt-crud | Prompt management |
| sedaily-column-usage-handler | Usage tracking |

### DynamoDB Tables
| Table | Purpose |
|-------|---------|
| sedaily-column-conversations | Chat history |
| sedaily-column-prompts | System prompts |
| sedaily-column-files | File metadata |
| sedaily-column-usage | Usage statistics |
| sedaily-column-websocket-connections | Active connections |

### Other Resources
| Resource | ID/Name |
|----------|---------|
| S3 Bucket | sedaily-column-frontend |
| CloudFront Distribution | EH9OF7IFDTPLW (d3ck0lkvawjvhg.cloudfront.net) |
| Secrets Manager | regression-v1 (Anthropic API key) |

## AI Configuration
| Setting | Value |
|---------|-------|
| Primary Provider | Anthropic API |
| Default Model | claude-opus-4-5-20251101 |
| Max Tokens | 4096 |
| Temperature | 0.7 |
| Fallback | AWS Bedrock |

### Available Models (Dynamic Selection)
| Model ID | Name | Description |
|----------|------|-------------|
| claude-opus-4-5-20251101 | Opus 4.5 | 복잡한 작업에 최적 (Default) |
| claude-sonnet-4-5-20250929 | Sonnet 4.5 | 일상적 작업에 최고 |
| claude-haiku-4-5-20251001 | Haiku 4.5 | 빠른 답변에 최적 |

## Change History

### Phase 6: Dynamic Model Selection (2026-01-01)
- **Added dynamic Claude model selection feature**
- Users can switch between Claude 4.5 models per message:
  - Opus 4.5 (Default): Complex tasks
  - Sonnet 4.5: Daily tasks
  - Haiku 4.5: Quick responses
- Frontend changes:
  - `ChatInput.jsx`: Model selector dropdown with Korean descriptions
  - `ChatPage.jsx`: Model state management with localStorage persistence
  - `MainContent.jsx`: Model state and change handler
  - `websocketService.js`: modelId parameter in WebSocket payloads
- Backend changes:
  - `message.py`: Extract modelId from request (camelCase/snake_case support)
  - `websocket_service.py`: Pass model_id to stream_response
  - `anthropic_client.py`: Use dynamic model_id in API requests
- UI Design: Korean descriptions, checkmarks, toast notifications
- Default model: claude-opus-4-5-20251101 (Opus 4.5)

### Phase 5: Final Testing & Deployment Verification (2025-12-21)
- **Production deployment verified** - All components tested and working
- Backend: 6/6 Lambda functions deployed successfully
- Frontend: S3 + CloudFront deployment complete
- Authentication: Cognito login verified
- HTTP Status: 200 OK
- All deployment scripts tested and verified

### Phase 4: Project Cleanup & Structure Optimization (2025-12-21)
- **Major cleanup**: Removed ~40 unused files and directories
- Deleted obsolete documentation:
  - `PROMPT_CACHING_IMPLEMENTATION.md` (Bedrock-based, outdated)
  - `PROMPT_CACHING_PERFORMANCE.md` (Bedrock-based, outdated)
  - `README_PROMPT_CACHING.md` (duplicate)
  - `CACHING_SUMMARY.md` (duplicate)
  - `PROJECT_STRUCTURE_ANALYSIS.md` (one-time analysis)
  - `ANTHROPIC_API_KEY_SETUP.md` (referenced deleted scripts)
  - `MAINTENANCE_GUIDE.md` (referenced deleted scripts)
  - `WEB_SEARCH_SETUP.md` (referenced deleted scripts)
- Deleted directories:
  - `admin-dashboard/` (demo dashboard, unused)
  - `infrastructure/` (initial setup docs, AWS already configured)
  - `backend/scripts/` (moved deploy script to root)
- Deleted build artifacts:
  - `*.zip` files (10 Lambda packages)
  - `__pycache__/` directories
  - `node_modules/`, `dist/` (regenerated on build)
- Reorganized deployment scripts:
  - `deploy-backend.sh` (moved from `backend/scripts/05-deploy-lambda.sh`)
  - `deploy-column-frontend.sh` (kept at root)
- Cleaned frontend:
  - Removed `config.column.js` (unused duplicate)
  - Removed `update-to-column.sh` (one-time migration)
  - Removed `scripts/` folder (initial setup)
- Final structure: Minimal, clean, production-focused

### Phase 3: Anthropic Prompt Caching Fix (2025-12-21)
- **Fixed Anthropic Prompt Caching** - 67% cost reduction achieved
- Issue: `cache_control` had invalid `ttl` parameter
  - Fixed to `{"type": "ephemeral"}` (Anthropic managed TTL)
- Issue: Dynamic values in system prompt invalidating cache
  - `{{current_datetime}}`, `{{session_id}}` changed every request
  - Fixed: Static values for system prompt, dynamic context in user message
- Issue: Conversation context prepended to system prompt
  - Fixed: Moved to user message for cache preservation
- SSE streaming parser improved for `message_start`/`message_stop` events
- Logger fix: `logging.getLogger()` -> `setup_logger()` for CloudWatch output
- Test results (4 tests):
  - Test 1 (Cache MISS): 7,232 tokens cached
  - Test 2-4 (Cache HIT): 100% hit rate
  - Cost savings: ~67% per request

### Phase 2: Claude 4.5 Opus Migration (2025-12-07)
- Migrated from AWS Bedrock to Anthropic Direct API
- Model: `claude-opus-4-5-20251101` (Claude Opus 4.5)
- Added dual AI provider support:
  - Primary: Anthropic API (direct)
  - Fallback: AWS Bedrock (claude-sonnet-4)
- Added `anthropic_client.py`:
  - Streaming response support
  - Secrets Manager integration
- Updated `bedrock_client_enhanced.py` as fallback

### Phase 1: Initial Setup (2024-09)
- Project initialization with React + Vite frontend
- AWS infrastructure: S3, CloudFront, API Gateway, Lambda, DynamoDB
- WebSocket real-time chat implementation
- REST API for conversation/prompt/usage management
- Multiple engine support: C1, C2, C7 column styles

## Deployment Guide

### Deploy Commands
```bash
# Backend (Lambda functions)
./deploy-backend.sh

# Frontend (S3 + CloudFront)
./deploy-column-frontend.sh

# Full deployment
./deploy-backend.sh && ./deploy-column-frontend.sh
```

### Environment Configuration
Lambda environment variables:
```json
{
  "USE_ANTHROPIC_API": "true",
  "ANTHROPIC_SECRET_NAME": "regression-v1",
  "ANTHROPIC_MODEL_ID": "claude-opus-4-5-20251101",
  "FALLBACK_TO_BEDROCK": "true"
}
```

### Log Monitoring
```bash
# Real-time Lambda logs
aws logs tail /aws/lambda/sedaily-column-websocket-message --follow --region us-east-1

# Check cache status
aws logs tail /aws/lambda/sedaily-column-websocket-message --since 5m --region us-east-1 | grep -E "(Cache|cache)"
```

## Cost Optimization

### Anthropic Prompt Caching (67% savings)
- System prompt (~7,200 tokens) cached with Anthropic ephemeral cache
- Cache TTL: ~5 minutes (Anthropic managed)
- **Cache MISS**: ~$0.10/request (first request creates cache)
- **Cache HIT**: ~$0.03/request (subsequent requests)
- Key requirements for cache hit:
  - System prompt must be **identical** across requests
  - Dynamic content (time, session) moved to user message
  - Conversation context in user message, not system prompt

### Pricing (Claude Opus 4.5)
| Token Type | Price per 1M tokens |
|------------|---------------------|
| Input | $5.00 |
| Output | $25.00 |
| Cache Write | $10.00 |
| **Cache Read** | **$0.50** (90% off) |

### DynamoDB Caching
- Permanent in-memory cache in Lambda container
- DB queries only on cold start
- Reduces DynamoDB read costs

## Tech Stack

### Backend
- Python 3.11
- AWS Lambda
- Anthropic Claude Opus 4.5
- DynamoDB
- API Gateway (REST + WebSocket)
- Secrets Manager

### Frontend
- React 18.2
- Vite 4.4
- Tailwind CSS 3.3
- S3 + CloudFront

## Monitoring

### Cache Monitoring Patterns
```bash
# DynamoDB Cache
Cache HIT for C1 - DB query skipped (permanent cache)
Cache MISS for C1 - fetching from DB (first time)

# Anthropic Prompt Cache
Anthropic Cache HIT! Read 7232 tokens from cache
Anthropic Cache MISS! Created cache with 7232 tokens

# Usage & Cost
API Usage: {'input_tokens': 2227, 'cache_read_input_tokens': 7232, ...}
API Cost: $0.029276
```

### CloudWatch Metrics
- Lambda invocations and errors
- API Gateway request count
- DynamoDB read/write capacity
- WebSocket connection count

## Troubleshooting

### Common Issues

1. **WebSocket not connecting**
   - Check Lambda logs for errors
   - Verify API Gateway WebSocket stage is deployed

2. **AI responses not working**
   - Check Anthropic API key in Secrets Manager
   - Verify Lambda environment variables

3. **Cache not working**
   - Verify system prompt is static (no dynamic values)
   - Check logs for `cache_read_input_tokens > 0`

### Rollback
```bash
# Rollback using git
git checkout <commit-hash> -- backend/
./deploy-backend.sh
```

## Related Documents
- [AWS_INFRASTRUCTURE_MAP.md](./AWS_INFRASTRUCTURE_MAP.md) - AWS resource details

## License
Proprietary - Seoul Economic Daily
