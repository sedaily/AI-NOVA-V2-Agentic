"""
Anthropic API 직접 호출 클라이언트 - Prompt Caching 최적화 버전
AWS Bedrock 대신 Anthropic API를 직접 사용
비용 최적화를 위한 Prompt Caching 적용
"""
import os
import sys
import json
import logging
import urllib.request
import urllib.parse
import urllib.error
import boto3
import uuid
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Iterator, Optional

# 상위 디렉토리를 경로에 추가하여 utils 모듈 임포트 가능하게 함
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from utils.logger import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    # Fallback to standard logging if custom logger not available
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)

# Secrets Manager 클라이언트
secrets_client = boto3.client('secretsmanager', region_name='us-east-1')

def get_api_key_from_secrets():
    """Secrets Manager에서 API 키 가져오기"""
    try:
        secret_name = os.environ.get('ANTHROPIC_SECRET_NAME', 'foreign-v1')
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

# 모델 설정
MODEL_ID = os.environ.get('ANTHROPIC_MODEL_ID', "opus-4-20250514")  # Claude Opus 4.6
MAX_TOKENS = int(os.environ.get('MAX_TOKENS', '4096'))
TEMPERATURE = float(os.environ.get('TEMPERATURE', '0.3'))

# 웹 검색 설정
ENABLE_NATIVE_WEB_SEARCH = os.environ.get('ENABLE_NATIVE_WEB_SEARCH', 'true').lower() == 'true'
WEB_SEARCH_MAX_USES = int(os.environ.get('WEB_SEARCH_MAX_USES', '5'))

# 캐싱 설정 (Anthropic API는 TTL을 자동 관리 - 약 5분)

def _replace_template_variables(prompt: str) -> str:
    """
    정적 템플릿 변수만 치환 (캐싱 최적화)
    동적 변수는 user_message에 추가하여 캐시 무효화 방지
    """
    replacements = {
        '{{user_location}}': '대한민국',
        '{{timezone}}': 'Asia/Seoul (KST)',
        '{{language}}': '한국어',
        '{{service_name}}': '교열 서비스'
    }
    
    for key, value in replacements.items():
        prompt = prompt.replace(key, value)
    
    return prompt

def _create_dynamic_context() -> str:
    """
    동적 컨텍스트 생성 (user_message에 추가용)
    캐시 무효화를 방지하기 위해 system prompt가 아닌 user message에 포함
    """
    kst = timezone(timedelta(hours=9))
    current_time = datetime.now(kst)
    session_id = str(uuid.uuid4())[:8]
    
    return f"""[현재 세션 정보]
- 현재 시간: {current_time.strftime('%Y-%m-%d %H:%M:%S KST')}
- 오늘 날짜: {current_time.strftime('%Y년 %m월 %d일')}
- 사용자 위치: 대한민국 (Asia/Seoul)
- 세션 ID: {session_id}
- 연도 기준: {current_time.year}년"""

