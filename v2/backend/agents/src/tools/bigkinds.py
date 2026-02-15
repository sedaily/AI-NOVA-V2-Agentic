"""
BigKinds API Tool
한국 뉴스 데이터베이스 검색 (빅카인즈)

주요 기능:
- 뉴스 검색 (키워드, 날짜, 언론사 필터)
- 트렌딩 키워드 조회
- 기사 상세 조회
- 연관어 분석

API 문서: https://www.bigkinds.or.kr/api/guide
"""

import os
import httpx
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from functools import wraps

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# API 설정
BIGKINDS_API_URL = os.getenv("BIGKINDS_API_URL", "https://tools.kinds.or.kr")
BIGKINDS_API_KEY = os.getenv("BIGKINDS_API_KEY", "")

# 재시도 설정
MAX_RETRIES = 3
RETRY_DELAY = 1.0

# 경제 언론사 목록
ECONOMY_PROVIDERS = [
    "서울경제",
    "한국경제",
    "매일경제",
    "머니투데이",
    "이데일리",
    "파이낸셜뉴스",
    "헤럴드경제",
    "아시아경제",
]

# 카테고리 매핑
CATEGORY_MAP = {
    "경제": "economy",
    "정치": "politics",
    "사회": "society",
    "국제": "international",
    "IT": "it_science",
    "문화": "culture",
    "스포츠": "sports",
}


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
                        logger.warning(f"BigKinds API retry {attempt + 1}/{max_retries}")
            raise last_exception
        return wrapper
    return decorator


