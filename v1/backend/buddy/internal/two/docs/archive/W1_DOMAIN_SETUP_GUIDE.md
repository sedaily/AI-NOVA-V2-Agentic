# W1.SEDAILY.AI 도메인 설정 가이드

## 개요

이 가이드는 w1.sedaily.ai 커스텀 도메인을 설정하는 방법을 설명합니다.

## 배포 단계

### 1단계: 프론트엔드 배포

```bash
# 프론트엔드만 배포
./scripts/deploy-w1-frontend.sh

# 또는 전체 배포
./scripts/deploy-w1-complete.sh
```

### 2단계: SSL 인증서 및 커스텀 도메인 설정

```bash
./scripts/setup-w1-domain.sh
```

이 스크립트는 다음을 수행합니다:
- SSL 인증서 요청 (*.w1.sedaily.ai)
- API Gateway 커스텀 도메인 설정
- CloudFront 배포 업데이트

### 3단계: DNS 레코드 설정

다음 DNS 레코드를 설정해야 합니다:

#### Route 53 설정 (권장)

```bash
# 호스팅 존 ID 확인
aws route53 list-hosted-zones --query 'HostedZones[?Name==`sedaily.ai.`].Id' --output text

# 레코드 생성 (예시)
HOSTED_ZONE_ID="Z1234567890ABC"

# 1. 메인 도메인 (w1.sedaily.ai)
aws route53 change-resource-record-sets \
    --hosted-zone-id "$HOSTED_ZONE_ID" \
    --change-batch '{
        "Changes": [{
            "Action": "CREATE",
            "ResourceRecordSet": {
                "Name": "w1.sedaily.ai",
                "Type": "CNAME",
                "TTL": 300,
                "ResourceRecords": [{"Value": "d9am5o27m55dc.cloudfront.net"}]
            }
        }]
    }'

# 2. API 도메인 (api.w1.sedaily.ai)
aws route53 change-resource-record-sets \
    --hosted-zone-id "$HOSTED_ZONE_ID" \
    --change-batch '{
        "Changes": [{
            "Action": "CREATE", 
            "ResourceRecordSet": {
                "Name": "api.w1.sedaily.ai",
                "Type": "CNAME",
                "TTL": 300,
                "ResourceRecords": [{"Value": "d-abc123.execute-api.us-east-1.amazonaws.com"}]
            }
        }]
    }'

# 3. WebSocket 도메인 (ws.w1.sedaily.ai)
aws route53 change-resource-record-sets \
    --hosted-zone-id "$HOSTED_ZONE_ID" \
    --change-batch '{
        "Changes": [{
            "Action": "CREATE",
            "ResourceRecordSet": {
                "Name": "ws.w1.sedaily.ai", 
                "Type": "CNAME",
                "TTL": 300,
                "ResourceRecords": [{"Value": "d-xyz789.execute-api.us-east-1.amazonaws.com"}]
            }
        }]
    }'
```

#### 수동 DNS 설정

도메인 관리 패널에서 다음 CNAME 레코드를 추가:

| 이름 | 타입 | 값 | TTL |
|------|------|-----|-----|
| w1 | CNAME | CloudFront 도메인 | 300 |
| api.w1 | CNAME | API Gateway 도메인 | 300 |
| ws.w1 | CNAME | WebSocket API 도메인 | 300 |

## 환경변수 파일

### 프론트엔드 (.env.w1)

```env
VITE_API_BASE_URL=https://api.w1.sedaily.ai
VITE_WS_URL=wss://ws.w1.sedaily.ai
VITE_CUSTOM_DOMAIN=w1.sedaily.ai
VITE_APP_NAME=W1 AI Assistant
```

### 백엔드 (.env.w1)

```env
CUSTOM_DOMAIN=w1.sedaily.ai
API_DOMAIN=api.w1.sedaily.ai
WS_DOMAIN=ws.w1.sedaily.ai
REST_API_URL=https://api.w1.sedaily.ai
WEBSOCKET_API_URL=wss://ws.w1.sedaily.ai
CORS_ORIGINS=https://w1.sedaily.ai,https://api.w1.sedaily.ai
```

