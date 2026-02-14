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
        # AI 클라이언트 초기화 - Bedrock 전용 (2026-01 마이그레이션 완료)
        self.bedrock_client = BedrockClientEnhanced()
        self.ai_client = self.bedrock_client  # 호환성 유지
        self.ai_provider = 'bedrock'
        logger.info("🎯 AI Provider: AWS Bedrock (Prompt Caching Enabled)")

        self.conversation_manager = ConversationManager()
        self.prompts_table = prompts_table
        self.perplexity_client = PerplexityClient()

        # files 테이블 초기화
        self.files_table = dynamodb.Table('sedaily-column-files')
        logger.info("WebSocketService initialized")
    
    def process_message(
        self,
        user_message: str,
        engine_type: str,
        conversation_id: Optional[str],
        user_id: str,
        conversation_history: List[Dict],
        user_role: str = 'user',
        model_id: str = 'claude-opus-4-5-20251101'
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
        user_role: str = 'user',
        model_id: str = 'claude-opus-4-5-20251101',
        web_search_enabled: bool = True
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
            
            # 웹 검색 수행 (Perplexity API)
            self.last_web_search_result = None
            web_search_context = ""

            if web_search_enabled:
                logger.info(f"🔍 Performing web search via Perplexity for: {user_message[:100]}")
                try:
                    # search_for_context()를 사용하여 오늘 날짜가 포함된 시스템 프롬프트 적용
                    search_result = self.perplexity_client.search_for_context(user_message)
                    if search_result and search_result.get('success'):
                        self.last_web_search_result = search_result
                        web_search_context = search_result.get('content', '')
                        citations_count = len(search_result.get('citations', []))
                        logger.info(f"✅ 웹검색 완료: {citations_count} 출처")
                    else:
                        logger.warning("⚠️ Web search returned no results")
                        self.last_web_search_result = {'success': False, 'citations': []}
                except Exception as e:
                    logger.error(f"❌ Web search failed: {str(e)}")
                    self.last_web_search_result = {'success': False, 'citations': []}

            # Bedrock 클라이언트 사용
            logger.info(f"🤖 Using Bedrock client with engine {engine_type}, model {model_id}")

            total_response = ""
            self.last_usage_info = None

            # 웹 검색 결과를 프롬프트에 추가
            enhanced_message = user_message
            if web_search_context:
                enhanced_message = f"[최신 웹 검색 정보]\n{web_search_context}\n\n[사용자 질문]\n{user_message}"

            # 시스템 프롬프트 생성 - 정보 제공형 (하드코딩)
            system_prompt = """# 서울경제 AI 뉴스 어시스턴트

## 역할
당신은 서울경제신문의 AI 뉴스 어시스턴트입니다.
웹 검색 결과를 활용하여 사용자에게 최신 뉴스와 정보를 명확하고 구조적으로 전달합니다.

## 핵심 원칙
1. **정보 제공 중심**: 사용자의 질문에 직접 답변하세요. 진단이나 분석 요청을 하지 마세요.
2. **웹 검색 활용**: 제공된 웹 검색 결과를 바탕으로 최신 정보를 전달하세요.
3. **구조화된 응답**: 뉴스/이슈는 번호 목록으로 정리하세요.
4. **경제 관점**: 서울경제 독자(30-60대 비즈니스 리더)에게 유용한 관점으로 해석하세요.

## 응답 스타일
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
응답:
"오늘(1월 24일) 주요 뉴스입니다:

1. **은값 100달러 돌파** - 역대 최고치 경신, 금 대비 상승률 22%
2. **현대차 로봇 양산 발표** - 2026년 상용화 목표
3. **한은 성장률 하향** - 기존 2.1%에서 1.6%로 0.5%p 하향 조정
..."

사용자에게 필요한 정보를 바로 제공하세요."""

            # DynamoDB 프롬프트 파일이 있으면 추가 (선택적)
            if prompt_data.get('files'):
                for file_item in prompt_data.get('files', []):
                    if file_item.get('content'):
                        system_prompt += f"\n\n[참고 자료: {file_item.get('fileName', 'file')}]\n{file_item.get('content')}"

            # 스트리밍 응답 생성
            try:
                for chunk in self.bedrock_client.stream_response(
                    user_message=enhanced_message,
                    system_prompt=system_prompt,
                    conversation_context=formatted_history,
                    model_id=model_id  # 프론트엔드에서 선택한 모델 전달
                ):
                    # usage 정보인지 텍스트인지 구분
                    if isinstance(chunk, dict) and chunk.get('type') == 'usage':
                        self.last_usage_info = chunk
                        logger.info(f"📊 Captured usage info: {chunk}")
                    else:
                        yield chunk
                        total_response += chunk

            except Exception as e:
                logger.error(f"Bedrock error: {str(e)}")
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
                input_tokens = int(len(input_text.split()) * 1.3)
                logger.info(f"📊 Using estimated input tokens: {input_tokens}")

            if actual_output_tokens is not None:
                output_tokens = actual_output_tokens
                logger.info(f"📊 Using actual output tokens: {output_tokens}")
            else:
                output_tokens = int(len(output_text.split()) * 1.3)
                logger.info(f"📊 Using estimated output tokens: {output_tokens}")

            total_tokens = input_tokens + output_tokens
            cache_read = cache_read_tokens or 0
            cache_creation = cache_creation_tokens or 0

            logger.info(f"Usage tracked - User: {user_id}, Engine: {engine_type}")
            logger.info(f"Tokens - Input: {input_tokens}, Output: {output_tokens}")
            logger.info(f"📊 Cache - Read: {cache_read}, Creation: {cache_creation}")

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
                        cacheReadTokens = if_not_exists(cacheReadTokens, :zero) + :cacheRead,
                        cacheCreationTokens = if_not_exists(cacheCreationTokens, :zero) + :cacheCreation,
                        engineType = :engine,
                        usageDate = :date,
                        updatedAt = :now,
                        lastModelId = :modelId
                """,
                ExpressionAttributeValues={
                    ':zero': 0,
                    ':one': 1,
                    ':input': input_tokens,
                    ':output': output_tokens,
                    ':total': total_tokens,
                    ':cacheRead': cache_read,
                    ':cacheCreation': cache_creation,
                    ':engine': engine_type,
                    ':date': usage_date,
                    ':now': now.isoformat(),
                    ':modelId': model_id or 'unknown'
                }
            )

            logger.info(f"Usage tracked: {user_id}, {engine_type}, "
                       f"tokens={input_tokens}+{output_tokens}, cache_read={cache_read}")

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

