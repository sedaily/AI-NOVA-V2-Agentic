"""
Anthropic API 클라이언트 - AWS Bedrock 대체/병행용
Claude Opus 4.5 API 직접 호출 지원
"""
import json
import logging
import os
import sys
import time
import requests
from typing import Dict, Any, Iterator, List, Optional
from datetime import datetime, timezone, timedelta
import boto3
from botocore.exceptions import ClientError

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config.aws import AWS_REGION
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Secrets Manager 클라이언트
secrets_client = boto3.client('secretsmanager', region_name=AWS_REGION)

# Anthropic API 설정
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_API_VERSION = "2023-06-01"

# 모델 설정 (환경변수로 오버라이드 가능)
DEFAULT_MODEL = "claude-3-5-sonnet-20241022"  # 기본값 (Sonnet 사용)
OPUS_MODEL = os.environ.get('ANTHROPIC_MODEL_ID', 'claude-opus-4-5-20251101')  # Opus 4.5 최신 버전

# 토큰 설정
MAX_TOKENS = int(os.environ.get('MAX_TOKENS', '4096'))
TEMPERATURE = float(os.environ.get('TEMPERATURE', '0.3'))
TOP_P = float(os.environ.get('TOP_P', '0.95'))
TOP_K = int(os.environ.get('TOP_K', '40'))

# Rate limit 설정
RATE_LIMIT_DELAY = 1.0  # 요청 간 최소 대기 시간 (초)
MAX_RETRIES = 3
RETRY_DELAY = 60  # Rate limit 시 대기 시간 (초)

