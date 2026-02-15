"""
FinalReviewer Agent
최종 검수 Agent - 모든 결과 종합 및 최종 확인
"""

from typing import Dict, Any
import logging
from datetime import datetime

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class FinalReviewerAgent(BaseAgent):
    """최종 검수 Agent"""

    def __init__(self):
        super().__init__(
            name="FinalReviewer",
            agent_id="REVIEWER",
            temperature=0.2,
            max_tokens=2048,
        )

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        최종 검수

        확인 항목:
        1. 모든 필수 요소 완성 여부
        2. 최종 품질 점수
        3. 발행 준비 상태 확인
        """
        self.log_step("최종 검수 시작")

        # 결과 수집
        final_article = state.get("final_article", state.get("draft", ""))
        titles = state.get("titles", [])
        quality_score = state.get("quality_score", 0)
        corrections = state.get("corrections", [])
        fact_check = state.get("fact_check_report") or {}
        image_url = state.get("image_url")
        tts_url = state.get("tts_url")
        infographic_data = state.get("infographic_data")
        errors = state.get("errors", [])

        # 최종 리포트 생성
        final_report = {
            "timestamp": datetime.utcnow().isoformat(),
            "article_type": state.get("article_type", "online"),
            "engine_type": state.get("engine_type", "11"),
            "reporter_id": state.get("reporter_id", ""),

            # 기사 정보
            "article": {
                "content": final_article,
                "length": len(final_article),
                "titles": titles,
                "selected_title": titles[0] if titles else None,
            },

            # 품질 정보
            "quality": {
                "score": quality_score,
                "corrections_count": len(corrections),
                "revision_count": state.get("revision_count", 0),
            },

            # 팩트체크 정보
            "fact_check": {
                "verified_count": fact_check.get("verified_count", 0),
                "unverified_count": fact_check.get("unverified_count", 0),
                "has_critical_errors": bool(fact_check.get("critical_errors")),
            },

            # 미디어 정보
            "media": {
                "image_url": image_url,
                "tts_url": tts_url,
                "has_infographic": bool(infographic_data),
            },

            # 상태 정보
            "status": {
                "is_complete": bool(final_article and titles),
                "is_ready_to_publish": quality_score >= 80 and not fact_check.get("critical_errors"),
                "errors": errors,
            },
        }

        state["final_report"] = final_report

        # 발행 준비 상태 결정
        if final_report["status"]["is_ready_to_publish"]:
            self.log_step(f"✅ 발행 준비 완료 (품질 점수: {quality_score}점)")
        else:
            reasons = []
            if quality_score < 80:
                reasons.append(f"품질 점수 미달 ({quality_score}점)")
            if fact_check.get("critical_errors"):
                reasons.append("팩트체크 오류 발견")
            if not final_article:
                reasons.append("기사 본문 없음")
            if not titles:
                reasons.append("제목 없음")

            self.log_step(f"⚠️ 추가 검토 필요: {', '.join(reasons)}")

        state["current_step"] = "final_reviewer"

        return state


agent = FinalReviewerAgent()

async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    return await agent.run(state)
