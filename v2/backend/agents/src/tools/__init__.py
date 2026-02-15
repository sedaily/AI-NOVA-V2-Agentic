"""
Tools Module
외부 API 연동 도구들

Agent에서 사용 가능한 도구 목록:
- BigKinds: 한국 뉴스 검색 (빅카인즈)
- Perplexity: 실시간 웹 검색 및 AI 요약
- Web Search: 일반 웹/뉴스 검색
- TTS: 음성 합성 (Gemini)
- Image: 이미지 생성 (NanoBanana)
"""

# BigKinds API 도구
from .bigkinds import (
    # LangChain Tools (@tool 데코레이터)
    search_bigkinds_news,
    get_bigkinds_trending,
    analyze_bigkinds_topic,
    find_press_release_coverage,
    # 내부 함수
    search_bigkinds,
    get_trending_keywords,
    analyze_keyword_trend,
    # 유틸리티
    get_api_status as get_bigkinds_status,
    health_check as bigkinds_health_check,
)

# Perplexity API 도구
from .perplexity import (
    # LangChain Tools
    perplexity_search_news,
    research_topic_deep,
    verify_claim,
    analyze_competitor,
    get_market_insights,
    # 내부 함수 (하위 호환성)
    perplexity_search,
    research_topic,
    perplexity_request,
    # 유틸리티
    get_api_status as get_perplexity_status,
    health_check as perplexity_health_check,
)

# Web Search 도구
from .web_search import (
    # LangChain Tools
    search_web,
    search_news_web,
    verify_fact_web,
    search_images,
    # 내부 함수 (하위 호환성)
    web_search,
    search_news,
    verify_fact,
    # 유틸리티
    get_api_status as get_websearch_status,
    health_check as websearch_health_check,
)

# TTS 도구
from .gemini_tts import generate_tts

# Image 생성 도구
from .nanobanana import generate_image


# Agent에서 사용할 Tool 목록
AGENT_TOOLS = [
    # BigKinds
    search_bigkinds_news,
    get_bigkinds_trending,
    analyze_bigkinds_topic,
    find_press_release_coverage,
    # Perplexity
    perplexity_search_news,
    research_topic_deep,
    verify_claim,
    analyze_competitor,
    get_market_insights,
    # Web Search
    search_web,
    search_news_web,
    verify_fact_web,
    search_images,
]


def get_all_tools():
    """모든 Agent 도구 반환"""
    return AGENT_TOOLS


def get_research_tools():
    """리서치용 도구만 반환"""
    return [
        search_bigkinds_news,
        get_bigkinds_trending,
        perplexity_search_news,
        research_topic_deep,
        search_web,
        search_news_web,
    ]


def get_factcheck_tools():
    """팩트체크용 도구 반환"""
    return [
        verify_claim,
        verify_fact_web,
        search_bigkinds_news,
    ]


def get_analysis_tools():
    """분석용 도구 반환"""
    return [
        analyze_bigkinds_topic,
        analyze_competitor,
        get_market_insights,
    ]


async def check_all_apis():
    """모든 API 상태 확인"""
    return {
        "bigkinds": get_bigkinds_status(),
        "perplexity": get_perplexity_status(),
        "web_search": get_websearch_status(),
    }


async def health_check_all():
    """모든 API 헬스체크"""
    results = {}

    try:
        results["bigkinds"] = await bigkinds_health_check()
    except Exception:
        results["bigkinds"] = False

    try:
        results["perplexity"] = await perplexity_health_check()
    except Exception:
        results["perplexity"] = False

    try:
        results["web_search"] = await websearch_health_check()
    except Exception:
        results["web_search"] = False

    return results


__all__ = [
    # BigKinds Tools
    "search_bigkinds_news",
    "get_bigkinds_trending",
    "analyze_bigkinds_topic",
    "find_press_release_coverage",
    "search_bigkinds",
    "get_trending_keywords",
    "analyze_keyword_trend",
    # Perplexity Tools
    "perplexity_search_news",
    "research_topic_deep",
    "verify_claim",
    "analyze_competitor",
    "get_market_insights",
    "perplexity_search",
    "research_topic",
    "perplexity_request",
    # Web Search Tools
    "search_web",
    "search_news_web",
    "verify_fact_web",
    "search_images",
    "web_search",
    "search_news",
    "verify_fact",
    # Other Tools
    "generate_tts",
    "generate_image",
    # Tool Collections
    "AGENT_TOOLS",
    "get_all_tools",
    "get_research_tools",
    "get_factcheck_tools",
    "get_analysis_tools",
    # Health Checks
    "check_all_apis",
    "health_check_all",
]
