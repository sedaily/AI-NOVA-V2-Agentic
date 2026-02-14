# b1.sedaily.ai
AI Press Release Assistant - Claude Opus 4.5 based real-time chat with web search

Last Updated: 2025-12-21

## Overview
NX-P2-BUDDY is an AI-powered press release writing assistant for Seoul Economic Daily. Built on Anthropic Claude Opus 4.5 with real-time WebSocket streaming, native web search, and prompt caching for cost optimization.

Live: https://b1.sedaily.ai

## Features
- Real-time Chat: WebSocket-based streaming responses
- Web Search: Anthropic's native web search integration (2025 data)
- **Prompt Caching: 81% cost reduction with Anthropic ephemeral cache** ✅
- DynamoDB Caching: Permanent prompt cache in Lambda container
- Multiple AI Providers: Anthropic API primary, Bedrock fallback
- Dual Engine Support: Corporate (11) / Government (22) press release modes
- Press Release Generation: Structured 5-step article creation workflow

## Architecture
```
Frontend (React + Vite)
  ↓
CloudFront (CDN) → b1.sedaily.ai
  ↓
S3 (Static Hosting)

WebSocket Flow:
User → API Gateway WebSocket → Lambda (message handler)
  ↓
Anthropic Claude Opus 4.5 (with web search)
  ↓
Streaming Response → User

REST API Flow:
User → API Gateway REST → Lambda (conversation/prompt/usage)
  ↓
DynamoDB (conversations, prompts, usage tracking)
```

## Project Structure
```
.
├── README.md
├── upgrade-aws-resources.md    # AWS infrastructure documentation
├── update-buddy-code.sh        # Backend deployment script
├── deploy-p2-frontend.sh       # Frontend deployment script
├── backend/
│   ├── handlers/               # Lambda handlers (websocket)
│   ├── lib/                    # AI clients (anthropic, bedrock, perplexity)
│   ├── services/               # websocket_service
│   ├── src/                    # Core business logic
│   │   ├── models/
│   │   ├── repositories/
│   │   └── config/
│   ├── utils/                  # Logger utilities
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── features/           # auth, chat, dashboard, landing
    │   ├── shared/
    │   └── config.js
    └── package.json
```

## Quick Start

### Prerequisites
- AWS CLI configured
- Node.js 18+
- Python 3.11+
- AWS Account: 887078546492

### Deployment
```bash
# Backend only (Lambda functions)
./update-buddy-code.sh

# Frontend only (S3 + CloudFront)
./deploy-p2-frontend.sh

# Full deployment
./update-buddy-code.sh && ./deploy-p2-frontend.sh
```

## Current Deployment
Status: Production Ready

Updated: 2025-12-21

## URLs
| Resource | URL |
|----------|-----|
| Primary Domain | https://b1.sedaily.ai |
| CloudFront | https://dxiownvrignup.cloudfront.net |
| REST API | https://pisnqqgu75.execute-api.us-east-1.amazonaws.com/prod |
| WebSocket API | wss://dwc2m51as4.execute-api.us-east-1.amazonaws.com/prod |

## AWS Resources (us-east-1)

### Lambda Functions
| Function | Purpose |
|----------|---------|
| p2-two-websocket-connect-two | WebSocket connection handler |
| p2-two-websocket-message-two | Main chat handler (Claude API) |
| p2-two-websocket-disconnect-two | WebSocket disconnect handler |
| p2-two-conversation-api-two | Conversation CRUD |
| p2-two-prompt-crud-two | Prompt management |
| p2-two-usage-handler-two | Usage tracking |

### DynamoDB Tables
| Table | Purpose |
|-------|---------|
| p2-two-conversations-two | Chat history |
| p2-two-messages-two | Message storage |
| p2-two-prompts-two | System prompts |
| p2-two-files-two | File metadata |
| p2-two-usage-two | Usage statistics |
| p2-two-websocket-connections-two | Active connections |

### Other Resources
| Resource | ID/Name |
|----------|---------|
| S3 Bucket | p2-two-frontend |
| CloudFront Distribution | E2WPOE6AL2G5DZ |
| Secrets Manager | buddy-v1 (Anthropic API key) |

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

