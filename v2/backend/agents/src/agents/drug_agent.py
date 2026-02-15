"""
DrugAgent
약물 처리 Agent - 기사 길이 조절
"""

from typing import Dict, Any
import logging

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class DrugAgent(BaseAgent):
    """약물 처리 (길이 조절) Agent"""

    def __init__(self):
        super().__init__(
            name="DrugAgent",
            agent_id="DRUG",
            temperature=0.3,
            max_tokens=8192,
        )

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        기사 길이 조절

        기준:
        - 일보: 300~500자
        - 지면: 1000~1500자
        - 온라인: 800~1200자
        """
        self.log_step("길이 조절 시작")

        draft = state.get("draft", "")
        article_type = state.get("article_type", "online")

        if not draft:
            return state

        # 목표 길이
        target_length = {
            "daily": (300, 500),
            "print": (1000, 1500),
            "online": (800, 1200),
        }
        min_len, max_len = target_length.get(article_type, (800, 1200))
        current_len = len(draft)

        # 길이가 적절하면 패스
        if min_len <= current_len <= max_len:
            self.log_step(f"길이 적절함: {current_len}자")
            state["final_article"] = draft
            return state

        # 조절 필요
        if current_len < min_len:
            action = "expand"
            instruction = f"기사를 {min_len}자 이상으로 확장해주세요. 배경 설명이나 전문가 의견을 추가하세요."
        else:
            action = "reduce"
            instruction = f"기사를 {max_len}자 이내로 축약해주세요. 핵심만 남기고 중복되거나 덜 중요한 내용을 제거하세요."

        system_prompt = f"""당신은 기사 편집 전문가입니다.

[목표]
현재 길이: {current_len}자
목표 길이: {min_len}~{max_len}자
필요 작업: {"확장" if action == "expand" else "축약"}

[규칙]
- 핵심 팩트는 반드시 유지
- 문장의 자연스러움 유지
- 서울경제 스타일 유지

{instruction}

수정된 기사만 반환하세요."""

        user_message = draft

        messages = self.build_messages(system_prompt, user_message)

        try:
            response = await self.invoke(messages)
            state["draft"] = response
            state["final_article"] = response
            self.log_step(f"길이 조절 완료: {current_len}자 → {len(response)}자")

        except Exception as e:
            logger.error(f"길이 조절 실패: {e}")
            state["final_article"] = draft

        state["current_step"] = "drug_agent"

        return state


agent = DrugAgent()

async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    return await agent.run(state)
