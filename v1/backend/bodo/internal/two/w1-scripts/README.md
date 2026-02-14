# W1.SEDAILY.AI Deployment Scripts

## 📁 Structure
```
w1-scripts/
├── config.sh           # Central configuration (DO NOT EDIT unless necessary)
├── deploy-backend.sh   # Deploy Lambda functions
├── deploy-frontend.sh  # Deploy frontend to S3/CloudFront
├── monitor-logs.sh     # View CloudWatch logs
├── test-service.sh     # Health check all components
└── README.md          # This file
```

## 🚀 Quick Start

### 1. Deploy Backend (Lambda Updates)
```bash
cd w1-scripts
./deploy-backend.sh
```
This will:
- Package Python code with dependencies
- Update all w1-* Lambda functions
- Optionally update environment variables

### 2. Deploy Frontend
```bash
./deploy-frontend.sh
```
This will:
- Build the React app
- Upload to S3 bucket
- Invalidate CloudFront cache

### 3. Monitor Logs
```bash
# Interactive menu
./monitor-logs.sh

# Quick commands
./monitor-logs.sh errors           # Show all errors
./monitor-logs.sh websocket        # Show WebSocket logs
./monitor-logs.sh live             # Live tail WebSocket logs
```

### 4. Test Service
```bash
./test-service.sh
```
Checks:
- Frontend availability
- API endpoints
- WebSocket connection
- Lambda functions
- DynamoDB tables
- Secret Manager access

## ⚠️ Important Notes

1. **Only W1 Resources**: These scripts ONLY manage w1.sedaily.ai resources
2. **API Keys**: Stored in AWS Secrets Manager as `bodo-v1`
3. **No Cross-Service**: Scripts ignore b1-*, nx-*, g2-* resources
4. **Production Only**: These scripts work with production w1.sedaily.ai

## 🔧 Configuration

All configuration is in `config.sh`:
- API Gateway IDs
- Lambda function names
- DynamoDB tables
- S3 buckets
- CloudFront distribution

**DO NOT** manually edit these unless you know what you're doing.

## 📝 Common Tasks

### Update API Key
```bash
# API key is stored in AWS Secrets Manager
aws secretsmanager update-secret \
    --secret-id bodo-v1 \
    --secret-string '{"api_key":"new-key-here"}' \
    --region us-east-1
```

### Update Single Lambda Function
```bash
# Package first
cd ../backend
zip -r lambda.zip . -x "*.pyc" "__pycache__/*"

# Deploy to specific function
aws lambda update-function-code \
    --function-name w1-websocket-message \
    --zip-file fileb://lambda.zip \
    --region us-east-1
```

### Clear CloudFront Cache
```bash
aws cloudfront create-invalidation \
    --distribution-id d9am5o27m55dc \
    --paths "/*"
```

## 🐛 Troubleshooting

### "API key not set" Error
1. Check Secret Manager: `bodo-v1` exists
2. Check IAM permissions: `w1-lambda-execution-role` has access
3. Check environment variables in Lambda

### Frontend Not Updating
1. Wait 5-10 minutes for CloudFront
2. Clear browser cache
3. Check S3 bucket has new files

### WebSocket Connection Failed
1. Check `ws.w1.sedaily.ai` mapping
2. Verify w1-websocket-* functions are running
3. Check CloudWatch logs: `./monitor-logs.sh websocket`