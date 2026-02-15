"""
AgentCore Memory
AWS Bedrock AgentCore 메모리 연동
"""

import os
import logging
from typing import Dict, Any, List, Optional
import boto3
from datetime import datetime
import json

logger = logging.getLogger(__name__)

AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
MEMORY_ID = os.getenv("AGENTCORE_MEMORY_ID", "")


class AgentCoreMemory:
    """AWS AgentCore 메모리 관리"""

    def __init__(self, memory_id: Optional[str] = None):
        self.memory_id = memory_id or MEMORY_ID
        self.client = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)

    async def store_memory(
        self,
        session_id: str,
        content: Dict[str, Any],
        memory_type: str = "conversation",
    ) -> bool:
        """
        메모리 저장

        Args:
            session_id: 세션 ID
            content: 저장할 내용
            memory_type: 메모리 타입 (conversation, style, preference)

        Returns:
            성공 여부
        """
        if not self.memory_id:
            logger.warning("AGENTCORE_MEMORY_ID not set")
            return False

        try:
            self.client.invoke_agent(
                agentId=self.memory_id,
                agentAliasId="TSTALIASID",
                sessionId=session_id,
                inputText=json.dumps({
                    "action": "store",
                    "type": memory_type,
                    "content": content,
                    "timestamp": datetime.utcnow().isoformat(),
                }),
            )
            return True
        except Exception as e:
            logger.error(f"AgentCore store error: {e}")
            return False

    async def retrieve_memory(
        self,
        session_id: str,
        memory_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        메모리 조회

        Args:
            session_id: 세션 ID
            memory_type: 필터할 메모리 타입
            limit: 최대 결과 수

        Returns:
            메모리 리스트
        """
        if not self.memory_id:
            return []

        try:
            response = self.client.invoke_agent(
                agentId=self.memory_id,
                agentAliasId="TSTALIASID",
                sessionId=session_id,
                inputText=json.dumps({
                    "action": "retrieve",
                    "type": memory_type,
                    "limit": limit,
                }),
            )

            # 응답 파싱
            memories = []
            for event in response.get("completion", []):
                if "chunk" in event:
                    chunk_data = event["chunk"].get("bytes", b"")
                    if chunk_data:
                        memories.extend(json.loads(chunk_data.decode()))

            return memories

        except Exception as e:
            logger.error(f"AgentCore retrieve error: {e}")
            return []

    async def get_reporter_style(
        self,
        reporter_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        기자 스타일 정보 조회

        Args:
            reporter_id: 기자 ID

        Returns:
            스타일 정보
        """
        memories = await self.retrieve_memory(
            session_id=f"reporter_{reporter_id}",
            memory_type="style",
            limit=1,
        )

        if memories:
            return memories[0]
        return None

    async def update_reporter_style(
        self,
        reporter_id: str,
        style_data: Dict[str, Any],
    ) -> bool:
        """
        기자 스타일 정보 업데이트

        Args:
            reporter_id: 기자 ID
            style_data: 스타일 데이터

        Returns:
            성공 여부
        """
        return await self.store_memory(
            session_id=f"reporter_{reporter_id}",
            content=style_data,
            memory_type="style",
        )

    async def store_article_feedback(
        self,
        reporter_id: str,
        article_id: str,
        feedback: Dict[str, Any],
    ) -> bool:
        """
        기사 피드백 저장 (스타일 학습용)

        Args:
            reporter_id: 기자 ID
            article_id: 기사 ID
            feedback: 피드백 데이터

        Returns:
            성공 여부
        """
        return await self.store_memory(
            session_id=f"reporter_{reporter_id}",
            content={
                "article_id": article_id,
                "feedback": feedback,
                "timestamp": datetime.utcnow().isoformat(),
            },
            memory_type="feedback",
        )
