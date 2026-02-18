# AWS Bedrock Agents 구현 파이프라인

## Phase 1: 준비 단계 (1-2일)

### 1.1 AWS 리소스 생성
```bash
# IAM Role 생성
aws iam create-role \
  --role-name BedrockAgentExecutionRole \
  --assume-role-policy# Bedrock Agent 파이프라인 구현 완료 ✅

## 현재 상태: 프로덕션 배포 완료

**배포일**: 2025년 1월
**상태**: ✅ 운영 중
**API 엔드포인트**: `https://ieec2gpr0c.execute-api.us-east-1.amazonaws.com/prod/invoke-agent`

---

## 아키텍처 개요

```
프론트엔드 (React)
    ↓
    ↓ POST /invoke-agent
    ↓
API Gateway (ieec2gpr0c)
    ↓
    ↓ Lambda 호출
    ↓
API Gateway Lambda
    ↓
    ↓ invoke_agent()
    ↓
Bedrock Agent (JGEFIJJERA)
    ↓
    ↓ 메시지 분석
    ↓
서비스 코드 추출 (b1, t1, p1, w1, f1, r1)
    ↓
    ↓ Lambda 직접 호출
    ↓
각 서비스 Lambda
    ↓
    ↓ WebSocket 또는 REST
    ↓
실제 서비스 처리
```

---

## 배포된 리소스

### 1. Bedrock Agent
- **Agent ID**: `JGEFIJJERA`
- **Alias ID**: `0U7GBBKCVR`
- **모델**: `us.anthropic.claude-opus-4-5-20251101-v1:0` (Claude Opus 4.5)
- **역할**: 사용자 메시지를 분석하여 적절한 서비스 결정

### 2. API Gateway
- **API ID**: `ieec2gpr0c`
- **Stage**: `prod`
- **엔드포인트**: `https://ieec2gpr0c.execute-api.us-east-1.amazonaws.com/prod`
- **리소스**: `/invoke-agent`
- **메서드**: `POST`, `OPTIONS` (CORS 지원)

### 3. Lambda 함수
- **함수 위치**: `backend/agents/api-gateway/lambda_function.py`
- **역할**:
  1. Bedrock Agent 호출
  2. Agent 응답에서 서비스 코드 추출
  3. 해당 서비스 Lambda 직접 호출
  4. 결과 반환

### 4. 서비스 Lambda 매핑
```python
SERVICE_LAMBDAS = {
    'b1': 'buddy-handler',           # 일보버디, 기사버디
    't1': 'title-handler',           # 제목생성
    'p1': 'proofreading-handler',    # 교열
    'w1': 'bodo-handler',            # 보도자료
    'f1': 'foreign-handler',         # 외신
    'r1': 'regression-handler'       # 퇴고
}
```

---

## 프론트엔드 통합

### ChatInput.jsx 구현

**AI Agent 모드 활성화**:
```javascript
// AI 버튼 클릭 시
const handleAgentButton = (agentType) => {
  if (selectedAgentType === agentType) {
    setSelectedAgentType(null);  // 모드 해제
  } else {
    setSelectedAgentType(agentType);  // 모드 활성화
  }
};
```

**메시지 전송 시 Agent 호출**:
```javascript
if (selectedAgentType && messageText) {
  // 1. 사용자 메시지 표시
  onSendMessage(messageText, null);
  
  // 2. Bedrock Agent 호출
  const response = await fetch(
    'https://ieec2gpr0c.execute-api.us-east-1.amazonaws.com/prod/invoke-agent',
    {
      method: 'POST',
      mode: 'cors',
      headers: { 
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({ 
        message: messageText, 
        sessionId: `session-${Date.now()}` 
      })
    }
  );
  
  // 3. Agent 응답을 채팅창에 표시
  const result = await response.json();
  onTitlesGenerated([{
    role: 'assistant',
    content: '🤖 ' + result.response,
    timestamp: new Date().toISOString()
  }]);
}
```

---

## CORS 설정

### 문제
- 브라우저에서 API Gateway 호출 시 CORS 에러 발생
- `Failed to fetch` 에러

### 해결
**스크립트**: `backend/agents/fix-cors-now.py`

```bash
cd backend/agents
python fix-cors-now.py
```

**적용된 설정**:
- OPTIONS 메서드 추가 (preflight 요청 처리)
- CORS 헤더 설정:
  - `Access-Control-Allow-Origin: *`
  - `Access-Control-Allow-Headers: Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token`
  - `Access-Control-Allow-Methods: POST,OPTIONS`

---

## 사용 흐름

### 1. 사용자 관점
1. **AI 버튼 클릭** → "AI 모드 선택됨" 토스트 표시
2. **메시지 입력** → 예: "이 기사 제목 만들어줘"
3. **전송 버튼 클릭** → 로딩 표시
4. **결과 수신** → 채팅창에 🤖 아이콘과 함께 응답 표시
5. **자동 모드 해제** → 다음 메시지는 일반 모드

