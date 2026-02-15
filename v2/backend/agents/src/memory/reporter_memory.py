"""
Reporter Memory
기자별 스타일 및 선호도 학습

AgentCore Memory 통합:
- 장기 기억: 기자 스타일, 선호도
- 패턴 학습: 문체, 어조, 키워드 빈도
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .agent_core import get_memory_manager, AgentCoreMemoryManager

logger = logging.getLogger(__name__)


class ReporterMemory:
    """
    기자 메모리 관리

    AgentCore Memory + DB 하이브리드 저장:
    - AgentCore: 장기 기억 (스타일 학습, 패턴)
    - DB: 원본 데이터 백업
    """

    def __init__(self):
        self._memory_manager: Optional[AgentCoreMemoryManager] = None

    @property
    def memory(self) -> AgentCoreMemoryManager:
        """Memory Manager 반환"""
        if self._memory_manager is None:
            self._memory_manager = get_memory_manager()
        return self._memory_manager

    async def get_style(self, reporter_id: str) -> Dict[str, Any]:
        """
        기자 스타일 정보 조회

        Returns:
            {
                "style_summary": "문체 요약",
                "preferred_patterns": [...],
                "word_preferences": {...},
                "avg_article_length": 800,
            }
        """
        # 1. AgentCore Memory에서 조회
        try:
            await self.memory.initialize()

            style = await self.memory.get_reporter_preference(reporter_id, "style")
            patterns = await self.memory.get_reporter_preference(reporter_id, "writing_patterns")

            if style or patterns:
                return {
                    "style_summary": style.get("style_summary", "") if style else "",
                    "preferred_patterns": patterns.get("common_phrases", []) if patterns else [],
                    "word_preferences": style.get("word_preferences", {}) if style else {},
                    "avg_article_length": patterns.get("avg_length", 800) if patterns else 800,
                    "tone_distribution": patterns.get("tone_distribution", {}) if patterns else {},
                    "total_articles": patterns.get("total_articles", 0) if patterns else 0,
                }
        except Exception as e:
            logger.warning(f"AgentCore Memory lookup failed: {e}")

        # 2. DB에서 조회 (폴백)
        try:
            from ..database.connection import db_connection
            async with db_connection() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM reporter_styles WHERE reporter_id = $1",
                    reporter_id,
                )
                if row:
                    return {
                        "style_summary": row.get("style_summary", ""),
                        "preferred_patterns": row.get("preferred_patterns", []),
                        "word_preferences": row.get("word_preferences", {}),
                        "avg_article_length": row.get("avg_article_length", 800),
                    }
        except Exception as e:
            logger.debug(f"DB lookup failed: {e}")

        # 3. 기본값
        return {
            "style_summary": "",
            "preferred_patterns": [],
            "word_preferences": {},
            "avg_article_length": 800,
        }

    async def learn_from_article(
        self,
        reporter_id: str,
        article_content: str,
        article_type: str,
        was_edited: bool = False,
        final_version: Optional[str] = None,
    ) -> bool:
        """
        기사에서 스타일 학습

        Args:
            reporter_id: 기자 ID
            article_content: 기사 내용
            article_type: 기사 유형
            was_edited: 수정 여부
            final_version: 최종 버전 (수정된 경우)

        Returns:
            학습 성공 여부
        """
        try:
            # 분석할 텍스트 결정
            text_to_analyze = final_version if was_edited else article_content

            # AgentCore Memory에 학습
            await self.memory.initialize()
            success = await self.memory.learn_writing_pattern(
                reporter_id=reporter_id,
                article_text=text_to_analyze,
                article_metadata={
                    "article_type": article_type,
                    "was_edited": was_edited,
                    "learned_at": datetime.utcnow().isoformat(),
                }
            )

            # 수정된 경우 피드백으로도 저장
            if was_edited and final_version:
                await self.memory.store_reporter_preference(
                    reporter_id=reporter_id,
                    preference_type="edit_feedback",
                    data={
                        "original_length": len(article_content),
                        "final_length": len(final_version),
                        "article_type": article_type,
                    }
                )

            # DB에도 백업 저장
            try:
                from ..database.connection import db_connection
                current_style = await self.get_style(reporter_id)

                async with db_connection() as conn:
                    await conn.execute("""
                        INSERT INTO reporter_styles (reporter_id, style_summary, preferred_patterns, avg_article_length, updated_at)
                        VALUES ($1, $2, $3, $4, NOW())
                        ON CONFLICT (reporter_id) DO UPDATE SET
                            preferred_patterns = $3,
                            avg_article_length = $4,
                            updated_at = NOW()
                    """, reporter_id, current_style.get("style_summary", ""),
                        current_style.get("preferred_patterns", []),
                        current_style.get("avg_article_length", 800))
            except Exception as db_error:
                logger.debug(f"DB backup failed (non-critical): {db_error}")

            return success

        except Exception as e:
            logger.error(f"Learn from article error: {e}")
            return False

    def _extract_patterns(self, text: str) -> List[str]:
        """텍스트에서 문체 패턴 추출"""
        patterns = []

        # 문장 시작 패턴
        sentences = text.split(".")
        for sent in sentences[:10]:
            sent = sent.strip()
            if len(sent) > 5:
                # 첫 3어절 추출
                words = sent.split()[:3]
                if words:
                    patterns.append(" ".join(words))

        return patterns[:20]

    def _merge_patterns(
        self,
        existing: List[str],
        new: List[str],
    ) -> List[str]:
        """패턴 병합 (빈도 기반)"""
        from collections import Counter

        all_patterns = existing + new
        counter = Counter(all_patterns)

        # 상위 30개 유지
        return [p for p, _ in counter.most_common(30)]

    async def get_writing_preferences(
        self,
        reporter_id: str,
    ) -> Dict[str, Any]:
        """기자 작성 선호도 조회"""
        style = await self.get_style(reporter_id)

        return {
            "target_length": style.get("avg_article_length", 800),
            "style_hints": style.get("style_summary", ""),
            "preferred_patterns": style.get("preferred_patterns", [])[:5],
            "tone_distribution": style.get("tone_distribution", {}),
            "total_articles_learned": style.get("total_articles", 0),
        }

    async def get_style_for_prompt(
        self,
        reporter_id: str,
    ) -> str:
        """
        프롬프트에 포함할 스타일 컨텍스트 생성

        Args:
            reporter_id: 기자 ID

        Returns:
            프롬프트용 스타일 문자열
        """
        style = await self.get_style(reporter_id)

        if not style.get("total_articles", 0):
            return ""

        parts = []

        if style.get("style_summary"):
            parts.append(f"문체 요약: {style['style_summary']}")

        if style.get("avg_article_length"):
            parts.append(f"선호 길이: {style['avg_article_length']}자 내외")

        patterns = style.get("preferred_patterns", [])[:5]
        if patterns:
            parts.append(f"자주 사용하는 표현: {', '.join(patterns)}")

        tone = style.get("tone_distribution", {})
        if tone:
            if tone.get("formal", 0) > tone.get("casual", 0):
                parts.append("선호 어조: 격식체 (했다, 밝혔다)")
            else:
                parts.append("선호 어조: 설명체 (했습니다, 있습니다)")

        total = style.get("total_articles", 0)
        if total:
            parts.append(f"(학습된 기사: {total}개)")

        return "\n".join(parts)

    async def record_feedback(
        self,
        reporter_id: str,
        article_id: str,
        feedback_type: str,
        feedback_data: Dict[str, Any],
    ) -> bool:
        """
        기사 피드백 기록

        Args:
            reporter_id: 기자 ID
            article_id: 기사 ID
            feedback_type: 피드백 유형 (edit, approve, reject)
            feedback_data: 피드백 데이터

        Returns:
            성공 여부
        """
        try:
            await self.memory.initialize()
            return await self.memory.store_reporter_preference(
                reporter_id=reporter_id,
                preference_type=f"feedback_{feedback_type}_{article_id}",
                data={
                    "article_id": article_id,
                    "type": feedback_type,
                    **feedback_data,
                    "recorded_at": datetime.utcnow().isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Record feedback error: {e}")
            return False