### Phase 7: Final Testing & Deployment Verification (2025-12-21)
- **Production deployment verified** - All components tested and working
- Backend: 4/4 Lambda functions deployed successfully
- Frontend: S3 + CloudFront deployment complete (70 files)
- Authentication: Cognito login verified
- HTTP Status: 200 OK
- Fixed `update-buddy-code.sh` environment variable format
- Changed from JSON to AWS CLI shorthand: `Variables={KEY=value}`

### Phase 6: Frontend Cleanup & Full Deployment (2025-12-21)
- **Frontend cleanup** - Removed 10+ unused files
- Deleted: `.env.backup.*` (5 files), `.env.production.template`
- Deleted: `deployment-log.txt`, `deployment-info.txt`, `.env.w1`
- Deleted: `src/features/*/LandingPresenter.jsx.backup`
- Deleted: `src/features/chat/services/*.backup.*` (2 files)
- Final frontend structure: 48 source files, clean layout
- Full deployment verified: Backend Lambda + Frontend S3/CloudFront

### Phase 5: Prompt Caching Logging Fix (2025-12-21)
- **Fixed CloudWatch logging for Anthropic Prompt Caching** ✅
- Issue: `logging.getLogger()` not outputting to CloudWatch
- Fixed: Changed to `setup_logger()` from utils module
- Issue: Usage extraction from wrong SSE event (`message_stop`)
- Fixed: Extract usage from `message_start` event per Anthropic spec
- Added cache management functions:
  - `clear_prompt_cache()` - Clear prompt cache by engine type
  - `get_cache_stats()` - Get cache statistics
- Log output now shows:
  - `✅ Prompt caching enabled (TTL: 1h)`
  - `💰 API Cost: $0.015947 | cache_read: 27925, cache_write: 0`

### Phase 4: Project Cleanup (2025-12-21)
- Removed ~30+ unused files and scripts
- Deleted: ZIP packages (15MB), backup files, deprecated scripts
- Deleted: `docs/archive/`, `deprecated-scripts/`, `scripts-v2/`
- Removed all `*_backup.py`, `*_dual.py`, `*_fixed.py` files
- Cleaned `__pycache__/` directories
- Final structure: Clean 6-folder layout

### Phase 3: Prompt Caching Optimization (2025-12-20)
- Implemented Anthropic Prompt Caching with `cache_control`
- Dynamic/static context separation for improved cache hit rate:
  - Static: user location, timezone (cacheable in system prompt)
  - Dynamic: current time, session ID (in user message)
- Lambda in-memory permanent cache for DynamoDB queries
- Expected savings: 81% per request

### Phase 2: Claude 4.5 Opus Migration (2024-12)
- Migrated from AWS Bedrock to Anthropic Direct API
- Model: `claude-opus-4-5-20251101` (Claude Opus 4.5)
- Added dual AI provider support:
  - Primary: Anthropic API (direct)
  - Fallback: AWS Bedrock (claude-sonnet-4)
- Integrated native web search functionality
- Added `anthropic_client.py`:
  - Streaming response support
  - Secrets Manager integration
  - Web search tool configuration
- Added `citation_formatter.py` for source formatting
- Updated `bedrock_client_enhanced.py` as fallback
- Added `perplexity_client.py` for alternative search

### Phase 1: Initial Setup (2024-12)
- Project initialization with React + Vite frontend
- AWS infrastructure: S3, CloudFront, API Gateway, Lambda, DynamoDB
- WebSocket real-time chat implementation
- REST API for conversation/prompt/usage management
- Dual engine support (Corporate/Government press releases)
- User authentication with AWS Cognito

## Deployment Guide

### Deploy Commands
```bash
# Backend (Lambda functions)
./update-buddy-code.sh

# Frontend (S3 + CloudFront)
./deploy-p2-frontend.sh

# Full deployment
./update-buddy-code.sh && ./deploy-p2-frontend.sh
```

