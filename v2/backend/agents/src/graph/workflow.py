"""
LangGraph 워크플로우 정의
기사 작성 전체 파이프라인을 구성합니다.
"""

import os
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import ArticleState
from .routers import (
    quality_check_router,
    fact_check_router,
    media_generation_router,
)

# Agent imports (lazy import to avoid circular dependencies)
def get_agents():
    from ..agents import (
        issue_collector,
        source_analyzer,
        source_integrator,
        w1_writer,
        quality_gate,
        r1_reviser,
        t1_titler,
        p1_proofreader,
        style_checker,
        layout_agent,
        drug_agent,
        fact_checker,
        infographic_agent,
        image_agent,
        tts_agent,
        final_reviewer,
    )
    return {
        "issue_collector": issue_collector.run,
        "source_analyzer": source_analyzer.run,
        "source_integrator": source_integrator.run,
        "w1_writer": w1_writer.run,
        "quality_gate": quality_gate.run,
        "r1_reviser": r1_reviser.run,
        "t1_titler": t1_titler.run,
        "p1_proofreader": p1_proofreader.run,
        "style_checker": style_checker.run,
        "layout_agent": layout_agent.run,
        "drug_agent": drug_agent.run,
        "fact_checker": fact_checker.run,
        "infographic_agent": infographic_agent.run,
        "image_agent": image_agent.run,
        "tts_agent": tts_agent.run,
        "final_reviewer": final_reviewer.run,
    }


def create_workflow(use_agentcore_memory: bool = False) -> StateGraph:
    """
    기사 작성 워크플로우 생성

    Args:
        use_agentcore_memory: AgentCore Memory 사용 여부

    Returns:
        컴파일된 LangGraph 워크플로우
    """

    # 워크플로우 생성
    workflow = StateGraph(ArticleState)

    agents = get_agents()

    # ===== Phase 1: 소재 수집 노드 =====
    workflow.add_node("issue_collector", agents["issue_collector"])
    workflow.add_node("source_analyzer", agents["source_analyzer"])
    workflow.add_node("source_integrator", agents["source_integrator"])

    # ===== Phase 2: 기사 작성 노드 =====
    workflow.add_node("w1_writer", agents["w1_writer"])
    workflow.add_node("quality_gate", agents["quality_gate"])
    workflow.add_node("r1_reviser", agents["r1_reviser"])
    workflow.add_node("t1_titler", agents["t1_titler"])
    workflow.add_node("p1_proofreader", agents["p1_proofreader"])
    workflow.add_node("style_checker", agents["style_checker"])

    # ===== Phase 3: 최종 마무리 노드 =====
    workflow.add_node("layout_agent", agents["layout_agent"])
    workflow.add_node("drug_agent", agents["drug_agent"])
    workflow.add_node("fact_checker", agents["fact_checker"])
    workflow.add_node("infographic_agent", agents["infographic_agent"])
    workflow.add_node("image_agent", agents["image_agent"])
    workflow.add_node("tts_agent", agents["tts_agent"])
    workflow.add_node("final_reviewer", agents["final_reviewer"])

    # ===== 병렬 처리 노드 =====
    workflow.add_node("parallel_refine", parallel_refine_node)
    workflow.add_node("parallel_media", parallel_media_node)

    # ===== 엣지 정의 (Phase 1) =====
    workflow.set_entry_point("issue_collector")
    workflow.add_edge("issue_collector", "source_analyzer")
    workflow.add_edge("source_analyzer", "source_integrator")
    workflow.add_edge("source_integrator", "w1_writer")

    # ===== 엣지 정의 (Phase 2) =====
    workflow.add_edge("w1_writer", "quality_gate")

    # 품질 검사 조건부 라우팅
    workflow.add_conditional_edges(
        "quality_gate",
        quality_check_router,
        {
            "pass": "parallel_refine",
            "revise": "r1_reviser",
        }
    )
    workflow.add_edge("r1_reviser", "quality_gate")  # 루프백

    workflow.add_edge("parallel_refine", "layout_agent")

    # ===== 엣지 정의 (Phase 3) =====
    workflow.add_edge("layout_agent", "drug_agent")
    workflow.add_edge("drug_agent", "p1_proofreader")
    workflow.add_edge("p1_proofreader", "fact_checker")

    # 팩트체크 조건부 라우팅
    workflow.add_conditional_edges(
        "fact_checker",
        fact_check_router,
        {
            "pass": "parallel_media",
            "warning": "parallel_media",
            "block": "r1_reviser",
        }
    )

    workflow.add_edge("parallel_media", "final_reviewer")
    workflow.add_edge("final_reviewer", END)

    # ===== 체크포인터 설정 =====
    if use_agentcore_memory:
        try:
            from langgraph_checkpoint_aws import AgentCoreMemorySaver
            memory_id = os.environ.get("AGENTCORE_MEMORY_ID")
            region = os.environ.get("AWS_REGION", "ap-northeast-2")
            checkpointer = AgentCoreMemorySaver(memory_id, region_name=region)
        except ImportError:
            print("Warning: AgentCore Memory not available, using in-memory")
            checkpointer = MemorySaver()
    else:
        checkpointer = MemorySaver()

    # 컴파일
    compiled_graph = workflow.compile(checkpointer=checkpointer)

    return compiled_graph


async def parallel_refine_node(state: ArticleState) -> ArticleState:
    """
    병렬 처리 노드: T1 (제목), P1 (교정), StyleChecker
    """
    import asyncio

    agents = get_agents()

    # 병렬 실행
    results = await asyncio.gather(
        agents["t1_titler"](state),
        agents["p1_proofreader"](state),
        agents["style_checker"](state),
        return_exceptions=True
    )

    # 결과 병합
    for result in results:
        if isinstance(result, Exception):
            state["errors"].append(str(result))
        elif isinstance(result, dict):
            state.update(result)

    return state


async def parallel_media_node(state: ArticleState) -> ArticleState:
    """
    병렬 처리 노드: Infographic, Image, TTS
    """
    import asyncio

    agents = get_agents()
    article_type = state.get("article_type", "online")

    tasks = []

    # 기사 유형에 따라 생성할 미디어 결정
    if article_type == "online":
        tasks = [
            agents["infographic_agent"](state),
            agents["image_agent"](state),
            agents["tts_agent"](state),
        ]
    elif article_type == "print":
        tasks = [
            agents["image_agent"](state),
        ]
    # daily는 미디어 생성 없음

    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                state["errors"].append(str(result))
            elif isinstance(result, dict):
                state.update(result)

    return state


# 기본 그래프 인스턴스
graph = None

def get_graph():
    """그래프 싱글톤 인스턴스 반환"""
    global graph
    if graph is None:
        graph = create_workflow()
    return graph