### 2. 시스템 관점
1. **프론트엔드** → API Gateway 호출
2. **API Gateway** → Lambda 함수 실행
3. **Lambda** → Bedrock Agent 호출
4. **Agent** → 메시지 분석 ("제목" 키워드 감지)
5. **Agent** → 서비스 코드 결정 (t1)
6. **Lambda** → title-handler Lambda 호출
7. **title-handler** → 실제 제목 생성 서비스 실행
8. **응답 반환** → 프론트엔드까지 전달

---

## 배포 스크립트

### API Gateway Lambda 배포
```bash
cd backend/agents/api-gateway
zip -r lambda.zip lambda_function.py
aws lambda update-function-code \
  --function-name api-gateway-handler \
  --zip-file fileb://lambda.zip
```

### CORS 재설정 (필요시)
```bash
cd backend/agents
python fix-cors-now.py
```

---

## 모니터링

### CloudWatch Logs
```bash
# API Gateway Lambda 로그
aws logs tail /aws/lambda/api-gateway-handler --follow

# Bedrock Agent 로그
aws logs tail /aws/bedrock/agent/JGEFIJJERA --follow
```

### 주요 로그 포인트
- `🌐 API 호출 시작` - 프론트엔드 요청 시작
- `🤖 Bedrock Agent 응답` - Agent 분석 결과
- `Calling service: {code}` - 선택된 서비스
- `✅ Agent 응답을 채팅창에 표시` - 성공적인 응답

---

## 비용 분석

### Bedrock Agent 비용 (us-east-1)
- **Claude Opus 4.5**:
  - Input: $15.00 / MTok
  - Output: $75.00 / MTok
  - 참고: Sonnet 3.5보다 5배 비용, 하지만 최고 성능

### 예상 사용량 (1000 요청/일 기준)
- 평균 입력: 200 tokens
- 평균 출력: 100 tokens
- **일일 비용**: ~$30-40
- **월간 비용**: ~$900-1,200

### 비용 최적화 방안
1. **모델 다운그레이드**: Sonnet 3.5로 변경 시 80% 비용 절감
2. **캐싱**: 동일한 요청 결과 캐싱
3. **배치 처리**: 여러 요청 묶어서 처리
4. **Rule-based 병행**: 간단한 케이스는 Rule-based 사용

---

## 트러블슈팅

### CORS 에러
**증상**: `Failed to fetch`, `CORS policy` 에러
**해결**: 
```bash
cd backend/agents
python fix-cors-now.py
```

### Agent 응답 없음
**증상**: 로딩만 계속되고 응답 없음
**확인사항**:
1. Agent ID, Alias ID 확인
2. Lambda 권한 확인 (Bedrock 호출 권한)
3. CloudWatch 로그 확인

### 서비스 호출 실패
**증상**: Agent는 응답하지만 실제 서비스 결과 없음
**확인사항**:
1. 서비스 Lambda 이름 확인 (`SERVICE_LAMBDAS` 매핑)
2. Lambda 간 호출 권한 확인
3. 서비스 Lambda 로그 확인

---

## 향후 개선 사항

### 1. 멀티 에이전트 협업
현재는 단일 Agent가 모든 분석을 수행하지만, 향후:
- **Language Agent**: 언어 감지 전담
- **Category Agent**: 카테고리 분류 전담
- **Length Agent**: 길이 분석 전담
- **Supervisor Agent**: 전체 조율

### 2. 스트리밍 응답
현재는 전체 응답을 기다리지만, 향후:
- 실시간 스트리밍으로 응답 표시
- 사용자 경험 개선

### 3. 컨텍스트 유지
현재는 매 요청마다 새 세션이지만, 향후:
- 세션 ID 유지로 대화 컨텍스트 보존
- 연속된 요청 처리 개선

### 4. A/B 테스트
- Rule-based vs AI Agent 성능 비교
- 정확도, 속도, 비용 분석

---

## 참고 문서

- [AWS Bedrock Agent 공식 문서](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [API Gateway CORS 설정](https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-cors.html)
- [Lambda 함수 간 호출](https://docs.aws.amazon.com/lambda/latest/dg/lambda-invocation.html)

---

## 체크리스트

### 배포 완료 ✅
- [x] Bedrock Agent 생성 (JGEFIJJERA)
- [x] Agent Alias 생성 (0U7GBBKCVR)
- [x] API Gateway 설정 (ieec2gpr0c)
- [x] Lambda 함수 배포
- [x] CORS 설정
- [x] 프론트엔드 통합
- [x] 서비스 Lambda 매핑

### 테스트 완료 ✅
- [x] API Gateway 호출 테스트
- [x] CORS preflight 테스트
- [x] Agent 응답 테스트
- [x] 서비스 호출 테스트
- [x] 프론트엔드 통합 테스트

### 모니터링 설정 🔄
- [ ] CloudWatch 대시보드
- [ ] 비용 알림 설정
- [ ] 에러 알림 설정
- [ ] 성능 메트릭 수집

---

## 연락처

**문제 발생 시**:
1. CloudWatch 로그 확인
2. `backend/agents/fix-cors-now.py` 실행
3. 개발팀 문의

**배포 완료**: 2025년 1월 ✅
