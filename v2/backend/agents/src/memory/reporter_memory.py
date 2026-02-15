"""
Reporter Memory
기자별 스타일 및 선호도 학습
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .agent_core import AgentCoreMemory
from ..database.connection import db_connection

logger = logging.getLogger(__name__)


class ReporterMemory:
    """기자 메모리 관리"""

    def __init__(self):
        self.agent_core = AgentCoreMemory()

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
        # 1. AgentCore에서 조회
        style = await self.agent_core.get_reporter_style(reporter_id)
        if style:
            return style

        # 2. DB에서 조회
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
        """
        try:
            # 분석할 텍스트 결정
            text_to_analyze = final_version if was_edited else article_content

            # 스타일 특성 추출 (간단한 통계)
            patterns = self._extract_patterns(text_to_analyze)

            # 기존 스타일 조회
            current_style = await self.get_style(reporter_id)

            # 스타일 업데이트 (평균화)
            updated_patterns = self._merge_patterns(
                current_style.get("preferred_patterns", []),
                patterns,
            )

            # 저장
            updated_style = {
                **current_style,
                "preferred_patterns": updated_patterns,
                "avg_article_length": int(
                    (current_style.get("avg_article_length", 800) + len(text_to_analyze)) / 2
                ),
                "last_updated": datetime.utcnow().isoformat(),
            }

            # AgentCore에 저장
            await self.agent_core.update_reporter_style(reporter_id, updated_style)

            # DB에도 저장
            async with db_connection() as conn:
                await conn.execute("""
                    INSERT INTO reporter_styles (reporter_id, style_summary, preferred_patterns, avg_article_length, updated_at)
                    VALUES ($1, $2, $3, $4, NOW())
                    ON CONFLICT (reporter_id) DO UPDATE SET
                        preferred_patterns = $3,
                        avg_article_length = $4,
                        updated_at = NOW()
                """, reporter_id, updated_style.get("style_summary", ""),
                    updated_style["preferred_patterns"],
                    updated_style["avg_article_length"])

            return True

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
        }
