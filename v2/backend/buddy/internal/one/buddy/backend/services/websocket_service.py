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
from lib.perplexity_client import PerplexityClient
from utils.logger import setup_logger

logger = setup_logger(__name__)

# 글로벌 캐시 - Lambda 컨테이너 재사용 시 유지됨 (영구 캐시)
PROMPT_CACHE: Dict[str, Dict[str, Any]] = {}

# DynamoDB 클라이언트 - 프롬프트 테이블 접근용
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

# f1 서비스용 테이블 설정
PROMPTS_TABLE_NAME = os.environ.get('PROMPTS_TABLE', 'b1-prompts-v2')
FILES_TABLE_NAME = os.environ.get('FILES_TABLE', 'b1-files-v2')

prompts_table = dynamodb.Table(PROMPTS_TABLE_NAME)
files_table = dynamodb.Table(FILES_TABLE_NAME)

logger.info(f"Using prompts table: {PROMPTS_TABLE_NAME}")
logger.info(f"Using files table: {FILES_TABLE_NAME}")


def get_ai_client(user_id: str = None, engine_type: str = None):
    """
    AI 클라이언트 반환 - Bedrock 전용

    Anthropic Direct API는 더 이상 사용하지 않음 (2026-01 Bedrock 마이그레이션 완료)
    """
    from lib.bedrock_client_enhanced import BedrockClientEnhanced
    logger.info("🎯 AI Provider: AWS Bedrock (Prompt Caching Enabled)")
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

    def stream_response(
        self,
        user_message: str,
        engine_type: str,
        conversation_id: str,
        user_id: str,
        conversation_history: List[Dict],
        user_role: str = 'user',
        selected_model: Optional[str] = None,
        web_search_enabled: bool = True
    ) -> Generator[str, None, None]:
        """
        AI 스트리밍 응답 생성 (Bedrock/Anthropic 자동 선택)

        Args:
            selected_model: 프론트엔드 모델 ID

        Yields:
            str: 응답 청크

        Returns (via self.last_usage_info):
            dict: 실제 토큰 사용량 정보 (캐시 메트릭 포함)
        """
        # 토큰 사용량 저장용 (캐시 메트릭 포함)
        self.last_usage_info = None

        try:
            # AI 클라이언트 선택
            ai_client = self._get_or_create_ai_client(user_id, engine_type)
            
            # 대화 컨텍스트를 포함한 프롬프트 생성
            formatted_history = self._format_conversation_for_bedrock(conversation_history)

            # DynamoDB에서 프롬프트 로드 (파일만 사용)
            prompt_data_from_db = self._load_prompt_from_dynamodb(engine_type)

            # 시스템 프롬프트 하드코딩 (정보 제공형)
            prompt_data = {
                'description': """# 서울경제 AI 뉴스 어시스턴트

## 역할
당신은 서울경제신문의 AI 뉴스 어시스턴트입니다.
웹 검색 결과를 활용하여 사용자에게 최신 뉴스와 정보를 명확하고 구조적으로 전달합니다.

## 핵심 원칙
1. **정보 제공 중심**: 사용자의 질문에 직접 답변하세요. 진단이나 분석 요청을 하지 마세요.
2. **웹 검색 활용**: 제공된 웹 검색 결과를 바탕으로 최신 정보를 전달하세요.
3. **구조화된 응답**: 뉴스/이슈는 번호 목록으로 정리하세요.
4. **경제 관점**: 서울경제 독자(30-60대 비즈니스 리더)에게 유용한 관점으로 해석하세요.""",
                'instruction': """## 응답 스타일
- 간결하고 명확하게 (문장당 50자 이내)
- 핵심 정보 먼저, 부가 설명 나중에
- 숫자와 데이터 강조
- 출처 명시 (필요시)

## 금지 사항
- ❌ "어떤 방향을 선택하시겠습니까?" 같은 선택 요청
- ❌ 사용자 입력을 "기사"로 인식하고 진단하기
- ❌ "개선 방향 1️⃣2️⃣3️⃣" 형식의 응답
- ❌ 불필요한 질문으로 대화 늘리기

## 응답 예시
사용자: "오늘의 이슈"
응답: "오늘(1월 24일) 주요 뉴스입니다:
1. **은값 100달러 돌파** - 역대 최고치 경신
2. **현대차 로봇 양산 발표** - 2026년 상용화 목표
3. **한은 성장률 하향** - 0.5%p 하향 조정..."

사용자에게 필요한 정보를 바로 제공하세요.""",
                'files': prompt_data_from_db.get('files', [])
            }

            logger.info(f"=== Prompt Data Loaded for {engine_type} ===")
            logger.info(f"AI Client: {ai_client.__class__.__name__}")

            # 웹 검색 수행 (web_search_enabled 파라미터 사용)
            self.last_web_search_result = None
            web_search_context = ""

            if web_search_enabled:
                logger.info(f"🔍 Web search ENABLED")
                try:
                    search_result = self.perplexity_client.search(user_message, enable=True)
                    if search_result and search_result.get('success'):
                        self.last_web_search_result = search_result  # 프론트엔드용 저장
                        web_search_context = search_result.get('content', '')  # content만 추출
                        citations_count = len(search_result.get('citations', []))
                        logger.info(f"✅ 웹검색 완료: {citations_count} 출처, content {len(web_search_context)} chars")
                    else:
                        self.last_web_search_result = {'success': False, 'citations': []}
                        logger.warning(f"⚠️ Web search returned no results")
                except Exception as e:
                    logger.error(f"❌ Web search failed: {str(e)}")
                    self.last_web_search_result = {'success': False, 'citations': []}

            # 웹 검색 결과를 메시지에 추가
            enhanced_message = user_message
            if web_search_context:
                enhanced_message = f"[최신 웹 검색 정보]\n{web_search_context}\n\n[사용자 질문]\n{user_message}"
                logger.info(f"📝 Enhanced message with web search context: {len(enhanced_message)} chars")

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
                    files=prompt_data.get('files', []),
                    selected_model=selected_model
                ):
                    # usage 정보인지 텍스트인지 구분
                    if isinstance(chunk, dict) and chunk.get('type') == 'usage':
                        self.last_usage_info = chunk
                        logger.info(f"📊 Captured usage info: {chunk}")
                    else:
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
                    files=prompt_data.get('files', []),
                    selected_model=selected_model
                ):
                    # usage 정보인지 텍스트인지 구분
                    if isinstance(chunk, dict) and chunk.get('type') == 'usage':
                        self.last_usage_info = chunk
                        logger.info(f"📊 Captured usage info (fallback): {chunk}")
                    else:
                        total_response += chunk
                        yield chunk

            # AI 응답 저장은 message.py에서 처리하므로 여기서는 제거
            # 중복 저장 방지를 위해 주석 처리
            logger.info(f"AI response completed: {len(total_response)} chars (저장은 message.py에서 처리)")

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
        output_text: str,
        actual_input_tokens: Optional[int] = None,
        actual_output_tokens: Optional[int] = None,
        cache_read_tokens: Optional[int] = None,
        cache_creation_tokens: Optional[int] = None,
        model_id: Optional[str] = None
    ) -> None:
        """
        사용량 추적 (캐시 메트릭 포함)

        Args:
            user_id: 사용자 ID
            engine_type: 엔진 타입
            input_text: 입력 텍스트 (폴백용)
            output_text: 출력 텍스트 (폴백용)
            actual_input_tokens: Bedrock에서 반환한 실제 입력 토큰 수
            actual_output_tokens: Bedrock에서 반환한 실제 출력 토큰 수
            cache_read_tokens: 캐시에서 읽은 토큰 수 (캐시 히트)
            cache_creation_tokens: 캐시에 생성된 토큰 수 (캐시 미스)
            model_id: 사용된 모델 ID
        """
        try:
            # 실제 토큰 수 사용, 없으면 추정치 사용
            if actual_input_tokens is not None:
                input_tokens = actual_input_tokens
                logger.info(f"📊 Using actual input tokens: {input_tokens}")
            else:
                input_tokens = len(input_text.split()) * 2  # 단어당 약 2토큰 추정
                logger.info(f"📊 Using estimated input tokens: {input_tokens}")

            if actual_output_tokens is not None:
                output_tokens = actual_output_tokens
                logger.info(f"📊 Using actual output tokens: {output_tokens}")
            else:
                output_tokens = len(output_text.split()) * 2
                logger.info(f"📊 Using estimated output tokens: {output_tokens}")

            # 캐시 토큰 정보
            cache_read = cache_read_tokens or 0
            cache_creation = cache_creation_tokens or 0

            logger.info(f"Usage tracked - User: {user_id}, Engine: {engine_type}")
            logger.info(f"Tokens - Input: {input_tokens}, Output: {output_tokens}")
            logger.info(f"📊 Cache - Read: {cache_read}, Creation: {cache_creation}")

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
                        cacheReadTokens :cacheRead,
                        cacheCreationTokens :cacheCreation,
                        messageCount :one
                    SET updatedAt = :timestamp,
                        lastUsedAt = :timestamp,
                        engineType = if_not_exists(engineType, :engineType),
                        usageDate = if_not_exists(usageDate, :usageDate),
                        lastModelId = :modelId
                """,
                ExpressionAttributeValues={
                    ':total': Decimal(str(input_tokens + output_tokens)),
                    ':input': Decimal(str(input_tokens)),
                    ':output': Decimal(str(output_tokens)),
                    ':cacheRead': Decimal(str(cache_read)),
                    ':cacheCreation': Decimal(str(cache_creation)),
                    ':one': Decimal('1'),
                    ':timestamp': datetime.utcnow().isoformat() + 'Z',
                    ':engineType': engine_type,
                    ':usageDate': today,
                    ':modelId': model_id or 'unknown'
                }
            )

            logger.info(f"Usage recorded in DynamoDB (cache_read={cache_read}, cache_creation={cache_creation})")

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