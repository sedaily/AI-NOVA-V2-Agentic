# f1.sedaily.ai
AI Chat Service - Claude Opus 4.5 based real-time chat with native web search

Last Updated: 2026-01-01

## Overview
F1 is an AI-powered chat service for Seoul Economic Daily. Built on Anthropic Claude Opus 4.5 with real-time WebSocket streaming, native web search, and automatic citation formatting.

Live: https://f1.sedaily.ai

## Features
- Real-time Chat: WebSocket-based streaming responses
- **Conversation History Caching: 90% cost reduction on cached tokens**
- Web Search: Anthropic's native web search integration (2025 data)
- Auto Citation: URL detection with footnote formatting and source credibility indicators
- Multiple AI Providers: Anthropic API primary, Bedrock fallback
- Korean Economic Focus: Specialized for Korean economic news and analysis

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
Anthropic Claude Opus 4.5 (with web search)
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
├── AWS_STACK_DOCUMENTATION.md
├── upgrade-f1-anthropic.sh    # Backend deployment
├── upgrade-f1-frontend.sh     # Frontend deployment
├── config/                    # Environment configuration
├── backend/
│   ├── handlers/              # Lambda handlers
│   │   ├── api/              # REST API handlers
│   │   └── websocket/        # WebSocket handlers
│   ├── lib/                  # anthropic_client, bedrock_client, citation_formatter
│   ├── services/             # websocket_service
│   ├── src/                  # Core business logic
│   │   ├── models/
│   │   ├── repositories/
│   │   └── services/
│   └── utils/
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
- Python 3.9+
- AWS Account: 887078546492

### Deployment
```bash
# Full deployment (frontend + backend)
./upgrade-f1-anthropic.sh && ./upgrade-f1-frontend.sh

# Frontend only
./upgrade-f1-frontend.sh

# Backend only
./upgrade-f1-anthropic.sh
```

## Current Deployment
Status: Production Ready

Updated: 2025-12-21

## URLs
| Resource | URL |
|----------|-----|
| Primary Domain | https://f1.sedaily.ai |
| CloudFront | https://drbxxcxyi7jpk.cloudfront.net |
| CloudFront ID | E1HNX1UP39MOOM |

## AWS Resources (us-east-1)

### Lambda Functions
| Function | Purpose |
|----------|---------|
| f1-websocket-connect-two | WebSocket connection handler |
| f1-websocket-message-two | Main chat handler (Claude API + Web Search) |
| f1-websocket-disconnect-two | WebSocket disconnect handler |
| f1-conversation-api-two | Conversation CRUD |
| f1-prompt-crud-two | Prompt management |
| f1-usage-handler-two | Usage tracking |

### DynamoDB Tables
| Table | Purpose |
|-------|---------|
| f1-conversations-two | Chat history |
| f1-messages-two | Message history |
| f1-prompts-two | System prompts |
| f1-files-two | File metadata |
| f1-usage-two | Usage statistics |
| f1-websocket-connections-two | Active connections |

### Other Resources
| Resource | ID/Name |
|----------|---------|
| S3 Bucket | f1-two-frontend |
| Secrets Manager | foreign-v1 (Anthropic API key) |

## AI Configuration
| Setting | Value |
|---------|-------|
| Primary Provider | Anthropic API |
| Model | claude-opus-4-5-20251101 |
| Max Tokens | 4096 |
| Temperature | 0.3 |
| Fallback | AWS Bedrock |
| Web Search | Enabled (max 5 uses) |

## Change History

### Phase 6: Conversation History Caching (2026-01-01)
- **Added conversation history caching for cost optimization**

| | Before | After |
|---|--------|-------|
| API Method | `stream_response()` | `stream_response_with_history()` |
| History Caching | None | 3 strategic breakpoints |
| Cache Hit | 0 tokens | 63,409 tokens |
| Cost per Request | $0.32 (full price) | $0.03 (90% off on cached) |

- Implementation:
  - `anthropic_client.py`: Added `_apply_conversation_caching()`, `stream_response_with_history()`
  - `websocket_service.py`: Added `_prepare_messages_for_caching()`, `_validate_message_alternation()`
- Cache breakpoint strategy (Anthropic max 4 limit):
  - System prompt: 1 breakpoint
  - Conversation history: up to 3 breakpoints (first, middle, last-1)

### Phase 5: Lambda Timeout Fix (2025-12-21)
- **Lambda timeout increased**: 120s → 180s (3 minutes)
- Fixed: Long AI responses (foreign news translation) getting cut off
- All 6 Lambda functions updated with new timeout
- Verified: Prompt loading from DynamoDB working correctly
  - Instruction: 18,315 chars
  - Files: 8 reference files
  - Total system prompt: 108,977 chars