class AnthropicClient:
    """Anthropic API 클라이언트"""
    
    def __init__(self):
        """클라이언트 초기화"""
        self.api_key = self._get_api_key()
        self.last_request_time = 0
        self.model_id = self._get_model_id()
        self.service_name = os.environ.get('SERVICE_NAME', 'buddy')  # 서비스 식별자
        logger.info(f"AnthropicClient initialized with model: {self.model_id}, service: {self.service_name}")
    
    def _get_model_id(self) -> str:
        """사용할 모델 ID 결정"""
        # 환경변수에서 모델 선택
        use_opus = os.environ.get('USE_OPUS_MODEL', 'true').lower() == 'true'
        
        if use_opus:
            return OPUS_MODEL
        return DEFAULT_MODEL
    
    def _get_api_key(self) -> str:
        """AWS Secrets Manager에서 API 키 가져오기"""
        try:
            secret_name = os.environ.get('ANTHROPIC_SECRET_NAME', 'buddy-v1')
            
            response = secrets_client.get_secret_value(SecretId=secret_name)
            secret = json.loads(response['SecretString'])
            
            # API 키 추출 (다양한 키 이름 지원)
            api_key = (secret.get('api_key') or 
                      secret.get('API_KEY') or 
                      secret.get('anthropic_api_key') or
                      secret.get('ANTHROPIC_API_KEY'))
            
            if not api_key:
                raise ValueError(f"API key not found in secret: {secret_name}")
            
            logger.info(f"✅ API key loaded from Secrets Manager: {secret_name}")
            return api_key
            
        except ClientError as e:
            logger.error(f"Failed to get API key from Secrets Manager: {str(e)}")
            # 환경변수 폴백 (개발용)
            api_key = os.environ.get('ANTHROPIC_API_KEY')
            if api_key:
                logger.warning("⚠️ Using API key from environment variable (not recommended for production)")
                return api_key
            raise ValueError("Anthropic API key not found in Secrets Manager or environment")
    
    def _apply_rate_limit(self):
        """Rate limit 적용"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < RATE_LIMIT_DELAY:
            sleep_time = RATE_LIMIT_DELAY - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _get_default_metadata(self) -> Dict[str, Any]:
        """기본 메타데이터 생성"""
        return {
            "user_id": self.service_name  # 'buddy' 서비스 식별
        }
    
    def _make_request(self, messages: List[Dict], system: str, stream: bool = False, metadata: Optional[Dict] = None) -> Any:
        """API 요청 실행"""
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": ANTHROPIC_API_VERSION,
            "content-type": "application/json"
        }
        
        # Claude 4.5 Opus는 temperature와 top_p를 동시에 사용할 수 없음
        body = {
            "model": self.model_id,
            "max_tokens": MAX_TOKENS,
            "temperature": TEMPERATURE,  # temperature만 사용
            "messages": messages,
            "system": system,
            "stream": stream
        }
        
        # top_k는 선택적으로 추가 (Claude 4.5 Opus에서 지원)
        if TOP_K > 0:
            body["top_k"] = TOP_K
        
        # 메타데이터 추가 (서비스 추적용)
        if metadata:
            body["metadata"] = metadata
        else:
            body["metadata"] = self._get_default_metadata()
        
        # Rate limit 적용
        self._apply_rate_limit()
        
        # 스트리밍 요청
        if stream:
            response = requests.post(
                ANTHROPIC_API_URL,
                headers=headers,
                json=body,
                stream=True,
                timeout=30
            )
            return response
        
        # 일반 요청
        response = requests.post(
            ANTHROPIC_API_URL,
            headers=headers,
            json=body,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            self._handle_error(response)
    
    def _handle_error(self, response):
        """API 오류 처리"""
        error_msg = f"API request failed: {response.status_code}"
        
        try:
            error_data = response.json()
            error_msg = f"{error_msg} - {error_data.get('error', {}).get('message', response.text)}"
        except:
            error_msg = f"{error_msg} - {response.text}"
        
        # Rate limit 오류
        if response.status_code == 429:
            logger.warning(f"Rate limit exceeded: {error_msg}")
            raise RateLimitError(error_msg)
        
        # 기타 오류
        logger.error(error_msg)
        raise Exception(error_msg)
    
    def stream_response(
        self,
        user_message: str,
        system_prompt: str,
        conversation_history: Optional[List[Dict]] = None,
        enable_caching: bool = True
    ) -> Iterator[str]:
        """
        스트리밍 응답 생성 (Bedrock 인터페이스와 호환)
        
        Args:
            user_message: 사용자 메시지
            system_prompt: 시스템 프롬프트
            conversation_history: 대화 이력
            enable_caching: 캐싱 활성화 여부 (Anthropic API는 자동 캐싱)
        
        Yields:
            응답 텍스트 청크
        """
        retry_count = 0
        
        while retry_count < MAX_RETRIES:
            try:
                # 메시지 구성
                messages = conversation_history if conversation_history else []
                messages.append({"role": "user", "content": user_message})
                
                logger.info(f"📤 Calling Anthropic API with model: {self.model_id}, service: {self.service_name}")
                
                # API 호출 (스트리밍) - 메타데이터 포함
                response = self._make_request(
                    messages=messages,
                    system=system_prompt,
                    stream=True,
                    metadata={"user_id": self.service_name}  # buddy 서비스 식별
                )
                
                # 응답 체크
                if response.status_code != 200:
                    self._handle_error(response)
                
                # 스트리밍 처리
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        
                        # SSE 형식 파싱
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]  # "data: " 제거
                            
                            if data_str == '[DONE]':
                                logger.info("✅ Streaming completed")
                                return
                            
                            try:
                                data = json.loads(data_str)
                                
                                # 메시지 시작
                                if data.get('type') == 'message_start':
                                    message = data.get('message', {})
                                    usage = message.get('usage', {})
                                    if usage:
                                        logger.info(f"📊 Token usage - input: {usage.get('input_tokens', 0)}, "
                                                   f"output: {usage.get('output_tokens', 0)}")
                                
                                # 컨텐츠 델타
                                elif data.get('type') == 'content_block_delta':
                                    delta = data.get('delta', {})
                                    if delta.get('type') == 'text_delta':
                                        text = delta.get('text', '')
                                        if text:
                                            yield text
                                
                                # 메시지 종료
                                elif data.get('type') == 'message_stop':
                                    logger.info("✅ Message complete")
                                    return
                                
                                # 오류
                                elif data.get('type') == 'error':
                                    error = data.get('error', {})
                                    raise Exception(f"Stream error: {error.get('message', 'Unknown error')}")
                                    
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse SSE data: {data_str[:100]}")
                                continue
                
                return
                
            except RateLimitError as e:
                retry_count += 1
                if retry_count >= MAX_RETRIES:
                    logger.error(f"Max retries exceeded for rate limit")
                    
                    # Bedrock 폴백 옵션 체크
                    if os.environ.get('FALLBACK_TO_BEDROCK', 'false').lower() == 'true':
                        logger.info("🔄 Falling back to Bedrock...")
                        yield "[Rate limit 초과 - Bedrock으로 전환]"
                        raise  # 상위 핸들러에서 Bedrock으로 처리
                    else:
                        yield f"\n\n[오류] API rate limit 초과. 잠시 후 다시 시도해주세요."
                        return
                
                wait_time = RETRY_DELAY * retry_count
                logger.warning(f"Rate limit hit, waiting {wait_time} seconds... (retry {retry_count}/{MAX_RETRIES})")
                time.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"Error in stream_response: {str(e)}")
                yield f"\n\n[오류] AI 응답 생성 실패: {str(e)}"
                return
    
    def stream_bedrock(
        self,
        user_message: str,
        engine_type: str,
        conversation_context: str = "",
        user_role: str = 'user',
        guidelines: Optional[str] = None,
        description: Optional[str] = None,
        files: Optional[List[Dict]] = None
    ) -> Iterator[str]:
        """
        Bedrock 호환 인터페이스
        BedrockClientEnhanced.stream_bedrock()과 동일한 시그니처
        
        이 메서드를 사용하면 기존 Bedrock 코드를 수정 없이 
        Anthropic API로 전환 가능
        """
        try:
            # Bedrock 스타일 프롬프트를 Anthropic 스타일로 변환
            from lib.bedrock_client_enhanced import create_enhanced_system_prompt
            
            prompt_data = {
                'prompt': {
                    'instruction': guidelines or "",
                    'description': description or ""
                },
                'files': files or [],
                'userRole': user_role
            }
            
            # 시스템 프롬프트 생성 (Bedrock과 동일한 로직 사용)
            system_prompt = create_enhanced_system_prompt(
                prompt_data,
                engine_type,
                use_enhanced=True,
                flexibility_level="strict"
            )
            
            # 대화 컨텍스트 포함
            enhanced_message = self._create_message_with_context(
                user_message,
                conversation_context
            )
            
            logger.info(f"🚀 Anthropic API streaming - Engine: {engine_type}, Role: {user_role}")
            
            # Anthropic API 호출
            for chunk in self.stream_response(
                user_message=enhanced_message,
                system_prompt=system_prompt,
                enable_caching=True
            ):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error in stream_bedrock compatibility: {str(e)}")
            
            # Bedrock 폴백
            if os.environ.get('FALLBACK_TO_BEDROCK', 'false').lower() == 'true':
                logger.info("🔄 Falling back to Bedrock due to error...")
                raise  # 상위 핸들러에서 처리
            else:
                yield f"\n\n[오류] 응답 생성 실패: {str(e)}"
    
    def _create_message_with_context(self, user_message: str, conversation_context: str) -> str:
        """대화 컨텍스트를 메시지에 포함"""
        # 한국 시간 (UTC+9)
        kst = timezone(timedelta(hours=9))
        current_time = datetime.now(kst)
        
        # 동적 컨텍스트 정보
        context_info = f"""[현재 세션 정보]
