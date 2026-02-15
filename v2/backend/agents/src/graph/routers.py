"""
LangGraph 조건부 라우터
워크플로우 분기 로직을 정의합니다.
"""

from typing import Literal
from .state import ArticleState


def quality_check_router(state: ArticleState) -> Literal["pass", "revise", "fail"]:
    """
    품질 검사 라우터

    Returns:
        - "pass": 품질 통과 → 다음 단계로
        - "revise": 수정 필요 → R1 Agent로
        - "fail": 최대 재시도 초과 → 강제 통과
    """
    quality_score = state.get("quality_score", 0)
    revision_count = state.get("revision_count", 0)

    # 최대 3회 수정 후 강제 통과
    if revision_count >= 3:
        return "pass"

    # 품질 점수 기준
    if quality_score >= 80:
        return "pass"
    elif quality_score >= 60:
        return "revise"
    else:
        return "revise"


def fact_check_router(state: ArticleState) -> Literal["pass", "warning", "block"]:
    """
    팩트체크 라우터

    Returns:
        - "pass": 모든 팩트 검증됨
        - "warning": 일부 미검증 (경고와 함께 진행)
        - "block": 심각한 오류 발견 (수정 필요)
    """
    fact_report = state.get("fact_check_report", {})

    if not fact_report:
        return "pass"

    unverified_count = fact_report.get("unverified_count", 0)
    critical_errors = fact_report.get("critical_errors", [])

    if critical_errors:
        return "block"
    elif unverified_count > 2:
        return "warning"
    else:
        return "pass"


def article_type_router(state: ArticleState) -> Literal["online", "print", "daily"]:
    """
    기사 유형 라우터
    기사 유형에 따라 다른 처리 경로로 분기
    """
    return state.get("article_type", "online")


def source_type_router(state: ArticleState) -> Literal["press_release", "topic", "mixed"]:
    """
    소스 유형 라우터
    """
    sources = state.get("selected_sources", [])

    if not sources:
        return "topic"

    source_types = set(s.get("source_type") for s in sources)

    if len(source_types) > 1:
        return "mixed"
    elif "press_release" in source_types:
        return "press_release"
    else:
        return "topic"


def media_generation_router(state: ArticleState) -> Literal["all", "image_only", "none"]:
    """
    미디어 생성 라우터
    기사 유형에 따라 생성할 미디어 결정
    """
    article_type = state.get("article_type", "online")

    if article_type == "online":
        return "all"  # 이미지, 인포그래픽, TTS 모두
    elif article_type == "print":
        return "image_only"  # 이미지만
    else:  # daily
        return "none"  # 미디어 없음
