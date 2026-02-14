"""
WebSocket Service
WebSocket 메시지 처리 및 Bedrock 통합 서비스
Application-level Prompt Caching 적용
"""
import json
import boto3
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Generator
import uuid
import os
import sys
from datetime import datetime, timezone, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config.aws import AWS_REGION, DYNAMODB_TABLES

from handlers.websocket.conversation_manager import ConversationManager
from lib.bedrock_client_enhanced import BedrockClientEnhanced
from lib.anthropic_client import AnthropicClient
from lib import web_search_client  # Tavily 웹검색 (모듈 레벨 함수)
from utils.logger import setup_logger

logger = setup_logger(__name__)

# 글로벌 캐시 - Lambda 컨테이너 재사용 시 유지됨 (영구 캐시)
PROMPT_CACHE: Dict[str, Dict[str, Any]] = {}
# TTL 제거 - 컨테이너 수명 동안 영구 유지

# DynamoDB 클라이언트 - 프롬프트 테이블 접근용
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

# f1 서비스용 테이블 설정
PROMPTS_TABLE_NAME = os.environ.get('PROMPTS_TABLE', 'f1-prompts-two')
FILES_TABLE_NAME = os.environ.get('FILES_TABLE', 'f1-files-two')

prompts_table = dynamodb.Table(PROMPTS_TABLE_NAME)
files_table = dynamodb.Table(FILES_TABLE_NAME)

