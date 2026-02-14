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
from lib.citation_formatter import CitationFormatter  # Citation Formatter 추가
from lib import web_search_client  # Tavily 웹검색 (모듈 레벨 함수)
from utils.logger import setup_logger

logger = setup_logger(__name__)

# 글로벌 캐시 - Lambda 컨테이너 재사용 시 유지됨 (영구 캐시)
PROMPT_CACHE: Dict[str, Dict[str, Any]] = {}

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
        # web_search_client는 모듈 레벨 함수 사용

        # files 테이블 초기화
        self.files_table = dynamodb.Table('sedaily-column-files')
        logger.info("WebSocketService initialized with Bedrock and Perplexity support")
    
    def process_message(
        self,
        user_message: str,
        engine_type: str,
        conversation_id: Optional[str],
        user_id: str,
        conversation_history: List[Dict],
        user_role: str = 'user',
        model_id: str = 'opus-4-20250514'
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

        캐시 히트 시 DB 조회를 생략하여 성능 향상
        Lambda 컨테이너 수명 동안 영구 유지
        """
        global PROMPT_CACHE

        # 캐시 확인 (영구 캐시 - TTL 없음)
        if engine_type in PROMPT_CACHE:
            logger.info(f"Cache HIT for {engine_type} - DB query skipped")
            return PROMPT_CACHE[engine_type]

        logger.info(f"Cache MISS for {engine_type} - fetching from DB")

        # 캐시 미스 - DB에서 로드
        prompt_data = self._fetch_prompt_from_db(engine_type)

        # 캐시 업데이트 (영구 저장)
        PROMPT_CACHE[engine_type] = prompt_data
        logger.info(f"Permanently cached prompt for {engine_type} "
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
        model_id: str = 'opus-4-20250514',
        web_search_enabled: bool = False
    ) -> Generator[str, None, None]:
        """
        Bedrock 스트리밍 응답 생성

        Yields:
            str: 응답 청크 또는 웹검색 결과 dict
        """
        try:
            # 대화 히스토리를 메시지 리스트로 준비 (캐싱용)
            messages_for_caching = self._prepare_messages_for_caching(conversation_history, user_message)
            logger.info(f"📋 Prepared {len(messages_for_caching)} messages for conversation caching")

            # DynamoDB에서 프롬프트 로드
            prompt_data = self._load_prompt_from_dynamodb(engine_type)
            logger.info(f"Loaded prompt for {engine_type}: instruction={len(prompt_data.get('instruction', ''))} chars, description={len(prompt_data.get('description', ''))} chars")
            logger.info(f"Prompt data content - Description: {prompt_data.get('description', '')[:100]}...")
            logger.info(f"Prompt data content - Instruction: {prompt_data.get('instruction', '')[:100]}...")

            logger.info(f"Streaming response for engine {engine_type}")
            logger.info(f"Conversation context: {len(messages_for_caching)} messages")

            # 🌐 Tavily 웹검색 (사용자 요청 시)
            web_context = ""
            if web_search_enabled:
                logger.info(f"🌐 Tavily web search enabled for: {user_message[:100]}")
                try:
                    search_result = web_search_client.search(user_message, max_results=5)
                    if search_result.get('success') and search_result.get('results'):
                        # 프론트엔드로 웹검색 결과 전송
                        yield {
                            'type': 'web_search_results',
                            'query': user_message,
                            'sources': search_result.get('results', [])
                        }
                        # AI 프롬프트에 웹검색 컨텍스트 추가
                        web_context = web_search_client.format_context(search_result)
                        logger.info(f"✅ Tavily search: '{user_message[:50]}' → {len(search_result.get('results', []))} results")
                except Exception as e:
                    logger.error(f"❌ Tavily search failed: {str(e)}")

            # 기존 웹 검색 활성화 여부 결정 (환경변수 기반)
            enable_native_web_search = os.environ.get('ENABLE_NATIVE_WEB_SEARCH', 'false').lower() == 'true'
            enable_perplexity_search = os.environ.get('ENABLE_WEB_SEARCH', 'false').lower() == 'true'

            # Perplexity를 통한 웹 검색 (기존 방식, 폴백용)
            web_search_result = None
            if enable_perplexity_search and not enable_native_web_search and not web_search_enabled:
                logger.info(f"🔍 Performing web search via Perplexity for: {user_message[:100]}")
                try:
                    web_search_result = self.perplexity_client.search(user_message)
                    if web_search_result:
                        logger.info(f"✅ Perplexity search completed: {len(web_search_result)} chars")
                    else:
                        logger.warning("⚠️ Perplexity search returned no results")
                except Exception as e:
                    logger.error(f"❌ Perplexity search failed: {str(e)}")
                    # 웹 검색 실패해도 계속 진행

            # Bedrock 클라이언트 사용
            logger.info(f"🤖 Using Bedrock client with engine {engine_type}")
            
            # 현재 날짜 로깅
            from datetime import datetime, timezone, timedelta
            kst = timezone(timedelta(hours=9))
            current_time = datetime.now(kst)
            logger.info(f"📅 Current date for response: {current_time.strftime('%Y-%m-%d %H:%M:%S KST')}")

            total_response = ""

            # 웹 검색 결과를 프롬프트에 추가 (Tavily 또는 Perplexity)
            enhanced_message = user_message
            if web_context:  # Tavily 웹검색 결과
                enhanced_message = f"[최신 웹 검색 정보 (Tavily)]\n{web_context}\n\n[사용자 질문]\n{user_message}"
            elif web_search_result:  # Perplexity 웹검색 결과
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

            # 스트리밍 응답 생성 (Bedrock 사용)
            try:
                # 대화 히스토리를 문자열로 변환 (Bedrock용)
                conversation_context = self._format_conversation_for_bedrock(conversation_history)

                # 웹 검색 결과가 있으면 메시지에 추가
                final_message = enhanced_message if (web_context or web_search_result) else user_message

                for chunk in self.bedrock_client.stream_bedrock(
                    user_message=final_message,
                    engine_type=engine_type,
                    conversation_context=conversation_context,
                    user_role=user_role,
                    instruction=prompt_data.get('instruction'),
                    description=prompt_data.get('description'),
                    files=prompt_data.get('files', [])
                ):
                    yield chunk
                    total_response += chunk

            except Exception as e:
                logger.error(f"Bedrock API error: {str(e)}")
                error_msg = f"⚠️ 응답 처리 중 오류가 발생했습니다: {str(e)}"
                yield error_msg
                total_response += error_msg
            

            # Citation 포맷팅 적용 (응답 완료 후)
            enable_citation = os.environ.get('ENABLE_CITATION_FORMATTING', 'true').lower() == 'true'
            if enable_citation and total_response and ("http" in total_response or web_search_result or web_context):
                try:
                    # 웹 검색 결과에서 출처 정보 추출
                    search_citations = []
                    if web_search_result:
                        search_citations = CitationFormatter.extract_citations_from_web_search(web_search_result)
                    
                    # Citation 포맷팅 적용
                    formatted_response = CitationFormatter.format_response_with_citations(
                        total_response, 
                        search_citations
                    )
                    
                    # 포맷팅이 적용된 경우에만 추가 청크 전송
                    if formatted_response != total_response:
                        citation_diff = formatted_response[len(total_response):]
                        if citation_diff:
                            yield citation_diff
                            total_response = formatted_response
                            logger.info("✅ Citation formatting applied")
                    
                except Exception as cite_error:
                    logger.error(f"Citation formatting error: {str(cite_error)}")
                    # Citation 오류는 무시하고 계속 진행
            
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
        model_id: str = None,
        input_tokens: int = None,
        output_tokens: int = None
    ) -> dict:
        """사용량 추적 + 크레딧 차감"""
        try:
            from handlers.api.usage import deduct_credits, get_user_credits

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
                'default': {'input': 4.5, 'output': 22.5}
            }
                'claude-opus-4-5-20251101': {'input': 7.5, 'output': 37.5},
                'claude-sonnet-4-5-20250929': {'input': 4.5, 'output': 22.5},
                'claude-haiku-4-5-20251001': {'input': 1.5, 'output': 7.5},
                'default': {'input': 4.5, 'output': 22.5}
            }
            rates = CREDIT_RATES.get(model_id, CREDIT_RATES['default'])
            credits_used = round((input_tokens / 1000) * rates['input'] + (output_tokens / 1000) * rates['output'], 2)

            # 현재 날짜 (YYYY-MM-DD)
            now = datetime.now()
            usage_date = now.strftime('%Y-%m-%d')
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
            캐싱 가능한 메시지 리스트
        """
        messages = []

        # 최근 10개 턴만 사용 (컨텍스트 관리)
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

        return messages

    def _validate_message_alternation(self, messages: List[Dict]) -> List[Dict]:
        """
        Anthropic API는 user/assistant 교대를 요구함
        연속된 같은 role이 있으면 placeholder 삽입
        """
        if not messages:
            return messages

        validated = []
        prev_role = None

        for msg in messages:
            current_role = msg.get('role')

            # 연속된 같은 role이면 placeholder 삽입
            if prev_role == current_role:
                if current_role == 'user':
                    validated.append({
                        'role': 'assistant',
                        'content': '(계속)'
                    })
                else:
                    validated.append({
                        'role': 'user',
                        'content': '(계속)'
                    })

            validated.append(msg)
            prev_role = current_role

        return validated

