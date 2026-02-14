"""
Anthropic API 직접 호출 클라이언트
AWS Bedrock 대신 Anthropic API를 직접 사용
Prompt Caching 최적화 적용
"""
import os
import json
import logging
import requests
import boto3
from typing import Dict, Any, Iterator, Optional
import uuid
from datetime import datetime, timezone, timedelta

# Lambda 환경에서 로깅 설정
try:
    from utils.logger import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Secrets Manager 클라이언트
secrets_client = boto3.client('secretsmanager', region_name='us-east-1')

def get_api_key_from_secrets():
    """Secrets Manager에서 API 키 가져오기"""
    try:
        secret_name = os.environ.get('ANTHROPIC_SECRET_NAME', 'regression-v1')
        response = secrets_client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response['SecretString'])
        return secret.get('api_key', '')
    except Exception as e:
        logger.error(f"Failed to retrieve API key from Secrets Manager: {str(e)}")
        # 폴백: 환경변수에서 가져오기
        return os.environ.get('ANTHROPIC_API_KEY', '')

# Anthropic API 설정
ANTHROPIC_API_KEY = None  # 요청 시점에 동적으로 가져옴
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

def _replace_template_variables(prompt: str) -> str:
    """정적 값만 치환 (캐싱 최적화)"""
    replacements = {
        '{{user_location}}': '대한민국',
        '{{timezone}}': 'Asia/Seoul (KST)'
    }
    
    result = prompt
    for key, value in replacements.items():
        result = result.replace(key, value)
    
    return result

def _create_dynamic_context() -> str:
    """동적 컨텍스트 생성 (user_message에 추가용)"""
    kst = timezone(timedelta(hours=9))
    current_time = datetime.now(kst)
    session_id = str(uuid.uuid4())[:8]
    
    return f"""[현재 세션 정보]
- 현재 시간: {current_time.strftime('%Y-%m-%d %H:%M:%S KST')}
- 오늘 날짜: {current_time.strftime('%Y년 %m월 %d일')}
- 사용자 위치: 대한민국 (Asia/Seoul)
- 세션 ID: {session_id}
- 중요: 응답 시 반드시 현재 연도 {current_time.year}년을 기준으로 작성하세요.
"""

def _calculate_cost(usage: Dict[str, Any]) -> float:
    """비용 계산 (Claude Opus 4.5 기준)"""
    input_tokens = usage.get('input_tokens', 0)
    output_tokens = usage.get('output_tokens', 0)
    cache_creation = usage.get('cache_creation_input_tokens', 0)
    cache_read = usage.get('cache_read_input_tokens', 0)
    
    cost_input = (input_tokens / 1_000_000) * PRICE_INPUT
    cost_output = (output_tokens / 1_000_000) * PRICE_OUTPUT
    cost_cache_write = (cache_creation / 1_000_000) * PRICE_CACHE_WRITE
    cost_cache_read = (cache_read / 1_000_000) * PRICE_CACHE_READ
    
    return cost_input + cost_output + cost_cache_write + cost_cache_read

def _log_usage(usage: Dict[str, Any]) -> None:
    """Usage 정보 로깅"""
    input_tokens = usage.get('input_tokens', 0)
    output_tokens = usage.get('output_tokens', 0)
    cache_creation = usage.get('cache_creation_input_tokens', 0)
    cache_read = usage.get('cache_read_input_tokens', 0)
    
    cost = _calculate_cost(usage)
    
    logger.info(f"💰 API Cost: ${cost:.6f} | "
               f"input: {input_tokens}, output: {output_tokens}, "
               f"cache_read: {cache_read}, cache_write: {cache_creation}")
    
    if cache_read > 0:
        savings = ((cache_read / 1_000_000) * (PRICE_INPUT - PRICE_CACHE_READ))
        logger.info(f"✅ Cache hit! Saved: ${savings:.6f} ({cache_read} tokens from cache)")

