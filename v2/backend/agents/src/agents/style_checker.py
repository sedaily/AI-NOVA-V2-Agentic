"""
StyleChecker Agent
스타일북 준수 여부 검사
"""

from typing import Dict, Any
import logging
import json

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class StyleCheckerAgent(BaseAgent):
    """스타일 검사 Agent"""

    def __init__(self):
        super().__init__(
            name="StyleChecker",
            agent_id="STYLE",
            temperature=0.1,
            max_tokens=2048,
        )

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """스타일북 준수 여부 검사"""
        self.log_step("스타일 검사 시작")

        draft = state.get("draft", "")
        if not draft:
            return state

        # 스타일북 규칙 검색
        style_rules = await self.get_style_context(draft[:500])

        system_prompt = f"""당신은 서울경제신문의 스타일 가이드 검토자입니다.

{f'[스타일북 규칙]{chr(10)}{style_rules}' if style_rules else ''}

[검사 항목]
1. 표기법: 숫자, 날짜, 단위 표기
2. 용어: 경제/금융 전문용어 통일
3. 문장 스타일: 서울경제 톤앤매너
4. 금지 표현: 비속어, 차별적 표현
5. 인용 형식: 인용문, 출처 표기

다음 JSON 형식으로 응답해주세요:
{{
    "violations": [
        {{
            "text": "위반 텍스트",
            "rule": "위반한 규칙",
            "suggestion": "수정 제안"
        }}
    ],
    "compliance_score": 0-100,
    "summary": "전체 평가 요약"
}}"""

        user_message = f"다음 기사의 스타일 가이드 준수 여부를 검사해주세요:\n\n{draft}"

        messages = self.build_messages(system_prompt, user_message)

        try:
            response = await self.invoke(messages)

            try:
                json_match = response
                if "```json" in response:
                    json_match = response.split("```json")[1].split("```")[0]
                result = json.loads(json_match.strip())
                state["style_check_result"] = result
            except json.JSONDecodeError:
                state["style_check_result"] = {"raw": response}

        except Exception as e:
            logger.error(f"스타일 검사 실패: {e}")

        state["current_step"] = "style_checker"
        self.log_step("스타일 검사 완료")

        return state


agent = StyleCheckerAgent()

async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    return await agent.run(state)
