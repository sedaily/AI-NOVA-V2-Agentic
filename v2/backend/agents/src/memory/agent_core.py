"""
AgentCore Memory
AWS Bedrock AgentCore Memory 연동 (최신 SDK)

LangGraph Checkpoint + Memory Store 통합
- AgentCoreMemorySaver: 워크플로우 상태 체크포인트
- AgentCoreMemoryStore: 기자 스타일/선호도 장기 기억
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
MEMORY_ID = os.getenv("AGENTCORE_MEMORY_ID", "")

# AgentCore Memory 전략 정의
MEMORY_STRATEGIES = [
    {
        "summaryMemoryStrategy": {
            "name": "SessionSummarizer",
            "namespaces": ["/summaries/{actorId}/{sessionId}"],
            "description": "세션별 대화 요약 저장"
        }
    },
    {
        "userPreferenceMemoryStrategy": {
            "name": "ReporterStyle",
            "namespaces": ["/preferences/{actorId}"],
            "description": "기자별 스타일 선호도"
        }
    },
    {
        "semanticMemoryStrategy": {
            "name": "ArticlePatterns",
            "namespaces": ["/patterns/{actorId}"],
            "description": "기사 작성 패턴 학습"
        }
    }
]


class AgentCoreMemoryManager:
    """
    AWS AgentCore Memory 통합 관리자

    LangGraph와 연동하여:
    1. 워크플로우 체크포인트 (세션 간 상태 유지)
    2. 기자 스타일 학습 (장기 기억)
    3. 세션 요약 (컨텍스트 압축)
    """

    def __init__(self, memory_id: Optional[str] = None):
        self.memory_id = memory_id or MEMORY_ID
        self.region = AWS_REGION
        self._checkpointer = None
        self._store = None
        self._memory_client = None
        self._initialized = False

    async def initialize(self) -> bool:
        """
        AgentCore Memory 초기화

        Returns:
            초기화 성공 여부
        """
        if self._initialized:
            return True

        if not self.memory_id:
            logger.warning("AGENTCORE_MEMORY_ID not set - using local memory")
            return False

        try:
            # AWS SDK 임포트
            from langgraph_checkpoint_aws import AgentCoreMemorySaver, AgentCoreMemoryStore

            # Checkpointer 초기화 (워크플로우 상태)
            self._checkpointer = AgentCoreMemorySaver(
                self.memory_id,
                region_name=self.region
            )

            # Store 초기화 (장기 기억)
            self._store = AgentCoreMemoryStore(
                self.memory_id,
                region_name=self.region
            )

            self._initialized = True
            logger.info(f"AgentCore Memory initialized: {self.memory_id}")
            return True

        except ImportError as e:
            logger.warning(f"AgentCore SDK not available: {e}")
            return False
        except Exception as e:
            logger.error(f"AgentCore initialization failed: {e}")
            return False

    @property
    def checkpointer(self):
        """LangGraph 체크포인터 반환"""
        if self._checkpointer:
            return self._checkpointer

        # 폴백: 인메모리 체크포인터
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()

    @property
    def store(self):
        """LangGraph 스토어 반환"""
        return self._store

    async def store_reporter_preference(
        self,
        reporter_id: str,
        preference_type: str,
        data: Dict[str, Any],
    ) -> bool:
        """
        기자 선호도 저장

        Args:
            reporter_id: 기자 ID
            preference_type: 선호도 유형 (style, tone, length, etc.)
            data: 선호도 데이터

        Returns:
            성공 여부
        """
        if not self._store:
            logger.warning("AgentCore Store not available")
            return False

        try:
            namespace = f"/preferences/{reporter_id}"
            key = preference_type

            # 기존 데이터 조회
            existing = await self._store.get(namespace, key)

            # 병합
            if existing:
                merged = {**existing, **data, "updated_at": datetime.utcnow().isoformat()}
            else:
                merged = {**data, "created_at": datetime.utcnow().isoformat()}

            # 저장
            await self._store.put(namespace, key, merged)
            logger.info(f"Stored preference for reporter {reporter_id}: {preference_type}")
            return True

        except Exception as e:
            logger.error(f"Store preference error: {e}")
            return False

    async def get_reporter_preference(
        self,
        reporter_id: str,
        preference_type: str,
    ) -> Optional[Dict[str, Any]]:
        """
        기자 선호도 조회

        Args:
            reporter_id: 기자 ID
            preference_type: 선호도 유형

        Returns:
            선호도 데이터
        """
        if not self._store:
            return None

        try:
            namespace = f"/preferences/{reporter_id}"
            return await self._store.get(namespace, preference_type)
        except Exception as e:
            logger.error(f"Get preference error: {e}")
            return None

    async def get_all_reporter_preferences(
        self,
        reporter_id: str,
    ) -> Dict[str, Any]:
        """
        기자의 모든 선호도 조회

        Args:
            reporter_id: 기자 ID

        Returns:
            전체 선호도 데이터
        """
        if not self._store:
            return {}

        try:
            namespace = f"/preferences/{reporter_id}"
            items = await self._store.list(namespace)

            preferences = {}
            for key in items:
                data = await self._store.get(namespace, key)
                if data:
                    preferences[key] = data

            return preferences

        except Exception as e:
            logger.error(f"Get all preferences error: {e}")
            return {}

    async def store_session_summary(
        self,
        reporter_id: str,
        session_id: str,
        summary: Dict[str, Any],
    ) -> bool:
        """
        세션 요약 저장

        Args:
            reporter_id: 기자 ID
            session_id: 세션 ID
            summary: 세션 요약 데이터

        Returns:
            성공 여부
        """
        if not self._store:
            return False

        try:
            namespace = f"/summaries/{reporter_id}/{session_id}"
            await self._store.put(namespace, "summary", {
                **summary,
                "created_at": datetime.utcnow().isoformat(),
            })
            return True

        except Exception as e:
            logger.error(f"Store session summary error: {e}")
            return False

    async def get_recent_sessions(
        self,
        reporter_id: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        최근 세션 요약 조회

        Args:
            reporter_id: 기자 ID
            limit: 최대 개수

        Returns:
            세션 요약 리스트
        """
        if not self._store:
            return []

        try:
            # 세션 네임스페이스 조회
            base_namespace = f"/summaries/{reporter_id}"
            sessions = await self._store.list(base_namespace)

            summaries = []
            for session_ns in sessions[:limit]:
                summary = await self._store.get(session_ns, "summary")
                if summary:
                    summaries.append(summary)

            # 최신순 정렬
            summaries.sort(
                key=lambda x: x.get("created_at", ""),
                reverse=True
            )

            return summaries[:limit]

        except Exception as e:
            logger.error(f"Get recent sessions error: {e}")
            return []

    async def learn_writing_pattern(
        self,
        reporter_id: str,
        article_text: str,
        article_metadata: Dict[str, Any],
    ) -> bool:
        """
        기사 작성 패턴 학습

        Args:
            reporter_id: 기자 ID
            article_text: 기사 본문
            article_metadata: 기사 메타데이터

        Returns:
            성공 여부
        """
        if not self._store:
            return False

        try:
            namespace = f"/patterns/{reporter_id}"

            # 기존 패턴 조회
            existing = await self._store.get(namespace, "writing_patterns") or {
                "total_articles": 0,
                "avg_length": 0,
                "common_phrases": [],
                "tone_distribution": {},
            }

            # 새 패턴 분석
            new_patterns = self._analyze_patterns(article_text, article_metadata)

            # 병합 (가중 평균)
            total = existing["total_articles"]
            merged = {
                "total_articles": total + 1,
                "avg_length": int(
                    (existing["avg_length"] * total + len(article_text)) / (total + 1)
                ),
                "common_phrases": self._merge_phrases(
                    existing.get("common_phrases", []),
                    new_patterns.get("phrases", [])
                ),
                "tone_distribution": self._merge_distribution(
                    existing.get("tone_distribution", {}),
                    new_patterns.get("tone", {})
                ),
                "updated_at": datetime.utcnow().isoformat(),
            }

            await self._store.put(namespace, "writing_patterns", merged)
            logger.info(f"Learned pattern for reporter {reporter_id}")
            return True

        except Exception as e:
            logger.error(f"Learn pattern error: {e}")
            return False

    def _analyze_patterns(
        self,
        text: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """텍스트에서 패턴 분석"""
        # 문장 분리
        sentences = [s.strip() for s in text.split(".") if s.strip()]

        # 시작 구문 추출
        phrases = []
        for sent in sentences[:10]:
            words = sent.split()[:3]
            if len(words) >= 2:
                phrases.append(" ".join(words))

        # 어조 분석 (간단한 키워드 기반)
        tone = {}
        formal_keywords = ["했다", "밝혔다", "전했다", "발표했다"]
        casual_keywords = ["했어요", "했습니다", "있습니다"]

        text_lower = text.lower()
        tone["formal"] = sum(1 for kw in formal_keywords if kw in text_lower)
        tone["casual"] = sum(1 for kw in casual_keywords if kw in text_lower)

        return {
            "phrases": phrases,
            "tone": tone,
        }

    def _merge_phrases(
        self,
        existing: List[str],
        new: List[str],
    ) -> List[str]:
        """구문 병합 (빈도 기반)"""
        from collections import Counter

        all_phrases = existing + new
        counter = Counter(all_phrases)
        return [p for p, _ in counter.most_common(50)]

    def _merge_distribution(
        self,
        existing: Dict[str, int],
        new: Dict[str, int],
    ) -> Dict[str, int]:
        """분포 병합"""
        merged = existing.copy()
        for key, value in new.items():
            merged[key] = merged.get(key, 0) + value
        return merged


# 싱글톤 인스턴스
_memory_manager: Optional[AgentCoreMemoryManager] = None


def get_memory_manager() -> AgentCoreMemoryManager:
    """AgentCore Memory Manager 싱글톤 반환"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = AgentCoreMemoryManager()
    return _memory_manager


async def initialize_memory() -> bool:
    """메모리 시스템 초기화"""
    manager = get_memory_manager()
    return await manager.initialize()


# =============================================================================
# Memory Resource 생성 (최초 1회 실행)
# =============================================================================

async def create_memory_resource(
    name: str = "SedailyReporterMemory",
) -> Optional[str]:
    """
    AWS AgentCore Memory 리소스 생성 (최초 1회)

    Args:
        name: 메모리 리소스 이름

    Returns:
        생성된 Memory ID
    """
    try:
        from bedrock_agentcore.memory import MemoryClient

        client = MemoryClient(region_name=AWS_REGION)

        # Memory 생성
        response = client.create_memory_and_wait(
            name=name,
            strategies=MEMORY_STRATEGIES,
        )

        memory_id = response.get("id")
        logger.info(f"Created AgentCore Memory: {memory_id}")

        # .env 파일 업데이트 안내
        print(f"\n{'='*60}")
        print("AgentCore Memory 생성 완료!")
        print(f"{'='*60}")
        print(f"Memory ID: {memory_id}")
        print(f"\n.env 파일에 다음을 추가하세요:")
        print(f"AGENTCORE_MEMORY_ID={memory_id}")
        print(f"{'='*60}\n")

        return memory_id

    except ImportError:
        logger.error("bedrock_agentcore package not installed")
        print("\n설치 필요: pip install bedrock-agentcore")
        return None
    except Exception as e:
        logger.error(f"Create memory resource error: {e}")
        return None


# =============================================================================
# Legacy 호환성 (기존 AgentCoreMemory 클래스)
# =============================================================================

class AgentCoreMemory:
    """
    AWS AgentCore 메모리 관리 (Legacy 호환)

    새 코드에서는 AgentCoreMemoryManager 사용 권장
    """

    def __init__(self, memory_id: Optional[str] = None):
        self._manager = AgentCoreMemoryManager(memory_id)

    async def store_memory(
        self,
        session_id: str,
        content: Dict[str, Any],
        memory_type: str = "conversation",
    ) -> bool:
        """메모리 저장 (Legacy)"""
        await self._manager.initialize()
        return await self._manager.store_session_summary(
            reporter_id="default",
            session_id=session_id,
            summary={"type": memory_type, "content": content}
        )

    async def retrieve_memory(
        self,
        session_id: str,
        memory_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """메모리 조회 (Legacy)"""
        await self._manager.initialize()
        return await self._manager.get_recent_sessions("default", limit)

    async def get_reporter_style(self, reporter_id: str) -> Optional[Dict[str, Any]]:
        """기자 스타일 조회 (Legacy)"""
        await self._manager.initialize()
        return await self._manager.get_reporter_preference(reporter_id, "style")

    async def update_reporter_style(
        self,
        reporter_id: str,
        style_data: Dict[str, Any],
    ) -> bool:
        """기자 스타일 업데이트 (Legacy)"""
        await self._manager.initialize()
        return await self._manager.store_reporter_preference(
            reporter_id, "style", style_data
        )

    async def store_article_feedback(
        self,
        reporter_id: str,
        article_id: str,
        feedback: Dict[str, Any],
    ) -> bool:
        """기사 피드백 저장 (Legacy)"""
        await self._manager.initialize()
        return await self._manager.store_reporter_preference(
            reporter_id,
            f"feedback_{article_id}",
            feedback
        )
