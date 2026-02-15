"""
Prompt Loader
DynamoDB에서 프롬프트 로딩
"""

import os
import logging
from typing import Dict, Any, Optional
import boto3
from functools import lru_cache

logger = logging.getLogger(__name__)

AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")

# DynamoDB 테이블명 (서비스별)
PROMPT_TABLES = {
    "W1": os.getenv("DYNAMO_BODO_TABLE", "sedaily-bodo-prompts"),
    "T1": os.getenv("DYNAMO_TITLE_TABLE", "sedaily-title-prompts"),
    "P1": os.getenv("DYNAMO_PROOF_TABLE", "sedaily-proofreading-prompts"),
    "R1": os.getenv("DYNAMO_REGRESSION_TABLE", "sedaily-regression-prompts"),
}

# 기본 프롬프트 ID (시스템 프롬프트)
DEFAULT_PROMPT_IDS = {
    "W1_11": "system_w1_engine11",  # 기업 보도자료
    "W1_22": "system_w1_engine22",  # 정부/공공 보도자료
    "T1": "system_t1_titlegen",
    "P1": "system_p1_proofread",
    "R1": "system_r1_revision",
}


class PromptLoader:
    """DynamoDB 프롬프트 로더"""

    def __init__(self):
        self.dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
        self._cache: Dict[str, Dict[str, Any]] = {}

    @lru_cache(maxsize=50)
    def get_prompt(
        self,
        prompt_type: str,
        engine_type: Optional[str] = None,
        prompt_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        프롬프트 조회

        Args:
            prompt_type: W1, T1, P1, R1
            engine_type: 11 (기업) 또는 22 (정부/공공)
            prompt_id: 특정 프롬프트 ID (없으면 기본값)

        Returns:
            프롬프트 데이터 (instruction, description, files 등)
        """
        # 캐시 키 생성
        cache_key = f"{prompt_type}_{engine_type or 'default'}_{prompt_id or 'system'}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        # 테이블 및 ID 결정
        table_name = PROMPT_TABLES.get(prompt_type)
        if not table_name:
            logger.warning(f"Unknown prompt type: {prompt_type}")
            return self._get_fallback_prompt(prompt_type, engine_type)

        # 프롬프트 ID 결정
        if not prompt_id:
            key = f"{prompt_type}_{engine_type}" if engine_type else prompt_type
            prompt_id = DEFAULT_PROMPT_IDS.get(key, DEFAULT_PROMPT_IDS.get(prompt_type))

        try:
            table = self.dynamodb.Table(table_name)
            response = table.get_item(Key={"promptId": prompt_id})

            if "Item" not in response:
                logger.warning(f"Prompt not found: {prompt_id}")
                return self._get_fallback_prompt(prompt_type, engine_type)

            item = response["Item"]
            prompt_data = {
                "prompt_id": item.get("promptId"),
                "name": item.get("promptName"),
                "description": item.get("prompt", {}).get("description", ""),
                "instruction": item.get("prompt", {}).get("instruction", ""),
                "files": item.get("files", []),
                "engine_type": item.get("engineType"),
                "metadata": item.get("metadata", {}),
            }

            self._cache[cache_key] = prompt_data
            return prompt_data

        except Exception as e:
            logger.error(f"Error loading prompt {prompt_id}: {e}")
            return self._get_fallback_prompt(prompt_type, engine_type)

    def get_system_prompt(
        self,
        prompt_type: str,
        engine_type: Optional[str] = None,
    ) -> str:
        """
        시스템 프롬프트 텍스트만 반환

        Args:
            prompt_type: W1, T1, P1, R1
            engine_type: 11 또는 22

        Returns:
            시스템 프롬프트 문자열
        """
        prompt_data = self.get_prompt(prompt_type, engine_type)
        return prompt_data.get("instruction", "")

    def get_prompt_with_files(
        self,
        prompt_type: str,
        engine_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        프롬프트와 첨부 파일 함께 반환

        Returns:
            {
                "instruction": "...",
                "files": [{"fileName": "...", "fileContent": "..."}]
            }
        """
        prompt_data = self.get_prompt(prompt_type, engine_type)
        return {
            "instruction": prompt_data.get("instruction", ""),
            "files": prompt_data.get("files", []),
        }

    def _get_fallback_prompt(
        self,
        prompt_type: str,
        engine_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """폴백 프롬프트 (DynamoDB 접근 실패 시)"""
        from .prompt_templates import PROMPT_TEMPLATES

        template = PROMPT_TEMPLATES.get(prompt_type, {})
        if engine_type and engine_type in template:
            return template[engine_type]
        return template.get("default", {"instruction": "", "description": ""})

    def clear_cache(self):
        """캐시 초기화"""
        self._cache.clear()
        self.get_prompt.cache_clear()

    def list_available_prompts(self, prompt_type: str) -> list:
        """사용 가능한 프롬프트 목록"""
        table_name = PROMPT_TABLES.get(prompt_type)
        if not table_name:
            return []

        try:
            table = self.dynamodb.Table(table_name)
            response = table.scan(
                ProjectionExpression="promptId, promptName, engineType, isPublic",
                FilterExpression="isPublic = :public",
                ExpressionAttributeValues={":public": True},
            )
            return response.get("Items", [])
        except Exception as e:
            logger.error(f"Error listing prompts: {e}")
            return []


# 싱글톤 인스턴스
prompt_loader = PromptLoader()
