# w1 배포 정보

## 배포 정보
- **서비스명**: w1
- **리전**: us-east-1
- **배포 시간**: 2025년 9월 24일 수요일 15시 03분 46초 KST

## 주요 URL
- **REST API**: https://16ayefk5lc.execute-api.us-east-1.amazonaws.com/prod
- **WebSocket API**: wss://prsebeg7ub.execute-api.us-east-1.amazonaws.com/prod
- **웹사이트 (CloudFront)**: https://d1jr0dnwnnrlr1.cloudfront.net
dwme7h338xphl.cloudfront.net
d9am5o27m55dc.cloudfront.net

## 배포 명령어

### 전체 배포 (새 서비스)
```bash
./deploy-new-service.sh [service-name]
```

### 개별 컴포넌트 배포
```bash
# Lambda 코드만 업데이트
bash scripts/06-deploy-lambda-code.sh w1 us-east-1

# 프론트엔드만 배포
bash scripts/09-deploy-frontend.sh w1 us-east-1
```

## 로그 확인
```bash
# Lambda 함수 로그
aws logs tail /aws/lambda/w1-websocket-message --follow

# API Gateway 로그
aws logs tail API-Gateway-Execution-Logs_16ayefk5lc/prod --follow
```

## 리소스 삭제 (주의!)
```bash
# DynamoDB 테이블 삭제
aws dynamodb delete-table --table-name w1-conversations-v2
aws dynamodb delete-table --table-name w1-prompts-v2
aws dynamodb delete-table --table-name w1-usage
aws dynamodb delete-table --table-name w1-websocket-connections

# Lambda 함수 삭제
aws lambda delete-function --function-name w1-websocket-connect
aws lambda delete-function --function-name w1-websocket-disconnect
aws lambda delete-function --function-name w1-websocket-message
aws lambda delete-function --function-name w1-conversation-api
aws lambda delete-function --function-name w1-prompt-crud
aws lambda delete-function --function-name w1-usage-handler

# S3 버킷 삭제
aws s3 rb s3://w1-frontend --force
```

## 문의사항
문제가 발생하면 endpoints.json 파일의 정보를 확인해주세요.
