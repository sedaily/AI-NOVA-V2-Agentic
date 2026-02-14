# 멀티테넌트 구축 현황 리포트

## ✅ 완료된 작업

### 1. 데이터 레이어
- **DynamoDB 테이블 생성 완료**
  - `sedaily-column-tenants`: 테넌트 정보
  - `sedaily-column-user-tenants`: 사용자-테넌트 매핑
- **30명 사용자 마이그레이션 완료**
  - 모든 사용자 sedaily 테넌트로 매핑
  - role: user, plan: enterprise

### 2. Lambda Authorizer
- **함수 배포 완료**
  - 함수명: `sedaily-column-authorizer`
  - Layer: python-jose 패키지 포함
  - IAM 권한 설정 완료
- **테스트 결과**
  - 가짜 토큰 → 401 Unauthorized ✅
  - 정상 작동 확인

### 3. API Gateway 연동
- **REST API Authorizer 생성**
  - ID: 7yepx4
  - TTL: 300초 (5분 캐싱)
- **테스트 엔드포인트 적용**
  - GET /conversations → Authorizer 적용 ✅
  - 배포 완료 (deployment ID: 5gc0ng)

## ⚠️ 현재 이슈

### 문제: 기존 Lambda와의 호환성
현재 Lambda 함수들이 기존 방식으로 작동 중:
- Query Parameter로 userId를 직접 받음
- Authorizer Context를 활용하지 않음

### 해결 방법
기존 Lambda 함수들을 업데이트해야 함:

```python
# 현재 (기존 방식)
def handler(event, context):
    query_params = event.get('queryStringParameters', {})
    user_id = query_params.get('userId')  # Query에서 직접 받음

# 변경 필요 (멀티테넌트 방식)
def handler(event, context):
    # Authorizer Context에서 정보 추출
    auth_context = event.get('requestContext', {}).get('authorizer', {})

    if auth_context:
        # Authorizer가 있는 경우 (새 방식)
        user_id = auth_context.get('userId')
        tenant_id = auth_context.get('tenantId')
        role = auth_context.get('role')
    else:
        # Authorizer가 없는 경우 (기존 방식 - 하위 호환성)
        query_params = event.get('queryStringParameters', {})
        user_id = query_params.get('userId')
        tenant_id = 'sedaily'  # 기본값
```

## 📋 다음 작업

### Phase 1: Lambda 함수 업데이트 (하위 호환성 유지)
1. conversation.py 업데이트
2. prompt.py 업데이트
3. usage.py 업데이트

### Phase 2: 점진적 전환
1. 개발 환경에서 테스트
2. 일부 사용자로 파일럿
3. 전체 적용

### Phase 3: 기존 방식 제거
1. Query Parameter 방식 제거
2. 완전한 멀티테넌트 전환

## 🔄 롤백 계획

필요시 즉시 롤백 가능:
1. API Gateway에서 Authorizer 제거
2. 기존 Query Parameter 방식으로 복귀

## 📊 인프라 상태

```
멀티테넌트 인프라
├── DynamoDB ✅
│   ├── sedaily-column-tenants (1개 테넌트)
│   └── sedaily-column-user-tenants (30명 사용자)
├── Lambda Authorizer ✅
│   └── sedaily-column-authorizer (Active)
├── API Gateway ✅
│   └── Authorizer 설정 완료
└── Lambda Functions ⚠️
    └── 업데이트 필요 (Authorizer Context 활용)
```

## 💡 권장사항

1. **단계적 접근**
   - 먼저 하나의 Lambda 함수만 업데이트
   - 테스트 후 나머지 함수 업데이트

2. **하위 호환성 유지**
   - 당분간 두 방식 모두 지원
   - 안정화 후 기존 방식 제거

3. **모니터링 강화**
   - CloudWatch 로그 확인
   - 에러율 모니터링

## 🎯 최종 목표

- 완전한 멀티테넌트 구조
- 여러 신문사 지원 가능
- 플랜별 기능 제한
- 사용량 기반 과금