"""
WebSocket 서비스 - 완성 버전 (Prompt Caching 적용)
우수사례 코드를 참고하여 프롬프트 로드 기능 추가
애플리케이션 레벨 캐싱으로 DynamoDB 조회 최소화
"""
import os
import sys
import json
import boto3
import logging
import time
from typing import Dict, List, Generator, Optional, Any, Tuple
from datetime import datetime, timezone
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config.aws import AWS_REGION, DYNAMODB_TABLES
from lib.bedrock_client_enhanced import BedrockClientEnhanced
from lib.anthropic_client import AnthropicClient
from utils.logger import setup_logger

logger = setup_logger(__name__)

# 글로벌 캐시 - Lambda 컨테이너 재사용 시 유지됨
PROMPT_CACHE: Dict[str, Tuple[Dict[str, Any], float]] = {}
CACHE_TTL = 300  # 5분 (초 단위)

class WebSocketService:
    """WebSocket 통신 서비스"""
    
    def __init__(self):
        # AWS 리소스 초기화
        self.dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
        self.conversations_table = self.dynamodb.Table(DYNAMODB_TABLES['conversations'])
        self.prompts_table = self.dynamodb.Table(DYNAMODB_TABLES['prompts'])
        self.usage_table = self.dynamodb.Table(DYNAMODB_TABLES['usage'])
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
            
            # DynamoDB에서 프롬프트와 파일 통합 로드
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
        output_text: str
    ) -> None:
        """
        사용량 추적
        """
        try:
            # 토큰 수 추정 (대략적인 계산)
            input_tokens = len(input_text.split()) * 2
            output_tokens = len(output_text.split()) * 2
            
            # 사용량 기록
            year_month = datetime.now(timezone.utc).strftime('%Y-%m')

            # 원자적 업데이트
            self.usage_table.update_item(
                Key={
                    'userId': user_id,
                    'yearMonth': year_month
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
                    ':total': input_tokens + output_tokens,
                    ':engine': engine_type,
                    ':now': datetime.now(timezone.utc).isoformat()
                }
            )
            
            logger.info(f"Usage tracked for {user_id}: {input_tokens} + {output_tokens} tokens")
            
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
                role_label = "사용자" if role == 'user' else "AI"
                formatted_messages.append(f"{role_label}: {content}")
        
        if formatted_messages:
            return "\n\n=== 이전 대화 내용 ===\n" + "\n\n".join(formatted_messages) + "\n\n=== 현재 질문 ==="
        
        return ""