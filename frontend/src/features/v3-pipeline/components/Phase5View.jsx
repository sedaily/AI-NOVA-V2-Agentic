import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  Check,
  Sparkles,
  RefreshCw,
  Copy,
  Download,
  Loader2,
  Edit2,
} from "lucide-react";
import PhaseIndicator from "./PhaseIndicator";

const Phase5View = ({
  onComplete,
  onBack,
  onPhaseClick,
  onHomeClick,
  articleData,
  titleSuggestions = null,
  isGenerating = false,
  onRegenerateTitles,
}) => {
  const [selectedTitle, setSelectedTitle] = useState(null);
  const [customTitle, setCustomTitle] = useState("");
  const [isEditingCustom, setIsEditingCustom] = useState(false);
  const [copied, setCopied] = useState(false);
  const customInputRef = useRef(null);

  // Mock title suggestions
  const titles = titleSuggestions || [
    {
      id: 1,
      title: "삼성전자, AI 반도체 시장 공략...1조원 투자 결정",
      style: "직설형",
      recommended: true,
    },
    {
      id: 2,
      title: "\"AI 시대 주도권 잡겠다\"...삼성, 반도체 대규모 투자",
      style: "인용형",
      recommended: false,
    },
    {
      id: 3,
      title: "삼성의 승부수, AI 반도체에 1조 베팅",
      style: "감성형",
      recommended: false,
    },
  ];

  const handleCopy = async () => {
    const finalTitle = selectedTitle === "custom"
      ? customTitle
      : titles.find((t) => t.id === selectedTitle)?.title;

    if (finalTitle) {
      await navigator.clipboard.writeText(finalTitle);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleComplete = () => {
    const finalTitle = selectedTitle === "custom"
      ? customTitle
      : titles.find((t) => t.id === selectedTitle)?.title;

    onComplete({
      title: finalTitle,
      article: articleData?.finalDraft,
    });
  };

  const handleDownload = () => {
    const finalTitle = selectedTitle === "custom"
      ? customTitle
      : titles.find((t) => t.id === selectedTitle)?.title;

    const content = `${finalTitle}\n\n${articleData?.finalDraft || ""}`;
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `article_${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const isValid = selectedTitle !== null && (selectedTitle !== "custom" || customTitle.trim());

  return (
    <div className="min-h-screen flex flex-col bg-bg-100">
      {/* Header */}
      <header className="flex-shrink-0 bg-bg-100">
        <PhaseIndicator currentPhase={5} onPhaseClick={onPhaseClick} onHomeClick={onHomeClick} />
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 py-8">
        <motion.div
          className="w-full max-w-2xl mx-auto"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          {/* Title */}
          <motion.div
            className="text-center mb-12"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <h2
              className="text-3xl md:text-4xl text-text-100 text-center mb-3 tracking-tight"
              style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
            >
              제목을 선택해주세요
            </h2>
            <p
              className="text-text-300 text-center text-lg"
              style={{ fontFamily: "'Noto Sans KR', sans-serif" }}
            >
              AI가 추천한 제목 중 선택하거나 직접 입력하세요
            </p>
          </motion.div>

          {/* Loading State */}
          {isGenerating && (
            <div className="flex flex-col items-center justify-center py-16">
              <Loader2 className="w-8 h-8 text-text-300 animate-spin mb-4" />
              <p className="text-text-200">제목을 생성하고 있습니다...</p>
              <p className="text-text-400 text-sm mt-2">잠시만 기다려주세요</p>
            </div>
          )}

          {/* Title Options */}
          {!isGenerating && (
            <motion.div
              className="space-y-3 mb-6"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
            >
              {titles.map((item, index) => (
                <motion.button
                  key={item.id}
                  onClick={() => setSelectedTitle(item.id)}
                  className={`
                    w-full text-left p-6 rounded-2xl
                    transition-all duration-300 ease-out
                    bg-always-white
                    ${selectedTitle === item.id
                      ? "shadow-xl shadow-text-100/15 ring-2 ring-text-100"
                      : "shadow-md shadow-text-100/5 hover:shadow-lg hover:shadow-text-100/10"
                    }
                  `}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 + index * 0.1, duration: 0.4 }}
                  whileHover={{ y: -2 }}
                  whileTap={{ scale: 0.99 }}
                >
                  <div className="flex items-start gap-4">
                    {/* Selection indicator - Left side like Phase 2 */}
                    <div
                      className={`
                        flex-shrink-0 w-6 h-6 rounded-full mt-0.5
                        flex items-center justify-center transition-all duration-300
                        ${selectedTitle === item.id
                          ? "bg-text-100"
                          : "border-2 border-border-300"
                        }
                      `}
                    >
                      {selectedTitle === item.id && (
                        <Check className="w-3.5 h-3.5 text-bg-000" strokeWidth={3} />
                      )}
                    </div>

                    <div className="flex-1">
                      <p
                        className="text-lg font-medium text-text-100 mb-2"
                        style={{ fontFamily: "Georgia, 'Noto Serif KR', serif" }}
                      >
                        {item.title}
                      </p>
                      <div className="flex items-center gap-2">
                        <span className="px-2.5 py-1 bg-bg-100 text-text-400 text-xs rounded-full">
                          {item.style}
                        </span>
                        {item.recommended && (
                          <span className="flex items-center gap-1 px-2.5 py-1 bg-text-100/10 text-text-200 text-xs font-medium rounded-full">
                            <Sparkles className="w-3 h-3" />
                            추천
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </motion.button>
              ))}

              {/* Custom Title Input */}
              <motion.button
                onClick={() => {
                  setSelectedTitle("custom");
                  setIsEditingCustom(true);
                  setTimeout(() => customInputRef.current?.focus(), 0);
                }}
                className={`
                  w-full text-left p-6 rounded-2xl
                  transition-all duration-300 ease-out
                  ${selectedTitle === "custom"
                    ? "bg-always-white shadow-xl shadow-text-100/15 ring-2 ring-text-100"
                    : "bg-always-white shadow-md shadow-text-100/5 hover:shadow-lg hover:shadow-text-100/10"
                  }
                `}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5, duration: 0.4 }}
                whileHover={{ y: -2 }}
                whileTap={{ scale: 0.99 }}
              >
                <div className="flex items-center gap-4">
                  {/* Selection indicator */}
                  <div
                    className={`
                      flex-shrink-0 w-6 h-6 rounded-full
                      flex items-center justify-center transition-all duration-300
                      ${selectedTitle === "custom"
                        ? "bg-text-100"
                        : "border-2 border-border-300"
                      }
                    `}
                  >
                    {selectedTitle === "custom" && (
                      <Check className="w-3.5 h-3.5 text-bg-000" strokeWidth={3} />
                    )}
                  </div>

                  <Edit2 className="w-5 h-5 text-text-400" />
                  {isEditingCustom || customTitle ? (
                    <input
                      ref={customInputRef}
                      value={customTitle}
                      onChange={(e) => setCustomTitle(e.target.value)}
                      onBlur={() => setIsEditingCustom(false)}
                      onClick={(e) => e.stopPropagation()}
                      placeholder="직접 입력..."
                      className="
                        flex-1 bg-transparent
                        text-lg text-text-100
                        focus:outline-none
                      "
                      style={{ fontFamily: "Georgia, 'Noto Serif KR', serif" }}
                      autoFocus
                    />
                  ) : (
                    <span className="text-text-400">직접 입력하기</span>
                  )}
                </div>
              </motion.button>

              {/* Regenerate Button */}
              <motion.div
                className="flex justify-center pt-4"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.6 }}
              >
                <button
                  onClick={onRegenerateTitles}
                  className="
                    flex items-center gap-2 px-4 py-2.5
                    text-text-400 hover:text-text-200
                    rounded-full hover:bg-bg-200
                    transition-all duration-200
                  "
                >
                  <RefreshCw className="w-4 h-4" />
                  <span className="text-sm font-medium">다른 제목 추천받기</span>
                </button>
              </motion.div>
            </motion.div>
          )}

          {/* Action Buttons */}
          {!isGenerating && (
            <motion.div
              className="flex items-center justify-between pt-8"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.7, duration: 0.4 }}
            >
              {/* Back Button - Ghost style like other phases */}
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

              {/* Secondary Actions */}
              <div className="flex items-center gap-2">
                <button
                  onClick={handleCopy}
                  disabled={!isValid}
                  className={`
                    flex items-center gap-2 px-3 py-2
                    rounded-full transition-all duration-200
                    ${isValid
                      ? "text-text-400 hover:text-text-200 hover:bg-bg-200"
                      : "text-text-400/40 cursor-not-allowed"
                    }
                  `}
                >
                  {copied ? (
                    <Check className="w-4 h-4 text-green-500" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </button>

                <button
                  onClick={handleDownload}
                  disabled={!isValid}
                  className={`
                    flex items-center gap-2 px-3 py-2
                    rounded-full transition-all duration-200
                    ${isValid
                      ? "text-text-400 hover:text-text-200 hover:bg-bg-200"
                      : "text-text-400/40 cursor-not-allowed"
                    }
                  `}
                >
                  <Download className="w-4 h-4" />
                </button>
              </div>

              {/* Complete Button - Elegant, matching other phases */}
              <motion.button
                onClick={handleComplete}
                disabled={!isValid}
                className={`
                  flex items-center gap-2 px-8 py-3
                  rounded-full font-medium text-sm
                  transition-all duration-300
                  ${isValid
                    ? "bg-text-100 text-bg-000 hover:bg-text-200 shadow-lg shadow-text-100/20"
                    : "bg-bg-200 text-text-400 cursor-not-allowed"
                  }
                `}
                whileHover={isValid ? { scale: 1.02, y: -1 } : {}}
                whileTap={isValid ? { scale: 0.98 } : {}}
              >
                <Check className="w-4 h-4" />
                <span>완료</span>
              </motion.button>
            </motion.div>
          )}
        </motion.div>
      </main>
    </div>
  );
};

export default Phase5View;
