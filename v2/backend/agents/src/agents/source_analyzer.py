"""
SourceAnalyzer Agent
소스 분석 및 기사 방향 제안을 담당합니다.
"""

from typing import Dict, Any, List
import logging
import json

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class SourceAnalyzerAgent(BaseAgent):
    """소스 분석 Agent"""

    def __init__(self):
        super().__init__(
            name="SourceAnalyzer",
            agent_id="ANALYZER",
            temperature=0.5,
        )

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        소스 분석 실행

        1. 수집된 이슈/소스 분석
        2. 기사 관점 제안
        3. 기사 유형 추천
        """
        self.log_step("소스 분석 시작")

        collected_issues = state.get("collected_issues", [])
        collected_sources = state.get("collected_sources", [])

        # 분석할 소스 통합
        all_sources = collected_issues + collected_sources

        if not all_sources:
            state["source_analysis"] = {"error": "분석할 소스가 없습니다."}
            return state

        # 소스 내용 추출
        source_texts = []
        for source in all_sources[:10]:  # 최대 10개
            if isinstance(source, dict):
                source_texts.append(f"[{source.get('source', 'unknown')}] {source.get('title', '')}\n{source.get('content', '')[:500]}")
            elif isinstance(source, str):
                source_texts.append(source[:500])

        # LLM으로 분석
        system_prompt = """당신은 서울경제신문의 편집국장입니다.
수집된 소스를 분석하여 기사 작성 방향을 제안해주세요.

다음 JSON 형식으로 응답해주세요:
{
    "main_topic": "핵심 주제",
    "summary": "2-3문장 요약",
    "suggested_angles": [
        {"angle": "관점1", "reason": "이유"},
        {"angle": "관점2", "reason": "이유"},
        {"angle": "관점3", "reason": "이유"}
    ],
    "recommended_article_types": [
        {"type": "online|print|daily", "reason": "이유"}
    ],
    "key_facts": ["팩트1", "팩트2", "팩트3"],
    "stakeholders": ["이해관계자1", "이해관계자2"],
    "potential_follow_up": "후속 취재 방향"
}"""

        user_message = f"""다음 소스들을 분석해주세요:

{chr(10).join(source_texts)}"""

        messages = self.build_messages(system_prompt, user_message)

        try:
            response = await self.invoke(messages)

            # JSON 파싱
            try:
                # JSON 블록 추출
                json_match = response
                if "```json" in response:
                    json_match = response.split("```json")[1].split("```")[0]
                elif "```" in response:
                    json_match = response.split("```")[1].split("```")[0]

                analysis = json.loads(json_match.strip())
            except json.JSONDecodeError:
                analysis = {"raw_analysis": response}

            state["source_analysis"] = analysis

        except Exception as e:
            logger.error(f"소스 분석 실패: {e}")
            state["source_analysis"] = {"error": str(e)}

        state["current_step"] = "source_analyzer"
        self.log_step("소스 분석 완료")

        return state


# 모듈 레벨 실행 함수
agent = SourceAnalyzerAgent()

async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    return await agent.run(state)