현재 시간: {current_time.strftime('%Y-%m-%d %H:%M:%S KST')}
사용자 위치: 대한민국
타임존: Asia/Seoul (KST)

※ 시간 관련 질문이 있으면 위의 현재 시간을 참조하세요.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
        
        if conversation_context:
            return f"""{context_info}{conversation_context}

위의 대화 내용을 참고하여 답변해주세요.

사용자의 질문: {user_message}
"""
        return f"""{context_info}사용자의 질문: {user_message}"""


class RateLimitError(Exception):
    """Rate limit 오류"""
    pass


def get_ai_client(prefer_anthropic: bool = None):
    """
    환경 설정에 따라 적절한 AI 클라이언트 반환
    
    Args:
        prefer_anthropic: True면 Anthropic, False면 Bedrock, None이면 환경변수 참조
    
    Returns:
        AnthropicClient 또는 BedrockClientEnhanced 인스턴스
    """
    try:
        # 명시적 선택이 있으면 우선
        if prefer_anthropic is not None:
            use_anthropic = prefer_anthropic
        else:
            # 환경변수 확인
            use_anthropic = os.environ.get('USE_ANTHROPIC_API', 'false').lower() == 'true'
        
        if use_anthropic:
            logger.info("🎯 Using Anthropic API")
            return AnthropicClient()
        else:
            logger.info("🎯 Using AWS Bedrock")
            from lib.bedrock_client_enhanced import BedrockClientEnhanced
            return BedrockClientEnhanced()
            
    except Exception as e:
        logger.error(f"Failed to initialize AI client: {str(e)}")
        # 기본값으로 Bedrock 사용
        logger.info("⚠️ Falling back to Bedrock due to initialization error")
        from lib.bedrock_client_enhanced import BedrockClientEnhanced
        return BedrockClientEnhanced()


# 사용 예시
if __name__ == "__main__":
    # 테스트 코드
    client = AnthropicClient()
    
    test_message = "안녕하세요! 오늘 날씨가 어떤가요?"
    test_prompt = "당신은 친절한 AI 어시스턴트입니다."
    
    print("Testing Anthropic API streaming...")
    for chunk in client.stream_response(test_message, test_prompt):
        print(chunk, end='', flush=True)
    print("\n✅ Test completed")