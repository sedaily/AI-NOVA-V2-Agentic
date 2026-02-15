"""
외부 API 도구 테스트

테스트 항목:
1. BigKinds API (뉴스 검색)
2. Perplexity API (웹 검색/리서치)
3. Web Search (SerpAPI/DuckDuckGo)
4. Tool 목록 확인
"""

import asyncio
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_tool_imports():
    """도구 import 테스트"""
    print(f"\n{'='*60}")
    print("1. 도구 Import 테스트")
    print(f"{'='*60}")

    try:
        from src.tools import (
            # BigKinds
            search_bigkinds_news,
            get_bigkinds_trending,
            analyze_bigkinds_topic,
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
            # Collections
            AGENT_TOOLS,
            get_all_tools,
            get_research_tools,
            get_factcheck_tools,
        )

        print(f"BigKinds 도구:")
        print(f"  - search_bigkinds_news: {search_bigkinds_news.name}")
        print(f"  - get_bigkinds_trending: {get_bigkinds_trending.name}")
        print(f"  - analyze_bigkinds_topic: {analyze_bigkinds_topic.name}")

        print(f"\nPerplexity 도구:")
        print(f"  - perplexity_search_news: {perplexity_search_news.name}")
        print(f"  - research_topic_deep: {research_topic_deep.name}")
        print(f"  - verify_claim: {verify_claim.name}")
        print(f"  - analyze_competitor: {analyze_competitor.name}")
        print(f"  - get_market_insights: {get_market_insights.name}")

        print(f"\nWeb Search 도구:")
        print(f"  - search_web: {search_web.name}")
        print(f"  - search_news_web: {search_news_web.name}")
        print(f"  - verify_fact_web: {verify_fact_web.name}")

        print(f"\n도구 컬렉션:")
        print(f"  - AGENT_TOOLS: {len(AGENT_TOOLS)}개")
        print(f"  - get_all_tools(): {len(get_all_tools())}개")
        print(f"  - get_research_tools(): {len(get_research_tools())}개")
        print(f"  - get_factcheck_tools(): {len(get_factcheck_tools())}개")

        return True

    except ImportError as e:
        print(f"Import 오류: {e}")
        return False


async def test_api_status():
    """API 상태 확인"""
    print(f"\n{'='*60}")
    print("2. API 상태 확인")
    print(f"{'='*60}")

    from src.tools import check_all_apis

    status = await check_all_apis()

    for api_name, api_status in status.items():
        print(f"\n{api_name}:")
        if isinstance(api_status, dict):
            for key, value in api_status.items():
                print(f"  - {key}: {value}")
        else:
            print(f"  - status: {api_status}")

    return True


async def test_bigkinds_tools():
    """BigKinds 도구 테스트"""
    print(f"\n{'='*60}")
    print("3. BigKinds 도구 테스트")
    print(f"{'='*60}")

    from src.tools.bigkinds import get_api_status

    status = get_api_status()
    print(f"API 설정: {status}")

    if not status.get("configured"):
        print("BIGKINDS_API_KEY가 설정되지 않음 - 스킵")
        return True

    # 실제 API 호출 테스트
    from src.tools import search_bigkinds_news

    try:
        result = await search_bigkinds_news.ainvoke({
            "query": "삼성전자 반도체",
            "days": 7,
            "max_results": 3,
        })
        print(f"\n검색 결과 (처음 200자):")
        print(result[:200] + "...")
        return True
    except Exception as e:
        print(f"API 호출 실패: {e}")
        return False


async def test_perplexity_tools():
    """Perplexity 도구 테스트"""
    print(f"\n{'='*60}")
    print("4. Perplexity 도구 테스트")
    print(f"{'='*60}")

    from src.tools.perplexity import get_api_status

    status = get_api_status()
    print(f"API 설정: {status}")

    if not status.get("configured"):
        print("PERPLEXITY_API_KEY가 설정되지 않음 - 스킵")
        return True

    # 실제 API 호출 테스트
    from src.tools import perplexity_search_news

    try:
        result = await perplexity_search_news.ainvoke({
            "query": "AI 반도체 시장 전망",
            "recency": "week",
        })
        print(f"\n검색 결과 (처음 200자):")
        print(result[:200] + "...")
        return True
    except Exception as e:
        print(f"API 호출 실패: {e}")
        return False


