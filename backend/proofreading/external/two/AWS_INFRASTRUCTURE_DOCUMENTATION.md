# AWS Infrastructure Documentation

NX-WT-PRF Proofreading Service

Last Updated: 2025-12-20
Infrastructure Version: Production v3.2

---

## Overview

This document provides detailed AWS infrastructure configuration for the Seoul Economic Daily AI Proofreading Service (nx-wt-prf).

### Service Architecture

```
+------------------+     +---------------+     +------------------+
|   CloudFront     |---->|  S3 Bucket    |     |  API Gateway     |
|  (CDN)           |     |  (Frontend)   |     |  (WebSocket)     |
+------------------+     +---------------+     +--------+---------+
                                                        |
                                                        v
                                               +------------------+
                                               | Lambda Functions |
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

### 1. Lambda Functions (6 Production)

| Function Name                    | Runtime     | Handler                               | Purpose                    | Memory | Timeout |
| -------------------------------- | ----------- | ------------------------------------- | -------------------------- | ------ | ------- |
| `nx-wt-prf-websocket-message`    | Python 3.11 | handlers.websocket.message.handler    | WebSocket message, AI response | 512MB  | 300s    |
| `nx-wt-prf-conversation-api`     | Python 3.11 | handlers.api.conversation.handler     | Conversation history REST API | 256MB  | 30s     |
| `nx-wt-prf-prompt-crud`          | Python 3.11 | handlers.api.prompt.handler           | Prompt CRUD operations     | 256MB  | 30s     |
| `nx-wt-prf-usage-handler`        | Python 3.11 | handlers.api.usage.handler            | Usage tracking and analysis | 256MB  | 30s     |
| `nx-wt-prf-websocket-connect`    | Python 3.11 | handlers.websocket.connect.handler    | WebSocket connection handling | 128MB  | 30s     |
| `nx-wt-prf-websocket-disconnect` | Python 3.11 | handlers.websocket.disconnect.handler | WebSocket disconnect handling | 128MB  | 30s     |

### 2. DynamoDB Tables

| Table Name                        | Purpose              | Partition Key    | Sort Key                 | GSIs             |
| --------------------------------- | -------------------- | ---------------- | ------------------------ | ---------------- |
| `nx-wt-prf-conversations`         | Conversation history | userId (S)       | conversationId (S)       | engineType-index |
| `nx-wt-prf-prompts`               | System prompt management | id (S)       | -                        | -                |
| `nx-wt-prf-files`                 | Prompt attachments   | promptId (S)     | fileId (S)               | -                |
| `nx-wt-prf-usage`                 | Usage statistics     | userId (S)       | yearMonth (S)            | -                |
| `nx-wt-prf-usage-tracking`        | Detailed usage tracking | userId (S)    | usageDate#engineType (S) | -                |
| `nx-wt-prf-websocket-connections` | WebSocket connection management | connectionId (S) | -          | -                |

### 3. API Gateway

#### REST API

| API Name        | ID         | Endpoint                                               | Stage |
| --------------- | ---------- | ------------------------------------------------------ | ----- |
| `nx-wt-prf-api` | wxwdb89w4m | https://wxwdb89w4m.execute-api.us-east-1.amazonaws.com | prod  |

#### WebSocket API

| API Name                  | ID         | Endpoint                                                  | Protocol  |
| ------------------------- | ---------- | --------------------------------------------------------- | --------- |
| `nx-wt-prf-websocket-api` | p062xh167h | wss://p062xh167h.execute-api.us-east-1.amazonaws.com/prod | WebSocket |

### 4. S3 Buckets

| Bucket Name                 | Purpose             | Public Access | Website Hosting |
| --------------------------- | ------------------- | ------------- | --------------- |
| `nx-prf-prod-frontend-2025` | Production Frontend | Public Read   | Enabled         |

### 5. CloudFront Distributions

| Distribution ID | Domain Name                   | Origin                                                     | Comment             |
| --------------- | ----------------------------- | ---------------------------------------------------------- | ------------------- |
| `E39OHKSWZD4F8J` | d1tas3e2v5373v.cloudfront.net | nx-prf-prod-frontend-2025.s3-website-us-east-1.amazonaws.com | p1.sedaily.ai (Production) |
| `E3E25OIRRG1ZR` | d1ykmbuznjkj67.cloudfront.net | nx-prf-prod-frontend-2025.s3-website-us-east-1.amazonaws.com | Direct CloudFront Access |

### 6. Secrets Manager

| Secret Name | Description                        | Usage                 |
| ----------- | ---------------------------------- | --------------------- |
| `proof-v1`  | Anthropic API Key for Proofreading | Production AI Service |

---

## IAM Roles and Policies

### Lambda Execution Role

- **Role Name**: `lambda-execution-role`
- **Attached Policies**:
  - `AWSLambdaBasicExecutionRole` - CloudWatch Logs
  - `AmazonAPIGatewayInvokeFullAccess` - API Gateway
  - `AmazonDynamoDBFullAccess` - DynamoDB
  - `AmazonS3FullAccess` - S3
  - `AmazonBedrockFullAccess` - Bedrock AI
  - `ProofreadingSecretsAccess` (Custom) - Secrets Manager for proof-v1

### Custom Policy: ProofreadingSecretsAccess

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["secretsmanager:GetSecretValue"],
      "Resource": "arn:aws:secretsmanager:us-east-1:887078546492:secret:proof-v1*"
    }
  ]
}
```

