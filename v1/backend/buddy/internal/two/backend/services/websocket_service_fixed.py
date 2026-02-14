"""
WebSocket Service - Fixed Version
프롬프트와 파일 테이블 조회 로직 수정
"""
import json
import boto3
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Generator
import uuid
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config.aws import AWS_REGION, DYNAMODB_TABLES

from handlers.websocket.conversation_manager import ConversationManager
from lib.bedrock_client_enhanced import BedrockClientEnhanced

logger = logging.getLogger(__name__)

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
        logger.info("WebSocketService initialized with fixed table references")

    def _load_prompt_from_dynamodb(self, engine_type: str) -> Dict[str, Any]:
        """DynamoDB에서 프롬프트와 파일 로드 (수정된 버전)"""
        try:
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

                logger.info(f"Loaded prompt for {engine_type}: instruction={len(prompt_data.get('instruction', ''))} chars, description={len(prompt_data.get('description', ''))} chars")

                # files 테이블에서 관련 파일들 로드
                try:
                    # p2-two-files-two 테이블은 fileId가 파티션 키일 가능성이 높음
                    # 전체 스캔 대신 GSI를 사용하거나, 파일 ID 목록을 프롬프트에 저장하는 방식 권장
                    files_response = self.files_table.scan()

                    if 'Items' in files_response:
                        # 파일이 있는 경우 (현재는 1개만 있음)
                        for file_item in files_response['Items']:
                            prompt_data['files'].append({
                                'fileName': file_item.get('fileName', ''),
                                'fileContent': file_item.get('fileContent', ''),
                                'fileType': 'text'
                            })
                        logger.info(f"Loaded {len(prompt_data['files'])} files for {engine_type}")

                        # 파일 내용 로그 (디버깅용)
                        for idx, file in enumerate(prompt_data['files']):
                            logger.info(f"File {idx}: {file['fileName']}, size={len(file.get('fileContent', ''))} chars")

                except Exception as fe:
                    logger.error(f"Error loading files from {FILES_TABLE_NAME}: {str(fe)}")

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
        Bedrock 스트리밍 응답 생성 (개선된 버전)

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

            # 파일 내용 결합
            combined_files_content = ""
            if prompt_data.get('files'):
                for file in prompt_data['files']:
                    combined_files_content += f"\n\n--- File: {file.get('fileName', 'unnamed')} ---\n"
                    combined_files_content += file.get('fileContent', '')
                logger.info(f"Combined files content: {len(combined_files_content)} chars")

            logger.info(f"Streaming response for engine {engine_type}")
            logger.info(f"Conversation context: {len(formatted_history)} messages")

            # Bedrock 스트리밍 호출
            total_response = ""
            for chunk in self.bedrock_client.stream_bedrock(
                user_message=user_message,
                engine_type=engine_type,
                conversation_context=formatted_history,
                user_role=user_role,
                guidelines=prompt_data.get('instruction'),  # instruction 필드 전달
                description=prompt_data.get('description'),  # description 필드 전달
                files=prompt_data.get('files', [])  # files 리스트 전달
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

    # 나머지 메서드들은 기존과 동일...
    def process_message(
        self,
        user_message: str,
        engine_type: str,
        conversation_id: Optional[str],
        user_id: str,
        conversation_history: List[Dict],
        user_role: str = 'user'
    ) -> Dict[str, Any]:
        """메시지 처리 및 대화 히스토리 병합"""
        try:
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
                logger.info(f"New conversation created: {conversation_id}")

            db_history = self.conversation_manager.get_conversation_history(
                conversation_id,
                limit=20
            )

            merged_history = self._merge_conversation_history(
                client_history=conversation_history,
                db_history=db_history
            )

            self.conversation_manager.save_message(
                conversation_id=conversation_id,
                role='user',
                content=user_message,
                engine_type=engine_type,
                user_id=user_id
            )

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

    def _format_conversation_for_bedrock(self, conversation_history: List[Dict]) -> List[Dict]:
        """Bedrock 형식으로 대화 히스토리 포맷"""
        formatted = []
        for msg in conversation_history:
            formatted.append({
                'role': msg.get('role', 'user'),
                'content': msg.get('content', '')
            })
        return formatted

    def _merge_conversation_history(
        self,
        client_history: List[Dict],
        db_history: List[Dict]
    ) -> List[Dict]:
        """클라이언트와 DB의 대화 히스토리 병합"""
        merged = []

        for msg in db_history:
            merged.append({
                'role': msg.get('role', msg.get('type', 'user')),
                'content': msg.get('content', ''),
                'timestamp': msg.get('timestamp', '')
            })

        db_timestamps = {msg.get('timestamp') for msg in db_history if msg.get('timestamp')}

        for msg in client_history:
            if msg.get('timestamp') and msg['timestamp'] not in db_timestamps:
                merged.append({
                    'role': msg.get('role', 'user'),
                    'content': msg.get('content', ''),
                    'timestamp': msg.get('timestamp', '')
                })

        return merged

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
            input_tokens = len(input_text.split())
            output_tokens = len(output_text.split())

            logger.info(f"Usage tracked - User: {user_id}, Engine: {engine_type}")
            logger.info(f"Tokens - Input: {input_tokens}, Output: {output_tokens}")

        except Exception as e:
            logger.error(f"Error tracking usage: {str(e)}")