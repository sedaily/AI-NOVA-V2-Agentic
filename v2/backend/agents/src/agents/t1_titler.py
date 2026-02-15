"""
T1 Titler Agent
TITLE-NOMICS 3.0 - 제목 생성 전문 Agent

5가지 유형의 제목 생성:
1. 저널리즘 충실형
2. 균형잡힌 후킹형
3. 클릭유도형
4. SEO/AEO 최적화형
5. 소셜미디어 공유형
"""

from typing import Dict, Any, List
import logging
import json

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class T1TitlerAgent(BaseAgent):
    """제목 생성 Agent (TITLE-NOMICS 3.0)"""

    def __init__(self):
        super().__init__(
            name="T1Titler",
            agent_id="T1",
            temperature=0.85,  # 창의성 높게
            max_tokens=2048,
        )

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        제목 생성 실행

        4명의 전문가 협업 시스템:
        - 김경제: 창의적 비전 디렉터
        - 정경제: 통찰력 분석가
        - 박한글: 언어 혁신가
        - 이디지: 디지털 전략가
        """
        self.log_step("제목 생성 시작")

        draft = state.get("draft", "")
        article_type = state.get("article_type", "online")

        if not draft:
            state["titles"] = []
            return state

        # KB 규칙 검색
        kb_rules = await self.get_kb_context(draft[:500])

        # DynamoDB에서 T1 프롬프트 로드 (또는 폴백 템플릿 사용)
        base_prompt = self.get_prompt_with_context(
            prompt_type="T1",
            kb_context=kb_rules,
        )

        # JSON 출력 형식 추가
        output_format = """
다음 JSON 형식으로 응답해주세요:
{
    "titles": [
        {"type": "journalism", "title": "...", "rationale": "..."},
        {"type": "balanced", "title": "...", "rationale": "..."},
        {"type": "click", "title": "...", "rationale": "..."},
        {"type": "seo", "title": "...", "rationale": "..."},
        {"type": "social", "title": "...", "rationale": "..."}
    ],
    "recommended": "가장 추천하는 제목 유형",
    "keywords": ["핵심", "키워드", "목록"]
}"""

        system_prompt = f"{base_prompt}\n{output_format}"

        user_message = f"""다음 {self._get_article_type_name(article_type)} 기사의 제목 5종을 생성해주세요:

{draft[:2000]}"""

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
                state["titles"] = result.get("titles", [])

            except json.JSONDecodeError:
                # 파싱 실패 시 텍스트에서 제목 추출 시도
                state["titles"] = self._extract_titles_from_text(response)

        except Exception as e:
            logger.error(f"제목 생성 실패: {e}")
            state["titles"] = []
            state["errors"] = state.get("errors", []) + [str(e)]

        state["current_step"] = "t1_titler"
        self.log_step(f"제목 {len(state.get('titles', []))}개 생성 완료")

        return state

    def _extract_titles_from_text(self, text: str) -> List[Dict]:
        """텍스트에서 제목 추출 (폴백)"""
        titles = []
        lines = text.split("\n")

        type_mapping = {
            "1": "journalism",
            "2": "balanced",
            "3": "click",
            "4": "seo",
            "5": "social",
        }

        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                # 번호나 대시로 시작하는 줄은 제목일 가능성
                title_text = line.lstrip("0123456789.-) ").strip()
                if title_text and len(title_text) > 10:
                    titles.append({
                        "type": type_mapping.get(str(len(titles) + 1), "default"),
                        "title": title_text,
                    })

        return titles[:5]

    def _get_article_type_name(self, article_type: str) -> str:
        names = {"daily": "일보", "print": "지면", "online": "온라인"}
        return names.get(article_type, "온라인")


# 모듈 레벨 실행 함수
agent = T1TitlerAgent()

async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    return await agent.run(state)
