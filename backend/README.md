# SEDAILY.AI Services

AI-powered content creation platform for Seoul Economic Daily.

Last Updated: 2026-01-18

## Overview

This repository contains 6 AI services built on Anthropic Claude Opus 4.5 with real-time WebSocket streaming, native web search, and prompt caching optimization.

All services share a common architecture:
- **Frontend**: React + Vite + Tailwind CSS
- **Backend**: Python 3.11 + AWS Lambda
- **AI**: Anthropic Claude Opus 4.5 (primary) + AWS Bedrock (fallback)
- **Infrastructure**: API Gateway (REST + WebSocket) + DynamoDB + S3 + CloudFront

## Services

| Service | Domain | Purpose | Status |
|---------|--------|---------|--------|
| p1 | p1.sedaily.ai | Proofreading & Title Generation | Production |
| r1 | r1.sedaily.ai | Column Writing Assistant | Production |
| f1 | f1.sedaily.ai | General Chat Service | Production |
| b1 | b1.sedaily.ai | Press Release Assistant | Production |
| w1 | w1.sedaily.ai | Press Release Service | Production |
| t1 | t1.sedaily.ai | Title AI Conversation | Production |

## Service Details

### p1.sedaily.ai (Proofreading)
- **Path**: `/proofreading/external/two/`
- **Features**: Article proofreading, title generation, grammar correction
- **CloudFront**: E39OHKSWZD4F8J
- **Cost Savings**: 92% with prompt caching

### r1.sedaily.ai (Column Writing)
- **Path**: `/regression/external/two/`
- **Features**: Column article writing, style guidance
- **CloudFront**: EH9OF7IFDTPLW
- **Cost Savings**: 67% with prompt caching

### f1.sedaily.ai (Chat)
- **Path**: `/foreign/external/two/`
- **Features**: General AI chat, web search integration
- **CloudFront**: E1HNX1UP39MOOM
- **Cost Savings**: Standard pricing

### b1.sedaily.ai (Press Release Assistant)
- **Path**: `/buddy/external/two/`
- **Features**: Corporate/Government press release writing, dual engine support
- **CloudFront**: E2WPOE6AL2G5DZ
- **Cost Savings**: 81% with prompt caching

### w1.sedaily.ai (Press Release Service)
- **Path**: `/bodo/external/two/`
- **Features**: Press release writing, 12-step systematic prompt
- **CloudFront**: E10S6CKR5TLUBG
- **Cost Savings**: 90% with prompt caching

### t1.sedaily.ai (Title AI Conversation)
- **Path**: `/title/external/two/`
- **Features**: AI conversation, web search, RAG support (Aurora PostgreSQL)
- **CloudFront**: EIYU5SFVTHQMN
- **Cost Savings**: 90% with prompt caching

## Common Architecture

```
Frontend (React + Vite)
  |
CloudFront (CDN) --> S3 (Static Hosting)

WebSocket Flow:
User --> API Gateway WebSocket --> Lambda (message handler)
  |
Anthropic Claude Opus 4.5 (with web search)
  |
Streaming Response --> User

REST API Flow:
User --> API Gateway REST --> Lambda (CRUD handlers)
  |
DynamoDB (conversations, prompts, usage)
```

## Common Features

### AI Configuration
| Setting | Value |
|---------|-------|
| Primary Provider | Anthropic API |
| Model | claude-opus-4-5-20251101 |
| Max Tokens | 4096 |
| Temperature | 0.3 - 0.7 |
| Fallback | AWS Bedrock (claude-sonnet-4) |
| Web Search | Enabled (max 5 uses) |

### Prompt Caching
All services use Anthropic ephemeral prompt caching:
- Cache TTL: 5 minutes - 1 hour (Anthropic managed)
- Cost reduction: 67% - 92% per request
- Requirements:
  - System prompt must be identical across requests
  - Dynamic content (time, session) in user message
  - Conversation context in messages array

### Pricing (Claude Opus 4.5)
| Token Type | Price per 1M tokens |
|------------|---------------------|
| Input | $5.00 |
| Output | $25.00 |
| Cache Write | $10.00 |
| Cache Read | $0.50 (90% off) |

## Unified Change History

