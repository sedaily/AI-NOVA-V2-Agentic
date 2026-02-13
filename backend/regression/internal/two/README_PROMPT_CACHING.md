# 프롬프트 캐싱 구현 인덱스

> **빠른 참조**: 이 문서는 AI가 프롬프트 캐싱 구현 내용을 빠르게 검색하고 이해할 수 있도록 작성된 인덱스입니다.

---

## 📋 목차

1. [구현 개요](#구현-개요)
2. [핵심 키워드](#핵심-키워드)
3. [수정된 파일 위치](#수정된-파일-위치)
4. [주요 변경 사항](#주요-변경-사항)
5. [검증 결과](#검증-결과)
6. [문제 해결 가이드](#문제-해결-가이드)
7. [관련 문서](#관련-문서)

---

## 구현 개요

**프로젝트**: sedaily_column (서울경제신문 칼럼 AI 서비스)
**목적**: AWS Bedrock Prompt Caching을 통한 토큰 비용 90% 절감
**구현 일자**: 2025-11-15
**검증 상태**: ✅ 프로덕션 배포 및 검증 완료

### 핵심 성과
- ✅ **24,028 토큰** 캐싱 성공 (실측)
- ✅ **90% 비용 절감** (AWS 공식 정책)
- ✅ **5분 TTL** 동안 캐시 히트 지속
- ✅ **Application-level 캐싱** + **Bedrock 캐싱** 이중 최적화

---

## 핵심 키워드

### 검색 키워드 (AI용)
```
프롬프트 캐싱, Prompt Caching, AWS Bedrock, Claude Opus 4.1
cache_control, ephemeral, cache_read_input_tokens, cache_creation_input_tokens
토큰 비용 절감, Token Cost Optimization, 성능 최적화
Lambda, DynamoDB, CloudWatch Logs, WebSocket
서울경제신문, sedaily_column, 칼럼 AI 서비스
Logger 설정, setup_logger, 동적 프롬프트, 정적 프롬프트
```

### 기술 스택
```
- AWS Bedrock Runtime (Claude Opus 4.1)
- Python 3.9
- Lambda (sedaily-column-websocket-message)
- DynamoDB (prompts, files 테이블)
- CloudWatch Logs
```

---

## 수정된 파일 위치

### 1. 주요 수정 파일 (Bedrock 클라이언트)
```
/backend/lib/bedrock_client_enhanced.py
```

**수정 내용**:
- Line 15-17: Logger 설정 변경 (`logging.getLogger` → `setup_logger`)
- Line 317-343: `_replace_template_variables()` - 동적 값 제거
- Line 382-404: `_build_cached_system_blocks()` - 캐시 블록 생성
- Line 408-491: `stream_claude_response_enhanced()` - 캐싱 지원 추가
- Line 466-476: 캐시 메트릭 로깅
- Line 506-570: `stream_bedrock()` - 메인 스트리밍 메서드
- Line 572-595: `_create_system_prompt_with_context()` - 정적 프롬프트 생성
- Line 597-638: `_create_user_message_with_context()` - 동적 값 처리

### 2. Application-level 캐싱 (기존 활용)
```
/backend/services/websocket_service.py
```

**관련 코드**:
- Line 24-25: `PROMPT_CACHE` 글로벌 변수
- Line 109-140: `_load_prompt_from_dynamodb()` - 인메모리 캐싱
- Line 142-210: `_fetch_prompt_from_db()` - DB 조회

### 3. 배포 스크립트
```
/backend/deploy-prompt-caching.sh
```

### 4. 문서
```
/PROMPT_CACHING_IMPLEMENTATION.md  (상세 구현 보고서)
/README_PROMPT_CACHING.md  (본 인덱스 문서)
```

---

## 주요 변경 사항

### 변경 1: Logger 설정 수정 (Critical Fix)

**위치**: `backend/lib/bedrock_client_enhanced.py:15-17`

**Before**:
```python
import logging
logger = logging.getLogger(__name__)
```

**After**:
```python
from utils.logger import setup_logger
logger = setup_logger(__name__)
```

**이유**: CloudWatch Logs 출력을 위해 프로젝트 표준 logger 사용 필수

---

### 변경 2: 캐시 블록 생성

**위치**: `backend/lib/bedrock_client_enhanced.py:382-404`

**핵심 코드**:
```python
def _build_cached_system_blocks(system_prompt: str, prompt_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    blocks = []
    blocks.append({
        "type": "text",
        "text": system_prompt,
        "cache_control": {"type": "ephemeral"}  # 5분간 캐싱
    })
    logger.info(f"✅ Built cached system blocks: {len(system_prompt)} chars")
    return blocks
```

**효과**: Bedrock API에서 시스템 프롬프트를 5분간 캐싱

---

### 변경 3: 동적 값 분리

**위치**: `backend/lib/bedrock_client_enhanced.py:317-343, 597-638`

**전략**:
- **시스템 프롬프트** (정적): 캐시 가능, 절대 변하지 않음
- **User Message** (동적): 시간, 세션ID, 대화 컨텍스트 포함

**Before** (❌ 캐시 미스):
```python
system_prompt = f"{current_time}\n{session_id}\n{conversation_context}\n{base_prompt}"
```

**After** (✅ 캐시 히트):
```python
# 시스템 프롬프트: 정적만
system_prompt = base_prompt

# User Message: 동적 값 포함
user_message = f"[현재 시간: {current_time}]\n[세션: {session_id}]\n{conversation_context}\n{user_question}"
```

---

### 변경 4: 캐시 메트릭 로깅

**위치**: `backend/lib/bedrock_client_enhanced.py:466-476`

**코드**:
```python
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

**로그 예시**:
```
첫 요청: 📊 Cache metrics - read: 0, write: 24028, input: 1009
재요청:  📊 Cache metrics - read: 24028, write: 0, input: 1589
```

---

## 검증 결과

### Bedrock 프롬프트 캐싱 (실측: 2025-11-15 00:43 UTC)

| 요청 | read | write | input | 상태 |
|------|------|-------|-------|------|
| 1차 | 0 | 24,028 | 1,009 | ✅ 캐시 생성 |
| 2차 | 24,028 | 0 | 1,589 | ✅ 캐시 히트 |
| 3차 | 24,028 | 0 | 666 | ✅ 캐시 지속 |

### Application-level 캐싱 (실측)

| 요청 | 상태 | DB 조회 | 캐시 연령 |
|------|------|---------|-----------|
| 1차 | Cache MISS | 45ms | - |
| 2차 | Cache HIT | 생략 | 46.3s |
| 3차 | Cache HIT | 생략 | 99.4s |

### 비용 절감 효과 (24,028 토큰 기준)

| 요청 횟수 | 일반 비용 | 캐시 비용 | 절감액 |
|-----------|-----------|-----------|--------|
| 100회 | $36.04 | $3.60 | $32.44 |
| 1,000회 | $360.42 | $36.04 | $324.38 |
| 10,000회 | $3,604.20 | $360.42 | $3,243.78 |

---

## 문제 해결 가이드

### 문제 1: 캐시 메트릭 로그가 안 보임

**증상**:
```bash
aws logs tail /aws/lambda/sedaily-column-websocket-message \
  --since 5m --region us-east-1 | grep "📊"
# 결과 없음
```

**원인**: Logger 설정 문제

**해결**:
```python
# ❌ 잘못된 방법
logger = logging.getLogger(__name__)

# ✅ 올바른 방법
from utils.logger import setup_logger
logger = setup_logger(__name__)
```

**확인 명령**:
```bash
aws logs tail /aws/lambda/sedaily-column-websocket-message \
  --since 5m --region us-east-1 | grep "lib.bedrock_client_enhanced"
```

---

### 문제 2: 캐시가 생성되지만 히트 안 됨

**증상**:
```
첫 요청: 📊 Cache metrics - read: 0, write: 24028
재요청:  📊 Cache metrics - read: 0, write: 24028  ⚠️ read가 0!
```

**원인**: 시스템 프롬프트에 동적 값 포함

**확인 항목**:
1. `_replace_template_variables()`에서 `current_datetime`, `session_id` 제거 확인
2. `_create_user_message_with_context()`에 동적 값 이동 확인
3. 시스템 프롬프트가 매 요청마다 동일한지 확인

**검증 스크립트**:
```python
prompt1 = create_enhanced_system_prompt(prompt_data, "C1")
time.sleep(2)
prompt2 = create_enhanced_system_prompt(prompt_data, "C1")
assert prompt1 == prompt2, "시스템 프롬프트가 변경됨!"
```

---

### 문제 3: Application 캐시 미작동

**증상**: 매번 `Cache MISS` 출력

**원인**: Lambda 컨테이너 cold start

**해결**: 정상 동작입니다. 연속 요청 시 `Cache HIT` 확인

---

## 관련 문서

### 상세 구현 문서
```
/PROMPT_CACHING_IMPLEMENTATION.md
```
- 전체 구현 내역
- 코드 변경 사항
- 성능 벤치마크
- 비용 계산
- 트러블슈팅

### AWS 공식 문서
- [AWS Bedrock Prompt Caching](https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html)
- [Anthropic Claude Prompt Caching Guide](https://docs.anthropic.com/claude/docs/prompt-caching)
- [AWS Bedrock 요금](https://aws.amazon.com/bedrock/pricing/)

### 배포 스크립트
```bash
/backend/deploy-prompt-caching.sh
```

---

## 빠른 명령어 참조

### 배포
```bash
cd /Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/칼럼/sedaily_\ column/backend
./deploy-prompt-caching.sh
```

### 로그 확인 (캐시 메트릭)
```bash
aws logs tail /aws/lambda/sedaily-column-websocket-message \
  --since 5m --region us-east-1 | grep "📊 Cache metrics"
```

### 로그 확인 (Bedrock 클라이언트)
```bash
aws logs tail /aws/lambda/sedaily-column-websocket-message \
  --since 5m --region us-east-1 | grep "lib.bedrock_client_enhanced"
```

### 로그 확인 (Application 캐시)
```bash
aws logs tail /aws/lambda/sedaily-column-websocket-message \
  --since 5m --region us-east-1 | grep -E "(Cache HIT|Cache MISS)"
```

---

## 핵심 개념 요약

### 캐시 히트 조건
1. ✅ 시스템 프롬프트가 문자 단위로 완전히 동일
2. ✅ 5분 이내 재요청 (TTL)
3. ✅ 동일 모델 ID (Claude Opus 4.1)
4. ✅ Lambda 컨테이너 재사용

### 캐시 미스 원인
1. ❌ 시스템 프롬프트에 동적 값 (시간, UUID)
2. ❌ 대화 컨텍스트를 시스템 프롬프트에 포함
3. ❌ 5분 TTL 초과
4. ❌ Lambda cold start

### 최적화 전략
1. ✅ 시스템 프롬프트: 정적만
2. ✅ User Message: 동적 값
3. ✅ Application 캐시: DynamoDB 조회 최적화
4. ✅ Logger: `setup_logger()` 사용

---

**문서 버전**: 1.0
**최종 업데이트**: 2025-11-15
**Lambda 함수**: sedaily-column-websocket-message (us-east-1)
**검증 상태**: ✅ 프로덕션 배포 완료
