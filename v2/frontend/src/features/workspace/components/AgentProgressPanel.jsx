/**
 * AgentProgressPanel
 * AI Agent 워크플로우 진행 상태 표시 컴포넌트
 */

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Loader2,
  CheckCircle,
  Circle,
  AlertCircle,
  Bot,
  FileSearch,
  FileText,
  Type,
  CheckSquare,
  RefreshCw,
  Ruler,
  Layout,
  Search,
  BarChart3,
  Image,
  Volume2,
  ClipboardCheck,
} from 'lucide-react';

// 단계별 아이콘 매핑
const STEP_ICONS = {
  issue_collector: FileSearch,
  source_analyzer: Search,
  source_integrator: FileText,
  w1_writer: FileText,
  t1_titler: Type,
  p1_proofreader: CheckSquare,
  style_checker: CheckSquare,
  quality_gate: CheckCircle,
  r1_reviser: RefreshCw,
  drug_agent: Ruler,
  layout_agent: Layout,
  fact_checker: Search,
  infographic_agent: BarChart3,
  image_agent: Image,
  tts_agent: Volume2,
  final_reviewer: ClipboardCheck,
};

// 단계 그룹 정의
const PHASE_GROUPS = [
  {
    phase: 1,
    name: '소재 수집',
    color: 'blue',
    steps: ['issue_collector', 'source_analyzer', 'source_integrator'],
  },
  {
    phase: 2,
    name: '기사 작성',
    color: 'violet',
    steps: ['w1_writer', 't1_titler', 'p1_proofreader', 'style_checker', 'quality_gate', 'r1_reviser', 'drug_agent', 'layout_agent'],
  },
  {
    phase: 3,
    name: '최종 마무리',
    color: 'emerald',
    steps: ['fact_checker', 'infographic_agent', 'image_agent', 'tts_agent', 'final_reviewer'],
  },
];

const STEP_NAMES = {
  issue_collector: '이슈 수집',
  source_analyzer: '소스 분석',
  source_integrator: '소스 통합',
  w1_writer: '기사 초안',
  t1_titler: '제목 생성',
  p1_proofreader: '교정',
  style_checker: '스타일 검사',
  quality_gate: '품질 검사',
  r1_reviser: '퇴고',
  drug_agent: '길이 조절',
  layout_agent: '레이아웃',
  fact_checker: '팩트체크',
  infographic_agent: '인포그래픽',
  image_agent: '이미지 생성',
  tts_agent: 'TTS 생성',
  final_reviewer: '최종 검수',
};

