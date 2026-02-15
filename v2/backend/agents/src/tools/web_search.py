"""
Web Search Tool
일반 웹 검색 (DuckDuckGo, SerpAPI 등)
"""

import os
import httpx
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")


async def web_search(
    query: str,
    num_results: int = 5,
    language: str = "ko",
    region: str = "kr",
) -> Optional[Dict[str, Any]]:
    """
    웹 검색 실행

    Args:
        query: 검색어
        num_results: 결과 수
        language: 언어 코드
        region: 지역 코드

    Returns:
        검색 결과 또는 None
    """
    # SerpAPI 사용 가능하면 우선 사용
    if SERPAPI_KEY:
        return await _search_serpapi(query, num_results, language, region)

    # DuckDuckGo 폴백
    return await _search_duckduckgo(query, num_results)


async def _search_serpapi(
    query: str,
    num_results: int = 5,
    language: str = "ko",
    region: str = "kr",
) -> Optional[Dict[str, Any]]:
    """SerpAPI 검색"""
    try:
        params = {
            "api_key": SERPAPI_KEY,
            "q": query,
            "num": num_results,
            "hl": language,
            "gl": region,
            "engine": "google",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://serpapi.com/search",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("organic_results", [])[:num_results]:
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": "serpapi",
                })

            return {
                "results": results,
                "query": query,
                "total": len(results),
                "source": "serpapi",
            }

    except Exception as e:
        logger.error(f"SerpAPI error: {e}")
        return None


async def _search_duckduckgo(
    query: str,
    num_results: int = 5,
) -> Optional[Dict[str, Any]]:
    """DuckDuckGo 검색 (API 키 불필요)"""
    try:
        # DuckDuckGo Instant Answer API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://api.duckduckgo.com/",
                params={
                    "q": query,
                    "format": "json",
                    "no_html": 1,
                    "skip_disambig": 1,
                },
            )
            response.raise_for_status()
            data = response.json()

            results = []

            # Abstract 결과
            if data.get("Abstract"):
                results.append({
                    "title": data.get("Heading", ""),
                    "link": data.get("AbstractURL", ""),
                    "snippet": data.get("Abstract", ""),
                    "source": "duckduckgo",
                })

            # Related Topics
            for topic in data.get("RelatedTopics", [])[:num_results-1]:
                if isinstance(topic, dict) and "Text" in topic:
                    results.append({
                        "title": topic.get("Text", "")[:100],
                        "link": topic.get("FirstURL", ""),
                        "snippet": topic.get("Text", ""),
                        "source": "duckduckgo",
                    })

            return {
                "results": results[:num_results],
                "query": query,
                "total": len(results),
                "source": "duckduckgo",
            }

    except Exception as e:
        logger.error(f"DuckDuckGo error: {e}")
        return None


async def search_news(
    query: str,
    num_results: int = 10,
) -> Optional[Dict[str, Any]]:
    """
    뉴스 전용 검색

    Args:
        query: 검색어
        num_results: 결과 수

    Returns:
        뉴스 검색 결과
    """
    if SERPAPI_KEY:
        try:
            params = {
                "api_key": SERPAPI_KEY,
                "q": query,
                "num": num_results,
                "tbm": "nws",  # 뉴스 검색
                "hl": "ko",
                "gl": "kr",
                "engine": "google",
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://serpapi.com/search",
                    params=params,
                )
                response.raise_for_status()
                data = response.json()

                results = []
                for item in data.get("news_results", [])[:num_results]:
                    results.append({
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "source": item.get("source", ""),
                        "date": item.get("date", ""),
                    })

                return {
                    "results": results,
                    "query": query,
                    "total": len(results),
                    "type": "news",
                }

        except Exception as e:
            logger.error(f"SerpAPI news search error: {e}")

    # 폴백: 일반 검색
    return await web_search(f"{query} 뉴스", num_results)


async def verify_fact(
    claim: str,
    context: Optional[str] = None,
) -> Dict[str, Any]:
    """
    사실 검증을 위한 검색

    Args:
        claim: 검증할 주장
        context: 추가 문맥

    Returns:
        검증 결과
    """
    search_query = claim
    if context:
        search_query = f"{claim} {context}"

    result = await web_search(search_query, num_results=5)

    if not result or not result.get("results"):
        return {
            "verified": False,
            "confidence": 0,
            "sources": [],
            "claim": claim,
        }

    return {
        "verified": True,
        "confidence": min(len(result["results"]) * 20, 100),
        "sources": result["results"],
        "claim": claim,
        "source": result.get("source", "web"),
    }
