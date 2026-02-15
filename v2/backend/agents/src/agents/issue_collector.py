"""
IssueCollector Agent
이슈/뉴스 수집을 담당합니다.

사용하는 도구:
- search_bigkinds_news: 한국 뉴스 검색 (빅카인즈)
- perplexity_search_news: 실시간 웹 검색 (Perplexity)
- get_bigkinds_trending: 트렌딩 키워드 조회

Tool 통합:
- LLM이 자동으로 필요한 도구를 선택하여 호출
- 검색 결과를 분석하여 이슈 목록 생성
"""

from typing import Dict, Any, List
import logging

from .base_agent import BaseAgent
from ..tools import (
    search_bigkinds_news,
    get_bigkinds_trending,
    perplexity_search_news,
    get_research_tools,
)

logger = logging.getLogger(__name__)

# 이슈 수집용 시스템 프롬프트
ISSUE_COLLECTOR_PROMPT = """당신은 경제 전문 뉴스 에디터입니다.
다음 도구를 사용하여 오늘의 주요 경제 이슈를 수집하고 분석해주세요.

사용 가능한 도구:
1. search_bigkinds_news: 빅카인즈에서 한국 뉴스 검색
2. get_bigkinds_trending: 경제 분야 트렌딩 키워드 조회
3. perplexity_search_news: 실시간 웹 검색 (최신 정보)

수집 절차:
1. 먼저 트렌딩 키워드를 확인하세요
2. 주요 키워드로 뉴스를 검색하세요
3. 실시간 웹 검색으로 최신 동향을 파악하세요

결과 형식:
각 이슈에 대해 다음 정보를 포함해주세요:
- 제목: 이슈 제목
- 요약: 핵심 내용 2-3문장
- 출처: 원본 소스
- 중요도: 상/중/하
- 키워드: 관련 키워드 목록"""


class IssueCollectorAgent(BaseAgent):
    """이슈/뉴스 수집 Agent (도구 사용)"""

    def __init__(self):
        super().__init__(
            name="IssueCollector",
            agent_id="COLLECTOR",
            temperature=0.3,
            tools=get_research_tools(),  # 리서치 도구 바인딩
        )

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        이슈 수집 실행

        1. LLM이 도구를 사용하여 뉴스/이슈 검색
        2. 검색 결과를 분석하여 이슈 목록 생성
        3. 상태에 저장
        """
        self.log_step("이슈 수집 시작")

        # 검색 쿼리 (사용자 입력 또는 기본값)
        search_query = state.get("search_query", "오늘의 경제 주요 이슈")

        # 메시지 구성
        user_message = f"""오늘의 주요 경제 이슈를 수집해주세요.

검색 키워드: {search_query}

1. 먼저 트렌딩 키워드를 확인하고
2. 주요 키워드로 뉴스를 검색하고
3. 최신 동향을 파악한 후
4. 중요도 순으로 이슈 목록을 정리해주세요.

각 이슈는 JSON 형식으로:
{{
    "title": "이슈 제목",
    "summary": "핵심 내용",
    "source": "출처",
    "importance": "상/중/하",
    "keywords": ["키워드1", "키워드2"]
}}"""

        messages = self.build_messages(ISSUE_COLLECTOR_PROMPT, user_message)

        try:
            # 도구 사용 가능한 LLM 호출
            result = await self.invoke_with_tools(messages, max_iterations=5)

            # 결과 파싱
            collected_issues = self._parse_issues(result["content"])

            # 도구 결과에서 추가 정보 추출
            for tr in result.get("tool_results", []):
                if tr["name"] in ["search_bigkinds_news", "perplexity_search_news"]:
                    # 도구 결과를 소스로 추가
                    state.setdefault("collected_sources", []).append({
                        "source": tr["name"],
                        "content": str(tr["result"])[:2000],
                    })

            state["collected_issues"] = collected_issues
            state["tool_calls_log"] = result.get("tool_calls", [])

            self.log_step(f"이슈 수집 완료: {len(collected_issues)}건, 도구 호출: {len(result.get('tool_calls', []))}회")

        except Exception as e:
            logger.error(f"이슈 수집 실패: {e}")
            state["collected_issues"] = []
            state["errors"] = state.get("errors", []) + [f"IssueCollector error: {str(e)}"]

        state["current_step"] = "issue_collector"
        return state

    def _parse_issues(self, content: str) -> List[Dict[str, Any]]:
        """LLM 응답에서 이슈 목록 파싱"""
        import json
        import re

        issues = []

        # JSON 배열 찾기
        json_match = re.search(r'\[[\s\S]*\]', content)
        if json_match:
            try:
                issues = json.loads(json_match.group())
                return issues
            except json.JSONDecodeError:
                pass

        # 개별 JSON 객체 찾기
        json_objects = re.findall(r'\{[^{}]+\}', content)
        for obj_str in json_objects:
            try:
                obj = json.loads(obj_str)
                if "title" in obj:
                    issues.append(obj)
            except json.JSONDecodeError:
                continue

        # JSON 파싱 실패 시 텍스트 분석
        if not issues and content:
            issues.append({
                "title": "수집된 이슈",
                "summary": content[:500],
                "source": "llm_analysis",
                "importance": "중",
                "keywords": [],
            })

        return issues

    async def run_simple(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        단순 이슈 수집 (도구 직접 호출)

        도구를 LLM 없이 직접 호출하여 빠르게 수집
        """
        self.log_step("단순 이슈 수집 시작")

        collected_issues = []
        search_query = state.get("search_query", "경제 뉴스")

        # 1. 트렌딩 키워드 조회
        try:
            trending_result = await get_bigkinds_trending.ainvoke({"category": "경제"})
            if trending_result:
                collected_issues.append({
                    "source": "bigkinds_trending",
                    "title": "오늘의 트렌딩 키워드",
                    "content": trending_result,
                    "importance": "상",
                })
            self.log_step("트렌딩 키워드 수집 완료")
        except Exception as e:
            logger.error(f"트렌딩 키워드 조회 실패: {e}")

        # 2. 빅카인즈 뉴스 검색
        try:
            bigkinds_result = await search_bigkinds_news.ainvoke({
                "query": search_query,
                "days": 1,
                "max_results": 5,
            })
            if bigkinds_result:
                collected_issues.append({
                    "source": "bigkinds",
                    "title": f"'{search_query}' 관련 뉴스",
                    "content": bigkinds_result,
                    "importance": "상",
                })
            self.log_step(f"빅카인즈 검색 완료: {search_query}")
        except Exception as e:
            logger.error(f"빅카인즈 검색 실패: {e}")

        # 3. Perplexity 실시간 검색
        try:
            perplexity_result = await perplexity_search_news.ainvoke({
                "query": f"오늘 한국 경제 {search_query}",
                "recency": "day",
            })
            if perplexity_result:
                collected_issues.append({
                    "source": "perplexity",
                    "title": "실시간 이슈 요약",
                    "content": perplexity_result,
                    "importance": "상",
                })
            self.log_step("Perplexity 검색 완료")
        except Exception as e:
            logger.error(f"Perplexity 검색 실패: {e}")

        state["collected_issues"] = collected_issues
        state["current_step"] = "issue_collector"

        self.log_step(f"단순 이슈 수집 완료: {len(collected_issues)}건")

        return state


# 모듈 레벨 실행 함수
agent = IssueCollectorAgent()


async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    """기본 실행 (도구 사용)"""
    return await agent.run(state)


async def run_simple(state: Dict[str, Any]) -> Dict[str, Any]:
    """단순 실행 (도구 직접 호출)"""
    return await agent.run_simple(state)