### Phase 11: Dark/Light Theme Toggle (2026-01-18)
**All Services**
- Added theme toggle button to Header.jsx (Sun/Moon icons)
- Theme state persisted in localStorage (`theme` key)
- Added inline script in index.html to prevent FOUC (Flash of Unstyled Content)
- Tailwind CSS `darkMode: "class"` configuration
- CSS variables define light/dark color schemes in index.css
- Theme toggle hidden on landing pages
- Fixed S3 bucket names in documentation:
  - bodo: `w1-sedaily-frontend` → `w1-frontend`
  - foreign: `f1-frontend-two` → `f1-two-frontend`

### Phase 10: f1 Lambda Timeout Fix (2025-12-21)
**f1.sedaily.ai**
- Fixed: Long AI responses (foreign news translation) getting cut off mid-response
- Root cause: Lambda timeout was 120 seconds (insufficient for complex translations)
- Fix: Updated all 6 f1 Lambda functions timeout: 120s → 180s (3 minutes)
- Verified: Prompt loading from DynamoDB working correctly
  - Instruction: 18,315 chars
  - Files: 8 reference files
  - Total system prompt: 108,977 chars
- Redeployed backend and frontend

### Phase 9: Final Testing & t1 Cognito Fix (2025-12-21)
**All Services - Production Verified**
| Service | Backend | Frontend | Auth | Status |
|---------|---------|----------|------|--------|
| p1.sedaily.ai | 4/4 Lambda | S3 + CloudFront | Cognito | PASS |
| r1.sedaily.ai | 6/6 Lambda | S3 + CloudFront | Cognito | PASS |
| f1.sedaily.ai | 6/6 Lambda | S3 + CloudFront | Cognito | PASS |
| b1.sedaily.ai | 4/4 Lambda | S3 + CloudFront | Cognito | PASS |
| w1.sedaily.ai | 6/6 Lambda | S3 + CloudFront | Cognito | PASS |
| t1.sedaily.ai | 4/4 Lambda | S3 + CloudFront | Cognito | PASS |

**t1.sedaily.ai**
- Fixed Cognito login error (`InvalidParameterException: clientId empty`)
- Root cause: Missing `frontend/.env` file after cleanup
- Fix: Created `.env` with Cognito configuration:
  - User Pool: `sedaily.ai_cognito` (`us-east-1_ohLOswurY`)
  - Client ID: `4m4edj8snokmhqnajhlj41h9n2` (`nx-tt-dev-ver3-web-client`)
- Rebuilt and redeployed frontend
- Verified: Login functionality working

### Phase 8: Deployment Script Fixes (2025-12-21)
**p1.sedaily.ai**
- Fixed `deploy-frontend.sh` S3 bucket policy (CloudFront-only → public read)
- Simplified CloudFront section to use fixed distribution ID
- Removed unused CloudFront creation logic

**b1.sedaily.ai**
- Fixed `update-buddy-code.sh` environment variable format
- Changed from JSON to AWS CLI shorthand: `Variables={KEY=value}`
- Removed env var update from script (already configured)
- Kept `deployment.zip` for manual retries

### Phase 7: p1 CloudFront Fix (2025-12-21)
**p1.sedaily.ai**
- Fixed Access Denied error on p1.sedaily.ai
- Root cause: CloudFront `E39OHKSWZD4F8J` pointed to wrong S3 bucket
- Fix: Updated origin from `nx-wt-prf-frontend-prod` to `nx-prf-prod-frontend-2025`
- Updated `deploy-frontend.sh` with correct bucket and CloudFront ID
- Verified: `https://p1.sedaily.ai` returns HTTP 200

### Phase 6: Final Cleanup & Deployment (2025-12-21)
**All Services**
- Removed backup files, ZIP packages, `__pycache__/` directories
- Deleted unused documentation (consolidated into README)
- Cleaned `node_modules/`, `dist/` (regenerated on build)
- Deployment scripts tested and verified
- README standardized: English, consistent format

### Phase 5: Prompt Caching Fix (2025-12-21)
**All Services**
- Fixed Anthropic Prompt Caching implementation
- Issue: `cache_control` had invalid `ttl` parameter
- Fixed: Changed to `{"type": "ephemeral"}`
- Issue: Dynamic values in system prompt invalidating cache
- Fixed: Static values for system prompt, dynamic in user message
- Logger fix: `logging.getLogger()` -> `setup_logger()` for CloudWatch
- SSE streaming parser improved for `message_start`/`message_stop` events
- Added detailed usage logging with cost calculation

