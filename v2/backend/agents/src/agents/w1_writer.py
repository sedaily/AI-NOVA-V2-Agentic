"""
W1 Writer Agent
보도자료 기사화 전문 Agent

Engine 11: 기업 보도자료
Engine 22: 정부/공공 보도자료

Temperature: 0.81
Max Tokens: 16384
"""

from typing import Dict, Any
import logging

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class W1WriterAgent(BaseAgent):
    """기사 작성 Agent (보도자료 Pro)"""

    def __init__(self):
        super().__init__(
            name="W1Writer",
            agent_id="W1",
            model_id="apac.anthropic.claude-3-5-sonnet-20241022-v2:0",
            temperature=0.81,
            max_tokens=16384,
        )

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        기사 초안 작성

        1. Aurora에서 관련 KB 규칙 검색
        2. 스타일북 검색
        3. 기자 스타일 조회
        4. 기사 생성
        """
        self.log_step("기사 작성 시작")

        article_type = state.get("article_type", "online")
        engine_type = state.get("engine_type", "11")
        reporter_id = state.get("reporter_id", "")
        integrated_context = state.get("integrated_context", {})
        selected_sources = state.get("selected_sources", [])

        # 소스 텍스트 준비
        source_text = integrated_context.get("structured_info", "")
        if not source_text:
            source_text = "\n\n".join([
                f"{s.get('title', '')}\n{s.get('content', '')}"
                for s in selected_sources
            ])

        # 1. KB 규칙 검색 (벡터 검색)
        kb_rules = await self.get_kb_context(source_text[:1000])

        # 2. 스타일북 검색
        style_rules = await self.get_style_context(source_text[:500])

        # 3. 기자 스타일 조회
        reporter_style = ""
        if reporter_id:
            reporter_style = await self.get_reporter_context(reporter_id)

        # 4. Few-shot 예시 검색
        examples = await self.get_examples(source_text[:500])
        examples_text = ""
        if examples:
            examples_text = "\n\n[참고 예시]\n" + "\n".join([
                f"- {ex.get('correct', '')}" for ex in examples[:2]
            ])

        # 시스템 프롬프트 구성 (DynamoDB 또는 폴백 템플릿에서 로드)
        base_prompt = self.get_prompt_with_context(
            prompt_type="W1",
            engine_type=engine_type,
            kb_context=kb_rules,
            style_context=style_rules,
            reporter_context=reporter_style,
        )

        # 기사 유형별 추가 지시 + 예시 추가
        article_instruction = self._get_article_instruction(article_type)
        system_prompt = f"{base_prompt}\n\n{article_instruction}{examples_text}"

        # 사용자 메시지
        user_message = f"""다음 소스를 바탕으로 {self._get_article_type_name(article_type)} 기사를 작성해주세요.

{source_text}"""

        messages = self.build_messages(system_prompt, user_message)

        try:
            response = await self.invoke(messages)
            state["draft"] = response
            state["revision_count"] = 0

        except Exception as e:
            logger.error(f"기사 작성 실패: {e}")
            state["draft"] = ""
            state["errors"] = state.get("errors", []) + [str(e)]

        state["current_step"] = "w1_writer"
        self.log_step("기사 작성 완료")

        return state

    def _get_article_instruction(self, article_type: str) -> str:
        """기사 유형별 지시문"""
        instructions = {
            "daily": """[일보 작성]
- 분량: 300~500자
- 스타일: 핵심 팩트 위주, 간결한 문체
- 구조: 제목 + 리드문 + 본문 1~2문단
- 특징: 빠른 배포를 위한 속보형""",

            "print": """[지면 기사 작성]
- 분량: 1000~1500자
- 스타일: 배경 설명 포함, 깊이있는 분석
- 구조: 제목 + 부제 + 리드문 + 본문 + 전망
- 특징: 인용구 활용, 전문가 의견 포함""",

            "online": """[온라인 기사 작성]
- 분량: 800~1200자
- 스타일: SEO 최적화, 모바일 친화적
- 구조: 제목(50자 이내) + 리드문 + 소제목 포함 본문
- 특징: 클릭 유도, 가독성 중시""",
        }
        return instructions.get(article_type, instructions["online"])

    def _get_article_type_name(self, article_type: str) -> str:
        """기사 유형 한글명"""
        names = {
            "daily": "일보",
            "print": "지면",
            "online": "온라인",
        }
        return names.get(article_type, "온라인")


# 모듈 레벨 실행 함수
agent = W1WriterAgent()

async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    return await agent.run(state)