@tool
async def search_bigkinds_news(
    query: str,
    days: int = 7,
    max_results: int = 10,
    economy_only: bool = True,
) -> str:
    """
    빅카인즈에서 한국 뉴스를 검색합니다.

    Args:
        query: 검색할 키워드 (예: "삼성전자 반도체")
        days: 검색 기간 (일 단위, 기본 7일)
        max_results: 최대 결과 수 (기본 10개)
        economy_only: 경제 언론사만 검색 (기본 True)

    Returns:
        검색된 뉴스 기사 목록 (제목, 요약, 출처, 날짜)
    """
    result = await search_bigkinds(
        query=query,
        start_date=(datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"),
        end_date=datetime.now().strftime("%Y-%m-%d"),
        provider=ECONOMY_PROVIDERS if economy_only else None,
        max_results=max_results,
    )

    if result.get("error"):
        return f"검색 오류: {result['error']}"

    if not result.get("articles"):
        return f"'{query}'에 대한 검색 결과가 없습니다."

    # 결과 포맷팅
    output = f"## '{query}' 검색 결과 ({result['total']}건)\n\n"

    for i, article in enumerate(result["articles"], 1):
        output += f"### {i}. {article['title']}\n"
        output += f"- **출처**: {article['provider']} | {article['published_at']}\n"
        if article.get('byline'):
            output += f"- **기자**: {article['byline']}\n"
        output += f"- **요약**: {article['content'][:200]}...\n"
        if article.get('url'):
            output += f"- **링크**: {article['url']}\n"
        output += "\n"

    return output


@with_retry()
async def search_bigkinds(
    query: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    provider: Optional[List[str]] = None,
    category: Optional[List[str]] = None,
    max_results: int = 10,
    sort_by: str = "date",
) -> Dict[str, Any]:
    """
    BigKinds 뉴스 검색 (내부 함수)

    Args:
        query: 검색어
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)
        provider: 언론사 필터
        category: 카테고리 필터
        max_results: 최대 결과 수
        sort_by: 정렬 기준 (date, relevance)

    Returns:
        검색 결과 딕셔너리
    """
    if not BIGKINDS_API_KEY:
        logger.warning("BIGKINDS_API_KEY not set")
        return {"articles": [], "total": 0, "error": "API key not configured"}

    # 기본 날짜 설정
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
            "sort": {sort_by: "desc"},
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
                "images",
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
                f"{BIGKINDS_API_URL}/search/news",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

            articles = []
            for doc in data.get("documents", []):
                articles.append({
                    "title": doc.get("title", ""),
                    "content": doc.get("content", "")[:500],
                    "published_at": doc.get("published_at", ""),
                    "provider": doc.get("provider", ""),
                    "category": doc.get("category", ""),
                    "byline": doc.get("byline", ""),
                    "url": doc.get("news_url", ""),
                    "images": doc.get("images", []),
                })

            return {
                "articles": articles,
                "total": data.get("total_hits", len(articles)),
                "query": query,
            }

    except httpx.HTTPStatusError as e:
        logger.error(f"BigKinds API HTTP error: {e}")
        return {"articles": [], "total": 0, "error": f"HTTP {e.response.status_code}"}
    except Exception as e:
        logger.error(f"BigKinds API error: {e}")
        return {"articles": [], "total": 0, "error": str(e)}


@tool
async def get_bigkinds_trending(category: str = "경제") -> str:
    """
    빅카인즈에서 트렌딩 키워드를 조회합니다.

    Args:
        category: 카테고리 (경제, 정치, 사회, 국제, IT, 문화, 스포츠)

    Returns:
        오늘의 트렌딩 키워드 목록
    """
    keywords = await get_trending_keywords(category=category, period="day")

    if not keywords:
        return f"'{category}' 분야 트렌딩 키워드를 가져올 수 없습니다."

    output = f"## {category} 분야 오늘의 트렌딩 키워드\n\n"
    for i, kw in enumerate(keywords[:20], 1):
        output += f"{i}. {kw}\n"

    return output


@with_retry()
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
                f"{BIGKINDS_API_URL}/issue/ranking",
                json={
                    "access_key": BIGKINDS_API_KEY,
                    "argument": {
                        "target_date": datetime.now().strftime("%Y-%m-%d"),
                        "category": CATEGORY_MAP.get(category, "economy"),
                        "news_cluster": True,
                    },
                },
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

            keywords = []
            for item in data.get("result", {}).get("topics", []):
                keywords.append(item.get("topic", ""))

            return keywords

    except Exception as e:
        logger.error(f"BigKinds trending error: {e}")
        return []


@tool
async def analyze_bigkinds_topic(
    keyword: str,
    days: int = 30,
) -> str:
    """
    특정 키워드에 대한 뉴스 트렌드를 분석합니다.

    Args:
        keyword: 분석할 키워드 (예: "AI 반도체")
        days: 분석 기간 (일 단위, 기본 30일)

    Returns:
        키워드 관련 트렌드 분석 결과
    """
    result = await analyze_keyword_trend(keyword=keyword, days=days)

    if result.get("error"):
        return f"분석 오류: {result['error']}"

    output = f"## '{keyword}' 트렌드 분석 (최근 {days}일)\n\n"

    # 기사 수 추이
    if result.get("daily_count"):
        output += "### 일별 기사 수\n"
        for date, count in list(result["daily_count"].items())[-7:]:
            output += f"- {date}: {count}건\n"
        output += "\n"

    # 연관 키워드
    if result.get("related_keywords"):
        output += "### 연관 키워드\n"
        for kw in result["related_keywords"][:10]:
            output += f"- {kw}\n"
        output += "\n"

    # 주요 언론사
    if result.get("top_providers"):
        output += "### 주요 보도 언론사\n"
        for provider, count in list(result["top_providers"].items())[:5]:
            output += f"- {provider}: {count}건\n"

    return output


@with_retry()
async def analyze_keyword_trend(
    keyword: str,
    days: int = 30,
) -> Dict[str, Any]:
    """
    키워드 트렌드 분석 (내부 함수)

    Args:
        keyword: 키워드
        days: 분석 기간

    Returns:
        분석 결과
    """
    if not BIGKINDS_API_KEY:
        return {"error": "API key not configured"}

    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # 시계열 분석
            response = await client.post(
                f"{BIGKINDS_API_URL}/analysis/timeline",
                json={
                    "access_key": BIGKINDS_API_KEY,
                    "argument": {
                        "query": keyword,
                        "published_at": {
                            "from": start_date,
                            "until": end_date,
                        },
                        "interval": "day",
                    },
                },
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            timeline_data = response.json()

            # 연관어 분석
            response2 = await client.post(
                f"{BIGKINDS_API_URL}/analysis/word-cloud",
                json={
                    "access_key": BIGKINDS_API_KEY,
                    "argument": {
                        "query": keyword,
                        "published_at": {
                            "from": start_date,
                            "until": end_date,
                        },
                        "provider": ECONOMY_PROVIDERS,
                    },
                },
                headers={"Content-Type": "application/json"},
            )
            response2.raise_for_status()
            wordcloud_data = response2.json()

            # 결과 정리
            daily_count = {}
            for item in timeline_data.get("result", {}).get("timeline", []):
                daily_count[item.get("date", "")] = item.get("count", 0)

            related_keywords = []
            for item in wordcloud_data.get("result", {}).get("words", []):
                related_keywords.append(item.get("word", ""))

            # 언론사별 기사 수 (추가 검색 필요)
            top_providers = {}
            search_result = await search_bigkinds(
                query=keyword,
                start_date=start_date,
                end_date=end_date,
                max_results=100,
            )
            for article in search_result.get("articles", []):
                provider = article.get("provider", "")
                top_providers[provider] = top_providers.get(provider, 0) + 1

            return {
                "keyword": keyword,
                "period": f"{start_date} ~ {end_date}",
                "total_articles": sum(daily_count.values()),
                "daily_count": daily_count,
                "related_keywords": related_keywords,
                "top_providers": dict(sorted(
                    top_providers.items(),
                    key=lambda x: x[1],
                    reverse=True
                )),
            }

    except Exception as e:
        logger.error(f"BigKinds analysis error: {e}")
        return {"error": str(e)}


@tool
async def find_press_release_coverage(
    company: str,
    topic: str,
    days: int = 30,
) -> str:
    """
    특정 기업/기관의 보도자료 관련 기사를 검색합니다.

    Args:
        company: 기업/기관명 (예: "삼성전자")
        topic: 주제/키워드 (예: "실적 발표")
        days: 검색 기간 (일 단위)

    Returns:
        관련 기사 목록
    """
    query = f"{company} {topic}"
    result = await search_bigkinds(
        query=query,
        start_date=(datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"),
        end_date=datetime.now().strftime("%Y-%m-%d"),
        provider=ECONOMY_PROVIDERS,
        max_results=20,
    )

    if result.get("error"):
        return f"검색 오류: {result['error']}"

    if not result.get("articles"):
        return f"'{company}'의 '{topic}' 관련 기사가 없습니다."

    output = f"## {company} - {topic} 관련 보도 ({result['total']}건)\n\n"

    for i, article in enumerate(result["articles"], 1):
        output += f"{i}. **{article['title']}**\n"
        output += f"   - {article['provider']} | {article['published_at']}\n"
        output += f"   - {article['content'][:150]}...\n\n"

    return output


# =============================================================================
# 유틸리티 함수
# =============================================================================

def get_api_status() -> Dict[str, Any]:
    """API 상태 확인"""
    return {
        "configured": bool(BIGKINDS_API_KEY),
        "api_url": BIGKINDS_API_URL,
        "economy_providers": ECONOMY_PROVIDERS,
    }


async def health_check() -> bool:
    """API 연결 상태 확인"""
    if not BIGKINDS_API_KEY:
        return False

    try:
        result = await search_bigkinds(query="테스트", max_results=1)
        return "error" not in result
    except Exception:
        return False
