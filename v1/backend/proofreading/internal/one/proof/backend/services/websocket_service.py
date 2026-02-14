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
from lib.perplexity_client import get_perplexity_client
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

        # AI 클라이언트 초기화 - Bedrock 전용 (2026-01 마이그레이션 완료)
        self.ai_client = BedrockClientEnhanced()
        self.ai_provider = 'bedrock'
        logger.info("🎯 AI Provider: AWS Bedrock (Prompt Caching Enabled)")
        self.bedrock_client = self.ai_client

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
        selected_model: str = 'claude-opus-4-5-20251101',
        web_search_enabled: bool = False
    ) -> Generator[str, None, None]:
        """
        Bedrock 스트리밍 응답 생성

        Yields:
            str: 응답 청크

        Returns (via self.last_usage_info):
            dict: 실제 토큰 사용량 정보
        """
        # 토큰 사용량 저장용
        self.last_usage_info = None
        self.last_web_search_result = None

        # 웹검색 실행 (활성화된 경우)
        web_search_context = ""
        if web_search_enabled:
            try:
                perplexity = get_perplexity_client()
                if perplexity.is_available():
                    logger.info(f"🔍 웹검색 실행: {user_message[:50]}...")
                    search_result = perplexity.search_for_context(
                        user_query=user_message,
                        recency_filter="day",
                        use_domain_filter=True
                    )

                    if search_result.get('success'):
                        self.last_web_search_result = search_result
                        web_search_context = perplexity.format_search_results_for_prompt(search_result)
                        logger.info(f"🌐 웹검색 완료: {len(search_result.get('citations', []))}개 출처")
                    else:
                        logger.warning(f"웹검색 실패: {search_result.get('error')}")
                else:
                    logger.warning("Perplexity API 사용 불가")
            except Exception as e:
                logger.error(f"웹검색 오류: {str(e)}")

        try:
            # 대화 컨텍스트를 포함한 프롬프트 생성
            formatted_history = self._format_conversation_for_bedrock(conversation_history)

            # DynamoDB에서 프롬프트와 파일 통합 로드
            prompt_data = self._load_prompt_from_dynamodb(engine_type)
            logger.info(f"Loaded prompt for {engine_type}: instruction={len(prompt_data.get('instruction', ''))} chars")

            logger.info(f"Streaming response for engine {engine_type}")
            logger.info(f"Conversation context: {len(formatted_history)} messages")

            # 웹검색 결과를 사용자 메시지에 추가
            enhanced_message = user_message
            if web_search_context:
                enhanced_message = f"{web_search_context}\n\n사용자 질문: {user_message}"
                logger.info(f"웹검색 컨텍스트 추가됨 ({len(web_search_context)} chars)")

            # AI 스트리밍 호출 (Anthropic 또는 Bedrock)
            total_response = ""
            
            # Anthropic API 사용 시
            if self.ai_provider == 'anthropic' and hasattr(self.ai_client, 'stream_response'):
                try:
                    logger.info(f"Using Anthropic API for {engine_type} with prompt caching")
                    
                    # 프롬프트와 대화 컨텍스트 결합 (Bedrock과 동일한 체계적 프롬프트)
                    full_system_prompt = self._build_system_prompt(
                        guidelines=prompt_data.get('instruction', ''),
                        description=prompt_data.get('description', ''),
                        files=prompt_data.get('files', []),
                        conversation_context=formatted_history,
                        engine_type=engine_type,
                        user_role=user_role
                    )
                    
                    # 웹 검색 활성화 여부 판단
                    enable_web_search = self._should_enable_web_search(user_message)
                    
                    # Prompt Caching 활성화 (기본값: True)
                    use_caching = os.environ.get('ENABLE_PROMPT_CACHING', 'true').lower() == 'true'
                    
                    for chunk in self.ai_client.stream_response(
                        user_message=enhanced_message,
                        system_prompt=full_system_prompt,
                        conversation_context=formatted_history,
                        enable_web_search=enable_web_search,
                        web_search_max_uses=int(os.environ.get('WEB_SEARCH_MAX_USES', '5')),
                        use_caching=use_caching  # Prompt Caching 파라미터 추가
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
                            user_message=enhanced_message,
                            engine_type=engine_type,
                            conversation_context=formatted_history,
                            user_role=user_role,
                            guidelines=prompt_data.get('instruction'),
                            description=prompt_data.get('description'),
                            files=prompt_data.get('files', []),
                            selected_model=selected_model  # 선택된 모델 전달
                        ):
                            # usage 정보인지 텍스트인지 구분
                            if isinstance(chunk, dict) and chunk.get('type') == 'usage':
                                self.last_usage_info = chunk
                                logger.info(f"📊 Captured usage info: {chunk}")
                            else:
                                total_response += chunk
                                yield chunk
                    else:
                        raise

            # Bedrock 사용 시 (기존 로직)
            else:
                for chunk in self.bedrock_client.stream_bedrock(
                    user_message=enhanced_message,
                    engine_type=engine_type,
                    conversation_context=formatted_history,  # 대화 컨텍스트 전달
                    user_role=user_role,
                    guidelines=prompt_data.get('instruction'),  # DynamoDB instruction 전달
                    description=prompt_data.get('description'),  # DynamoDB description 전달
                    files=prompt_data.get('files', []),  # DynamoDB files 전달
                    selected_model=selected_model  # 선택된 모델 전달
                ):
                    # usage 정보인지 텍스트인지 구분
                    if isinstance(chunk, dict) and chunk.get('type') == 'usage':
                        self.last_usage_info = chunk
                        logger.info(f"📊 Captured usage info: {chunk}")
                    else:
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
        actual_input_tokens: Optional[int] = None,
        actual_output_tokens: Optional[int] = None,
        cache_read_tokens: Optional[int] = None,
        cache_creation_tokens: Optional[int] = None,
        model_id: Optional[str] = None
    ) -> None:
        """
        사용량 추적 (월별 + 일별)

        Args:
            user_id: 사용자 ID
            engine_type: 엔진 타입
            input_text: 입력 텍스트 (폴백용)
            output_text: 출력 텍스트 (폴백용)
            actual_input_tokens: Bedrock에서 반환한 실제 입력 토큰 수
            actual_output_tokens: Bedrock에서 반환한 실제 출력 토큰 수
            cache_read_tokens: 캐시에서 읽은 토큰 수
            cache_creation_tokens: 캐시에 생성된 토큰 수
            model_id: 사용된 모델 ID
        """
        try:
            # 실제 토큰 수 사용, 없으면 추정치 사용
            if actual_input_tokens is not None:
                input_tokens = actual_input_tokens
                logger.info(f"📊 Using actual input tokens: {input_tokens}")
            else:
                input_tokens = len(input_text.split()) * 2
                logger.info(f"📊 Using estimated input tokens: {input_tokens}")

            if actual_output_tokens is not None:
                output_tokens = actual_output_tokens
                logger.info(f"📊 Using actual output tokens: {output_tokens}")
            else:
                output_tokens = len(output_text.split()) * 2
                logger.info(f"📊 Using estimated output tokens: {output_tokens}")

            total_tokens = input_tokens + output_tokens

            # 캐시 토큰 정보
            cache_read = cache_read_tokens or 0
            cache_creation = cache_creation_tokens or 0

            now = datetime.now(timezone.utc)
            year_month = now.strftime('%Y-%m')
            today = now.strftime('%Y-%m-%d')

            # yearMonth에 engineType 포함하여 중복 방지
            year_month_with_engine = f"{year_month}#{engine_type.lower()}"

            # 1. 월별 사용량 기록 (기존 + 캐시 정보)
            self.usage_table.update_item(
                Key={
                    'userId': user_id,
                    'yearMonth': year_month_with_engine
                },
                UpdateExpression="""
                    ADD requestCount :one,
                        inputTokens :input,
                        outputTokens :output,
                        totalTokens :total,
                        cacheReadTokens :cacheRead,
                        cacheCreationTokens :cacheCreation
                    SET engineType = :engine,
                        lastModelId = :modelId,
                        updatedAt = :now
                """,
                ExpressionAttributeValues={
                    ':one': 1,
                    ':input': input_tokens,
                    ':output': output_tokens,
                    ':total': total_tokens,
                    ':cacheRead': cache_read,
                    ':cacheCreation': cache_creation,
                    ':engine': engine_type,
                    ':modelId': model_id or 'unknown',
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
                        cacheReadTokens :cacheRead,
                        cacheCreationTokens :cacheCreation,
                        messageCount :one
                    SET #date = :date,
                        engineType = :engine,
                        lastModelId = :modelId,
                        updatedAt = :now
                """,
                ExpressionAttributeNames={
                    '#date': 'date'  # 'date'는 예약어이므로 ExpressionAttributeNames 사용
                },
                ExpressionAttributeValues={
                    ':one': 1,
                    ':input': input_tokens,
                    ':output': output_tokens,
                    ':total': total_tokens,
                    ':cacheRead': cache_read,
                    ':cacheCreation': cache_creation,
                    ':date': today,
                    ':engine': engine_type,
                    ':modelId': model_id or 'unknown',
                    ':now': now.isoformat()
                }
            )

            logger.info(f"📊 Usage tracked for {user_id}: "
                       f"input={input_tokens}, output={output_tokens}, "
                       f"cache_read={cache_read}, cache_creation={cache_creation}, "
                       f"model={model_id} (monthly + daily)")

        except Exception as e:
            logger.error(f"Error tracking usage: {e}")
    
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
        user_role: str = "user"
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