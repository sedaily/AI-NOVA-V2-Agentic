# t1.sedaily.ai
AI Conversation Service - Claude Opus 4.5 based real-time chat with web search

Last Updated: 2026-01-18

## Overview
t1.sedaily.ai is an AI-powered conversation service built on Anthropic Claude Opus 4.5. It features real-time WebSocket communication, native web search integration, and prompt caching for cost optimization.

Live: https://t1.sedaily.ai

## Features
- Real-time Chat: WebSocket-based streaming responses
- Web Search: Anthropic's native web search integration (2025 data)
- Prompt Caching: 90% cost reduction with ephemeral cache (1-hour TTL)
- DynamoDB Caching: Permanent prompt cache in Lambda container
- Multiple AI Providers: Anthropic API primary, Bedrock fallback
- RAG Support: Aurora PostgreSQL vector database (optional)

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
├── .env.deploy           # Production configuration (gitignored)
├── .gitignore
├── README.md
├── deploy-main.sh        # Main deployment (interactive menu)
├── deploy-backend.sh     # Backend only
├── deploy-frontend.sh    # Frontend only
├── backend/
│   ├── handlers/         # Lambda handlers
│   ├── lib/              # anthropic_client, bedrock_client
│   ├── services/         # websocket_service
│   ├── src/              # Core business logic
│   ├── utils/            # Utility functions
│   └── requirements.txt
└── frontend/
    ├── src/
    ├── public/
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
# Full deployment (frontend + backend)
./deploy-main.sh
# Select option 1

# Frontend only
./deploy-frontend.sh

