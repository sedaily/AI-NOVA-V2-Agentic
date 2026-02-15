# Phase 2: 프론트엔드 연동

## 개요
Agent 워크플로우와 프론트엔드 UI 연동

**작업 기간**: 2026-02-15
**상태**: 완료

---

## 1. 구현 파일

### 1.1 Agent 워크플로우 서비스

**파일**: `frontend/src/features/workspace/services/agentWorkflowService.js`

```javascript
const AGENT_API_URL = import.meta.env.VITE_AGENT_API_URL || 'http://localhost:8001';

export const WORKFLOW_STEPS = {
  // Phase 1: 소재 수집
  ISSUE_COLLECTOR: { id: 'issue_collector', name: '이슈 수집', phase: 1, order: 1 },
  SOURCE_ANALYZER: { id: 'source_analyzer', name: '소스 분석', phase: 1, order: 2 },
  SOURCE_INTEGRATOR: { id: 'source_integrator', name: '소스 통합', phase: 1, order: 3 },

  // Phase 2: 기사 작성
  W1_WRITER: { id: 'w1_writer', name: '기사 초안 작성', phase: 2, order: 4 },
  T1_TITLER: { id: 't1_titler', name: '제목 생성', phase: 2, order: 5 },
  P1_PROOFREADER: { id: 'p1_proofreader', name: '교정', phase: 2, order: 6 },
  R1_REVISER: { id: 'r1_reviser', name: '퇴고', phase: 2, order: 7 },
  QUALITY_GATE: { id: 'quality_gate', name: '품질 검증', phase: 2, order: 8 },
  STYLE_CHECKER: { id: 'style_checker', name: '스타일 검사', phase: 2, order: 9 },

  // Phase 3: 최종 마무리
  LAYOUT_AGENT: { id: 'layout_agent', name: '레이아웃', phase: 3, order: 10 },
  DRUG_AGENT: { id: 'drug_agent', name: '금칙어 검사', phase: 3, order: 11 },
  FACT_CHECKER: { id: 'fact_checker', name: '팩트체크', phase: 3, order: 12 },
  INFOGRAPHIC: { id: 'infographic_agent', name: '인포그래픽', phase: 3, order: 13 },
  IMAGE_AGENT: { id: 'image_agent', name: '이미지 생성', phase: 3, order: 14 },
  TTS_AGENT: { id: 'tts_agent', name: '음성 변환', phase: 3, order: 15 },
  FINAL_REVIEWER: { id: 'final_reviewer', name: '최종 검토', phase: 3, order: 16 },
};

class AgentWorkflowService {
  constructor() {
    this.ws = null;
    this.sessionId = null;
  }

  // 워크플로우 시작
  async startWorkflow(params) {
    const response = await fetch(`${AGENT_API_URL}/workflow/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    const data = await response.json();
    this.sessionId = data.session_id;
    return data;
  }

  // 워크플로우 실행
  async runWorkflow(step = 'full') {
    const response = await fetch(`${AGENT_API_URL}/workflow/${this.sessionId}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ step }),
    });
    return response.json();
  }

  // WebSocket 연결
  connectWebSocket(onMessage) {
    const wsUrl = `${AGENT_API_URL.replace('http', 'ws')}/workflow/${this.sessionId}/ws`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };

    return this.ws;
  }
}

export const agentWorkflowService = new AgentWorkflowService();
```

### 1.2 React Hook

**파일**: `frontend/src/features/workspace/hooks/useAgentWorkflow.js`

```javascript
import { useState, useCallback, useRef, useEffect } from 'react';
import { agentWorkflowService, WORKFLOW_STEPS } from '../services/agentWorkflowService';

export default function useAgentWorkflow() {
  const [isRunning, setIsRunning] = useState(false);
  const [currentStep, setCurrentStep] = useState(null);
  const [completedSteps, setCompletedSteps] = useState([]);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState({});
  const [error, setError] = useState(null);

  // 워크플로우 시작
  const startWorkflow = useCallback(async (params) => {
    setIsRunning(true);
    setError(null);

    const session = await agentWorkflowService.startWorkflow(params);

    // WebSocket 연결
    agentWorkflowService.connectWebSocket((data) => {
      if (data.type === 'step_start') {
        setCurrentStep(data.step);
      } else if (data.type === 'step_complete') {
        setCompletedSteps(prev => [...prev, data.step]);
        updateProgress();
      } else if (data.type === 'result') {
        setResults(data.results);
      } else if (data.type === 'error') {
        setError(data.message);
      } else if (data.type === 'complete') {
        setIsRunning(false);
      }
    });

    // 워크플로우 실행
    await agentWorkflowService.runWorkflow('full');
  }, []);

  return {
    isRunning,
    currentStep,
    completedSteps,
    progress,
    results,
    error,
    startWorkflow,
    stopWorkflow,
    reset,
  };
}
```

### 1.3 진행 상태 패널

**파일**: `frontend/src/features/workspace/components/AgentProgressPanel.jsx`

```jsx
import React from 'react';
import { WORKFLOW_STEPS } from '../services/agentWorkflowService';

const PHASES = [
  { id: 1, name: '소재 수집', color: 'blue' },
  { id: 2, name: '기사 작성', color: 'green' },
  { id: 3, name: '최종 마무리', color: 'purple' },
];

export default function AgentProgressPanel({
  isRunning,
  currentStep,
  completedSteps,
  progress,
  error,
}) {
  const getStepStatus = (stepId) => {
    if (completedSteps.includes(stepId)) return 'completed';
    if (currentStep === stepId) return 'running';
    return 'pending';
  };

  return (
    <div className="agent-progress-panel">
      <div className="progress-header">
        <h3>AI Agent 진행 상황</h3>
        <span>{Math.round(progress)}%</span>
      </div>

      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${progress}%` }} />
      </div>

      {PHASES.map((phase) => (
        <div key={phase.id} className="phase-section">
          <h4>{phase.name}</h4>
          <div className="step-list">
            {Object.values(WORKFLOW_STEPS)
              .filter((step) => step.phase === phase.id)
              .map((step) => (
                <div key={step.id} className={`step-item ${getStepStatus(step.id)}`}>
                  <StatusIcon status={getStepStatus(step.id)} />
                  <span>{step.name}</span>
                </div>
              ))}
          </div>
        </div>
      ))}
    </div>
  );
}
```

---

## 2. ArticleEditor 통합

### 2.1 변경 사항

**파일**: `frontend/src/features/workspace/components/ArticleEditor.jsx`

```jsx
// 추가된 imports
import useAgentWorkflow from "../hooks/useAgentWorkflow";
import AgentProgressPanel from "./AgentProgressPanel";

