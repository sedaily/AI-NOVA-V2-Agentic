"""
KB Repository
KB 문서 관리
"""

from typing import List, Dict, Any, Optional
from .vector_store import VectorStore


class KBRepository:
    """KB 문서 저장소"""

    def __init__(self):
        self.vector_store = VectorStore()
        self.table = "kb_documents"

    async def search_rules(
        self,
        query: str,
        engine_type: Optional[str] = None,
        category: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """KB 규칙 검색"""
        filters = {}
        if engine_type:
            filters["engine_type"] = engine_type
        if category:
            filters["category"] = category

        results = await self.vector_store.search_similar(
            table=self.table,
            query=query,
            top_k=top_k,
            filters=filters if filters else None,
        )

        return [
            {
                "doc_id": r.get("doc_id"),
                "title": r.get("title"),
                "content": r.get("content"),
                "category": r.get("category"),
                "similarity": r.get("similarity", 0),
            }
            for r in results
        ]

    async def add_document(
        self,
        doc_id: str,
        title: str,
        content: str,
        category: str,
        engine_type: str = "11",
        metadata: Optional[Dict] = None,
    ) -> bool:
        """KB 문서 추가"""
        data = {
            "doc_id": doc_id,
            "title": title,
            "content": content,
            "category": category,
            "engine_type": engine_type,
            "metadata": metadata or {},
        }
        return await self.vector_store.insert_with_embedding(
            table=self.table,
            data=data,
            text_field="content",
        )
