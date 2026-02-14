# AWS Infrastructure Documentation

BODO Internal Service (보도자료 작성 AI)

Last Updated: 2026-01-24
Infrastructure Version: Production v1.0

---

## Overview

This document provides detailed AWS infrastructure configuration for the Seoul Economic Daily BODO (Press Release) AI Service.

### Service Architecture

```
+------------------+     +---------------+     +------------------+
|   CloudFront     |---->|  S3 Bucket    |     |  API Gateway     |
|  (CDN)           |     |  (Frontend)   |     |  (WebSocket)     |
+------------------+     +---------------+     +--------+---------+
  ap-northeast-2                                        |
                                               +--------+---------+
                                               | Lambda Functions |
                                               |   (us-east-1)    |
                                               +--------+---------+
                                                        |
                         +------------------------------+------------------------------+
                         v                              v                              v
                 +---------------+              +---------------+              +---------------+
                 |  DynamoDB     |              |  Bedrock AI   |              |Anthropic API  |
                 |  (Database)   |              |  (Fallback)   |              |(Primary AI)   |
                 +---------------+              +---------------+              +---------------+
```

---

## AWS Stack Components

### 1. Lambda Functions (6 Production - Shared with w1.sedaily.ai)

| Function Name              | Runtime    | Purpose                        | Memory  | Timeout |
| -------------------------- | ---------- | ------------------------------ | ------- | ------- |
| `w1-websocket-message`     | Python 3.9 | WebSocket message, AI response | 1024MB  | 120s    |
| `w1-websocket-connect`     | Python 3.9 | WebSocket connection handling  | 128MB   | 30s     |
| `w1-websocket-disconnect`  | Python 3.9 | WebSocket disconnect handling  | 128MB   | 30s     |
| `w1-conversation-api`      | Python 3.9 | Conversation history REST API  | 256MB   | 30s     |
| `w1-usage-handler`         | Python 3.9 | Usage tracking and analysis    | 256MB   | 30s     |
| `w1-prompt-crud`           | Python 3.9 | Prompt CRUD operations         | 256MB   | 30s     |

**Note:** Backend resources are shared with w1.sedaily.ai (external/two service). Only the frontend is separate.

### 2. DynamoDB Tables (Shared with w1.sedaily.ai)

| Table Name         | Purpose                  | Partition Key    | Sort Key        |
| ------------------ | ------------------------ | ---------------- | --------------- |
| `w1-conversations` | Conversation history     | userId (S)       | conversationId  |
| `w1-messages`      | Message storage          | conversationId   | timestamp       |
| `w1-prompts`       | System prompt management | promptId (S)     | -               |
| `w1-usage`         | Usage statistics         | userId (S)       | period (S)      |
| `w1-connections`   | WebSocket connections    | connectionId (S) | -               |

### 3. API Gateway

#### REST API

| API Name   | ID         | Endpoint                                               | Region    |
| ---------- | ---------- | ------------------------------------------------------ | --------- |
| `w1-api`   | 16ayefk5lc | https://16ayefk5lc.execute-api.us-east-1.amazonaws.com | us-east-1 |

#### WebSocket API

| API Name       | ID         | Endpoint                                                  | Region    |
| -------------- | ---------- | --------------------------------------------------------- | --------- |
| `w1-websocket` | prsebeg7ub | wss://prsebeg7ub.execute-api.us-east-1.amazonaws.com/prod | us-east-1 |

### 4. S3 Buckets

| Bucket Name                       | Purpose             | Public Access | Region         |
| --------------------------------- | ------------------- | ------------- | -------------- |
| `bodo-frontend-20251204-230645dc` | Production Frontend | Public Read   | ap-northeast-2 |

### 5. CloudFront Distributions

| Distribution ID  | Domain Name                   | Origin                         | Comment              |
| ---------------- | ----------------------------- | ------------------------------ | -------------------- |
| `EDF1H6DB796US`  | d2emwatb21j743.cloudfront.net | bodo-frontend-* S3 bucket      | BODO Internal        |