# 모델 설정
MODEL_ID = "opus-4-20250514"  # Claude Opus 4.6 - 최고 성능 모델
MAX_TOKENS = 4096
TEMPERATURE = 0.7

# 비용 계산용 가격 (Claude Opus 4.5 기준)
PRICE_INPUT = 5.0  # Base Input Tokens (per 1M tokens)
PRICE_OUTPUT = 25.0  # Output Tokens (per 1M tokens)
PRICE_CACHE_WRITE = 10.0  # 1h Cache Writes (per 1M tokens)
PRICE_CACHE_READ = 0.50  # Cache Hits (per 1M tokens)


def stream_anthropic_response(
    user_message: str,
    system_prompt: str,
    api_key: Optional[str] = None,
    enable_web_search: bool = False,
    enable_caching: bool = True,
    model_id: str = 'opus-4-20250514'
) -> Iterator[str]:
    """
    Anthropic API를 통한 스트리밍 응답 생성
    
    Args:
        user_message: 사용자 메시지
        system_prompt: 시스템 프롬프트
        api_key: API 키 (없으면 환경변수 사용)
        enable_web_search: 웹 검색 기능 활성화
    
    Yields:
        응답 텍스트 청크
    """
    try:
        # API 키 확인 (Secrets Manager에서 가져오기)
        api_key = api_key or get_api_key_from_secrets()
        if not api_key:
            logger.error("Anthropic API key not found")
            yield "[오류] API 키가 설정되지 않았습니다."
            return
        
        # 정적 컨텍스트는 system_prompt에, 동적 컨텍스트는 user_message에
        static_system_prompt = _replace_template_variables(system_prompt)
        dynamic_context = _create_dynamic_context()
        enhanced_user_message = f"{dynamic_context}\n\n{user_message}"
        
        # 요청 헤더
        headers = {
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
            "accept": "text/event-stream",
            "anthropic-beta": "prompt-caching-2024-07-31"  # 캐싱 베타 기능 활성화
        }
        
        # 요청 본문 (프롬프트 캐싱 적용)
        if enable_caching:
            # System prompt를 캐싱 가능한 형식으로 변경
            body = {
                "model": model_id,
                "max_tokens": MAX_TOKENS,
                "temperature": TEMPERATURE,
                "system": [
                    {
                        "type": "text",
                        "text": static_system_prompt,
                        "cache_control": {"type": "ephemeral"}  # Anthropic 자동 TTL 관리 (~5분)
                    }
                ],
                "messages": [
                    {"role": "user", "content": enhanced_user_message}
                ],
                "stream": True
            }
        else:
            # 캐싱 미사용 시 기존 방식
            body = {
                "model": model_id,
                "max_tokens": MAX_TOKENS,
                "temperature": TEMPERATURE,
                "system": static_system_prompt,
                "messages": [
                    {"role": "user", "content": enhanced_user_message}
                ],
                "stream": True
            }
        
        # 웹 검색 도구 추가
        if enable_web_search:
            body["tools"] = [
                {
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": 5  # 최대 5번까지 웹 검색 허용
                }
            ]
            logger.info("웹 검색 기능이 활성화되었습니다")
        
        logger.info(f"Calling Anthropic API with model: {model_id} (caching: {enable_caching})")
        
        # API 호출 (스트리밍)
        response = requests.post(
            ANTHROPIC_API_URL,
            headers=headers,
            json=body,
            stream=True
        )
        
        if response.status_code != 200:
            error_msg = f"API 오류: {response.status_code} - {response.text}"
            logger.error(error_msg)
            yield f"[오류] {error_msg}"
            return
        
        # 사용량 추적
        usage_info = {
            'input_tokens': 0,
            'output_tokens': 0,
            'cache_read_input_tokens': 0,
            'cache_creation_input_tokens': 0
        }

        # 스트리밍 응답 처리 (Anthropic SSE 형식)
        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')

                # event: 라인 무시 (Anthropic SSE 형식)
                if line_text.startswith('event: '):
                    continue

                # SSE 형식 파싱
                if line_text.startswith('data: '):
                    data_str = line_text[6:]  # 'data: ' 제거

                    if data_str == '[DONE]':
                        logger.info("Streaming completed (DONE marker)")
                        break

                    try:
                        data = json.loads(data_str)
                        event_type = data.get('type', '')

                        # 메시지 시작 이벤트 (사용량 정보 포함)
                        if event_type == 'message_start':
                            message = data.get('message', {})
                            usage = message.get('usage', {})
                            usage_info.update({
                                'input_tokens': usage.get('input_tokens', 0),
                                'cache_read_input_tokens': usage.get('cache_read_input_tokens', 0),
                                'cache_creation_input_tokens': usage.get('cache_creation_input_tokens', 0)
                            })
                            logger.info(f"📥 message_start - input: {usage_info['input_tokens']}, "
                                       f"cache_read: {usage_info['cache_read_input_tokens']}, "
                                       f"cache_write: {usage_info['cache_creation_input_tokens']}")

                            # 캐시 히트/미스 로깅
                            if usage_info['cache_read_input_tokens'] > 0:
                                logger.info(f"🎯 Anthropic Cache HIT! Read {usage_info['cache_read_input_tokens']} tokens from cache")
                            if usage_info['cache_creation_input_tokens'] > 0:
                                logger.info(f"💾 Anthropic Cache MISS! Created cache with {usage_info['cache_creation_input_tokens']} tokens")

                        # 컨텐츠 블록 델타 처리
                        elif event_type == 'content_block_delta':
                            delta = data.get('delta', {})
                            if delta.get('type') == 'text_delta':
                                text = delta.get('text', '')
                                if text:
                                    yield text

                        # 메시지 델타 (최종 사용량 - output_tokens)
                        elif event_type == 'message_delta':
                            usage = data.get('usage', {})
                            if usage.get('output_tokens'):
                                usage_info['output_tokens'] = usage.get('output_tokens', 0)
                                logger.info(f"📤 message_delta - output: {usage_info['output_tokens']}")

                        # 메시지 종료 (Anthropic SSE 종료 이벤트)
                        elif event_type == 'message_stop':
                            logger.info("Streaming completed (message_stop)")
                            _log_usage(usage_info)
                            break

                        # 에러 처리
                        elif event_type == 'error':
                            error = data.get('error', {})
                            error_msg = error.get('message', '알 수 없는 오류')
                            logger.error(f"API Error: {error_msg}")
                            yield f"\n\n[오류] {error_msg}"
                            break

                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse SSE data: {data_str[:100]}... Error: {e}")
                        continue

        # 스트림 종료 시 사용량 로깅 (message_stop 없이 종료된 경우)
        if usage_info['input_tokens'] > 0 or usage_info['output_tokens'] > 0:
            logger.info(f"📊 Final usage: {usage_info}")
            _log_usage(usage_info)
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        yield f"\n\n[오류] 네트워크 오류: {str(e)}"
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        yield f"\n\n[오류] 예상치 못한 오류: {str(e)}"


