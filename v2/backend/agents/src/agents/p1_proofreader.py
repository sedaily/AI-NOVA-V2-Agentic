"""
P1 Proofreader Agent
교정 AI - 맞춤법, 문법, 스타일 검사

Temperature: 0.02 (정확성 우선)
"""

from typing import Dict, Any, List
import logging
import json

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class P1ProofreaderAgent(BaseAgent):
    """교정 Agent"""

    def __init__(self):
        super().__init__(
            name="P1Proofreader",
            agent_id="P1",
            temperature=0.02,  # 정확성 우선
            max_tokens=4096,
        )

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        교정 실행

        검사 항목:
        1. 맞춤법 오류
        2. 문법 오류
        3. 문장 구조
        4. 서울경제 스타일 가이드 준수
        5. 팩트 체크 필요 항목
        """
        self.log_step("교정 시작")

        draft = state.get("draft", "")
        if not draft:
            state["corrections"] = []
            return state

        # KB 규칙 검색 (P1 교정 규칙)
        kb_rules = await self.get_kb_context(draft[:500])

        # 스타일북 검색
        style_rules = await self.get_style_context(draft[:300])

        # Few-shot 예시 검색
        examples = await self.get_examples(draft[:300])
        examples_text = ""
        if examples:
            examples_text = "\n[교정 예시]\n" + "\n".join([
                f"잘못: {ex.get('wrong', '')}\n올바름: {ex.get('correct', '')}\n이유: {ex.get('explanation', '')}"
                for ex in examples[:3]
            ])

        # DynamoDB에서 P1 프롬프트 로드 (또는 폴백 템플릿 사용)
        base_prompt = self.get_prompt_with_context(
            prompt_type="P1",
            kb_context=kb_rules,
            style_context=style_rules,
        )

        system_prompt = f"{base_prompt}{examples_text}"

        user_message = f"""다음 기사를 교정해주세요:

{draft}"""

        messages = self.build_messages(system_prompt, user_message)

        try:
            response = await self.invoke(messages)

            # JSON 파싱
            try:
                json_match = response
                if "```json" in response:
                    json_match = response.split("```json")[1].split("```")[0]
                elif "```" in response:
                    json_match = response.split("```")[1].split("```")[0]

                result = json.loads(json_match.strip())
                state["corrections"] = result.get("corrections", [])
                state["style_issues"] = result.get("style_issues", [])

                # 품질 점수 업데이트 (교정 사항 기반)
                high_severity = len([c for c in state["corrections"] if c.get("severity") == "high"])
                medium_severity = len([c for c in state["corrections"] if c.get("severity") == "medium"])

                quality_penalty = (high_severity * 10) + (medium_severity * 3)
                current_score = state.get("quality_score", 85)
                state["quality_score"] = max(0, current_score - quality_penalty)

            except json.JSONDecodeError:
                state["corrections"] = []
                state["proofread_raw"] = response

        except Exception as e:
            logger.error(f"교정 실패: {e}")
            state["corrections"] = []
            state["errors"] = state.get("errors", []) + [str(e)]

        state["current_step"] = "p1_proofreader"
        self.log_step(f"교정 완료: {len(state.get('corrections', []))}건 발견")

        return state


# 모듈 레벨 실행 함수
agent = P1ProofreaderAgent()

async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    return await agent.run(state)
