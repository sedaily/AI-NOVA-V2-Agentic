"""
Vector Store
Aurora PostgreSQL pgvector 벡터 검색

Titan Embeddings v2 (1024 차원) 사용
임베딩 캐싱으로 API 호출 최소화
"""

import os
import logging
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from functools import lru_cache
import boto3
import json
import asyncio

from .connection import db_connection

logger = logging.getLogger(__name__)

AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")

# 임베딩 차원 (Titan v2)
EMBEDDING_DIMENSION = 1024

# 임베딩 캐시 (메모리 내)
_embedding_cache: Dict[str, List[float]] = {}
_cache_max_size = 1000


class VectorStore:
    """
    pgvector 기반 벡터 저장소

    Features:
    - Titan Embeddings v2 (1024 차원)
    - 임베딩 캐싱 (메모리 + Redis 선택)
    - Agent별 필터링 검색
    - 배치 임베딩 지원
    """

    def __init__(self, use_cache: bool = True):
        self.bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)
        self.embedding_model = "amazon.titan-embed-text-v2:0"
        self.use_cache = use_cache
        self.dimension = EMBEDDING_DIMENSION

    def _cache_key(self, text: str) -> str:
        """캐시 키 생성 (해시)"""
        return hashlib.md5(text.encode()).hexdigest()

    async def get_embedding(self, text: str) -> List[float]:
        """
        Bedrock Titan으로 임베딩 생성

        Args:
            text: 임베딩할 텍스트

        Returns:
            1024차원 임베딩 벡터
        """
        if not text or not text.strip():
            return []

        # 캐시 확인
        if self.use_cache:
            cache_key = self._cache_key(text)
            if cache_key in _embedding_cache:
                return _embedding_cache[cache_key]

        try:
            # 텍스트 길이 제한 (Titan 최대 8K)
            truncated_text = text[:8000]

            response = self.bedrock.invoke_model(
                modelId=self.embedding_model,
                body=json.dumps({"inputText": truncated_text}),
                contentType="application/json",
            )
            result = json.loads(response["body"].read())
            embedding = result.get("embedding", [])

            # 캐시 저장
            if self.use_cache and embedding:
                if len(_embedding_cache) >= _cache_max_size:
                    # 캐시 절반 삭제 (간단한 LRU 대체)
                    keys_to_remove = list(_embedding_cache.keys())[:_cache_max_size // 2]
                    for k in keys_to_remove:
                        del _embedding_cache[k]

                _embedding_cache[self._cache_key(text)] = embedding

            return embedding

        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return []

    async def get_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 10,
    ) -> List[List[float]]:
        """
        배치 임베딩 생성

        Args:
            texts: 텍스트 리스트
            batch_size: 배치 크기

        Returns:
            임베딩 벡터 리스트
        """
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await asyncio.gather(
                *[self.get_embedding(text) for text in batch]
            )
            embeddings.extend(batch_embeddings)

        return embeddings

    async def search_similar(
        self,
        table: str,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        min_similarity: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        유사도 검색

        Args:
            table: 테이블명
            query: 검색 쿼리
            top_k: 상위 K개
            filters: 필터 조건 (컬럼: 값)
            min_similarity: 최소 유사도 (0-1)

        Returns:
            검색 결과 리스트
        """
        embedding = await self.get_embedding(query)
        if not embedding:
            logger.warning(f"Failed to get embedding for query: {query[:50]}...")
            return []

        return await self.search_by_embedding(
            table=table,
            embedding=embedding,
            top_k=top_k,
            filters=filters,
            min_similarity=min_similarity,
        )

    async def search_by_embedding(
        self,
        table: str,
        embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        min_similarity: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        임베딩 벡터로 직접 검색

        Args:
            table: 테이블명
            embedding: 검색 벡터
            top_k: 상위 K개
            filters: 필터 조건
            min_similarity: 최소 유사도

        Returns:
            검색 결과 리스트
        """
        embedding_str = f"[{','.join(map(str, embedding))}]"

        # WHERE 절 구성
        where_conditions = []
        params = []
        param_idx = 1

        if filters:
            for col, val in filters.items():
                if val is not None:
                    where_conditions.append(f"{col} = ${param_idx}")
                    params.append(val)
                    param_idx += 1

        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)

        # 유사도 계산 (1 - cosine distance)
        sql = f"""
            SELECT *,
                   1 - (embedding <=> $1::vector) as similarity
            FROM {table}
            {where_clause}
            ORDER BY embedding <=> $1::vector
            LIMIT {top_k}
        """

        try:
            async with db_connection() as conn:
                rows = await conn.fetch(sql, embedding_str, *params)

                results = []
                for row in rows:
                    row_dict = dict(row)
                    similarity = row_dict.get("similarity", 0)

                    # 최소 유사도 필터
                    if similarity >= min_similarity:
                        # embedding 컬럼 제외 (대용량)
                        row_dict.pop("embedding", None)
                        results.append(row_dict)

                return results

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    async def insert_with_embedding(
        self,
        table: str,
        data: Dict[str, Any],
        text_field: str,
    ) -> bool:
        """
        임베딩과 함께 데이터 삽입

        Args:
            table: 테이블명
            data: 삽입할 데이터
            text_field: 임베딩할 텍스트 필드명

        Returns:
            성공 여부
        """
        text = data.get(text_field, "")
        embedding = await self.get_embedding(text)
        if not embedding:
            logger.warning(f"Failed to get embedding for insert")
            return False

        data["embedding"] = f"[{','.join(map(str, embedding))}]"

        columns = list(data.keys())
        placeholders = [f"${i+1}" for i in range(len(columns))]

        sql = f"""
            INSERT INTO {table} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            ON CONFLICT DO NOTHING
        """

        try:
            async with db_connection() as conn:
                await conn.execute(sql, *data.values())
                return True
        except Exception as e:
            logger.error(f"Insert error: {e}")
            return False

    async def upsert_with_embedding(
        self,
        table: str,
        data: Dict[str, Any],
        text_field: str,
        conflict_field: str,
    ) -> bool:
        """
        임베딩과 함께 데이터 Upsert

        Args:
            table: 테이블명
            data: 데이터
            text_field: 임베딩할 텍스트 필드
            conflict_field: 충돌 감지 필드

        Returns:
            성공 여부
        """
        text = data.get(text_field, "")
        embedding = await self.get_embedding(text)
        if not embedding:
            return False

        data["embedding"] = f"[{','.join(map(str, embedding))}]"

        columns = list(data.keys())
        placeholders = [f"${i+1}" for i in range(len(columns))]
        update_set = [f"{col} = EXCLUDED.{col}" for col in columns if col != conflict_field]

        sql = f"""
            INSERT INTO {table} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            ON CONFLICT ({conflict_field}) DO UPDATE SET
            {', '.join(update_set)}
        """

        try:
            async with db_connection() as conn:
                await conn.execute(sql, *data.values())
                return True
        except Exception as e:
            logger.error(f"Upsert error: {e}")
            return False


