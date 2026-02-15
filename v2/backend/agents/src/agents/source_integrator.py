"""
SourceIntegrator Agent
선택된 소스를 통합하여 기사 작성 준비를 합니다.
"""

from typing import Dict, Any
import logging

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class SourceIntegratorAgent(BaseAgent):
    """소스 통합 Agent"""

    def __init__(self):
        super().__init__(
            name="SourceIntegrator",
            agent_id="INTEGRATOR",
            temperature=0.3,
        )

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        소스 통합 실행

        1. 선택된 소스 수집
        2. 중복 제거 및 정리
        3. 기사 작성용 컨텍스트 생성
        """
        self.log_step("소스 통합 시작")

        selected_sources = state.get("selected_sources", [])
        source_analysis = state.get("source_analysis", {})

        if not selected_sources:
            # 선택된 소스가 없으면 분석 결과 기반으로 자동 선택
            collected = state.get("collected_issues", []) + state.get("collected_sources", [])
            selected_sources = collected[:3]  # 상위 3개 자동 선택
            state["selected_sources"] = selected_sources

        # 소스 통합 컨텍스트 생성
        integrated_context = {
            "main_topic": source_analysis.get("main_topic", ""),
            "key_facts": source_analysis.get("key_facts", []),
            "sources": [],
        }

        for source in selected_sources:
            integrated_context["sources"].append({
                "title": source.get("title", ""),
                "content": source.get("content", ""),
                "source_type": source.get("source", "unknown"),
            })

        # 통합된 텍스트 생성
        system_prompt = """당신은 기사 작성을 위한 소스 정리 전문가입니다.
여러 소스를 통합하여 기사 작성에 사용할 수 있는 구조화된 정보로 정리해주세요.

다음 형식으로 정리해주세요:
1. 핵심 사실 (5W1H)
2. 주요 인용문/데이터
3. 배경 정보
4. 관련 이해관계자
5. 추가 확인 필요 사항"""

        source_texts = "\n\n".join([
            f"[소스 {i+1}] {s.get('title', '')}\n{s.get('content', '')}"
            for i, s in enumerate(selected_sources)
        ])

        messages = self.build_messages(system_prompt, source_texts)

        try:
            response = await self.invoke(messages)
            integrated_context["structured_info"] = response
        except Exception as e:
            logger.error(f"소스 통합 실패: {e}")
            integrated_context["structured_info"] = source_texts

        state["integrated_context"] = integrated_context
        state["current_step"] = "source_integrator"

        self.log_step("소스 통합 완료")

        return state


# 모듈 레벨 실행 함수
agent = SourceIntegratorAgent()

async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    return await agent.run(state)
