# NX-WT-PRF Internal
AI Proofreading Service - Simplified Internal Version (No Login Required)

Last Updated: 2025-12-24

## Overview
Internal employee version of Seoul Economic Daily's AI proofreading service. Uses the same backend as the external version (p1.sedaily.ai) but with a simplified UI - no login, no sidebar, direct access to chat.

**Live:** https://d1zig3y52jaq1s.cloudfront.net

## Internal vs External Comparison
| Feature | Internal (this project) | External (external/two) |
|---------|------------------------|-------------------------|
| Login | ❌ None | ✅ Cognito Auth |
| Sidebar | ❌ None | ✅ Enabled |
| Landing Page | ❌ None (direct to /11) | ✅ Enabled |
| Domain | d1zig3y52jaq1s.cloudfront.net | p1.sedaily.ai |
| S3 Bucket | nexus-multi-frontend-20251204 | nx-prf-prod-frontend-2025 |
| Region | ap-northeast-2 (Seoul) | us-east-1 (Virginia) |
| **Backend** | **Shared (Same)** | **Shared (Same)** |

## Features
- Real-time Chat: WebSocket-based streaming responses
- Web Search: Anthropic's native web search integration (2025 data)
- **Prompt Caching: 92% cost reduction with Anthropic ephemeral cache** ✅
- No login required - direct access
- Simplified UI (no sidebar, no landing page)

## Architecture
```
Frontend (React + Vite)
  ↓
CloudFront (CDN)
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
├── AWS_INFRASTRUCTURE_DOCUMENTATION.md
├── deploy-anthropic.sh     # Backend deployment
├── deploy-frontend.sh      # Frontend deployment
├── config/                 # Environment configuration
├── backend/
│   ├── handlers/           # Lambda handlers
│   │   ├── api/           # REST API handlers
│   │   └── websocket/     # WebSocket handlers
│   ├── lib/               # anthropic_client, bedrock_client
│   ├── services/          # websocket_service
│   ├── src/               # Core business logic
│   │   ├── models/
│   │   ├── repositories/
│   │   └── services/
│   └── utils/
└── frontend/
    ├── src/
    │   ├── features/      # auth, chat, dashboard
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
./deploy-anthropic.sh && ./deploy-frontend.sh

# Frontend only
./deploy-frontend.sh

# Backend only
./deploy-anthropic.sh
```

## Current Deployment
Status: Production Ready

Updated: 2025-12-21

## URLs
| Resource | URL |
|----------|-----|
| **Internal Domain** | https://d1zig3y52jaq1s.cloudfront.net |
| External Domain | https://p1.sedaily.ai (see external/two) |
| REST API (shared) | https://wxwdb89w4m.execute-api.us-east-1.amazonaws.com/prod |
| WebSocket API (shared) | wss://p062xh167h.execute-api.us-east-1.amazonaws.com/prod |

## AWS Resources (us-east-1)

### Lambda Functions
| Function | Purpose |
|----------|---------|
| nx-wt-prf-websocket-connect | WebSocket connection handler |
| nx-wt-prf-websocket-message | Main chat handler (Claude API) |
| nx-wt-prf-websocket-disconnect | WebSocket disconnect handler |
| nx-wt-prf-conversation-api | Conversation CRUD |
| nx-wt-prf-prompt-crud | Prompt management |
| nx-wt-prf-usage-handler | Usage tracking |

### DynamoDB Tables
| Table | Purpose |
|-------|---------|
| nx-wt-prf-conversations | Chat history |
| nx-wt-prf-prompts | System prompts |
| nx-wt-prf-files | File metadata |
| nx-wt-prf-usage | Usage statistics |
| nx-wt-prf-usage-tracking | Detailed tracking |
| nx-wt-prf-websocket-connections | Active connections |

### Frontend Resources (Internal - ap-northeast-2)
| Resource | ID/Name |
|----------|---------|
| S3 Bucket | nexus-multi-frontend-20251204 |
| CloudFront Distribution | E1O9OA8UA34Z49 |
| Domain | d1zig3y52jaq1s.cloudfront.net |

### Shared Resources (us-east-1)
| Resource | ID/Name |
|----------|---------|
| Secrets Manager | proof-v1 (Anthropic API key) |
| Cognito User Pool | us-east-1_ohLOswurY (not used in internal) |