### 6. Secrets Manager

| Secret Name                 | Description                  | Region    | Usage              |
| --------------------------- | ---------------------------- | --------- | ------------------ |
| `bodo-v1`                   | Anthropic API Key for BODO   | us-east-1 | Fallback AI        |
| `nexus/perplexity-api-key`  | Perplexity API Key           | us-east-1 | Web Search         |

---

## Environment Variables

### Lambda Environment Configuration

```json
{
  "AI_PROVIDER": "bedrock",
  "USE_ANTHROPIC_API": "false",
  "ANTHROPIC_SECRET_NAME": "bodo-v1",
  "ANTHROPIC_MODEL_ID": "claude-opus-4-5-20251101",
  "FALLBACK_TO_BEDROCK": "true",
  "MAX_TOKENS": "4096",
  "TEMPERATURE": "0.3",
  "ENABLE_NATIVE_WEB_SEARCH": "true",
  "USE_OPUS_MODEL": "true"
}
```

**Note**: Primary AI uses AWS Bedrock. Web search uses Perplexity API (secret: `nexus/perplexity-api-key`).

---

## Web Search Feature

### Implementation
- Uses **Perplexity API** (`sonar` model) for web search
- Same implementation as PROOF service
- Controllable from frontend via `webSearchEnabled` parameter
- Citations displayed in frontend toggle box (WebSearchSources component)

### Flow
1. Frontend sends `webSearchEnabled: true/false` in WebSocket message
2. `message.py` parses `webSearchEnabled` from body
3. `websocket_service.py` calls Perplexity API if enabled
4. Backend sends `web_search_start` and `web_search_results` WebSocket messages
5. Frontend displays citations in toggle box

---

## Deployment Process

### Deployment Scripts

| Script                           | Purpose                              |
| -------------------------------- | ------------------------------------ |
| `w1-scripts/deploy-backend.sh`   | Deploy Lambda with Anthropic        |
| `w1-scripts/deploy-frontend.sh`  | Deploy frontend to S3/CloudFront    |
| `w1-scripts/config.sh`           | Shared configuration                |

### Deployment Commands

```bash
# Backend deployment
cd /Users/yeong-gwang/nexus/services/bodo/internal/one/bodo
./w1-scripts/deploy-backend.sh

# Frontend deployment
./w1-scripts/deploy-frontend.sh -y
```

---

## Comparison: BODO vs PROOF

| Feature           | BODO (보도)                      | PROOF (교열)                     |
| ----------------- | -------------------------------- | -------------------------------- |
| Service Purpose   | Press release writing            | Proofreading                     |
| Lambda Prefix     | `w1-*`                           | `nx-wt-prf-*`                    |
| AI Provider       | AWS Bedrock                      | AWS Bedrock                      |
| Secret Name       | `bodo-v1`                        | `proof-v1`                       |
| Web Search        | Perplexity API (sonar)           | Perplexity API (sonar)           |
| S3 Bucket         | `bodo-frontend-20251204-*`       | `nexus-multi-frontend-20251204`  |
| CloudFront Domain | d2emwatb21j743.cloudfront.net    | d1zig3y52jaq1s.cloudfront.net    |
| Temperature       | 0.3 (more deterministic)         | 0.7 (more creative)              |

---

## Support Contacts

- **AWS Account ID**: 887078546492
- **Service Owner**: Seoul Economic Daily Digital News Team
- **Backend Region**: us-east-1 (N. Virginia)
- **Frontend Region**: ap-northeast-2 (Seoul)

---

## Version History

| Date       | Version | Changes                                  | Author      |
| ---------- | ------- | ---------------------------------------- | ----------- |
| 2026-01-24 | 1.0     | Initial documentation, web search toggle | Claude Code |

---

*End of Document*
