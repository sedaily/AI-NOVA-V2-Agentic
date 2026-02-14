"""
WebSocket Service
WebSocket 메시지 처리 및 Bedrock 통합 서비스
"""
import json
import boto3
import logging
import time
import os
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional, Generator, Tuple
import uuid

from handlers.websocket.conversation_manager import ConversationManager
from lib.bedrock_client_enhanced import BedrockClientEnhanced
from lib.anthropic_client import AnthropicClient
from utils.logger import setup_logger

# RAG 기능 (선택적 import)
try:
    from lib.vector_search import get_vector_search
    RAG_AVAILABLE = True
    logger = setup_logger(__name__)
    logger.info("✅ RAG 모듈 로드 성공")
except ImportError as e:
    RAG_AVAILABLE = False
    logger = setup_logger(__name__)
    logger.warning(f"⚠️  RAG 모듈 없음: {str(e)}")

# DynamoDB 클라이언트
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
prompts_table = dynamodb.Table('nx-tt-dev-ver3-prompts')
usage_table = dynamodb.Table('nx-tt-dev-ver3-usage-tracking')

# 프롬프트 캐시 (Lambda 컨테이너 재사용 시 유지)
PROMPT_CACHE: Dict[str, Tuple[Dict[str, Any], float]] = {}
CACHE_TTL = 300  # 5분 (초 단위)


