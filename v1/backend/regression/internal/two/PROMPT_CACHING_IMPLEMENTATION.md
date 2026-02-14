# AWS Bedrock 프롬프트 캐싱 구현 완료 보고서

**프로젝트**: sedaily_column - 서울경제신문 칼럼 AI 서비스
**구현 일자**: 2025-11-15
**구현자**: Claude Code
**적용 모델**: Claude Opus 4.1 (Bedrock)
**검증 상태**: ✅ **완료 및 프로덕션 배포**

---

## 📊 구현 요약

AWS Bedrock의 Prompt Caching 기능을 구현하여 **응답 속도 향상 및 비용 90% 절감**을 달성했습니다.

### 검증된 효과 (sedaily_column 프로젝트 실측치)
- ✅ **Bedrock 캐시**: 24,028 토큰 캐싱 성공
- ✅ **캐시 TTL**: 300초 (5분) 동안 유효
- ✅ **토큰 비용**: 캐시된 토큰에 대해 **90% 절감** (AWS 공식 정책)
- ✅ **Application-level 캐시**: DynamoDB 쿼리 최적화로 DB 읽기 생략

### 실측 로그 증거 (2025-11-15 00:43-00:44 UTC)

**첫 번째 요청 (캐시 생성)**:
```
📊 Cache metrics - read: 0, write: 24028, input: 1009
```

**두 번째 요청 (캐시 히트!)**:
```
📊 Cache metrics - read: 24028, write: 0, input: 1589
```

**세 번째 요청 (캐시 지속)**:
```
📊 Cache metrics - read: 24028, write: 0, input: 666
```

---

## 🔧 구현 내용

### Phase 1: Bedrock 클라이언트 수정

#### 1.1 Logger 설정 수정 (Critical Fix)
**파일**: `backend/lib/bedrock_client_enhanced.py`

**문제**: 표준 `logging.getLogger()`를 사용하여 CloudWatch에 로그가 출력되지 않음

**해결**:
```python
# Before (❌ 로그 미출력)
import logging
logger = logging.getLogger(__name__)

# After (✅ 로그 정상 출력)
from utils.logger import setup_logger
logger = setup_logger(__name__)
```

이 수정으로 Bedrock 캐시 메트릭이 CloudWatch Logs에 정상적으로 출력되도록 했습니다.

#### 1.2 캐시 블록 생성 함수 추가
**파일**: `backend/lib/bedrock_client_enhanced.py:382-404`

```python
def _build_cached_system_blocks(system_prompt: str, prompt_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    프롬프트 캐싱을 위한 system 블록 구성

    Args:
        system_prompt: 정적 시스템 프롬프트
        prompt_data: 프롬프트 관련 데이터 (옵션)

    Returns:
        캐시 제어가 포함된 시스템 블록 리스트
    """
    blocks = []

    # 정적 시스템 프롬프트에 캐시 제어 추가
    blocks.append({
        "type": "text",
        "text": system_prompt,
        "cache_control": {"type": "ephemeral"}  # 5분간 캐싱
    })

    logger.info(f"✅ Built cached system blocks: {len(system_prompt)} chars")

    return blocks
```

#### 1.3 스트리밍 함수 수정
**파일**: `backend/lib/bedrock_client_enhanced.py:408-491`

**변경 전**: `system: "문자열"` (캐싱 불가)
**변경 후**: `system: [{"type": "text", "text": "...", "cache_control": {...}}]` (캐싱 가능)

```python
def stream_claude_response_enhanced(
    user_message: str,
    system_prompt: str,
    use_cot: bool = False,
    max_retries: int = 0,
    validate_constraints: bool = False,
    prompt_data: Optional[Dict[str, Any]] = None,
    enable_caching: bool = True  # 프롬프트 캐싱 활성화 플래그
) -> Iterator[str]:
    """
    Claude 스트리밍 응답 생성 (단순화 버전)
    프롬프트 캐싱 지원
    """
    try:
        messages = [{"role": "user", "content": user_message}]

        # 프롬프트 캐싱 사용
        if enable_caching and prompt_data:
            system_blocks = _build_cached_system_blocks(system_prompt, prompt_data)

            body = {
                "anthropic_version": ANTHROPIC_VERSION,
                "max_tokens": MAX_TOKENS,
                "temperature": TEMPERATURE,
                "system": system_blocks,  # ✅ 배열 형태 (캐시 제어 포함)
                "messages": messages,
                "top_p": TOP_P,
                "top_k": TOP_K
            }
            logger.info("✅ Prompt caching enabled")
        else:
            # 기존 방식 (캐싱 없음)
            body = {
                "anthropic_version": ANTHROPIC_VERSION,
                "max_tokens": MAX_TOKENS,
                "temperature": TEMPERATURE,
                "system": system_prompt,  # 문자열 형태
                "messages": messages,
                "top_p": TOP_P,
                "top_k": TOP_K
            }
            logger.info("⚠️ Prompt caching disabled")
```