## AI Configuration
| Setting | Value |
|---------|-------|
| Primary Provider | Anthropic API |
| Model | claude-opus-4-5-20251101 |
| Max Tokens | 4096 |
| Temperature | 0.7 |
| Fallback | AWS Bedrock |
| Web Search | Enabled (max 5 uses) |

## Change History

### Phase 9: Internal Version Setup (2025-12-24)
- **Created internal-only version** for Seoul Economic Daily employees
- Removed login requirement (ProtectedRoute disabled)
- Removed sidebar (showSidebar = false)
- Removed landing page (/ redirects to /11 directly)
- Removed login button from Header
- Deployed to new CloudFront distribution:
  - S3: `nexus-multi-frontend-20251204` (ap-northeast-2)
  - CloudFront: `E1O9OA8UA34Z49`
  - Domain: `d1zig3y52jaq1s.cloudfront.net`
- Updated `deploy-frontend.sh` with internal CloudFront settings
- Updated README.md to reflect internal version differences
- Backend remains shared with external version (p1.sedaily.ai)

### Phase 8: Final Testing & Deployment Verification (2025-12-21)
- **Production deployment verified** - All components tested and working
- Backend: 4/4 Lambda functions deployed successfully
- Frontend: S3 + CloudFront deployment complete
- Authentication: Cognito login verified
- HTTP Status: 200 OK
- Fixed `deploy-frontend.sh` S3 bucket policy (CloudFront-only → public read)
- Simplified CloudFront section to use fixed distribution ID

### Phase 7: CloudFront Fix (2025-12-21)
- **Fixed p1.sedaily.ai Access Denied error**
- Root cause: `p1.sedaily.ai` CloudFront (`E39OHKSWZD4F8J`) pointed to wrong bucket
- Fix: Updated CloudFront origin from `nx-wt-prf-frontend-prod` to `nx-prf-prod-frontend-2025`
- Updated `deploy-frontend.sh` with correct bucket and CloudFront ID
- Updated `AWS_INFRASTRUCTURE_DOCUMENTATION.md` with correct values
- Verified: `https://p1.sedaily.ai` returns HTTP 200

### Phase 6: Final Cleanup (2025-12-21)
- Removed duplicate documentation files:
  - `DEPLOYMENT_MANUAL.md` - consolidated into README
  - `MAINTENANCE_GUIDE.md` - consolidated into README
  - `PROMPT_CACHING_OPTIMIZATION.md` - consolidated into README
- Deleted `infrastructure/`, `work-logs/` directories
- Deleted build artifacts: `*.zip`, `node_modules/`, `dist/`
- Final structure: README + AWS docs + deploy scripts + source code

### Phase 5: Prompt Caching Fix & Optimization (2025-12-21)
- **Fixed Anthropic Prompt Caching** - 92% cost reduction achieved ✅
- Issue: `cache_control` had invalid `ttl` parameter → Fixed to `{"type": "ephemeral"}`
- Issue: Dynamic values in system prompt invalidating cache:
  - `{{current_datetime}}`, `{{session_id}}` changed every request
  - Fixed: Static values for system prompt, dynamic context moved to user message
- Issue: Conversation context prepended to system prompt → Moved to user message
- SSE streaming parser improved for Anthropic's `message_start`/`message_stop` events
- Added detailed usage logging: `📊 API Usage`, `💵 Total cost`, `🎯 Cache HIT`
- Cost comparison:
  - Cache MISS: ~$0.70/request
  - Cache HIT: ~$0.06/request (92% savings)
- Frontend refactoring: Consolidated duplicate `usageService.js` to shared service

### Phase 4: Project Cleanup & Documentation (2025-12-20)
- Removed ~50 unused files and scripts
- Deleted archive folders: `upgrade-archive/`, `backend/scripts/`
- Removed Node.js files: `serverless.yml`, `handler.js`, `index.js`
- Removed test files: `test_web_search.py`, `test_new_table.py`
- Documentation overhaul with SEOdaily-ENG template format

### Phase 3: Systematic Prompt Integration (2025-12-20)
- Added `create_enhanced_system_prompt()` to `websocket_service.py`
- 11-section systematic prompt structure:
  1. Current Context - Time, language, location
  2. Identity & Mission - AI role definition
  3. Security Rules - Input validation
  4. Core Process - 5-step workflow
  5. Journalist Features - Fact-checking, confidence
  6. Korean Language Rules - Grammar standards
  7. Output Rules - Response format
  8. Time-Sensitive Info - Current data handling
  9. Ethics Guidelines - Content standards
  10. Quality Check - Pre-response validation
  11. Never Do This - Prohibited actions
