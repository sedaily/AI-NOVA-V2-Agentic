# CORS 문제 해결 가이드

## 발생한 문제
f2 서비스에서 모든 CRUD 작업이 CORS 에러로 실패하는 문제 발생

### 에러 메시지
```
Access to fetch at 'https://71eh2lfh7l.execute-api.us-east-1.amazonaws.com/prod/prompts/11'
from origin 'https://d2jd7isapnx6e.cloudfront.net' has been blocked by CORS policy:
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## 근본 원인 분석

### 1. 잘못된 API Gateway 구성
- f2 API Gateway가 Lambda 통합 없이 생성됨
- OPTIONS 메서드만 있고 실제 GET, POST, PUT, DELETE 메서드가 Lambda와 연결되지 않음
- CORS 헤더가 Lambda 응답에 포함되지 않음

### 2. 환경 변수 설정 오류
- frontend/.env 파일이 f1 API 엔드포인트를 가리키고 있었음
- 이로 인해 f2 서비스가 f1의 데이터를 표시하는 문제 발생

## 해결 과정

### 1단계: 문제 진단
```bash
# v2(f1)와 f2 API Gateway 비교
aws apigateway get-resources --rest-api-id [f1-api-id]
aws apigateway get-resources --rest-api-id [f2-api-id]

# f2 API에 Lambda 통합이 없음을 발견
```

### 2단계: API Gateway 재생성
1. 기존 잘못된 API 삭제
2. 올바른 Lambda 통합과 CORS 설정으로 새 API 생성
3. 새로운 API ID 획득:
   - REST API: 690d8chbhb
   - WebSocket: oxttb0ubhi

### 3단계: Frontend 환경 변수 업데이트
```bash
# .env 및 .env.production 파일 수정
VITE_API_BASE_URL=https://690d8chbhb.execute-api.us-east-1.amazonaws.com/prod
VITE_WS_URL=wss://oxttb0ubhi.execute-api.us-east-1.amazonaws.com/prod
```

### 4단계: Frontend 재배포
```bash
npm run build
aws s3 sync dist/ s3://f2-two-frontend --delete
aws cloudfront create-invalidation --distribution-id E1LFL5A9YH99EY --paths "/*"
```

## CORS 설정 핵심 요소

### Lambda 통합 응답 헤더
```json
{
  "method.response.header.Access-Control-Allow-Origin": "'*'",
  "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
  "method.response.header.Access-Control-Allow-Methods": "'GET,POST,PUT,DELETE,OPTIONS,PATCH'"
}
```

### Lambda 함수 응답 형식
```javascript
{
  statusCode: 200,
  headers: {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS,PATCH'
  },
  body: JSON.stringify(data)
}
```

## 예방 방법

1. **API Gateway 생성 시 체크리스트**
   - Lambda 프록시 통합 확인
   - 모든 HTTP 메서드에 대한 Lambda 연결 확인
   - OPTIONS 메서드에 MOCK 통합 설정
   - Integration Response에 CORS 헤더 설정

2. **환경 변수 관리**
   - 서비스별로 명확한 네이밍 규칙 사용
   - 배포 전 .env 파일 검증
   - 자동화된 설정 업데이트 스크립트 사용

3. **배포 검증**
   - API Gateway 배포 후 curl로 테스트
   - CloudFront 캐시 무효화 확인
   - 브라우저 개발자 도구에서 CORS 헤더 확인

## 트러블슈팅 명령어

### API Gateway 상태 확인
```bash
# REST API 리소스 확인
aws apigateway get-resources --rest-api-id [API_ID]

# 특정 메서드의 통합 설정 확인
aws apigateway get-integration --rest-api-id [API_ID] --resource-id [RESOURCE_ID] --http-method GET

# CORS 헤더 테스트
curl -X OPTIONS https://[API_ID].execute-api.us-east-1.amazonaws.com/prod/[endpoint] -v
```

### CloudFront 캐시 정리
```bash
# 전체 캐시 무효화
aws cloudfront create-invalidation --distribution-id [DIST_ID] --paths "/*"

# 무효화 상태 확인
aws cloudfront get-invalidation --distribution-id [DIST_ID] --id [INVALIDATION_ID]
```

## 자주 발생하는 실수

1. **Lambda 통합 누락**: API Gateway 생성 시 Lambda 함수 연결 누락
2. **CORS 헤더 불일치**: OPTIONS 응답과 실제 메서드 응답의 CORS 헤더 불일치
3. **캐시 문제**: CloudFront 캐시로 인한 이전 설정 유지
4. **환경 변수 혼동**: 여러 서비스 간 API 엔드포인트 혼용

## 참고 자료
- AWS API Gateway CORS 문서
- Lambda 프록시 통합 가이드
- CloudFront 캐시 무효화 문서