### Phase 4: Project Cleanup (2025-12-20 ~ 2025-12-21)
**All Services**
- Removed 30-50 unused files per service
- Deleted archive/backup directories
- Removed test files and deprecated scripts
- Documentation consolidated into README

### Phase 3: Prompt Caching Optimization (2025-12-20)
**All Services**
- Implemented Anthropic Prompt Caching with `cache_control`
- Dynamic/static context separation for improved cache hit rate
- Lambda in-memory permanent cache for DynamoDB queries
- Added `calculate_cost()` function for real-time cost tracking

### Phase 2: Claude 4.5 Opus Migration (2024-11 ~ 2024-12)
**All Services**
- Migrated from AWS Bedrock to Anthropic Direct API
- Model: `claude-opus-4-5-20251101` (Claude Opus 4.5)
- Added dual AI provider support (Anthropic primary, Bedrock fallback)
- Integrated native web search functionality
- Added `anthropic_client.py` with streaming support
- Secrets Manager integration for API keys

### Phase 1: Initial Setup (2024-09 ~ 2024-10)
**All Services**
- Project initialization with React + Vite frontend
- AWS infrastructure: S3, CloudFront, API Gateway, Lambda, DynamoDB
- WebSocket real-time chat implementation
- REST API for conversation/prompt/usage management
- User authentication with AWS Cognito

## Deployment

Each service has its own deployment scripts:

```bash
# p1.sedaily.ai
cd proofreading/external/two
./deploy-anthropic.sh && ./deploy-frontend.sh

# r1.sedaily.ai
cd regression/external/two
./deploy-backend.sh && ./deploy-column-frontend.sh

# f1.sedaily.ai
cd foreign/external/two
./upgrade-f1-anthropic.sh && ./upgrade-f1-frontend.sh

# b1.sedaily.ai
cd buddy/external/two
./update-buddy-code.sh && ./deploy-p2-frontend.sh

# w1.sedaily.ai
cd bodo/external/two/w1-scripts
./deploy-backend.sh && ./deploy-frontend.sh

# t1.sedaily.ai
cd title/external/two
./deploy-backend.sh && ./deploy-frontend.sh
```

## AWS Resources

### Region: us-east-1

### Secrets Manager
| Service | Secret Name |
|---------|-------------|
| p1 | proof-v1 |
| r1 | regression-v1 |
| f1 | foreign-v1 |
| b1 | buddy-v1 |
| w1 | bodo-v1 |
| t1 | title-v1 |

### Lambda Functions (Total: 30)
- p1: 4 functions (nx-wt-prf-*)
- r1: 6 functions (sedaily-column-*)
- f1: 6 functions (f1-*-two)
- b1: 4 functions (p2-two-*-two)
- w1: 6 functions (w1-*)
- t1: 4 functions (nx-tt-dev-ver3-*)

## Monitoring

### CloudWatch Log Groups
```bash
# Pattern for each service
/aws/lambda/{service-prefix}-websocket-message
/aws/lambda/{service-prefix}-conversation-api
```

### Cache Monitoring Patterns
```
# DynamoDB Cache
Cache HIT for [engine] - DB query skipped (permanent cache)
Cache MISS for [engine] - fetching from DB

# Anthropic Prompt Cache
Prompt caching enabled (TTL: 1h)
API Cost: $X.XXXXXX | cache_read: X, cache_write: X
```

## Directory Structure

```
/services/
├── README.md                    # This file
├── test-reporting/              # Test reports
├── proofreading/external/two/   # p1.sedaily.ai
├── regression/external/two/     # r1.sedaily.ai
├── foreign/external/two/        # f1.sedaily.ai
├── buddy/external/two/          # b1.sedaily.ai
├── bodo/external/two/           # w1.sedaily.ai
└── title/external/two/          # t1.sedaily.ai
```

## Related Documentation

- [Test Report 2025-12-21](./test-reporting/2025-12-21-cleanup-and-deployment-test.md)
- Individual service READMEs in each service directory

## License

Proprietary - Seoul Economic Daily
