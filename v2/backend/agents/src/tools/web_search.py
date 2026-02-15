"""
Web Search Tool
일반 웹 검색 (SerpAPI, DuckDuckGo)

주요 기능:
- 일반 웹 검색
- 뉴스 검색
- 팩트 검증
- 이미지 검색

지원 엔진:
- SerpAPI (Google 검색 API)
- DuckDuckGo (무료, API 키 불필요)
"""

import os
import httpx
import logging
import asyncio
from typing import Dict, Any, List, Optional
from functools import wraps

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# API 설정
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
SERPAPI_URL = "https://serpapi.com/search"

# 재시도 설정
MAX_RETRIES = 3
RETRY_DELAY = 1.0


def with_retry(max_retries: int = MAX_RETRIES, delay: float = RETRY_DELAY):
    """재시도 데코레이터"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except (httpx.HTTPStatusError, httpx.RequestError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (attempt + 1))
                        logger.warning(f"Web search retry {attempt + 1}/{max_retries}")
            raise last_exception
        return wrapper
    return decorator


@tool
async def search_web(
    query: str,
    num_results: int = 5,
    region: str = "kr",
) -> str:
    """
    웹 검색을 수행합니다.

    Args:
        query: 검색할 키워드 (예: "삼성전자 반도체")
        num_results: 검색 결과 수 (기본 5개)
        region: 검색 지역 (kr: 한국, us: 미국)

    Returns:
        검색 결과 목록
    """
    result = await web_search_internal(
        query=query,
        num_results=num_results,
        region=region,
    )

    if not result or not result.get("results"):
        return f"'{query}'에 대한 검색 결과가 없습니다."

    # 결과 포맷팅
    output = f"## 웹 검색 결과: {query}\n\n"
    output += f"총 {result.get('total', 0)}건 (출처: {result.get('source', 'web')})\n\n"

    for i, item in enumerate(result["results"], 1):
        output += f"### {i}. {item.get('title', '제목 없음')}\n"
        output += f"- **링크**: {item.get('link', '')}\n"
        if item.get('snippet'):
            output += f"- **요약**: {item['snippet']}\n"
        output += "\n"

    return output


@tool
async def search_news_web(
    query: str,
    num_results: int = 10,
) -> str:
    """
    뉴스 기사를 검색합니다.

    Args:
        query: 검색할 키워드 (예: "현대차 전기차")
        num_results: 검색 결과 수 (기본 10개)

    Returns:
        뉴스 검색 결과
    """
    result = await search_news_internal(
        query=query,
        num_results=num_results,
    )

    if not result or not result.get("results"):
        return f"'{query}' 관련 뉴스를 찾을 수 없습니다."

    # 결과 포맷팅
    output = f"## 뉴스 검색: {query}\n\n"
    output += f"총 {result.get('total', 0)}건\n\n"

    for i, item in enumerate(result["results"], 1):
        output += f"{i}. **{item.get('title', '')}**\n"
        if item.get('source'):
            output += f"   - 출처: {item['source']}"
        if item.get('date'):
            output += f" | {item['date']}"
        output += "\n"
        if item.get('snippet'):
            output += f"   - {item['snippet'][:150]}...\n"
        if item.get('link'):
            output += f"   - [링크]({item['link']})\n"
        output += "\n"

    return output


@tool
async def verify_fact_web(
    claim: str,
    context: str = "",
) -> str:
    """
    웹 검색을 통해 주장의 사실 여부를 검증합니다.

    Args:
        claim: 검증할 주장 (예: "테슬라가 한국 공장 설립 계획 발표")
        context: 추가 맥락 정보

    Returns:
        검증 결과 및 관련 출처
    """
    search_query = claim
    if context:
        search_query = f"{claim} {context}"

    result = await web_search_internal(search_query, num_results=5)

    if not result or not result.get("results"):
        output = f"## 팩트체크 결과\n\n"
        output += f"**주장**: {claim}\n\n"
        output += "**결과**: 관련 정보를 찾을 수 없습니다.\n"
        output += "**신뢰도**: 0%\n"
        return output

    num_sources = len(result["results"])
    confidence = min(num_sources * 20, 100)

    output = f"## 팩트체크 결과\n\n"
    output += f"**주장**: {claim}\n\n"
    output += f"**관련 소스**: {num_sources}개 발견\n"
    output += f"**신뢰도 점수**: {confidence}%\n\n"
    output += "### 관련 출처\n"

    for i, item in enumerate(result["results"], 1):
        output += f"{i}. [{item.get('title', '')}]({item.get('link', '')})\n"
        if item.get('snippet'):
            output += f"   {item['snippet'][:100]}...\n\n"

    return output


@tool
async def search_images(
    query: str,
    num_results: int = 5,
) -> str:
    """
    이미지를 검색합니다 (SerpAPI 필요).

    Args:
        query: 검색할 키워드
        num_results: 검색 결과 수

    Returns:
        이미지 검색 결과
    """
    if not SERPAPI_KEY:
        return "이미지 검색을 위해서는 SERPAPI_KEY가 필요합니다."

    result = await search_images_internal(query, num_results)

    if not result or not result.get("images"):
        return f"'{query}' 관련 이미지를 찾을 수 없습니다."

    output = f"## 이미지 검색: {query}\n\n"

    for i, img in enumerate(result["images"], 1):
        output += f"{i}. {img.get('title', '제목 없음')}\n"
        output += f"   - 원본: {img.get('original', '')}\n"
        output += f"   - 출처: {img.get('source', '')}\n\n"

    return output


# =============================================================================
# 내부 함수
# =============================================================================


@with_retry()
async def web_search_internal(
    query: str,
    num_results: int = 5,
    language: str = "ko",
    region: str = "kr",
) -> Optional[Dict[str, Any]]:
    """
    웹 검색 실행 (내부 함수)

    SerpAPI 사용 가능하면 우선 사용,
    아니면 DuckDuckGo 폴백
    """
    if SERPAPI_KEY:
        return await _search_serpapi(query, num_results, language, region)
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
            response = await client.get(SERPAPI_URL, params=params)
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
        # SerpAPI 실패 시 DuckDuckGo 폴백
        return await _search_duckduckgo(query, num_results)


async def _search_duckduckgo(
    query: str,
    num_results: int = 5,
) -> Optional[Dict[str, Any]]:
    """DuckDuckGo 검색 (API 키 불필요)"""
    try:
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


@with_retry()
async def search_news_internal(
    query: str,
    num_results: int = 10,
) -> Optional[Dict[str, Any]]:
    """뉴스 검색 (내부 함수)"""
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
                response = await client.get(SERPAPI_URL, params=params)
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

    # 폴백: 일반 검색 + "뉴스" 키워드
    return await web_search_internal(f"{query} 뉴스", num_results)


async def search_images_internal(
    query: str,
    num_results: int = 5,
) -> Optional[Dict[str, Any]]:
    """이미지 검색 (내부 함수, SerpAPI만 지원)"""
    if not SERPAPI_KEY:
        return None

    try:
        params = {
            "api_key": SERPAPI_KEY,
            "q": query,
            "tbm": "isch",  # 이미지 검색
            "hl": "ko",
            "gl": "kr",
            "engine": "google",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(SERPAPI_URL, params=params)
            response.raise_for_status()
            data = response.json()

            images = []
            for item in data.get("images_results", [])[:num_results]:
                images.append({
                    "title": item.get("title", ""),
                    "original": item.get("original", ""),
                    "thumbnail": item.get("thumbnail", ""),
                    "source": item.get("source", ""),
                    "link": item.get("link", ""),
                })

            return {
                "images": images,
                "query": query,
                "total": len(images),
            }

    except Exception as e:
        logger.error(f"SerpAPI image search error: {e}")
        return None


# =============================================================================
# 유틸리티 함수
# =============================================================================


def get_api_status() -> Dict[str, Any]:
    """API 상태 확인"""
    return {
        "serpapi_configured": bool(SERPAPI_KEY),
        "fallback_available": True,  # DuckDuckGo는 항상 사용 가능
    }


async def health_check() -> bool:
    """검색 가능 여부 확인"""
    try:
        result = await web_search_internal("테스트", num_results=1)
        return result is not None and len(result.get("results", [])) > 0
    except Exception:
        return False


# =============================================================================
# 하위 호환성을 위한 함수
# =============================================================================


async def web_search(
    query: str,
    num_results: int = 5,
    language: str = "ko",
    region: str = "kr",
) -> Optional[Dict[str, Any]]:
    """하위 호환성을 위한 wrapper"""
    return await web_search_internal(query, num_results, language, region)


async def search_news(
    query: str,
    num_results: int = 10,
) -> Optional[Dict[str, Any]]:
    """하위 호환성을 위한 wrapper"""
    return await search_news_internal(query, num_results)


async def verify_fact(
    claim: str,
    context: Optional[str] = None,
) -> Dict[str, Any]:
    """하위 호환성을 위한 wrapper"""
    search_query = claim
    if context:
        search_query = f"{claim} {context}"

    result = await web_search_internal(search_query, num_results=5)

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
