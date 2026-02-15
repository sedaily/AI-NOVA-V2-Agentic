"""
InfographicAgent
인포그래픽 생성 Agent
"""

from typing import Dict, Any
import logging

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class InfographicAgent(BaseAgent):
    """인포그래픽 생성 Agent"""

    def __init__(self):
        super().__init__(
            name="InfographicAgent",
            agent_id="INFOGRAPHIC",
            temperature=0.5,
            max_tokens=2048,
        )

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        인포그래픽 데이터 추출 및 생성

        처리:
        1. 기사에서 시각화 가능한 데이터 추출
        2. 차트/그래프 타입 결정
        3. 인포그래픽 생성 요청
        """
        self.log_step("인포그래픽 생성 시작")

        draft = state.get("final_article", state.get("draft", ""))
        if not draft:
            return state

        # 데이터 추출
        system_prompt = """기사에서 인포그래픽으로 시각화할 수 있는 데이터를 추출해주세요.

다음 JSON 형식으로 응답:
{
    "has_data": true/false,
    "data_points": [
        {"label": "라벨", "value": 숫자, "unit": "단위"}
    ],
    "chart_type": "bar|line|pie|comparison",
    "title": "인포그래픽 제목",
    "source": "데이터 출처"
}"""

        messages = self.build_messages(system_prompt, draft[:2000])

        try:
            response = await self.invoke(messages)

            import json
            try:
                json_match = response
                if "```json" in response:
                    json_match = response.split("```json")[1].split("```")[0]
                data = json.loads(json_match.strip())

                if data.get("has_data"):
                    # TODO: 실제 인포그래픽 생성 API 호출
                    state["infographic_data"] = data
                    state["infographic_url"] = None  # 생성 후 URL 설정
                    self.log_step("인포그래픽 데이터 추출 완료")
                else:
                    self.log_step("시각화 가능한 데이터 없음")

            except json.JSONDecodeError:
                self.log_step("데이터 추출 실패")

        except Exception as e:
            logger.error(f"인포그래픽 생성 실패: {e}")

        state["current_step"] = "infographic_agent"

        return state


agent = InfographicAgent()

async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    return await agent.run(state)
