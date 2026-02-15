"""
Perplexity API Tool
실시간 웹 검색 및 AI 요약

주요 기능:
- 실시간 웹 검색 (최신 정보)
- 주제 리서치
- 팩트체크 지원
- 경쟁사 분석

API 문서: https://docs.perplexity.ai/
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
PERPLEXITY_API_URL = os.getenv("PERPLEXITY_API_URL", "https://api.perplexity.ai")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")

# 재시도 설정
MAX_RETRIES = 3
RETRY_DELAY = 1.0

# 모델 설정
MODELS = {
    "fast": "llama-3.1-sonar-small-128k-online",
    "balanced": "llama-3.1-sonar-large-128k-online",
    "pro": "llama-3.1-sonar-huge-128k-online",
}

# 검색 기간 필터
RECENCY_FILTERS = {
    "day": "day",
    "week": "week",
    "month": "month",
    "year": "year",
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
                        logger.warning(f"Perplexity API retry {attempt + 1}/{max_retries}")
            raise last_exception
        return wrapper
    return decorator


@tool
async def perplexity_search_news(
    query: str,
    recency: str = "week",
    focus_economy: bool = True,
) -> str:
    """
    Perplexity로 최신 뉴스 및 정보를 검색합니다.

    Args:
        query: 검색할 키워드 또는 질문 (예: "삼성전자 AI 반도체 전망")
        recency: 검색 기간 (day, week, month)
        focus_economy: 경제/비즈니스 중심 검색 여부

    Returns:
        검색 결과 요약 및 출처
    """
    system_content = """You are a professional business news researcher.
Provide accurate, well-sourced information focusing on:
- Business and economic impact
- Key statistics and data
- Recent developments
- Expert opinions

Answer in Korean. Be concise but comprehensive."""

    if focus_economy:
        query = f"[경제/비즈니스 관점] {query}"

    result = await perplexity_request(
        query=query,
        system_prompt=system_content,
        max_tokens=2048,
        recency_filter=RECENCY_FILTERS.get(recency, "week"),
    )

    if result.get("error"):
        return f"검색 오류: {result['error']}"

    # 결과 포맷팅
    output = f"## Perplexity 검색 결과\n\n"
    output += f"**쿼리**: {query}\n\n"
    output += f"### 요약\n{result.get('answer', '결과 없음')}\n\n"

    if result.get("sources"):
        output += "### 출처\n"
        for i, source in enumerate(result["sources"][:5], 1):
            output += f"{i}. {source}\n"

    return output


@tool
async def research_topic_deep(
    topic: str,
    focus_areas: str = "",
    include_data: bool = True,
) -> str:
    """
    특정 주제에 대해 심층 리서치를 수행합니다.

    Args:
        topic: 리서치할 주제 (예: "전기차 배터리 시장")
        focus_areas: 집중 분석 영역 (쉼표 구분, 예: "시장규모,주요업체,기술동향")
        include_data: 통계/데이터 포함 여부

    Returns:
        주제에 대한 심층 분석 결과
    """
    focus_list = [f.strip() for f in focus_areas.split(",") if f.strip()]
    focus_str = f"\n\n집중 분석 영역: {', '.join(focus_list)}" if focus_list else ""

    data_request = """
6. 관련 통계/데이터 (가능한 경우)
7. 시장 전망""" if include_data else ""

    query = f"""다음 주제에 대해 심층 리서치를 수행해주세요:

주제: {topic}
{focus_str}

다음 항목을 포함해 답변해주세요:
1. 핵심 요약 (3-5문장)
2. 배경 및 현황
3. 주요 이해관계자 (기업, 기관, 인물)
4. 최근 주요 동향 (최근 1개월)
5. 전문가 의견 및 전망
{data_request}