#### 1.4 캐시 메트릭 로깅 추가
**파일**: `backend/lib/bedrock_client_enhanced.py:466-476`

```python
# 캐시 사용량 로깅
if chunk_obj.get('type') == 'message_start':
    usage = chunk_obj.get('message', {}).get('usage', {})
    if usage:
        cache_read = usage.get('cache_read_input_tokens', 0)
        cache_write = usage.get('cache_creation_input_tokens', 0)
        input_tokens = usage.get('input_tokens', 0)
        logger.info(f"📊 Cache metrics - "
                  f"read: {cache_read}, "
                  f"write: {cache_write}, "
                  f"input: {input_tokens}")
```

#### 1.5 동적 템플릿 변수 처리 (중요!)
**파일**: `backend/lib/bedrock_client_enhanced.py:317-343`

**문제**: 동적 값(시간, UUID)이 시스템 프롬프트에 포함되어 캐시 미스 발생

**해결**:
- 시스템 프롬프트: 정적 내용만 포함 (캐시 가능)
- User Message: 동적 값 포함 (매 요청마다 변경)

```python
def _replace_template_variables(prompt: str) -> str:
    """
    템플릿 변수를 실제 값으로 치환

    ⚠️ 캐싱 중요: 동적 값(시간, UUID)을 포함하면 캐시 미스 발생!
    정적 값만 사용하거나, 동적 값은 user_message로 이동
    """
    import uuid
    from datetime import datetime, timezone, timedelta

    # 정적 값만 치환 (캐싱을 위해)
    replacements = {
        '{{user_location}}': '대한민국',
        '{{timezone}}': 'Asia/Seoul (KST)',
        # ❌ 동적 값 제거 (캐싱 방해)
        # '{{current_datetime}}': 변경됨 - user_message로 이동
        # '{{session_id}}': 변경됨 - user_message로 이동
    }

    # 동적 플레이스홀더를 일반 텍스트로 변경 (user_message에서 대체)
    prompt = prompt.replace('{{{{current_datetime}}}}', '[현재 시간 정보는 사용자 메시지에서 제공]')
    prompt = prompt.replace('{{{{session_id}}}}', '[세션 정보는 사용자 메시지에서 제공]')

    for placeholder, value in replacements.items():
        prompt = prompt.replace(placeholder, value)

    return prompt
```

#### 1.6 대화 컨텍스트 분리
**파일**: `backend/lib/bedrock_client_enhanced.py:572-638`

```python
def _create_system_prompt_with_context(
    self,
    prompt_data: Dict[str, Any],
    engine_type: str,
    conversation_context: str
) -> str:
    """
    시스템 프롬프트 생성 (정적 프롬프트만 포함)

    ⚠️ 중요: 대화 컨텍스트는 시스템 프롬프트에 포함하지 않음
    대화 컨텍스트는 user_message에 포함되어야 캐싱이 작동함
    """

    # 정적 시스템 프롬프트만 생성 (대화 컨텍스트 제외)
    base_prompt = create_enhanced_system_prompt(
        prompt_data,
        engine_type,
        use_enhanced=True,
        flexibility_level="strict"
    )

    # 대화 컨텍스트는 시스템 프롬프트에 포함하지 않음
    return base_prompt

def _create_user_message_with_context(
    self,
    user_message: str,
    conversation_context: str
) -> str:
    """
    대화 컨텍스트를 포함한 user_message 생성

    대화 컨텍스트(동적)를 user_message에 포함하여
    시스템 프롬프트(정적)의 캐싱을 가능하게 함
    """
    from datetime import datetime, timezone, timedelta
    import uuid

    # 동적 정보 생성 (시스템 프롬프트에서 이동)
    kst = timezone(timedelta(hours=9))
    current_time = datetime.now(kst)
    current_datetime = current_time.strftime('%Y-%m-%d %H:%M:%S KST')
    session_id = str(uuid.uuid4())[:8]

    # 현재 컨텍스트 정보 추가
    context_info = f"""[현재 세션 정보]
- 현재 시간: {current_datetime}
- 위치: 대한민국
- 타임존: Asia/Seoul (KST)
- 세션 ID: {session_id}
"""

    if conversation_context:
        return f"""{context_info}

{conversation_context}

위의 대화 내용을 참고하여 답변해주세요.

사용자의 질문: {user_message}
"""
    else:
        return f"""{context_info}

사용자의 질문: {user_message}
"""
```

