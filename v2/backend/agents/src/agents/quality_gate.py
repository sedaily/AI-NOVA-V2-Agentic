"""
QualityGate Agent
품질 검사 Agent - 기사 품질 점수 평가
"""

from typing import Dict, Any
import logging
import json

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class QualityGateAgent(BaseAgent):
    """품질 검사 Agent"""

    def __init__(self):
        super().__init__(
            name="QualityGate",
            agent_id="QUALITY",
            temperature=0.1,
            max_tokens=2048,
        )

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        품질 검사 실행

        평가 항목:
        1. 완성도 (구조, 분량)
        2. 정확성 (팩트, 수치)
        3. 가독성 (문장, 용어)
        4. 스타일 (서울경제 톤)
        5. SEO (제목, 키워드)
        """
        self.log_step("품질 검사 시작")

        draft = state.get("draft", "")
        article_type = state.get("article_type", "online")

        if not draft:
            state["quality_score"] = 0
            return state

        system_prompt = """당신은 서울경제신문의 품질 관리 편집자입니다.

[평가 기준]
1. 완성도 (20점): 기사 구조, 적절한 분량, 논리적 흐름
2. 정확성 (25점): 팩트 정확도, 수치 일관성, 출처 명시
3. 가독성 (20점): 문장 명확성, 적절한 용어, 단락 구성
4. 스타일 (20점): 서울경제 톤앤매너, 일관된 문체
5. SEO/매력도 (15점): 제목 매력, 키워드 활용

다음 JSON 형식으로 응답해주세요:
{
    "scores": {
        "completeness": 0-20,
        "accuracy": 0-25,
        "readability": 0-20,
        "style": 0-20,
        "seo": 0-15
    },
    "total_score": 0-100,
    "passed": true/false,
    "issues": ["발견된 문제점"],
    "strengths": ["잘된 점"],
    "recommendations": ["개선 권고사항"]
}"""

        # 기사 유형별 기대 분량
        expected_length = {
            "daily": (300, 500),
            "print": (1000, 1500),
            "online": (800, 1200),
        }
        min_len, max_len = expected_length.get(article_type, (800, 1200))

        user_message = f"""다음 {article_type} 기사의 품질을 평가해주세요.
기대 분량: {min_len}~{max_len}자
실제 분량: {len(draft)}자

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
                state["quality_score"] = result.get("total_score", 70)
                state["quality_report"] = result

            except json.JSONDecodeError:
                # 파싱 실패 시 기본 점수
                state["quality_score"] = 75
                state["quality_report"] = {"raw": response}

        except Exception as e:
            logger.error(f"품질 검사 실패: {e}")
            state["quality_score"] = 70  # 기본 점수
            state["errors"] = state.get("errors", []) + [str(e)]

        state["current_step"] = "quality_gate"
        self.log_step(f"품질 점수: {state.get('quality_score', 0)}점")

        return state


# 모듈 레벨 실행 함수
agent = QualityGateAgent()

async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    return await agent.run(state)