export default function ArticleEditor() {
  // Agent 워크플로우 Hook
  const agentWorkflow = useAgentWorkflow();

  // Agent 모드 토글
  const [useAgentMode, setUseAgentMode] = useState(true);

  // 기사 생성 함수 수정
  const generateArticle = async () => {
    if (useAgentMode) {
      // Agent 워크플로우 사용
      await agentWorkflow.startWorkflow({
        sources: selectedSources,
        article_type: articleType,
        engine_type: engineType,
        reporter_id: reporterId,
      });
    } else {
      // 기존 단일 API 호출
      await legacyGenerate();
    }
  };

  return (
    <div className="article-editor">
      {/* 메인 에디터 영역 */}
      <div className="editor-main">
        {/* ... */}
      </div>

      {/* 사이드바 - Agent 진행 상황 */}
      <div className="editor-sidebar">
        {useAgentMode && (
          <AgentProgressPanel
            isRunning={agentWorkflow.isRunning}
            currentStep={agentWorkflow.currentStep}
            completedSteps={agentWorkflow.completedSteps}
            progress={agentWorkflow.progress}
            error={agentWorkflow.error}
          />
        )}
      </div>
    </div>
  );
}
```

---

## 3. API 엔드포인트

### 3.1 백엔드 API (FastAPI)

```python
# main.py

@app.post("/workflow/start")
async def start_workflow(request: WorkflowStartRequest):
    """워크플로우 세션 시작"""
    session_id = str(uuid.uuid4())
    state = WorkflowState(
        user_id=request.user_id,
        sources=request.sources,
        article_type=request.article_type,
        engine_type=request.engine_type,
    )
    await save_session_state(session_id, state)
    return {"session_id": session_id}

@app.post("/workflow/{session_id}/run")
async def run_workflow(session_id: str, request: RunRequest):
    """워크플로우 실행"""
    state = await get_session_state(session_id)
    result = await workflow_graph.ainvoke(state)
    return result

@app.websocket("/workflow/{session_id}/ws")
async def workflow_websocket(websocket: WebSocket, session_id: str):
    """실시간 진행 상황 WebSocket"""
    await websocket.accept()
    # 진행 상황 스트리밍
```

---

## 4. UI/UX 흐름

```
┌────────────────────────────────────────────────────────┐
│  ArticleEditor                                          │
│  ┌─────────────────────────┐ ┌────────────────────────┐│
│  │                         │ │ Agent Progress Panel   ││
│  │   소스 입력 영역         │ │                        ││
│  │   - 보도자료 업로드      │ │ ▶ Phase 1: 소재 수집   ││
│  │   - URL 입력            │ │   ✓ 이슈 수집          ││
│  │                         │ │   ✓ 소스 분석          ││
│  ├─────────────────────────┤ │   ● 소스 통합 (진행중) ││
│  │                         │ │                        ││
│  │   기사 에디터            │ │ ○ Phase 2: 기사 작성   ││
│  │   (실시간 업데이트)      │ │   ○ 기사 초안 작성     ││
│  │                         │ │   ○ 제목 생성          ││
│  │                         │ │   ○ 교정               ││
│  │                         │ │   ○ 퇴고               ││
│  │                         │ │                        ││
│  │                         │ │ ○ Phase 3: 최종 마무리 ││
│  │                         │ │   ...                  ││
│  └─────────────────────────┘ └────────────────────────┘│
│                                                        │
│  [Agent 모드 ON/OFF]  [기사 생성]  [저장]              │
└────────────────────────────────────────────────────────┘
```

---

## 5. 환경 변수

```bash
# .env
VITE_AGENT_API_URL=http://localhost:8001
VITE_WS_URL=ws://localhost:8001
```
