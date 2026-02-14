# Prompt Caching 구현 완료 보고서

**프로젝트**: Nexus AI Title Generation Service
**구현일**: 2025-11-14
**버전**: 1.0
**구현자**: Claude Code

---

## 📋 목차

1. [구현 개요](#구현-개요)
2. [구현 내용](#구현-내용)
3. [주요 변경사항](#주요-변경사항)
4. [테스트 방법](#테스트-방법)
5. [배포 가이드](#배포-가이드)
6. [성능 예상 효과](#성능-예상-효과)
7. [모니터링 가이드](#모니터링-가이드)
8. [트러블슈팅](#트러블슈팅)

---

## 구현 개요

### 적용된 캐싱 레벨

1. **Bedrock Prompt Caching** (AWS 레벨)
   - Claude 모델의 ephemeral cache 활용
   - 시스템 프롬프트 5분간 캐싱
   - 토큰 비용 90% 절감

2. **Application-level Caching** (애플리케이션 레벨)
   - Lambda 컨테이너 재사용 시 메모리 캐싱
   - DynamoDB 조회 100% 제거 (캐시 히트 시)
   - TTL: 300초 (5분)

### 예상 성능 개선

- ✅ TTFT (Time To First Token): **최대 85% 단축**
- ✅ 토큰 비용: **90% 절감** (캐시 히트 시)
- ✅ DynamoDB 조회: **100% 제거** (캐시 히트 시)
- ✅ 응답 시간: **20-40% 개선**

---

## 구현 내용

### Phase 1: Bedrock 클라이언트 수정

#### 파일: `backend/lib/bedrock_client_enhanced.py`

**1.1 로거 설정 변경**
```python
# Before
logger = logging.getLogger(__name__)

# After
from utils.logger import setup_logger
logger = setup_logger(__name__)
```

**1.2 캐시 블록 생성 함수 추가**
```python
def _build_cached_system_blocks(system_prompt: str, prompt_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """프롬프트 캐싱을 위한 system 블록 구성"""
    blocks = []
    blocks.append({
        "type": "text",
        "text": system_prompt,
        "cache_control": {"type": "ephemeral"}  # 5분간 캐싱
    })
    return blocks
```

**1.3 스트리밍 함수 캐싱 지원 추가**
```python
def stream_claude_response_enhanced(
    user_message: str,
    system_prompt: str,
    prompt_data: Optional[Dict[str, Any]] = None,
    enable_caching: bool = True  # ✅ 추가
) -> Iterator[str]:
    # 캐싱 활성화 시
    if enable_caching and prompt_data:
        system_blocks = _build_cached_system_blocks(system_prompt, prompt_data)
        body = {
            "system": system_blocks,  # ✅ 배열 형태
            ...
        }
    else:
        body = {
            "system": system_prompt,  # 문자열 형태
            ...
        }
```

**1.4 캐시 메트릭 로깅**
```python
# 스트리밍 응답 처리 중
if chunk_obj.get('type') == 'message_start':
    usage = chunk_obj.get('message', {}).get('usage', {})
    if usage:
        logger.info(f"📊 Cache metrics - "
                  f"read: {usage.get('cache_read_input_tokens', 0)}, "
                  f"write: {usage.get('cache_creation_input_tokens', 0)}, "
                  f"input: {usage.get('input_tokens', 0)}")
```

**1.5 대화 컨텍스트 분리 (중요!)**
```python
# ✅ 정적 시스템 프롬프트 생성 (캐싱 가능)
system_prompt = self._create_system_prompt_with_context(
    prompt_data,
    engine_type,
    ""  # 대화 컨텍스트 포함 안 함
)

# ✅ 대화 컨텍스트를 user_message에 포함
enhanced_user_message = self._create_user_message_with_context(
    user_message,
    conversation_context
)
```

### Phase 2: 애플리케이션 레벨 캐싱

#### 파일: `backend/services/websocket_service.py`

**2.1 글로벌 캐시 선언**
```python
# 파일 상단
from utils.logger import setup_logger

logger = setup_logger(__name__)

# 글로벌 캐시 - Lambda 컨테이너 재사용 시 유지됨
PROMPT_CACHE: Dict[str, Tuple[Dict[str, Any], float]] = {}
CACHE_TTL = 300  # 5분 (초 단위)
```

**2.2 캐싱 로직 구현**
```python
def _load_prompt_from_dynamodb(self, engine_type: str) -> Dict[str, Any]:
    """DynamoDB에서 프롬프트와 파일 로드 (인메모리 캐싱 적용)"""
    global PROMPT_CACHE
    now = time.time()

    # 캐시 확인
    if engine_type in PROMPT_CACHE:
        cached_data, cached_time = PROMPT_CACHE[engine_type]
        age = now - cached_time

        if age < CACHE_TTL:
            logger.info(f"✅ Cache HIT for {engine_type} (age: {age:.1f}s)")
            return cached_data
        else:
            logger.info(f"⏰ Cache EXPIRED for {engine_type} (age: {age:.1f}s)")
    else:
        logger.info(f"❌ Cache MISS for {engine_type} - 최초 조회")

    # 캐시 미스 - DB 조회
    prompt_data = self._fetch_prompt_from_db(engine_type)

    # 캐시 업데이트
    PROMPT_CACHE[engine_type] = (prompt_data, now)
    logger.info(f"💾 Cached prompt for {engine_type}")

    return prompt_data
```

**2.3 DB 조회 분리**
```python
def _fetch_prompt_from_db(self, engine_type: str) -> Dict[str, Any]:
    """실제 DB 조회 로직 (캐시 미스 시에만 호출)"""
    start_time = time.time()

    # 기존 DB 조회 로직
    response = self.prompts_table.get_item(Key={'id': engine_type})
    # ... 파일 로드 등

    elapsed = (time.time() - start_time) * 1000
    logger.info(f"🔍 DB fetch for {engine_type}: {elapsed:.0f}ms")

    return prompt_data
```

### Phase 3: 테스트 스크립트

#### 파일: `backend/test_prompt_caching.py`

로컬 테스트 스크립트 생성 완료:
- 캐시 히트/미스 검증
- 성능 측정
- 월간 요청 시뮬레이션

---

## 주요 변경사항

### 수정된 파일 목록

1. ✅ `backend/lib/bedrock_client_enhanced.py`
   - 로거 변경: `logging.getLogger()` → `setup_logger()`
   - `_build_cached_system_blocks()` 함수 추가
   - `stream_claude_response_enhanced()` 캐싱 지원
   - 캐시 메트릭 로깅 추가
   - `_create_user_message_with_context()` 함수 추가
   - 대화 컨텍스트 분리 로직 구현

2. ✅ `backend/services/websocket_service.py`
   - 로거 변경
   - 글로벌 `PROMPT_CACHE` 추가
   - `_load_prompt_from_dynamodb()` 캐싱 로직 적용
   - `_fetch_prompt_from_db()` DB 조회 분리

3. ✅ `backend/test_prompt_caching.py` (신규)
   - 로컬 테스트 스크립트

4. ✅ `PROMPT_CACHING_IMPLEMENTATION.md` (신규)
   - 구현 문서

### 변경되지 않은 부분

- DynamoDB 테이블 구조: 변경 없음
- API Gateway 설정: 변경 없음
- 프론트엔드 코드: 변경 없음
- 기존 기능: 모두 유지됨

---

## 테스트 방법

### 1. 로컬 테스트

```bash
cd backend
python test_prompt_caching.py
```

**예상 출력**:
```
[테스트 1] 첫 번째 조회 (캐시 미스 예상) - C1
✅ 완료: 1234ms
   - Files: 5개

[테스트 2] 두 번째 조회 (캐시 히트 예상) - C1
✅ 완료: 0ms
   - 성능 개선: 거의 즉시 반환 (캐시 히트)
```

### 2. Lambda 배포

```bash
# 기존 배포 스크립트 사용
cd backend/scripts
./99-deploy-lambda.sh

# 또는
./deploy.sh
```

### 3. CloudWatch 로그 확인

```bash
# 실시간 로그 모니터링
aws logs tail /aws/lambda/nexus-websocket-message \
  --follow \
  --since 1m \
  --region us-east-1 \
  --format short
```

**성공적인 로그 예시**:
```
2025-11-14T10:24:36 ❌ Cache MISS for C1 - 최초 조회
2025-11-14T10:24:36 🔍 DB fetch for C1: 5 files in 234ms
2025-11-14T10:24:36 💾 Cached prompt for C1
2025-11-14T10:24:36 ✅ Prompt caching enabled - system prompt: 15234 chars
2025-11-14T10:24:38 📊 Cache metrics - read: 0, write: 15234, input: 2148

# 2번째 요청
2025-11-14T10:25:12 ✅ Cache HIT for C1 (age: 36.2s) - DB 조회 생략
2025-11-14T10:25:12 ✅ Prompt caching enabled
2025-11-14T10:25:14 📊 Cache metrics - read: 15234, write: 0, input: 1842  ✅ 성공!
```

---

## 배포 가이드

### 1. 사전 확인

```bash
# 현재 브랜치 확인
git branch

# 변경사항 확인
git status

# 변경된 파일 확인
git diff backend/lib/bedrock_client_enhanced.py
git diff backend/services/websocket_service.py
```

### 2. 커밋 및 배포

```bash
# 변경사항 커밋
git add backend/lib/bedrock_client_enhanced.py
git add backend/services/websocket_service.py
git add backend/test_prompt_caching.py
git add PROMPT_CACHING_IMPLEMENTATION.md

git commit -m "feat: Implement Prompt Caching for Bedrock and application-level

- Add Bedrock prompt caching with ephemeral cache control
- Implement application-level in-memory caching (TTL: 5min)
- Separate conversation context from system prompt for cache hits
- Add cache metrics logging
- Expected: 85% TTFT reduction, 90% token cost savings"

# 배포
cd backend
./scripts/99-deploy-lambda.sh
```

### 3. 배포 후 검증

```bash
# 1. CloudWatch 로그 확인
aws logs tail /aws/lambda/nexus-websocket-message \
  --since 5m --region us-east-1 | grep -E "Cache|📊"

# 2. 캐시 메트릭 확인
aws logs filter-pattern "Cache metrics" \
  --log-group-name /aws/lambda/nexus-websocket-message \
  --start-time $(date -u -d '10 minutes ago' +%s)000

# 3. 함수 버전 확인
aws lambda get-function --function-name nexus-websocket-message \
  --query 'Configuration.LastModified'
```

---

## 성능 예상 효과

### 1. 애플리케이션 캐싱 효과

| 항목 | Before | After (캐시 히트) | 개선율 |
|------|--------|------------------|--------|
| DynamoDB 조회 | 매번 | 0회 | 100% |
| 프롬프트 로드 시간 | 200-500ms | <1ms | 99.8% |
| Lambda 실행 시간 | 포함 | 제거 | 개선 |

### 2. Bedrock 캐싱 효과

| 항목 | Before | After (캐시 히트) | 개선율 |
|------|--------|------------------|--------|
| TTFT | 3,500ms | 500ms | 85% ↓ |
| 입력 토큰 비용 | $0.015/1K | $0.0015/1K | 90% ↓ |
| 토큰 처리 시간 | 포함 | 캐시됨 | 개선 |

### 3. 월간 비용 절감 (예시)

**가정**: 월 10,000 요청, 평균 캐시 토큰 15,000개

```
캐싱 전:
  10,000 요청 × 15,000 토큰 × $0.015/1K = $2,250

캐싱 후:
  1회 캐시 생성: 15,000 × $0.015/1K = $0.225
  9,999회 캐시 읽기: 9,999 × 15,000 × $0.0015/1K = $224.98
  합계: $225.20

절감액: $2,024.80 (90% 절감)
```

---

## 모니터링 가이드

### 1. 주요 메트릭

#### 애플리케이션 캐싱
```bash
# 캐시 히트/미스 비율
aws logs filter-pattern "Cache HIT" \
  --log-group-name /aws/lambda/nexus-websocket-message

aws logs filter-pattern "Cache MISS" \
  --log-group-name /aws/lambda/nexus-websocket-message
```

#### Bedrock 캐싱
```bash
# 캐시 읽기 확인 (read > 0이면 성공)
aws logs filter-pattern "Cache metrics" \
  --log-group-name /aws/lambda/nexus-websocket-message \
  | grep "read:"
```

### 2. CloudWatch 대시보드

**추가 권장 메트릭**:
1. `CacheHitRate`: 캐시 히트율
2. `CacheReadTokens`: 캐시 읽기 토큰 수
3. `DBQueryTime`: DynamoDB 조회 시간
4. `TTFTImprovement`: TTFT 개선율

### 3. 알람 설정

```bash
# 캐시 히트율이 80% 미만일 때 알람
aws cloudwatch put-metric-alarm \
  --alarm-name nexus-low-cache-hit-rate \
  --metric-name CacheHitRate \
  --threshold 80 \
  --comparison-operator LessThanThreshold
```

---

## 트러블슈팅

### 문제 1: 캐시가 생성되지만 히트되지 않음

**증상**:
```
📊 Cache metrics - read: 0, write: 15234, input: 1842
📊 Cache metrics - read: 0, write: 15234, input: 2105  # 계속 write만 발생
```

**원인**: 시스템 프롬프트에 동적 요소가 포함됨

**해결**:
1. `_create_system_prompt_with_context()` 함수 확인
2. 대화 컨텍스트가 시스템 프롬프트에 포함되지 않았는지 확인
3. 템플릿 변수(`{{current_datetime}}` 등)가 매번 다르게 치환되는지 확인

### 문제 2: CloudWatch에 캐시 로그가 나타나지 않음

**증상**: 캐시 관련 로그가 CloudWatch에 없음

**원인**: Lambda 로그 레벨이 WARNING

**해결**:
```python
# utils/logger.py에서 INFO 레벨 사용 확인
logger.setLevel(logging.INFO)

# 또는 환경 변수 설정
LOG_LEVEL=INFO
```

### 문제 3: 애플리케이션 캐시가 작동하지 않음

**증상**: 매번 DB 조회 발생

**원인**: Lambda 컨테이너가 재사용되지 않음

**확인**:
```bash
# Lambda 동시 실행 수 확인
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name ConcurrentExecutions \
  --dimensions Name=FunctionName,Value=nexus-websocket-message
```

**해결**: 정상 동작. 새 컨테이너는 캐시가 비어있음 (예상된 동작)

### 문제 4: 캐시 만료가 작동하지 않음

**증상**: 5분 후에도 캐시가 재생성되지 않음

**확인**:
```python
# websocket_service.py의 TTL 체크 로직 확인
if age < CACHE_TTL:  # 이 조건 확인
    return cached_data
```

---

## 다음 단계

### 1. 성능 측정 및 최적화
- [ ] 1주일간 CloudWatch 메트릭 수집
- [ ] 실제 캐시 히트율 측정
- [ ] TTFT 개선율 측정
- [ ] 비용 절감 효과 분석

### 2. 추가 개선 사항
- [ ] 여러 엔진 타입별 캐시 히트율 분석
- [ ] TTL 최적화 (5분 → 조정)
- [ ] 캐시 워밍 (Lambda 초기화 시 미리 로드)
- [ ] CloudWatch 대시보드 구성

### 3. 문서화
- [ ] 팀 공유 및 교육
- [ ] 운영 가이드 작성
- [ ] 장애 대응 매뉴얼 작성

---

## 참고 자료

- [AWS Bedrock Prompt Caching 공식 문서](https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html)
- [Anthropic Claude Prompt Caching Guide](https://docs.anthropic.com/claude/docs/prompt-caching)
- [프로젝트 README](./README.md)
- [매뉴얼 원본](./MANUAL.md)

---

**문서 버전**: 1.0
**최종 업데이트**: 2025-11-14
**작성자**: Claude Code
**검증 상태**: ⏳ 배포 후 검증 필요

---

## 체크리스트

### 구현 완료
- [x] Bedrock 클라이언트 캐싱 구현
- [x] 애플리케이션 레벨 캐싱 구현
- [x] 캐시 메트릭 로깅 추가
- [x] 대화 컨텍스트 분리
- [x] 테스트 스크립트 작성
- [x] 문서 작성

### 배포 전 확인
- [ ] 로컬 테스트 실행
- [ ] Git 커밋
- [ ] Lambda 배포
- [ ] CloudWatch 로그 확인
- [ ] 캐시 메트릭 검증

### 배포 후 모니터링
- [ ] 1시간 후 로그 확인
- [ ] 24시간 후 성능 측정
- [ ] 1주일 후 효과 분석
- [ ] 비용 절감 효과 확인
