/**
 * useAgentWorkflow Hook
 * Agent 워크플로우 상태 관리 및 실시간 업데이트
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import agentWorkflowService, { WORKFLOW_STEPS, calculateProgress } from '../services/agentWorkflowService';

const useAgentWorkflow = () => {
  // 워크플로우 상태
  const [isRunning, setIsRunning] = useState(false);
  const [currentStep, setCurrentStep] = useState(null);
  const [progress, setProgress] = useState(0);
  const [phase, setPhase] = useState(0);

  // 결과 상태
  const [draft, setDraft] = useState('');
  const [titles, setTitles] = useState([]);
  const [qualityScore, setQualityScore] = useState(0);
  const [corrections, setCorrections] = useState([]);
  const [factCheckReport, setFactCheckReport] = useState(null);
  const [finalReport, setFinalReport] = useState(null);

  // 미디어 상태
  const [imageUrl, setImageUrl] = useState(null);
  const [ttsUrl, setTtsUrl] = useState(null);
  const [infographicData, setInfographicData] = useState(null);

  // 에러 상태
  const [error, setError] = useState(null);

  // 이벤트 로그
  const [logs, setLogs] = useState([]);

  // 세션 정보
  const [sessionId, setSessionId] = useState(null);

  // 리스너 참조
  const listenerRef = useRef(null);

  // 로그 추가 헬퍼
  const addLog = useCallback((message, type = 'info') => {
    setLogs((prev) => [
      ...prev,
      {
        id: Date.now(),
        message,
        type,
        timestamp: new Date().toLocaleTimeString(),
      },
    ].slice(-50)); // 최근 50개만 유지
  }, []);

  // 상태 업데이트 핸들러
  const handleWorkflowUpdate = useCallback((data) => {
    switch (data.type) {
      case 'started':
        setIsRunning(true);
        setSessionId(data.sessionId);
        addLog('워크플로우 시작됨', 'success');
        break;

      case 'progress':
        setCurrentStep(data.currentStep || data.current_step);
        setProgress(data.progress || calculateProgress(data.current_step));

        // 단계 정보 찾기
        const stepInfo = Object.values(WORKFLOW_STEPS).find(
          (s) => s.id === (data.currentStep || data.current_step)
        );
        if (stepInfo) {
          setPhase(stepInfo.phase);
          addLog(`[Phase ${stepInfo.phase}] ${stepInfo.name} 진행 중...`);
        }

        // 결과 업데이트
        if (data.draft) setDraft(data.draft);
        if (data.titles) setTitles(data.titles);
        if (data.quality_score !== undefined) setQualityScore(data.quality_score);
        if (data.corrections) setCorrections(data.corrections);
        break;

      case 'completed':
        setIsRunning(false);
        setProgress(100);

        // 최종 결과 반영
        if (data.draft) setDraft(data.draft);
        if (data.titles) setTitles(data.titles);
        if (data.quality_score !== undefined) setQualityScore(data.quality_score);
        if (data.final_report) setFinalReport(data.final_report);
        if (data.image_url) setImageUrl(data.image_url);
        if (data.tts_url) setTtsUrl(data.tts_url);
        if (data.fact_check_report) setFactCheckReport(data.fact_check_report);
        if (data.infographic_data) setInfographicData(data.infographic_data);

        addLog('워크플로우 완료!', 'success');
        break;

      case 'error':
        setError(data.error);
        addLog(`오류: ${data.error}`, 'error');
        break;

      default:
        break;
    }
  }, [addLog]);

  // 리스너 등록/해제
  useEffect(() => {
    listenerRef.current = agentWorkflowService.addListener(handleWorkflowUpdate);

    return () => {
      if (listenerRef.current) {
        listenerRef.current();
      }
    };
  }, [handleWorkflowUpdate]);

  // 워크플로우 시작
  const startWorkflow = useCallback(async (params) => {
    setError(null);
    setLogs([]);
    setProgress(0);
    setPhase(0);
    setDraft('');
    setTitles([]);
    setQualityScore(0);
    setFinalReport(null);

    try {
      const result = await agentWorkflowService.startWorkflow(params);
      setSessionId(result.sessionId);
      addLog(`세션 생성: ${result.sessionId}`);
      return result;
    } catch (err) {
      setError(err.message);
      addLog(`시작 실패: ${err.message}`, 'error');
      throw err;
    }
  }, [addLog]);

  // 워크플로우 실행
  const runWorkflow = useCallback(async (step = 'full') => {
    setIsRunning(true);
    setError(null);

    try {
      addLog(`워크플로우 실행: ${step === 'full' ? '전체' : step}`);
      const result = await agentWorkflowService.runWorkflow(step);

      // 결과 반영
      if (result.draft) setDraft(result.draft);
      if (result.titles) setTitles(result.titles);
      if (result.quality_score !== undefined) setQualityScore(result.quality_score);

      return result;
    } catch (err) {
      setError(err.message);
      setIsRunning(false);
      throw err;
    }
  }, [addLog]);

  // 수정 요청
  const requestRevision = useCallback(async (feedback) => {
    setIsRunning(true);
    setError(null);

    try {
      addLog('수정 요청 중...');
      const result = await agentWorkflowService.requestRevision(feedback);
      addLog('수정 완료', 'success');
      return result;
    } catch (err) {
      setError(err.message);
      setIsRunning(false);
      throw err;
    }
  }, [addLog]);

  // 상태 새로고침
  const refreshStatus = useCallback(async () => {
    try {
      const status = await agentWorkflowService.getStatus();
      if (status) {
        handleWorkflowUpdate({ type: 'progress', ...status });
      }
      return status;
    } catch (err) {
      console.error('상태 조회 실패:', err);
      return null;
    }
  }, [handleWorkflowUpdate]);

  // 세션 초기화
  const resetWorkflow = useCallback(() => {
    agentWorkflowService.resetSession();
    setIsRunning(false);
    setCurrentStep(null);
    setProgress(0);
    setPhase(0);
    setDraft('');
    setTitles([]);
    setQualityScore(0);
    setCorrections([]);
    setFactCheckReport(null);
    setFinalReport(null);
    setImageUrl(null);
    setTtsUrl(null);
    setInfographicData(null);
    setError(null);
    setLogs([]);
    setSessionId(null);
  }, []);

  // 현재 단계 정보 가져오기
  const getCurrentStepInfo = useCallback(() => {
    if (!currentStep) return null;
    return Object.values(WORKFLOW_STEPS).find((s) => s.id === currentStep);
  }, [currentStep]);

  return {
    // 상태
    isRunning,
    currentStep,
    progress,
    phase,
    sessionId,
    error,
    logs,

    // 결과
    draft,
    titles,
    qualityScore,
    corrections,
    factCheckReport,
    finalReport,

    // 미디어
    imageUrl,
    ttsUrl,
    infographicData,

    // 액션
    startWorkflow,
    runWorkflow,
    requestRevision,
    refreshStatus,
    resetWorkflow,

    // 유틸
    getCurrentStepInfo,
    setDraft,
    setTitles,
  };
};

export default useAgentWorkflow;
