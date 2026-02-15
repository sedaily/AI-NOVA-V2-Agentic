"""
LangGraph Tool 통합 테스트

테스트 항목:
1. ToolNode 생성 및 실행
2. BaseAgent 도구 바인딩
3. IssueCollector Agent (도구 사용)
4. IssueCollector Agent (단순 실행)
"""

import asyncio
import logging
import os

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_tool_node():
    """ToolNode 테스트"""
    print(f"\n{'='*60}")
    print("1. ToolNode 테스트")
    print(f"{'='*60}")

    from src.graph.tool_node import ToolNode, create_tool_node
    from src.tools import search_bigkinds_news, perplexity_search_news, search_web

    # ToolNode 생성
    tools = [search_bigkinds_news, perplexity_search_news, search_web]
    tool_node = create_tool_node(tools, name="test_tool_node")

    print(f"등록된 도구: {list(tool_node.tools_by_name.keys())}")

    # 도구 스키마 확인
    schemas = tool_node.get_tool_schemas()
    print(f"\n도구 스키마 ({len(schemas)}개):")
    for schema in schemas:
        print(f"  - {schema['name']}: {schema.get('description', '')[:50]}...")

    return True


async def test_base_agent_tools():
    """BaseAgent 도구 바인딩 테스트"""
    print(f"\n{'='*60}")
    print("2. BaseAgent 도구 바인딩 테스트")
    print(f"{'='*60}")

    from src.agents.base_agent import BaseAgent
    from src.tools import get_research_tools

    # 테스트용 Agent 클래스
    class TestAgent(BaseAgent):
        def __init__(self):
            super().__init__(
                name="TestAgent",
                agent_id="TEST",
                temperature=0.5,
                tools=get_research_tools(),
            )

        async def run(self, state):
            return state

    agent = TestAgent()

    print(f"Agent: {agent.name}")
    print(f"도구 수: {len(agent.tools)}")
    print(f"도구 목록:")
    for tool in agent.tools:
        tool_name = tool.name if hasattr(tool, 'name') else str(tool)
        print(f"  - {tool_name}")

    # LLM with tools 확인
    llm_with_tools = agent.llm_with_tools
    print(f"\nLLM with tools: {type(llm_with_tools).__name__}")

    return True


async def test_issue_collector_simple():
    """IssueCollector 단순 실행 테스트"""
    print(f"\n{'='*60}")
    print("3. IssueCollector 단순 실행 테스트")
    print(f"{'='*60}")

    from src.agents.issue_collector import run_simple

    # 초기 상태
    state = {
        "search_query": "AI 반도체",
        "collected_issues": [],
        "collected_sources": [],
        "errors": [],
        "current_step": "",
    }

    print(f"검색 쿼리: {state['search_query']}")
    print("이슈 수집 중...")

    try:
        result = await run_simple(state)

        print(f"\n수집된 이슈: {len(result.get('collected_issues', []))}건")
        for i, issue in enumerate(result.get("collected_issues", []), 1):
            print(f"\n{i}. {issue.get('title', '제목 없음')}")
            print(f"   출처: {issue.get('source', '')}")
            content = issue.get('content', '')
            if content:
                print(f"   내용: {content[:150]}...")

        if result.get("errors"):
            print(f"\n에러: {result['errors']}")

        return len(result.get("collected_issues", [])) > 0

    except Exception as e:
        print(f"테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_tool_node_execution():
    """ToolNode 실행 테스트"""
    print(f"\n{'='*60}")
    print("4. ToolNode 실행 테스트")
    print(f"{'='*60}")

    from src.graph.tool_node import create_tool_node
    from src.tools import search_web

    # ToolNode 생성
    tool_node = create_tool_node([search_web])

    # 테스트 상태
    state = {
        "tool_calls": [
            {
                "id": "call_1",
                "name": "search_web",
                "args": {"query": "테스트", "num_results": 2},
            }
        ],
        "tool_results": [],
        "pending_tool_calls": True,
        "errors": [],
    }

    print(f"실행할 도구: {state['tool_calls'][0]['name']}")
    print(f"인자: {state['tool_calls'][0]['args']}")

    try:
        result = await tool_node(state)

        print(f"\n실행 결과:")
        print(f"  - pending_tool_calls: {result.get('pending_tool_calls')}")
        print(f"  - tool_results 수: {len(result.get('tool_results', []))}")

        for tr in result.get("tool_results", []):
            print(f"\n  도구: {tr['name']}")
            result_str = str(tr['result'])[:200]
            print(f"  결과: {result_str}...")

        return len(result.get("tool_results", [])) > 0

    except Exception as e:
        print(f"테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_parse_tool_calls():
    """도구 호출 파싱 테스트"""
    print(f"\n{'='*60}")
    print("5. 도구 호출 파싱 테스트")
    print(f"{'='*60}")

    from src.graph.tool_node import parse_tool_calls_from_response

    # 테스트 케이스 1: Dict 형식
    response1 = {
        "tool_calls": [
            {"id": "tc1", "name": "search_web", "args": {"query": "test"}}
        ]
    }
    result1 = parse_tool_calls_from_response(response1)
    print(f"Dict 형식: {len(result1)}개 파싱됨")

    # 테스트 케이스 2: 빈 응답
    response2 = {"content": "일반 텍스트 응답"}
    result2 = parse_tool_calls_from_response(response2)
    print(f"빈 응답: {len(result2)}개 파싱됨")

    return len(result1) == 1 and len(result2) == 0


async def main():
    """메인 테스트"""
    print("\n" + "=" * 60)
    print("  LangGraph Tool 통합 테스트")
    print("=" * 60)

    # 환경 변수 확인
    print("\n환경 변수 확인:")
    print(f"  BIGKINDS_API_KEY: {'설정됨' if os.getenv('BIGKINDS_API_KEY') else '미설정'}")
    print(f"  PERPLEXITY_API_KEY: {'설정됨' if os.getenv('PERPLEXITY_API_KEY') else '미설정'}")
    print(f"  SERPAPI_KEY: {'설정됨' if os.getenv('SERPAPI_KEY') else '미설정'}")

    results = {}

    # 1. ToolNode 테스트
    results["tool_node"] = await test_tool_node()

    # 2. BaseAgent 도구 바인딩
    results["base_agent_tools"] = await test_base_agent_tools()

    # 3. IssueCollector 단순 실행
    results["issue_collector_simple"] = await test_issue_collector_simple()

    # 4. ToolNode 실행
    results["tool_node_execution"] = await test_tool_node_execution()

    # 5. 도구 호출 파싱
    results["parse_tool_calls"] = await test_parse_tool_calls()

    # 결과 요약
    print(f"\n{'='*60}")
    print("테스트 결과 요약")
    print(f"{'='*60}")

    for test_name, success in results.items():
        status = "Pass" if success else "Fail"
        print(f"  {test_name}: {status}")

    print(f"{'='*60}")

    # 사용 예시
    print("\n사용 예시:")
    print("```python")
    print("from src.agents.issue_collector import run_simple")
    print("")
    print("state = {'search_query': 'AI 반도체'}")
    print("result = await run_simple(state)")
    print("print(result['collected_issues'])")
    print("```")
    print()


if __name__ == "__main__":
    asyncio.run(main())
