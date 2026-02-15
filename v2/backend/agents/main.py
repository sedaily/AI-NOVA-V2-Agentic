"""
Nexus AI Agent API Server
FastAPI 기반 Agent 워크플로우 API
"""

import os
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis.asyncio as redis

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis 설정
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# 세션 저장소 (Redis 또는 메모리)
sessions: Dict[str, Dict[str, Any]] = {}
redis_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행"""
    global redis_client
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        await redis_client.ping()
        logger.info("Redis 연결 성공")
    except Exception as e:
        logger.warning(f"Redis 연결 실패, 메모리 세션 사용: {e}")
        redis_client = None

    yield

    if redis_client:
        await redis_client.close()


app = FastAPI(
    title="Nexus AI Agent API",
    description="AI 기자 어시스턴트 Agent 워크플로우 API",
    version="2.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ====================================================
# Pydantic Models
# ====================================================

class SourceItem(BaseModel):
    id: str
    title: str
    content: str
    source_type: str = "press_release"


class WorkflowStartRequest(BaseModel):
    user_id: Optional[str] = "anonymous"
    reporter_id: Optional[str] = None
    sources: List[SourceItem]
    article_type: str = "online"  # daily, print, online
    engine_type: str = "11"  # 11: 기업, 22: 정부/공공


class WorkflowRunRequest(BaseModel):
    step: str = "full"  # full, single


class WorkflowState(BaseModel):
    session_id: str
    user_id: str
    sources: List[Dict[str, Any]]
    article_type: str
    engine_type: str
    current_step: str = "initialized"
    status: str = "active"
    draft: str = ""
    titles: List[Dict[str, str]] = []
    corrections: List[Dict[str, Any]] = []
    quality_score: int = 0
    revision_count: int = 0
    created_at: str = ""
    updated_at: str = ""


# ====================================================
# API Endpoints
# ====================================================

@app.get("/")
async def root():
    """API 루트"""
    return {
        "service": "Nexus AI Agent API",
        "version": "2.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    checks = {
        "api": "healthy",
        "redis": "unknown",
        "database": "unknown"
    }

    # Redis 체크
    if redis_client:
        try:
            await redis_client.ping()
            checks["redis"] = "healthy"
        except:
            checks["redis"] = "unhealthy"
    else:
        checks["redis"] = "not_configured"

    return {
        "status": "healthy" if checks["api"] == "healthy" else "unhealthy",
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/workflow/start")
async def start_workflow(request: WorkflowStartRequest):
    """워크플로우 세션 시작"""
    session_id = str(uuid.uuid4())

    state = {
        "session_id": session_id,
        "user_id": request.user_id,
        "sources": [s.model_dump() for s in request.sources],
        "article_type": request.article_type,
        "engine_type": request.engine_type,
        "current_step": "initialized",
        "status": "active",
        "draft": "",
        "titles": [],
        "corrections": [],
        "quality_score": 0,
        "revision_count": 0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    # 세션 저장
    if redis_client:
        import json
        await redis_client.set(f"workflow:{session_id}", json.dumps(state), ex=3600)
    else:
        sessions[session_id] = state

    logger.info(f"워크플로우 시작: {session_id}")

    return {
        "session_id": session_id,
        "status": "created",
        "message": "워크플로우 세션이 생성되었습니다."
    }


@app.get("/workflow/{session_id}")
async def get_workflow_status(session_id: str):
    """워크플로우 상태 조회"""
    state = await _get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    return state


@app.post("/workflow/{session_id}/run")
async def run_workflow(session_id: str, request: WorkflowRunRequest):
    """워크플로우 실행 (시뮬레이션)"""
    state = await _get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    # 시뮬레이션: 각 단계 실행
    steps = [
        ("issue_collector", "이슈 수집 완료"),
        ("source_analyzer", "소스 분석 완료"),
        ("source_integrator", "소스 통합 완료"),
        ("w1_writer", "기사 초안 작성 완료"),
        ("t1_titler", "제목 생성 완료"),
        ("p1_proofreader", "교정 완료"),
        ("r1_reviser", "퇴고 완료"),
        ("quality_gate", "품질 검증 완료"),
    ]

    # 소스 텍스트 추출
    source_text = "\n\n".join([
        f"{s.get('title', '')}\n{s.get('content', '')}"
        for s in state.get("sources", [])
    ])

    # 시뮬레이션 결과 생성
    state["current_step"] = "completed"
    state["status"] = "completed"
    state["draft"] = f"""[시뮬레이션 기사]