class WebSocketService:
    """WebSocket 메시지 처리 서비스"""

    # 토큰당 예상 비용 (USD)
    COST_PER_1K_INPUT_TOKENS = {
        'T5': Decimal('0.003'),
        'H8': Decimal('0.015')
    }
    COST_PER_1K_OUTPUT_TOKENS = {
        'T5': Decimal('0.015'),
        'H8': Decimal('0.075')
    }

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
        self.usage_table = usage_table
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
        DynamoDB에서 프롬프트와 파일 로드 (인메모리 캐싱 적용)

        캐싱 전략:
        - TTL: 5분 (관리자가 프롬프트 수정 시 최대 5분 후 반영)
        - Lambda 컨테이너 재사용 시 캐시 유지
        - 대량 문서 조회 비용 절감
        """
        global PROMPT_CACHE

        try:
            now = time.time()

            # 캐시 확인
            if engine_type in PROMPT_CACHE:
                cached_data, cached_time = PROMPT_CACHE[engine_type]
                age = now - cached_time

                if age < CACHE_TTL:
                    logger.info(f"✅ Cache HIT for {engine_type} (age: {age:.1f}s) - DB 조회 생략")
                    return cached_data
                else:
                    logger.info(f"⏰ Cache EXPIRED for {engine_type} (age: {age:.1f}s) - 재조회")
            else:
                logger.info(f"❌ Cache MISS for {engine_type} - 최초 조회")

            # 캐시 미스 또는 만료 - DB에서 로드
            prompt_data = self._fetch_prompt_from_db(engine_type)

            # 캐시 업데이트
            PROMPT_CACHE[engine_type] = (prompt_data, now)
            logger.info(f"💾 Cached prompt for {engine_type} "
                       f"({len(prompt_data.get('files', []))} files, "
                       f"{len(str(prompt_data))} bytes)")

            return prompt_data

        except Exception as e:
            logger.error(f"Error loading prompt: {str(e)}")
            return {'instruction': '', 'description': '', 'files': []}

    def _fetch_prompt_from_db(self, engine_type: str) -> Dict[str, Any]:
        """
        실제 DB 조회 로직 (캐싱 전용)
        캐시 미스 시에만 호출됨
        """
        try:
            start_time = time.time()

            # 프롬프트 테이블에서 기본 정보 로드
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
                    files_table = dynamodb.Table('nx-tt-dev-ver3-files')
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

                        elapsed = (time.time() - start_time) * 1000
                        logger.info(f"🔍 DB fetch for {engine_type}: "
                                  f"{len(prompt_data['files'])} files in {elapsed:.0f}ms")
                except Exception as fe:
                    logger.error(f"Error loading files: {str(fe)}")

                return prompt_data
            else:
                logger.warning(f"No prompt found for engine type: {engine_type}")
                return {'instruction': '', 'description': '', 'files': []}
        except Exception as e:
            logger.error(f"Error fetching from DB: {str(e)}")
            return {'instruction': '', 'description': '', 'files': []}

    def _create_rag_enhanced_prompt(
        self,
        user_message: str,
        engine_type: str
    ) -> Dict[str, Any]:
        """
        RAG로 관련 프롬프트 청크를 검색하여 동적으로 프롬프트 구성

        Args:
            user_message: 사용자 입력 (기사 내용)
            engine_type: 엔진 타입

        Returns:
            RAG로 구성된 프롬프트 데이터
        """
        if not RAG_AVAILABLE:
            logger.warning("⚠️  RAG 모듈 없음 - 기존 방식 사용")
            return self._load_prompt_from_dynamodb(engine_type)

        try:
            logger.info("🔍 RAG 모드: 벡터 검색 시작")

            # 1. 벡터 검색 수행
            vector_search = get_vector_search()
            relevant_chunks = vector_search.search_similar_chunks(
                query=user_message,
                top_k=int(os.environ.get('RAG_TOP_K', '10')),
                min_similarity=float(os.environ.get('RAG_MIN_SIMILARITY', '0.7'))
            )

            if not relevant_chunks:
                logger.warning("⚠️  RAG 검색 결과 없음 - 기본 프롬프트 사용")
                return self._load_prompt_from_dynamodb(engine_type)

            # 2. 검색 결과로 컨텍스트 구성
            max_rag_tokens = int(os.environ.get('RAG_MAX_TOKENS', '15000'))
            rag_context = vector_search.build_context_from_results(
                relevant_chunks,
                max_tokens=max_rag_tokens
            )

            # 3. 기본 instruction과 description은 유지 (코어 지침)
            base_prompt = self._load_prompt_from_dynamodb(engine_type)

            # 4. RAG 강화 프롬프트 구성
            rag_prompt_data = {
                'instruction': base_prompt.get('instruction', ''),
                'description': base_prompt.get('description', ''),
                'files': [
                    {
                        'fileName': 'rag_retrieved_context.txt',
                        'fileContent': rag_context,
                        'fileType': 'text'
                    }
                ]
            }

            logger.info(f"✅ RAG 프롬프트 구성 완료: {len(relevant_chunks)}개 청크")
            logger.info(f"   - Instruction: {len(rag_prompt_data['instruction'])} chars")
            logger.info(f"   - Description: {len(rag_prompt_data['description'])} chars")
            logger.info(f"   - RAG Context: ~{max_rag_tokens} tokens")

            return rag_prompt_data

        except Exception as e:
            logger.error(f"❌ RAG 프롬프트 생성 실패: {str(e)}")
            logger.info("🔄 Fallback: 기본 프롬프트 사용")
            return self._load_prompt_from_dynamodb(engine_type)
    
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

            # RAG 사용 여부 결정 (환경변수로 제어)
            use_rag = os.environ.get('USE_RAG', 'false').lower() == 'true'

            if use_rag and RAG_AVAILABLE:
                # RAG 방식: 동적 프롬프트 구성
                logger.info("📚 RAG 모드 활성화")
                prompt_data = self._create_rag_enhanced_prompt(
                    user_message=user_message,
                    engine_type=engine_type
                )
            else:
                # 기존 방식: 전체 프롬프트 캐싱
                logger.info("💾 캐시 모드 활성화")
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
                    
                    # 프롬프트와 대화 컨텍스트 결합
                    full_system_prompt = self._build_system_prompt(
                        guidelines=prompt_data.get('instruction', ''),
                        description=prompt_data.get('description', ''),
                        files=prompt_data.get('files', []),
                        conversation_context=formatted_history
                    )
                    
                    for chunk in self.ai_client.stream_response(
                        user_message=user_message,
                        system_prompt=full_system_prompt,
                        conversation_context=formatted_history
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
                for chunk in self.bedrock_client.stream_bedrock(
                    user_message=user_message,
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
            input_tokens = int(len(input_text.split()) * 1.3)
            output_tokens = int(len(output_text.split()) * 1.3)
            total_tokens = input_tokens + output_tokens

            # 현재 년월 (YYYY-MM)
            now = datetime.now()
            year_month = now.strftime('%Y-%m')

            # DynamoDB 키 (실제 테이블 구조에 맞춤)
            pk = f"user#{user_id}"
            sk = f"engine#{engine_type}#{year_month}"

            # 업데이트
            self.usage_table.update_item(
                Key={
                    'PK': pk,
                    'SK': sk
                },
                UpdateExpression="""
                    SET messageCount = if_not_exists(messageCount, :zero) + :one,
                        inputTokens = if_not_exists(inputTokens, :zero) + :input,
                        outputTokens = if_not_exists(outputTokens, :zero) + :output,
                        totalTokens = if_not_exists(totalTokens, :zero) + :total,
                        engineType = :engine,
                        userId = :userId,
                        yearMonth = :yearMonth,
                        updatedAt = :now,
                        lastUsedAt = :now
                """,
                ExpressionAttributeValues={
                    ':zero': 0,
                    ':one': 1,
                    ':input': input_tokens,
                    ':output': output_tokens,
                    ':total': total_tokens,
                    ':engine': engine_type,
                    ':userId': user_id,
                    ':yearMonth': year_month,
                    ':now': now.isoformat()
                }
            )

            logger.info(f"Usage tracked: {user_id}, {engine_type}, "
                       f"tokens={input_tokens}+{output_tokens}")

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
    
    def _build_system_prompt(
        self,
        guidelines: str,
        description: str,
        files: List[Dict],
        conversation_context: str
    ) -> str:
        """
        Anthropic API용 시스템 프롬프트 구성
        """
        prompt_parts = []
        
        # 기본 가이드라인
        if guidelines:
            prompt_parts.append(guidelines)
        
        # 설명 추가
        if description:
            prompt_parts.append(f"\n\n=== 추가 설명 ===\n{description}")
        
        # 파일 내용 추가
        if files:
            prompt_parts.append("\n\n=== 참고 문서 ===")
            for file in files:
                file_name = file.get('fileName', 'Unknown')
                file_content = file.get('fileContent', '')
                if file_content:
                    prompt_parts.append(f"\n[{file_name}]\n{file_content}")
        
        # 대화 컨텍스트 추가
        if conversation_context:
            prompt_parts.append(f"\n\n{conversation_context}")
        
        return "\n".join(prompt_parts)
    
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