### Phase 4: Final Testing & Deployment Verification (2025-12-21)
- **Production deployment verified** - All components tested and working
- Backend: 6/6 Lambda functions deployed successfully
- Frontend: S3 + CloudFront deployment complete
- Authentication: Cognito login verified
- HTTP Status: 200 OK
- All deployment scripts tested and verified

### Phase 3: Project Cleanup (2025-12-21)
- Removed archive directories: `cleanup-archive/`, `scripts-backup/`
- Deleted build artifacts: `*.zip`, `__pycache__/`, `node_modules/`, `dist/`
- Deleted test files: `test_caching_optimization.py`
- Consolidated documentation into README
- Final structure: Minimal, clean, production-focused

### Phase 2: Web Search Integration (2025-12-14)
- Added Anthropic native web search functionality
- Implemented auto citation formatting with source credibility:
  - Official news sources (YTN, Yonhap)
  - Government/public institutions (.gov.kr, .go.kr)
  - General websites
- Added `citation_formatter.py` for source formatting
- Web search triggers: "today", "latest", "news" keywords

### Phase 1: Claude 4.5 Opus Migration (2025-12)
- Migrated from AWS Bedrock to Anthropic Direct API
- Model: `claude-opus-4-5-20251101` (Claude Opus 4.5)
- Added dual AI provider support:
  - Primary: Anthropic API (direct)
  - Fallback: AWS Bedrock
- Added `anthropic_client.py`:
  - Streaming response support
  - Secrets Manager integration
  - Web search tool configuration

### Initial Setup
- Project initialization with React + Vite frontend
- AWS infrastructure: S3, CloudFront, API Gateway, Lambda, DynamoDB
- WebSocket real-time chat implementation
- REST API for conversation/prompt/usage management

## Deployment Guide

### Deploy Commands
```bash
# Backend (Lambda functions)
./upgrade-f1-anthropic.sh

# Frontend (S3 + CloudFront)
./upgrade-f1-frontend.sh

# Full deployment
./upgrade-f1-anthropic.sh && ./upgrade-f1-frontend.sh
```

### Environment Configuration
Lambda environment variables:
```json
{
  "USE_ANTHROPIC_API": "true",
  "ANTHROPIC_SECRET_NAME": "foreign-v1",
  "ANTHROPIC_MODEL_ID": "claude-opus-4-5-20251101",
  "AI_PROVIDER": "anthropic_api",
  "FALLBACK_TO_BEDROCK": "true",
  "ENABLE_NATIVE_WEB_SEARCH": "true",
  "WEB_SEARCH_MAX_USES": "5",
  "MAX_TOKENS": "4096",
  "TEMPERATURE": "0.3"
}
```

### Log Monitoring
```bash
# Real-time Lambda logs
aws logs tail /aws/lambda/f1-websocket-message-two --follow

# Check function status
aws lambda get-function --function-name f1-websocket-message-two
```

## Web Search Feature

### Trigger Keywords
- Korean: "오늘", "최신", "뉴스", "현재"
- English: "today", "latest", "news", "current"

### Citation Format
Sources are automatically formatted with credibility indicators:
- Official news: YTN, Yonhap News, major outlets
- Government: .gov.kr, .go.kr domains
- General: Other web sources

### Usage Limit
- Maximum 5 web searches per conversation
- Automatic fallback to cached knowledge when limit reached

## Tech Stack

### Backend
- Python 3.9
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

### CloudWatch Metrics
- Lambda invocations and errors
- API Gateway request count
- DynamoDB read/write capacity
- WebSocket connection count

### Key Metrics
- Response time: WebSocket message processing speed
- Error rate: Lambda function execution failures
- Web search usage: Daily search request count
- User activity: Conversation session count

## Troubleshooting

### Common Issues

1. **WebSocket not connecting**
   - Check Lambda logs for errors
   - Verify API Gateway WebSocket stage is deployed

2. **AI responses not working**
   - Check Anthropic API key in Secrets Manager (foreign-v1)
   - Verify Lambda environment variables

3. **Web search not triggering**
   - Check if trigger keywords are present in query
   - Verify `ENABLE_NATIVE_WEB_SEARCH=true`
   - Check if search limit (5) has been reached

### Rollback
```bash
# Rollback using git
git checkout <commit-hash> -- backend/
./upgrade-f1-anthropic.sh
```

## Related Documents
- [AWS_STACK_DOCUMENTATION.md](./AWS_STACK_DOCUMENTATION.md) - AWS resource details

## License
Proprietary - Seoul Economic Daily
