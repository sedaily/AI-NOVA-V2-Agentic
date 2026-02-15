"""
Database Connection
Aurora PostgreSQL 연결 관리
"""

import os
import logging
from typing import Optional
from contextlib import asynccontextmanager
import asyncpg

logger = logging.getLogger(__name__)

DB_HOST = os.getenv("AURORA_HOST", "localhost")
DB_PORT = int(os.getenv("AURORA_PORT", "5432"))
DB_NAME = os.getenv("AURORA_DB", "nexus_kb")
DB_USER = os.getenv("AURORA_USER", "postgres")
DB_PASSWORD = os.getenv("AURORA_PASSWORD", "")

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
    async with db_connection() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS kb_documents (
                id SERIAL PRIMARY KEY,
                doc_id VARCHAR(255) UNIQUE NOT NULL,
                title VARCHAR(500),
                content TEXT NOT NULL,
                category VARCHAR(100),
                engine_type VARCHAR(10),
                embedding vector(1536),
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS stylebook (
                id SERIAL PRIMARY KEY,
                rule_id VARCHAR(255) UNIQUE NOT NULL,
                category VARCHAR(100),
                rule_text TEXT NOT NULL,
                embedding vector(1536),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS example_articles (
                id SERIAL PRIMARY KEY,
                article_id VARCHAR(255) UNIQUE NOT NULL,
                content TEXT NOT NULL,
                article_type VARCHAR(50),
                engine_type VARCHAR(10),
                embedding vector(1536),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS kb_embedding_idx
            ON kb_documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)
        """)