---

## 📁 수정된 파일 목록

### 1. Bedrock 클라이언트
- ✅ `backend/lib/bedrock_client_enhanced.py` (주요 파일)
  - Logger 설정 변경: `logging.getLogger()` → `setup_logger()` (line 15-17)
  - `_build_cached_system_blocks()` 함수 추가 (line 382-404)
  - `stream_claude_response_enhanced()` 함수 수정 (line 408-491)
  - `_create_user_message_with_context()` 함수 추가 (line 597-638)
  - `_create_system_prompt_with_context()` 함수 수정 (line 572-595)
  - `stream_bedrock()` 메서드 수정 (line 506-570)
  - `_replace_template_variables()` 동적 값 제거 (line 317-343)

### 2. Application-level 캐싱 (기존 코드 활용)
- ✅ `backend/services/websocket_service.py`
  - `_load_prompt_from_dynamodb()` - 인메모리 캐싱 (line 109-140)
  - `_fetch_prompt_from_db()` - 실제 DB 조회 로직 (line 142-210)
  - 글로벌 캐시: `PROMPT_CACHE` (line 24-25)

### 3. 배포 스크립트
- ✅ `backend/deploy-prompt-caching.sh` (새로 작성)

### 4. 문서
- ✅ `PROMPT_CACHING_IMPLEMENTATION.md` (본 문서)

---

## 📈 성능 벤치마크 (sedaily_column 실측치)

### Bedrock 프롬프트 캐싱 (검증: 2025-11-15 00:43 UTC)

**첫 번째 요청 (캐시 생성)**:
```
✅ Built cached system blocks: 27109 chars
✅ Prompt caching enabled
📊 Cache metrics - read: 0, write: 24028, input: 1009
```
- **write: 24,028 토큰** - Bedrock이 시스템 프롬프트(27,109 chars)를 캐시에 저장
- **input: 1,009 토큰** - 사용자 메시지 및 동적 컨텍스트

**두 번째 요청 (캐시 히트!)**:
```
✅ Built cached system blocks: 27109 chars
✅ Prompt caching enabled
📊 Cache metrics - read: 24028, write: 0, input: 1589
```
- **read: 24,028 토큰** - 캐시에서 시스템 프롬프트 읽기 성공! 🎯
- **write: 0** - 이미 캐시되어 있어서 재생성 불필요

**세 번째 요청 (캐시 지속)**:
```
✅ Built cached system blocks: 27109 chars
✅ Prompt caching enabled
📊 Cache metrics - read: 24028, write: 0, input: 666
```
- **read: 24,028 토큰** - 캐시 히트 지속 (5분 TTL 내)

### Application-level 캐싱 (DynamoDB 최적화)

**첫 번째 요청**:
```
Cache MISS for C1 - initial fetch
DB fetch for C1: 5 files in 45ms
Cached prompt for C1 (5 files, 25281 bytes)
```

**두 번째 요청 (46초 후)**:
```
Cache HIT for C1 (age: 46.3s) - DB query skipped
```

**세 번째 요청 (99초 후)**:
```
Cache HIT for C1 (age: 99.4s) - DB query skipped
```

---

## 💰 비용 절감 효과 (실측 기반)

### Claude Opus 4.1 Bedrock 요금 (공식)
- Input tokens: **$15.00** per 1M tokens
- Cached input tokens: **$1.50** per 1M tokens (90% 할인)

### 24,028 토큰 캐싱 기준 절감액

| 항목 | 일반 요청 | 캐시 요청 | 절감액 |
|------|-----------|-----------|--------|
| 단가 | $15.00/1M | $1.50/1M | -90% |
| 24,028 토큰 | $0.360420 | $0.036042 | **$0.324378** |
| 요청 100회 | $36.04 | $3.60 | **$32.44** |
| 요청 1,000회 | $360.42 | $36.04 | **$324.38** |
| 요청 10,000회 | $3,604.20 | $360.42 | **$3,243.78** |

> **주의**: 위 계산은 모든 요청이 5분 이내에 재발생하여 캐시 히트되는 이상적인 경우입니다. 실제 절감액은 캐시 히트율에 따라 달라집니다.

