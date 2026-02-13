"""
프롬프트(Prompt) 리포지토리
DynamoDB와의 모든 상호작용을 캡슐화
"""
import boto3
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import logging
import os

from ..models import Prompt, PromptConfig, PromptFile

logger = logging.getLogger(__name__)


class PromptRepository:
    """프롬프트 데이터 접근 계층"""

    def __init__(self, table_name: str = None, region: str = None):
        table_name = table_name or os.environ.get('PROMPTS_TABLE', 'f1-prompts-two')
        region = region or os.environ.get('AWS_REGION', 'us-east-1')
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = self.dynamodb.Table(table_name)
        logger.info(f"PromptRepository initialized with table: {table_name}")
    
    def save(self, prompt: Prompt) -> Prompt:
        """프롬프트 저장"""
        try:
            # ID가 없으면 생성
            if not prompt.prompt_id:
                prompt.prompt_id = str(uuid.uuid4())
            
            # 타임스탬프 업데이트
            now = datetime.now().isoformat()
            if not prompt.created_at:
                prompt.created_at = now
            prompt.updated_at = now
            
            # DynamoDB에 저장
            self.table.put_item(Item=prompt.to_dict())
            
            logger.info(f"Prompt saved: {prompt.prompt_id}")
            return prompt
            
        except Exception as e:
            logger.error(f"Error saving prompt: {str(e)}")
            raise
    
    def find_by_id(self, prompt_id: str) -> Optional[Prompt]:
        """ID로 프롬프트 조회"""
        try:
            response = self.table.get_item(
                Key={'promptId': prompt_id}
            )
            
            if 'Item' in response:
                return Prompt.from_dict(response['Item'])
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding prompt by id: {str(e)}")
            raise
    
    def find_by_user(self, user_id: str, engine_type: Optional[str] = None) -> List[Prompt]:
        """사용자별 프롬프트 목록 조회"""
        try:
            filter_expression = None
            expression_values = {':userId': user_id}
            
            if engine_type:
                filter_expression = 'engineType = :engineType'
                expression_values[':engineType'] = engine_type
            
            # prompts 테이블에는 GSI가 없으므로 scan 사용
            scan_filter = 'userId = :userId'
            if filter_expression:
                scan_filter += f' AND {filter_expression}'
            
            response = self.table.scan(
                FilterExpression=scan_filter,
                ExpressionAttributeValues=expression_values
            )
            
            prompts = []
            for item in response.get('Items', []):
                prompts.append(Prompt.from_dict(item))
            
            return prompts
            
        except Exception as e:
            logger.error(f"Error finding prompts by user: {str(e)}")
            raise
    
    def find_public(self, engine_type: Optional[str] = None, limit: int = 50) -> List[Prompt]:
        """공개 프롬프트 조회"""
        try:
            filter_expression = 'isPublic = :isPublic'
            expression_values = {':isPublic': True}
            
            if engine_type:
                filter_expression += ' AND engineType = :engineType'
                expression_values[':engineType'] = engine_type
            
            response = self.table.scan(
                FilterExpression=filter_expression,
                ExpressionAttributeValues=expression_values,
                Limit=limit
            )
            
            prompts = []
            for item in response.get('Items', []):
                prompts.append(Prompt.from_dict(item))
            
            return prompts
            
        except Exception as e:
            logger.error(f"Error finding public prompts: {str(e)}")
            raise
    
    def update(self, prompt: Prompt) -> Prompt:
        """프롬프트 업데이트"""
        try:
            prompt.updated_at = datetime.now().isoformat()
            
            self.table.put_item(Item=prompt.to_dict())
            
            logger.info(f"Prompt updated: {prompt.prompt_id}")
            return prompt
            
        except Exception as e:
            logger.error(f"Error updating prompt: {str(e)}")
            raise
    
    def delete(self, prompt_id: str) -> bool:
        """프롬프트 삭제"""
        try:
            self.table.delete_item(
                Key={'promptId': prompt_id}
            )
            
            logger.info(f"Prompt deleted: {prompt_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting prompt: {str(e)}")
            raise
    
    def search_by_name(self, user_id: str, prompt_name: str) -> List[Prompt]:
        """이름으로 프롬프트 검색"""
        try:
            # prompts 테이블에는 GSI가 없으므로 scan 사용
            response = self.table.scan(
                FilterExpression='userId = :userId AND contains(promptName, :promptName)',
                ExpressionAttributeValues={
                    ':userId': user_id,
                    ':promptName': prompt_name
                }
            )
            
            prompts = []
            for item in response.get('Items', []):
                prompts.append(Prompt.from_dict(item))
            
            return prompts
            
        except Exception as e:
            logger.error(f"Error searching prompts by name: {str(e)}")
            raise
    
    def clone(self, prompt_id: str, new_user_id: str, new_name: str) -> Prompt:
        """프롬프트 복제"""
        try:
            # 원본 조회
            original = self.find_by_id(prompt_id)
            if not original:
                raise ValueError(f"Prompt not found: {prompt_id}")
            
            # 새 프롬프트 생성
            cloned = Prompt(
                prompt_id='',  # 새 ID 자동 생성
                user_id=new_user_id,
                engine_type=original.engine_type,
                prompt_name=new_name,
                prompt=original.prompt,
                files=original.files,
                is_public=False,  # 복제된 프롬프트는 기본 비공개
                metadata={'cloned_from': prompt_id}
            )
            
            return self.save(cloned)
            
        except Exception as e:
            logger.error(f"Error cloning prompt: {str(e)}")
            raise