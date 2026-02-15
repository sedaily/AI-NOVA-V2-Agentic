"""
Agent 모듈
16개의 전문화된 Agent를 정의합니다.

Phase 1 (소재 수집):
- IssueCollector: 이슈/뉴스 수집
- SourceAnalyzer: 소스 분석
- SourceIntegrator: 소스 통합

Phase 2 (기사 작성):
- W1Writer: 기사 초안 작성
- QualityGate: 품질 검사
- R1Reviser: 퇴고/문장 다듬기
- T1Titler: 제목 생성
- P1Proofreader: 교정
- StyleChecker: 스타일 검사

Phase 3 (최종 마무리):
- LayoutAgent: 레이아웃 구조화
- DrugAgent: 약물 처리 (길이 조절)
- FactChecker: 팩트체크
- InfographicAgent: 인포그래픽 생성
- ImageAgent: 이미지 생성
- TTSAgent: TTS 생성
- FinalReviewer: 최종 검수
"""

from . import issue_collector
from . import source_analyzer
from . import source_integrator
from . import w1_writer
from . import quality_gate
from . import r1_reviser
from . import t1_titler
from . import p1_proofreader
from . import style_checker
from . import layout_agent
from . import drug_agent
from . import fact_checker
from . import infographic_agent
from . import image_agent
from . import tts_agent
from . import final_reviewer

__all__ = [
    "issue_collector",
    "source_analyzer",
    "source_integrator",
    "w1_writer",
    "quality_gate",
    "r1_reviser",
    "t1_titler",
    "p1_proofreader",
    "style_checker",
    "layout_agent",
    "drug_agent",
    "fact_checker",
    "infographic_agent",
    "image_agent",
    "tts_agent",
    "final_reviewer",
]
