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
            model_id="anthropic.claude-sonnet-4-20250514",
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

        # 시스템 프롬프트 구성
        system_prompt = self._build_system_prompt(
            engine_type=engine_type,
            article_type=article_type,
            kb_rules=kb_rules,
            style_rules=style_rules,
            reporter_style=reporter_style,
            examples_text=examples_text,
        )

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

    def _build_system_prompt(
        self,
        engine_type: str,
        article_type: str,
        kb_rules: str,
        style_rules: str,
        reporter_style: str,
        examples_text: str,
    ) -> str:
        """시스템 프롬프트 구성"""

        # 엔진별 기본 지시
        if engine_type == "22":
            engine_instruction = """[정부/공공 보도자료 기사화 시스템 v2.0]

절대 규칙:
- 대통령, 장관, 국회의원 등 모든 정치인 실명 사용 금지
- 여당, 야당, 정당명 일체 언급 금지
- 성공적, 실패한, 파격적 등 가치판단 표현 금지
- 경제적 영향 중심으로 분석

핵심 원칙:
1. 정치적 중립성 절대 유지
2. 경제적 영향 중심 분석
3. 독자 관점 재구성
4. 팩트 기반 작성"""
        else:
            engine_instruction = """[기업 보도자료 기사화 시스템]

핵심 역량:
1. 분석력: 기업 발표의 표면적 내용과 실제 의미 구분
2. 판단력: 뉴스가치와 독자 관심도 정확히 평가
3. 작성력: 복잡한 경제 현상을 명확하게 전달
4. 정확성: 팩트 체크와 검증을 통한 신뢰성 확보

독자: 투자자, 기업 관계자"""

        # 기사 유형별 지시
        article_instruction = self._get_article_instruction(article_type)

        return f"""당신은 서울경제신문의 AI 기자입니다.

{engine_instruction}

{article_instruction}

{f'[적용할 규칙]{chr(10)}{kb_rules}' if kb_rules else ''}

{f'[스타일북]{chr(10)}{style_rules}' if style_rules else ''}

{f'[기자 스타일]{chr(10)}{reporter_style}' if reporter_style else ''}

{examples_text}"""

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
