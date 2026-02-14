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
import re

from handlers.websocket.conversation_manager import ConversationManager
from lib.bedrock_client_enhanced import BedrockClientEnhanced
from lib.anthropic_client import AnthropicClient  # Anthropic API 클라이언트 추가
from lib.perplexity_client import PerplexityClient
from utils.logger import setup_logger

logger = setup_logger(__name__)

# 글로벌 캐시 - Lambda 컨테이너 재사용 시 유지됨
PROMPT_CACHE: Dict[str, Tuple[Dict[str, Any], float]] = {}
CACHE_TTL = 300  # 5분 (초 단위)

# DynamoDB 클라이언트 - 프롬프트 테이블 접근용
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
prompts_table = dynamodb.Table('sedaily-column-prompts')


class WebSocketService:
    """WebSocket 메시지 처리 서비스"""

    def __init__(self):
        # 기존 컴포넌트 유지
        self.bedrock_client = BedrockClientEnhanced()
        self.anthropic_client = AnthropicClient()  # Anthropic API 클라이언트
        self.conversation_manager = ConversationManager()
        self.prompts_table = prompts_table
        self.perplexity_client = PerplexityClient()  # Perplexity 추가


        # files 테이블 초기화
        self.files_table = dynamodb.Table('sedaily-column-files')
        logger.info("WebSocketService initialized with Anthropic and Perplexity support")
    
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
                logger.info(f"Cache HIT for {engine_type} (age: {age:.1f}s) - DB query skipped")
                return cached_data
            else:
                logger.info(f"Cache EXPIRED for {engine_type} (age: {age:.1f}s) - refetching")
        else:
            logger.info(f"Cache MISS for {engine_type} - initial fetch")

        # 캐시 미스 또는 만료 - DB에서 로드
        prompt_data = self._fetch_prompt_from_db(engine_type)

        # 캐시 업데이트
        PROMPT_CACHE[engine_type] = (prompt_data, now)
        logger.info(f"Cached prompt for {engine_type} "
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

            # 프롬프트 정보 로드
            response = self.prompts_table.get_item(Key={'promptId': engine_type})
            if 'Item' in response:
                item = response['Item']
                prompt_data = {
                    'instruction': item.get('instruction', ''),
                    'description': item.get('description', ''),
                    'files': []
                }

                # files 테이블에서 해당 promptId의 파일들 로드
                try:
                    files_response = self.files_table.query(
                        IndexName='promptId-index',
                        KeyConditionExpression='promptId = :promptId',
                        ExpressionAttributeValues={':promptId': engine_type}
                    )

                    files = []
                    for file_item in files_response.get('Items', []):
                        files.append({
                            'fileName': file_item.get('fileName', ''),
                            'fileContent': file_item.get('fileContent', ''),
                            'fileSize': file_item.get('fileSize', 0)
                        })

                    prompt_data['files'] = files

                except Exception as file_error:
                    logger.warning(f"Error loading files for {engine_type}: {str(file_error)}")
                    # files 테이블 오류 시 GSI 없이 scan으로 시도
                    try:
                        files_response = self.files_table.scan(
                            FilterExpression='promptId = :promptId',
                            ExpressionAttributeValues={':promptId': engine_type}
                        )

                        files = []
                        for file_item in files_response.get('Items', []):
                            files.append({
                                'fileName': file_item.get('fileName', ''),
                                'fileContent': file_item.get('fileContent', ''),
                                'fileSize': file_item.get('fileSize', 0)
                            })

                        prompt_data['files'] = files

                    except Exception as scan_error:
                        logger.error(f"Error scanning files for {engine_type}: {str(scan_error)}")

                elapsed = (time.time() - start_time) * 1000
                logger.info(f"DB fetch for {engine_type}: "
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

            # DynamoDB에서 프롬프트 로드
            prompt_data = self._load_prompt_from_dynamodb(engine_type)
            logger.info(f"Loaded prompt for {engine_type}: instruction={len(prompt_data.get('instruction', ''))} chars, description={len(prompt_data.get('description', ''))} chars")
            logger.info(f"Prompt data content - Description: {prompt_data.get('description', '')[:100]}...")
            logger.info(f"Prompt data content - Instruction: {prompt_data.get('instruction', '')[:100]}...")

            logger.info(f"Streaming response for engine {engine_type}")
            logger.info(f"Conversation context: {len(formatted_history)} messages")
            
            # 웹 검색 수행 (옵션)
            web_search_result = None
            enable_search = os.environ.get('ENABLE_WEB_SEARCH', 'false').lower() == 'true'
            
            if enable_search:
                logger.info(f"🔍 Performing web search via Perplexity for: {user_message[:100]}")
                try:
                    web_search_result = self.perplexity_client.search(user_message)
                    if web_search_result:
                        logger.info(f"✅ Web search completed: {len(web_search_result)} chars")
                    else:
                        logger.warning("⚠️ Web search returned no results")
                except Exception as e:
                    logger.error(f"❌ Web search failed: {str(e)}")
                    # 웹 검색 실패해도 계속 진행

            # Anthropic API 클라이언트 사용
            logger.info(f"🤖 Using Anthropic API client with engine {engine_type}")

            total_response = ""

            # 웹 검색 결과를 프롬프트에 추가
            enhanced_message = user_message
            if web_search_result:
                enhanced_message = f"[최신 웹 검색 정보]\n{web_search_result}\n\n[사용자 질문]\n{user_message}"

            # 시스템 프롬프트 생성
            system_prompt_parts = []
            if prompt_data.get('description'):
                system_prompt_parts.append(prompt_data.get('description'))
            if prompt_data.get('instruction'):
                system_prompt_parts.append(prompt_data.get('instruction'))
            if prompt_data.get('files'):
                # 파일 내용을 시스템 프롬프트에 포함
                for file_item in prompt_data.get('files', []):
                    if file_item.get('content'):
                        system_prompt_parts.append(f"[참고 자료: {file_item.get('fileName', 'file')}]\n{file_item.get('content')}")
            
            system_prompt = "\n\n".join(system_prompt_parts)

            # 스트리밍 응답 생성
            try:
                for chunk in self.anthropic_client.stream_response(
                    user_message=enhanced_message,  # 웹 검색 결과가 포함된 메시지
                    system_prompt=system_prompt,
                    conversation_context=formatted_history
                ):
                    yield chunk
                    total_response += chunk

            except Exception as e:
                logger.error(f"Anthropic API error: {str(e)}")
                error_msg = f"⚠️ 응답 처리 중 오류가 발생했습니다: {str(e)}"
                yield error_msg
                total_response += error_msg
            
            # AI 응답을 대화에 저장
            if total_response:
                self.conversation_manager.save_message(
                    conversation_id=conversation_id,
                    role='assistant',
                    content=total_response,
                    engine_type=engine_type,
                    user_id=user_id
                )
                logger.info(f"Response saved: {len(total_response)} chars")
            
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

            # 현재 날짜 (YYYY-MM-DD)
            now = datetime.now()
            usage_date = now.strftime('%Y-%m-%d')

            # DynamoDB 키
            sort_key = f"{usage_date}#{engine_type}"

            # usage 테이블
            usage_table = dynamodb.Table('sedaily-column-usage')

            # 업데이트
            usage_table.update_item(
                Key={
                    'userId': user_id,
                    'usageDate#engineType': sort_key
                },
                UpdateExpression="""
                    SET requestCount = if_not_exists(requestCount, :zero) + :one,
                        totalInputTokens = if_not_exists(totalInputTokens, :zero) + :input,
                        totalOutputTokens = if_not_exists(totalOutputTokens, :zero) + :output,
                        totalTokens = if_not_exists(totalTokens, :zero) + :total,
                        engineType = :engine,
                        usageDate = :date,
                        updatedAt = :now
                """,
                ExpressionAttributeValues={
                    ':zero': 0,
                    ':one': 1,
                    ':input': input_tokens,
                    ':output': output_tokens,
                    ':total': total_tokens,
                    ':engine': engine_type,
                    ':date': usage_date,
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

