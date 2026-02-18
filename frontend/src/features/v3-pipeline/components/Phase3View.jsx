import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowRight,
  ArrowLeft,
  RefreshCw,
  Copy,
  Check,
  Loader2,
} from "lucide-react";
import PhaseIndicator from "./PhaseIndicator";

const Phase3View = ({
  onNext,
  onBack,
  onPhaseClick,
  onHomeClick,
  angleData,
  generatedDraft = null,
  isGenerating = false,
  onRegenerate,
}) => {
  const [draft, setDraft] = useState(generatedDraft || "");
  const [copied, setCopied] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const editorRef = useRef(null);

  useEffect(() => {
    if (generatedDraft) {
      setDraft(generatedDraft);
    }
  }, [generatedDraft]);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(draft);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSubmit = () => {
    if (draft.trim()) {
      onNext({ draft, angleData });
    }
  };

  // Streaming animation for draft
  const [displayedDraft, setDisplayedDraft] = useState("");
  useEffect(() => {
    if (isGenerating && generatedDraft) {
      let index = 0;
      const interval = setInterval(() => {
        if (index < generatedDraft.length) {
          setDisplayedDraft(generatedDraft.slice(0, index + 1));
          index++;
        } else {
          clearInterval(interval);
        }
      }, 10);
      return () => clearInterval(interval);
    } else if (!isGenerating && generatedDraft) {
      setDisplayedDraft(generatedDraft);
    }
  }, [isGenerating, generatedDraft]);

  return (
    <div className="min-h-screen flex flex-col bg-bg-100">
      {/* Minimal Header */}
      <header className="flex-shrink-0 bg-bg-100">
        <PhaseIndicator currentPhase={3} onPhaseClick={onPhaseClick} onHomeClick={onHomeClick} />
      </header>

      {/* Main Content - Maximized Editor */}
      <main className="flex-1 flex flex-col px-6 py-8">
        <div className="flex-1 max-w-4xl w-full mx-auto flex flex-col">
          {/* Angle Context - Subtle badge */}
          <motion.div
            className="flex items-center gap-3 mb-6"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <span className="px-3 py-1.5 bg-text-100/10 text-text-200 text-sm font-medium rounded-full">
              {angleData?.selectedAngle?.title || "프레임워크"}
            </span>
            <span className="text-text-400 text-sm">기준으로 작성됨</span>
          </motion.div>

          {/* Editor Area */}
          <motion.div
            className="flex-1 relative"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
          >
            {/* Loading State */}
            {isGenerating && !displayedDraft && (
              <div className="absolute inset-0 flex flex-col items-center justify-center bg-always-white rounded-2xl shadow-xl shadow-text-100/10">
                <Loader2 className="w-8 h-8 text-text-300 animate-spin mb-4" />
                <p className="text-text-200">초안을 작성하고 있습니다...</p>
                <p className="text-text-400 text-sm mt-2">
                  잠시만 기다려주세요
                </p>
              </div>
            )}

            {/* Editor - Shadow instead of border, like Phase 1 */}
            <div
              className={`
                relative flex flex-col min-h-[560px] max-h-[calc(100vh-240px)]
                bg-always-white rounded-2xl
                transition-all duration-300 ease-out
                ${isEditing
                  ? "shadow-2xl shadow-text-100/15"
                  : "shadow-xl shadow-text-100/8"
                }
              `}
            >
              {/* Scrollable content area */}
              <div className="flex-1 overflow-y-auto p-8 pb-4">
                {isEditing ? (
                  <textarea
                    ref={editorRef}
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    onBlur={() => setIsEditing(false)}
                    className="
                      w-full min-h-[450px] h-full
                      bg-transparent resize-none
                      text-text-100 leading-relaxed
                      focus:outline-none
                      text-lg
                    "
                    style={{
                      fontFamily: "Georgia, 'Noto Serif KR', serif",
                      caretColor: "hsl(var(--text-100))"
                    }}
                    autoFocus
                  />
                ) : (
                  <div
                    onClick={() => {
                      setIsEditing(true);
                      setTimeout(() => editorRef.current?.focus(), 0);
                    }}
                    className="
                      min-h-[450px] cursor-text
                      text-text-100 leading-relaxed
                      text-lg
                      whitespace-pre-wrap
                    "
                    style={{ fontFamily: "Georgia, 'Noto Serif KR', serif" }}
                  >
                    {displayedDraft || draft || (
                      <span className="text-text-400/50">
                        AI가 초안을 생성합니다...
                      </span>
                    )}
                    {isGenerating && (
                      <span className="inline-block w-0.5 h-5 bg-text-100 animate-pulse ml-0.5" />
                    )}
                  </div>
                )}
              </div>

              {/* Bottom toolbar - fixed at bottom of card */}
              <AnimatePresence>
                {(draft || displayedDraft) && (
                  <motion.div
                    className="flex-shrink-0 px-8 py-4 border-t border-border-200/30 flex items-center justify-between"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                  >
                    {/* Left: Word count */}
                    <span className="text-text-400/60 text-sm">
                      {draft.length.toLocaleString()}자
                    </span>

                    {/* Center: Edit hint */}
                    <span className="text-text-400/40 text-xs">
                      클릭하여 직접 수정 가능
                    </span>

                    {/* Right: Action buttons */}
                    {!isGenerating && (
                      <div className="flex items-center gap-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCopy();
                          }}
                          className="
                            flex items-center gap-1.5 px-3 py-1.5
                            bg-bg-100 hover:bg-bg-200
                            rounded-lg text-xs text-text-300
                            transition-colors duration-200
                          "
                        >
                          {copied ? (
                            <>
                              <Check className="w-3.5 h-3.5 text-green-500" />
                              <span>복사됨</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3.5 h-3.5" />
                              <span>복사</span>
                            </>
                          )}
                        </button>

                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onRegenerate?.();
                          }}
                          className="
                            flex items-center gap-1.5 px-3 py-1.5
                            bg-bg-100 hover:bg-bg-200
                            rounded-lg text-xs text-text-300
                            transition-colors duration-200
                          "
                        >
                          <RefreshCw className="w-3.5 h-3.5" />
                          <span>재생성</span>
                        </button>
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        </div>

        {/* Bottom Action Bar - Matching Phase 1 & 2 */}
        <motion.div
          className="max-w-4xl mx-auto w-full px-6 py-6 flex items-center justify-between"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.4 }}
        >
          {/* Back Button - Ghost style */}
          <button
            onClick={onBack}
            className="
              flex items-center gap-2 px-4 py-2.5
              text-text-400 hover:text-text-200
              rounded-full
              transition-all duration-200
              hover:bg-bg-200
            "
          >
            <ArrowLeft className="w-5 h-5" />
            <span className="text-sm font-medium">이전</span>
          </button>

          {/* Next Button - Elegant, matching Phase 1 & 2 */}
          <motion.button
            onClick={handleSubmit}
            disabled={!draft.trim() || isGenerating}
            className={`
              flex items-center gap-2 px-8 py-3
              rounded-full font-medium text-sm
              transition-all duration-300
              ${draft.trim() && !isGenerating
                ? "bg-text-100 text-bg-000 hover:bg-text-200 shadow-lg shadow-text-100/20"
                : "bg-bg-200 text-text-400 cursor-not-allowed"
              }
            `}
            whileHover={draft.trim() && !isGenerating ? { scale: 1.02, y: -1 } : {}}
            whileTap={draft.trim() && !isGenerating ? { scale: 0.98 } : {}}
          >
            <span>교열 진행하기</span>
            <ArrowRight className="w-4 h-4" />
          </motion.button>
        </motion.div>
      </main>
    </div>
  );
};

export default Phase3View;