def stream_anthropic_response(
    user_message: str,
    system_prompt: str,
    api_key: Optional[str] = None,
    enable_web_search: bool = False,
    web_search_max_uses: int = 5,
    use_caching: bool = True,
    model_id: str = None
) -> Iterator[Dict[str, Any]]:
    """
    Anthropic API를 통한 스트리밍 응답 생성 (Prompt Caching 적용)
    
    Args:
        user_message: 사용자 메시지
        system_prompt: 시스템 프롬프트
        api_key: API 키 (없으면 환경변수 사용)
        enable_web_search: 웹 검색 도구 활성화 여부
        web_search_max_uses: 웹 검색 최대 사용 횟수
        use_caching: 프롬프트 캐싱 사용 여부
        model_id: 사용할 모델 ID (None이면 기본 모델 사용)

    Yields:
        응답 딕셔너리 (텍스트 청크, 사용량 정보 등)
    """
    try:
        # Model selection (parameter takes priority, fallback to default)
        selected_model = model_id or MODEL_ID
        logger.info(f"Using model: {selected_model}")

        # API 키 확인 (Secrets Manager에서 가져오기)
        api_key = api_key or get_api_key_from_secrets()
        if not api_key:
            logger.error("Anthropic API key not found")
            yield {"error": "API 키가 설정되지 않았습니다."}
            return
        
        # 요청 헤더
        headers = {
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "anthropic-beta": "prompt-caching-2024-07-31",  # Prompt Caching 베타 헤더
            "content-type": "application/json",
            "accept": "text/event-stream"
        }
        
        # 정적 변수 치환 (캐시 가능하도록)
        static_system_prompt = _replace_template_variables(system_prompt)
        
        # 동적 컨텍스트를 user message에 추가
        dynamic_context = _create_dynamic_context()
        enhanced_user_message = f"{dynamic_context}\n\n{user_message}"
        
        # 요청 본문 (Prompt Caching 적용)
        body = {
            "model": selected_model,  # Use selected model instead of default
            "max_tokens": MAX_TOKENS,
            "temperature": TEMPERATURE,
            "messages": [
                {"role": "user", "content": enhanced_user_message}
            ],
            "stream": True
        }
        
        # Prompt Caching 적용 (system prompt만 캐싱)
        if use_caching:
            body["system"] = [
                {
                    "type": "text",
                    "text": static_system_prompt,
                    "cache_control": {"type": "ephemeral"}  # Anthropic 자동 TTL 관리 (~5분)
                }
            ]
            logger.info("✅ Prompt caching enabled (ephemeral)")
        else:
            body["system"] = static_system_prompt
        
        # 웹 검색 도구 추가
        if enable_web_search and ENABLE_NATIVE_WEB_SEARCH:
            body["tools"] = [
                {
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": web_search_max_uses
                }
            ]
            logger.info(f"Web search enabled (max uses: {web_search_max_uses})")
        
        logger.info(f"Calling Anthropic API with model: {selected_model}, caching: {use_caching}")
        
        # API 호출 (스트리밍)
        data = json.dumps(body).encode('utf-8')
        request = urllib.request.Request(
            ANTHROPIC_API_URL,
            data=data,
            headers=headers,
            method='POST'
        )
        response = urllib.request.urlopen(request)
        
        if response.status != 200:
            error_msg = f"API 오류: {response.status} - {response.reason}"
            logger.error(error_msg)
            yield {"error": error_msg}
            return
        
        # 사용량 추적을 위한 변수
        usage_info = {
            'input_tokens': 0,
            'output_tokens': 0,
            'cache_read_input_tokens': 0,
            'cache_creation_input_tokens': 0
        }
        
        # 스트리밍 응답 처리 (Anthropic SSE 형식)
        buffer = ""
        for line in response:
            if line:
                line_text = line.decode('utf-8').strip()

                # 빈 줄 무시
                if not line_text:
                    continue

                # event: 라인 (Anthropic SSE 형식)
                if line_text.startswith('event: '):
                    continue  # 이벤트 타입은 data에서 처리

                # SSE 형식 파싱
                if line_text.startswith('data: '):
                    data_str = line_text[6:]  # 'data: ' 제거

                    # OpenAI 호환 종료 마커
                    if data_str == '[DONE]':
                        logger.info("Streaming completed (DONE marker)")
                        yield {"usage": usage_info}
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
                            logger.info(f"📥 message_start - input: {usage_info['input_tokens']}, cache_read: {usage_info['cache_read_input_tokens']}, cache_write: {usage_info['cache_creation_input_tokens']}")

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
                                    yield {"text": text}

                        # 메시지 델타 (최종 사용량 - output_tokens)
                        elif event_type == 'message_delta':
                            usage = data.get('usage', {})
                            if usage.get('output_tokens'):
                                usage_info['output_tokens'] = usage.get('output_tokens', 0)
                                logger.info(f"📤 message_delta - output: {usage_info['output_tokens']}")

                        # 메시지 종료 (Anthropic SSE 종료 이벤트)
                        elif event_type == 'message_stop':
                            logger.info("Streaming completed (message_stop)")
                            yield {"usage": usage_info}
                            break

                        # 에러 처리
                        elif event_type == 'error':
                            error = data.get('error', {})
                            error_msg = error.get('message', '알 수 없는 오류')
                            logger.error(f"API Error: {error_msg}")
                            yield {"error": error_msg}
                            break

                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse SSE data: {data_str[:100]}... Error: {e}")
                        continue

        # 스트림 종료 시 사용량 반환 (message_stop 없이 종료된 경우)
        if usage_info['input_tokens'] > 0 or usage_info['output_tokens'] > 0:
            logger.info(f"📊 Final usage: {usage_info}")
            yield {"usage": usage_info}
    
    except urllib.error.URLError as e:
        logger.error(f"Request error: {str(e)}")
        yield {"error": f"네트워크 오류: {str(e)}"}
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        yield {"error": f"예상치 못한 오류: {str(e)}"}