## 배포 확인

### 1. SSL 인증서 상태 확인

```bash
aws acm list-certificates \
    --region us-east-1 \
    --query 'CertificateSummaryList[?DomainName==`*.w1.sedaily.ai`]'
```

### 2. CloudFront 배포 상태 확인

```bash
aws cloudfront get-distribution \
    --id "$CLOUDFRONT_DISTRIBUTION_ID" \
    --query 'Distribution.Status'
```

### 3. API Gateway 도메인 확인

```bash
# REST API 도메인
aws apigateway get-domain-name \
    --domain-name "api.w1.sedaily.ai" \
    --region us-east-1

# WebSocket API 도메인  
aws apigatewayv2 get-domain-name \
    --domain-name "ws.w1.sedaily.ai" \
    --region us-east-1
```

### 4. 기능 테스트

```bash
# API 헬스체크
curl https://api.w1.sedaily.ai/health

# 웹사이트 접속
curl -I https://w1.sedaily.ai

# DNS 전파 확인
nslookup w1.sedaily.ai
nslookup api.w1.sedaily.ai
nslookup ws.w1.sedaily.ai
```

## 트러블슈팅

### SSL 인증서 문제

```bash
# 인증서 상태 확인
aws acm describe-certificate \
    --certificate-arn "$CERT_ARN" \
    --region us-east-1

# DNS 검증 레코드 확인
aws acm describe-certificate \
    --certificate-arn "$CERT_ARN" \
    --region us-east-1 \
    --query 'Certificate.DomainValidationOptions'
```

### CloudFront 캐시 무효화

```bash
aws cloudfront create-invalidation \
    --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" \
    --paths "/*"
```

### CORS 문제 해결

```bash
# API Gateway CORS 설정 확인
aws apigateway get-method \
    --rest-api-id "$REST_API_ID" \
    --resource-id "$RESOURCE_ID" \
    --http-method OPTIONS \
    --region us-east-1
```

## 모니터링

### CloudWatch 대시보드

- API Gateway 메트릭
- Lambda 함수 메트릭  
- CloudFront 메트릭
- DynamoDB 메트릭

### 로그 확인

```bash
# Lambda 로그
aws logs describe-log-groups \
    --log-group-name-prefix "/aws/lambda/w1"

# API Gateway 로그
aws logs describe-log-groups \
    --log-group-name-prefix "/aws/apigateway/w1"
```

## 백업 및 롤백

### 기존 엔드포인트 백업

기존 API Gateway 엔드포인트는 환경변수에 백업됨:
- `ORIGINAL_REST_API_URL`
- `ORIGINAL_WEBSOCKET_API_URL`

### 롤백 방법

```bash
# 환경변수를 기존 값으로 되돌리기
cp backend/.env backend/.env.w1.backup
cp backend/.env.bak backend/.env

cp frontend/.env frontend/.env.w1.backup  
cp frontend/.env.bak frontend/.env

# Lambda 함수 환경변수 롤백
./scripts/13-update-lambda-env.sh
```

## 보안 고려사항

1. **SSL/TLS**: TLS 1.2 이상 사용
2. **CORS**: 필요한 도메인만 허용
3. **API 키**: 필요시 API Gateway에서 API 키 설정
4. **WAF**: CloudFront에 WAF 연결 고려
5. **접근 로그**: CloudFront 및 API Gateway 로그 활성화

## 성능 최적화

1. **CloudFront 캐싱**: 정적 자원 캐싱 설정
2. **API Gateway 캐싱**: GET 요청 캐싱
3. **Lambda 최적화**: 메모리 및 타임아웃 튜닝
4. **DynamoDB**: 읽기/쓰기 용량 최적화

---

**문의사항**: ai@sedaily.com  
**업데이트**: 2025-01-27