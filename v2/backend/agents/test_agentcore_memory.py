"""
AgentCore Memory 테스트

테스트 항목:
1. Memory 초기화
2. 기자 스타일 저장/조회
3. 작성 패턴 학습
4. 세션 요약 저장
5. LangGraph 워크플로우 연동
"""

import os
import asyncio
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수 확인
MEMORY_ID = os.getenv("AGENTCORE_MEMORY_ID", "")


async def test_memory_initialization():
    """Memory Manager 초기화 테스트"""
    print(f"\n{'='*60}")
    print("1. AgentCore Memory 초기화 테스트")
    print(f"{'='*60}")

    from src.memory import get_memory_manager, initialize_memory

    manager = get_memory_manager()
    print(f"Memory ID: {manager.memory_id or '(not set)'}")

    if not manager.memory_id:
        print("AGENTCORE_MEMORY_ID 환경 변수가 설정되지 않았습니다.")
        print("로컬 메모리로 폴백됩니다.")
        return False

    success = await initialize_memory()
    print(f"초기화 결과: {'성공' if success else '실패 (SDK 미설치 또는 권한 없음)'}")

    return success


async def test_reporter_style():
    """기자 스타일 저장/조회 테스트"""
    print(f"\n{'='*60}")
    print("2. 기자 스타일 저장/조회 테스트")
    print(f"{'='*60}")

    from src.memory import get_memory_manager

    manager = get_memory_manager()
    await manager.initialize()

    reporter_id = "test_reporter_001"

    # 스타일 저장
    style_data = {
        "style_summary": "간결하고 팩트 중심의 문체",
        "preferred_tone": "formal",
        "word_preferences": {
            "했다": 10,
            "밝혔다": 8,
            "전했다": 5,
        },
    }

    if manager.store:
        success = await manager.store_reporter_preference(
            reporter_id=reporter_id,
            preference_type="style",
            data=style_data,
        )
        print(f"스타일 저장: {'성공' if success else '실패'}")

        # 스타일 조회
        retrieved = await manager.get_reporter_preference(reporter_id, "style")
        print(f"스타일 조회: {retrieved}")
        return True
    else:
        print("AgentCore Store가 초기화되지 않았습니다.")
        return False


async def test_pattern_learning():
    """작성 패턴 학습 테스트"""
    print(f"\n{'='*60}")
    print("3. 작성 패턴 학습 테스트")
    print(f"{'='*60}")

    from src.memory import get_memory_manager

    manager = get_memory_manager()
    await manager.initialize()

    reporter_id = "test_reporter_001"

    # 테스트 기사
    article_text = """삼성전자가 15일 차세대 AI 반도체 개발 계획을 발표했다.

이번에 발표된 'Exynos AI 3000'은 기존 대비 성능이 3배 향상되고 전력 소모는 40% 감소했다.

삼성전자 반도체 부문 김영한 사장은 "올해 4분기 양산을 목표로 하고 있다"며
"글로벌 AI 반도체 시장 1위를 탈환하겠다"고 밝혔다.

투자 규모는 약 5조원이며, 미국 텍사스 공장에서 생산될 예정이다."""

    if manager.store:
        success = await manager.learn_writing_pattern(
            reporter_id=reporter_id,
            article_text=article_text,
            article_metadata={
                "article_type": "online",
                "topic": "technology",
            }
        )
        print(f"패턴 학습: {'성공' if success else '실패'}")

        # 학습된 패턴 조회
        patterns = await manager.get_reporter_preference(reporter_id, "writing_patterns")
        if patterns:
            print(f"총 학습 기사: {patterns.get('total_articles', 0)}개")
            print(f"평균 길이: {patterns.get('avg_length', 0)}자")
            print(f"자주 사용하는 표현: {patterns.get('common_phrases', [])[:5]}")
        return True
    else:
        print("AgentCore Store가 초기화되지 않았습니다.")
        return False


async def test_session_summary():
    """세션 요약 저장 테스트"""
    print(f"\n{'='*60}")
    print("4. 세션 요약 저장 테스트")
    print(f"{'='*60}")

    from src.memory import get_memory_manager

    manager = get_memory_manager()
    await manager.initialize()

    reporter_id = "test_reporter_001"
    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    summary = {
        "articles_created": 3,
        "titles_generated": 15,
        "revisions": 2,
        "total_words": 2500,
        "topics": ["technology", "economy"],
    }

    if manager.store:
        success = await manager.store_session_summary(
            reporter_id=reporter_id,
            session_id=session_id,
            summary=summary,
        )
        print(f"세션 요약 저장: {'성공' if success else '실패'}")
        print(f"세션 ID: {session_id}")

        # 최근 세션 조회
        recent = await manager.get_recent_sessions(reporter_id, limit=3)
        print(f"최근 세션 수: {len(recent)}")
        return True
    else:
        print("AgentCore Store가 초기화되지 않았습니다.")
        return False


