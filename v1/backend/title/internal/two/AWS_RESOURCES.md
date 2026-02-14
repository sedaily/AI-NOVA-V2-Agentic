# AWS 리소스 목록 - t1.sedaily.ai

## 🌐 프론트엔드

- **S3 Bucket**: nexus-title-hub-frontend
- **CloudFront**: EIYU5SFVTHQMN (d1s58eamawxu4.cloudfront.net)
- **도메인**: https://t1.sedaily.ai

## 🔌 API Gateway

### REST API

- **ID**: qyfams2iva
- **이름**: nx-tt-dev-ver3-api
- **URL**: https://qyfams2iva.execute-api.us-east-1.amazonaws.com/prod

### WebSocket API

- **ID**: hsdpbajz23
- **이름**: nx-tt-dev-ver3-websocket-api
- **URL**: wss://hsdpbajz23.execute-api.us-east-1.amazonaws.com/prod

## ⚡ Lambda Functions

### WebSocket 핸들러

- nx-tt-dev-ver3-websocket-connect
- nx-tt-dev-ver3-websocket-message
- nx-tt-dev-ver3-websocket-disconnect

### REST API 핸들러

- nx-tt-dev-ver3-conversation-api
- nx-tt-dev-ver3-prompt-crud
- nx-tt-dev-ver3-usage-handler

## 📊 DynamoDB Tables

- nx-tt-dev-ver3-conversations
- nx-tt-dev-ver3-prompts
- nx-tt-dev-ver3-files
- nx-tt-dev-ver3-usage-tracking
- nx-tt-dev-ver3-websocket-connections

## 🔐 Secrets Manager

- claude-opus-45-api-key (Anthropic API 키)

## 🎯 태그

모든 리소스에 다음 태그 적용:

- Stack: nx-tt-dev-ver3
- Service: t1.sedaily.ai
- Environment: production
