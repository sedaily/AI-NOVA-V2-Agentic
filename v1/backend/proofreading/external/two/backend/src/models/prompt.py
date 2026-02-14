"""
프롬프트(Prompt) 도메인 모델
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime


@dataclass
class PromptFile:
    """프롬프트 파일 모델"""
    file_name: str
    file_content: str
    file_type: str = 'text'
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)


@dataclass 
class PromptConfig:
    """프롬프트 설정 모델"""
    description: str
    instruction: str
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)


@dataclass
class Prompt:
    """프롬프트 모델"""
    prompt_id: str
    user_id: str
    engine_type: str  # 'T5' or 'H8'
    prompt_name: str
    prompt: PromptConfig
    files: List[PromptFile] = field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    is_public: bool = False
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """DynamoDB 저장용 딕셔너리 변환"""
        return {
            'promptId': self.prompt_id,
            'userId': self.user_id,
            'engineType': self.engine_type,
            'promptName': self.prompt_name,
            'prompt': {
                'description': self.prompt.description,
                'instruction': self.prompt.instruction,
                'metadata': self.prompt.metadata
            },
            'files': [
                {
                    'fileName': f.file_name,
                    'fileContent': f.file_content,
                    'fileType': f.file_type,
                    'metadata': f.metadata
                }
                for f in self.files
            ],
            'createdAt': self.created_at or datetime.now().isoformat(),
            'updatedAt': self.updated_at or datetime.now().isoformat(),
            'isPublic': self.is_public,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Prompt':
        """DynamoDB 데이터에서 모델 생성"""
        prompt_config = PromptConfig(
            description=data['prompt'].get('description', ''),
            instruction=data['prompt'].get('instruction', ''),
            metadata=data['prompt'].get('metadata', {})
        )
        
        files = [
            PromptFile(
                file_name=f.get('fileName', ''),
                file_content=f.get('fileContent', ''),
                file_type=f.get('fileType', 'text'),
                metadata=f.get('metadata', {})
            )
            for f in data.get('files', [])
        ]
        
        return cls(
            prompt_id=data['promptId'],
            user_id=data['userId'],
            engine_type=data['engineType'],
            prompt_name=data['promptName'],
            prompt=prompt_config,
            files=files,
            created_at=data.get('createdAt'),
            updated_at=data.get('updatedAt'),
            is_public=data.get('isPublic', False),
            metadata=data.get('metadata', {})
        )