---

## Environment Variables

### Lambda Environment Configuration

```json
{
  "USE_ANTHROPIC_API": "true",
  "ANTHROPIC_SECRET_NAME": "proof-v1",
  "ANTHROPIC_MODEL_ID": "claude-opus-4-5-20251101",
  "AI_PROVIDER": "anthropic_api",
  "FALLBACK_TO_BEDROCK": "true",
  "ENABLE_NATIVE_WEB_SEARCH": "true",
  "WEB_SEARCH_MAX_USES": "5",
  "ANTHROPIC_MAX_TOKENS": "4096",
  "ANTHROPIC_TEMPERATURE": "0.7"
}
```

---

## Network Configuration

### Region

- **Primary Region**: us-east-1 (N. Virginia)
- **Reason**: Best performance for global access, all AWS services available

### Security Groups

- WebSocket connections allowed from all IPs (0.0.0.0/0)
- Lambda functions in default VPC
- DynamoDB accessed via AWS internal network

---

## Monitoring and Logging

### CloudWatch Log Groups

| Log Group                                 | Retention | Purpose                           |
| ----------------------------------------- | --------- | --------------------------------- |
| `/aws/lambda/nx-wt-prf-websocket-message` | 7 days    | WebSocket message processing logs |
| `/aws/lambda/nx-wt-prf-conversation-api`  | 7 days    | Conversation API logs             |
| `/aws/lambda/nx-wt-prf-prompt-crud`       | 7 days    | Prompt management logs            |
| `/aws/lambda/nx-wt-prf-usage-handler`     | 7 days    | Usage tracking logs               |

### Key Metrics to Monitor

- Lambda invocation count and errors
- DynamoDB read/write capacity consumption
- API Gateway 4xx/5xx errors
- WebSocket connection count
- Anthropic API success/failure rate
- Cache hit/miss ratio

---

## Deployment Process

### Current Deployment Process

1. **Code Update**: Local development and testing
2. **Package Creation**: `deploy-anthropic.sh` script
3. **Lambda Update**: AWS CLI commands
4. **Environment Update**: Configuration via AWS CLI
5. **Validation**: CloudWatch logs monitoring

### Deployment Scripts

| Script | Purpose |
|--------|---------|
| `deploy-anthropic.sh` | Deploy Lambda with Anthropic integration |
| `deploy-frontend.sh` | Deploy frontend to S3/CloudFront |

---

## Cost Optimization

### Current Optimizations

1. **Lambda**:
   - Memory optimized per function (128MB-512MB)
   - Timeout settings appropriate to function
2. **DynamoDB**:
   - On-demand billing mode
   - No reserved capacity
3. **S3**:
   - CloudFront caching reduces S3 requests
4. **API Gateway**:
   - WebSocket for real-time communication (cost-effective)
5. **Prompt Caching**:
   - Anthropic Prompt Caching (1h TTL) - 70-80% cost reduction
   - Permanent in-memory caching for DB queries

### Cost Breakdown (Estimated Monthly)

- Lambda: ~$50-100 (based on usage)
- DynamoDB: ~$20-50 (on-demand)
- S3 & CloudFront: ~$10-20
- API Gateway: ~$10-30
- Secrets Manager: ~$1
- **Total**: ~$91-201/month (excluding AI API costs)

---

## Disaster Recovery

### Backup Strategy

- **DynamoDB**: Point-in-time recovery enabled
- **Code**: Version controlled in Git
- **Secrets**: Manual backup recommended

### Recovery Time Objectives

- **RTO**: < 1 hour
- **RPO**: < 24 hours

---

## Maintenance Notes

### Regular Tasks

1. **Weekly**: Check CloudWatch logs for errors
2. **Monthly**: Review usage statistics and costs
3. **Quarterly**: Update dependencies and Lambda runtime
4. **Yearly**: Security audit and credential rotation

### Known Issues

1. Secrets Manager permissions need manual setup for new Lambda functions
2. WebSocket connections may timeout after 10 minutes of inactivity
3. Anthropic API fallback to Bedrock when rate limits hit

---

## Support Contacts

- **AWS Account ID**: 887078546492
- **Service Owner**: Seoul Economic Daily Digital News Team
- **Region**: us-east-1 (N. Virginia)

---

## Version History

| Date       | Version | Changes                                    | Author           |
| ---------- | ------- | ------------------------------------------ | ---------------- |
| 2025-12-20 | 3.2     | Documentation update, cleanup completed    | Claude Code      |
| 2025-12-20 | 3.1     | Systematic prompt integration              | Claude Code      |
| 2024-12-15 | 3.0     | Prompt Caching optimization                | Development Team |
| 2024-12-14 | 2.0     | Web search feature added                   | Development Team |
| 2024-11-01 | 1.0     | Anthropic Claude 4.5 Opus integration      | Development Team |

---

## Related Documents

- [README.md](./README.md) - Project overview

---

*End of Document*
