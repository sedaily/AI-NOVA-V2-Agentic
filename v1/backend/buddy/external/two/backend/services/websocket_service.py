"""
WebSocket Service with Dual AI Provider Support
Bedrock + Anthropic API 병행 지원 버전
"""
import json
import boto3
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Generator
import uuid
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config.aws import AWS_REGION, DYNAMODB_TABLES

from handlers.websocket.conversation_manager import ConversationManager
from lib import web_search_client
from utils.logger import setup_logger

logger = setup_logger(__name__)

# 글로벌 캐시 - Lambda 컨테이너 재사용 시 유지됨 (영구 캐시)
PROMPT_CACHE: Dict[str, Dict[str, Any]] = {}

# DynamoDB 클라이언트 - 프롬프트 테이블 접근용
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

# f1 서비스용 테이블 설정
PROMPTS_TABLE_NAME = os.environ.get('PROMPTS_TABLE', 'p2-two-prompts-two')
FILES_TABLE_NAME = os.environ.get('FILES_TABLE', 'p2-two-files-two')

prompts_table = dynamodb.Table(PROMPTS_TABLE_NAME)
files_table = dynamodb.Table(FILES_TABLE_NAME)

logger.info(f"Using prompts table: {PROMPTS_TABLE_NAME}")
logger.info(f"Using files table: {FILES_TABLE_NAME}")


def get_ai_client(user_id: str = None, engine_type: str = None):
    """
    환경변수와 사용자 정보에 따라 적절한 AI 클라이언트 반환
    
    우선순위:
    1. 환경변수 AI_PROVIDER
    2. 환경변수 USE_ANTHROPIC_API
    3. 사용자별 설정 (프리미엄 사용자 등)
    4. 기본값: Bedrock
    """
    try:
        # 1. 명시적 프로바이더 설정
        ai_provider = os.environ.get('AI_PROVIDER', '').lower()
        
        if ai_provider == 'anthropic_api' or ai_provider == 'anthropic':
            logger.info("🎯 AI Provider: Anthropic API (via AI_PROVIDER env)")
            from lib.anthropic_client import AnthropicClient
            return AnthropicClient()
        elif ai_provider == 'bedrock':
            logger.info("🎯 AI Provider: AWS Bedrock (via AI_PROVIDER env)")
            from lib.bedrock_client_enhanced import BedrockClientEnhanced
            return BedrockClientEnhanced()
        
        # 2. USE_ANTHROPIC_API 환경변수 확인
        use_anthropic = os.environ.get('USE_ANTHROPIC_API', 'false').lower() == 'true'
        
        if use_anthropic:
            logger.info("🎯 AI Provider: Anthropic API (via USE_ANTHROPIC_API env)")
            from lib.anthropic_client import AnthropicClient
            return AnthropicClient()
        
        # 3. 사용자별 설정 (예: 프리미엄 사용자)
        if user_id and engine_type:
            # 특정 엔진 타입에 대해 Anthropic 사용
            premium_engines = os.environ.get('ANTHROPIC_ENGINES', '').split(',')
            if engine_type in premium_engines:
                logger.info(f"🎯 AI Provider: Anthropic API (engine {engine_type} in premium list)")
                from lib.anthropic_client import AnthropicClient
                return AnthropicClient()
            
            # sedaily.com 도메인 사용자는 Anthropic API 사용 (옵션)
            if '@sedaily.com' in str(user_id) and os.environ.get('ANTHROPIC_FOR_INTERNAL', 'false').lower() == 'true':
                logger.info(f"🎯 AI Provider: Anthropic API (internal user: {user_id})")
                from lib.anthropic_client import AnthropicClient
                return AnthropicClient()
        
        # 4. 기본값: Bedrock
        logger.info("🎯 AI Provider: AWS Bedrock (default)")
        from lib.bedrock_client_enhanced import BedrockClientEnhanced
        return BedrockClientEnhanced()
        
    except ImportError as e:
        logger.error(f"Failed to import AI client: {str(e)}")
        logger.warning("⚠️ Falling back to Bedrock due to import error")
        from lib.bedrock_client_enhanced import BedrockClientEnhanced
        return BedrockClientEnhanced()
    except Exception as e:
        logger.error(f"Error selecting AI client: {str(e)}")
        logger.warning("⚠️ Falling back to Bedrock due to error")
        from lib.bedrock_client_enhanced import BedrockClientEnhanced
        return BedrockClientEnhanced()


