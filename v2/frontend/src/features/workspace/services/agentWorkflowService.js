/**
 * Agent Workflow Service
 * LangGraph 기반 멀티 에이전트 워크플로우 연동
 *
 * 워크플로우 단계:
 * Phase 1: 소재 수집 (IssueCollector → SourceAnalyzer → SourceIntegrator)
 * Phase 2: 기사 작성 (W1 → T1+P1+Style → QualityGate → R1 → Drug/Layout)
 * Phase 3: 최종 마무리 (FactChecker → Infographic+Image+TTS → FinalReviewer)
 */

const AGENT_API_URL = import.meta.env.VITE_AGENT_API_URL || 'http://localhost:8001';

// 워크플로우 단계 정의
export const WORKFLOW_STEPS = {
  // Phase 1: 소재 수집
  ISSUE_COLLECTOR: { id: 'issue_collector', name: '이슈 수집', phase: 1, order: 1 },
  SOURCE_ANALYZER: { id: 'source_analyzer', name: '소스 분석', phase: 1, order: 2 },
  SOURCE_INTEGRATOR: { id: 'source_integrator', name: '소스 통합', phase: 1, order: 3 },

  // Phase 2: 기사 작성
  W1_WRITER: { id: 'w1_writer', name: '기사 초안 작성', phase: 2, order: 4 },
  T1_TITLER: { id: 't1_titler', name: '제목 생성', phase: 2, order: 5 },
  P1_PROOFREADER: { id: 'p1_proofreader', name: '교정', phase: 2, order: 5 },
  STYLE_CHECKER: { id: 'style_checker', name: '스타일 검사', phase: 2, order: 5 },
  QUALITY_GATE: { id: 'quality_gate', name: '품질 검사', phase: 2, order: 6 },
  R1_REVISER: { id: 'r1_reviser', name: '퇴고', phase: 2, order: 7 },
  DRUG_AGENT: { id: 'drug_agent', name: '길이 조절', phase: 2, order: 8 },
  LAYOUT_AGENT: { id: 'layout_agent', name: '레이아웃', phase: 2, order: 8 },

  // Phase 3: 최종 마무리
  FACT_CHECKER: { id: 'fact_checker', name: '팩트체크', phase: 3, order: 9 },
  INFOGRAPHIC: { id: 'infographic_agent', name: '인포그래픽', phase: 3, order: 10 },
  IMAGE_AGENT: { id: 'image_agent', name: '이미지 생성', phase: 3, order: 10 },
  TTS_AGENT: { id: 'tts_agent', name: 'TTS 생성', phase: 3, order: 10 },
  FINAL_REVIEWER: { id: 'final_reviewer', name: '최종 검수', phase: 3, order: 11 },
};

// 단계별 진행률 계산
const calculateProgress = (currentStep) => {
  const stepOrder = {
    'start': 0,
    'issue_collector': 5,
    'source_analyzer': 10,
    'source_integrator': 15,
    'w1_writer': 30,
    't1_titler': 45,
    'p1_proofreader': 50,
    'style_checker': 55,
    'quality_gate': 60,
    'r1_reviser': 70,
    'drug_agent': 75,
    'layout_agent': 78,
    'fact_checker': 82,
    'infographic_agent': 88,
    'image_agent': 92,
    'tts_agent': 95,
    'final_reviewer': 100,
  };
  return stepOrder[currentStep] || 0;
};

class AgentWorkflowService {
  constructor() {
    this.baseURL = AGENT_API_URL;
    this.ws = null;
    this.sessionId = null;
    this.listeners = new Set();
  }

