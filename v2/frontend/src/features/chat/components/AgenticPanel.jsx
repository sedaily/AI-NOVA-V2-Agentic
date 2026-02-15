import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bot,
  Loader2,
  CheckCircle2,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Sparkles,
  FileText,
  PenTool,
  BookOpen,
  Globe,
  Zap,
  Search,
  Shield,
  Copy,
  Check,
} from "lucide-react";
import ReactMarkdown from "react-markdown";

// 도구 아이콘 매핑
const TOOL_ICONS = {
  analyze_content: <Search className="w-4 h-4" />,
  write_article: <FileText className="w-4 h-4" />,
  generate_titles: <Sparkles className="w-4 h-4" />,
  proofread: <PenTool className="w-4 h-4" />,
  polish_writing: <BookOpen className="w-4 h-4" />,
  translate_foreign: <Globe className="w-4 h-4" />,
  search_related: <Search className="w-4 h-4" />,
  fact_check: <Shield className="w-4 h-4" />,
};

const TOOL_NAMES = {
  analyze_content: "콘텐츠 분석",
  write_article: "기사 작성",
  generate_titles: "제목 생성",
  proofread: "교열",
  polish_writing: "퇴고",
  translate_foreign: "외신 번역",
  search_related: "관련 검색",
  fact_check: "팩트체크",
};

const TOOL_COLORS = {
  analyze_content: "from-blue-500 to-cyan-500",
  write_article: "from-orange-500 to-red-500",
  generate_titles: "from-purple-500 to-pink-500",
  proofread: "from-green-500 to-emerald-500",
  polish_writing: "from-teal-500 to-green-500",
  translate_foreign: "from-indigo-500 to-violet-500",
  search_related: "from-amber-500 to-yellow-500",
  fact_check: "from-red-500 to-rose-500",
};

const AgenticPanel = ({
  isOpen,
  onClose,
  executionLog = [],
  finalResult,
  isRunning,
  iterations,
  onCopyResult,
}) => {
  const [expandedSteps, setExpandedSteps] = useState({});
  const [copied, setCopied] = useState(false);
  const logEndRef = useRef(null);

  // 자동 스크롤
  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [executionLog]);

  const toggleStep = (index) => {
    setExpandedSteps((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  const handleCopy = () => {
    if (finalResult) {
      navigator.clipboard.writeText(finalResult);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      onCopyResult?.();
    }
  };

  if (!isOpen) return null;

  // 도구 호출만 필터링
  const toolCalls = executionLog.filter(
    (log) => log.type === "tool_call" || log.type === "tool_result"
  );

  // 도구별 그룹화
  const groupedTools = [];
  for (let i = 0; i < toolCalls.length; i += 2) {
    if (toolCalls[i]?.type === "tool_call") {
      groupedTools.push({
        call: toolCalls[i],
        result: toolCalls[i + 1],
      });
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95 }}
        animate={{ scale: 1 }}
        exit={{ scale: 0.95 }}
        className="bg-bg-100 rounded-2xl shadow-2xl w-full max-w-4xl max-h-[85vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-border-300/10 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-text-100">
                Agentic AI 실행 중
              </h2>
              <p className="text-sm text-text-400">
                {isRunning
                  ? "AI가 자율적으로 작업을 수행하고 있습니다..."
                  : `완료 (${iterations}회 반복)`}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-bg-200 transition text-text-400"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Progress Steps */}
          <div className="space-y-3 mb-6">
            {groupedTools.map((group, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="bg-bg-200/50 rounded-xl overflow-hidden"
              >
                {/* Tool Header */}
                <button
                  onClick={() => toggleStep(idx)}
                  className="w-full px-4 py-3 flex items-center justify-between hover:bg-bg-200 transition"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-8 h-8 rounded-lg bg-gradient-to-br ${
                        TOOL_COLORS[group.call.tool] || "from-gray-500 to-gray-600"
                      } flex items-center justify-center text-white`}
                    >
                      {TOOL_ICONS[group.call.tool] || <Zap className="w-4 h-4" />}
                    </div>
                    <span className="font-medium text-text-100">
                      {TOOL_NAMES[group.call.tool] || group.call.tool}
                    </span>
                    {group.result ? (
                      <CheckCircle2 className="w-4 h-4 text-green-500" />
                    ) : (
                      <Loader2 className="w-4 h-4 text-accent-main-100 animate-spin" />
                    )}
                  </div>
                  {expandedSteps[idx] ? (
                    <ChevronUp className="w-5 h-5 text-text-400" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-text-400" />
                  )}
                </button>

                {/* Tool Details */}
                <AnimatePresence>
                  {expandedSteps[idx] && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="px-4 pb-4"
                    >
                      {group.result && (
                        <div className="bg-bg-100 rounded-lg p-3 text-sm text-text-300 max-h-48 overflow-y-auto">
                          <pre className="whitespace-pre-wrap font-mono text-xs">
                            {group.result.result}
                          </pre>
                        </div>
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ))}

            {/* Running Indicator */}
            {isRunning && (
              <div className="flex items-center gap-2 px-4 py-3 text-text-400">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm">다음 단계 계획 중...</span>
              </div>
            )}

            <div ref={logEndRef} />
          </div>

          {/* Final Result */}
          {finalResult && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-gradient-to-br from-accent-main-100/5 to-purple-500/5 rounded-xl border border-accent-main-100/20 p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-text-100 flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-accent-main-100" />
                  최종 결과
                </h3>
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-bg-200 hover:bg-bg-300 transition text-sm text-text-200"
                >
                  {copied ? (
                    <>
                      <Check className="w-4 h-4 text-green-500" />
                      복사됨
                    </>
                  ) : (
                    <>
                      <Copy className="w-4 h-4" />
                      복사
                    </>
                  )}
                </button>
              </div>
              <div
                className="prose prose-sm max-w-none text-text-200"
                style={{ fontFamily: '"Source Serif 4", serif' }}
              >
                <ReactMarkdown>{finalResult}</ReactMarkdown>
              </div>
            </motion.div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-border-300/10 flex items-center justify-between bg-bg-200/30">
          <div className="text-sm text-text-400">
            {isRunning ? (
              <span className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                AI Agent 실행 중...
              </span>
            ) : (
              <span>
                ✨ {groupedTools.length}개 도구 사용 · {iterations}회 반복
              </span>
            )}
          </div>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-bg-200 hover:bg-bg-300 transition text-text-200"
            >
              닫기
            </button>
            {finalResult && (
              <button
                onClick={handleCopy}
                className="px-4 py-2 rounded-lg bg-accent-main-100 text-white hover:opacity-90 transition"
              >
                결과 복사
              </button>
            )}
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default AgenticPanel;
