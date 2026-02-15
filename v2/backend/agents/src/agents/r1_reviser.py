"""
R1 Reviser Agent
퇴고 시스템 - 문장 다듬기 및 개선
"""

from typing import Dict, Any
import logging

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class R1ReviserAgent(BaseAgent):
    """퇴고 Agent"""

    def __init__(self):
        super().__init__(
            name="R1Reviser",
            agent_id="R1",
            temperature=0.5,
            max_tokens=8192,
        )

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        퇴고 실행

        개선 항목:
        1. 문장의 간결성과 명확성
        2. 논리적 흐름 강화
        3. 독자 가독성 향상
        4. 서울경제 톤앤매너 적용
        5. 교정 사항 반영
        """
        self.log_step("퇴고 시작")

        draft = state.get("draft", "")
        corrections = state.get("corrections", [])
        revision_count = state.get("revision_count", 0)

        if not draft:
            return state

        # KB 규칙 검색
        kb_rules = await self.get_kb_context(draft[:500])

        # 스타일북 검색
        style_rules = await self.get_style_context(draft[:300])

        # 교정 사항 텍스트화
        corrections_text = ""
        if corrections:
            corrections_text = "\n".join([
                f"- {c.get('original', '')} → {c.get('corrected', '')} ({c.get('reason', '')})"
                for c in corrections[:10]
            ])

        system_prompt = f"""당신은 서울경제신문의 퇴고 전문가입니다.

{f'[퇴고 규칙]{chr(10)}{kb_rules}' if kb_rules else ''}

{f'[스타일북]{chr(10)}{style_rules}' if style_rules else ''}

[퇴고 원칙]
1. 문장의 간결성: 불필요한 수식어 제거
2. 명확성: 모호한 표현 구체화
3. 논리적 흐름: 문단 간 연결 강화
4. 가독성: 긴 문장 분리, 적절한 문단 나누기
5. 톤앤매너: 서울경제 스타일 일관성 유지

{f'[반영할 교정 사항]{chr(10)}{corrections_text}' if corrections_text else ''}

수정된 기사 전문을 반환해주세요. 설명 없이 기사 본문만 출력하세요."""

        user_message = f"""다음 기사를 퇴고해주세요 (수정 {revision_count + 1}회차):

{draft}"""

        messages = self.build_messages(system_prompt, user_message)

        try:
            response = await self.invoke(messages)

            # 응답에서 불필요한 설명 제거
            revised_draft = self._clean_response(response)

            state["draft"] = revised_draft
            state["revision_count"] = revision_count + 1

            # 품질 점수 소폭 상승 (퇴고 효과)
            current_score = state.get("quality_score", 70)
            state["quality_score"] = min(100, current_score + 5)

        except Exception as e:
            logger.error(f"퇴고 실패: {e}")
            state["errors"] = state.get("errors", []) + [str(e)]

        state["current_step"] = "r1_reviser"
        self.log_step(f"퇴고 완료 ({revision_count + 1}회차)")

        return state

    def _clean_response(self, response: str) -> str:
        """응답 정리 (설명 텍스트 제거)"""
        # 마크다운 코드 블록 제거
        if "```" in response:
            parts = response.split("```")
            if len(parts) >= 3:
                return parts[1].strip()

        # "수정된 기사:" 같은 prefix 제거
        prefixes = [
            "수정된 기사:",
            "퇴고 결과:",
            "개선된 기사:",
            "다음은 수정된",
        ]
        for prefix in prefixes:
            if prefix in response:
                response = response.split(prefix, 1)[-1].strip()

        return response.strip()


# 모듈 레벨 실행 함수
agent = R1ReviserAgent()

async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    return await agent.run(state)
