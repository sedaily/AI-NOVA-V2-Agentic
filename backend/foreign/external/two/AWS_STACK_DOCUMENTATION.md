# AWS Stack Documentation

f1.sedaily.ai Service Infrastructure

Last Updated: 2025-12-21

---

## Active Service Stacks

### 1. f1-two Stack (Main Service)
- **Service URL**: https://f1.sedaily.ai
- **Status**: Active
- **Last Deployment**: 2025-12-14 (Web search feature)
- **Package Size**: ~17MB

#### Lambda Functions
| Function | Role | Runtime | Last Modified |
|----------|------|---------|---------------|
| `f1-conversation-api-two` | Conversation API | Python 3.9 | 2025-12-14 |
| `f1-prompt-crud-two` | Prompt Management | Python 3.9 | 2025-12-14 |
| `f1-usage-handler-two` | Usage Tracking | Python 3.9 | 2025-12-14 |
| `f1-websocket-connect-two` | WebSocket Connect | Python 3.9 | 2025-12-14 |
| `f1-websocket-disconnect-two` | WebSocket Disconnect | Python 3.9 | 2025-12-14 |
| `f1-websocket-message-two` | **WebSocket Message** | Python 3.9 | 2025-12-14 |

#### DynamoDB Tables
| Table | Purpose |
|-------|---------|
| `f1-conversations-two` | Conversation sessions |
| `f1-messages-two` | Message history |
| `f1-prompts-two` | System prompts |
| `f1-files-two` | File metadata |
| `f1-usage-two` | Usage statistics |
| `f1-websocket-connections-two` | WebSocket connection management |

---

### 2. f1-nova Stack (Nova Version)
- **Status**: Separate operation
- **Last Deployment**: 2025-11-30
- **Package Size**: ~15MB

#### Lambda Functions
| Function | Last Modified |
|----------|---------------|
| `f1-nova-websocket-connect-two` | 2025-11-03 |
| `f1-nova-websocket-message-two` | 2025-11-30 |
| `f1-nova-websocket-disconnect-two` | 2025-11-03 |
| `f1-nova-conversation-api-two` | 2025-11-30 |
| `f1-nova-prompt-crud-two` | 2025-11-03 |
| `f1-nova-usage-handler-two` | 2025-11-03 |

---

### 3. tf1 Stack (TF1 Service)
- **Status**: Separate operation
- **Last Deployment**: 2025-12-10
- **Package Size**: ~15MB

#### Lambda Functions
| Function | Last Modified |
|----------|---------------|
| `tf1-websocket-connect-two` | 2025-12-09 |
| `tf1-websocket-message-two` | 2025-12-10 |
| `tf1-websocket-disconnect-two` | 2025-12-09 |
| `tf1-conversation-api-two` | 2025-12-09 |
| `tf1-prompt-crud-two` | 2025-12-09 |
| `tf1-usage-handler-two` | 2025-12-09 |

---

## Deployment Scripts

| Script | Target | Purpose | Status |
|--------|--------|---------|--------|
| `upgrade-f1-anthropic.sh` | f1-two | Backend Lambda deployment | Verified |
| `upgrade-f1-frontend.sh` | f1-two | Frontend S3 deployment | Verified |

---

## Environment Configuration

### f1-websocket-message-two Environment Variables
```bash
AI_PROVIDER=anthropic_api
ANTHROPIC_MODEL_ID=claude-opus-4-5-20251101
ANTHROPIC_SECRET_NAME=foreign-v1
ENABLE_NATIVE_WEB_SEARCH=true
FALLBACK_TO_BEDROCK=true
MAX_TOKENS=4096
TEMPERATURE=0.3
USE_ANTHROPIC_API=true
WEB_SEARCH_MAX_USES=5
```

### Key Features
- Anthropic Claude 4.5 Opus
- Native Web Search (web_search_20250305)
- Auto Citation Formatting
- Bedrock Fallback Support
- Real-time Date Recognition

---

## Monitoring & Debugging

### CloudWatch Logs
```bash
# Main websocket handler logs
aws logs tail /aws/lambda/f1-websocket-message-two --follow

# Conversation API logs
aws logs tail /aws/lambda/f1-conversation-api-two --follow

# Prompt management logs
aws logs tail /aws/lambda/f1-prompt-crud-two --follow
```

### Function Status Check
```bash
# Get function info
aws lambda get-function --function-name f1-websocket-message-two

# Check environment variables
aws lambda get-function-configuration \
  --function-name f1-websocket-message-two \
  --query 'Environment.Variables'
```

### DynamoDB Table Status
```bash
# Table info
aws dynamodb describe-table --table-name f1-conversations-two

# Recent items
aws dynamodb scan --table-name f1-conversations-two --max-items 5
```

---

## Resource Usage

### Lambda Function Size Comparison
- **f1-two**: ~17MB (latest - includes web search)
- **f1-nova**: ~15MB
- **tf1**: ~15MB

### Deployment Package Contents
- **Dependencies**: boto3, anthropic, requests, etc.
- **Source Code**: handlers, lib, services, utils
- **New Features**: citation_formatter.py (source formatting)

---

## Important Notes

### 1. Stack Separation
- **Never mix stacks**: Each stack operates independently
- **Deployment scripts**: Always verify target stack before running

### 2. Environment Variable Management
- **Secrets Manager**: API keys managed in foreign-v1
- **Manual setup**: May be required if script fails

### 3. Monitoring Requirements
- **API Call Volume**: Anthropic API rate limits
- **Error Rate**: Verify Bedrock fallback operation
- **Response Time**: May increase with web search

---

## Related Documents
- [README.md](./README.md) - Project overview

---

**Document Created**: 2025-12-14
**Last Updated**: 2025-12-21