class AnthropicClient:
    """Anthropic API 직접 호출 클라이언트 (Prompt Caching 최적화)"""

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
        self.last_usage = {}  # 마지막 사용량 정보 저장

        logger.info("AnthropicClient initialized with prompt caching support")

    def _apply_conversation_caching(self, conversation_history: list) -> list:
        """
        대화 히스토리에 캐싱 적용

        전략:
        - Anthropic은 최대 4개의 cache breakpoint 지원
        - 시스템 프롬프트에 1개 사용 중
        - 대화 히스토리에서 최대 3개 사용 가능
        - 마지막 user 메시지를 제외한 이전 턴들을 캐싱
        """
        cached_messages = []
        history_len = len(conversation_history)

        # 캐싱할 포인트 결정 (최대 3개)
        cache_points = set()
        if history_len >= 2:
            cache_points.add(0)  # 첫 번째 턴
        if history_len >= 4:
            cache_points.add(history_len // 2)  # 중간 턴
        if history_len >= 6:
            cache_points.add(history_len - 2)  # 마지막에서 두 번째 턴

        for idx, msg in enumerate(conversation_history):
            role = msg.get('role', 'user')
            content = msg.get('content', '')

            if not content:
                continue

            # user 메시지에만 cache_control 적용 (Anthropic 제약)
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
                cached_messages.append({
                    "role": role,
                    "content": content
                })

        return cached_messages

    def stream_response_with_history(
        self,
        messages: list,
        system_prompt: str,
        enable_caching: bool = True,
        enable_web_search: bool = False,
        model_id: str = None
    ):
        """
        대화 히스토리를 포함한 스트리밍 응답 생성

        Args:
            messages: 캐싱이 적용된 메시지 리스트
            system_prompt: 시스템 프롬프트
            enable_caching: 시스템 프롬프트 캐싱 활성화
            enable_web_search: 웹 검색 활성화
        """
        logger.info(f"🚀 stream_response_with_history STARTED - messages: {len(messages)}, model: {model_id}")
        try:
            api_key = self.api_key or get_api_key_from_secrets()
            if not api_key:
                logger.error("❌ API key not found!")
                yield "[오류] API 키가 설정되지 않았습니다."
                return
            logger.info("✅ API key retrieved successfully")

            # 요청 헤더
            headers = {
                "x-api-key": api_key,
                "anthropic-version": ANTHROPIC_VERSION,
                "anthropic-beta": "prompt-caching-2024-07-31",
                "content-type": "application/json",
                "accept": "text/event-stream"
            }

            # 정적 변수 치환
            static_system_prompt = _replace_template_variables(system_prompt)

            # 사용할 모델 결정
            use_model = model_id if model_id else self.model_id

            # 동적 컨텍스트 생성 (현재 시간 정보)
            dynamic_context = _create_dynamic_context()

            # 마지막 메시지에 동적 컨텍스트 추가
            if messages:
                messages_with_context = messages[:-1] + [{
                    "role": messages[-1].get("role", "user"),
                    "content": f"{dynamic_context}\n\n{messages[-1].get('content', '')}"
                }]
            else:
                messages_with_context = messages

            # 대화 히스토리에 캐시 브레이크포인트 적용
            if enable_caching and len(messages_with_context) >= 2:
                cached_messages = self._apply_conversation_caching(messages_with_context)
                logger.info(f"📤 Calling Anthropic API with CONVERSATION caching, model: {use_model}, messages: {len(cached_messages)}")
            else:
                cached_messages = messages_with_context
                logger.info(f"📤 Calling Anthropic API (no conversation cache), model: {use_model}, messages: {len(messages_with_context)}")

            # 요청 본문
            body = {
                "model": use_model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": cached_messages,
                "stream": True
            }

            # 시스템 프롬프트 캐싱
            if enable_caching:
                body["system"] = [{
                    "type": "text",
                    "text": static_system_prompt,
                    "cache_control": {"type": "ephemeral"}
                }]
            else:
                body["system"] = static_system_prompt

            # 웹 검색 도구
            if enable_web_search:
                body["tools"] = [{
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": 5
                }]
                logger.info("🌐 Web search tool enabled")

            # API 호출 (requests 사용)
            logger.info(f"📡 Making API request to Anthropic with {len(messages)} messages...")
            response = requests.post(
                ANTHROPIC_API_URL,
                headers=headers,
                json=body,
                stream=True,
                timeout=180
            )
            logger.info(f"📥 API Response status: {response.status_code}")

            if response.status_code != 200:
                error_text = response.text[:500]
                logger.error(f"API Error: {response.status_code} - {error_text}")
                yield f"[오류] API 오류: {response.status_code} - {error_text}"
                return

            # 스트리밍 처리
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8').strip()
                    if not line_text or line_text.startswith('event: '):
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

                                    cost = self._calculate_cost(usage)
                                    logger.info(f"💰 Token Usage: input={usage.get('input_tokens', 0)}, "
                                              f"output={usage.get('output_tokens', 0)}, "
                                              f"cache_read={cache_read}, cache_write={cache_write}")
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
    
    def _calculate_cost(self, usage: Dict[str, int]) -> float:
        """
        비용 계산 (Claude Opus 4.5 기준)
        
        Pricing (per 1M tokens):
        - Base Input: $5.00
        - Output: $25.00
        - Cache Write (1h): $10.00
        - Cache Read: $0.50
        """
        PRICE_INPUT = 5.0  # Base Input Tokens
        PRICE_OUTPUT = 25.0  # Output Tokens
        PRICE_CACHE_WRITE = 10.0  # 1h Cache Writes
        PRICE_CACHE_READ = 0.50  # Cache Hits
        
        cost_input = (usage.get('input_tokens', 0) / 1_000_000) * PRICE_INPUT
        cost_output = (usage.get('output_tokens', 0) / 1_000_000) * PRICE_OUTPUT
        cost_cache_write = (usage.get('cache_creation_input_tokens', 0) / 1_000_000) * PRICE_CACHE_WRITE
        cost_cache_read = (usage.get('cache_read_input_tokens', 0) / 1_000_000) * PRICE_CACHE_READ
        
        total_cost = cost_input + cost_output + cost_cache_write + cost_cache_read
        
        # 상세 비용 로깅
        logger.info(f"💰 Cost Breakdown:")
        logger.info(f"  - Input: ${cost_input:.6f} ({usage.get('input_tokens', 0)} tokens)")
        logger.info(f"  - Output: ${cost_output:.6f} ({usage.get('output_tokens', 0)} tokens)")
        logger.info(f"  - Cache Write: ${cost_cache_write:.6f} ({usage.get('cache_creation_input_tokens', 0)} tokens)")
        logger.info(f"  - Cache Read: ${cost_cache_read:.6f} ({usage.get('cache_read_input_tokens', 0)} tokens)")
        logger.info(f"  - TOTAL: ${total_cost:.6f}")
        
        return total_cost
    
    def stream_response(
        self,
        user_message: str,
        system_prompt: str,
        conversation_context: str = "",
        enable_web_search: bool = False,
        web_search_max_uses: int = 5,
        use_caching: bool = True,
        model_id: str = None
    ) -> Iterator[str]:
        """
        스트리밍 응답 생성 (Prompt Caching 적용)
        
        Args:
            user_message: 사용자 메시지
            system_prompt: 시스템 프롬프트
            conversation_context: 대화 컨텍스트
            enable_web_search: 웹 검색 활성화 여부
            web_search_max_uses: 웹 검색 최대 사용 횟수
            use_caching: 프롬프트 캐싱 사용 여부
            model_id: 사용할 모델 ID (None이면 기본 모델 사용)

        Yields:
            응답 청크
        """
        try:
            # Model selection (parameter takes priority, fallback to default)
            selected_model = model_id or self.model_id
            logger.info(f"Using model: {selected_model}")

            # 시스템 프롬프트는 정적으로 유지 (캐싱 최적화)
            # 대화 컨텍스트는 user_message에 추가하여 캐시 무효화 방지
            full_prompt = system_prompt

            # 대화 컨텍스트를 user_message에 추가
            if conversation_context:
                user_message = f"{conversation_context}\n\n[현재 질문]\n{user_message}"
            
            logger.info(f"Streaming with Anthropic API (web_search: {enable_web_search}, caching: {use_caching})")
            
            # 사용량 추적 초기화
            self.last_usage = {
                'input_tokens': 0,
                'output_tokens': 0,
                'cache_read_input_tokens': 0,
                'cache_creation_input_tokens': 0
            }
            
            # Anthropic API 스트리밍 (Prompt Caching 포함)
            for chunk in stream_anthropic_response(
                user_message=user_message,
                system_prompt=full_prompt,
                api_key=self.api_key,
                enable_web_search=enable_web_search,
                web_search_max_uses=web_search_max_uses,
                use_caching=use_caching,
                model_id=selected_model  # Pass selected model to API call
            ):
                if "text" in chunk:
                    yield chunk["text"]
                elif "usage" in chunk:
                    # 사용량 정보 업데이트
                    self.last_usage.update(chunk["usage"])
                    
                    # 비용 계산
                    cost = self._calculate_cost(self.last_usage)
                    self.last_usage['total_cost'] = cost
                    
                    # 캐시 효율성 계산
                    total_input = self.last_usage['input_tokens'] + self.last_usage['cache_creation_input_tokens']
                    if total_input > 0:
                        cache_efficiency = (self.last_usage['cache_read_input_tokens'] / total_input) * 100
                        logger.info(f"📊 Cache Efficiency: {cache_efficiency:.1f}%")
                
                elif "error" in chunk:
                    yield f"\n\n[오류] {chunk['error']}"
        
        except Exception as e:
            logger.error(f"Error in stream_response: {str(e)}")
            yield f"\n\n[오류] 응답 생성 실패: {str(e)}"
    
    def get_last_usage(self) -> Dict[str, Any]:
        """마지막 요청의 사용량 정보 반환"""
        return self.last_usage