class AnthropicClient:
    """Anthropic API 직접 호출 클라이언트"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: Anthropic API 키 (없으면 Secrets Manager에서 가져옴)
        """
        self.api_key = api_key or get_api_key_from_secrets()
        if not self.api_key:
            logger.warning("Anthropic API key not set")

        self.model_id = MODEL_ID
        self.max_tokens = MAX_TOKENS
        self.temperature = TEMPERATURE
        self.last_usage = {}  # Usage 추적용
        logger.info("AnthropicClient initialized with caching support")

    def _apply_conversation_caching(self, conversation_history: list) -> list:
        """
        대화 히스토리에 캐싱 적용

        전략:
        - Anthropic은 최대 4개의 cache breakpoint 지원
        - 시스템 프롬프트에 1개 사용 중
        - 대화 히스토리에서 최대 3개 사용 가능
        """
        cached_messages = []
        history_len = len(conversation_history)

        cache_points = set()
        if history_len >= 2:
            cache_points.add(0)
        if history_len >= 4:
            cache_points.add(history_len // 2)
        if history_len >= 6:
            cache_points.add(history_len - 2)

        for idx, msg in enumerate(conversation_history):
            role = msg.get('role', 'user')
            content = msg.get('content', '')

            if not content:
                continue

            if role == 'user' and idx in cache_points:
                cached_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "text",
                        "text": content,
                        "cache_control": {"type": "ephemeral"}
                    }]
                })
                logger.info(f"🔖 Cache breakpoint at turn {idx}")
            else:
                cached_messages.append({"role": role, "content": content})

        return cached_messages

    def stream_response_with_history(
        self,
        messages: list,
        system_prompt: str,
        enable_caching: bool = True,
        enable_web_search: bool = False,
        model_id: str = 'opus-4-20250514'
    ):
        """대화 히스토리를 포함한 스트리밍 응답 생성 (캐싱 적용)"""
        try:
            api_key = self.api_key or get_api_key_from_secrets()
            if not api_key:
                yield "[오류] API 키가 설정되지 않았습니다."
                return

            headers = {
                "x-api-key": api_key,
                "anthropic-version": ANTHROPIC_VERSION,
                "anthropic-beta": "prompt-caching-2024-07-31",
                "content-type": "application/json",
                "accept": "text/event-stream"
            }

            static_system_prompt = _replace_template_variables(system_prompt)

            # 동적 컨텍스트 생성 (현재 시간 정보)
            dynamic_context = _create_dynamic_context()

            # 대화 히스토리 캐싱 적용
            if enable_caching and len(messages) > 1:
                history = messages[:-1]  # 마지막 메시지 제외
                current = messages[-1]   # 현재 메시지
                # 현재 메시지에 동적 컨텍스트 추가
                current_with_context = {
                    "role": current.get("role", "user"),
                    "content": f"{dynamic_context}\n\n{current.get('content', '')}"
                }
                cached_history = self._apply_conversation_caching(history)
                processed_messages = cached_history + [current_with_context]
                logger.info(f"📚 Conversation caching applied: {len(history)} history messages, {len(cached_history)} cached")
            else:
                # 단일 메시지인 경우에도 동적 컨텍스트 추가
                if messages:
                    current = messages[-1]
                    current_with_context = {
                        "role": current.get("role", "user"),
                        "content": f"{dynamic_context}\n\n{current.get('content', '')}"
                    }
                    processed_messages = messages[:-1] + [current_with_context] if len(messages) > 1 else [current_with_context]
                else:
                    processed_messages = messages

            logger.info(f"📤 Calling Anthropic API with history caching, model: {model_id}, messages: {len(processed_messages)}")

            body = {
                "model": model_id,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": processed_messages,
                "stream": True
            }

            if enable_caching:
                body["system"] = [{
                    "type": "text",
                    "text": static_system_prompt,
                    "cache_control": {"type": "ephemeral"}
                }]
            else:
                body["system"] = static_system_prompt

            if enable_web_search:
                body["tools"] = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}]

            response = requests.post(ANTHROPIC_API_URL, headers=headers, json=body, stream=True)

            if response.status_code != 200:
                yield f"[오류] API 오류: {response.status_code}"
                return

            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if line_text.startswith('event: '):
                        continue
                    if line_text.startswith('data: '):
                        data_str = line_text[6:]
                        if data_str == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            event_type = data.get('type', '')

                            if event_type == 'message_start':
                                message = data.get('message', {})
                                usage = message.get('usage', {})
                                if usage:
                                    cache_read = usage.get('cache_read_input_tokens', 0)
                                    cache_write = usage.get('cache_creation_input_tokens', 0)
                                    if cache_read > 0:
                                        logger.info(f"🎯 CONVERSATION CACHE HIT! cache_read: {cache_read} tokens")
                                    elif cache_write > 0:
                                        logger.info(f"📝 CONVERSATION CACHE MISS - cache_write: {cache_write} tokens")
                                    cost = _calculate_cost(usage)
                                    logger.info(f"💰 Token Usage: input={usage.get('input_tokens', 0)}, output={usage.get('output_tokens', 0)}, cache_read={cache_read}, cache_write={cache_write}")
                                    logger.info(f"💰 API Cost: ${cost:.6f}")

                            elif event_type == 'content_block_delta':
                                delta = data.get('delta', {})
                                if delta.get('type') == 'text_delta':
                                    text = delta.get('text', '')
                                    if text:
                                        yield text

                            elif event_type == 'message_stop':
                                logger.info("✅ Message complete")
                                return
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            logger.error(f"Error in stream_response_with_history: {str(e)}")
            yield f"\n\n[오류] AI 응답 생성 실패: {str(e)}"
    
    def stream_response(
        self,
        user_message: str,
        system_prompt: str,
        conversation_context: str = "",
        enable_web_search: bool = False,
        enable_caching: bool = True,
        model_id: str = 'opus-4-20250514'
    ) -> Iterator[str]:
        """
        스트리밍 응답 생성
        
        Args:
            user_message: 사용자 메시지
            system_prompt: 시스템 프롬프트
            conversation_context: 대화 컨텍스트
            enable_web_search: 웹 검색 기능 활성화
        
        Yields:
            응답 청크
        """
        try:
            # 시스템 프롬프트는 정적으로 유지 (캐싱 최적화)
            # 대화 컨텍스트는 user_message에 추가하여 캐시 무효화 방지
            static_system_prompt = self._replace_template_variables(system_prompt)

            # 동적 컨텍스트와 대화 컨텍스트를 user_message에 추가
            enhanced_user_message = self._create_message_with_context(user_message, conversation_context)
            
            logger.info(f"Streaming with Anthropic API, model: {model_id} (caching: {enable_caching})")

            # Anthropic API 스트리밍
            for chunk in stream_anthropic_response(
                user_message=enhanced_user_message,
                system_prompt=static_system_prompt,
                api_key=self.api_key,
                enable_web_search=enable_web_search,
                enable_caching=enable_caching,
                model_id=model_id
            ):
                yield chunk
        
        except Exception as e:
            logger.error(f"Error in stream_response: {str(e)}")
            yield f"\n\n[오류] 응답 생성 실패: {str(e)}"
    
    def _replace_template_variables(self, prompt: str) -> str:
        """정적 템플릿 변수 치환 (캐싱 최적화용)"""
        replacements = {
            '{{user_location}}': '대한민국',
            '{{timezone}}': 'Asia/Seoul (KST)',
            '{{language}}': '한국어',
            '{{service_name}}': 'Sedaily Column'
        }
        
        result = prompt
        for key, value in replacements.items():
            result = result.replace(key, value)
        
        return result
    
    def _create_dynamic_message(self, user_message: str) -> str:
        """동적 컨텍스트를 user_message에 추가 (캐시 무효화 방지)"""
        # 한국 시간 (UTC+9)
        kst = timezone(timedelta(hours=9))
        current_time = datetime.now(kst)
        session_id = str(uuid.uuid4())[:8]
        
        # 동적 컨텍스트 정보 (user_message에만 포함)
        dynamic_context = f"""[현재 세션 정보]
- 현재 시간: {current_time.strftime('%Y-%m-%d %H:%M:%S KST')}
- 세션 ID: {session_id}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

사용자의 질문: {user_message}"""
        
        return dynamic_context
    
    def _create_message_with_context(self, user_message: str, conversation_context: str) -> str:
        """대화 컨텍스트를 메시지에 포함 (기존 호환성 유지)"""
        dynamic_msg = self._create_dynamic_message(user_message)
        
        if conversation_context:
            return f"""{conversation_context}

위의 대화 내용을 참고하여 답변해주세요.

{dynamic_msg}"""
        return dynamic_msg