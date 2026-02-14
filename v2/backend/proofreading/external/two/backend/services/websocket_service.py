"""
WebSocket 서비스 - 완성 버전 (Permanent Prompt Caching 적용)
우수사례 코드를 참고하여 프롬프트 로드 기능 추가
영구 인메모리 캐싱으로 DynamoDB 조회 최소화 (Lambda 컨테이너 수명 동안 유지)
"""
import os
import sys
import json
import boto3
import logging
import time
from typing import Dict, List, Generator, Optional, Any
from datetime import datetime, timezone
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config.aws import AWS_REGION, DYNAMODB_TABLES
from lib.bedrock_client_enhanced import BedrockClientEnhanced, create_enhanced_system_prompt
from lib.anthropic_client import AnthropicClient
from lib.web_search_client import search as web_search, format_context as format_web_context
from utils.logger import setup_logger

logger = setup_logger(__name__)

# 글로벌 캐시 - Lambda 컨테이너 재사용 시 영구 유지 (TTL 제거)
PROMPT_CACHE: Dict[str, Dict[str, Any]] = {}
# CACHE_TTL 제거 - 영구 캐시로 전환

class WebSocketService:
    """WebSocket 통신 서비스"""
    
    def __init__(self):
        # AWS 리소스 초기화
        self.dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
        self.conversations_table = self.dynamodb.Table(DYNAMODB_TABLES['conversations'])
        self.prompts_table = self.dynamodb.Table(DYNAMODB_TABLES['prompts'])
        self.usage_table = self.dynamodb.Table(DYNAMODB_TABLES['usage'])
        self.daily_usage_table = self.dynamodb.Table(DYNAMODB_TABLES['daily_usage'])  # 일별 사용량 추적
        self.files_table = self.dynamodb.Table(DYNAMODB_TABLES['files'])  # 파일 테이블 추가

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

        # 대화 관리자
        from handlers.websocket.conversation_manager import ConversationManager
        self.conversation_manager = ConversationManager()

        logger.info("WebSocketService initialized")
    
    def _load_prompt_from_dynamodb(self, engine_type: str) -> Dict[str, Any]:
        """
        DynamoDB에서 프롬프트와 파일 로드 (영구 인메모리 캐싱 적용)

        캐시 히트 시 DB 조회를 완전히 생략하여 최대 성능 향상
        Lambda 컨테이너가 재시작될 때까지 캐시 유지
        """
        global PROMPT_CACHE

        # 영구 캐시 확인 (TTL 없음)
        if engine_type in PROMPT_CACHE:
            logger.info(f"✅ Cache HIT for {engine_type} - DB query skipped (permanent cache)")
            return PROMPT_CACHE[engine_type]

        logger.info(f"❌ Cache MISS for {engine_type} - fetching from DB (first time)")

        # 캐시 미스 - DB에서 로드
        prompt_data = self._fetch_prompt_from_db(engine_type)

        # 영구 캐시 업데이트
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

            # 프롬프트 테이블에서 기본 정보 로드 (id 키 사용)
            response = self.prompts_table.get_item(Key={'id': engine_type})
            if 'Item' in response:
                item = response['Item']
                prompt_data = {
                    'instruction': item.get('instruction', ''),
                    'description': item.get('description', ''),
                    'files': []
                }

                # files 테이블에서 관련 파일들 로드
                try:
                    files_response = self.files_table.scan(
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
            logger.error(f"Error loading prompt from DynamoDB: {str(e)}")
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
    ) -> Generator[Any, None, None]:
        """
        Bedrock 스트리밍 응답 생성

        Yields:
            str or dict: 응답 청크 또는 웹검색 결과
        """
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

            # DynamoDB에서 프롬프트와 파일 통합 로드
            prompt_data = self._load_prompt_from_dynamodb(engine_type)
            logger.info(f"Loaded prompt for {engine_type}: instruction={len(prompt_data.get('instruction', ''))} chars")

            logger.info(f"Streaming response for engine {engine_type}")
            logger.info(f"Conversation context: {len(formatted_history)} messages")
            logger.info(f"Using model: {model_id}, web_search: {web_search_enabled}")

            # AI 스트리밍 호출 (Anthropic 또는 Bedrock)
            total_response = ""
            
            # Anthropic API 사용 시
            if self.ai_provider == 'anthropic' and hasattr(self.ai_client, 'stream_response_with_history'):
                try:
                    logger.info(f"Using Anthropic API with conversation caching for {engine_type}")

                    # 프롬프트와 대화 컨텍스트 결합 (Bedrock과 동일한 체계적 프롬프트)
                    full_system_prompt = self._build_system_prompt(
                        guidelines=prompt_data.get('instruction', ''),
                        description=prompt_data.get('description', ''),
                        files=prompt_data.get('files', []),
                        conversation_context=formatted_history,
                        engine_type=engine_type,
                        user_role=user_role,
                        web_context=web_context
                    )

                    # 웹 검색 활성화 여부 판단
                    enable_web_search = self._should_enable_web_search(user_message)

                    # 대화 히스토리를 캐싱용 메시지 리스트로 준비
                    messages_for_caching = self._prepare_messages_for_caching(
                        conversation_history=conversation_history,
                        current_message=user_message
                    )

                    for chunk in self.ai_client.stream_response_with_history(
                        messages=messages_for_caching,
                        system_prompt=full_system_prompt,
                        enable_caching=True,
                        enable_web_search=enable_web_search,
                        model_id=model_id
                    ):
                        total_response += chunk
                        yield chunk

                    # 사용량 정보 로깅 (비용 포함)
                    if hasattr(self.ai_client, 'get_last_usage'):
                        usage = self.ai_client.get_last_usage()
                        if usage:
                            logger.info(f"📊 API Usage: {usage}")
                            if 'total_cost' in usage:
                                logger.info(f"💵 Total cost for this request: ${usage['total_cost']:.6f}")
                        
                except Exception as e:
                    # Anthropic API 실패 시 Bedrock으로 폴백
                    if os.environ.get('FALLBACK_TO_BEDROCK', 'true').lower() == 'true':
                        logger.warning(f"Anthropic API failed, falling back to Bedrock: {str(e)}")
                        total_response = ""
                        for chunk in self.bedrock_client.stream_bedrock(
                            user_message=user_message,
                            engine_type=engine_type,
                            conversation_context=formatted_history,
                            user_role=user_role,
                            guidelines=prompt_data.get('instruction'),
                            description=prompt_data.get('description'),
                            files=prompt_data.get('files', []),
                            web_context=web_context  # 웹검색 컨텍스트 전달
                        ):
                            total_response += chunk
                            yield chunk
                    else:
                        raise
            
            # Bedrock 사용 시 (기존 로직)
            else:
                for chunk in self.bedrock_client.stream_bedrock(
                    user_message=user_message,
                    engine_type=engine_type,
                    conversation_context=formatted_history,  # 대화 컨텍스트 전달
                    user_role=user_role,
                    guidelines=prompt_data.get('instruction'),  # DynamoDB instruction 전달
                    description=prompt_data.get('description'),  # DynamoDB description 전달
                    files=prompt_data.get('files', []),  # DynamoDB files 전달
                    web_context=web_context  # 웹검색 컨텍스트 전달
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
            yield f"오류가 발생했습니다: {str(e)}"
    
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
                import uuid
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

    def process_conversation(
        self,
        user_message: str,
        conversation_id: str,
        user_id: str,
        conversation_history: List[Dict],
        user_role: str = 'user'
    ) -> Dict:
        """
        대화 처리 및 히스토리 병합

        Returns:
            Dict: conversation_id와 병합된 히스토리
        """
        try:
            # 대화 ID 생성 또는 검증
            if not conversation_id:
                # 새 대화 생성
                conversation_id = f"{user_id}_{datetime.now().timestamp()}"
                logger.info(f"Created new conversation: {conversation_id}")

            # DB에서 기존 대화 로드
            db_history = []
            if conversation_id:
                try:
                    response = self.conversations_table.get_item(
                        Key={
                            'userId': user_id,
                            'conversationId': conversation_id
                        }
                    )
                    if 'Item' in response:
                        db_history = response['Item'].get('messages', [])
                        logger.info(f"Loaded {len(db_history)} messages from DB")
                except Exception as e:
                    logger.error(f"Error loading conversation from DB: {e}")

            # 클라이언트와 DB 히스토리 병합
            merged_history = self._merge_conversation_history(
                conversation_history,
                db_history
            )

            # 사용자 메시지 저장
            self.conversation_manager.save_message(
                conversation_id=conversation_id,
                role='user',
                content=user_message,
                engine_type='',  # 엔진 타입은 나중에 설정
                user_id=user_id
            )

            return {
                'conversation_id': conversation_id,
                'merged_history': merged_history
            }

        except Exception as e:
            logger.error(f"Error processing conversation: {e}")
            raise
    
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
        """
        사용량 추적 (월별 + 일별) + 크레딧 차감

        Returns:
            dict: 크레딧 사용 정보 + 잔액 정보
        """
        try:
            from handlers.api.usage import deduct_credits, get_user_credits

            # 실제 토큰 정보 가져오기 (Anthropic API 응답에서)
            if (input_tokens is None or output_tokens is None) and hasattr(self, 'ai_client'):
                last_usage = self.ai_client.get_last_usage()
                if last_usage:
                    if input_tokens is None:
                        input_tokens = last_usage.get('input_tokens', 0)
                    if output_tokens is None:
                        output_tokens = last_usage.get('output_tokens', 0)
                    logger.info(f"📊 Using actual API tokens: input={input_tokens}, output={output_tokens}")

            # 폴백: 실제 값이 없으면 추정 (텍스트 길이 기반)
            if input_tokens is None or input_tokens == 0:
                input_tokens = int(len(input_text.split()) * 1.3)
                logger.info(f"⚠️ Estimated input tokens: {input_tokens}")
            if output_tokens is None or output_tokens == 0:
                output_tokens = int(len(output_text.split()) * 1.3)
                logger.info(f"⚠️ Estimated output tokens: {output_tokens}")

            total_tokens = input_tokens + output_tokens

            # 크레딧 계산 (모델별 요금)
            if not model_id:
                model_id = 'opus-4-20250514'

            # 모델별 요금 (NC per 1,000 tokens)
            CREDIT_RATES = {
                'opus-4-20250514': {'input': 7.5, 'output': 37.5},
                'claude-opus-4-5-20251101': {'input': 7.5, 'output': 37.5},
                'claude-sonnet-4-5-20250929': {'input': 4.5, 'output': 22.5},
                'default': {'input': 4.5, 'output': 22.5}
            }
            CREDIT_RATES = {
                'claude-opus-4-5-20251101': {'input': 7.5, 'output': 37.5},
                'claude-sonnet-4-5-20250929': {'input': 4.5, 'output': 22.5},
                'claude-haiku-4-5-20251001': {'input': 1.5, 'output': 7.5},
                'default': {'input': 4.5, 'output': 22.5}
            }
            rates = CREDIT_RATES.get(model_id, CREDIT_RATES['default'])
            input_credits = (input_tokens / 1000) * rates['input']
            output_credits = (output_tokens / 1000) * rates['output']
            credits_used = round(input_credits + output_credits, 2)

            now = datetime.now(timezone.utc)
            year_month = now.strftime('%Y-%m')
            today = now.strftime('%Y-%m-%d')

            # yearMonth에 engineType 포함하여 중복 방지
            year_month_with_engine = f"{year_month}#{engine_type.lower()}"

            # 1. 월별 사용량 기록 (기존)
            self.usage_table.update_item(
                Key={
                    'userId': user_id,
                    'yearMonth': year_month_with_engine
                },
                UpdateExpression="""
                    ADD requestCount :one,
                        inputTokens :input,
                        outputTokens :output,
                        totalTokens :total
                    SET engineType = :engine,
                        updatedAt = :now
                """,
                ExpressionAttributeValues={
                    ':one': 1,
                    ':input': input_tokens,
                    ':output': output_tokens,
                    ':total': total_tokens,
                    ':engine': engine_type,
                    ':now': now.isoformat()
                }
            )

            # 2. 일별 사용량 기록 (신규 - 대시보드 날짜 필터링용)
            date_engine_key = f"{today}#{engine_type}"
            self.daily_usage_table.update_item(
                Key={
                    'userId': user_id,
                    'dateEngine': date_engine_key
                },
                UpdateExpression="""
                    ADD inputTokens :input,
                        outputTokens :output,
                        totalTokens :total,
                        messageCount :one
                    SET #date = :date,
                        engineType = :engine,
                        updatedAt = :now
                """,
                ExpressionAttributeNames={
                    '#date': 'date'
                },
                ExpressionAttributeValues={
                    ':one': 1,
                    ':input': input_tokens,
                    ':output': output_tokens,
                    ':total': total_tokens,
                    ':date': today,
                    ':engine': engine_type,
                    ':now': now.isoformat()
                }
            )

            # 3. 크레딧 잔액에서 차감 (통합 크레딧 시스템)
            balance_info = deduct_credits(
                user_id=user_id,
                amount=credits_used,
                model_id=model_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )

            # 잔액 정보 가져오기
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

            logger.info(f"💳 Usage tracked: {user_id}, {engine_type}, model={model_id}, "
                       f"tokens={input_tokens}+{output_tokens}, credits={credits_used:.2f} NC, "
                       f"balance={current_balance:.2f} NC")

            return {
                'credits_used': credits_used,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': total_tokens,
                'model_id': model_id,
                'balance': current_balance,
                'total_used': total_used
            }

        except Exception as e:
            logger.error(f"Error tracking usage: {e}")
            return None
    
    def _merge_conversation_history(
        self,
        client_history: List[Dict] = None,
        db_history: List[Dict] = None
    ) -> List[Dict]:
        """
        클라이언트와 DB의 대화 히스토리 병합
        
        DB 히스토리를 기준으로 하되, 클라이언트 히스토리에만 있는 메시지는 추가
        """
        client_history = client_history or []
        db_history = db_history or []
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
    
    def _build_system_prompt(
        self,
        guidelines: str,
        description: str,
        files: List[Dict],
        conversation_context: str,
        engine_type: str = "P1",
        user_role: str = "user",
        web_context: str = ""
    ) -> str:
        """
        Anthropic API용 시스템 프롬프트 구성
        Bedrock과 동일한 체계적 프롬프트 사용
        """
        # prompt_data 구성
        prompt_data = {
            'prompt': {
                'instruction': guidelines or "",
                'description': description or ""
            },
            'files': files or [],
            'userRole': user_role
        }

        # Bedrock과 동일한 체계적 프롬프트 생성
        system_prompt = create_enhanced_system_prompt(
            prompt_data=prompt_data,
            engine_type=engine_type,
            use_enhanced=True,
            flexibility_level="strict"
        )

        # 웹 검색 컨텍스트 추가
        if web_context:
            system_prompt = system_prompt + "\n\n" + web_context
            logger.info(f"📎 Added web context to system prompt ({len(web_context)} chars)")

        return system_prompt
    
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
                role_label = "사용자" if role == 'user' else "AI"
                formatted_messages.append(f"{role_label}: {content}")
        
        if formatted_messages:
            return "\n\n=== 이전 대화 내용 ===\n" + "\n\n".join(formatted_messages) + "\n\n=== 현재 질문 ==="
        
        return ""

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

    def _should_enable_web_search(self, user_message: str) -> bool:
        """
        사용자 메시지에서 웹 검색 활성화 필요성 분석
        """
        try:
            # 환경변수로 웹 검색 기능 전역 비활성화 가능
            if os.environ.get('ENABLE_NATIVE_WEB_SEARCH', 'true').lower() != 'true':
                return False
            
            # 검색 키워드들
            search_keywords = [
                '최신', '오늘', '현재', '뉴스', '주가', '환율', '날씨', '트렌드',
                '속보', '실시간', '녹색소비', '카이스트', '디스카운트', '배당락',
                '비단등', '어디', '먹을거리', '관깑', '도시락', '매매', '알바', '일자리',
                '새로나온', '출시', '업데이트', '대표검', '순양', '손보', '이종명',
                '센터', '뿌리오', '로보트', '관련', 'related', 'latest', 'today', 'news', 'current'
            ]
            
            # 커미션 표현들
            action_keywords = [
                '찾아줘', '알아줘', '서치해', '검색해', '확인해',
                '업데이트 된', '정보', '어떻게'
            ]
            
            # 키워드 매칭
            message_lower = user_message.lower()
            
            # 검색 키워드 및 명령 매칭
            for keyword in search_keywords + action_keywords:
                if keyword in message_lower:
                    logger.info(f"Web search enabled by keyword: {keyword}")
                    return True
            
            # 특정 질문 패턴들
            question_patterns = [
                '예전에', '예전과', '비교', '차이', '저번과', '지난', 
                '지난번', '전년', '전달', '전주', '전 대비', 
                '전에 비해', '전 세대', '전과', '지나고',
                '안 되나요', '안 돼요', '안 되는', '되지 않는', 
                '작동안해', '메이지', '앉야', '개판', '이번', '이달', '그 전', '배경'
            ]
            
            for pattern in question_patterns:
                if pattern in message_lower:
                    logger.info(f"Web search enabled by pattern: {pattern}")
                    return True
                    
            return False
        
        except Exception as e:
            logger.error(f"Error in web search keyword detection: {str(e)}")
            return False