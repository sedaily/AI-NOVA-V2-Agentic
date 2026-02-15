"""
AI NOVA v2 - 전체 워크플로우 E2E 테스트

테스트 항목:
1. 개별 Agent 노드 테스트
2. Phase 1: 소재 수집 (IssueCollector → SourceAnalyzer → SourceIntegrator)
3. Phase 2: 기사 작성 (W1Writer → QualityGate → Reviser)
4. Phase 3: 마무리 (Layout → Drug → Proofreader → FactChecker → Media → FinalReviewer)
5. 전체 워크플로우 통합 테스트
"""

import asyncio
import logging
import os
import sys
import time
from typing import Dict, Any

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 테스트용 초기 상태
def get_initial_state() -> Dict[str, Any]:
    """테스트용 초기 상태 생성"""
    return {
        # Phase 1: 소재 수집
        "search_query": "AI 반도체 삼성전자",
        "collected_issues": [],
        "collected_sources": [],
        "selected_sources": [],
        "source_analysis": None,

        # Phase 2: 기사 작성
        "article_type": "online",
        "engine_type": "11",
        "draft": "",
        "quality_score": 0.0,
        "revision_count": 0,
        "titles": [],
        "corrections": [],
        "style_issues": [],

        # Phase 3: 최종 마무리
        "final_article": "",
        "layout_structure": None,
        "infographic_url": None,
        "image_url": None,
        "tts_url": None,
        "fact_check_report": None,

        # Tool Integration
        "tool_calls": [],
        "tool_results": [],
        "pending_tool_calls": False,

        # Meta
        "reporter_id": "test_reporter_001",
        "session_id": f"test_session_{int(time.time())}",
        "messages": [],
        "errors": [],
        "current_step": "",
    }


