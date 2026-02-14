"""
WebSocket Service
WebSocket 메시지 처리 및 Bedrock 통합 서비스
"""
import json
import boto3
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Generator
import uuid
import os
import re

from handlers.websocket.conversation_manager import ConversationManager
from lib.bedrock_client_enhanced import BedrockClientEnhanced

logger = logging.getLogger(__name__)

# DynamoDB 클라이언트 - 프롬프트 테이블 접근용
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
prompts_table = dynamodb.Table(os.environ.get('PROMPTS_TABLE', 'tem1-prompts-v2'))


class WebSocketService:
    """WebSocket 메시지 처리 서비스"""

    def __init__(self):
        # 기존 컴포넌트 유지
        self.bedrock_client = BedrockClientEnhanced()
        self.conversation_manager = ConversationManager()
        self.prompts_table = prompts_table


        # files 테이블 초기화
        self.files_table = dynamodb.Table(os.environ.get('FILES_TABLE', 'tem1-files'))
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
        """DynamoDB에서 프롬프트 및 파일 로드"""
        try:
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
                    logger.info(f"Loaded {len(files)} files for {engine_type}")

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
                        logger.info(f"Loaded {len(files)} files for {engine_type} (via scan)")

                    except Exception as scan_error:
                        logger.error(f"Error scanning files for {engine_type}: {str(scan_error)}")

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

            # 기본 Bedrock 클라이언트 사용
            logger.info(f"🤖 Using Bedrock client with engine {engine_type}")

            total_response = ""


            # 스트리밍 응답 생성
            try:
                for chunk in self.bedrock_client.stream_bedrock(
                    user_message=user_message,
                    engine_type=engine_type,
                    conversation_context=formatted_history,
                    user_role=user_role,
                    guidelines=prompt_data.get('instruction'),
                    description=prompt_data.get('description'),  # description 추가!
                    files=prompt_data.get('files', [])  # 실제 파일도 전달
                ):
                    yield chunk
                    total_response += chunk

            except Exception as e:
                logger.error(f"Bedrock client error: {str(e)}")
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
            input_tokens = len(input_text.split())
            output_tokens = len(output_text.split())
            
            logger.info(f"Usage tracked - User: {user_id}, Engine: {engine_type}")
            logger.info(f"Tokens - Input: {input_tokens}, Output: {output_tokens}")
            
            # TODO: DynamoDB에 사용량 저장
            
        except Exception as e:
            logger.error(f"Error tracking usage: {str(e)}")
    
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

