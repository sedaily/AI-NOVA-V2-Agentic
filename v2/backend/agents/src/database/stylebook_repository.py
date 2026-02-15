"""
Stylebook Repository
스타일북 규칙 관리
"""

from typing import List, Dict, Any
from .vector_store import VectorStore


class StylebookRepository:
    """스타일북 저장소"""

    def __init__(self):
        self.vector_store = VectorStore()
        self.table = "stylebook"

    async def search_rules(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """스타일 규칙 검색"""
        filters = {"category": category} if category else None

        results = await self.vector_store.search_similar(
            table=self.table,
            query=query,
            top_k=top_k,
            filters=filters,
        )

        return [
            {
                "rule_id": r.get("rule_id"),
                "category": r.get("category"),
                "rule_text": r.get("rule_text"),
                "similarity": r.get("similarity", 0),
            }
            for r in results
        ]

    async def add_rule(
        self,
        rule_id: str,
        category: str,
        rule_text: str,
    ) -> bool:
        """스타일 규칙 추가"""
        data = {
            "rule_id": rule_id,
            "category": category,
            "rule_text": rule_text,
        }
        return await self.vector_store.insert_with_embedding(
            table=self.table,
            data=data,
            text_field="rule_text",
        )


from typing import Optional
