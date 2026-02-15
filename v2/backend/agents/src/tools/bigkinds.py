"""
BigKinds API Tool
한국 뉴스 데이터베이스 검색
"""

import os
import httpx
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

BIGKINDS_API_URL = os.getenv("BIGKINDS_API_URL", "https://www.bigkinds.or.kr/api")
BIGKINDS_API_KEY = os.getenv("BIGKINDS_API_KEY", "")


async def search_bigkinds(
    query: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    provider: Optional[List[str]] = None,
    category: Optional[List[str]] = None,
    max_results: int = 10,
) -> Dict[str, Any]:
    """
    BigKinds 뉴스 검색

    Args:
        query: 검색어
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)
        provider: 언론사 필터 (예: ["서울경제", "한국경제"])
        category: 카테고리 필터 (예: ["경제", "정치"])
        max_results: 최대 결과 수

    Returns:
        검색 결과 딕셔너리
    """
    if not BIGKINDS_API_KEY:
        logger.warning("BIGKINDS_API_KEY not set")
        return {"articles": [], "total": 0, "error": "API key not configured"}

    # 기본 날짜 설정 (최근 7일)
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    payload = {
        "access_key": BIGKINDS_API_KEY,
        "argument": {
            "query": query,
            "published_at": {
                "from": start_date,
                "until": end_date,
            },
            "sort": {"date": "desc"},
            "return_from": 0,
            "return_size": max_results,
            "fields": [
                "title",
                "content",
                "published_at",
                "provider",
                "category",
                "byline",
                "news_url",
            ],
        },
    }

    if provider:
        payload["argument"]["provider"] = provider
    if category:
        payload["argument"]["category"] = category

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BIGKINDS_API_URL}/news/search",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

            articles = []
            for doc in data.get("documents", []):
                articles.append({
                    "title": doc.get("title", ""),
                    "content": doc.get("content", "")[:500],  # 요약
                    "published_at": doc.get("published_at", ""),
                    "provider": doc.get("provider", ""),
                    "category": doc.get("category", ""),
                    "byline": doc.get("byline", ""),
                    "url": doc.get("news_url", ""),
                })

            return {
                "articles": articles,
                "total": data.get("total_hits", len(articles)),
                "query": query,
            }

    except httpx.HTTPStatusError as e:
        logger.error(f"BigKinds API HTTP error: {e}")
        return {"articles": [], "total": 0, "error": str(e)}
    except Exception as e:
        logger.error(f"BigKinds API error: {e}")
        return {"articles": [], "total": 0, "error": str(e)}


async def get_trending_keywords(
    category: str = "경제",
    period: str = "day",
) -> List[str]:
    """
    BigKinds 트렌드 키워드 조회

    Args:
        category: 카테고리
        period: 기간 (day, week, month)

    Returns:
        트렌딩 키워드 리스트
    """
    if not BIGKINDS_API_KEY:
        return []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BIGKINDS_API_URL}/trend/keywords",
                json={
                    "access_key": BIGKINDS_API_KEY,
                    "argument": {
                        "category": category,
                        "period": period,
                    },
                },
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

            return [kw.get("keyword", "") for kw in data.get("keywords", [])]

    except Exception as e:
        logger.error(f"BigKinds trending error: {e}")
        return []
