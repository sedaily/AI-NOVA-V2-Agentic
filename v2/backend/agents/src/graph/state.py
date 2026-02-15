"""
LangGraph State 정의
기사 작성 워크플로우의 상태를 관리합니다.

Tool 통합:
- tool_calls: 현재 처리해야 할 도구 호출 목록
- tool_results: 도구 실행 결과
"""

from typing import TypedDict, List, Optional, Annotated, Any
from operator import add


class ToolCall(TypedDict):
    """도구 호출 정보"""
    id: str                  # 도구 호출 ID
    name: str                # 도구 이름
    args: dict               # 도구 인자


class ToolResult(TypedDict):
    """도구 실행 결과"""
    tool_call_id: str        # 도구 호출 ID
    name: str                # 도구 이름
    result: Any              # 실행 결과


class ArticleState(TypedDict):
    """기사 작성 워크플로우 상태"""

    # ===== Phase 1: 소재 수집 =====
    collected_issues: List[dict]        # 수집된 이슈 목록
    collected_sources: List[dict]       # 수집된 소스 (보도자료, 뉴스 등)
    selected_sources: List[dict]        # 선택된 소스
    source_analysis: Optional[dict]     # 소스 분석 결과

    # ===== Phase 2: 기사 작성 =====
    article_type: str                   # "online" | "print" | "daily"
    engine_type: str                    # "11" (기업) | "22" (정부/공공)
    draft: str                          # 현재 초안
    quality_score: float                # 품질 점수 (0-100)
    revision_count: int                 # 수정 횟수
    titles: List[dict]                  # 생성된 제목들
    corrections: List[dict]             # 교정 사항
    style_issues: List[dict]            # 스타일 이슈

    # ===== Phase 3: 최종 마무리 =====
    final_article: str                  # 최종 기사
    layout_structure: Optional[dict]    # 레이아웃 구조
    infographic_url: Optional[str]      # 인포그래픽 URL
    image_url: Optional[str]            # 대표 이미지 URL
    tts_url: Optional[str]              # TTS 음성 URL
    fact_check_report: Optional[dict]   # 팩트체크 리포트

    # ===== Tool Integration =====
    tool_calls: List[ToolCall]          # 현재 처리해야 할 도구 호출
    tool_results: List[ToolResult]      # 도구 실행 결과
    pending_tool_calls: bool            # 처리 대기 중인 도구 호출 여부

    # ===== Meta =====
    reporter_id: str                    # 기자 ID
    session_id: str                     # 세션 ID
    messages: Annotated[List[dict], add]  # 대화 히스토리
    errors: List[str]                   # 에러 로그
    current_step: str                   # 현재 단계


class SourceInfo(TypedDict):
    """소스 정보"""
    source_type: str        # "press_release" | "news" | "topic"
    title: str
    content: str
    url: Optional[str]
    published_at: Optional[str]
    keywords: List[str]


class TitleOption(TypedDict):
    """제목 옵션"""
    type: str               # "journalism" | "balanced" | "click" | "seo" | "social"
    title: str
    score: float


class CorrectionItem(TypedDict):
    """교정 항목"""
    original: str
    corrected: str
    reason: str
    category: str           # "spelling" | "grammar" | "style" | "fact"


class FactCheckItem(TypedDict):
    """팩트체크 항목"""
    claim: str
    verified: bool
    source: Optional[str]
    confidence: float