- Lambda redeployment with prompt changes

### Phase 2: Cost Optimization (2025-12-20)
- Implemented Anthropic Prompt Caching with `cache_control`
- Added `calculate_cost()` function for real-time cost tracking
- Dynamic/static context separation for improved cache hit rate:
  - Static: user location, timezone (cacheable)
  - Dynamic: current time, session ID (per request)
- Claude Opus 4.5 pricing integration:
  - Input: $5.00/1M tokens
  - Output: $25.00/1M tokens
  - Cache Read: $0.50/1M tokens (90% savings)
- DynamoDB cache: 5-min TTL -> permanent (container lifetime)
- Expected savings: 70-80%

### Phase 1: Claude 4.5 Opus Migration (2024-12)
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

### Initial Setup
- Project initialization with React + Vite frontend
- AWS infrastructure: S3, CloudFront, API Gateway, Lambda, DynamoDB
- WebSocket real-time chat implementation
- REST API for conversation/prompt/usage management

## Deployment Guide

### Deploy Commands
```bash
# Backend (Lambda functions)
./deploy-anthropic.sh

# Frontend (S3 + CloudFront)
./deploy-frontend.sh

# Full deployment
./deploy-anthropic.sh && ./deploy-frontend.sh
```

### Environment Configuration
Lambda environment variables:
```json
{
  "USE_ANTHROPIC_API": "true",
  "ANTHROPIC_SECRET_NAME": "proof-v1",
  "ANTHROPIC_MODEL_ID": "claude-opus-4-5-20251101",
  "FALLBACK_TO_BEDROCK": "true",
  "ENABLE_NATIVE_WEB_SEARCH": "true",
  "WEB_SEARCH_MAX_USES": "5"
}
```

### Log Monitoring
```bash
# Real-time Lambda logs
aws logs tail /aws/lambda/nx-wt-prf-websocket-message --follow

# Check deployment
aws lambda get-function --function-name nx-wt-prf-websocket-message --query 'Configuration.LastModified'
```

## Cost Optimization

### Anthropic Prompt Caching (92% savings) ✅
- System prompt (~67,000 tokens) cached with Anthropic ephemeral cache
- Cache TTL: ~5 minutes (Anthropic managed)
- **Cache MISS**: ~$0.70/request (first request creates cache)
- **Cache HIT**: ~$0.06/request (subsequent requests)
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

### Estimated Monthly Cost
| Service | Cost |
|---------|------|
| Anthropic Claude | ~$30-80 (with caching) |
| Lambda | ~$50-100 |
| DynamoDB | ~$20-50 |
| S3/CloudFront | ~$10-20 |
| API Gateway | ~$10-30 |
| **Total** | **~$80-200/month** |

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

### CloudWatch Metrics
- Lambda invocations and errors
- API Gateway request count
- DynamoDB read/write capacity
- WebSocket connection count

### Cache Monitoring Patterns
```bash
# DynamoDB Cache
✅ Cache HIT for Basic - DB query skipped (permanent cache)
❌ Cache MISS for Basic - fetching from DB (first time)

# Anthropic Prompt Cache
🎯 Anthropic Cache HIT! Read 67043 tokens from cache
💾 Anthropic Cache MISS! Created cache with 67043 tokens

# Usage & Cost
📊 API Usage: {'input_tokens': 4405, 'cache_read_input_tokens': 67043, ...}
💵 Total cost for this request: $0.057122
```

### Cost Tracking
AWS Cost Explorer with tag: `nx-wt-prf`

## Troubleshooting

### Common Issues

1. **WebSocket not connecting**
   - Check Lambda logs for errors
   - Verify API Gateway WebSocket stage is deployed
   ```bash
   wscat -c wss://p062xh167h.execute-api.us-east-1.amazonaws.com/prod
   ```

2. **AI responses not working**
   - Check Anthropic API key in Secrets Manager
   - Verify Lambda environment variables

3. **Frontend not updating**
   - Run CloudFront cache invalidation
   - Check S3 bucket sync

### Rollback
```bash
# Rollback using git
git checkout <commit-hash> -- backend/
./deploy-anthropic.sh
```

## Related Documents
- [AWS_INFRASTRUCTURE_DOCUMENTATION.md](./AWS_INFRASTRUCTURE_DOCUMENTATION.md) - AWS resource details

## License
Proprietary - Seoul Economic Daily