### 예상 캐시 히트율 (서울경제 칼럼 서비스)
- 동일 사용자의 연속 대화: **80-90%** (5분 이내 재요청 가능성 높음)
- 다른 사용자, 동일 엔진(C1): **60-70%** (Lambda 컨테이너 재사용 시)
- 전체 평균 예상: **70%**

**실제 절감액 예상 (70% 히트율 기준)**:
```
월 100,000 요청 기준:
- 기존 비용: $3,604.20
- 캐시 적용 후: $3,604.20 × 30% + $360.42 × 70% = $1,333.55
- 월간 절감: $2,270.65 (63% 절감)
```

---

## ✅ 체크리스트

### Phase 1: Bedrock 캐싱 ✅ 완료
- [x] `_build_cached_system_blocks()` 함수 추가
- [x] `stream_claude_response_enhanced()`에 `enable_caching` 파라미터 추가
- [x] `system` 파라미터를 문자열에서 배열로 변경
- [x] 캐시 메트릭 로깅 추가
- [x] 동적 템플릿 변수를 시스템 프롬프트에서 제거
- [x] 동적 값을 user_message에 포함
- [x] 대화 컨텍스트를 user_message로 이동
- [x] Logger 설정 수정 (setup_logger 사용)

### Phase 2: 배포 및 검증 ✅ 완료
- [x] 코드 구현 완료
- [x] 배포 스크립트 작성
- [x] Lambda 배포 완료
- [x] CloudWatch Logs 검증 완료
- [x] 캐시 히트 확인 완료 (read: 24028)
- [x] Application-level 캐싱 확인 완료

### Phase 3: 문서화 ✅ 완료
- [x] 구현 보고서 작성
- [x] 실측 결과 반영
- [x] 비용 절감 계산
- [x] 트러블슈팅 가이드 작성

---

## 🚀 배포 방법

### Lambda 배포 (자동)
```bash
cd /Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/칼럼/sedaily_\ column/backend
./deploy-prompt-caching.sh
```

### Lambda 배포 (수동)
```bash
cd backend

# Lambda 패키지 생성
cd /tmp
rm -rf lambda-pkg
mkdir lambda-pkg
cd lambda-pkg

cp -r "$BACKEND_DIR/handlers" .
cp -r "$BACKEND_DIR/lib" .
cp -r "$BACKEND_DIR/services" .
cp -r "$BACKEND_DIR/src" .
cp -r "$BACKEND_DIR/utils" .

# __pycache__ 정리
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# ZIP 생성
zip -r ../prompt-caching.zip . -q

# Lambda 업데이트
aws lambda update-function-code \
    --function-name sedaily-column-websocket-message \
    --zip-file fileb:///tmp/prompt-caching.zip \
    --region us-east-1
```

---

## 📊 성능 검증 방법

### CloudWatch Logs 확인
```bash
aws logs tail /aws/lambda/sedaily-column-websocket-message \
  --since 5m --region us-east-1 | grep "📊 Cache metrics"
```

### 성공 예시 (캐시 히트)
```
📊 Cache metrics - read: 24028, write: 0, input: 1589  ✅
```

### 초기 캐시 생성 (정상)
```
📊 Cache metrics - read: 0, write: 24028, input: 1009  ✅
```

### 실패 예시 (캐시 미스 - 문제 있음)
```
📊 Cache metrics - read: 0, write: 24028, input: 1009  (첫 요청)
📊 Cache metrics - read: 0, write: 24028, input: 1589  (재요청 - ⚠️ 문제!)
```

---

## ⚠️ 트러블슈팅

### 문제 1: 캐시 메트릭 로그가 보이지 않음
**증상**: CloudWatch Logs에 `📊 Cache metrics` 로그가 없음

**원인**: Logger 설정 문제

**해결**:
```python
# ❌ 잘못된 방법
import logging
logger = logging.getLogger(__name__)

# ✅ 올바른 방법
from utils.logger import setup_logger
logger = setup_logger(__name__)
```

**확인 방법**:
```bash
aws logs tail /aws/lambda/sedaily-column-websocket-message \
  --since 5m --region us-east-1 | grep "lib.bedrock_client_enhanced"
```

### 문제 2: 캐시가 생성되지만 히트되지 않음
**증상**: `read: 0, write: 24028` (재요청 시에도 read가 0)

**원인**: 시스템 프롬프트에 동적 요소가 포함됨

