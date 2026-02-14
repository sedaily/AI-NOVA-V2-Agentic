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
from lib.perplexity_client import get_perplexity_client
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
        # AI 클라이언트 초기화 - Bedrock 전용 (2026-01 마이그레이션 완료)
        self.ai_client = BedrockClientEnhanced()
        self.ai_provider = 'bedrock'
        logger.info("🎯 AI Provider: AWS Bedrock (Prompt Caching Enabled)")

        # Bedrock 클라이언트 (동일 인스턴스 참조)
        self.bedrock_client = self.ai_client
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
        selected_model: str = 'claude-opus-4-5-20251101',
        web_search_enabled: bool = True
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

        try:
            # 웹 검색 수행 (Perplexity API)
            web_search_context = ""
            if web_search_enabled:
                try:
                    perplexity = get_perplexity_client()
                    if perplexity.is_available():
                        logger.info(f"🔍 Perplexity 웹검색 시작: {user_message[:50]}...")
                        search_result = perplexity.search_for_context(
                            user_query=user_message,
                            recency_filter="day",
                            use_domain_filter=True
                        )
                        if search_result:
                            self.last_web_search_result = search_result
                            web_search_context = perplexity.format_search_results_for_prompt(search_result)
                            logger.info(f"✅ 웹검색 완료: {len(web_search_context)} chars")
                except Exception as e:
                    logger.warning(f"⚠️ Perplexity 웹검색 실패 (계속 진행): {str(e)}")

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
            if self.ai_provider == 'anthropic' and hasattr(self.ai_client, 'stream_response'):
                try:
                    logger.info(f"Using Anthropic API for {engine_type}")

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
                    
                    for chunk in self.ai_client.stream_response(
                        user_message=user_message,
                        system_prompt=full_system_prompt,
                        conversation_history=conversation_history,  # 캐싱 최적화: messages 배열로 전달
                        enable_web_search=web_search_enabled  # 프론트엔드에서 전달된 웹검색 설정 사용
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
                # 웹검색 결과가 있으면 메시지에 추가
                enhanced_message = user_message
                if web_search_context:
                    enhanced_message = f"{web_search_context}\n\n사용자 질문: {user_message}"
                    logger.info(f"웹검색 컨텍스트 추가됨 ({len(web_search_context)} chars)")

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
        actual_input_tokens: Optional[int] = None,
        actual_output_tokens: Optional[int] = None,
        cache_read_tokens: Optional[int] = None,
        cache_creation_tokens: Optional[int] = None,
        model_id: Optional[str] = None
    ) -> None:
        """
        사용량 추적

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
                input_tokens = len(input_text.split())
                logger.info(f"📊 Using estimated input tokens: {input_tokens}")

            if actual_output_tokens is not None:
                output_tokens = actual_output_tokens
                logger.info(f"📊 Using actual output tokens: {output_tokens}")
            else:
                output_tokens = len(output_text.split())
                logger.info(f"📊 Using estimated output tokens: {output_tokens}")

            # 캐시 토큰 정보
            cache_read = cache_read_tokens or 0
            cache_creation = cache_creation_tokens or 0

            logger.info(f"Usage tracked - User: {user_id}, Engine: {engine_type}")
            logger.info(f"Tokens - Input: {input_tokens}, Output: {output_tokens}, "
                       f"Cache read: {cache_read}, Cache creation: {cache_creation}")

            # DynamoDB에 사용량 저장
            usage_table = dynamodb.Table(os.environ.get('USAGE_TABLE', 'w1-usage'))
            year_month = datetime.now().strftime('%Y-%m')

            # period 키 생성 (테이블 스키마: userId, period)
            period = f"{year_month}#{engine_type}"

            # 원자적 업데이트로 사용량 증가
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
                        cacheReadTokens :cacheRead,
                        cacheCreationTokens :cacheCreation,
                        messageCount :one
                    SET updatedAt = :timestamp,
                        lastUsedAt = :timestamp,
                        engineType = if_not_exists(engineType, :engineType),
                        yearMonth = if_not_exists(yearMonth, :yearMonth),
                        lastModelId = :modelId
                """,
                ExpressionAttributeValues={
                    ':total': Decimal(str(input_tokens + output_tokens)),
                    ':input': Decimal(str(input_tokens)),
                    ':output': Decimal(str(output_tokens)),
                    ':cacheRead': Decimal(str(cache_read)),
                    ':cacheCreation': Decimal(str(cache_creation)),
                    ':one': Decimal('1'),
                    ':timestamp': datetime.now().isoformat(),
                    ':engineType': engine_type,
                    ':yearMonth': year_month,
                    ':modelId': model_id or 'unknown'
                }
            )

            logger.info(f"📊 Usage saved to DynamoDB - Table: {usage_table.name}, userId: {user_id}, period: {period}")

        except Exception as e:
            logger.error(f"Error tracking usage: {str(e)}", exc_info=True)

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