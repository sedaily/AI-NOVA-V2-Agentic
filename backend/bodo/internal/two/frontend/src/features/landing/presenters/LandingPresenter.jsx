import React from "react";
import { Zap, Sparkles, ArrowRight, CheckCircle2 } from "lucide-react";
import Header from "../../../shared/components/layout/Header";

const LandingPresenter = ({
  // Data props
  isVisible,
  selectedEngine,
  articleInput,
  showArticleInput,
  stats,
  engines,
  features,
  userRole,

  // Action props
  onEngineSelect,
  onArticleInputChange,
  onProceedWithArticle,
  onCancelArticleInput,
  onLogout,
  onLogin,
}) => {
  return (
    <div className="min-h-screen overflow-x-hidden">
      {/* Animated Background */}
      <div className="fixed inset-0 -z-10">
        <div className="absolute inset-0 bg-gradient-to-br from-slate-700 via-blue-800/30 to-slate-700" />
        <div className="absolute inset-0">
          <div className="absolute top-0 -left-4 w-72 h-72 bg-blue-400 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-blob" />
          <div className="absolute top-0 -right-4 w-72 h-72 bg-purple-400 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-blob animation-delay-2000" />
          <div className="absolute -bottom-8 left-20 w-72 h-72 bg-sky-300 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-blob animation-delay-4000" />
        </div>
      </div>

      {/* Header Component */}
      <Header
        onLogout={onLogout}
        onAdminLogin={() => onLogin && onLogin("admin")}
        onHome={() => window.location.reload()}
        isLandingPage={true}
        userRole={userRole}
      />

      {/* Main Content */}
      <main className="relative z-10">
        <div className="container max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          {/* Hero Section */}
          <div
            className={`text-center mb-16 transition-all duration-1000 ${
              isVisible
                ? "opacity-100 translate-y-0"
                : "opacity-0 translate-y-10"
            }`}
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-400/15 border border-blue-400/30 rounded-full mb-6">
              <Sparkles className="w-4 h-4 text-blue-400" />
              <span className="text-sm text-blue-300">
                AI 기반 보도자료 작성 플랫폼
              </span>
            </div>

            <h1 className="text-5xl md:text-6xl font-bold mb-8">
              <span className="bg-gradient-to-r from-white via-blue-200 to-white bg-clip-text text-transparent animate-gradient">
                초안은 AI가, 검증과 취재는 기자가
              </span>
            </h1>

            <div className="my-10">
              <p className="text-lg md:text-xl text-gray-200 mb-3">
                AI가 3분 만에 정리한 초안으로 시작하세요.<br />
                남은 시간, 현장 취재와 팩트체크로 진짜 기사를 완성하세요.
              </p>
            </div>
          </div>

          {/* Stats Section - Removed */}

          {/* Product Selection */}
          <div className="main-content">
            <div className="product-selection">
              <h2
                className={`text-xl md:text-2xl font-semibold text-center mb-10 text-gray-200 transition-all duration-1000 delay-300 ${
                  isVisible
                    ? "opacity-100 translate-y-0"
                    : "opacity-0 translate-y-10"
                }`}
              >
                매일 쏟아지는 보도자료 더미... 이제 AI가 먼저 핵심만 뽑아 초안을
                만듭니다.
              </h2>

              <div className="grid md:grid-cols-2 gap-8 mb-12">
                {/* C1 Card */}
                <div
                  className={`relative group transition-all duration-500 delay-400 ${
                    isVisible
                      ? "opacity-100 translate-y-0"
                      : "opacity-0 translate-y-10"
                  }`}
                  onClick={() => onEngineSelect("11")}
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-orange-600 to-red-600 rounded-2xl blur-xl opacity-20 group-hover:opacity-40 transition-opacity" />
                  <div className="relative bg-gray-800/80 backdrop-blur-xl rounded-2xl p-8 border border-gray-600 hover:border-orange-400/50 transition-all cursor-pointer hover:transform hover:scale-105 min-h-[500px] flex flex-col">
                    <div className="flex justify-between items-start mb-6">
                      <div className="flex items-center gap-4">
                        <div className="p-3 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl">
                          <Zap className="w-8 h-8 text-white" />
                        </div>
                        <div>
                          <h3 className="text-2xl font-bold text-white mb-1">
                            💼 기업 보도자료
                          </h3>
                          <p className="text-orange-400 text-sm font-medium">
                            실적·신제품·투자·M&A·인사
                          </p>
                        </div>
                      </div>
                      <div className="px-3 py-1 bg-orange-500/20 border border-orange-500/30 rounded-full">
                        <span className="text-xs text-orange-300">
                          Corporate PR
                        </span>
                      </div>
                    </div>

                    <div className="space-y-3 mb-6 flex-grow">
                      <div className="flex items-center gap-3">
                        <span className="text-orange-400">✓</span>
                        <span className="text-gray-200 text-sm">
                          분기 실적 자동 분석 (전년/전분기 대비)
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-orange-400">✓</span>
                        <span className="text-gray-200 text-sm">
                          신제품/서비스 핵심 요약
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-orange-400">✓</span>
                        <span className="text-gray-200 text-sm">
                          투자유치 규모와 가치 평가
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-orange-400">✓</span>
                        <span className="text-gray-200 text-sm">
                          M&A/인수합병 영향 분석
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-orange-400">✓</span>
                        <span className="text-gray-200 text-sm">
                          인사 발표 자동 정리
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-orange-400">✓</span>
                        <span className="text-gray-200 text-sm">
                          ESG/사회공헌 팩트 추출
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-orange-400">✓</span>
                        <span className="text-gray-200 text-sm">
                          산업별 맞춤 템플릿 (IT/제조/금융/유통)
                        </span>
                      </div>
                    </div>

                    <button className="w-full bg-gradient-to-r from-orange-500 to-red-500 text-white font-semibold py-3 px-6 rounded-xl hover:from-orange-600 hover:to-red-600 transition-all flex items-center justify-center gap-2 group mt-auto">
                      기업 보도자료 변환하기
                      <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                    </button>
                  </div>
                </div>

                {/* C2 Card */}
                <div
                  className={`relative group transition-all duration-500 delay-500 ${
                    isVisible
                      ? "opacity-100 translate-y-0"
                      : "opacity-0 translate-y-10"
                  }`}
                  onClick={() => onEngineSelect("22")}
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl blur-xl opacity-20 group-hover:opacity-40 transition-opacity" />
                  <div className="relative bg-gray-800/80 backdrop-blur-xl rounded-2xl p-8 border border-gray-600 hover:border-blue-400/50 transition-all cursor-pointer hover:transform hover:scale-105 min-h-[500px] flex flex-col">
                    <div className="flex justify-between items-start mb-6">
                      <div className="flex items-center gap-4">
                        <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-500 rounded-xl">
                          <Sparkles className="w-8 h-8 text-white" />
                        </div>
                        <div>
                          <h3 className="text-2xl font-bold text-white mb-1">
                            🏛️ 정부/공공 보도자료
                          </h3>
                          <p className="text-blue-400 text-sm font-medium">
                            정책·통계·예산·규제·해명
                          </p>
                        </div>
                      </div>
                      <div className="px-3 py-1 bg-blue-500/20 border border-blue-500/30 rounded-full">
                        <span className="text-xs text-blue-300">
                          Gov & Public PR
                        </span>
                      </div>
                    </div>

                    <div className="space-y-3 mb-6 flex-grow">
                      <div className="flex items-center gap-3">
                        <span className="text-blue-400">✓</span>
                        <span className="text-gray-200 text-sm">
                          경제정책 영향 분석 (기재부/산업부)
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-blue-400">✓</span>
                        <span className="text-gray-200 text-sm">
                          부동산/금융 규제 요약 (국토부/금융위)
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-blue-400">✓</span>
                        <span className="text-gray-200 text-sm">
                          고용/노동 정책 정리 (고용부)
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-blue-400">✓</span>
                        <span className="text-gray-200 text-sm">
                          통계청/한은 수치 자동 해석
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-blue-400">✓</span>
                        <span className="text-gray-200 text-sm">
                          정치적 표현 자동 필터링
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-blue-400">✓</span>
                        <span className="text-gray-200 text-sm">
                          정책 수혜 대상 명확화
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-blue-400">✓</span>
                        <span className="text-gray-200 text-sm">
                          부처별 발표 스타일 최적화
                        </span>
                      </div>
                    </div>

                    <button className="w-full bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold py-3 px-6 rounded-xl hover:from-blue-600 hover:to-purple-600 transition-all flex items-center justify-center gap-2 group mt-auto">
                      정부 보도자료 변환하기
                      <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Features Grid - Removed */}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default LandingPresenter;