async def test_reporter_memory_class():
    """ReporterMemory 클래스 테스트"""
    print(f"\n{'='*60}")
    print("5. ReporterMemory 클래스 테스트")
    print(f"{'='*60}")

    from src.memory import ReporterMemory

    reporter_memory = ReporterMemory()
    reporter_id = "test_reporter_001"

    # 스타일 조회
    style = await reporter_memory.get_style(reporter_id)
    print(f"스타일 조회 결과:")
    print(f"  - 문체 요약: {style.get('style_summary', '(없음)')}")
    print(f"  - 평균 길이: {style.get('avg_article_length', 800)}자")
    print(f"  - 패턴 수: {len(style.get('preferred_patterns', []))}")

    # 작성 선호도
    prefs = await reporter_memory.get_writing_preferences(reporter_id)
    print(f"작성 선호도:")
    print(f"  - 목표 길이: {prefs.get('target_length', 800)}자")
    print(f"  - 학습된 기사: {prefs.get('total_articles_learned', 0)}개")

    # 프롬프트용 스타일
    prompt_style = await reporter_memory.get_style_for_prompt(reporter_id)
    if prompt_style:
        print(f"프롬프트용 스타일:\n{prompt_style}")
    else:
        print("프롬프트용 스타일: (학습된 데이터 없음)")

    return True


async def test_workflow_with_memory():
    """LangGraph 워크플로우 + Memory 테스트"""
    print(f"\n{'='*60}")
    print("6. LangGraph 워크플로우 + Memory 테스트")
    print(f"{'='*60}")

    try:
        from src.graph.workflow import get_graph, get_graph_async

        # 메모리 없는 그래프
        graph_no_memory = get_graph(use_memory=False)
        print(f"메모리 없는 그래프: {type(graph_no_memory).__name__}")

        # 메모리 있는 그래프
        graph_with_memory = await get_graph_async(use_memory=True)
        print(f"메모리 있는 그래프: {type(graph_with_memory).__name__}")

        return True
    except Exception as e:
        print(f"워크플로우 테스트 실패: {e}")
        return False


async def test_base_agent_memory():
    """BaseAgent Memory 통합 테스트"""
    print(f"\n{'='*60}")
    print("7. BaseAgent Memory 통합 테스트")
    print(f"{'='*60}")

    try:
        from src.agents.base_agent import BaseAgent
        from typing import Dict, Any

        # 테스트용 Agent 생성
        class TestAgent(BaseAgent):
            def __init__(self):
                super().__init__(
                    name="TestAgent",
                    agent_id="TEST",
                    use_memory=True
                )

            async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
                return state

        agent = TestAgent()
        reporter_id = "test_reporter_001"

        # Memory Manager 접근
        print(f"Memory Manager: {type(agent.memory).__name__}")

        # 기자 컨텍스트 조회
        context = await agent.get_reporter_context(reporter_id)
        if context:
            print(f"기자 컨텍스트:\n{context}")
        else:
            print("기자 컨텍스트: (없음 또는 학습 전)")

        return True
    except Exception as e:
        print(f"BaseAgent 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """메인 테스트 실행"""
    print("\n" + "=" * 60)
    print("  AgentCore Memory 통합 테스트")
    print("=" * 60)
    print(f"AGENTCORE_MEMORY_ID: {MEMORY_ID or '(not set)'}")
    print("=" * 60)

    results = {}

    # 1. 초기화 테스트
    results["initialization"] = await test_memory_initialization()

    # 2. 기자 스타일 테스트
    results["reporter_style"] = await test_reporter_style()

    # 3. 패턴 학습 테스트
    results["pattern_learning"] = await test_pattern_learning()

    # 4. 세션 요약 테스트
    results["session_summary"] = await test_session_summary()

    # 5. ReporterMemory 클래스 테스트
    results["reporter_memory_class"] = await test_reporter_memory_class()

    # 6. 워크플로우 테스트
    results["workflow"] = await test_workflow_with_memory()

    # 7. BaseAgent 테스트
    results["base_agent"] = await test_base_agent_memory()

    # 결과 요약
    print(f"\n{'='*60}")
    print("테스트 결과 요약")
    print(f"{'='*60}")

    for test_name, success in results.items():
        status = "Pass" if success else "Fail (or SDK not available)"
        print(f"  {test_name}: {status}")

    print(f"{'='*60}")

    if not MEMORY_ID:
        print("\n참고: AGENTCORE_MEMORY_ID가 설정되지 않아")
        print("      일부 테스트가 로컬 메모리로 폴백되었습니다.")
        print("\nAgentCore Memory 리소스 생성:")
        print("  python -c \"import asyncio; from src.memory import create_memory_resource; asyncio.run(create_memory_resource())\"")

    print()


if __name__ == "__main__":
    asyncio.run(main())
