# Nexus Foreign - ONE (Internal Simplified Version)

> **Last Updated**: 2025-12-24 (KST)
> **URL**: https://d1zig3y52jaq1s.cloudfront.net
> **Purpose**: Internal use (Direct chat without login/sidebar)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│           Shared Backend (f1-two stack, us-east-1)       │
│  - 6 Lambda Functions (Claude 4.5 Opus)                  │
│  - API Gateway (REST + WebSocket)                        │
│  - 6 DynamoDB Tables                                     │
└─────────────────────────────────────────────────────────┘
                           ▲
            ┌──────────────┴──────────────┐
            │                             │
     ┌──────┴──────┐              ┌───────┴─────┐
     │    ONE      │  ◀── Current │    TWO      │
     │ d1zig3y...  │              │ d22634f...  │
     └─────────────┘              └─────────────┘
```

---

## Frontend Resources (ONE)

| Item | Value |
|------|-------|
| **CloudFront ID** | `E1O9OA8UA34Z49` |
| **CloudFront URL** | `https://d1zig3y52jaq1s.cloudfront.net` |
| **S3 Bucket** | `nexus-multi-frontend-20251204` |
| **Region** | `ap-northeast-2` |

---

## Deployment

### Frontend Deployment
```bash
./deploy-f1-frontend.sh
```

### Backend Deployment (Shared with TWO)
```bash
./deploy-f1-backend.sh
```

---

## Changelog

### 2025-12-24 (KST)

#### Phase 1: Project Cleanup
- Removed unnecessary files from `one/` directory
- Before: 53,198 files (~475MB) → After: 107 files (~8.7MB)
- Deleted: `node_modules/`, `dist/`, `__pycache__/`, backup files, deployment logs

#### Phase 2: Script Consolidation
- Reduced deployment scripts from 9 to 2
- Kept only: `deploy-f1-frontend.sh`, `deploy-f1-backend.sh`

#### Phase 3: Frontend Configuration Update
- Updated `deploy-f1-frontend.sh` for ONE's CloudFront
  - S3 Bucket: `nexus-multi-frontend-20251204`
  - CloudFront ID: `E1O9OA8UA34Z49`
  - Region: `ap-northeast-2`

#### Phase 4: UI Simplification
- Removed landing page → Direct redirect to `/11`
- Disabled login/signup routes
- All routes redirect to `/11` (English News → Korean Article)
- Modified files: `frontend/src/App.jsx`

#### Phase 5: Documentation Update
- Created this README.md with English documentation
- Added phase-based changelog with Korean dates

---

## Shared Backend Info (f1-two Stack)

### API Gateway
| Type | ID | Endpoint |
|------|-----|----------|
| REST | razlubfzw1 | https://razlubfzw1.execute-api.us-east-1.amazonaws.com/prod |
| WebSocket | 5c6e29dg50 | wss://5c6e29dg50.execute-api.us-east-1.amazonaws.com/prod |

### Lambda Functions
| Function | Purpose |
|----------|---------|
| f1-conversation-api-two | Conversation CRUD |
| f1-prompt-crud-two | Prompt management |
| f1-usage-handler-two | Usage tracking |
| f1-websocket-connect-two | WebSocket connect |
| f1-websocket-disconnect-two | WebSocket disconnect |
| f1-websocket-message-two | Message processing (Claude 4.5 Opus) |

### AI Configuration
| Setting | Value |
|---------|-------|
| Provider | Anthropic API (Primary) |
| Model | claude-opus-4-5-20251101 |
| Fallback | AWS Bedrock (Claude Sonnet 4) |

---

## Project Structure

```
one/foriegn/
├── README.md                  # This document
├── deploy-f1-frontend.sh      # Frontend deployment script
├── deploy-f1-backend.sh       # Backend deployment script
├── F1_STACK_INFO.md           # Backend stack details (legacy)
│
├── frontend/
│   ├── src/App.jsx            # Main app (simplified routing)
│   ├── .env                   # Development env
│   └── .env.production        # Production env
│
├── backend/
│   ├── handlers/              # Lambda handlers
│   ├── services/              # Business logic
│   └── lib/                   # AI clients
│
└── config/
    └── production.env         # Production settings
```

---

## Key Features (Internal Version)

- **No Login**: Immediate access
- **No Sidebar**: Clean UI
- **Direct Chat**: `/` redirects to `/11` automatically
- **Engine Selection**: `/11` (EN→KR), `/22` (JP→KR)

---

## Troubleshooting

### MIME Type Error
```bash
# Re-upload JS files with correct content type
aws s3 cp frontend/dist/ s3://nexus-multi-frontend-20251204/ \
  --recursive --exclude "*" --include "*.js" \
  --content-type "application/javascript" \
  --region ap-northeast-2

# Invalidate cache
aws cloudfront create-invalidation \
  --distribution-id E1O9OA8UA34Z49 --paths "/*"
```

### Changes Not Reflecting
1. Wait for CloudFront cache invalidation (1-2 min)
2. Hard refresh browser (Ctrl+Shift+R)

---

## Related

- `../../two/` - TWO frontend (different CloudFront: d22634fcti3bhs.cloudfront.net)
- `F1_STACK_INFO.md` - Legacy backend stack documentation