# Backend only
./deploy-backend.sh
```

## Current Deployment
Status: Production Ready

Updated: 2025-12-21

## URLs
| Resource | URL |
|----------|-----|
| Primary Domain | https://t1.sedaily.ai |
| CloudFront | https://d1s58eamawxu4.cloudfront.net |
| REST API | https://qyfams2iva.execute-api.us-east-1.amazonaws.com/prod |
| WebSocket API | wss://hsdpbajz23.execute-api.us-east-1.amazonaws.com |

## AWS Resources (us-east-1)

### Lambda Functions
| Function | Purpose |
|----------|---------|
| nx-tt-dev-ver3-websocket-connect | WebSocket connection handler |
| nx-tt-dev-ver3-websocket-message | Main chat handler (Claude API) |
| nx-tt-dev-ver3-websocket-disconnect | WebSocket disconnect handler |
| nx-tt-dev-ver3-conversation-api | Conversation CRUD |
| nx-tt-dev-ver3-prompt-crud | Prompt management |
| nx-tt-dev-ver3-usage-handler | Usage tracking |

### DynamoDB Tables
| Table | Purpose |
|-------|---------|
| nx-tt-dev-ver3-conversations | Chat history |
| nx-tt-dev-ver3-prompts | System prompts |
| nx-tt-dev-ver3-files | File metadata |
| nx-tt-dev-ver3-usage-tracking | API usage |
| nx-tt-dev-ver3-websocket-connections | Active connections |

### Other Resources
- S3 Bucket: nexus-title-hub-frontend
- CloudFront Distribution: EIYU5SFVTHQMN
- Aurora Cluster: nx-tt-vector-db (PostgreSQL)
- Secrets Manager: title-v1 (Anthropic API key)

## AI Configuration
| Setting | Value |
|---------|-------|
| Primary Provider | Anthropic API |
| Model | claude-opus-4-5-20251101 |
| Max Tokens | 4096 |
| Temperature | 0.3 |
| Fallback | AWS Bedrock |
| Web Search | Enabled |

## Change History

### Phase 11: Web Search Sources UI & Footnotes (2026-01-18)
- **Added Web Search Sources Component** - Claude.ai style collapsible sources UI
- New files:
  - `frontend/src/features/chat/components/WebSearchSources.jsx` - Sources toggle component
  - `backend/lib/web_search_client.py` - Web search result handling
- Features implemented:
  1. **Sources Persistence**: Web search results stored in message object (no longer disappears after chat completes)
  2. **Footnotes in AI Response**: Clickable footnote numbers `[1]`, `[2]` linking to sources
  3. **Collapsible Sources Panel**: Shows query and result count, expandable list with favicons
  4. **Reference Section**: "참고 자료" section at bottom of AI response with numbered sources
- Technical details:
  - `ChatPage.jsx`: Stores `webSearchResults` in AI message object during `ai_start`
  - `AssistantMessage.jsx`:
    - `urlToFootnote` Map for URL → footnote number mapping
    - ReactMarkdown `a` component renders inline footnotes
    - `scrollToFootnote()` function for smooth scroll to source
  - `websocket_service.py`: Yields `web_search_results` message before AI streaming
- Dark mode toggle fix:
  - `Header.jsx`: Replaced local `isDarkMode` state with `useTheme()` from ThemeContext
  - Centralized theme management now works correctly
- UI behavior:
  - Sources panel appears at TOP of AI response (before content)
  - Footnotes appear as superscript next to links `[1]`
  - Click footnote → scrolls to corresponding source in reference section

### Phase 10: Dark/Light Theme Toggle (2026-01-18)
- **Added Theme Toggle** - Dark/Light mode switching functionality
- Implementation:
  - Added theme toggle button to `Header.jsx` (Sun/Moon icons from lucide-react)
  - Theme state persisted in `localStorage` under key `theme`
  - Added inline script in `index.html` to prevent flash of unstyled content (FOUC)
- Technical details:
  - `isDarkMode` state initialized from localStorage
  - `useEffect` hook applies `.dark` class to `document.documentElement`
  - Tailwind CSS `darkMode: "class"` configuration
  - CSS variables in `index.css` define light/dark color schemes
- UI behavior:
  - Theme toggle hidden on landing page (`isLandingPage` prop)
  - Sun icon (☀️) shown in dark mode, Moon icon (🌙) in light mode
- Deployed to all 6 services: t1, p1, w1, b1, f1, r1

### Phase 9: Cognito Authentication Fix (2025-12-21)
- **Fixed Cognito Login Error** - `InvalidParameterException: clientId empty`
- Root cause: Missing `frontend/.env` file (deleted during cleanup)
- Solution: Created `frontend/.env` with Cognito configuration
  - User Pool: `sedaily.ai_cognito` (`us-east-1_ohLOswurY`)
  - Client ID: `4m4edj8snokmhqnajhlj41h9n2` (`nx-tt-dev-ver3-web-client`)
- Rebuilt and redeployed frontend to S3
- CloudFront cache invalidated
- Verified: Login functionality working correctly

### Phase 8: Prompt Caching Optimization (2025-12-21)
- **Fixed Anthropic Prompt Caching** - Now working with 90% cost reduction
- Problem: Dynamic content (date/time, conversation history) in system prompt was breaking cache
- Solution:
  1. Moved dynamic date/time to `user_message` via `create_dynamic_context()`
  2. Made `enhance_system_prompt_with_context()` static (no timestamps)
  3. Removed conversation history from `system_prompt`
  4. Conversation history now passed as proper `messages` array
- Added cache tracking logs:
  - `🎯 PROMPT CACHE HIT! cache_read: X tokens`
  - `📝 PROMPT CACHE MISS - cache_write: X tokens`
  - `💰 Token Usage: input=X, output=Y, cache_read=Z`
  - `💵 Estimated savings from cache: $X.XX`
- Fixed `lib.anthropic_client` logging (using `setup_logger()`)
- Cache performance verified:
  - System prompt: ~74,615 tokens cached
  - Savings per request: ~$0.34
  - Cache hit rate: 100% after first request

### Phase 7: Frontend Refactoring (2025-12-20)
- Removed duplicate `usageService.js` (893 lines)
  - `dashboard/services/usageService.js` deleted
  - `Dashboard.jsx` now imports from `chat/services/usageService.js`
- Fixed `authService.js` import path bug (`../../` → `../../../`)
- Fixed `deploy-frontend.sh` build path (`build/` → `dist/`)
- Removed empty folders:
  - `features/chat/utils/`
  - `features/profile/hooks/`

### Phase 6: Project Cleanup (2025-12-20)
- Removed unused files: `serverless.yml`, `handler.js`, `index.js`
- Removed unused folders: `infrastructure/`, `terraform/`
- Removed root `package.json`, `package-lock.json`
- Deleted unused backend modules:
  - `src/config/aws.py`
  - `src/services/prompt_service.py`, `usage_service.py`
  - `src/repositories/prompt_repository.py`, `usage_repository.py`
  - `src/models/prompt.py`, `usage.py`
- Moved config: `config/t1-production.env` -> `.env.deploy`
- Added `.gitignore` for sensitive files
- README restructured to reference format with full change history

### Phase 5: Anthropic Prompt Optimization (2025-12-20)
- Added `create_enhanced_system_prompt()` function to `anthropic_client.py`
- CoT-based 5-step systematic prompt structure:
  1. YOUR MISSION - Role and goal definition
  2. CORE INSTRUCTIONS - Admin-configured guidelines
  3. KNOWLEDGE BASE - DynamoDB files reference
  4. STEP-BY-STEP PROCESS - 5-step workflow
  5. CRITICAL MISTAKES TO AVOID - Prohibited actions
- Permanent DynamoDB prompt caching (Lambda container lifetime)
- Prompt caching with 1-hour ephemeral TTL (90% cost savings)
- Secrets Manager consolidated to `title-v1`
- Removed unused RAG code (`USE_RAG=false`)

### Phase 4: Cost Optimization (2025-12-16)
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

### Phase 3.5: Bug Fixes & Refactoring (2025-12-13)
- Fixed data overwrite bug: added engine type to yearMonth key
- Cleaned up backend package dependencies
- Removed redundant deployment files
- Improved Lambda deployment package structure

### Phase 3: Claude 4.5 Opus Migration (2025-12-03)
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

### Phase 2.5: Monorepo Migration (2025-12-07)
- Migrated to Nexus monorepo structure
- Path: `nexus/services/title/external/two`
- Added internal/two variants for all services
- Unified deployment scripts across services

### Phase 2: WebSocket Real-time Chat (2025-11-25)
- Implemented WebSocket API via API Gateway
- Created WebSocket Lambda handlers:
  - `connect.py` - Connection management
  - `message.py` - Chat message processing
  - `disconnect.py` - Cleanup on disconnect
  - `conversation_manager.py` - Conversation state
- DynamoDB tables:
  - `nx-tt-dev-ver3-websocket-connections` - Active connections
  - `nx-tt-dev-ver3-conversations` - Chat history
- Streaming response support for real-time AI output
- Connection state management with DynamoDB

### Phase 1.5: REST API Development (2025-11-20)
- Created REST API handlers:
  - `conversation.py` - Conversation CRUD operations
  - `prompt.py` - System prompt management
  - `usage.py` - Usage tracking and analytics
- DynamoDB tables:
  - `nx-tt-dev-ver3-prompts` - System prompts storage
  - `nx-tt-dev-ver3-usage-tracking` - API usage metrics
  - `nx-tt-dev-ver3-files` - File metadata
- API Gateway REST API configuration
- CORS configuration for frontend

### Phase 1: Initial Setup (2025-11-15)
- Project initialization
- Frontend setup:
  - React 18 with Vite
  - TypeScript configuration
  - Tailwind CSS styling
  - Chat UI components
- AWS infrastructure:
  - S3 bucket: `nexus-title-hub-frontend`
  - CloudFront distribution: `EIYU5SFVTHQMN`
  - Custom domain: `t1.sedaily.ai`
  - SSL certificate configuration
- Basic Lambda function structure
- Initial DynamoDB table design
- Deployment scripts: `deploy-frontend.sh`, `deploy-backend.sh`

## Deployment Guide

### Deploy Menu Options
```bash
./deploy-main.sh
```
1. Full deployment (frontend + backend)
2. Frontend only
3. Backend only
4. Lambda packaging only
5. Lambda environment variables only
6. CloudFront cache invalidation only

### Environment Configuration
All settings in `.env.deploy` (gitignored):
- AWS resource IDs
- Lambda function names
- API Gateway endpoints
- AI provider settings

### Log Monitoring
```bash
# Real-time Lambda logs
aws logs tail /aws/lambda/nx-tt-dev-ver3-websocket-message --follow