async def test_issue_collector():
    """IssueCollector Agent 테스트"""
    print(f"\n{'='*60}")
    print("1. IssueCollector Agent 테스트")
    print(f"{'='*60}")

    from src.agents.issue_collector import run, run_simple

    state = get_initial_state()
    print(f"검색 쿼리: {state['search_query']}")

    try:
        # 단순 실행 (직접 도구 호출)
        print("\n[run_simple 테스트]")
        result = await run_simple(state)

        issues = result.get("collected_issues", [])
        sources = result.get("collected_sources", [])

        print(f"수집된 이슈: {len(issues)}건")
        print(f"수집된 소스: {len(sources)}건")

        if issues:
            print(f"\n첫 번째 이슈:")
            print(f"  - 제목: {issues[0].get('title', 'N/A')[:50]}...")
            print(f"  - 출처: {issues[0].get('source', 'N/A')}")

        return len(issues) > 0 or len(sources) > 0, result

    except Exception as e:
        logger.error(f"IssueCollector 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False, state


async def test_source_analyzer(state: Dict[str, Any]):
    """SourceAnalyzer Agent 테스트"""
    print(f"\n{'='*60}")
    print("2. SourceAnalyzer Agent 테스트")
    print(f"{'='*60}")

    from src.agents.source_analyzer import run

    # 이전 단계의 소스가 없으면 더미 데이터 추가
    if not state.get("collected_sources"):
        state["collected_sources"] = [
            {
                "title": "삼성전자, AI 반도체 HBM4 개발 성공",
                "content": "삼성전자가 차세대 AI 반도체용 HBM4 메모리 개발에 성공했다고 발표했다. HBM4는 기존 HBM3 대비 처리 속도가 2배 이상 빠르며, AI 학습에 최적화된 구조를 갖추고 있다.",
                "source": "삼성전자 보도자료",
                "url": "https://example.com/samsung",
                "published_at": "2026-02-15",
            }
        ]

    print(f"분석할 소스: {len(state.get('collected_sources', []))}건")

    try:
        result = await run(state)

        analysis = result.get("source_analysis", {})
        selected = result.get("selected_sources", [])

        print(f"분석 결과: {bool(analysis)}")
        print(f"선택된 소스: {len(selected)}건")

        if analysis:
            print(f"  - 주요 키워드: {analysis.get('keywords', [])[:5]}")

        return True, result

    except Exception as e:
        logger.error(f"SourceAnalyzer 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False, state


async def test_source_integrator(state: Dict[str, Any]):
    """SourceIntegrator Agent 테스트"""
    print(f"\n{'='*60}")
    print("3. SourceIntegrator Agent 테스트")
    print(f"{'='*60}")

    from src.agents.source_integrator import run

    # 선택된 소스가 없으면 더미 데이터
    if not state.get("selected_sources"):
        state["selected_sources"] = state.get("collected_sources", [])

    print(f"통합할 소스: {len(state.get('selected_sources', []))}건")

    try:
        result = await run(state)

        integrated = result.get("integrated_context", {})

        print(f"통합 결과: {bool(integrated)}")
        if integrated:
            info = integrated.get("structured_info", "")
            print(f"  - 통합 정보 길이: {len(info)}자")

        return True, result

    except Exception as e:
        logger.error(f"SourceIntegrator 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False, state


async def test_w1_writer(state: Dict[str, Any]):
    """W1Writer Agent 테스트"""
    print(f"\n{'='*60}")
    print("4. W1Writer Agent 테스트 (기사 작성)")
    print(f"{'='*60}")

    from src.agents.w1_writer import run

    # 통합 컨텍스트가 없으면 더미 데이터
    if not state.get("integrated_context"):
        state["integrated_context"] = {
            "structured_info": """
[보도자료 요약]
삼성전자가 차세대 AI 반도체용 HBM4 메모리 개발에 성공했다.
- HBM4는 기존 HBM3 대비 처리 속도 2배 향상
- AI 학습에 최적화된 구조
- 2026년 하반기 양산 예정
- 글로벌 AI 기업들과 공급 협의 중
""",
            "key_facts": [
                "삼성전자 HBM4 개발 성공",
                "HBM3 대비 2배 속도 향상",
                "2026년 하반기 양산 예정"
            ]
        }

    print(f"기사 유형: {state.get('article_type', 'online')}")
    print(f"엔진 유형: {state.get('engine_type', '11')}")

    try:
        result = await run(state)

        draft = result.get("draft", "")

        print(f"초안 작성: {'성공' if draft else '실패'}")
        if draft:
            print(f"  - 초안 길이: {len(draft)}자")
            print(f"  - 미리보기: {draft[:150]}...")

        return bool(draft), result

    except Exception as e:
        logger.error(f"W1Writer 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False, state


async def test_quality_gate(state: Dict[str, Any]):
    """QualityGate Agent 테스트"""
    print(f"\n{'='*60}")
    print("5. QualityGate Agent 테스트 (품질 검사)")
    print(f"{'='*60}")

    from src.agents.quality_gate import run

    # 초안이 없으면 더미 데이터
    if not state.get("draft"):
        state["draft"] = """삼성전자, AI 반도체 HBM4 개발 성공

삼성전자가 차세대 인공지능(AI) 반도체용 고대역폭 메모리 'HBM4' 개발에 성공했다고 15일 밝혔다.

회사에 따르면 HBM4는 기존 HBM3 대비 데이터 처리 속도가 2배 이상 빠르다. 특히 AI 학습에 최적화된 구조를 갖춰 대규모 언어모델(LLM) 학습 시간을 크게 단축할 수 있다.

삼성전자는 2026년 하반기부터 HBM4 양산에 돌입할 예정이며, 글로벌 주요 AI 기업들과 공급 협의를 진행 중이다.

업계 관계자는 "HBM4는 AI 반도체 시장의 게임체인저가 될 것"이라며 "삼성전자가 SK하이닉스와의 기술 격차를 좁힐 수 있는 중요한 계기"라고 평가했다."""

    print(f"초안 길이: {len(state.get('draft', ''))}자")

    try:
        result = await run(state)

        score = result.get("quality_score", 0)

        print(f"품질 점수: {score}/100")
        print(f"통과 여부: {'통과' if score >= 80 else '수정 필요'}")

        return True, result

    except Exception as e:
        logger.error(f"QualityGate 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False, state


async def test_t1_titler(state: Dict[str, Any]):
    """T1Titler Agent 테스트"""
    print(f"\n{'='*60}")
    print("6. T1Titler Agent 테스트 (제목 생성)")
    print(f"{'='*60}")

    from src.agents.t1_titler import run

    try:
        result = await run(state)

        titles = result.get("titles", [])

        print(f"생성된 제목: {len(titles)}개")
        for i, title in enumerate(titles[:3], 1):
            print(f"  {i}. [{title.get('type', 'N/A')}] {title.get('title', 'N/A')}")

        return len(titles) > 0, result

    except Exception as e:
        logger.error(f"T1Titler 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False, state


async def test_p1_proofreader(state: Dict[str, Any]):
    """P1Proofreader Agent 테스트"""
    print(f"\n{'='*60}")
    print("7. P1Proofreader Agent 테스트 (교정)")
    print(f"{'='*60}")

    from src.agents.p1_proofreader import run

    try:
        result = await run(state)

        corrections = result.get("corrections", [])

        print(f"교정 사항: {len(corrections)}개")
        for i, corr in enumerate(corrections[:3], 1):
            print(f"  {i}. {corr.get('original', '')[:20]} → {corr.get('corrected', '')[:20]}")

        return True, result

    except Exception as e:
        logger.error(f"P1Proofreader 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False, state


async def test_fact_checker(state: Dict[str, Any]):
    """FactChecker Agent 테스트"""
    print(f"\n{'='*60}")
    print("8. FactChecker Agent 테스트 (팩트체크)")
    print(f"{'='*60}")

    from src.agents.fact_checker import run

    try:
        result = await run(state)

        report = result.get("fact_check_report", {})

        print(f"팩트체크 완료: {bool(report)}")
        if report:
            print(f"  - 검증된 항목: {report.get('verified_count', 0)}개")
            print(f"  - 미검증 항목: {report.get('unverified_count', 0)}개")

        return True, result

    except Exception as e:
        logger.error(f"FactChecker 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False, state


async def test_final_reviewer(state: Dict[str, Any]):
    """FinalReviewer Agent 테스트"""
    print(f"\n{'='*60}")
    print("9. FinalReviewer Agent 테스트 (최종 검토)")
    print(f"{'='*60}")

    from src.agents.final_reviewer import run

    try:
        result = await run(state)

        # final_article 또는 draft 확인
        final = result.get("final_article") or result.get("draft", "")
        final_report = result.get("final_report", {})

        print(f"최종 검토 완료: {'성공' if final_report else '실패'}")
        if final:
            print(f"  - 기사 길이: {len(final)}자")
        if final_report:
            print(f"  - 품질 점수: {final_report.get('quality', {}).get('score', 'N/A')}")
            print(f"  - 발행 준비: {'완료' if final_report.get('status', {}).get('is_ready_to_publish') else '추가 검토 필요'}")

        return bool(final_report), result

    except Exception as e:
        logger.error(f"FinalReviewer 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False, state


async def test_full_workflow():
    """전체 워크플로우 E2E 테스트"""
    print(f"\n{'='*60}")
    print("전체 워크플로우 E2E 테스트")
    print(f"{'='*60}")

    from src.graph import get_graph

    try:
        # 그래프 생성
        print("\n워크플로우 그래프 생성 중...")
        graph = get_graph(use_memory=False)
        print("그래프 생성 완료")

        # 초기 상태
        state = get_initial_state()
        state["search_query"] = "AI 반도체 삼성전자 HBM4"

        # 설정
        config = {
            "configurable": {
                "thread_id": state["session_id"],
            }
        }

        print(f"\n검색 쿼리: {state['search_query']}")
        print(f"기사 유형: {state['article_type']}")
        print(f"세션 ID: {state['session_id']}")

        # 워크플로우 실행
        print("\n워크플로우 실행 중...")
        start_time = time.time()

        final_state = await graph.ainvoke(state, config)

        elapsed = time.time() - start_time
        print(f"\n워크플로우 완료 (소요시간: {elapsed:.2f}초)")

        # 결과 요약
        print(f"\n{'='*60}")
        print("결과 요약")
        print(f"{'='*60}")

        print(f"수집된 이슈: {len(final_state.get('collected_issues', []))}건")
        print(f"수집된 소스: {len(final_state.get('collected_sources', []))}건")
        print(f"품질 점수: {final_state.get('quality_score', 0)}/100")
        print(f"수정 횟수: {final_state.get('revision_count', 0)}")
        print(f"생성된 제목: {len(final_state.get('titles', []))}개")
        print(f"교정 사항: {len(final_state.get('corrections', []))}개")
        print(f"에러: {len(final_state.get('errors', []))}개")

        if final_state.get("final_article"):
            print(f"\n최종 기사 길이: {len(final_state['final_article'])}자")
            print(f"미리보기:\n{final_state['final_article'][:300]}...")

        if final_state.get("errors"):
            print(f"\n에러 목록:")
            for err in final_state["errors"][:5]:
                print(f"  - {err}")

        return bool(final_state.get("final_article")), final_state

    except Exception as e:
        logger.error(f"전체 워크플로우 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False, {}


async def test_phase_by_phase():
    """Phase별 순차 테스트"""
    print(f"\n{'#'*60}")
    print("#  Phase별 순차 테스트")
    print(f"{'#'*60}")

    results = {}
    state = get_initial_state()

    # Phase 1: 소재 수집
    print(f"\n{'='*60}")
    print("PHASE 1: 소재 수집")
    print(f"{'='*60}")

    success, state = await test_issue_collector()
    results["issue_collector"] = success

    success, state = await test_source_analyzer(state)
    results["source_analyzer"] = success

    success, state = await test_source_integrator(state)
    results["source_integrator"] = success

    # Phase 2: 기사 작성
    print(f"\n{'='*60}")
    print("PHASE 2: 기사 작성")
    print(f"{'='*60}")

    success, state = await test_w1_writer(state)
    results["w1_writer"] = success

    success, state = await test_quality_gate(state)
    results["quality_gate"] = success

    success, state = await test_t1_titler(state)
    results["t1_titler"] = success

    success, state = await test_p1_proofreader(state)
    results["p1_proofreader"] = success

    # Phase 3: 팩트체크 & 마무리
    print(f"\n{'='*60}")
    print("PHASE 3: 팩트체크 & 마무리")
    print(f"{'='*60}")

    success, state = await test_fact_checker(state)
    results["fact_checker"] = success

    success, state = await test_final_reviewer(state)
    results["final_reviewer"] = success

    return results, state


async def main():
    """메인 테스트"""
    print("\n" + "=" * 60)
    print("  AI NOVA v2 - E2E 워크플로우 테스트")
    print("=" * 60)

    # 환경 변수 확인
    print("\n환경 변수 확인:")
    env_vars = [
        "ANTHROPIC_API_KEY",
        "AWS_REGION",
        "BIGKINDS_API_KEY",
        "PERPLEXITY_API_KEY",
        "SERPAPI_KEY",
    ]
    for var in env_vars:
        status = "설정됨" if os.getenv(var) else "미설정"
        print(f"  {var}: {status}")

    # 테스트 모드 선택
    print("\n테스트 모드:")
    print("  1. Phase별 순차 테스트 (개별 Agent)")
    print("  2. 전체 워크플로우 E2E 테스트")
    print("  3. 모든 테스트 실행")

    # 기본값: 모든 테스트 실행
    mode = os.environ.get("TEST_MODE", "3")

    results = {}

    if mode in ["1", "3"]:
        print("\n" + "=" * 60)
        print("Phase별 순차 테스트 시작")
        print("=" * 60)

        phase_results, final_state = await test_phase_by_phase()
        results.update(phase_results)

    if mode in ["2", "3"]:
        print("\n" + "=" * 60)
        print("전체 워크플로우 E2E 테스트 시작")
        print("=" * 60)

        success, _ = await test_full_workflow()
        results["full_workflow"] = success

    # 최종 결과 요약
    print(f"\n{'='*60}")
    print("테스트 결과 요약")
    print(f"{'='*60}")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, success in results.items():
        status = "PASS" if success else "FAIL"
        icon = "✓" if success else "✗"
        print(f"  {icon} {test_name}: {status}")

    print(f"\n총 결과: {passed}/{total} 통과")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
