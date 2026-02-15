"""
Database Module
Aurora PostgreSQL + pgvector 연동

주요 기능:
- VectorStore: 벡터 검색 (Titan Embeddings v2)
- search_kb_rules(): Agent별 KB 규칙 검색
- search_stylebook(): 스타일북 검색
- search_examples(): Few-shot 예시 검색
"""

from .connection import (
    get_db_connection,
    close_db_connection,
    db_connection,
    init_database,
    get_db_pool,
    close_db_pool,
)
from .vector_store import (
    VectorStore,
    get_vector_store,
    search_kb_rules,
    search_stylebook,
    search_examples,
    get_reporter_style,
    clear_embedding_cache,
    get_cache_stats,
    EMBEDDING_DIMENSION,
)
from .kb_repository import KBRepository
from .stylebook_repository import StylebookRepository

__all__ = [
    # Connection
    "get_db_connection",
    "close_db_connection",
    "db_connection",
    "init_database",
    "get_db_pool",
    "close_db_pool",
    # Vector Store
    "VectorStore",
    "get_vector_store",
    "EMBEDDING_DIMENSION",
    # Agent 검색 함수 (토큰 절약)
    "search_kb_rules",
    "search_stylebook",
    "search_examples",
    "get_reporter_style",
    # 캐시 관리
    "clear_embedding_cache",
    "get_cache_stats",
    # Repositories
    "KBRepository",
    "StylebookRepository",
]
