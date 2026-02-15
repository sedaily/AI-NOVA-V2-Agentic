"""
Vector Store
pgvector 벡터 검색 유틸리티
"""

import os
import logging
from typing import List, Dict, Any, Optional
import boto3
import json

from .connection import db_connection

logger = logging.getLogger(__name__)

BEDROCK_REGION = os.getenv("AWS_REGION", "ap-northeast-2")


class VectorStore:
    """pgvector 기반 벡터 저장소"""

    def __init__(self):
        self.bedrock = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)
        self.embedding_model = "amazon.titan-embed-text-v2:0"

    async def get_embedding(self, text: str) -> List[float]:
        """Bedrock Titan으로 임베딩 생성"""
        try:
            response = self.bedrock.invoke_model(
                modelId=self.embedding_model,
                body=json.dumps({"inputText": text[:8000]}),
                contentType="application/json",
            )
            result = json.loads(response["body"].read())
            return result.get("embedding", [])
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return []

    async def search_similar(
        self,
        table: str,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """유사도 검색"""
        embedding = await self.get_embedding(query)
        if not embedding:
            return []

        embedding_str = f"[{','.join(map(str, embedding))}]"

        where_clause = ""
        if filters:
            conditions = [f"{k} = '{v}'" for k, v in filters.items()]
            where_clause = "WHERE " + " AND ".join(conditions)

        sql = f"""
            SELECT *, 1 - (embedding <=> '{embedding_str}'::vector) as similarity
            FROM {table}
            {where_clause}
            ORDER BY embedding <=> '{embedding_str}'::vector
            LIMIT {top_k}
        """

        async with db_connection() as conn:
            rows = await conn.fetch(sql)
            return [dict(row) for row in rows]

    async def insert_with_embedding(
        self,
        table: str,
        data: Dict[str, Any],
        text_field: str,
    ) -> bool:
        """임베딩과 함께 데이터 삽입"""
        text = data.get(text_field, "")
        embedding = await self.get_embedding(text)
        if not embedding:
            return False

        data["embedding"] = f"[{','.join(map(str, embedding))}]"

        columns = ", ".join(data.keys())
        placeholders = ", ".join([f"${i+1}" for i in range(len(data))])

        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"

        async with db_connection() as conn:
            await conn.execute(sql, *data.values())
            return True
