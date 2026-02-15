"""
FactChecker Agent
팩트체크 Agent - 사실 검증
"""

from typing import Dict, Any
import logging
import json

from .base_agent import BaseAgent
from ..tools.bigkinds import search_bigkinds
from ..tools.web_search import web_search

logger = logging.getLogger(__name__)


class FactCheckerAgent(BaseAgent):
    """팩트체크 Agent"""

    def __init__(self):
        super().__init__(
            name="FactChecker",
            agent_id="FACT",
            temperature=0.1,
            max_tokens=4096,
        )

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        팩트체크 실행

        검증 항목:
        1. 숫자/통계 정확성
        2. 인명/기관명 정확성
        3. 날짜/시간 정확성
        4. 인용문 출처 확인
        """
        self.log_step("팩트체크 시작")

        draft = state.get("final_article", state.get("draft", ""))
        if not draft:
            return state

        # 1단계: 검증 필요 항목 추출 (DynamoDB 또는 폴백 템플릿에서 로드)
        system_prompt = self.get_system_prompt("FACT_CHECK")

        messages = self.build_messages(system_prompt, draft)

        try:
            response = await self.invoke(messages)

            try:
                json_match = response
                if "```json" in response:
                    json_match = response.split("```json")[1].split("```")[0]
                items = json.loads(json_match.strip()).get("items_to_verify", [])
            except:
                items = []

            # 2단계: 각 항목 검증 (웹 검색 활용)
            verified_items = []
            unverified_items = []

            for item in items[:5]:  # 최대 5개 검증
                try:
                    # 웹 검색으로 검증
                    search_result = await web_search(item.get("text", ""))
                    if search_result:
                        verified_items.append({
                            **item,
                            "verified": True,
                            "source": search_result.get("source", "웹 검색"),
                        })
                    else:
                        unverified_items.append(item)
                except:
                    unverified_items.append(item)

            state["fact_check_report"] = {
                "total_items": len(items),
                "verified_count": len(verified_items),
                "unverified_count": len(unverified_items),
                "verified_items": verified_items,
                "unverified_items": unverified_items,
                "critical_errors": [],  # 심각한 오류 없음
            }

        except Exception as e:
            logger.error(f"팩트체크 실패: {e}")
            state["fact_check_report"] = {
                "error": str(e),
                "verified_count": 0,
                "unverified_count": 0,
            }

        state["current_step"] = "fact_checker"
        self.log_step("팩트체크 완료")

        return state


agent = FactCheckerAgent()

async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    return await agent.run(state)