### Environment Configuration
Lambda environment variables:
```json
{
  "USE_ANTHROPIC_API": "true",
  "ANTHROPIC_SECRET_NAME": "buddy-v1",
  "ANTHROPIC_MODEL_ID": "claude-opus-4-5-20251101",
  "SERVICE_NAME": "buddy",
  "AI_PROVIDER": "anthropic_api",
  "FALLBACK_TO_BEDROCK": "true",
  "ENABLE_NATIVE_WEB_SEARCH": "true",
  "MAX_TOKENS": "4096",
  "TEMPERATURE": "0.3"
}
```

### Log Monitoring
```bash
# Real-time Lambda logs
aws logs tail /aws/lambda/p2-two-websocket-message-two --follow --region us-east-1

# Check cache status
aws logs tail /aws/lambda/p2-two-websocket-message-two --since 5m --region us-east-1 | grep -E "💰|cache|Cache"

# Check deployment
aws lambda get-function --function-name p2-two-websocket-message-two --query 'Configuration.LastModified'
```

## Cost Optimization

### Anthropic Prompt Caching (81% savings) ✅
- System prompt (~27,925 tokens) cached with Anthropic ephemeral cache
- Cache TTL: 1 hour (Anthropic managed)
- **Cache MISS**: ~$0.155/request (first request creates cache)
- **Cache HIT**: ~$0.029/request (subsequent requests)
- Key requirements for cache hit:
  - System prompt must be **identical** across requests
  - Dynamic content (time, session) moved to user message
  - Conversation context in messages array, not system prompt

### Pricing (Claude Opus 4.5)
| Token Type | Price per 1M tokens |
|------------|---------------------|
| Input | $5.00 |
| Output | $25.00 |
| Cache Write | $10.00 |
| **Cache Read** | **$0.50** (90% off) |

### Lambda In-Memory Caching
- Permanent cache in Lambda container (no TTL)
- DynamoDB queries only on cold start
- Cache functions: `clear_prompt_cache()`, `get_cache_stats()`

### Estimated Monthly Cost
| Service | Cost |
|---------|------|
| Anthropic Claude | ~$30-50 (with caching) |
| Lambda | ~$30-50 |
| DynamoDB | ~$10-20 |
| S3/CloudFront | ~$5-10 |
| API Gateway | ~$5-15 |
| **Total** | **~$80-150/month** |

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
- Framer Motion
- S3 + CloudFront

## Monitoring

### CloudWatch Metrics
- Lambda invocations and errors
- API Gateway request count
- DynamoDB read/write capacity
- WebSocket connection count

### Cache Monitoring Patterns
```bash
# DynamoDB Cache
✅ Cache HIT for 11 - DB query skipped (permanent cache)
❌ Cache MISS for 11 - fetching from DB
💾 Permanently cached prompt for 11 (2 files, 42931 bytes)

# Anthropic Prompt Cache
✅ Prompt caching enabled (TTL: 1h)
💰 API Cost: $0.015947 | input: 392, output: 1, cache_read: 27925, cache_write: 0
```

### Cost Tracking
AWS Cost Explorer with tag: `p2-two`

## Troubleshooting

### Common Issues

1. **WebSocket not connecting**
   - Check Lambda logs for errors
   - Verify API Gateway WebSocket stage is deployed
   ```bash
   wscat -c wss://dwc2m51as4.execute-api.us-east-1.amazonaws.com/prod
   ```

2. **AI responses not working**
   - Check Anthropic API key in Secrets Manager (`buddy-v1`)
   - Verify Lambda environment variables
   ```bash
   aws lambda get-function-configuration --function-name p2-two-websocket-message-two
   ```

3. **Frontend not updating**
   - Run CloudFront cache invalidation
   ```bash
   aws cloudfront create-invalidation --distribution-id E2WPOE6AL2G5DZ --paths "/*"
   ```

4. **Cache not hitting**
   - Check if system prompt is identical across requests
   - Verify dynamic content is in user message, not system prompt
   - Check logs for `cache_write` vs `cache_read` values

### Rollback
```bash
# Rollback using git
git checkout <commit-hash> -- backend/
./update-buddy-code.sh
```

## Related Documents
- [upgrade-aws-resources.md](./upgrade-aws-resources.md) - AWS infrastructure details

## License
Proprietary - Seoul Economic Daily
