# 멀티테넌트 Lambda Authorizer 배포 가이드

## 📋 현재 상태
- ✅ DynamoDB 테이블 생성 완료
- ✅ 30명 사용자 마이그레이션 완료
- ⏳ Lambda Authorizer 배포 대기
- ⏳ API Gateway 연동 대기

## 🚀 Lambda Authorizer 배포 절차

### 1. Lambda 함수 생성

```bash
# Lambda 함수 패키징
cd backend
zip -r authorizer.zip handlers/api/authorizer.py src/models/tenant.py src/repositories/tenant_repository.py

# Lambda 함수 생성 (AWS Console 또는 CLI)
aws lambda create-function \
  --function-name sedaily-column-authorizer \
  --runtime python3.11 \
  --role arn:aws:iam::887078546492:role/lambda-execution-role \
  --handler handlers.api.authorizer.handler \
  --zip-file fileb://authorizer.zip \
  --timeout 10 \
  --memory-size 256 \
  --environment Variables="{
    USER_POOL_ID=us-east-1_ohLOswurY,
    AWS_REGION=us-east-1,
    TENANTS_TABLE=sedaily-column-tenants,
    USER_TENANTS_TABLE=sedaily-column-user-tenants
  }" \
  --region us-east-1
```

### 2. Lambda Layer 추가 (필요한 패키지)

```bash
# requirements.txt
python-jose[cryptography]==3.3.0
boto3==1.26.137

# Layer 생성
pip install -r requirements.txt -t python/
zip -r layer.zip python
aws lambda publish-layer-version \
  --layer-name sedaily-authorizer-deps \
  --zip-file fileb://layer.zip \
  --compatible-runtimes python3.11
```

### 3. API Gateway 설정

#### REST API의 경우:
1. API Gateway Console 접속
2. Authorization > Authorizers > Create New Authorizer
3. 설정:
   - Name: `sedaily-multitenant-authorizer`
   - Type: Lambda
   - Lambda Function: `sedaily-column-authorizer`
   - Token Source: `Authorization`
   - Token Validation: 비활성화 (JWT 자체 검증)
   - TTL: 300 (5분 캐싱)

#### HTTP API의 경우:
```json
{
  "authorizerUri": "arn:aws:lambda:us-east-1:887078546492:function:sedaily-column-authorizer",
  "authorizerType": "REQUEST",
  "identitySource": "$request.header.Authorization",
  "authorizerResultTtlInSeconds": 300
}
```

### 4. 기존 Lambda 함수들 업데이트

각 Lambda 함수에서 테넌트 정보 활용:

```python
# handlers/api/conversation.py 예시
def handler(event, context):
    # Authorizer에서 전달된 테넌트 정보
    authorizer_context = event.get('requestContext', {}).get('authorizer', {})
    tenant_id = authorizer_context.get('tenantId', 'sedaily')  # 기본값
    user_role = authorizer_context.get('role', 'user')
    plan = authorizer_context.get('plan', 'enterprise')

    # 테넌트별 데이터 필터링
    if tenant_id:
        # DynamoDB 쿼리에 tenant_id 추가
        conversations = get_conversations_by_tenant(tenant_id, user_id)
```

## 🧪 테스트 절차

### 1. Authorizer 단독 테스트

```bash
# JWT 토큰으로 테스트
aws lambda invoke \
  --function-name sedaily-column-authorizer \
  --payload '{"authorizationToken": "Bearer YOUR_JWT_TOKEN", "methodArn": "arn:aws:execute-api:us-east-1:887078546492:api-id/*/GET/*"}' \
  response.json
```

### 2. API Gateway 통합 테스트

```bash
# 헤더에 JWT 토큰 포함하여 요청
curl -X GET https://your-api.execute-api.us-east-1.amazonaws.com/conversations \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3. 테넌트별 격리 확인

- sedaily 사용자로 로그인 → sedaily 데이터만 표시
- 추후 다른 테넌트 추가 시 → 해당 테넌트 데이터만 표시

## 📝 체크리스트

- [ ] Lambda Authorizer 함수 생성
- [ ] 필요한 IAM 권한 설정
- [ ] API Gateway에 Authorizer 연결
- [ ] 기존 API 엔드포인트에 Authorizer 적용
- [ ] 테스트 수행
- [ ] 모니터링 설정

## 🔄 롤백 계획

문제 발생 시:
1. API Gateway에서 Authorizer 비활성화
2. 기존 인증 방식으로 즉시 복귀
3. DynamoDB 테이블은 유지 (데이터 손실 없음)

## 📊 모니터링

CloudWatch에서 확인할 메트릭:
- Lambda Authorizer 실행 시간
- 인증 실패율
- DynamoDB 읽기/쓰기 용량
- API Gateway 4xx/5xx 에러율

## 🎯 다음 단계

1. **Phase 1** (현재): 단일 테넌트로 안정화
2. **Phase 2**: 새로운 테넌트 추가 테스트
3. **Phase 3**: 플랜별 기능 제한 구현
4. **Phase 4**: 사용량 기반 과금 시스템 구축

## 💡 참고사항

- 현재 모든 사용자는 'sedaily' 테넌트의 'user' 역할
- 관리자 승격이 필요한 경우 DynamoDB에서 직접 수정
- Cognito Pool은 변경 없이 그대로 유지됨
- 언제든지 기존 방식으로 롤백 가능