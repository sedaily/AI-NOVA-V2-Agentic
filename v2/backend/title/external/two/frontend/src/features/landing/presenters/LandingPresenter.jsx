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
    <div className="min-h-screen overflow-x-hidden bg-[#0a0a0f]">
      {/* Premium Animated Background */}
      <div className="fixed inset-0 -z-10">
        {/* Base gradient - 더 깊고 세련된 배경 */}
        <div className="absolute inset-0 bg-[#0a0a0f]" />
        {/* Subtle gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-b from-purple-950/30 via-transparent to-transparent" />
        {/* Refined ambient lights */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-[-10%] left-[20%] w-[500px] h-[500px] bg-purple-600/10 rounded-full filter blur-[120px]" />
          <div className="absolute top-[20%] right-[10%] w-[400px] h-[400px] bg-blue-600/8 rounded-full filter blur-[100px]" />
          <div className="absolute bottom-[10%] left-[30%] w-[600px] h-[600px] bg-indigo-600/5 rounded-full filter blur-[150px]" />
        </div>
        {/* Subtle noise texture for premium feel */}
        <div className="absolute inset-0 opacity-[0.015]" style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg viewBox=\'0 0 256 256\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cfilter id=\'noise\'%3E%3CfeTurbulence type=\'fractalNoise\' baseFrequency=\'0.8\' numOctaves=\'4\' stitchTiles=\'stitch\'/%3E%3C/filter%3E%3Crect width=\'100%25\' height=\'100%25\' filter=\'url(%23noise)\'/%3E%3C/svg%3E")' }} />
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
          {/* Hero Section - Premium Design */}
          <div
            className={`text-center mb-20 transition-all duration-1000 ${
              isVisible
                ? "opacity-100 translate-y-0"
                : "opacity-0 translate-y-10"
            }`}
          >
            {/* Premium Badge */}
            <div className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-purple-500/10 to-blue-500/10 border border-purple-500/20 rounded-full mb-8 backdrop-blur-sm">
              <Sparkles className="w-4 h-4 text-purple-400" />
              <span className="text-sm font-medium bg-gradient-to-r from-purple-300 to-blue-300 bg-clip-text text-transparent">
                AI 기반 제목 생성 플랫폼
              </span>
            </div>

            {/* Main Title with Glow Effect */}
            <div className="relative">
              {/* Glow effect behind title */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-[400px] h-[100px] bg-purple-500/20 rounded-full filter blur-[60px]" />
              </div>
              <h1 className="relative text-6xl md:text-8xl font-bold mb-6 tracking-tight">
                <span className="bg-gradient-to-r from-white via-purple-300 to-white bg-clip-text text-transparent drop-shadow-2xl">
                  TITLE-HUB
                </span>
              </h1>
            </div>

            <p className="text-xl md:text-2xl text-gray-400 mb-2 font-light tracking-wide">
              AI 제목 생성 시스템
            </p>

          </div>

          {/* Stats Section - Removed */}

          {/* Product Selection */}
          <div className="main-content">
            <div className="product-selection">
              <h2
                className={`text-2xl md:text-3xl font-bold text-center mb-12 text-white transition-all duration-1000 delay-300 ${
                  isVisible
                    ? "opacity-100 translate-y-0"
                    : "opacity-0 translate-y-10"
                }`}
              >
                독자와의 첫 만남, 제목을 추천합니다.
              </h2>

              <div className="grid md:grid-cols-2 gap-6 lg:gap-8 mb-12">
                {/* T5 Card - Premium Glass Design */}
                <div
                  className={`relative group transition-all duration-500 delay-400 ${
                    isVisible
                      ? "opacity-100 translate-y-0"
                      : "opacity-0 translate-y-10"
                  }`}
                  onClick={() => onEngineSelect("T5")}
                >
                  {/* Glow effect */}
                  <div className="absolute -inset-0.5 bg-gradient-to-r from-orange-500/50 to-red-500/50 rounded-2xl blur-lg opacity-0 group-hover:opacity-30 transition-all duration-500" />
                  <div className="relative bg-[#12121a]/90 backdrop-blur-xl rounded-2xl p-8 border border-white/[0.08] hover:border-orange-500/30 transition-all duration-300 cursor-pointer hover:transform hover:scale-[1.02] min-h-[500px] flex flex-col shadow-2xl shadow-black/20">
                    <div className="flex justify-between items-start mb-6">
                      <div className="flex items-center gap-4">
                        <div className="p-3 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl">
                          <Zap className="w-8 h-8 text-white" />
                        </div>
                        <div>
                          <h3 className="text-3xl font-bold text-white mb-1">
                            T5
                          </h3>
                          <p className="text-orange-400 text-sm font-medium">
                            핵심을 꿰뚫는 타이틀
                          </p>
                        </div>
                      </div>
                      <div className="px-3 py-1 bg-orange-500/20 border border-orange-500/30 rounded-full">
                        <span className="text-xs text-orange-300">
                          RECOMMENDED
                        </span>
                      </div>
                    </div>

                    <p className="text-gray-300 mb-6">
                      5가지 다른 세상 엿보기 - <span className="text-orange-400 font-semibold">유형별</span> 차별화된 제목 생성
                    </p>

                    <div className="space-y-3 mb-6 flex-grow">
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-orange-400 flex-shrink-0" />
                        <span className="text-gray-300 text-sm">
                          저널리즘 충실형 (신뢰도 중심)
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-orange-400 flex-shrink-0" />
                        <span className="text-gray-300 text-sm">
                          균형잡힌 후킹형 (정보+호기심)
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-orange-400 flex-shrink-0" />
                        <span className="text-gray-300 text-sm">
                          클릭유도형 (참여도 극대화)
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-orange-400 flex-shrink-0" />
                        <span className="text-gray-300 text-sm">
                          SEO 최적화형 (검색 노출)
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-orange-400 flex-shrink-0" />
                        <span className="text-gray-300 text-sm">
                          소셜미디어형 (바이럴 확산)
                        </span>
                      </div>
                    </div>

                    <button className="w-full bg-gradient-to-r from-orange-500 to-red-500 text-white font-semibold py-3 px-6 rounded-xl hover:from-orange-600 hover:to-red-600 transition-all flex items-center justify-center gap-2 group mt-auto">
                      T5 선택하기
                      <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                    </button>
                  </div>
                </div>

                {/* C7 Card - Premium Glass Design */}
                <div
                  className={`relative group transition-all duration-500 delay-500 ${
                    isVisible
                      ? "opacity-100 translate-y-0"
                      : "opacity-0 translate-y-10"
                  }`}
                  onClick={() => onEngineSelect("C7")}
                >
                  {/* Glow effect */}
                  <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500/50 to-purple-500/50 rounded-2xl blur-lg opacity-0 group-hover:opacity-30 transition-all duration-500" />
                  <div className="relative bg-[#12121a]/90 backdrop-blur-xl rounded-2xl p-8 border border-white/[0.08] hover:border-blue-500/30 transition-all duration-300 cursor-pointer hover:transform hover:scale-[1.02] min-h-[500px] flex flex-col shadow-2xl shadow-black/20">
                    <div className="flex justify-between items-start mb-6">
                      <div className="flex items-center gap-4">
                        <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-500 rounded-xl">
                          <Sparkles className="w-8 h-8 text-white" />
                        </div>
                        <div>
                          <h3 className="text-3xl font-bold text-white mb-1">
                            C7
                          </h3>
                          <p className="text-blue-400 text-sm font-medium">
                            <span className="block">
                              창의력 폭발, 무엇을 상상하든 그 이상의 제목
                            </span>
                          </p>
                        </div>
                      </div>
                      <div className="px-3 py-1 bg-blue-500/20 border border-blue-500/30 rounded-full">
                        <span className="text-xs text-blue-300">CREATIVE</span>
                      </div>
                    </div>

                    <p className="text-gray-300 mb-6">
                      <span className="block md:inline">
                        7가지 창의성 엔진으로{" "}
                        <span className="text-blue-400 font-semibold">
                          매번
                        </span>{" "}
                        새로운 걸작 제목 생성
                      </span>
                    </p>

                    <div className="space-y-3 mb-6 flex-grow">
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <span className="text-gray-300 text-sm">
                          언어 혁신 엔진 (업계 최초 표현 창조)
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <span className="text-gray-300 text-sm">
                          충돌 생성 엔진 (아하! 순간 보장)
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <span className="text-gray-300 text-sm">
                          감정 증폭 엔진 (바로 공유하고 싶은)
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <span className="text-gray-300 text-sm">
                          관점 전환 엔진 (경쟁사가 못 본 각도)
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <span className="text-gray-300 text-sm">
                          문화 코드 엔진 (시대정신과 공명)
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <span className="text-gray-300 text-sm">
                          미래 예측 엔진 (트렌드 선도)
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <span className="text-gray-300 text-sm">
                          바이럴 설계 엔진 (화제성 극대화)
                        </span>
                      </div>
                    </div>

                    <button className="w-full bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold py-3 px-6 rounded-xl hover:from-blue-600 hover:to-purple-600 transition-all flex items-center justify-center gap-2 group mt-auto">
                      C7 선택하기
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
