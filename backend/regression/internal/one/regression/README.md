# AI Column Service (Internal)

Simplified internal AI column writing service - No login required, direct access to chat

Last Updated: 2025-12-24

## Overview

This project shares the **same backend** with `external/two` (r1.sedaily.ai), but has a **separate frontend** deployment.

| Item | internal/one (this project) | external/two |
|------|---------------------------|--------------|
| Purpose | Internal use | External/Public |
| Domain | d1y2rjuowlwn37.cloudfront.net | r1.sedaily.ai |
| Landing Page | None (direct to /11) | Yes |
| Login | Disabled | Enabled |
| Sidebar | Disabled | Enabled |
| Backend | Shared | Shared |

## Live URL

```
https://d1y2rjuowlwn37.cloudfront.net
```

## Deployment Guide

### Frontend Deployment

```bash
./deploy-column-frontend.sh
```

Only deploys frontend. Backend is shared with external/two.

### Backend Deployment (Caution)

Backend is **shared** with external/two. If backend changes are needed:

```bash
./deploy-backend.sh
```

**WARNING**: Backend deployment affects both this service AND r1.sedaily.ai (external/two).

## AWS Resources

### Frontend (This Project Only)

| Resource | Value |
|----------|-------|
| CloudFront ID | E2Y96Q11K5DVPS |
| CloudFront Domain | d1y2rjuowlwn37.cloudfront.net |
| S3 Bucket | sedaily-column-frontend-1764856283 |
| Region | ap-northeast-2 |

### Backend (Shared with external/two)

| Resource | Value |
|----------|-------|
| REST API | t75vorhge1.execute-api.us-east-1.amazonaws.com |
| WebSocket API | ebqodb8ax9.execute-api.us-east-1.amazonaws.com |
| AI Model | Claude 4.5 Opus (Anthropic API) |
| Region | us-east-1 |

#### Lambda Functions (Shared)

| Function | Purpose |
|----------|---------|
| sedaily-column-websocket-message | Chat message handler (Claude API) |
| sedaily-column-websocket-connect | WebSocket connection |
| sedaily-column-websocket-disconnect | WebSocket disconnect |
| sedaily-column-conversation-api | Conversation CRUD |
| sedaily-column-prompt-crud | Prompt management |
| sedaily-column-usage-handler | Usage tracking |

#### DynamoDB Tables (Shared)

| Table | Purpose |
|-------|---------|
| sedaily-column-conversations | Chat history |
| sedaily-column-prompts | System prompts |
| sedaily-column-usage | Usage statistics |
| sedaily-column-websocket-connections | Active connections |

## Project Structure

```
regression/
├── README.md                    # This file
├── AWS_INFRASTRUCTURE_MAP.md    # AWS resource details
├── deploy-column-frontend.sh    # Frontend deployment script
├── deploy-backend.sh            # Backend deployment script (shared)
├── backend/                     # Backend source (shared)
│   ├── handlers/
│   │   ├── api/                # REST API handlers
│   │   └── websocket/          # WebSocket handlers
│   ├── lib/
│   │   └── anthropic_client.py # Claude API client with caching
│   ├── services/
│   ├── src/
│   ├── utils/
│   └── requirements.txt
└── frontend/                    # Frontend source
    ├── src/
    │   ├── App.jsx             # Routing (/ → /11 redirect)
    │   ├── features/
    │   │   ├── chat/           # Chat feature
    │   │   ├── dashboard/      # Dashboard
    │   │   └── auth/           # Auth (disabled)
    │   └── shared/
    ├── package.json
    └── vite.config.js
```

## Key Differences (vs external/two)

### App.jsx Changes

- `/` route redirects directly to `/11` (no landing page)
- Login/Signup routes redirect to `/11`
- `ProtectedRoute` always passes through (no auth check)
- `handleLogout` navigates to `/11` instead of `/`
- `LandingPage` component disabled

### ProtectedRoute.jsx

```javascript
// No login check - always allows access
const ProtectedRoute = ({ children }) => {
  return children;
};
```

## Log Monitoring

```bash
# Real-time WebSocket message logs
aws logs tail /aws/lambda/sedaily-column-websocket-message --follow --region us-east-1

# Check cache status
aws logs tail /aws/lambda/sedaily-column-websocket-message --since 5m --region us-east-1 | grep -E "(Cache|cache)"
```

## Change History

### Phase 1: Initial Setup from external/two (2025-12-24)

**Goal**: Create internal-use version without login/landing page

1. **Copied project structure from external/two**
   - Backend: Unchanged (shared with external/two)
   - Frontend: Modified for internal use

2. **Frontend modifications (App.jsx)**
   - Removed landing page route: `/` → redirect to `/11`
   - Disabled login/signup routes: redirect to `/11`
   - Disabled `LandingPage` component import
   - Modified `handleLogout`: navigate to `/11` instead of `/`
   - Modified `handleBackToLanding`: navigate to `/11`

3. **ProtectedRoute disabled**
   - Always returns `children` without authentication check

4. **Deployment script updated (deploy-column-frontend.sh)**
   - CloudFront ID: `E2Y96Q11K5DVPS`
   - S3 Bucket: `sedaily-column-frontend-1764856283`
   - Region: `ap-northeast-2`

5. **Backend script added (deploy-backend.sh)**
   - Same as external/two (deploys to shared Lambda functions)
   - 6 Lambda functions deployed

6. **Cleanup completed**
   - Removed unnecessary documentation files (8 files)
   - Removed unused backend scripts (8 files)
   - Removed unused directories: `admin-dashboard/`, `infrastructure/`, `sedaily-column-clone/`, `backend/scripts/`
   - Removed build artifacts: `*.zip`, `__pycache__/`

7. **anthropic_client.py updated**
   - Updated to latest version with prompt caching support
   - 67% cost reduction with Anthropic ephemeral cache

8. **First deployment completed**
   - Frontend deployed to: https://d1y2rjuowlwn37.cloudfront.net
   - Verified: No login required, direct access to /11 chat

## AI Configuration

| Setting | Value |
|---------|-------|
| Primary Provider | Anthropic API (Direct) |
| Model | claude-opus-4-5-20251101 |
| Max Tokens | 4096 |
| Temperature | 0.7 |
| Prompt Caching | Enabled (67% cost savings) |
| Fallback | AWS Bedrock (if needed) |

## Cost Optimization

### Anthropic Prompt Caching

- System prompt (~7,200 tokens) cached with ephemeral cache
- Cache TTL: ~5 minutes (Anthropic managed)
- **Cache MISS**: ~$0.10/request (first request)
- **Cache HIT**: ~$0.03/request (subsequent requests)

## Related Documents

- [AWS_INFRASTRUCTURE_MAP.md](./AWS_INFRASTRUCTURE_MAP.md) - AWS resource details
- external/two README - External service documentation (r1.sedaily.ai)

## Version Info

- **Last Updated**: 2025-12-24
- **AI Model**: Claude 4.5 Opus (claude-opus-4-5-20251101)
- **Prompt Caching**: Enabled