  /**
   * 세션 ID 생성
   */
  generateSessionId() {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * 워크플로우 시작
   */
  async startWorkflow(params) {
    const {
      reporterId = 'default',
      articleType = 'online',
      engineType = '11',
      sources = [],
      pressRelease = '',
      topic = '',
      keywords = [],
    } = params;

    this.sessionId = this.generateSessionId();

    try {
      const response = await fetch(`${this.baseURL}/api/article/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: this.sessionId,
          reporter_id: reporterId,
          article_type: articleType,
          engine_type: engineType,
          sources: sources.length > 0 ? sources : [{ type: 'press_release', content: pressRelease }],
          topic,
          keywords,
        }),
      });

      if (!response.ok) {
        throw new Error(`워크플로우 시작 실패: ${response.status}`);
      }

      const data = await response.json();
      this._notifyListeners({ type: 'started', sessionId: this.sessionId, ...data });

      return {
        sessionId: this.sessionId,
        status: data.status,
      };
    } catch (error) {
      console.error('워크플로우 시작 오류:', error);
      throw error;
    }
  }

  /**
   * 워크플로우 실행
   */
  async runWorkflow(step = 'full') {
    if (!this.sessionId) {
      throw new Error('세션이 시작되지 않았습니다.');
    }

    try {
      const response = await fetch(`${this.baseURL}/api/article/run`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: this.sessionId,
          step,
        }),
      });

      if (!response.ok) {
        throw new Error(`워크플로우 실행 실패: ${response.status}`);
      }

      const data = await response.json();

      this._notifyListeners({
        type: 'progress',
        currentStep: data.current_step,
        progress: calculateProgress(data.current_step),
        ...data,
      });

      if (data.status === 'completed') {
        this._notifyListeners({ type: 'completed', ...data });
      }

      return data;
    } catch (error) {
      console.error('워크플로우 실행 오류:', error);
      this._notifyListeners({ type: 'error', error: error.message });
      throw error;
    }
  }

  /**
   * 상태 조회
   */
  async getStatus() {
    if (!this.sessionId) {
      return null;
    }

    try {
      const response = await fetch(`${this.baseURL}/api/article/${this.sessionId}`);

      if (!response.ok) {
        throw new Error(`상태 조회 실패: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('상태 조회 오류:', error);
      throw error;
    }
  }

  /**
   * 수정 요청
   */
  async requestRevision(feedback) {
    if (!this.sessionId) {
      throw new Error('세션이 시작되지 않았습니다.');
    }

    try {
      const response = await fetch(`${this.baseURL}/api/article/${this.sessionId}/revise`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(feedback),
      });

      if (!response.ok) {
        throw new Error(`수정 요청 실패: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('수정 요청 오류:', error);
      throw error;
    }
  }

  /**
   * WebSocket 연결 (실시간 진행 상태)
   */
  connectWebSocket(onMessage) {
    const wsURL = this.baseURL.replace('http', 'ws') + '/ws';

    try {
      this.ws = new WebSocket(wsURL);

      this.ws.onopen = () => {
        console.log('WebSocket 연결됨');
        if (this.sessionId) {
          this.ws.send(JSON.stringify({ type: 'subscribe', session_id: this.sessionId }));
        }
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage(data);
          this._notifyListeners(data);
        } catch (e) {
          console.error('WebSocket 메시지 파싱 오류:', e);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket 오류:', error);
      };

      this.ws.onclose = () => {
        console.log('WebSocket 연결 종료');
        // 재연결 시도
        setTimeout(() => this.connectWebSocket(onMessage), 3000);
      };
    } catch (error) {
      console.error('WebSocket 연결 실패:', error);
    }
  }

  /**
   * WebSocket 연결 해제
   */
  disconnectWebSocket() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * 이벤트 리스너 등록
   */
  addListener(callback) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  /**
   * 리스너들에게 알림
   */
  _notifyListeners(data) {
    this.listeners.forEach((callback) => {
      try {
        callback(data);
      } catch (e) {
        console.error('리스너 실행 오류:', e);
      }
    });
  }

  /**
   * 단계별 실행 (개별 Agent 호출)
   */
  async runStep(stepId) {
    return this.runWorkflow(stepId);
  }

  /**
   * 세션 초기화
   */
  resetSession() {
    this.sessionId = null;
    this.disconnectWebSocket();
    this.listeners.clear();
  }
}

// 싱글톤 인스턴스
const agentWorkflowService = new AgentWorkflowService();

export default agentWorkflowService;
export { calculateProgress };
