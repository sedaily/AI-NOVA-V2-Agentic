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
from typing import List, Dict, Any, Optional, Generator, Tuple
import uuid
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config.aws import AWS_REGION, DYNAMODB_TABLES

from handlers.websocket.conversation_manager import ConversationManager
from lib.bedrock_client_enhanced import BedrockClientEnhanced
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


class WebSocketService:
    """WebSocket 메시지 처리 서비스"""

    def __init__(self):
        self.bedrock_client = BedrockClientEnhanced()
        self.conversation_manager = ConversationManager()
        self.prompts_table = prompts_table
        self.files_table = files_table
        self.perplexity_client = PerplexityClient()  # Perplexity 추가
        logger.info("WebSocketService initialized with Perplexity support")

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
        DynamoDB에서 프롬프트와 파일 로드 (인메모리 캐싱 적용)

        캐시 히트 시 DB 조회를 생략하여 성능 향상
        """
        global PROMPT_CACHE
        now = time.time()

        # 캐시 확인
        if engine_type in PROMPT_CACHE:
            cached_data, cached_time = PROMPT_CACHE[engine_type]
            age = now - cached_time

            if age < CACHE_TTL:
                logger.info(f"✅ Cache HIT for {engine_type} (age: {age:.1f}s) - DB query skipped")
                return cached_data
            else:
                logger.info(f"⏰ Cache EXPIRED for {engine_type} (age: {age:.1f}s) - refetching")
        else:
            logger.info(f"❌ Cache MISS for {engine_type} - initial fetch")

        # 캐시 미스 또는 만료 - DB에서 로드
        prompt_data = self._fetch_prompt_from_db(engine_type)

        # 캐시 업데이트
        PROMPT_CACHE[engine_type] = (prompt_data, now)
        logger.info(f"💾 Cached prompt for {engine_type} "
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
                    # p2-two-files-two 테이블은 전체 스캔 (현재 파일이 1개만 있음)
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
                logger.info(f"🔍 DB fetch for {engine_type}: "
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
        user_role: str = 'user'
    ) -> Generator[str, None, None]:
        """
        Bedrock 스트리밍 응답 생성

        Yields:
            str: 응답 청크
        """
        try:
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
            
            # 웹 검색 수행 (옵션)
            web_search_result = None
            # 두 가지 환경변수명 모두 확인 (호환성)
            enable_search_env = os.environ.get('ENABLE_WEB_SEARCH', os.environ.get('ENABLE_NEWS_SEARCH', 'false'))
            enable_search = enable_search_env.lower() == 'true'
            
            logger.info(f"Web search config - ENABLE_WEB_SEARCH: {os.environ.get('ENABLE_WEB_SEARCH')}, ENABLE_NEWS_SEARCH: {os.environ.get('ENABLE_NEWS_SEARCH')}, Final: {enable_search}")
            
            if enable_search:
                logger.info(f"🔍 Web search ENABLED - Searching for: {user_message[:100]}")
                try:
                    web_search_result = self.perplexity_client.search(user_message, enable=True)
                    if web_search_result:
                        logger.info(f"✅ Web search completed: {len(web_search_result)} chars")
                        logger.info(f"Search result sample: {web_search_result[:300]}...")
                    else:
                        logger.warning("⚠️ Web search returned no results")
                except Exception as e:
                    logger.error(f"❌ Web search failed with exception: {str(e)}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    # 웹 검색 실패해도 계속 진행
            else:
                logger.info(f"🔍 Web search DISABLED - Skipping Perplexity search")

            # Bedrock 스트리밍 호출
            total_response = ""
            
            # 웹 검색 결과를 프롬프트에 추가
            enhanced_message = user_message
            if web_search_result:
                enhanced_message = f"[최신 웹 검색 정보]\n{web_search_result}\n\n[사용자 질문]\n{user_message}"
            
            for chunk in self.bedrock_client.stream_bedrock(
                user_message=enhanced_message,  # 웹 검색 결과가 포함된 메시지
                engine_type=engine_type,
                conversation_context=formatted_history,  # 대화 컨텍스트 전달
                user_role=user_role,
                guidelines=prompt_data.get('instruction'),  # DynamoDB instruction 전달
                description=prompt_data.get('description'),  # DynamoDB description 전달
                files=prompt_data.get('files', [])  # DynamoDB files 전달
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

            # date 키 생성 (테이블 스키마: userId, date)
            date_key = f"{today}#{engine_type}"

            # 원자적 업데이트로 사용량 증가
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
                    ':timestamp': datetime.now().isoformat(),
                    ':engineType': engine_type,
                    ':usageDate': today
                }
            )

            logger.info(f"Usage saved to DynamoDB - Table: {usage_table.name}, userId: {user_id}, date: {date_key}")

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
        Bedrock에 전달할 대화 컨텍스트 포맷팅 - 선택지 매핑 개선
        """
        if not conversation_history:
            return ""

        formatted_messages = []
        last_ai_message = None
        
        for msg in conversation_history[-10:]:  # 최근 10개 메시지만 사용 #대화기억기능
            role = msg.get('role', 'user')
            content = msg.get('content', '')

            if content:
                if role == 'user':
                    formatted_messages.append(f"사용자: {content}")
                elif role == 'assistant':
                    formatted_messages.append(f"AI: {content}")
                    last_ai_message = content  # 마지막 AI 메시지 저장

        if formatted_messages:
            context = "\n\n=== 이전 대화 내용 ===\n" + "\n\n".join(formatted_messages) + "\n\n=== 현재 질문 ==="
            
            # 마지막 AI 메시지에 선택지가 있는지 확인
            if last_ai_message and self._has_numbered_options(last_ai_message):
                context += f"\n\n⚠️ 중요: 바로 위 AI 응답에서 번호 선택지를 제시했습니다. 사용자가 단순히 숫자만 입력하면 해당 번호의 작업을 바로 실행하세요. 새로운 선택지를 제시하지 마세요."
            
            return context

        return ""
    
    def _has_numbered_options(self, text: str) -> bool:
        """텍스트에 번호 선택지가 있는지 확인"""
        import re
        # "1.", "2.", "3." 등의 패턴이나 "1. ", "2. " 패턴 찾기
        numbered_pattern = r'(?:^|\n)\s*[1-9]\.\s+'
        return bool(re.search(numbered_pattern, text, re.MULTILINE))