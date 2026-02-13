import React from "react";
import {
  Zap,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  TrendingUp,
  Users,
  Shield,
} from "lucide-react";
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
        <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-slate-800/30 to-slate-900" />
        <div className="absolute inset-0">
          <div className="absolute top-0 -left-4 w-72 h-72 bg-slate-500 rounded-full mix-blend-multiply filter blur-xl opacity-15 animate-blob" />
          <div className="absolute top-0 -right-4 w-72 h-72 bg-indigo-500 rounded-full mix-blend-multiply filter blur-xl opacity-15 animate-blob animation-delay-2000" />
          <div className="absolute -bottom-8 left-20 w-72 h-72 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-15 animate-blob animation-delay-4000" />
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
        <div className="container max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-12">
          {/* Hero Section */}
          <div
            className={`text-center mb-8 sm:mb-16 transition-all duration-1000 ${
              isVisible
                ? "opacity-100 translate-y-0"
                : "opacity-0 translate-y-10"
            }`}
          >
            <div className="inline-flex items-center gap-2 px-3 sm:px-4 py-1.5 sm:py-2 bg-slate-500/15 border border-slate-500/30 rounded-full mb-4 sm:mb-6 backdrop-blur-sm shadow-lg">
              <Sparkles className="w-3 h-3 sm:w-4 sm:h-4 text-slate-400" />
              <span className="text-xs sm:text-sm text-slate-300">
                AI 기반 교열 서비스
              </span>
            </div>

            <h1 className="text-2xl sm:text-4xl md:text-5xl lg:text-6xl font-bold mb-3 sm:mb-8 md:mb-12 leading-tight text-white">
              <span className="block sm:hidden">
                <span className="block">기사 신뢰도의 최후 관문</span>
                <span className="block">AI 교열</span>
              </span>
              <span className="hidden sm:block bg-gradient-to-r from-white via-slate-200 to-white bg-clip-text text-transparent animate-gradient">
                <span className="sm:inline">기사 신뢰도의 최후 관문,</span>
                <span className="sm:inline sm:ml-2">AI 교열</span>
              </span>
            </h1>
          </div>

          {/* Stats Section - Hidden */}

          {/* Middle Text Section */}
          <div className="flex justify-center mb-4 sm:mb-8 md:mb-12">
            <p className="text-base sm:text-lg md:text-xl lg:text-2xl text-gray-300 max-w-3xl mx-auto text-center px-4">
              <span className="block sm:inline">맞춤법과 문법을 정확하게,</span>
              <span className="block sm:inline sm:ml-1">표기는 일관되게</span>
              <br className="hidden sm:block" />
              <span className="block mt-1 sm:mt-0">AI가 꼼꼼히 검토하고 제안합니다.</span>
            </p>
          </div>

          {/* Product Selection */}
          <div className="main-content">
            <div className="product-selection">
              <h2
                className={`text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl font-bold text-center mb-4 sm:mb-8 md:mb-12 text-white transition-all duration-1000 delay-300 px-4 ${
                  isVisible
                    ? "opacity-100 translate-y-0"
                    : "opacity-0 translate-y-10"
                }`}
              >
                <span className="block sm:inline">귀찮지만 없으면 불안한<span className="hidden sm:inline">,</span></span>{" "}
                <span className="block sm:inline sm:ml-1 text-blue-400">저널리즘의 필수</span>
                <span className="hidden sm:inline">...</span>
                <br className="block sm:hidden" />
                <span className="block sm:inline text-slate-300 mt-1 sm:mt-0 sm:ml-1">송고 전 6초</span>
                <span className="hidden sm:inline">,</span>
                <span className="inline sm:inline sm:ml-1">AI 교열로 안심하세요.</span>
              </h2>

              <div className="grid md:grid-cols-2 gap-4 sm:gap-6 md:gap-8 mb-8 sm:mb-12 px-2 sm:px-0">
                {/* T5 Card */}
                <div
                  className={`relative group transition-all duration-500 delay-400 ${
                    isVisible
                      ? "opacity-100 translate-y-0"
                      : "opacity-0 translate-y-10"
                  }`}
                  onClick={() => onEngineSelect("Basic")}
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-slate-600 via-indigo-600 to-slate-600 rounded-2xl blur-xl opacity-15 group-hover:opacity-35 transition-all duration-500" />
                  <div className="relative bg-gray-900/95 backdrop-blur-xl rounded-2xl p-4 sm:p-6 md:p-8 border border-gray-700/50 hover:border-slate-400/70 hover:shadow-2xl hover:shadow-slate-500/20 transition-all duration-500 cursor-pointer hover:transform hover:scale-[1.02] min-h-[400px] sm:min-h-[450px] md:min-h-[500px] flex flex-col">
                    <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start mb-4 sm:mb-6 gap-3 sm:gap-0">
                      <div className="flex items-center gap-2 sm:gap-3 md:gap-4">
                        <div className="p-2 sm:p-2.5 md:p-3 bg-gradient-to-br from-slate-500 via-indigo-500 to-slate-600 rounded-xl shadow-lg group-hover:shadow-slate-500/30 transition-all duration-300">
                          <Zap className="w-5 h-5 sm:w-6 sm:h-6 md:w-8 md:h-8 text-white" />
                        </div>
                        <div>
                          <h3 className="text-lg sm:text-xl md:text-2xl font-bold text-white mb-0 sm:mb-1">
                            💼 비즈니스 모드
                          </h3>
                          <p className="text-slate-400 text-xs sm:text-sm font-medium">
                            경제 · 금융 · 산업 · 증권 · 부동산
                          </p>
                        </div>
                      </div>
                      <div className="px-2 sm:px-3 py-0.5 sm:py-1 bg-gradient-to-r from-slate-500/20 to-indigo-500/20 border border-slate-400/40 rounded-full backdrop-blur-sm shadow-md self-start sm:self-auto">
                        <span className="text-[10px] sm:text-xs text-slate-300">
                          Business Mode
                        </span>
                      </div>
                    </div>

                    <p className="text-gray-300 mb-6 hidden">
                      <span className="block md:inline">
                        5가지 검사 항목으로
                      </span>
                      <span className="block md:inline md:ml-1">
                        <span className="text-slate-400 font-semibold">
                          8초 이내
                        </span>{" "}
                        정확한 교열 제공
                      </span>
                    </p>

                    <div className="space-y-2 sm:space-y-2.5 md:space-y-3 mb-4 sm:mb-6 flex-grow">
                      <div className="flex items-start gap-3">
                        <span className="text-slate-400 text-xs sm:text-sm mt-0.5">✓</span>
                        <span className="text-gray-300 text-xs sm:text-sm">
                          숫자 표기 일관성 (3억원→3억 원)
                        </span>
                      </div>
                      <div className="flex items-start gap-3">
                        <span className="text-slate-400 text-xs sm:text-sm mt-0.5">✓</span>
                        <span className="text-gray-300 text-xs sm:text-sm">
                          단위 표기 통일 (퍼센트/% 일관성)
                        </span>
                      </div>
                      <div className="flex items-start gap-3">
                        <span className="text-slate-400 text-xs sm:text-sm mt-0.5">✓</span>
                        <span className="text-gray-300 text-xs sm:text-sm">
                          경제 용어 띄어쓰기 정확성
                        </span>
                      </div>
                      <div className="flex items-start gap-3">
                        <span className="text-slate-400 text-xs sm:text-sm mt-0.5">✓</span>
                        <span className="text-gray-300 text-xs sm:text-sm">
                          조사 사용 적절성 (은/는, 이/가, 을/를)
                        </span>
                      </div>
                      <div className="flex items-start gap-3">
                        <span className="text-slate-400 text-xs sm:text-sm mt-0.5">✓</span>
                        <span className="text-gray-300 text-xs sm:text-sm">
                          주어-서술어 호응 검증
                        </span>
                      </div>
                      <div className="flex items-start gap-3">
                        <span className="text-slate-400 text-xs sm:text-sm mt-0.5">✓</span>
                        <span className="text-gray-300 text-xs sm:text-sm">
                          중복 표현 제거 및 정리
                        </span>
                      </div>
                      <div className="flex items-start gap-3">
                        <span className="text-slate-400 text-xs sm:text-sm mt-0.5">✓</span>
                        <span className="text-gray-300 text-xs sm:text-sm">
                          전문 용어 복합명사 규칙
                        </span>
                      </div>
                    </div>

                    <button className="w-full bg-gradient-to-r from-slate-500 via-indigo-500 to-slate-600 text-white font-semibold py-2.5 sm:py-3 px-4 sm:px-6 text-sm sm:text-base rounded-xl hover:from-slate-600 hover:via-indigo-600 hover:to-slate-700 hover:shadow-lg hover:shadow-slate-500/25 transform hover:scale-[1.02] transition-all duration-300 flex items-center justify-center gap-2 group mt-auto">
                      비즈니스 모드 선택하기
                      <ArrowRight className="w-4 h-4 sm:w-5 sm:h-5 group-hover:translate-x-1 transition-transform" />
                    </button>
                  </div>
                </div>

                {/* H8 Card */}
                <div
                  className={`relative group transition-all duration-500 delay-500 ${
                    isVisible
                      ? "opacity-100 translate-y-0"
                      : "opacity-0 translate-y-10"
                  }`}
                  onClick={() => onEngineSelect("Pro")}
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-indigo-600 via-blue-600 to-indigo-600 rounded-2xl blur-xl opacity-15 group-hover:opacity-35 transition-all duration-500" />
                  <div className="relative bg-gray-900/95 backdrop-blur-xl rounded-2xl p-8 border border-gray-700/50 hover:border-indigo-400/70 hover:shadow-2xl hover:shadow-indigo-500/20 transition-all duration-500 cursor-pointer hover:transform hover:scale-[1.02] min-h-[500px] flex flex-col">
                    <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start mb-4 sm:mb-6 gap-3 sm:gap-0">
                      <div className="flex items-center gap-2 sm:gap-3 md:gap-4">
                        <div className="p-2 sm:p-2.5 md:p-3 bg-gradient-to-br from-indigo-500 via-blue-500 to-indigo-600 rounded-xl shadow-lg group-hover:shadow-indigo-500/30 transition-all duration-300">
                          <Sparkles className="w-5 h-5 sm:w-6 sm:h-6 md:w-8 md:h-8 text-white" />
                        </div>
                        <div>
                          <h3 className="text-lg sm:text-xl md:text-2xl font-bold text-white mb-0 sm:mb-1">
                            📰 종합 뉴스 모드
                          </h3>
                          <p className="text-indigo-400 text-xs sm:text-sm font-medium">
                            <span className="block">정치 · 사회 · 문화 · 국제 · 스포츠</span>
                          </p>
                        </div>
                      </div>
                      <div className="px-2 sm:px-3 py-0.5 sm:py-1 bg-gradient-to-r from-indigo-500/20 to-blue-500/20 border border-indigo-400/40 rounded-full backdrop-blur-sm shadow-md self-start sm:self-auto">
                        <span className="text-[10px] sm:text-xs text-indigo-300">General Mode</span>
                      </div>
                    </div>

                    <p className="text-gray-300 mb-6 hidden">
                      <span className="block md:inline">8가지 전문 검사로</span>
                      <span className="block md:inline md:ml-1">
                        <span className="text-indigo-400 font-semibold">
                          15초 이내
                        </span>{" "}
                        완벽한 교정 제공
                      </span>
                    </p>

                    <div className="space-y-2 sm:space-y-2.5 md:space-y-3 mb-4 sm:mb-6 flex-grow">
                      <div className="flex items-start gap-3">
                        <span className="text-indigo-400 text-xs sm:text-sm mt-0.5">✓</span>
                        <span className="text-gray-300 text-xs sm:text-sm">
                          인용 부호 정확성 (큰따옴표/작은따옴표)
                        </span>
                      </div>
                      <div className="flex items-start gap-3">
                        <span className="text-indigo-400 text-xs sm:text-sm mt-0.5">✓</span>
                        <span className="text-gray-300 text-xs sm:text-sm">
                          간접 인용 문법 (~다고, ~라고 정확성)
                        </span>
                      </div>
                      <div className="flex items-start gap-3">
                        <span className="text-indigo-400 text-xs sm:text-sm mt-0.5">✓</span>
                        <span className="text-gray-300 text-xs sm:text-sm">
                          불필요한 피동문 개선
                        </span>
                      </div>
                      <div className="flex items-start gap-3">
                        <span className="text-indigo-400 text-xs sm:text-sm mt-0.5">✓</span>
                        <span className="text-gray-300 text-xs sm:text-sm">
                          애매한 주어 명확화 제안
                        </span>
                      </div>
                      <div className="flex items-start gap-3">
                        <span className="text-indigo-400 text-xs sm:text-sm mt-0.5">✓</span>
                        <span className="text-gray-300 text-xs sm:text-sm">
                          접속사 문체 통일 (그러나/하지만)
                        </span>
                      </div>
                      <div className="flex items-start gap-3">
                        <span className="text-indigo-400 text-xs sm:text-sm mt-0.5">✓</span>
                        <span className="text-gray-300 text-xs sm:text-sm">
                          문단 간 연결성 검토
                        </span>
                      </div>
                      <div className="flex items-start gap-3">
                        <span className="text-indigo-400 text-xs sm:text-sm mt-0.5">✓</span>
                        <span className="text-gray-300 text-xs sm:text-sm">
                          문체 일관성 유지 (경어체/평어체)
                        </span>
                      </div>
                    </div>

                    <button className="w-full bg-gradient-to-r from-indigo-500 via-blue-500 to-indigo-600 text-white font-semibold py-2.5 sm:py-3 px-4 sm:px-6 text-sm sm:text-base rounded-xl hover:from-indigo-600 hover:via-blue-600 hover:to-indigo-700 hover:shadow-lg hover:shadow-indigo-500/25 transform hover:scale-[1.02] transition-all duration-300 flex items-center justify-center gap-2 group mt-auto">
                      종합 뉴스 모드 선택하기
                      <ArrowRight className="w-4 h-4 sm:w-5 sm:h-5 group-hover:translate-x-1 transition-transform" />
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
