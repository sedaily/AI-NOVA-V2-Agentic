"""
LayoutAgent
기사 레이아웃 구조화 Agent
"""

from typing import Dict, Any
import logging

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class LayoutAgent(BaseAgent):
    """레이아웃 구조화 Agent"""

    def __init__(self):
        super().__init__(
            name="LayoutAgent",
            agent_id="LAYOUT",
            temperature=0.3,
            max_tokens=4096,
        )

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        레이아웃 구조화

        처리 항목:
        1. 문단 분리
        2. 소제목 배치
        3. 인용문 강조
        4. 핵심 요약 박스
        """
        self.log_step("레이아웃 구조화 시작")

        draft = state.get("draft", "")
        article_type = state.get("article_type", "online")

        if not draft:
            return state

        system_prompt = f"""당신은 뉴스 레이아웃 전문가입니다.

[{article_type} 기사 레이아웃 규칙]
- 온라인: 소제목 2-3개, 짧은 문단 (3-4문장), 핵심요약 박스
- 지면: 소제목 3-4개, 인용문 별도 표시, 관련기사 언급
- 일보: 소제목 없음, 단일 문단 가능

[구조화 요소]
1. ## 소제목 형식
2. > 인용문 형식
3. **강조** 형식
4. [핵심요약] 박스

기사를 구조화하여 반환해주세요. 내용은 변경하지 말고 형식만 정리하세요."""

        user_message = f"다음 기사를 {article_type} 형식에 맞게 레이아웃을 구조화해주세요:\n\n{draft}"

        messages = self.build_messages(system_prompt, user_message)

        try:
            response = await self.invoke(messages)
            state["draft"] = response
            state["layout_structure"] = {
                "type": article_type,
                "has_subheadings": "##" in response,
                "has_quotes": ">" in response,
            }

        except Exception as e:
            logger.error(f"레이아웃 구조화 실패: {e}")

        state["current_step"] = "layout_agent"
        self.log_step("레이아웃 구조화 완료")

        return state


agent = LayoutAgent()

async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    return await agent.run(state)