# =============================================================================
# Agent별 검색 함수 (토큰 절약용)
# =============================================================================

# 싱글톤 인스턴스
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """VectorStore 싱글톤"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


async def search_kb_rules(
    agent_id: str,
    query: str,
    top_k: int = 5,
    engine_type: Optional[str] = None,
) -> List[str]:
    """
    Agent별 KB 규칙 검색

    Args:
        agent_id: Agent ID (W1, T1, P1, R1 등)
        query: 검색 쿼리 (기사 내용 일부)
        top_k: 상위 K개
        engine_type: 엔진 유형 (11: 기업, 22: 정부/공공)

    Returns:
        관련 KB 규칙 텍스트 리스트
    """
    store = get_vector_store()

    filters = {}
    if engine_type:
        filters["engine_type"] = engine_type

    # Agent별 카테고리 매핑
    agent_categories = {
        "W1": "writing",
        "T1": "title",
        "P1": "proofreading",
        "R1": "revision",
        "FACT": "factcheck",
        "STYLE": "style",
    }

    category = agent_categories.get(agent_id)
    if category:
        filters["category"] = category

    results = await store.search_similar(
        table="kb_documents",
        query=query,
        top_k=top_k,
        filters=filters if filters else None,
        min_similarity=0.3,  # 최소 30% 유사도
    )

    return [r.get("content", "") for r in results if r.get("content")]


async def search_stylebook(
    query: str,
    top_k: int = 3,
    category: Optional[str] = None,
) -> List[str]:
    """
    스타일북 규칙 검색

    Args:
        query: 검색 쿼리
        top_k: 상위 K개
        category: 카테고리 필터

    Returns:
        스타일 규칙 텍스트 리스트
    """
    store = get_vector_store()

    filters = {"category": category} if category else None

    results = await store.search_similar(
        table="stylebook",
        query=query,
        top_k=top_k,
        filters=filters,
        min_similarity=0.3,
    )

    return [r.get("rule_text", "") for r in results if r.get("rule_text")]


async def search_examples(
    query: str,
    top_k: int = 3,
    article_type: Optional[str] = None,
    engine_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Few-shot 예시 검색

    Args:
        query: 검색 쿼리
        top_k: 상위 K개
        article_type: 기사 유형 (online, print, daily)
        engine_type: 엔진 유형

    Returns:
        예시 기사 리스트
    """
    store = get_vector_store()

    filters = {}
    if article_type:
        filters["article_type"] = article_type
    if engine_type:
        filters["engine_type"] = engine_type

    results = await store.search_similar(
        table="example_articles",
        query=query,
        top_k=top_k,
        filters=filters if filters else None,
        min_similarity=0.4,
    )

    return [
        {
            "article_id": r.get("article_id"),
            "content": r.get("content"),
            "article_type": r.get("article_type"),
            "similarity": r.get("similarity", 0),
        }
        for r in results
    ]


async def get_reporter_style(reporter_id: str) -> str:
    """
    기자 스타일 조회 (DB 기반)

    Args:
        reporter_id: 기자 ID

    Returns:
        스타일 요약 텍스트
    """
    try:
        async with db_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT style_summary, preferred_patterns, avg_article_length
                FROM reporter_styles
                WHERE reporter_id = $1
                """,
                reporter_id,
            )

            if row:
                parts = []
                if row.get("style_summary"):
                    parts.append(f"문체: {row['style_summary']}")
                if row.get("avg_article_length"):
                    parts.append(f"평균 길이: {row['avg_article_length']}자")
                if row.get("preferred_patterns"):
                    patterns = row["preferred_patterns"][:5]
                    if patterns:
                        parts.append(f"자주 사용: {', '.join(patterns)}")
                return "\n".join(parts)

            return ""

    except Exception as e:
        logger.debug(f"Reporter style lookup failed: {e}")
        return ""


# =============================================================================
# 유틸리티 함수
# =============================================================================

def clear_embedding_cache():
    """임베딩 캐시 초기화"""
    global _embedding_cache
    _embedding_cache = {}
    logger.info("Embedding cache cleared")


def get_cache_stats() -> Dict[str, Any]:
    """캐시 통계"""
    return {
        "size": len(_embedding_cache),
        "max_size": _cache_max_size,
    }
