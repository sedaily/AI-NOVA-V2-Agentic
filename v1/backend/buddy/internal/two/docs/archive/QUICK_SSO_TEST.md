# SSO 터미널 테스트 가이드

## 방법 1: 스크립트 사용

```bash
# 1. 브라우저에서 n1.sedaily.ai 로그인
# 2. DevTools → Application → Cookies에서 토큰 복사
# 3. test-sso.sh 편집하여 토큰 입력
# 4. 실행
./test-sso.sh
```

## 방법 2: 직접 curl 명령어

```bash
# 토큰을 변수로 설정
ID_TOKEN="eyJraWQ..."  # 브라우저에서 복사한 sso_id_token
ACCESS_TOKEN="eyJraWQ..."  # 브라우저에서 복사한 sso_access_token

# API 호출 테스트
curl -v \
  -H "Cookie: sso_id_token=$ID_TOKEN; sso_access_token=$ACCESS_TOKEN" \
  https://b1api.sedaily.ai/api/conversations
```

## 방법 3: 브라우저 개발자도구 (가장 간단)

1. **n1.sedaily.ai 로그인**
2. **DevTools (F12) → Console 탭**
3. **다음 코드 실행:**

```javascript
// 쿠키 확인
console.log('ID Token:', document.cookie.match(/sso_id_token=([^;]+)/)?.[1]);
console.log('Access Token:', document.cookie.match(/sso_access_token=([^;]+)/)?.[1]);

// b1.sedaily.ai로 이동하여 동일한 코드 실행 - 쿠키가 있으면 성공
```

4. **b1.sedaily.ai/11 접속**
5. **DevTools → Console에서 동일 코드 실행**
6. **쿠키가 표시되면 SSO 성공**

## 예상 결과

### 성공 시:
- HTTP 200 응답
- 대화 목록 반환
- 쿠키가 b1.sedaily.ai에서도 읽힘

### 실패 시:
- HTTP 401 Unauthorized
- 쿠키가 전달되지 않음
- 백엔드 로그 확인 필요

## 백엔드 로그 확인

```bash
# Lambda 로그 확인
aws logs tail /aws/lambda/p2-websocket-service --follow --region us-east-1
```