# Deployment logs
ls -la logs/
```

## Cost Optimization

### Anthropic Prompt Caching (90% savings) ✅ Verified Working
- System prompt (~74,615 tokens) cached with ephemeral TTL (5 min)
- Cache hit: $0.50/1M tokens vs $5.00/1M tokens (90% discount)
- **Savings per request: ~$0.34**
- Cache key: Static system prompt (no dynamic date/time)

### Caching Architecture
```
System Prompt (Cached)
├── Enhanced system prompt (CoT-based instructions)
├── Knowledge base files from DynamoDB
└── Static web search instructions

User Message (Not Cached)
├── Dynamic date/time context
└── User's actual message

Messages Array (Not Cached)
└── Conversation history (user/assistant turns)
```

### DynamoDB Caching
- Permanent in-memory cache in Lambda container
- DB queries only on cold start
- `✅ Cache HIT for T5 - DB query skipped`

### Cache Monitoring
```bash
# View cache performance in real-time
aws logs tail /aws/lambda/nx-tt-dev-ver3-websocket-message --follow | grep -E "CACHE|Token|💰|🎯|📝"
```

### Estimated Monthly Cost
| Service | Cost |
|---------|------|
| Anthropic Claude | ~$30 (with caching) |
| Lambda | ~$10 |
| DynamoDB | ~$5 |
| S3/CloudFront | ~$5 |
| Aurora | ~$30 |
| **Total** | **~$80/month** |

## Tech Stack

### Backend
- Python 3.11
- AWS Lambda
- Anthropic Claude Opus 4.5
- DynamoDB
- Aurora PostgreSQL (pgvector)
- API Gateway (REST + WebSocket)

### Frontend
- React 18
- Vite
- TypeScript
- Tailwind CSS
- S3 + CloudFront

## Monitoring

### CloudWatch Metrics
- Lambda invocations and errors
- API Gateway request count
- DynamoDB read/write capacity
- WebSocket connection count

### Cost Tracking
AWS Cost Explorer with tag: `nx-tt-dev-ver3`

## Troubleshooting

### Common Issues

1. **WebSocket not connecting**
   - Check Lambda logs for errors
   - Verify API Gateway WebSocket stage is deployed

2. **AI responses not working**
   - Check Anthropic API key in Secrets Manager
   - Verify Lambda environment variables

3. **Frontend not updating**
   - Run CloudFront cache invalidation
   - Check S3 bucket sync

### Rollback
```bash
# View recent deployments
ls -la logs/

# Rollback using git
git checkout <commit-hash> -- backend/
./deploy-backend.sh
```

## License
Proprietary - Seoul Economic Daily
