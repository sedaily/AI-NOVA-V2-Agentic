"""
AI Nexus Agent Service
메인 엔트리포인트
"""

import os
import logging
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from dotenv import load_dotenv

load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 워크플로우 임포트
from .graph.workflow import create_workflow
from .graph.state import ArticleState
from .database.connection import init_database, close_db_pool
from .memory.session_memory import SessionMemory


# 전역 인스턴스
workflow = None
session_memory = SessionMemory()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 라이프사이클 관리"""
    global workflow

    # 시작
    logger.info("Starting AI Nexus Agent Service...")
    await init_database()
    workflow = create_workflow()
    logger.info("Workflow initialized")

    yield

    # 종료
    logger.info("Shutting down...")
    await close_db_pool()


app = FastAPI(
    title="AI Nexus Agent Service",
    description="서울경제신문 AI 기자 어시스턴트 에이전트 서비스",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response 모델
class ArticleRequest(BaseModel):
    session_id: str
    reporter_id: str
    article_type: str = "online"  # online, print, daily
    engine_type: str = "11"  # 11 (기업), 22 (정부/공공)
    sources: list = []
    topic: str = ""
    keywords: list = []


class ArticleResponse(BaseModel):
    session_id: str
    status: str
    draft: str = ""
    titles: list = []
    quality_score: float = 0
    current_step: str = ""
    final_report: dict = {}


class StepRequest(BaseModel):
    session_id: str
    step: str  # 실행할 단계


# API 엔드포인트
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-nexus-agent"}


@app.post("/api/article/start", response_model=ArticleResponse)
async def start_article(request: ArticleRequest):
    """기사 작성 시작"""
    try:
        # 초기 상태 설정
        initial_state: ArticleState = {
            "session_id": request.session_id,
            "reporter_id": request.reporter_id,
            "article_type": request.article_type,
            "engine_type": request.engine_type,
            "collected_sources": request.sources,
            "topic": request.topic,
            "keywords": request.keywords,
            "current_step": "start",
            "draft": "",
            "titles": [],
            "quality_score": 0,
            "revision_count": 0,
            "corrections": [],
            "errors": [],
        }

        # 세션에 저장
        await session_memory.save_session_state(request.session_id, initial_state)

        return ArticleResponse(
            session_id=request.session_id,
            status="initialized",
            current_step="start",
        )

    except Exception as e:
        logger.error(f"Start article error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/article/run", response_model=ArticleResponse)
async def run_workflow(request: StepRequest):
    """워크플로우 실행 (전체 또는 특정 단계까지)"""
    try:
        # 세션 상태 조회
        state = await session_memory.get_session_state(request.session_id)
        if not state:
            raise HTTPException(status_code=404, detail="Session not found")

        # 워크플로우 실행
        config = {"configurable": {"thread_id": request.session_id}}

        if request.step == "full":
            # 전체 워크플로우 실행
            result = await workflow.ainvoke(state, config)
        else:
            # 특정 단계까지 실행
            result = await workflow.ainvoke(
                state,
                config,
                interrupt_before=[request.step],
            )

        # 상태 저장
        await session_memory.save_session_state(request.session_id, result)

        return ArticleResponse(
            session_id=request.session_id,
            status="completed" if result.get("final_report") else "in_progress",
            draft=result.get("final_article", result.get("draft", "")),
            titles=result.get("titles", []),
            quality_score=result.get("quality_score", 0),
            current_step=result.get("current_step", ""),
            final_report=result.get("final_report", {}),
        )

    except Exception as e:
        logger.error(f"Run workflow error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/article/{session_id}", response_model=ArticleResponse)
async def get_article_status(session_id: str):
    """기사 작성 상태 조회"""
    state = await session_memory.get_session_state(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    return ArticleResponse(
        session_id=session_id,
        status="completed" if state.get("final_report") else "in_progress",
        draft=state.get("final_article", state.get("draft", "")),
        titles=state.get("titles", []),
        quality_score=state.get("quality_score", 0),
        current_step=state.get("current_step", ""),
        final_report=state.get("final_report", {}),
    )


@app.post("/api/article/{session_id}/revise")
async def request_revision(session_id: str, feedback: Dict[str, Any]):
    """수정 요청"""
    state = await session_memory.get_session_state(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    # 피드백 추가
    state["user_feedback"] = feedback
    state["quality_score"] = max(0, state.get("quality_score", 80) - 10)

    # 워크플로우 재실행 (R1부터)
    config = {"configurable": {"thread_id": session_id}}
    result = await workflow.ainvoke(state, config)

    await session_memory.save_session_state(session_id, result)

    return {"status": "revised", "session_id": session_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )
