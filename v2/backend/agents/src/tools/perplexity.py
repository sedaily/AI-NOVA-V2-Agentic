"""
Perplexity API Tool
실시간 웹 검색 및 요약
"""

import os
import httpx
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

PERPLEXITY_API_URL = "https://api.perplexity.ai"
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")


async def perplexity_search(
    query: str,
    model: str = "llama-3.1-sonar-small-128k-online",
    max_tokens: int = 1024,
    search_recency_filter: str = "week",
) -> Dict[str, Any]:
    """
    Perplexity 실시간 웹 검색

    Args:
        query: 검색 쿼리
        model: Perplexity 모델
        max_tokens: 최대 토큰 수
        search_recency_filter: 검색 기간 필터 (day, week, month)

    Returns:
        검색 결과 및 요약
    """
    if not PERPLEXITY_API_KEY:
        logger.warning("PERPLEXITY_API_KEY not set")
        return {"answer": "", "sources": [], "error": "API key not configured"}

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful research assistant. Provide accurate, well-sourced information. Answer in Korean.",
            },
            {
                "role": "user",
                "content": query,
            },
        ],
        "max_tokens": max_tokens,
        "search_recency_filter": search_recency_filter,
        "return_citations": True,
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
                "model": model,
                "query": query,
            }

    except httpx.HTTPStatusError as e:
        logger.error(f"Perplexity API HTTP error: {e}")
        return {"answer": "", "sources": [], "error": str(e)}
    except Exception as e:
        logger.error(f"Perplexity API error: {e}")
        return {"answer": "", "sources": [], "error": str(e)}


async def research_topic(
    topic: str,
    focus_areas: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    특정 주제 심층 리서치

    Args:
        topic: 리서치 주제
        focus_areas: 집중 분야 리스트

    Returns:
        리서치 결과
    """
    focus_str = ""
    if focus_areas:
        focus_str = f"\n\n집중 분야: {', '.join(focus_areas)}"

    query = f"""다음 주제에 대해 최신 정보를 조사해주세요:

주제: {topic}
{focus_str}

다음 형식으로 답변해주세요:
1. 핵심 요약 (3-5문장)
2. 주요 사실/데이터
3. 최근 동향
4. 관련 기관/인물
5. 출처"""

    return await perplexity_search(
        query=query,
        max_tokens=2048,
        search_recency_filter="week",
    )
