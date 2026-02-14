# API Gateway Authorizer 설정 가이드

## 📋 Lambda Authorizer 정보
- **함수명**: sedaily-column-authorizer
- **ARN**: arn:aws:lambda:us-east-1:887078546492:function:sedaily-column-authorizer
- **상태**: 배포 완료 ✅

## 🔧 API Gateway 설정 방법

### Option 1: AWS Console에서 설정

1. **API Gateway Console 접속**
   - https://console.aws.amazon.com/apigateway
   - Region: us-east-1

2. **Authorizer 생성**
   - 좌측 메뉴 → Authorizers → Create Authorizer
   - 설정값:
     ```
     Name: sedaily-multitenant-authorizer
     Type: Lambda
     Lambda Function: sedaily-column-authorizer
     Lambda Invoke Role: (비워두기 - 자동 생성)
     Token Source: Authorization
     Token Validation: (비워두기)
     Authorization Caching: Enable (TTL: 300초)
     ```

3. **API 메서드에 Authorizer 적용**
   - Resources → 각 메서드 선택
   - Method Request → Authorization 설정
   - Authorizer 선택: sedaily-multitenant-authorizer

### Option 2: AWS CLI로 설정

```bash
# 1. API Gateway ID 확인
API_ID=$(aws apigateway get-rest-apis --region us-east-1 \
  --query "items[?name=='sedaily-column-api'].id" --output text)

# 2. Authorizer 생성
aws apigateway create-authorizer \
  --rest-api-id $API_ID \
  --name sedaily-multitenant-authorizer \
  --type REQUEST \
  --authorizer-uri arn:aws:lambda:us-east-1:887078546492:function:sedaily-column-authorizer \
  --identity-source method.request.header.Authorization \
  --authorizer-result-ttl-in-seconds 300 \
  --region us-east-1

# 3. Lambda 권한 추가 (API Gateway가 Lambda 호출 가능하도록)
aws lambda add-permission \
  --function-name sedaily-column-authorizer \
  --statement-id apigateway-authorizer \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:887078546492:$API_ID/*" \
  --region us-east-1
```

## 🧪 테스트 방법

### 1. Authorizer 테스트 (Console)
```
Test Authorizer 버튼 클릭
Authorization Token: Bearer [실제 JWT 토큰]
```

### 2. API 호출 테스트
```bash
# 토큰 없이 - 401 Unauthorized 예상
curl https://your-api.execute-api.us-east-1.amazonaws.com/prod/conversations

# 유효한 토큰으로
curl https://your-api.execute-api.us-east-1.amazonaws.com/prod/conversations \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 📝 Lambda 함수에서 테넌트 정보 사용

기존 Lambda 함수들에서 Authorizer가 전달한 정보 활용:

```python
def handler(event, context):
    # Authorizer Context 추출
    auth_context = event.get('requestContext', {}).get('authorizer', {})

    # 테넌트 정보
    tenant_id = auth_context.get('tenantId', 'sedaily')
    tenant_name = auth_context.get('tenantName')
    user_id = auth_context.get('userId')
    email = auth_context.get('email')
    role = auth_context.get('role')  # 'admin' or 'user'
    plan = auth_context.get('plan')  # 'enterprise'
    features = json.loads(auth_context.get('features', '[]'))

    # 테넌트별 처리
    if role == 'admin':
        # 관리자 기능
        pass

    # 플랜별 제한
    if plan == 'free' and 'ADVANCED_FEATURE' in request:
        return {
            'statusCode': 403,
            'body': json.dumps({'error': 'Upgrade to Pro plan'})
        }
```

## ⚠️ 주의사항

1. **기존 시스템과 병행 운영**
   - 현재: Authorizer 없이도 작동
   - 점진적 적용: 먼저 일부 엔드포인트에만 적용
   - 안정화 후: 모든 엔드포인트에 적용

2. **캐싱 설정**
   - TTL 300초 = 5분간 캐싱
   - 성능 향상, API 호출 감소

3. **에러 처리**
   - Authorizer 실패 → 401 Unauthorized
   - 테넌트 suspended → 403 Forbidden
   - 사용량 초과 → 429 Too Many Requests

## 🔄 롤백 방법

문제 발생 시:
1. API Gateway에서 Authorizer 제거
2. 각 메서드의 Authorization 설정을 NONE으로 변경
3. Deploy API

## 📊 모니터링

CloudWatch 대시보드에서 확인:
- `/aws/lambda/sedaily-column-authorizer` 로그
- Invocation count
- Error rate
- Duration

## ✅ 체크리스트

- [ ] Authorizer 생성
- [ ] Lambda 권한 설정
- [ ] 테스트 엔드포인트에 적용
- [ ] 테스트 수행
- [ ] 전체 엔드포인트에 적용
- [ ] 모니터링 설정