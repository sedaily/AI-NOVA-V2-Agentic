"""
WebSocket Service
WebSocket 메시지 처리 및 Bedrock 통합 서비스
영구 프롬프트 인메모리 캐싱 지원 (Lambda 컨테이너 수명 동안 유지)
"""
import json
import boto3
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Generator, Tuple
import uuid
import os
import sys
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config.aws import AWS_REGION, DYNAMODB_TABLES

from handlers.websocket.conversation_manager import ConversationManager
from lib.bedrock_client_enhanced import BedrockClientEnhanced
from lib.anthropic_client import AnthropicClient
from lib.web_search_client import search as web_search, format_context as format_web_context
from utils.logger import setup_logger

logger = setup_logger(__name__)

# DynamoDB 클라이언트 - 프롬프트 테이블 접근용
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
prompts_table = dynamodb.Table(DYNAMODB_TABLES['prompts'])

# 글로벌 프롬프트 캐시 - Lambda 컨테이너 재사용 시 유지됨 (영구 캐시)
PROMPT_CACHE: Dict[str, Dict[str, Any]] = {}
# TTL 제거 - Lambda 컨테이너가 살아있는 동안 영구적으로 캐시 유지


class WebSocketService:
    """WebSocket 메시지 처리 서비스"""

    def __init__(self):
        # AI 클라이언트 초기화 (환경변수에 따라 선택)
        use_anthropic = os.environ.get('USE_ANTHROPIC_API', 'false').lower() == 'true'
        if use_anthropic:
            self.ai_client = AnthropicClient()
            self.ai_provider = 'anthropic'
            logger.info("Using Anthropic API (Claude 4.5 Opus)")
        else:
            self.ai_client = BedrockClientEnhanced()
            self.ai_provider = 'bedrock'
            logger.info("Using AWS Bedrock (Claude 3.5 Sonnet)")
        
        # Bedrock 클라이언트도 폴백용으로 유지
        self.bedrock_client = BedrockClientEnhanced()
        self.conversation_manager = ConversationManager()
        self.prompts_table = prompts_table
        logger.info("WebSocketService initialized")

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
                ## 대화기억기능
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
        DynamoDB에서 프롬프트와 파일 로드 (영구 인메모리 캐싱 적용)

        캐시 히트 시 DynamoDB 조회를 완전히 생략하여 응답 속도 향상
        Lambda 컨테이너 수명 동안 영구 유지
        """
        global PROMPT_CACHE

        # 캐시 확인 (영구 캐시)
        if engine_type in PROMPT_CACHE:
            logger.info(f"✅ Cache HIT for {engine_type} - DB query skipped (permanent cache)")
            return PROMPT_CACHE[engine_type]

        logger.info(f"❌ Cache MISS for {engine_type} - fetching from DB")

        # 캐시 미스 - DB에서 로드
        prompt_data = self._fetch_prompt_from_db(engine_type)

        # 영구 캐시 업데이트 (TTL 없음)
        PROMPT_CACHE[engine_type] = prompt_data
        logger.info(f"💾 Permanently cached prompt for {engine_type} "
                   f"({len(prompt_data.get('files', []))} files, "
                   f"{len(str(prompt_data))} bytes)")

        return prompt_data

    def _fetch_prompt_from_db(self, engine_type: str) -> Dict[str, Any]:
        """
        실제 DB 조회 로직 (캐싱 전용)
        캐시 미스 시에만 호출됨
        """
        try:
            start_time = time.time()

            # 프롬프트 테이블에서 기본 정보 로드
            response = self.prompts_table.get_item(Key={'promptId': engine_type})
            if 'Item' in response:
                item = response['Item']
                prompt_data = {
                    'instruction': item.get('instruction', ''),
                    'description': item.get('description', ''),
                    'files': []
                }

                # files 테이블에서 관련 파일들 로드
                try:
                    files_table = dynamodb.Table(DYNAMODB_TABLES['files'])
                    files_response = files_table.scan(
                        FilterExpression='promptId = :promptId',
                        ExpressionAttributeValues={':promptId': engine_type}
                    )

                    if 'Items' in files_response:
                        for file_item in files_response['Items']:
                            prompt_data['files'].append({
                                'fileName': file_item.get('fileName', ''),
                                'fileContent': file_item.get('fileContent', ''),
                                'fileType': 'text'  # 기본값
                            })
                except Exception as fe:
                    logger.error(f"Error loading files: {str(fe)}")

                elapsed = (time.time() - start_time) * 1000
                logger.info(f"🔍 DB fetch for {engine_type}: "
                          f"{len(prompt_data['files'])} files in {elapsed:.0f}ms")

                return prompt_data
            else:
                logger.warning(f"No prompt found for engine type: {engine_type}")
                return {'instruction': '', 'description': '', 'files': []}

        except Exception as e:
            logger.error(f"Error fetching from DB: {str(e)}")
            return {'instruction': '', 'description': '', 'files': []}

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
        Bedrock 스트리밍 응답 생성

        Yields:
            str or dict: 응답 청크 또는 웹검색 결과
        """
        logger.info(f"🎯 Using model: {model_id}")
        try:
            # 웹검색 수행 (클라이언트에서 활성화한 경우)
            web_context = ""
            if web_search_enabled:
                logger.info(f"🌐 Web search enabled for message: {user_message[:50]}...")
                try:
                    search_result = web_search(user_message, max_results=5, days=3)
                    if search_result.get('success') and search_result.get('results'):
                        # 웹검색 결과를 클라이언트에 먼저 전송
                        yield {
                            'type': 'web_search_results',
                            'query': user_message,
                            'sources': search_result.get('results', [])
                        }
                        # LLM 컨텍스트용 포맷팅
                        web_context = format_web_context(search_result)
                        logger.info(f"🌐 Web search found {len(search_result.get('results', []))} results")
                    else:
                        logger.info("🌐 Web search returned no results")
                except Exception as ws_error:
                    logger.error(f"🌐 Web search failed: {str(ws_error)}")

            # 대화 컨텍스트를 포함한 프롬프트 생성
            formatted_history = self._format_conversation_for_bedrock(conversation_history)

            # DynamoDB에서 프롬프트 로드
            prompt_data = self._load_prompt_from_dynamodb(engine_type)
            logger.info(f"Loaded prompt for {engine_type}: instruction={len(prompt_data.get('instruction', ''))} chars")

            logger.info(f"Streaming response for engine {engine_type}")
            logger.info(f"Conversation context: {len(formatted_history)} messages")

            # AI 스트리밍 호출 (Anthropic 또는 Bedrock)
            total_response = ""
            
            # Anthropic API 사용 시
            if self.ai_provider == 'anthropic' and hasattr(self.ai_client, 'stream_response_with_history'):
                try:
                    logger.info(f"Using Anthropic API with conversation caching for {engine_type}")

                    # 체계적인 시스템 프롬프트 생성 (Bedrock과 동일한 구조 사용)
                    from lib.bedrock_client_enhanced import create_enhanced_system_prompt

                    prompt_data_for_system = {
                        'prompt': {
                            'instruction': prompt_data.get('instruction', ''),
                            'description': prompt_data.get('description', '')
                        },
                        'files': prompt_data.get('files', []),
                        'userRole': user_role
                    }

                    full_system_prompt = create_enhanced_system_prompt(
                        prompt_data_for_system,
                        engine_type,
                        use_enhanced=True,
                        flexibility_level="strict"
                    )

                    # 대화 히스토리를 캐싱용 메시지 리스트로 준비
                    messages_for_caching = self._prepare_messages_for_caching(
                        conversation_history=conversation_history,
                        current_message=user_message
                    )

                    for chunk in self.ai_client.stream_response_with_history(
                        messages=messages_for_caching,
                        system_prompt=full_system_prompt,
                        enable_caching=True,
                        enable_web_search=True,
                        model_id=model_id
                    ):
                        total_response += chunk
                        yield chunk
                        
                except Exception as e:
                    # Anthropic API 실패 시 Bedrock으로 폴백
                    if os.environ.get('FALLBACK_TO_BEDROCK', 'true').lower() == 'true':
                        logger.warning(f"Anthropic API failed, falling back to Bedrock: {str(e)}")
                        total_response = ""

                        # 폴백 시에도 웹검색 결과 처리
                        fallback_context = formatted_history
                        fallback_instruction = prompt_data.get('instruction', '')

                        if web_context:
                            fallback_context = web_context + "\n\n" + formatted_history
                            web_search_instruction = """

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[웹검색 모드 활성화]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
사용자가 웹검색 기능을 활성화했습니다. 다음 지침을 따르세요:

1. [WEB_SEARCH_RESULT] 태그 안의 실시간 웹검색 결과를 반드시 활용하세요
2. 검색 결과를 바탕으로 사용자의 질문에 직접 답변하세요
3. 뉴스나 정보 검색 요청에도 검색 결과를 활용하여 응답하세요
4. 출처를 [제목](URL) 형식의 마크다운 링크로 표시하세요

이 모드에서는 보도자료 작성 + 뉴스 정보 검색 모두 지원합니다.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
                            fallback_instruction = web_search_instruction + fallback_instruction

                        for chunk in self.bedrock_client.stream_bedrock(
                            user_message=user_message,
                            engine_type=engine_type,
                            conversation_context=fallback_context,
                            user_role=user_role,
                            guidelines=fallback_instruction,
                            description=prompt_data.get('description'),
                            files=prompt_data.get('files', []),
                            web_context="",  # 이미 fallback_context에 포함
                            model_id=model_id  # 모델 ID 전달
                        ):
                            total_response += chunk
                            yield chunk
                    else:
                        raise

            # Bedrock 사용 시 (기존 로직)
            else:
                # 웹검색 결과가 있으면 대화 컨텍스트와 지시문에 추가
                enhanced_context = formatted_history
                enhanced_instruction = prompt_data.get('instruction', '')

                if web_context:
                    enhanced_context = web_context + "\n\n" + formatted_history
                    logger.info("📎 Web search context added to conversation")

                    # 웹검색 활성화 시 추가 지시문
                    web_search_instruction = """

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[웹검색 모드 활성화]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
사용자가 웹검색 기능을 활성화했습니다. 다음 지침을 따르세요:

1. [WEB_SEARCH_RESULT] 태그 안의 실시간 웹검색 결과를 반드시 활용하세요
2. 검색 결과를 바탕으로 사용자의 질문에 직접 답변하세요
3. 뉴스나 정보 검색 요청에도 검색 결과를 활용하여 응답하세요
4. 출처를 [제목](URL) 형식의 마크다운 링크로 표시하세요
5. 보도자료 작성 요청이 아니더라도, 검색 결과를 활용한 정보 제공이 가능합니다

예시 응답:
"오늘 주요 뉴스입니다:
1. [삼성전자 실적 발표](https://news.example.com/1) - 4분기 실적이...
2. [코스피 상승 마감](https://news.example.com/2) - 오늘 코스피가..."

이 모드에서는 보도자료 작성 + 뉴스 정보 검색 모두 지원합니다.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
                    enhanced_instruction = web_search_instruction + enhanced_instruction

                for chunk in self.bedrock_client.stream_bedrock(
                    user_message=user_message,
                    engine_type=engine_type,
                    conversation_context=enhanced_context,  # 대화 컨텍스트 + 웹검색 결과
                    user_role=user_role,
                    guidelines=enhanced_instruction,  # 웹검색 지시문 포함된 instruction
                    description=prompt_data.get('description'),  # DynamoDB description 전달
                    files=prompt_data.get('files', []),  # DynamoDB files 전달
                    web_context="",  # 이미 enhanced_context에 포함됨
                    model_id=model_id  # 모델 ID 전달
                ):
                    total_response += chunk
                    yield chunk

            # AI 응답을 대화에 저장
            if total_response:
                self.conversation_manager.save_message(
                    conversation_id=conversation_id,
                    role='assistant',
                    content=total_response,
                    engine_type=engine_type,
                    user_id=user_id
                )
                logger.info(f"AI response saved: {len(total_response)} chars")

        except Exception as e:
            logger.error(f"Error streaming response: {str(e)}")
            raise

    def clear_history(self, conversation_id: str) -> bool:
        """대화 히스토리 초기화"""
        try:
            # 새로운 대화로 재생성
            self.conversation_manager.create_or_update_conversation(
                conversation_id=conversation_id,
                title="Cleared conversation"
            )
            logger.info(f"Cleared history for conversation {conversation_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing history: {str(e)}")
            return False
    
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
        """사용량 추적 (월별 + 일별) + 크레딧 차감"""
        try:
            from handlers.api.usage import deduct_credits, get_user_credits

            # 1. 토큰 수 결정 (API에서 받거나 추정)
            if input_tokens is None or output_tokens is None:
                # Anthropic API에서 실제 토큰 수 가져오기 시도
                if hasattr(self, 'ai_client') and hasattr(self.ai_client, 'get_last_usage'):
                    last_usage = self.ai_client.get_last_usage()
                    if last_usage:
                        input_tokens = last_usage.get('input_tokens', 0)
                        output_tokens = last_usage.get('output_tokens', 0)
                        logger.info(f"📊 실제 토큰 사용량: 입력={input_tokens}, 출력={output_tokens}")

                # 실제 토큰 수를 못 가져온 경우 추정
                if input_tokens is None:
                    input_tokens = len(input_text.split()) * 2
                if output_tokens is None:
                    output_tokens = len(output_text.split()) * 2

            logger.info(f"Usage tracked - User: {user_id}, Engine: {engine_type}")
            logger.info(f"Tokens - Input: {input_tokens}, Output: {output_tokens}")

            # 2. DynamoDB에 사용량 저장 (월별)
            usage_table = dynamodb.Table(os.environ.get('USAGE_TABLE', 'w1-usage'))
            year_month = datetime.now().strftime('%Y-%m')
            period = f"{year_month}#{engine_type}"

            from decimal import Decimal
            usage_table.update_item(
                Key={
                    'userId': user_id,
                    'period': period
                },
                UpdateExpression="""
                    ADD totalTokens :total,
                        inputTokens :input,
                        outputTokens :output,
                        messageCount :one
                    SET updatedAt = :timestamp,
                        lastUsedAt = :timestamp,
                        engineType = if_not_exists(engineType, :engineType),
                        yearMonth = if_not_exists(yearMonth, :yearMonth)
                """,
                ExpressionAttributeValues={
                    ':total': Decimal(str(input_tokens + output_tokens)),
                    ':input': Decimal(str(input_tokens)),
                    ':output': Decimal(str(output_tokens)),
                    ':one': Decimal('1'),
                    ':timestamp': datetime.now().isoformat(),
                    ':engineType': engine_type,
                    ':yearMonth': year_month
                }
            )
            logger.info(f"Usage saved to DynamoDB - Table: {usage_table.name}, userId: {user_id}, period: {period}")

            # 3. 크레딧 잔액에서 차감 (통합 크레딧 시스템)
            # 모델별 크레딧 요율 (NC per 1K tokens)
            CREDIT_RATES = {
                'opus-4-20250514': {'input': 7.5, 'output': 37.5},
                'claude-opus-4-5-20251101': {'input': 7.5, 'output': 37.5},
                'claude-sonnet-4-5-20250929': {'input': 4.5, 'output': 22.5},
                'default': {'input': 4.5, 'output': 22.5}
            }

            rates = CREDIT_RATES.get(model_id, CREDIT_RATES['default'])
            credits_used = round((input_tokens / 1000) * rates['input'] + (output_tokens / 1000) * rates['output'], 2)

            balance_info = deduct_credits(
                user_id=user_id,
                amount=credits_used,
                model_id=model_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )

            # 잔액 정보 가져오기 (차감 실패 시에도 현재 잔액 조회)
            current_balance = 0
            total_used = 0
            if balance_info:
                current_balance = balance_info.get('balance', 0)
                total_used = balance_info.get('totalUsed', 0)
            else:
                # 차감 실패 시 현재 잔액만 조회
                credit_status = get_user_credits(user_id)
                if credit_status:
                    current_balance = credit_status.get('balance', 0)
                    total_used = credit_status.get('totalUsed', 0)

            logger.info(f"💳 크레딧 차감: {credits_used} NC, 잔액: {current_balance} NC")

            return {
                'credits_used': credits_used,
                'balance': current_balance,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_used': total_used
            }

        except Exception as e:
            logger.error(f"Error tracking usage: {str(e)}", exc_info=True)
            return None

    def _merge_conversation_history(
        self,
        client_history: List[Dict],
        db_history: List[Dict]
    ) -> List[Dict]:
        """
        클라이언트와 DB의 대화 히스토리 병합

        DB 히스토리를 기준으로 하되, 클라이언트 히스토리에만 있는 메시지는 추가
        """
        merged = []

        # DB 히스토리를 기본으로 사용
        for msg in db_history:
            merged.append({
                'role': msg.get('role', msg.get('type', 'user')),
                'content': msg.get('content', ''),
                'timestamp': msg.get('timestamp', '')
            })

        # 클라이언트 히스토리에만 있는 메시지 확인 및 추가
        db_timestamps = {msg.get('timestamp') for msg in db_history if msg.get('timestamp')}

        for msg in client_history:
            timestamp = msg.get('timestamp')
            # 타임스탬프가 없거나 DB에 없는 메시지는 새로운 메시지로 간주
            if not timestamp or timestamp not in db_timestamps:
                # 중복 방지를 위해 최근 메시지와 비교
                content = msg.get('content', '')
                if not merged or merged[-1].get('content') != content:
                    merged.append({
                        'role': msg.get('role', 'user'),
                        'content': content,
                        'timestamp': timestamp or datetime.utcnow().isoformat() + 'Z'
                    })

        # 최대 30개 메시지만 유지 (컨텍스트 길이 관리) #대화기억기능
        if len(merged) > 30:
            merged = merged[-30:]

        return merged

    def _prepare_messages_for_caching(
        self,
        conversation_history: List[Dict],
        current_message: str
    ) -> List[Dict]:
        """대화 히스토리를 Anthropic 캐싱용 메시지 리스트로 준비"""
        messages = []
        recent_history = conversation_history[-10:] if conversation_history else []

        for msg in recent_history:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role in ['user', 'assistant'] and content:
                messages.append({'role': role, 'content': content})

        messages = self._validate_message_alternation(messages)
        messages.append({'role': 'user', 'content': current_message})

        logger.info(f"📚 Prepared {len(messages)} messages for caching")
        return messages

    def _validate_message_alternation(self, messages: List[Dict]) -> List[Dict]:
        """user/assistant 메시지 교대 검증"""
        if not messages:
            return messages

        validated = []
        for i, msg in enumerate(messages):
            if i > 0 and validated[-1]['role'] == msg['role']:
                placeholder_role = 'assistant' if msg['role'] == 'user' else 'user'
                validated.append({'role': placeholder_role, 'content': '(계속)'})
            validated.append(msg)
        return validated

    def _format_conversation_for_bedrock(self, conversation_history: List[Dict]) -> str:
        """
        Bedrock에 전달할 대화 컨텍스트 포맷팅
        """
        if not conversation_history:
            return ""

        formatted_messages = []
        for msg in conversation_history[-10:]:  # 최근 10개 메시지만 사용 #대화기억기능
            role = msg.get('role', 'user')
            content = msg.get('content', '')

            if content:
                if role == 'user':
                    formatted_messages.append(f"사용자: {content}")
                elif role == 'assistant':
                    formatted_messages.append(f"AI: {content}")

        if formatted_messages:
            return "\n\n=== 이전 대화 내용 ===\n" + "\n\n".join(formatted_messages) + "\n\n=== 현재 질문 ==="

        return ""