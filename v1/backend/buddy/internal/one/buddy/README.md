# Buddy Internal
AI Article Writing Assistant - Claude Opus 4.5 based real-time chat

Last Updated: 2025-12-24

## Overview
Internal version of AI press release writing assistant for Seoul Economic Daily.
Uses the same backend as the external version (b1.sedaily.ai), but deploys to a separate CloudFront distribution.

**Internal Version Features:**
- Login disabled (immediate access)
- Sidebar disabled
- No landing page (direct to `/11` chat)

## URLs
| Type | URL |
|------|-----|
| **Internal (this project)** | https://d3bwe2ohfohm85.cloudfront.net |
| External (separate project) | https://b1.sedaily.ai |

## one vs two Comparison

| Item | one (internal) | two (external) |
|------|----------------|----------------|
| CloudFront ID | EJX326D0QZ4T1 | E2WPOE6AL2G5DZ |
| CloudFront URL | d3bwe2ohfohm85.cloudfront.net | b1.sedaily.ai |
| S3 Bucket | buddy-frontend-202512042253 | p2-two-frontend |
| Login | Disabled | Enabled |
| Sidebar | Disabled | Enabled |
| Landing Page | None (direct to /11) | Yes |
| **Backend** | **Same** | **Same** |

## Deployment

### Frontend Deployment
```bash
# Run from project root
./deploy-p2-frontend.sh
```

The script automatically:
1. Install dependencies (`npm install`)
2. Build (`npm run build`)
3. Upload to S3 (`buddy-frontend-202512042253`)
4. Invalidate CloudFront cache (`EJX326D0QZ4T1`)

### Local Development
```bash
cd frontend
npm install
npm run dev
# http://localhost:3000
```

## Shared Backend (one/two identical)

### API Endpoints
| Resource | URL |
|----------|-----|
| REST API | https://pisnqqgu75.execute-api.us-east-1.amazonaws.com/prod |
| WebSocket API | wss://dwc2m51as4.execute-api.us-east-1.amazonaws.com/prod |

### Lambda Functions
| Function | Purpose |
|----------|---------|
| p2-two-websocket-connect-two | WebSocket connection |
| p2-two-websocket-message-two | Chat handler (Claude API) |
| p2-two-websocket-disconnect-two | WebSocket disconnect |
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

### Cognito (Shared)
| Resource | Value |
|----------|-------|
| User Pool ID | us-east-1_ohLOswurY |
| Client ID | 4m4edj8snokmhqnajhlj41h9n2 |

## AI Configuration
| Setting | Value |
|---------|-------|
| Provider | Anthropic API |
| Model | claude-opus-4-5-20251101 |
| Max Tokens | 4096 |
| Temperature | 0.3 |
| Web Search | Enabled |
| Fallback | AWS Bedrock |

## Project Structure
```
.
├── README.md                   # This file
├── deploy-p2-frontend.sh       # Frontend deployment script
├── backend/
│   ├── handlers/               # Lambda handlers
│   ├── lib/                    # AI clients
│   ├── services/               # websocket_service
│   └── src/                    # Core logic
└── frontend/
    ├── src/
    │   ├── features/           # auth, chat, dashboard
    │   └── shared/             # Common components
    ├── .env                    # Environment variables
    └── package.json
```

## Troubleshooting

### Changes not visible after deployment
Wait for CloudFront cache invalidation (2-3 minutes)
```bash
aws cloudfront create-invalidation --distribution-id EJX326D0QZ4T1 --paths "/*"
```

### Check Lambda logs
```bash
aws logs tail /aws/lambda/p2-two-websocket-message-two --follow --region us-east-1
```

---

## Changelog

### Phase 1: Initial Setup (2025-12-24)
**Date:** 2025-12-24 (KST)

**Work Completed:**
1. **Project Structure Setup**
   - Copied frontend/backend code from `external/two` as base
   - Configured separate CloudFront distribution for internal use

2. **Frontend AWS Resources Configuration**
   - S3 Bucket: `buddy-frontend-202512042253`
   - CloudFront ID: `EJX326D0QZ4T1`
   - CloudFront URL: `https://d3bwe2ohfohm85.cloudfront.net`

3. **Frontend Code Modifications**
   - `App.jsx`: Removed landing page, redirect `/` to `/11`
   - `App.jsx`: Disabled sidebar (`showSidebar = false`)
   - `App.jsx`: Removed `onToggleSidebar`, `isSidebarOpen` props from ChatPage and MainContent
   - `ProtectedRoute.jsx`: Disabled login check (all users pass through)
   - `Header.jsx`: Removed login/logout UI

4. **Deployment Script**
   - `deploy-p2-frontend.sh`: Updated with correct S3 bucket and CloudFront ID

5. **Environment Configuration**
   - `frontend/.env`: Synced API endpoints from external/two
   - Added `VITE_CLOUDFRONT_DOMAIN=d3bwe2ohfohm85.cloudfront.net`

6. **First Deployment**
   - Successfully deployed to https://d3bwe2ohfohm85.cloudfront.net
   - Cache invalidation ID: `IU8XSTYPJYSJTL97YWCX5M6JC`

**Files Modified:**
- `frontend/src/App.jsx`
- `frontend/src/features/auth/components/ProtectedRoute.jsx`
- `frontend/src/shared/components/layout/Header.jsx`
- `frontend/.env`
- `deploy-p2-frontend.sh`
- `README.md`

---

## Related
- External version: `/buddy/external/two/`
- Sync backend code from external/two when needed

## License
Proprietary - Seoul Economic Daily