logger.info(f"Using prompts table: {PROMPTS_TABLE_NAME}")
logger.info(f"Using files table: {FILES_TABLE_NAME}")


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
        self.files_table = files_table
        logger.info("WebSocketService initialized with Anthropic API support")

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
        DynamoDB에서 프롬프트와 파일 로드 (영구 캐싱 적용)

        캐시 히트 시 DB 조회를 완전히 생략하여 성능 극대화
        """
        global PROMPT_CACHE

        # 캐시 확인 (영구 캐시)
        if engine_type in PROMPT_CACHE:
            logger.info(f"Cache HIT for {engine_type} - DB query skipped")
            return PROMPT_CACHE[engine_type]
        
        logger.info(f"Cache MISS for {engine_type} - fetching from DB")

        # 캐시 미스 - DB에서 로드
        prompt_data = self._fetch_prompt_from_db(engine_type)

        # 캐시 업데이트 (영구 캐시)
        PROMPT_CACHE[engine_type] = prompt_data
        logger.info(f"Cached prompt for {engine_type} "
                   f"({len(prompt_data.get('files', []))} files, "
                   f"{len(str(prompt_data))} bytes) - will persist for container lifetime")

        return prompt_data

    def _fetch_prompt_from_db(self, engine_type: str) -> Dict[str, Any]:
        """
        실제 DB 조회 로직 (캐싱 전용)
        캐시 미스 시에만 호출됨
        """
        try:
            start_time = time.time()

            # 프롬프트 테이블에서 기본 정보 로드
            # 복합 키 사용: engineType (HASH) + promptId (RANGE)
            response = self.prompts_table.get_item(
                Key={
                    'engineType': engine_type,
                    'promptId': engine_type  # engineType과 promptId가 같은 값 사용
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
                    # f1-files-two 테이블은 전체 스캔 (현재 파일이 1개만 있음)
                    files_response = self.files_table.scan()

                    if 'Items' in files_response:
                        for file_item in files_response['Items']:
                            prompt_data['files'].append({
                                'fileName': file_item.get('fileName', ''),
                                'fileContent': file_item.get('fileContent', ''),
                                'fileType': 'text'  # 기본값
                            })
                except Exception as fe:
                    logger.error(f"Error loading files from {FILES_TABLE_NAME}: {str(fe)}")

                elapsed = (time.time() - start_time) * 1000
                logger.info(f"DB fetch for {engine_type}: "
                          f"{len(prompt_data['files'])} files in {elapsed:.0f}ms")

                return prompt_data
            else:
                logger.warning(f"No prompt found for engine type: {engine_type} in table {PROMPTS_TABLE_NAME}")
                return {'instruction': '', 'description': '', 'files': []}
        except Exception as e:
            logger.error(f"Error loading prompt from DynamoDB: {str(e)}")
            logger.error(f"Table: {PROMPTS_TABLE_NAME}, Key: engineType={engine_type}, promptId={engine_type}")
            return {'instruction': '', 'description': '', 'files': []}

    def stream_response(
        self,
        user_message: str,
        engine_type: str,
        conversation_id: str,
        user_id: str,
        conversation_history: List[Dict],
        user_role: str = 'user',
        model_id: str = 'opus-4-20250514',  # 모델 선택 파라미터
        web_search_enabled: bool = False  # 🌐 웹검색 활성화 여부
    ) -> Generator[str, None, None]:
        """
        Bedrock 스트리밍 응답 생성

        Yields:
            str: 응답 청크 또는 웹검색 결과 (dict)
        """
        logger.info(f"🎯 Using model: {model_id}, webSearch: {web_search_enabled}")
        try:
            # 🌐 웹검색이 활성화된 경우 Tavily 검색 수행
            web_context = ""
            if web_search_enabled:
                logger.info(f"🌐 Tavily 웹검색 시작: {user_message[:50]}...")
                search_result = web_search_client.search(user_message, max_results=5)

                if search_result.get('success') and search_result.get('results'):
                    # 검색 결과를 클라이언트로 전송하기 위해 yield
                    sources = [{
                        'title': r.get('title', ''),
                        'url': r.get('url', ''),
                        'content': r.get('content', '')[:200]
                    } for r in search_result.get('results', [])]

                    yield {
                        'type': 'web_search_results',
                        'query': user_message,
                        'sources': sources
                    }

                    # AI에게 전달할 컨텍스트 생성
                    web_context = web_search_client.format_context(search_result)
                    logger.info(f"🌐 웹검색 컨텍스트 추가: {len(web_context)} chars")

            # 대화 컨텍스트를 포함한 프롬프트 생성
            formatted_history = self._format_conversation_for_bedrock(conversation_history)

            # DynamoDB에서 프롬프트 로드 (수정된 메서드 사용)
            prompt_data = self._load_prompt_from_dynamodb(engine_type)

            # 로드된 데이터 상세 로깅
            logger.info(f"=== Prompt Data Loaded for {engine_type} ===")
            logger.info(f"Instruction length: {len(prompt_data.get('instruction', ''))} chars")
            logger.info(f"Description length: {len(prompt_data.get('description', ''))} chars")
            logger.info(f"Files count: {len(prompt_data.get('files', []))}")

            logger.info(f"Streaming response for engine {engine_type}")
            logger.info(f"Conversation context: {len(formatted_history)} messages")

            # AI 스트리밍 호출 (Anthropic 또는 Bedrock)
            total_response = ""

            # Anthropic API 사용 시
            if self.ai_provider == 'anthropic' and hasattr(self.ai_client, 'stream_response_with_history'):
                try:
                    logger.info(f"🤖 Using Anthropic API with conversation caching for {engine_type}")

                    # 프롬프트 구성 (캐싱 최적화: 정적 컨텐츠만 포함)
                    full_system_prompt = self._build_system_prompt(
                        instruction=prompt_data.get('instruction', ''),
                        description=prompt_data.get('description', ''),
                        files=prompt_data.get('files', [])
                    )

                    # 🌐 웹검색 컨텍스트가 있으면 시스템 프롬프트에 추가
                    if web_context:
                        full_system_prompt = full_system_prompt + "\n\n" + web_context
                        logger.info(f"🌐 웹검색 컨텍스트를 시스템 프롬프트에 추가")

                    # 웹 검색 활성화 조건 확인
                    enable_web_search = self._should_enable_web_search(user_message)

                    # 대화 히스토리를 캐싱용 메시지 리스트로 준비
                    messages_for_caching = self._prepare_messages_for_caching(
                        conversation_history=conversation_history,
                        current_message=user_message
                    )

                    # 대화 히스토리 캐싱이 적용된 스트리밍 응답
                    for chunk in self.ai_client.stream_response_with_history(
                        messages=messages_for_caching,
                        system_prompt=full_system_prompt,
                        enable_caching=True,
                        enable_web_search=enable_web_search,
                        model_id=model_id
                    ):
                        total_response += chunk
                        yield chunk
                        
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
                            files=prompt_data.get('files', [])
                        ):
                            total_response += chunk
                            yield chunk
                    else:
                        raise
            
            # Bedrock 사용 시 (기존 로직)
            else:
                logger.info(f"🤖 Using Bedrock client with engine {engine_type}")
                for chunk in self.bedrock_client.stream_bedrock(
                    user_message=user_message,
                    engine_type=engine_type,
                    conversation_context=formatted_history,
                    user_role=user_role,
                    guidelines=prompt_data.get('instruction'),
                    description=prompt_data.get('description'),
                    files=prompt_data.get('files', [])
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

    def clear_history(self, conversation_id: str, user_id: str = None) -> bool:
        """대화 히스토리 초기화"""
        try:
            # 새로운 대화로 재생성
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
                'claude-haiku-4-5-20251001': {'input': 1.5, 'output': 7.5},
                'default': {'input': 4.5, 'output': 22.5}
            }
            rates = CREDIT_RATES.get(model_id, CREDIT_RATES['default'])
            credits_used = round((input_tokens / 1000) * rates['input'] + (output_tokens / 1000) * rates['output'], 2)

            # DynamoDB에 사용량 저장
            usage_table = dynamodb.Table(os.environ.get('USAGE_TABLE', 'f1-usage-two'))
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
                    ':timestamp': datetime.now().isoformat(),
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
    
    def _build_system_prompt(
        self,
        instruction: str,
        description: str,
        files: List[Dict]
    ) -> str:
        """
        Anthropic API용 시스템 프롬프트 구성 (캐싱 최적화: 정적 컨텐츠만 포함)

        Note: 대화 히스토리는 여기에 포함하지 않음 (messages 배열로 별도 전달)
        """
        prompt_parts = []

        # 기본 가이드라인
        if instruction:
            prompt_parts.append(instruction)

        # 설명 추가
        if description:
            prompt_parts.append(f"\n\n=== 추가 설명 ===\n{description}")

        # 웹 검색 출처 표시 가이드라인 추가
        web_search_guidelines = """

