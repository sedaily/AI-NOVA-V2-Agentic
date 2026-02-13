# W1.SEDAILY.AI Service Resource Mapping

## 🎯 Active Resources (Currently Connected)

### Domain Configuration
- **Frontend**: w1.sedaily.ai → CloudFront (d9am5o27m55dc.cloudfront.net)
- **API**: api.w1.sedaily.ai → REST API (16ayefk5lc)
- **WebSocket**: ws.w1.sedaily.ai → WebSocket API (prsebeg7ub)

### API Gateway
- **REST API**: 16ayefk5lc (https://16ayefk5lc.execute-api.us-east-1.amazonaws.com/prod)
- **WebSocket API**: prsebeg7ub (wss://prsebeg7ub.execute-api.us-east-1.amazonaws.com/prod)

### Lambda Functions (w1 prefix)
```
w1-websocket-message      → WebSocket message handler
w1-websocket-connect      → WebSocket connection handler  
w1-websocket-disconnect   → WebSocket disconnection handler
w1-conversation-api       → Conversation CRUD operations
w1-usage-handler         → Usage tracking
w1-prompt-crud           → Prompt management
```

### DynamoDB Tables
```
w1-conversations
w1-messages  
w1-prompts
w1-usage
w1-connections
```

### Secrets Manager
- **Secret Name**: bodo-v1
- **IAM Role**: w1-lambda-execution-role

### S3 Bucket
- **Frontend**: w1-sedaily-frontend-bucket

## ❌ Not Connected (Should Ignore)

### Other Lambda Functions
- b1-* functions (different service)
- nx-wt-b1-* functions (different service)
- g2-* functions (old, not connected)
- w1-nova-* functions (different variant)

### Other API Gateways
- b1-websocket-api (z04tl783fj)
- nx-wt-b1-websocket-api (xdphfyzie0)
- g2-websocket-api (eskq5llc5c)

## 📝 Required Scripts

1. **deploy-backend.sh** - Update Lambda functions with new code
2. **deploy-frontend.sh** - Build and deploy frontend to S3/CloudFront
3. **update-env.sh** - Update Lambda environment variables
4. **test-service.sh** - Test all endpoints
5. **monitor-logs.sh** - View CloudWatch logs