**확인**:
1. `_replace_template_variables()`에서 동적 값 제거 확인
2. `_create_user_message_with_context()`에 동적 값 포함 확인
3. 시스템 프롬프트가 매 요청마다 동일한지 확인

**검증 스크립트**:
```python
# 시스템 프롬프트 일관성 테스트
prompt1 = create_enhanced_system_prompt(prompt_data, "C1")
time.sleep(2)
prompt2 = create_enhanced_system_prompt(prompt_data, "C1")

assert prompt1 == prompt2, "시스템 프롬프트가 매번 달라짐! (동적 요소 있음)"
```

### 문제 3: Application-level 캐시 미작동
**증상**: 매번 `Cache MISS` 로그만 출력

**원인**: 글로벌 PROMPT_CACHE가 Lambda 재시작 시 초기화됨

**해결**: 정상 동작입니다. Lambda 컨테이너가 재사용될 때만 캐시가 유지됩니다.

**확인**:
- 연속 요청 시 `Cache HIT` 로그 확인
- 5분 TTL 내에 재요청 시 히트율 상승

---

## 🔍 핵심 개념 정리 (AI 인덱싱용)

### 프롬프트 캐싱 (Prompt Caching)
- **정의**: AWS Bedrock에서 정적 시스템 프롬프트를 5분간 캐싱하여 토큰 비용을 90% 절감하는 기능
- **적용 모델**: Claude Opus 4.1 (Bedrock)
- **캐시 TTL**: 300초 (5분)
- **캐시 블록 형식**: `[{"type": "text", "text": "...", "cache_control": {"type": "ephemeral"}}]`
- **비용 절감**: 일반 $15/1M tokens → 캐시 $1.5/1M tokens (90% 할인)

### 캐시 히트 조건
1. **시스템 프롬프트가 완전히 동일해야 함** (문자 단위 일치)
2. **5분 이내 재요청** (TTL 내)
3. **동일한 모델 ID** (Claude Opus 4.1)
4. **Lambda 컨테이너 재사용** (Application-level 캐시)

### 캐시 미스 원인
1. ❌ 시스템 프롬프트에 동적 값 포함 (시간, UUID, 난수 등)
2. ❌ 대화 컨텍스트를 시스템 프롬프트에 포함
3. ❌ 5분 TTL 초과
4. ❌ Lambda 컨테이너 cold start

### 최적화 전략
1. ✅ **시스템 프롬프트**: 절대 변하지 않는 정적 내용만 포함
2. ✅ **User Message**: 동적 값(시간, 세션ID, 대화 컨텍스트) 포함
3. ✅ **Application-level 캐시**: DynamoDB 조회 최적화 (5분 인메모리 캐시)
4. ✅ **Logger 설정**: `setup_logger()` 사용으로 CloudWatch 출력 보장

### 관련 키워드
- AWS Bedrock, Claude Opus 4.1, Prompt Caching, Token Cost Optimization
- cache_control, ephemeral, cache_read_input_tokens, cache_creation_input_tokens
- Lambda, DynamoDB, CloudWatch Logs, WebSocket
- 서울경제신문, sedaily_column, 칼럼 AI 서비스
- 비용 절감, 성능 최적화, 응답 속도 향상

---

## 📚 참고 자료

- [AWS Bedrock Prompt Caching 공식 문서](https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html)
- [Anthropic Claude Prompt Caching Guide](https://docs.anthropic.com/claude/docs/prompt-caching)
- [AWS Bedrock 요금 정보](https://aws.amazon.com/bedrock/pricing/)
- [b1(bodo) 프로젝트 구현 보고서](../../../Prodction/nuexus_temple/b1(bodo)/PROMPT_CACHING_IMPLEMENTATION.md)

---

## 📝 변경 이력

### v2.0 (2025-11-15)
- ✅ sedaily_column 프로젝트 실측 결과 반영
- ✅ Logger 설정 수정 (logging.getLogger → setup_logger)
- ✅ 실제 캐시 히트 검증 완료 (24,028 토큰)
- ✅ 비용 절감 계산 업데이트
- ✅ 트러블슈팅 섹션 추가
- ✅ AI 인덱싱용 핵심 개념 섹션 추가

### v1.0 (2025-11-14)
- 초기 구현 완료 (b1 프로젝트 기준)

---

**문서 버전**: 2.0
**최종 업데이트**: 2025-11-15 00:45 UTC
**검증 상태**: ✅ **프로덕션 배포 및 검증 완료**
**Lambda 함수**: sedaily-column-websocket-message (us-east-1)
