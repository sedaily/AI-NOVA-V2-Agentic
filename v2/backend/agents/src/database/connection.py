"""
Database Connection
Aurora PostgreSQL 연결 관리
로컬 Docker 및 AWS Aurora 지원

pgvector 확장 + HNSW 인덱스
"""

import os
import logging
from typing import Optional
from contextlib import asynccontextmanager
import asyncpg

logger = logging.getLogger(__name__)

# DATABASE_URL이 있으면 우선 사용 (로컬 Docker 환경)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # DATABASE_URL 파싱
    from urllib.parse import urlparse
    parsed = urlparse(DATABASE_URL)
    DB_HOST = parsed.hostname or "localhost"
    DB_PORT = parsed.port or 5432
    DB_NAME = parsed.path.lstrip("/") or "nexus_kb"
    DB_USER = parsed.username or "nexus_user"
    DB_PASSWORD = parsed.password or "nexus_dev_password"
else:
    # 개별 환경 변수 사용 (프로덕션)
    DB_HOST = os.getenv("AURORA_HOST", "localhost")
    DB_PORT = int(os.getenv("AURORA_PORT", "5432"))
    DB_NAME = os.getenv("AURORA_DB", "nexus_kb")
    DB_USER = os.getenv("AURORA_USER", "nexus_user")
    DB_PASSWORD = os.getenv("AURORA_PASSWORD", "nexus_dev_password")

_pool: Optional[asyncpg.Pool] = None


async def get_db_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            host=DB_HOST, port=DB_PORT, database=DB_NAME,
            user=DB_USER, password=DB_PASSWORD,
            min_size=5, max_size=20, command_timeout=60,
        )
        async with _pool.acquire() as conn:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    return _pool


async def get_db_connection() -> asyncpg.Connection:
    pool = await get_db_pool()
    return await pool.acquire()


async def close_db_connection(conn: asyncpg.Connection):
    pool = await get_db_pool()
    await pool.release(conn)


@asynccontextmanager
async def db_connection():
    conn = await get_db_connection()
    try:
        yield conn
    finally:
        await close_db_connection(conn)


async def close_db_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def init_database():
    """
    데이터베이스 초기화

    테이블:
    - kb_documents: KB 규칙 (Agent별 카테고리)
    - stylebook: 스타일북 규칙
    - example_articles: Few-shot 예시
    - reporter_styles: 기자 스타일 학습

    임베딩: Titan v2 (1024 차원)
    """
    async with db_connection() as conn:
        # KB 문서 테이블
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS kb_documents (
                id SERIAL PRIMARY KEY,
                doc_id VARCHAR(255) UNIQUE NOT NULL,
                title VARCHAR(500),
                content TEXT NOT NULL,
                category VARCHAR(100),
                engine_type VARCHAR(10),
                embedding vector(1024),
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 스타일북 테이블
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS stylebook (
                id SERIAL PRIMARY KEY,
                rule_id VARCHAR(255) UNIQUE NOT NULL,
                category VARCHAR(100),
                rule_text TEXT NOT NULL,
                embedding vector(1024),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 예시 기사 테이블
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS example_articles (
                id SERIAL PRIMARY KEY,
                article_id VARCHAR(255) UNIQUE NOT NULL,
                content TEXT NOT NULL,
                article_type VARCHAR(50),
                engine_type VARCHAR(10),
                embedding vector(1024),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 기자 스타일 테이블
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS reporter_styles (
                id SERIAL PRIMARY KEY,
                reporter_id VARCHAR(255) UNIQUE NOT NULL,
                style_summary TEXT,
                preferred_patterns TEXT[],
                word_preferences JSONB,
                avg_article_length INTEGER DEFAULT 800,
                tone_distribution JSONB,
                total_articles INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 벡터 인덱스 (HNSW - 더 빠른 검색)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS kb_embedding_hnsw_idx
            ON kb_documents USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS stylebook_embedding_hnsw_idx
            ON stylebook USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS example_embedding_hnsw_idx
            ON example_articles USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
        """)

        # 필터링용 인덱스
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS kb_category_idx
            ON kb_documents (category, engine_type)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS stylebook_category_idx
            ON stylebook (category)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS example_type_idx
            ON example_articles (article_type, engine_type)
        """)

        logger.info("Database initialized successfully")