모든 정보는 출처를 명시해주세요."""

    result = await perplexity_request(
        query=query,
        system_prompt="You are a senior business analyst. Provide thorough, well-researched analysis in Korean.",
        max_tokens=4096,
        recency_filter="month",
        model="balanced",
    )

    if result.get("error"):
        return f"리서치 오류: {result['error']}"

    output = f"## '{topic}' 심층 리서치\n\n"
    output += result.get("answer", "리서치 결과를 가져올 수 없습니다.")

    if result.get("sources"):
        output += "\n\n### 참고 출처\n"
        for i, source in enumerate(result["sources"][:10], 1):
            output += f"{i}. {source}\n"

    return output


@tool
async def verify_claim(
    claim: str,
    context: str = "",
) -> str:
    """
    특정 주장이나 사실의 정확성을 검증합니다.

    Args:
        claim: 검증할 주장 (예: "삼성전자가 2024년 반도체 투자 50조원 발표")
        context: 추가 맥락 정보

    Returns:
        팩트체크 결과
    """
    context_str = f"\n\n추가 맥락: {context}" if context else ""

    query = f"""다음 주장의 사실 여부를 검증해주세요:

주장: {claim}
{context_str}

다음 형식으로 답변해주세요:
1. 검증 결과: [사실/부분사실/미확인/허위]
2. 근거: 이 결론에 도달한 이유
3. 관련 사실: 확인된 정확한 정보
4. 출처: 검증에 사용된 신뢰할 수 있는 출처"""

    result = await perplexity_request(
        query=query,
        system_prompt="You are a fact-checker. Verify claims objectively using reliable sources. Answer in Korean.",
        max_tokens=1500,
        recency_filter="month",
    )

    if result.get("error"):
        return f"검증 오류: {result['error']}"

    output = f"## 팩트체크 결과\n\n"
    output += f"**검증 대상**: {claim}\n\n"
    output += result.get("answer", "검증 결과를 가져올 수 없습니다.")

    return output


@tool
async def analyze_competitor(
    company: str,
    competitors: str = "",
    aspects: str = "시장점유율,제품,전략",
) -> str:
    """
    기업 경쟁 분석을 수행합니다.

    Args:
        company: 분석 대상 기업 (예: "삼성전자")
        competitors: 비교 대상 기업들 (쉼표 구분, 예: "SK하이닉스,마이크론")
        aspects: 분석 측면 (쉼표 구분, 예: "시장점유율,제품,전략")

    Returns:
        경쟁 분석 결과
    """
    competitor_list = [c.strip() for c in competitors.split(",") if c.strip()]
    aspect_list = [a.strip() for a in aspects.split(",") if a.strip()]

    competitor_str = f"\n비교 대상: {', '.join(competitor_list)}" if competitor_list else ""
    aspect_str = f"\n분석 측면: {', '.join(aspect_list)}" if aspect_list else ""

    query = f"""다음 기업에 대한 경쟁 분석을 수행해주세요:

대상 기업: {company}
{competitor_str}
{aspect_str}

다음을 포함해 분석해주세요:
1. 기업 개요 및 핵심 사업
2. 시장 내 포지션
3. 경쟁 우위 요소
4. 주요 경쟁사 대비 강점/약점
5. 최근 전략적 움직임
6. 향후 전망

최신 정보를 바탕으로 분석해주세요."""

    result = await perplexity_request(
        query=query,
        system_prompt="You are a business strategy consultant. Provide competitive analysis in Korean.",
        max_tokens=3000,
        recency_filter="month",
        model="balanced",
    )

    if result.get("error"):
        return f"분석 오류: {result['error']}"

    output = f"## {company} 경쟁 분석\n\n"
    output += result.get("answer", "분석 결과를 가져올 수 없습니다.")

    if result.get("sources"):
        output += "\n\n### 출처\n"
        for i, source in enumerate(result["sources"][:5], 1):
            output += f"{i}. {source}\n"

    return output


@tool
async def get_market_insights(
    industry: str,
    region: str = "한국",
) -> str:
    """
    특정 산업/시장에 대한 인사이트를 제공합니다.

    Args:
        industry: 산업/시장 (예: "AI 반도체", "전기차 배터리")
        region: 지역 (예: "한국", "글로벌", "미국")

    Returns:
        시장 인사이트
    """
    query = f"""{region} {industry} 시장에 대해 분석해주세요:

