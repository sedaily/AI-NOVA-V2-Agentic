"""
WebSocket Service with Dual AI Provider Support
Bedrock + Anthropic API 병행 지원 버전
"""
import json
import boto3
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Generator, Tuple
import uuid
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config.aws import AWS_REGION, DYNAMODB_TABLES

from handlers.websocket.conversation_manager import ConversationManager
from lib.perplexity_client import PerplexityClient
from utils.logger import setup_logger

logger = setup_logger(__name__)

# 글로벌 캐시 - Lambda 컨테이너 재사용 시 유지됨
PROMPT_CACHE: Dict[str, Tuple[Dict[str, Any], float]] = {}
CACHE_TTL = 300  # 5분 (초 단위)

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
        self.perplexity_client = PerplexityClient()
        # AI 클라이언트는 동적으로 선택됨
        self.ai_client = None
        logger.info("WebSocketService initialized with dual AI provider support")

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
        DynamoDB에서 프롬프트와 파일 로드 (인메모리 캐싱 적용)
        """
        global PROMPT_CACHE
        now = time.time()

        # 캐시 확인
        if engine_type in PROMPT_CACHE:
            cached_data, cached_time = PROMPT_CACHE[engine_type]
            age = now - cached_time

            if age < CACHE_TTL:
                logger.info(f"✅ Cache HIT for {engine_type} (age: {age:.1f}s)")
                return cached_data
            else:
                logger.info(f"⏰ Cache EXPIRED for {engine_type} (age: {age:.1f}s)")
        else:
            logger.info(f"❌ Cache MISS for {engine_type}")

        # 캐시 미스 또는 만료 - DB에서 로드
        prompt_data = self._fetch_prompt_from_db(engine_type)

        # 캐시 업데이트
        PROMPT_CACHE[engine_type] = (prompt_data, now)
        logger.info(f"💾 Cached prompt for {engine_type}")

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
                logger.info(f"🔍 DB fetch for {engine_type} in {elapsed:.0f}ms")

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
        user_role: str = 'user'
    ) -> Generator[str, None, None]:
        """
        AI 스트리밍 응답 생성 (Bedrock/Anthropic 자동 선택)

        Yields:
            str: 응답 청크
        """
        try:
            # AI 클라이언트 선택
            ai_client = self._get_or_create_ai_client(user_id, engine_type)
            
            # 대화 컨텍스트를 포함한 프롬프트 생성
            formatted_history = self._format_conversation_for_bedrock(conversation_history)

            # DynamoDB에서 프롬프트 로드
            prompt_data = self._load_prompt_from_dynamodb(engine_type)

            logger.info(f"=== Prompt Data Loaded for {engine_type} ===")
            logger.info(f"AI Client: {ai_client.__class__.__name__}")
            
            # 웹 검색 수행 (옵션)
            web_search_result = None
            enable_search = os.environ.get('ENABLE_WEB_SEARCH', 'false').lower() == 'true'
            
            if enable_search:
                logger.info(f"🔍 Web search ENABLED")
                try:
                    web_search_result = self.perplexity_client.search(user_message, enable=True)
                    if web_search_result:
                        logger.info(f"✅ Web search completed")
                except Exception as e:
                    logger.error(f"❌ Web search failed: {str(e)}")

            # 웹 검색 결과를 메시지에 추가
            enhanced_message = user_message
            if web_search_result:
                enhanced_message = f"[최신 웹 검색 정보]\n{web_search_result}\n\n[사용자 질문]\n{user_message}"

            total_response = ""
            retry_with_bedrock = False
            
            try:
                # AI 클라이언트 호출 (Bedrock 호환 인터페이스)
                for chunk in ai_client.stream_bedrock(
                    user_message=enhanced_message,
                    engine_type=engine_type,
                    conversation_context=formatted_history,
                    user_role=user_role,
                    guidelines=prompt_data.get('instruction'),
                    description=prompt_data.get('description'),
                    files=prompt_data.get('files', [])
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
                
                # 폴백 알림
                yield "\n\n[시스템: 프리미엄 모델 제한으로 표준 모델로 전환됩니다]\n\n"
                
                for chunk in bedrock_client.stream_bedrock(
                    user_message=enhanced_message,
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
        output_text: str
    ) -> None:
        """사용량 추적"""
        try:
            # 토큰 계산 (간단한 추정)
            input_tokens = len(input_text.split())
            output_tokens = len(output_text.split())

            logger.info(f"Usage tracked - User: {user_id}, Engine: {engine_type}")
            logger.info(f"Tokens - Input: {input_tokens}, Output: {output_tokens}")

            # DynamoDB에 사용량 저장
            usage_table = dynamodb.Table(os.environ.get('USAGE_TABLE', 'p2-two-usage-two'))
            today = datetime.now().strftime('%Y-%m-%d')

            date_key = f"{today}#{engine_type}"

            from decimal import Decimal
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
                    ':total': Decimal(str(input_tokens + output_tokens)),
                    ':input': Decimal(str(input_tokens)),
                    ':output': Decimal(str(output_tokens)),
                    ':one': Decimal('1'),
                    ':timestamp': datetime.utcnow().isoformat() + 'Z',
                    ':engineType': engine_type,
                    ':usageDate': today
                }
            )

            logger.info("Usage recorded in DynamoDB")

        except Exception as e:
            logger.error(f"Error tracking usage: {str(e)}")

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