async def test_websearch_tools():
    """Web Search 도구 테스트"""
    print(f"\n{'='*60}")
    print("5. Web Search 도구 테스트")
    print(f"{'='*60}")

    from src.tools.web_search import get_api_status

    status = get_api_status()
    print(f"API 설정: {status}")

    # DuckDuckGo는 API 키 없이도 사용 가능
    from src.tools import search_web

    try:
        result = await search_web.ainvoke({
            "query": "현대차 전기차",
            "num_results": 3,
        })
        print(f"\n검색 결과 (처음 200자):")
        print(result[:200] + "...")
        return True
    except Exception as e:
        print(f"검색 실패: {e}")
        return False


async def test_tool_schemas():
    """도구 스키마 확인"""
    print(f"\n{'='*60}")
    print("6. 도구 스키마 확인")
    print(f"{'='*60}")

    from src.tools import get_all_tools

    tools = get_all_tools()

    for tool in tools[:5]:  # 처음 5개만
        print(f"\n{tool.name}:")
        print(f"  - Description: {tool.description[:80]}...")
        if hasattr(tool, 'args_schema') and tool.args_schema:
            schema = tool.args_schema.schema()
            print(f"  - Args: {list(schema.get('properties', {}).keys())}")

    return True


async def test_health_checks():
    """헬스체크 테스트"""
    print(f"\n{'='*60}")
    print("7. 헬스체크 테스트")
    print(f"{'='*60}")

    from src.tools import health_check_all

    print("API 연결 상태 확인 중...")
    results = await health_check_all()

    for api_name, is_healthy in results.items():
        status = "OK" if is_healthy else "FAIL (API 키 미설정 또는 연결 오류)"
        print(f"  - {api_name}: {status}")

    return True


async def main():
    """메인 테스트 실행"""
    print("\n" + "=" * 60)
    print("  외부 API 도구 테스트")
    print("=" * 60)

    results = {}

    # 1. Import 테스트
    results["imports"] = await test_tool_imports()

    # 2. API 상태 확인
    results["api_status"] = await test_api_status()

    # 3. BigKinds 테스트
    results["bigkinds"] = await test_bigkinds_tools()

    # 4. Perplexity 테스트
    results["perplexity"] = await test_perplexity_tools()

    # 5. Web Search 테스트
    results["websearch"] = await test_websearch_tools()

    # 6. 스키마 확인
    results["schemas"] = await test_tool_schemas()

    # 7. 헬스체크
    results["health"] = await test_health_checks()

    # 결과 요약
    print(f"\n{'='*60}")
    print("테스트 결과 요약")
    print(f"{'='*60}")

    for test_name, success in results.items():
        status = "Pass" if success else "Fail"
        print(f"  {test_name}: {status}")

    print(f"{'='*60}")

    # 사용 안내
    print("\n사용 예시:")
    print("```python")
    print("from src.tools import get_all_tools, search_bigkinds_news")
    print("")
    print("# Agent에 도구 바인딩")
    print("tools = get_all_tools()")
    print("llm_with_tools = llm.bind_tools(tools)")
    print("")
    print("# 직접 호출")
    print("result = await search_bigkinds_news.ainvoke({")
    print('    "query": "삼성전자 반도체",')
    print('    "days": 7,')
    print("})")
    print("```")

    print("\n환경 변수:")
    print("  - BIGKINDS_API_KEY: 빅카인즈 API 키")
    print("  - PERPLEXITY_API_KEY: Perplexity API 키")
    print("  - SERPAPI_KEY: SerpAPI 키 (선택, 없으면 DuckDuckGo 사용)")
    print()


if __name__ == "__main__":
    asyncio.run(main())