1. 시장 현황 및 규모
2. 주요 플레이어
3. 최근 트렌드 (1개월 내)
4. 성장 동력 및 리스크
5. 향후 전망
6. 주요 뉴스/이슈

데이터와 출처를 포함해 답변해주세요."""

    result = await perplexity_request(
        query=query,
        system_prompt="You are a market research analyst. Provide market insights in Korean with data.",
        max_tokens=2500,
        recency_filter="week",
    )

    if result.get("error"):
        return f"분석 오류: {result['error']}"

    output = f"## {region} {industry} 시장 인사이트\n\n"
    output += result.get("answer", "인사이트를 가져올 수 없습니다.")

    return output


# =============================================================================
# 내부 함수
# =============================================================================


@with_retry()
async def perplexity_request(
    query: str,
    system_prompt: str = "You are a helpful assistant. Answer in Korean.",
    max_tokens: int = 2048,
    recency_filter: str = "week",
    model: str = "fast",
) -> Dict[str, Any]:
    """
    Perplexity API 요청 (내부 함수)

    Args:
        query: 검색 쿼리
        system_prompt: 시스템 프롬프트
        max_tokens: 최대 토큰 수
        recency_filter: 검색 기간 필터
        model: 모델 유형 (fast, balanced, pro)

    Returns:
        API 응답 딕셔너리
    """
    if not PERPLEXITY_API_KEY:
        logger.warning("PERPLEXITY_API_KEY not set")
        return {"answer": "", "sources": [], "error": "API key not configured"}

    model_id = MODELS.get(model, MODELS["fast"])

    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ],
        "max_tokens": max_tokens,
        "search_recency_filter": recency_filter,
        "return_citations": True,
        "return_related_questions": False,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{PERPLEXITY_API_URL}/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()

            # 응답 파싱
            answer = ""
            sources = []

            if "choices" in data and len(data["choices"]) > 0:
                message = data["choices"][0].get("message", {})
                answer = message.get("content", "")

            if "citations" in data:
                sources = data["citations"]

            return {
                "answer": answer,
                "sources": sources,
                "model": model_id,
                "query": query,
            }

    except httpx.HTTPStatusError as e:
        logger.error(f"Perplexity API HTTP error: {e}")
        return {"answer": "", "sources": [], "error": f"HTTP {e.response.status_code}"}
    except Exception as e:
        logger.error(f"Perplexity API error: {e}")
        return {"answer": "", "sources": [], "error": str(e)}


# =============================================================================
# 유틸리티 함수
# =============================================================================


def get_api_status() -> Dict[str, Any]:
    """API 상태 확인"""
    return {
        "configured": bool(PERPLEXITY_API_KEY),
        "api_url": PERPLEXITY_API_URL,
        "models": list(MODELS.keys()),
    }


async def health_check() -> bool:
    """API 연결 상태 확인"""
    if not PERPLEXITY_API_KEY:
        return False

    try:
        result = await perplexity_request(query="테스트", max_tokens=100)
        return "error" not in result
    except Exception:
        return False


# 하위 호환성을 위한 alias
async def perplexity_search(
    query: str,
    model: str = "llama-3.1-sonar-small-128k-online",
    max_tokens: int = 1024,
    search_recency_filter: str = "week",
) -> Dict[str, Any]:
    """하위 호환성을 위한 wrapper"""
    return await perplexity_request(
        query=query,
        max_tokens=max_tokens,
        recency_filter=search_recency_filter,
    )


async def research_topic(
    topic: str,
    focus_areas: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """하위 호환성을 위한 wrapper"""
    focus_str = ", ".join(focus_areas) if focus_areas else ""
    result_str = await research_topic_deep.ainvoke({
        "topic": topic,
        "focus_areas": focus_str,
        "include_data": True,
    })
    return {"answer": result_str, "sources": []}
