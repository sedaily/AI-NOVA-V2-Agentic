import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowRight,
  ArrowLeft,
  CheckCircle,
  Edit3,
  RefreshCw,
  Loader2,
  ArrowRightLeft,
  Check,
  X,
  Type,
  FileText,
  Pencil,
} from "lucide-react";
import PhaseIndicator from "./PhaseIndicator";

// Type labels and colors
const TYPE_CONFIG = {
  spelling: { label: "맞춤법", color: "bg-red-100 text-red-700" },
  grammar: { label: "문법", color: "bg-orange-100 text-orange-700" },
  punctuation: { label: "구두점", color: "bg-yellow-100 text-yellow-700" },
  style: { label: "문체", color: "bg-blue-100 text-blue-700" },
  concise: { label: "간결", color: "bg-purple-100 text-purple-700" },
  word: { label: "어휘", color: "bg-green-100 text-green-700" },
};

const Phase4View = ({
  onNext,
  onBack,
  onPhaseClick,
  onHomeClick,
  draftData,
  proofreadResult = null,
  revisedResult = null,
  isProcessing = false,
  onReprocess,
}) => {
  const [activeTab, setActiveTab] = useState("proofread");
  const [acceptedChanges, setAcceptedChanges] = useState(new Set());
  const [highlightedId, setHighlightedId] = useState(null);
  const [finalDraft, setFinalDraft] = useState(draftData?.draft || "");
  const contentRef = useRef(null);

  const original = draftData?.draft || "";

  // Mock corrections with more detail
  const corrections = activeTab === "proofread"
    ? proofreadResult?.corrections || [
        { id: 1, original: "됬다", corrected: "됐다", type: "spelling", position: 45 },
        { id: 2, original: "하였다", corrected: "했다", type: "grammar", position: 120 },
        { id: 3, original: "전략적  결정", corrected: "전략적 결정", type: "punctuation", position: 89 },
      ]
    : revisedResult?.revisions || [
        { id: 1, original: "것으로 보인다", corrected: "것이다", type: "concise", position: 150 },
        { id: 2, original: "매우 중요한", corrected: "핵심적인", type: "style", position: 200 },
      ];

  // Calculate summary by type
  const typeSummary = corrections.reduce((acc, c) => {
    acc[c.type] = (acc[c.type] || 0) + 1;
    return acc;
  }, {});

  const toggleChange = (id) => {
    const newSet = new Set(acceptedChanges);
    if (newSet.has(id)) {
      newSet.delete(id);
    } else {
      newSet.add(id);
    }
    setAcceptedChanges(newSet);
  };

  const acceptAll = () => {
    setAcceptedChanges(new Set(corrections.map((c) => c.id)));
  };

  const rejectAll = () => {
    setAcceptedChanges(new Set());
  };

  const handleChipClick = (correction) => {
    setHighlightedId(correction.id);
    // Auto-clear highlight after 2 seconds
    setTimeout(() => setHighlightedId(null), 2000);
  };

  const handleSubmit = () => {
    onNext({ finalDraft: finalDraft, corrections: acceptedChanges });
  };

  // Render text with inline highlights
  const renderHighlightedText = () => {
    let text = original;
    let result = [];
    let lastIndex = 0;

    // Sort corrections by position
    const sortedCorrections = [...corrections].sort((a, b) => a.position - b.position);

    sortedCorrections.forEach((correction, idx) => {
      const pos = text.indexOf(correction.original, lastIndex);
      if (pos !== -1) {
        // Add text before the correction
        if (pos > lastIndex) {
          result.push(
            <span key={`text-${idx}`}>{text.slice(lastIndex, pos)}</span>
          );
        }

        // Add the correction with highlight
        const isHighlighted = highlightedId === correction.id;
        const isAccepted = acceptedChanges.has(correction.id);

        result.push(
          <span
            key={`correction-${correction.id}`}
            className={`
              relative inline-block transition-all duration-300 rounded px-0.5 -mx-0.5
              ${isHighlighted ? "ring-2 ring-yellow-400 bg-yellow-50" : ""}
            `}
          >
            {/* Original (strikethrough if accepted) */}
            <span
              className={`
                ${isAccepted ? "line-through text-red-400/70" : "bg-red-100/50 text-red-700"}
                ${isHighlighted && !isAccepted ? "bg-red-100" : ""}
              `}
            >
              {correction.original}
            </span>
            {/* Corrected (shown if accepted) */}
            {isAccepted && (
              <span className="bg-green-100/50 text-green-700 ml-0.5">
                {correction.corrected}
              </span>
            )}
          </span>
        );

        lastIndex = pos + correction.original.length;
      }
    });

    // Add remaining text
    if (lastIndex < text.length) {
      result.push(<span key="text-end">{text.slice(lastIndex)}</span>);
    }

    return result;
  };

  return (
    <div className="min-h-screen flex flex-col bg-bg-100">
      {/* Header */}
      <header className="flex-shrink-0 bg-bg-100">
        <PhaseIndicator currentPhase={4} onPhaseClick={onPhaseClick} onHomeClick={onHomeClick} />
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden px-6 py-4">
        <div className="flex-1 max-w-5xl w-full mx-auto flex flex-col overflow-hidden">
          {/* Tab Switcher */}
          <motion.div
            className="flex items-center justify-center gap-1 mb-6 p-1 bg-bg-200/50 rounded-full w-fit mx-auto"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <button
              onClick={() => setActiveTab("proofread")}
              className={`
                flex items-center gap-2 px-5 py-2.5 rounded-full
                text-sm font-medium transition-all duration-300
                ${activeTab === "proofread"
                  ? "bg-text-100 text-bg-000 shadow-md"
                  : "text-text-400 hover:text-text-200"
                }
              `}
            >
              <CheckCircle className="w-4 h-4" />
              교열 (맞춤법/문법)
            </button>
            <button
              onClick={() => setActiveTab("revise")}
              className={`
                flex items-center gap-2 px-5 py-2.5 rounded-full
                text-sm font-medium transition-all duration-300
                ${activeTab === "revise"
                  ? "bg-text-100 text-bg-000 shadow-md"
                  : "text-text-400 hover:text-text-200"
                }
              `}
            >
              <Edit3 className="w-4 h-4" />
              퇴고 (문체/표현)
            </button>
          </motion.div>

          {/* Loading State */}
          {isProcessing && (
            <div className="flex-1 flex flex-col items-center justify-center">
              <Loader2 className="w-8 h-8 text-text-300 animate-spin mb-4" />
              <p className="text-text-200">
                {activeTab === "proofread" ? "교열 중..." : "퇴고 중..."}
              </p>
            </div>
          )}

          {/* Summary Dashboard */}
          {!isProcessing && corrections.length > 0 && (
            <motion.div
              className="mb-4 p-4 bg-always-white rounded-xl shadow-sm flex items-center justify-between"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <div className="flex items-center gap-4">
                <span className="text-sm font-medium text-text-100">
                  총 {corrections.length}개 수정
                </span>
                <div className="flex items-center gap-2">
                  {Object.entries(typeSummary).map(([type, count]) => (
                    <span
                      key={type}
                      className={`px-2 py-0.5 rounded-full text-xs font-medium ${TYPE_CONFIG[type]?.color || "bg-gray-100 text-gray-700"}`}
                    >
                      {TYPE_CONFIG[type]?.label || type} {count}
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={acceptAll}
                  className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-green-700 bg-green-50 hover:bg-green-100 rounded-full transition-colors"
                >
                  <Check className="w-3 h-3" />
                  모두 수락
                </button>
                <button
                  onClick={rejectAll}
                  className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-red-700 bg-red-50 hover:bg-red-100 rounded-full transition-colors"
                >
                  <X className="w-3 h-3" />
                  모두 거부
                </button>
              </div>
            </motion.div>
          )}

          {/* Main Content Area */}
          {!isProcessing && (
            <motion.div
              className="flex-1 flex gap-4 overflow-hidden"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.1 }}
            >
              {/* Text Panel with Inline Highlights */}
              <div className="flex-1 flex flex-col overflow-hidden">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-medium text-text-100">수정 미리보기</h3>
                  <span className="text-xs text-text-400">
                    수락된 변경사항이 적용됩니다
                  </span>
                </div>
                <div
                  ref={contentRef}
                  className="flex-1 p-6 bg-always-white rounded-2xl shadow-xl shadow-text-100/10 overflow-y-auto"
                >
                  <div
                    className="text-text-100 leading-loose whitespace-pre-wrap text-base"
                    style={{ fontFamily: "Georgia, 'Noto Serif KR', serif" }}
                  >
                    {renderHighlightedText()}
                  </div>
                </div>
              </div>

              {/* Corrections Sidebar */}
              <div className="w-72 flex flex-col overflow-hidden">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-medium text-text-200">수정 목록</h3>
                  <span className="text-xs text-text-400">
                    {acceptedChanges.size}/{corrections.length} 수락
                  </span>
                </div>
                <div className="flex-1 space-y-3 overflow-y-auto pr-1">
                  {corrections.map((correction) => {
                    const isAccepted = acceptedChanges.has(correction.id);
                    const isHighlighted = highlightedId === correction.id;
                    const typeConfig = TYPE_CONFIG[correction.type] || { label: correction.type, color: "bg-gray-100 text-gray-700" };

                    return (
                      <motion.div
                        key={correction.id}
                        className={`
                          p-4 rounded-2xl cursor-pointer transition-all duration-300
                          ${isAccepted
                            ? "bg-green-50/80 shadow-md shadow-green-200/30"
                            : "bg-always-white shadow-md shadow-text-100/5 hover:shadow-lg hover:shadow-text-100/10"
                          }
                          ${isHighlighted ? "ring-2 ring-yellow-400 shadow-lg" : ""}
                        `}
                        onClick={() => handleChipClick(correction)}
                        whileHover={{ y: -2 }}
                        whileTap={{ scale: 0.98 }}
                      >
                        {/* Type Badge */}
                        <span className={`inline-block px-2.5 py-1 rounded-full text-[10px] font-medium mb-3 ${typeConfig.color}`}>
                          {typeConfig.label}
                        </span>

                        {/* Change Preview */}
                        <div className="flex items-center gap-2 text-sm mb-3">
                          <span className="line-through text-text-400">{correction.original}</span>
                          <ArrowRightLeft className="w-3 h-3 text-text-300" />
                          <span className="text-text-100 font-medium">{correction.corrected}</span>
                        </div>

                        {/* Accept/Reject Buttons */}
                        <div className="flex gap-2">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              const newSet = new Set(acceptedChanges);
                              newSet.add(correction.id);
                              setAcceptedChanges(newSet);
                            }}
                            className={`
                              flex-1 py-2 rounded-xl text-xs font-medium transition-all duration-200
                              ${isAccepted
                                ? "bg-text-100 text-bg-000 shadow-sm"
                                : "bg-bg-100 text-text-300 hover:bg-bg-200"
                              }
                            `}
                          >
                            {isAccepted ? "수락됨 ✓" : "수락"}
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              const newSet = new Set(acceptedChanges);
                              newSet.delete(correction.id);
                              setAcceptedChanges(newSet);
                            }}
                            className={`
                              flex-1 py-2 rounded-xl text-xs font-medium transition-all duration-200
                              bg-bg-100 text-text-400 hover:bg-bg-200
                            `}
                          >
                            거부
                          </button>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              </div>
            </motion.div>
          )}
        </div>

        {/* Bottom Action Bar */}
        <motion.div
          className="max-w-5xl mx-auto w-full px-6 py-4 flex items-center justify-between"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.4 }}
        >
          <button
            onClick={onBack}
            className="flex items-center gap-2 px-4 py-2.5 text-text-400 hover:text-text-200 rounded-full transition-all duration-200 hover:bg-bg-200"
          >
            <ArrowLeft className="w-5 h-5" />
            <span className="text-sm font-medium">이전</span>
          </button>

          <button
            onClick={onReprocess}
            disabled={isProcessing}
            className="flex items-center gap-2 px-4 py-2.5 text-text-400 hover:text-text-200 rounded-full transition-all duration-200 hover:bg-bg-200"
          >
            <RefreshCw className={`w-4 h-4 ${isProcessing ? "animate-spin" : ""}`} />
            <span className="text-sm font-medium">다시 검사</span>
          </button>

          <motion.button
            onClick={handleSubmit}
            disabled={isProcessing}
            className={`
              flex items-center gap-2 px-8 py-3 rounded-full font-medium text-sm transition-all duration-300
              ${!isProcessing
                ? "bg-text-100 text-bg-000 hover:bg-text-200 shadow-lg shadow-text-100/20"
                : "bg-bg-200 text-text-400 cursor-not-allowed"
              }
            `}
            whileHover={!isProcessing ? { scale: 1.02, y: -1 } : {}}
            whileTap={!isProcessing ? { scale: 0.98 } : {}}
          >
            <span>제목 생성하기</span>
            <ArrowRight className="w-4 h-4" />
          </motion.button>
        </motion.div>
      </main>
    </div>
  );
};

export default Phase4View;
