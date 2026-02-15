"""
IssueCollector Agent
이슈/뉴스 수집을 담당합니다.

사용하는 도구:
- 빅카인즈 API: 한국 뉴스 검색
- 퍼플렉시티 API: 실시간 웹 검색
"""

from typing import Dict, Any, List
import logging

from .base_agent import BaseAgent
from ..tools.bigkinds import search_bigkinds
from ..tools.perplexity import search_perplexity

logger = logging.getLogger(__name__)


class IssueCollectorAgent(BaseAgent):
    """이슈/뉴스 수집 Agent"""

    def __init__(self):
        super().__init__(
            name="IssueCollector",
            agent_id="COLLECTOR",
            temperature=0.3,
        )

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        이슈 수집 실행

        1. 빅카인즈에서 최근 뉴스 검색
        2. 퍼플렉시티에서 실시간 이슈 검색
        3. 보도자료 수신함 확인 (TODO)
        """
        self.log_step("이슈 수집 시작")

        collected_issues = []

        # 1. 빅카인즈 뉴스 검색
        try:
            bigkinds_results = await search_bigkinds(
                query="오늘의 경제 뉴스",
                date_range="1d",
            )
            if bigkinds_results:
                for news in bigkinds_results.get("documents", [])[:5]:
                    collected_issues.append({
                        "source": "bigkinds",
                        "title": news.get("title", ""),
                        "content": news.get("content", ""),
                        "published_at": news.get("published_at", ""),
                        "url": news.get("url", ""),
                        "keywords": news.get("keywords", []),
                    })
            self.log_step(f"빅카인즈 결과: {len(bigkinds_results.get('documents', []))}건")
        except Exception as e:
            logger.error(f"빅카인즈 검색 실패: {e}")

        # 2. 퍼플렉시티 실시간 검색
        try:
            perplexity_results = await search_perplexity(
                query="오늘 한국 경제 주요 이슈",
            )
            if perplexity_results and perplexity_results.get("success"):
                collected_issues.append({
                    "source": "perplexity",
                    "title": "실시간 이슈 요약",
                    "content": perplexity_results.get("content", ""),
                    "citations": perplexity_results.get("citations", []),
                })
            self.log_step("퍼플렉시티 검색 완료")
        except Exception as e:
            logger.error(f"퍼플렉시티 검색 실패: {e}")

        # 상태 업데이트
        state["collected_issues"] = collected_issues
        state["current_step"] = "issue_collector"

        self.log_step(f"이슈 수집 완료: {len(collected_issues)}건")

        return state


# 모듈 레벨 실행 함수
agent = IssueCollectorAgent()

async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    return await agent.run(state)