### 📚 웹 검색 출처 표시 (필수)
웹 검색 결과 사용 시 반드시:
1. **인라인 각주**: 정보 제공 시 [1], [2] 형식으로 번호 표시
2. **출처 섹션**: 응답 마지막에 다음 형식으로 출처 명시
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   📚 출처:
   [1] 언론사/사이트명 - 제목 (URL)
   [2] 언론사/사이트명 - 제목 (URL)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3. **신뢰도 표시**:
   - 공식 언론사: ✅
   - 정부/공공기관: 🏛️
   - 일반 웹사이트: ℹ️

### 📅 시간 정보 활용
- "오늘", "최근", "최신" 등의 키워드가 있을 때 웹 검색 적극 활용
"""
        prompt_parts.append(web_search_guidelines)

        # 파일 내용 추가
        if files:
            prompt_parts.append("\n\n=== 참고 문서 ===")
            for file in files:
                file_name = file.get('fileName', 'Unknown')
                file_content = file.get('fileContent', '')
                if file_content:
                    prompt_parts.append(f"\n[{file_name}]\n{file_content}")

        # 캐싱 최적화: 대화 컨텍스트는 여기에 추가하지 않음 (messages로 전달)

        return "\n".join(prompt_parts)
    
    def _should_enable_web_search(self, user_message: str) -> bool:
        """
        사용자 메시지를 분석하여 웹 검색 기능 활성화 여부 결정
        
        Args:
            user_message: 사용자 메시지
            
        Returns:
            bool: 웹 검색 활성화 여부
        """
        # 기본 설정값 확인
        default_enabled = os.environ.get('ENABLE_NATIVE_WEB_SEARCH', 'true').lower() == 'true'
        
        if not default_enabled:
            return False
        
        # 웹 검색이 필요한 키워드들
        search_keywords = [
            '최신', '오늘', '현재', '지금', '최근', '뉴스', '소식', 
            '올해', '이번년', '2024년', '2025년',
            '실시간', '업데이트', '동향', '현황', '상황',
            '언제', '몇시', '시간', '날짜',
            '주가', '환율', '증시', '시세',
            '날씨', '기온', '미세먼지',
            '트렌드', '인기', '랭킹'
        ]
        
        # 사용자 메시지에 검색 키워드가 포함되어 있는지 확인
        user_message_lower = user_message.lower()
        for keyword in search_keywords:
            if keyword in user_message_lower:
                logger.info(f"Web search enabled by keyword: '{keyword}'")
                return True
        
        # URL이 포함된 경우 웹 검색 활성화 (추가 정보 필요할 수 있음)
        if 'http' in user_message_lower:
            logger.info("Web search enabled due to URL in message")
            return True
        
        # 질문형 문장에서 실시간 정보가 필요할 수 있는 경우
        question_indicators = ['어떻게', '어떤', '무엇', '언제', '어디서', '왜', '얼마']
        if any(indicator in user_message for indicator in question_indicators):
            # 추가적으로 시간/날짜 관련 단어가 있는지 확인
            time_words = ['지금', '현재', '오늘', '최근', '최신']
            if any(word in user_message for word in time_words):
                logger.info("Web search enabled for time-sensitive question")
                return True
        
        # 기본값은 환경변수 설정 따름
        return default_enabled

    def _prepare_messages_for_caching(
        self,
        conversation_history: List[Dict],
        current_message: str
    ) -> List[Dict]:
        """
        대화 히스토리를 Anthropic 캐싱용 메시지 리스트로 준비

        Args:
            conversation_history: 이전 대화 히스토리
            current_message: 현재 사용자 메시지

        Returns:
            Anthropic API에 전달할 메시지 리스트
        """
        messages = []

        # 최근 10개 메시지만 사용 (컨텍스트 길이 관리)
        recent_history = conversation_history[-10:] if conversation_history else []

        for msg in recent_history:
            role = msg.get('role', 'user')
            content = msg.get('content', '')

            if role in ['user', 'assistant'] and content:
                messages.append({
                    'role': role,
                    'content': content
                })

        # user/assistant 교대 검증
        messages = self._validate_message_alternation(messages)

        # 현재 사용자 메시지 추가
        messages.append({
            'role': 'user',
            'content': current_message
        })

        logger.info(f"📚 Prepared {len(messages)} messages for caching (history: {len(recent_history)})")
        return messages

    def _validate_message_alternation(self, messages: List[Dict]) -> List[Dict]:
        """
        Anthropic API는 user/assistant 메시지가 교대로 와야 함
        연속된 같은 역할의 메시지가 있으면 플레이스홀더 삽입

        Args:
            messages: 검증할 메시지 리스트

        Returns:
            교대가 보장된 메시지 리스트
        """
        if not messages:
            return messages

        validated = []
        for i, msg in enumerate(messages):
            if i > 0 and validated[-1]['role'] == msg['role']:
                # 같은 역할이 연속되면 반대 역할의 플레이스홀더 삽입
                placeholder_role = 'assistant' if msg['role'] == 'user' else 'user'
                validated.append({
                    'role': placeholder_role,
                    'content': '(계속)'
                })
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