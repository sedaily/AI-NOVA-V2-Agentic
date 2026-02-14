"""
대화(Conversation) 도메인 모델
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class Message:
    """메시지 모델"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: Optional[str] = None
    type: Optional[str] = None  # 'user' or 'assistant' - 프론트엔드 호환성
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)


@dataclass
class Conversation:
    """대화 모델"""
    conversation_id: str
    user_id: str
    engine_type: str  # 'C1' or 'C2'
    title: Optional[str] = None
    messages: List[Message] = field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """DynamoDB 저장용 딕셔너리 변환"""
        return {
            'conversationId': self.conversation_id,
            'userId': self.user_id,
            'engineType': self.engine_type,
            'title': self.title,
            'messages': [
                {
                    'role': msg.role,
                    'type': msg.type or msg.role,  # type 필드 추가 (role과 동일)
                    'content': msg.content,
                    'timestamp': msg.timestamp,
                    'metadata': msg.metadata
                }
                for msg in self.messages
            ],
            'createdAt': self.created_at or datetime.now().isoformat(),
            'updatedAt': self.updated_at or datetime.now().isoformat(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """DynamoDB 데이터에서 모델 생성"""
        messages = [
            Message(
                role=msg['role'],
                content=msg['content'],
                timestamp=msg.get('timestamp'),
                type=msg.get('type', msg['role']),  # type 필드 추가
                metadata=msg.get('metadata', {})
            )
            for msg in data.get('messages', [])
        ]
        
        return cls(
            conversation_id=data['conversationId'],
            user_id=data['userId'],
            engine_type=data['engineType'],
            title=data.get('title'),
            messages=messages,
            created_at=data.get('createdAt'),
            updated_at=data.get('updatedAt'),
            metadata=data.get('metadata', {})
        )