const AgentProgressPanel = ({
  isRunning,
  currentStep,
  progress,
  phase,
  qualityScore,
  logs,
  error,
}) => {
  // 단계 상태 판단
  const getStepStatus = (stepId, phaseNum) => {
    if (!currentStep) return 'pending';

    const currentPhaseGroup = PHASE_GROUPS.find((g) =>
      g.steps.includes(currentStep)
    );
    const stepPhaseGroup = PHASE_GROUPS.find((g) => g.steps.includes(stepId));

    if (!currentPhaseGroup || !stepPhaseGroup) return 'pending';

    // 이전 페이즈면 완료
    if (stepPhaseGroup.phase < currentPhaseGroup.phase) return 'completed';
    // 다음 페이즈면 대기
    if (stepPhaseGroup.phase > currentPhaseGroup.phase) return 'pending';

    // 같은 페이즈 내에서
    const stepIndex = stepPhaseGroup.steps.indexOf(stepId);
    const currentIndex = currentPhaseGroup.steps.indexOf(currentStep);

    if (stepIndex < currentIndex) return 'completed';
    if (stepIndex === currentIndex) return 'active';
    return 'pending';
  };

  const getStepColor = (status, color) => {
    switch (status) {
      case 'completed':
        return `text-${color}-600 bg-${color}-100`;
      case 'active':
        return `text-white bg-${color}-500`;
      case 'pending':
      default:
        return 'text-gray-400 bg-gray-100';
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
      {/* 헤더 */}
      <div className="p-4 border-b border-gray-100">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-violet-600" />
            <h3 className="font-semibold text-gray-900">AI Agent 워크플로우</h3>
          </div>
          {isRunning && (
            <span className="flex items-center gap-1.5 text-xs text-violet-600 bg-violet-50 px-2 py-1 rounded-full">
              <Loader2 className="w-3 h-3 animate-spin" />
              실행 중
            </span>
          )}
        </div>

        {/* 전체 진행률 */}
        <div className="relative h-2 bg-gray-100 rounded-full overflow-hidden">
          <motion.div
            className="absolute top-0 left-0 h-full bg-gradient-to-r from-violet-500 to-purple-500 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>
        <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
          <span>진행률: {progress}%</span>
          {qualityScore > 0 && (
            <span className={qualityScore >= 80 ? 'text-emerald-600' : 'text-amber-600'}>
              품질: {qualityScore}점
            </span>
          )}
        </div>
      </div>

      {/* 단계별 진행 상태 */}
      <div className="p-4 max-h-80 overflow-y-auto">
        {PHASE_GROUPS.map((group) => (
          <div key={group.phase} className="mb-4 last:mb-0">
            <div className="flex items-center gap-2 mb-2">
              <span
                className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                  phase >= group.phase
                    ? `bg-${group.color}-100 text-${group.color}-600`
                    : 'bg-gray-100 text-gray-400'
                }`}
              >
                Phase {group.phase}
              </span>
              <span className="text-sm text-gray-600">{group.name}</span>
            </div>

            <div className="grid grid-cols-4 gap-2">
              {group.steps.map((stepId) => {
                const status = getStepStatus(stepId, group.phase);
                const Icon = STEP_ICONS[stepId] || Circle;

                return (
                  <motion.div
                    key={stepId}
                    className={`flex flex-col items-center p-2 rounded-lg transition-colors ${
                      status === 'active'
                        ? `bg-${group.color}-50 border border-${group.color}-200`
                        : status === 'completed'
                        ? 'bg-gray-50'
                        : ''
                    }`}
                    animate={status === 'active' ? { scale: [1, 1.02, 1] } : {}}
                    transition={{ duration: 1, repeat: Infinity }}
                  >
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center mb-1 ${
                        status === 'completed'
                          ? `bg-${group.color}-100 text-${group.color}-600`
                          : status === 'active'
                          ? `bg-${group.color}-500 text-white`
                          : 'bg-gray-100 text-gray-400'
                      }`}
                    >
                      {status === 'active' ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : status === 'completed' ? (
                        <CheckCircle className="w-4 h-4" />
                      ) : (
                        <Icon className="w-4 h-4" />
                      )}
                    </div>
                    <span
                      className={`text-[10px] text-center ${
                        status === 'active'
                          ? `text-${group.color}-600 font-medium`
                          : status === 'completed'
                          ? 'text-gray-600'
                          : 'text-gray-400'
                      }`}
                    >
                      {STEP_NAMES[stepId]}
                    </span>
                  </motion.div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* 에러 표시 */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="p-3 bg-red-50 border-t border-red-100"
          >
            <div className="flex items-center gap-2 text-red-600 text-sm">
              <AlertCircle className="w-4 h-4" />
              <span>{error}</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 로그 (축소형) */}
      {logs.length > 0 && (
        <div className="p-3 bg-gray-50 border-t border-gray-100 max-h-32 overflow-y-auto">
          <div className="space-y-1">
            {logs.slice(-5).map((log) => (
              <div
                key={log.id}
                className={`text-xs flex items-center gap-2 ${
                  log.type === 'error'
                    ? 'text-red-600'
                    : log.type === 'success'
                    ? 'text-emerald-600'
                    : 'text-gray-500'
                }`}
              >
                <span className="text-gray-400">{log.timestamp}</span>
                <span>{log.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentProgressPanel;
