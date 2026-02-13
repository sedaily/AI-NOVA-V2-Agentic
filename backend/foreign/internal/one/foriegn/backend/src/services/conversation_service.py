"""
대화(Conversation) 비즈니스 로직
"""
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from ..models import Conversation, Message
from ..repositories import ConversationRepository

logger = logging.getLogger(__name__)


class ConversationService:
    """대화 관련 비즈니스 로직"""
    
    def __init__(self, repository: Optional[ConversationRepository] = None):
        self.repository = repository or ConversationRepository()
    
    def create_conversation(
        self,
        user_id: str,
        engine_type: str,
        title: Optional[str] = None,
        initial_message: Optional[str] = None
    ) -> Conversation:
        """새 대화 생성"""
        try:
            # 대화 모델 생성
            conversation = Conversation(
                conversation_id='',  # 자동 생성
                user_id=user_id,
                engine_type=engine_type,
                title=title or f"새 대화 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            
            # 초기 메시지 추가
            if initial_message:
                message = Message(
                    role='user',
                    content=initial_message,
                    timestamp=datetime.now().isoformat()
                )
                conversation.messages.append(message)
            
            # 저장
            saved = self.repository.save(conversation)
            logger.info(f"Conversation created: {saved.conversation_id}")
            
            return saved
            
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            raise
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """대화 조회"""
        try:
            return self.repository.find_by_id(conversation_id)
        except Exception as e:
            logger.error(f"Error getting conversation: {str(e)}")
            raise
    
    def get_user_conversations(
        self,
        user_id: str,
        limit: int = 1000
    ) -> List[Conversation]:
        """사용자의 대화 목록 조회 - 모든 대화 반환"""
        try:
            return self.repository.find_by_user(user_id, limit)
        except Exception as e:
            logger.error(f"Error getting user conversations: {str(e)}")
            raise
    
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """대화에 메시지 추가"""
        try:
            # 기존 대화 조회
            conversation = self.repository.find_by_id(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation not found: {conversation_id}")
            
            # 새 메시지 생성
            message = Message(
                role=role,
                content=content,
                timestamp=datetime.now().isoformat(),
                metadata=metadata or {}
            )
            
            # 메시지 추가
            conversation.messages.append(message)
            
            # 업데이트
            return self.repository.update_messages(conversation_id, conversation.messages)
            
        except Exception as e:
            logger.error(f"Error adding message: {str(e)}")
            raise
    
    def update_title(self, conversation_id: str, title: str) -> bool:
        """대화 제목 업데이트"""
        try:
            logger.info(f"ConversationService.update_title called: {conversation_id} -> {title}")
            result = self.repository.update_title(conversation_id, title)
            logger.info(f"Repository update_title returned: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in ConversationService.update_title: {str(e)}")
            logger.error(f"Exception details: {type(e).__name__}: {str(e)}")
            raise
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """대화 삭제"""
        try:
            return self.repository.delete(conversation_id)
        except Exception as e:
            logger.error(f"Error deleting conversation: {str(e)}")
            raise
    
    def get_recent_conversations(
        self,
        user_id: str,
        engine_type: Optional[str] = None,
        days: int = 30
    ) -> List[Conversation]:
        """최근 대화 조회"""
        try:
            return self.repository.find_recent(user_id, engine_type, days)
        except Exception as e:
            logger.error(f"Error getting recent conversations: {str(e)}")
            raise
    
    def generate_title_from_messages(self, messages: List[Message]) -> str:
        """메시지 내용에서 제목 생성"""
        try:
            if not messages:
                return "새 대화"
            
            # 첫 사용자 메시지 찾기
            for message in messages:
                if message.role == 'user' and message.content:
                    # 첫 30자 + 요약
                    content = message.content.strip()
                    if len(content) > 30:
                        return content[:30] + "..."
                    return content
            
            return "새 대화"
            
        except Exception as e:
            logger.error(f"Error generating title: {str(e)}")
            return "새 대화"
    
    def validate_conversation_access(
        self,
        conversation_id: str,
        user_id: str
    ) -> bool:
        """대화 접근 권한 검증"""
        try:
            conversation = self.repository.find_by_id(conversation_id)
            if not conversation:
                return False
            
            return conversation.user_id == user_id
            
        except Exception as e:
            logger.error(f"Error validating access: {str(e)}")
            return False
    
    def get_conversation_statistics(self, user_id: str) -> Dict[str, Any]:
        """사용자의 대화 통계"""
        try:
            conversations = self.repository.find_by_user(user_id, limit=100)
            
            stats = {
                'total_conversations': len(conversations),
                'by_engine': {},
                'total_messages': 0,
                'avg_messages_per_conversation': 0
            }
            
            # 엔진별 집계
            for conv in conversations:
                engine = conv.engine_type
                if engine not in stats['by_engine']:
                    stats['by_engine'][engine] = 0
                stats['by_engine'][engine] += 1
                
                # 메시지 수 집계
                stats['total_messages'] += len(conv.messages)
            
            # 평균 계산
            if stats['total_conversations'] > 0:
                stats['avg_messages_per_conversation'] = (
                    stats['total_messages'] / stats['total_conversations']
                )
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            raise