class WebSocketService:
    """WebSocket 메시지 처리 서비스 - Dual AI Provider Support"""

    def __init__(self):
        self.conversation_manager = ConversationManager()
        self.prompts_table = prompts_table
        self.files_table = files_table
        # AI 클라이언트는 동적으로 선택됨
        self.ai_client = None
        logger.info("WebSocketService initialized with dual AI provider support + Tavily web search")

    def _get_or_create_ai_client(self, user_id: str = None, engine_type: str = None):
        """AI 클라이언트를 가져오거나 생성"""
        if not self.ai_client:
            self.ai_client = get_ai_client(user_id, engine_type)
        return self.ai_client

    def process_message(
        self,
        user_message: str,
        engine_type: str,
        conversation_id: Optional[str],
        user_id: str,
        conversation_history: List[Dict],
        user_role: str = 'user'
    ) -> Dict[str, Any]:
        """
        메시지 처리 및 대화 히스토리 병합

        Returns:
            Dict containing conversation_id and merged_history
        """
        try:
            # 대화 ID가 없으면 생성
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
                logger.info(f"New conversation created: {conversation_id}")

            # DB에서 기존 대화 히스토리 조회
            db_history = self.conversation_manager.get_conversation_history(
                conversation_id,
                limit=20  # 최근 20개 메시지
            )

            # 클라이언트 히스토리와 DB 히스토리 병합
            merged_history = self._merge_conversation_history(
                client_history=conversation_history,
                db_history=db_history
            )

            # 사용자 메시지를 대화에 저장
            self.conversation_manager.save_message(
                conversation_id=conversation_id,
                role='user',
                content=user_message,
                engine_type=engine_type,
                user_id=user_id
            )

            # 병합된 히스토리에 현재 메시지 추가
            merged_history.append({
                'role': 'user',
                'content': user_message,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })

            logger.info(f"Processed message for conversation {conversation_id}")
            logger.info(f"Merged history length: {len(merged_history)}")

            return {
                'conversation_id': conversation_id,
                'merged_history': merged_history
            }

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            raise

    def _load_prompt_from_dynamodb(self, engine_type: str) -> Dict[str, Any]:
        """
        DynamoDB에서 프롬프트와 파일 로드 (영구 인메모리 캐싱)
        """
        global PROMPT_CACHE

        # 캐시 확인
        if engine_type in PROMPT_CACHE:
            logger.info(f"✅ Cache HIT for {engine_type} - DB query skipped")
            return PROMPT_CACHE[engine_type]

        logger.info(f"❌ Cache MISS for {engine_type} - fetching from DB")

        # 캐시 미스 - DB에서 로드
        prompt_data = self._fetch_prompt_from_db(engine_type)

        # 캐시 업데이트 (영구 저장)
        PROMPT_CACHE[engine_type] = prompt_data
        logger.info(f"💾 Permanently cached prompt for {engine_type}")

        return prompt_data

    def _fetch_prompt_from_db(self, engine_type: str) -> Dict[str, Any]:
        """실제 DB 조회 로직"""
        try:
            start_time = time.time()

            # 프롬프트 테이블에서 기본 정보 로드
            response = self.prompts_table.get_item(
                Key={
                    'engineType': engine_type,
                    'promptId': engine_type
                }
            )
            if 'Item' in response:
                item = response['Item']
                prompt_data = {
                    'instruction': item.get('instruction', ''),
                    'description': item.get('description', ''),
                    'files': []
                }

                # files 테이블에서 관련 파일들 로드
                try:
                    files_response = self.files_table.scan()

                    if 'Items' in files_response:
                        for file_item in files_response['Items']:
                            prompt_data['files'].append({
                                'fileName': file_item.get('fileName', ''),
                                'fileContent': file_item.get('fileContent', ''),
                                'fileType': 'text'
                            })
                except Exception as fe:
                    logger.error(f"Error loading files: {str(fe)}")

                elapsed = (time.time() - start_time) * 1000
                logger.info(f"🔍 DB fetch for {engine_type} in {elapsed:.0f}ms (will be cached permanently)")

                return prompt_data
            else:
                logger.warning(f"No prompt found for engine type: {engine_type}")
                return {'instruction': '', 'description': '', 'files': []}
        except Exception as e:
            logger.error(f"Error loading prompt from DynamoDB: {str(e)}")
            return {'instruction': '', 'description': '', 'files': []}

    def _prepare_messages_for_caching(self, conversation_history: List[Dict], current_message: str) -> List[Dict]:
        """
        대화 히스토리를 Anthropic 캐싱용 메시지 형식으로 변환
        """
        messages = []

        # 최근 10개 메시지만 사용
        recent_history = conversation_history[-10:] if conversation_history else []

        for msg in recent_history:
            role = msg.get('role', 'user')
            content = msg.get('content', '')

            if role in ['user', 'assistant'] and content:
                messages.append({
                    'role': role,
                    'content': content
                })

        # 메시지 교대 검증
        messages = self._validate_message_alternation(messages)

        # 현재 사용자 메시지 추가
        messages.append({
            'role': 'user',
            'content': current_message
        })

        return messages

    def _validate_message_alternation(self, messages: List[Dict]) -> List[Dict]:
        """
        Anthropic API 요구사항: user/assistant 메시지가 교대로 나와야 함
        """
        if not messages:
            return messages

        validated = []
        for i, msg in enumerate(messages):
            if i > 0 and validated[-1]['role'] == msg['role']:
                # 같은 역할이 연속되면 placeholder 삽입
                placeholder_role = 'assistant' if msg['role'] == 'user' else 'user'
                validated.append({
                    'role': placeholder_role,
                    'content': '(계속)'
                })
            validated.append(msg)

        return validated

    def stream_response(
        self,
        user_message: str,
        engine_type: str,
        conversation_id: str,
        user_id: str,
        conversation_history: List[Dict],
        user_role: str = 'user',
        model_id: str = 'opus-4-20250514',
        web_search_enabled: bool = False
    ) -> Generator[str, None, None]:
        """
        AI 스트리밍 응답 생성 (Bedrock/Anthropic 자동 선택)
        Anthropic API 사용 시 대화 히스토리 캐싱 적용

        Yields:
            str: 응답 청크
        """
        try:
            logger.info(f"Using model: {model_id}, web_search_enabled: {web_search_enabled}")

            # AI 클라이언트 선택
            ai_client = self._get_or_create_ai_client(user_id, engine_type)

            # DynamoDB에서 프롬프트 로드
            prompt_data = self._load_prompt_from_dynamodb(engine_type)

            logger.info(f"=== Prompt Data Loaded for {engine_type} ===")
            logger.info(f"AI Client: {ai_client.__class__.__name__}")

            # 🌐 Tavily 웹검색 수행 (클라이언트 요청 시)
            web_context = ""
            web_search_results = None  # 프론트엔드에 전송할 검색 결과
            if web_search_enabled:
                logger.info(f"🔍 Tavily Web search ENABLED for: {user_message[:50]}...")
                try:
                    # 검색 실행 (raw results)
                    search_result = web_search_client.search(user_message, max_results=5)
                    if search_result.get('success') and search_result.get('results'):
                        # 프론트엔드에 전송할 검색 결과 저장
                        web_search_results = {
                            'query': user_message,
                            'sources': search_result.get('results', [])
                        }
                        # LLM용 컨텍스트 포맷팅
                        web_context = web_search_client.format_context(search_result)
                        logger.info(f"✅ Tavily web search completed: {len(search_result.get('results', []))} results, context: {len(web_context)} chars")

                        # 웹검색 결과를 먼저 yield (프론트엔드에서 처리)
                        yield {
                            'type': 'web_search_results',
                            'query': user_message,
                            'sources': search_result.get('results', [])
                        }
                    else:
                        logger.warning("⚠️ Tavily web search returned empty results")
                except Exception as e:
                    logger.error(f"❌ Tavily web search failed: {str(e)}")
                    web_context = ""
                    web_search_results = None

            total_response = ""
            retry_with_bedrock = False

            # Anthropic API 사용 여부 확인
            is_anthropic = ai_client.__class__.__name__ == 'AnthropicClient'

            # 웹검색 지시문 (web_context가 있을 때)
            web_search_instruction = ""
            if web_context:
                web_search_instruction = """

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[웹검색 모드 활성화]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
사용자가 웹검색 기능을 활성화했습니다. 다음 지침을 따르세요:

1. [WEB_SEARCH_RESULT] 태그 안의 실시간 웹검색 결과를 반드시 활용하세요
2. 검색 결과를 바탕으로 사용자의 질문에 직접 답변하세요
3. 뉴스나 정보 검색 요청에도 검색 결과를 활용하여 응답하세요
4. 출처를 [제목](URL) 형식의 마크다운 링크로 표시하세요
5. 외신기사 작성 요청이 아니더라도, 검색 결과를 활용한 정보 제공이 가능합니다

예시 응답:
"오늘 주요 뉴스입니다:
1. [삼성전자 실적 발표](https://news.example.com/1) - 4분기 실적이...
2. [코스피 상승 마감](https://news.example.com/2) - 오늘 코스피가..."

이 모드에서는 외신기사 작성 + 뉴스 정보 검색 모두 지원합니다.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

            try:
                if is_anthropic and hasattr(ai_client, 'stream_response_with_history'):
                    # Anthropic API: 대화 히스토리 캐싱 사용
                    logger.info("🚀 Using Anthropic API with conversation history caching")

                    # 시스템 프롬프트 구성 (웹검색 지시문 포함)
                    system_prompt = self._build_system_prompt(prompt_data, user_role)
                    if web_context:
                        system_prompt = web_search_instruction + system_prompt

                    # 대화 히스토리 준비 (웹검색 결과 포함)
                    enhanced_message = web_context + "\n\n" + user_message if web_context else user_message
                    messages = self._prepare_messages_for_caching(conversation_history, enhanced_message)

                    logger.info(f"📝 Prepared {len(messages)} messages for caching")

                    # Tavily로 이미 검색했으면 Native 웹서치 비활성화
                    use_native_web_search = False
                    if not web_context:
                        use_native_web_search = os.environ.get('ENABLE_NATIVE_WEB_SEARCH', 'false').lower() == 'true'

                    if use_native_web_search:
                        logger.info("🔍 Anthropic Native Web Search ENABLED")

                    for chunk in ai_client.stream_response_with_history(
                        messages=messages,
                        system_prompt=system_prompt,
                        enable_caching=True,
                        enable_web_search=use_native_web_search,
                        model_id=model_id
                    ):
                        total_response += chunk
                        yield chunk
                else:
                    # Bedrock 또는 캐싱 미지원: 기존 방식 사용
                    logger.info("📋 Using standard stream_bedrock (no history caching)")
                    formatted_history = self._format_conversation_for_bedrock(conversation_history)

                    # 웹검색 결과가 있으면 대화 컨텍스트와 지시문에 추가
                    enhanced_context = formatted_history
                    enhanced_instruction = prompt_data.get('instruction', '')

                    if web_context:
                        enhanced_context = web_context + "\n\n" + formatted_history
                        enhanced_instruction = web_search_instruction + enhanced_instruction
                        logger.info("📎 Web search context added to conversation")

                    for chunk in ai_client.stream_bedrock(
                        user_message=user_message,
                        engine_type=engine_type,
                        conversation_context=enhanced_context,
                        user_role=user_role,
                        guidelines=enhanced_instruction,
                        description=prompt_data.get('description'),
                        files=prompt_data.get('files', []),
                        model_id=model_id
                    ):
                        total_response += chunk
                        yield chunk

            except Exception as e:
                # Anthropic API 오류 시 Bedrock 폴백
                if 'RateLimitError' in str(e.__class__.__name__) or 'anthropic' in str(e).lower():
                    if os.environ.get('FALLBACK_TO_BEDROCK', 'true').lower() == 'true':
                        logger.warning(f"⚠️ Anthropic API error, falling back to Bedrock: {str(e)}")
                        retry_with_bedrock = True
                    else:
                        raise
                else:
                    raise

            # Bedrock 폴백 처리
            if retry_with_bedrock:
                logger.info("🔄 Retrying with Bedrock...")
                from lib.bedrock_client_enhanced import BedrockClientEnhanced
                bedrock_client = BedrockClientEnhanced()
                formatted_history = self._format_conversation_for_bedrock(conversation_history)

                # 웹검색 결과가 있으면 대화 컨텍스트와 지시문에 추가
                enhanced_context = formatted_history
                enhanced_instruction = prompt_data.get('instruction', '')

                if web_context:
                    enhanced_context = web_context + "\n\n" + formatted_history
                    enhanced_instruction = web_search_instruction + enhanced_instruction

                # 폴백 알림
                yield "\n\n[시스템: 프리미엄 모델 제한으로 표준 모델로 전환됩니다]\n\n"

                for chunk in bedrock_client.stream_bedrock(
                    user_message=user_message,
                    engine_type=engine_type,
                    conversation_context=enhanced_context,
                    user_role=user_role,
                    guidelines=enhanced_instruction,
                    description=prompt_data.get('description'),
                    files=prompt_data.get('files', [])
                ):
                    total_response += chunk
                    yield chunk

            # AI 응답 저장은 message.py에서 처리하므로 여기서는 제거
            # 중복 저장 방지를 위해 주석 처리
            logger.info(f"AI response completed: {len(total_response)} chars (저장은 message.py에서 처리)")

        except Exception as e:
            logger.error(f"Error streaming response: {str(e)}")
            raise

    def _build_system_prompt(self, prompt_data: Dict[str, Any], user_role: str) -> str:
        """시스템 프롬프트 구성"""
        parts = []

        # 기본 instruction
        if prompt_data.get('instruction'):
            parts.append(prompt_data['instruction'])

        # description
        if prompt_data.get('description'):
            parts.append(f"\n\n[서비스 설명]\n{prompt_data['description']}")

        # 첨부 파일
        files = prompt_data.get('files', [])
        if files:
            parts.append("\n\n[참조 파일]")
            for f in files:
                file_name = f.get('fileName', 'unknown')
                file_content = f.get('fileContent', '')
                if file_content:
                    parts.append(f"\n--- {file_name} ---\n{file_content}")

        return "\n".join(parts)

    def clear_history(self, conversation_id: str, user_id: str = None) -> bool:
        """대화 히스토리 초기화"""
        try:
            self.conversation_manager.create_or_update_conversation(
                conversation_id=conversation_id,
                title="Cleared conversation",
                user_id=user_id
            )
            logger.info(f"Cleared history for conversation {conversation_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing history: {str(e)}")
            return False

    def track_usage(
        self,
        user_id: str,
        engine_type: str,
        input_text: str,
        output_text: str,
        model_id: str = None,
        input_tokens: int = None,
        output_tokens: int = None
    ) -> dict:
        """사용량 추적 + 크레딧 차감"""
        try:
            from handlers.api.usage import deduct_credits, get_user_credits
            from decimal import Decimal

            # 실제 토큰 정보 가져오기 (Anthropic API 응답에서)
            if (input_tokens is None or output_tokens is None) and hasattr(self, 'ai_client') and hasattr(self.ai_client, 'get_last_usage'):
                try:
                    last_usage = self.ai_client.get_last_usage()
                    if last_usage:
                        if input_tokens is None:
                            input_tokens = last_usage.get('input_tokens', 0)
                        if output_tokens is None:
                            output_tokens = last_usage.get('output_tokens', 0)
                        logger.info(f"📊 Using actual API tokens: input={input_tokens}, output={output_tokens}")
                except Exception as e:
                    logger.warning(f"Could not get last usage: {e}")

            # 폴백: 추정
            if input_tokens is None or input_tokens == 0:
                input_tokens = int(len(input_text.split()) * 1.3)
            if output_tokens is None or output_tokens == 0:
                output_tokens = int(len(output_text.split()) * 1.3)

            total_tokens = input_tokens + output_tokens

            # 크레딧 계산
            if not model_id:
                model_id = 'opus-4-20250514'

            CREDIT_RATES = {
                'opus-4-20250514': {'input': 7.5, 'output': 37.5},
                'claude-opus-4-5-20251101': {'input': 7.5, 'output': 37.5},
                'claude-sonnet-4-5-20250929': {'input': 4.5, 'output': 22.5},
                'default': {'input': 4.5, 'output': 22.5}
            }
                'claude-opus-4-5-20251101': {'input': 7.5, 'output': 37.5},
                'claude-sonnet-4-5-20250929': {'input': 4.5, 'output': 22.5},
                'claude-haiku-4-5-20251001': {'input': 1.5, 'output': 7.5},
                'default': {'input': 4.5, 'output': 22.5}
            }
            rates = CREDIT_RATES.get(model_id, CREDIT_RATES['default'])
            credits_used = round((input_tokens / 1000) * rates['input'] + (output_tokens / 1000) * rates['output'], 2)

            # DynamoDB에 사용량 저장
            usage_table = dynamodb.Table(os.environ.get('USAGE_TABLE', 'p2-two-usage-two'))
            today = datetime.now().strftime('%Y-%m-%d')
            date_key = f"{today}#{engine_type}"

            usage_table.update_item(
                Key={
                    'userId': user_id,
                    'date': date_key
                },
                UpdateExpression="""
                    ADD totalTokens :total,
                        inputTokens :input,
                        outputTokens :output,
                        messageCount :one
                    SET updatedAt = :timestamp,
                        lastUsedAt = :timestamp,
                        engineType = if_not_exists(engineType, :engineType),
                        usageDate = if_not_exists(usageDate, :usageDate)
                """,
                ExpressionAttributeValues={
                    ':total': Decimal(str(total_tokens)),
                    ':input': Decimal(str(input_tokens)),
                    ':output': Decimal(str(output_tokens)),
                    ':one': Decimal('1'),
                    ':timestamp': datetime.utcnow().isoformat() + 'Z',
                    ':engineType': engine_type,
                    ':usageDate': today
                }
            )

            # 크레딧 차감
            balance_info = deduct_credits(
                user_id=user_id,
                amount=credits_used,
                model_id=model_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )

            current_balance = 0
            total_used = 0
            if balance_info:
                current_balance = balance_info.get('balance', 0)
                total_used = balance_info.get('totalUsed', 0)
            else:
                credit_status = get_user_credits(user_id)
                if credit_status:
                    current_balance = credit_status.get('balance', 0)
                    total_used = credit_status.get('totalUsed', 0)

            logger.info(f"💳 Usage tracked: {user_id}, {engine_type}, credits={credits_used:.2f} NC, balance={current_balance:.2f} NC")

            return {
                'credits_used': credits_used,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'balance': current_balance,
                'total_used': total_used
            }

        except Exception as e:
            logger.error(f"Error tracking usage: {str(e)}")
            return None

    def _merge_conversation_history(
        self,
        client_history: List[Dict],
        db_history: List[Dict]
    ) -> List[Dict]:
        """클라이언트와 DB 히스토리 병합"""
        merged = []
        seen_ids = set()

        # DB 히스토리 먼저 추가
        for msg in db_history:
            msg_id = msg.get('messageId', f"{msg.get('timestamp', '')}_{msg.get('role', '')}")
            if msg_id not in seen_ids:
                merged.append(msg)
                seen_ids.add(msg_id)

        # 클라이언트 히스토리 추가 (중복 제거)
        for msg in client_history:
            msg_id = f"{msg.get('timestamp', '')}_{msg.get('role', '')}"
            if msg_id not in seen_ids:
                merged.append(msg)
                seen_ids.add(msg_id)

        # 시간순 정렬
        merged.sort(key=lambda x: x.get('timestamp', ''))

        return merged[-20:]  # 최근 20개만 유지

    def _format_conversation_for_bedrock(self, conversation_history: List[Dict]) -> str:
        """대화 히스토리를 Bedrock 형식으로 포맷팅"""
        if not conversation_history:
            return ""

        formatted = []
        for msg in conversation_history[-10:]:  # 최근 10개 메시지만
            role = msg.get('role', 'user')
            content = msg.get('content', '')

            if role == 'user':
                formatted.append(f"사용자: {content}")
            elif role == 'assistant':
                formatted.append(f"AI: {content}")

        return "\n\n".join(formatted) if formatted else ""

    @staticmethod
    def clear_prompt_cache(engine_type: str = None):
        """
        프롬프트 캐시 초기화 (관리용)

        Args:
            engine_type: 특정 엔진 타입만 삭제. None이면 전체 삭제
        """
        global PROMPT_CACHE

        if engine_type:
            if engine_type in PROMPT_CACHE:
                del PROMPT_CACHE[engine_type]
                logger.info(f"🗑️ Cleared cache for {engine_type}")
            else:
                logger.info(f"No cache found for {engine_type}")
        else:
            cache_size = len(PROMPT_CACHE)
            PROMPT_CACHE.clear()
            logger.info(f"🗑️ Cleared all cache ({cache_size} entries)")

    @staticmethod
    def get_cache_stats() -> Dict[str, Any]:
        """캐시 통계 정보 반환"""
        global PROMPT_CACHE

        stats = {
            'total_entries': len(PROMPT_CACHE),
            'engines': list(PROMPT_CACHE.keys()),
            'cache_size_bytes': sum(len(str(data)) for data in PROMPT_CACHE.values()),
            'permanent_cache': True  # 영구 캐시 사용 중
        }

        return stats