{source_text[:500]}...

(이 기사는 API 테스트를 위한 시뮬레이션입니다.)
"""

    state["titles"] = [
        {"type": "journalism", "title": "[테스트] 주요 뉴스 제목 - 저널리즘형"},
        {"type": "balanced", "title": "[테스트] 균형잡힌 뉴스 제목"},
        {"type": "click", "title": "[테스트] 클릭을 부르는 제목!"},
        {"type": "seo", "title": "[테스트] SEO 최적화 제목"},
        {"type": "social", "title": "[테스트] 소셜 공유용 제목"},
    ]

    state["quality_score"] = 85
    state["updated_at"] = datetime.now().isoformat()

    # 세션 업데이트
    await _save_session(session_id, state)

    logger.info(f"워크플로우 완료: {session_id}")

    return {
        "session_id": session_id,
        "status": "completed",
        "current_step": state["current_step"],
        "draft": state["draft"],
        "titles": state["titles"],
        "quality_score": state["quality_score"],
    }


@app.websocket("/workflow/{session_id}/ws")
async def workflow_websocket(websocket: WebSocket, session_id: str):
    """실시간 진행 상황 WebSocket"""
    await websocket.accept()

    try:
        # 진행 상황 시뮬레이션
        import asyncio
        import json

        steps = [
            ("issue_collector", "이슈 수집"),
            ("source_analyzer", "소스 분석"),
            ("source_integrator", "소스 통합"),
            ("w1_writer", "기사 초안 작성"),
            ("t1_titler", "제목 생성"),
            ("p1_proofreader", "교정"),
            ("r1_reviser", "퇴고"),
            ("quality_gate", "품질 검증"),
        ]

        for i, (step_id, step_name) in enumerate(steps):
            # 시작 알림
            await websocket.send_json({
                "type": "step_start",
                "step": step_id,
                "name": step_name,
                "progress": int((i / len(steps)) * 100)
            })

            await asyncio.sleep(0.5)  # 시뮬레이션 딜레이

            # 완료 알림
            await websocket.send_json({
                "type": "step_complete",
                "step": step_id,
                "name": step_name,
                "progress": int(((i + 1) / len(steps)) * 100)
            })

        # 완료
        await websocket.send_json({
            "type": "complete",
            "status": "success",
            "progress": 100
        })

    except WebSocketDisconnect:
        logger.info(f"WebSocket 연결 종료: {session_id}")


@app.get("/agents")
async def list_agents():
    """사용 가능한 Agent 목록"""
    return {
        "agents": [
            {"id": "issue_collector", "name": "이슈 수집", "phase": 1},
            {"id": "source_analyzer", "name": "소스 분석", "phase": 1},
            {"id": "source_integrator", "name": "소스 통합", "phase": 1},
            {"id": "w1_writer", "name": "기사 작성 (W1)", "phase": 2},
            {"id": "t1_titler", "name": "제목 생성 (T1)", "phase": 2},
            {"id": "p1_proofreader", "name": "교정 (P1)", "phase": 2},
            {"id": "r1_reviser", "name": "퇴고 (R1)", "phase": 2},
            {"id": "quality_gate", "name": "품질 검증", "phase": 2},
            {"id": "style_checker", "name": "스타일 검사", "phase": 2},
            {"id": "layout_agent", "name": "레이아웃", "phase": 3},
            {"id": "drug_agent", "name": "금칙어 검사", "phase": 3},
            {"id": "fact_checker", "name": "팩트체크", "phase": 3},
            {"id": "infographic_agent", "name": "인포그래픽", "phase": 3},
            {"id": "image_agent", "name": "이미지 생성", "phase": 3},
            {"id": "tts_agent", "name": "음성 변환", "phase": 3},
            {"id": "final_reviewer", "name": "최종 검토", "phase": 3},
        ]
    }


# ====================================================
# Helper Functions
# ====================================================

async def _get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """세션 조회"""
    if redis_client:
        import json
        data = await redis_client.get(f"workflow:{session_id}")
        return json.loads(data) if data else None
    return sessions.get(session_id)


async def _save_session(session_id: str, state: Dict[str, Any]):
    """세션 저장"""
    if redis_client:
        import json
        await redis_client.set(f"workflow:{session_id}", json.dumps(state), ex=3600)
    else:
        sessions[session_id] = state


# ====================================================
# Main
# ====================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8001"))

    logger.info(f"Starting Nexus AI Agent API on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
