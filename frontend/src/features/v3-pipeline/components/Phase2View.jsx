import React, { useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight, ArrowLeft, Sparkles, Check } from "lucide-react";
import PhaseIndicator from "./PhaseIndicator";

const Phase2View = ({
  onNext,
  onBack,
  onPhaseClick,
  onHomeClick,
  sourceData,
  analysisResult = null,
  isLoading = false,
}) => {
  const [selectedAngle, setSelectedAngle] = useState(null);

  // Mock angles - in production, these come from AI analysis
  const angles = analysisResult?.angles || [
    {
      id: 1,
      title: "경제적 파급효과 중심",
      description: "시장 규모, 투자 유치, 일자리 창출 등 경제적 영향력을 강조",
      recommended: true,
      keywords: ["시장규모", "투자", "성장률"],
    },
    {
      id: 2,
      title: "기술 혁신 관점",
      description: "신기술의 특징, 차별점, 기술적 우위를 중점적으로 다룸",
      recommended: false,
      keywords: ["기술", "혁신", "차별화"],
    },
    {
      id: 3,
      title: "사회적 가치 측면",
      description: "환경, ESG, 사회공헌 등 사회적 가치와 의미를 부각",
      recommended: false,
      keywords: ["ESG", "환경", "사회공헌"],
    },
  ];

  const handleSubmit = () => {
    if (selectedAngle) {
      const angle = angles.find((a) => a.id === selectedAngle);
      onNext({ selectedAngle: angle, sourceData });
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-bg-100">
      {/* Header with Phase Indicator */}
      <header className="flex-shrink-0 bg-bg-100">
        <PhaseIndicator currentPhase={2} onPhaseClick={onPhaseClick} onHomeClick={onHomeClick} />
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col items-center px-6 py-8">
        <motion.div
          className="w-full max-w-4xl mx-auto"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        >
          {/* Title - Serif, elegant like Phase 1 */}
          <motion.h1
            className="text-3xl md:text-4xl text-text-100 text-center mb-3 tracking-tight"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.4 }}
            style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
          >
            기사 방향을 선택해주세요
          </motion.h1>
          <motion.p
            className="text-text-300 text-center mb-12 text-lg"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.4 }}
            style={{ fontFamily: "'Noto Sans KR', sans-serif" }}
          >
            AI가 분석한 3가지 프레임워크 중 하나를 선택하세요
          </motion.p>

          {/* Loading State */}
          {isLoading && (
            <motion.div
              className="flex flex-col items-center justify-center py-16"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <div className="w-8 h-8 border-2 border-accent-main-100 border-t-transparent rounded-full animate-spin mb-4" />
              <p className="text-text-300">소재를 분석하고 있습니다...</p>
            </motion.div>
          )}

          {/* Angle Cards */}
          {!isLoading && (
            <motion.div
              className="space-y-4 mb-8"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3, duration: 0.3 }}
            >
              {angles.map((angle, index) => (
                <motion.button
                  key={angle.id}
                  onClick={() => setSelectedAngle(angle.id)}
                  className={`
                    w-full text-left p-6 rounded-2xl
                    transition-all duration-300 ease-out
                    bg-always-white
                    ${selectedAngle === angle.id
                      ? "shadow-xl shadow-text-100/15 ring-2 ring-text-100"
                      : "shadow-md shadow-text-100/5 hover:shadow-lg hover:shadow-text-100/10"
                    }
                  `}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 + index * 0.1, duration: 0.4 }}
                  whileHover={{ y: -2 }}
                  whileTap={{ scale: 0.99 }}
                >
                  <div className="flex items-start gap-4">
                    {/* Selection indicator - Left side */}
                    <div
                      className={`
                        flex-shrink-0 w-6 h-6 rounded-full mt-0.5
                        flex items-center justify-center transition-all duration-300
                        ${selectedAngle === angle.id
                          ? "bg-text-100"
                          : "border-2 border-border-300"
                        }
                      `}
                    >
                      {selectedAngle === angle.id && (
                        <Check className="w-3.5 h-3.5 text-bg-000" strokeWidth={3} />
                      )}
                    </div>

                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3
                          className="font-medium text-lg text-text-100"
                          style={{ fontFamily: "Georgia, 'Noto Serif KR', serif" }}
                        >
                          {angle.title}
                        </h3>
                        {angle.recommended && (
                          <span className="flex items-center gap-1 px-2.5 py-1 bg-text-100/10 text-text-200 text-xs font-medium rounded-full">
                            <Sparkles className="w-3 h-3" />
                            추천
                          </span>
                        )}
                      </div>
                      <p className="text-text-300 mb-4 leading-relaxed">{angle.description}</p>
                      <div className="flex flex-wrap gap-2">
                        {angle.keywords.map((keyword) => (
                          <span
                            key={keyword}
                            className="px-2.5 py-1 bg-bg-100 text-text-400 text-xs rounded-full"
                          >
                            #{keyword}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </motion.button>
              ))}
            </motion.div>
          )}

          {/* Action Buttons - Matching Phase 1 style */}
          {!isLoading && (
            <motion.div
              className="flex items-center justify-between pt-6"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6, duration: 0.4 }}
            >
              {/* Back Button - Ghost style */}
              <button
                onClick={onBack}
                className="
                  flex items-center gap-2 px-4 py-2.5
                  text-text-400 hover:text-text-200
                  rounded-full
                  transition-all duration-200
                  hover:bg-bg-100
                "
              >
                <ArrowLeft className="w-5 h-5" />
                <span className="text-sm font-medium">이전</span>
              </button>

              {/* Next Button - Elegant, matching Phase 1 */}
              <motion.button
                onClick={handleSubmit}
                disabled={!selectedAngle}
                className={`
                  flex items-center gap-2 px-8 py-3
                  rounded-full font-medium text-sm
                  transition-all duration-300
                  ${selectedAngle
                    ? "bg-text-100 text-bg-000 hover:bg-text-200 shadow-lg shadow-text-100/20"
                    : "bg-bg-200 text-text-400 cursor-not-allowed"
                  }
                `}
                whileHover={selectedAngle ? { scale: 1.02, y: -1 } : {}}
                whileTap={selectedAngle ? { scale: 0.98 } : {}}
              >
                <span>초안 작성하기</span>
                <ArrowRight className="w-4 h-4" />
              </motion.button>
            </motion.div>
          )}
        </motion.div>
      </main>
    </div>
  );
};

export default Phase2View;
