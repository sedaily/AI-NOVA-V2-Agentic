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
        <div className="absolute inset-0 bg-gradient-to-br from-pink-900/40 via-purple-800/30 to-rose-900/40" />
        <div className="absolute inset-0">
          <div className="absolute top-0 -left-4 w-72 h-72 bg-pink-400 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-blob" />
          <div className="absolute top-0 -right-4 w-72 h-72 bg-rose-400 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-blob animation-delay-2000" />
          <div className="absolute -bottom-8 left-20 w-72 h-72 bg-fuchsia-300 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-blob animation-delay-4000" />
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
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-pink-400/15 border border-pink-400/30 rounded-full mb-6">
              <Sparkles className="w-4 h-4 text-pink-400" />
              <span className="text-sm text-pink-300">
                AI버디, 일보&기사 작성 파트너
              </span>
            </div>

            <h1 className="text-5xl md:text-6xl font-bold mb-6">
              <span className="bg-gradient-to-r from-white via-pink-200 to-white bg-clip-text text-transparent animate-gradient">
                24시간 깨어있는 AI 동료...<br/>
                일보도, 초안도 함께 씁니다.
              </span>
            </h1>

            <p className="text-lg md:text-xl text-gray-200 mb-4 max-w-4xl mx-auto">
              새벽의 일보 고민, 마감 1시간 전 텅 빈 화면.<br/>
              AI 버디가 옆에 있습니다. 일보는 함께 다듬고, 초안은 같이 잡아갑니다.
            </p>
          </div>

          {/* Stats Section - Removed */}

          {/* Product Selection */}
          <div className="main-content">
            <div className="product-selection">
              <h2
                className={`text-xl md:text-2xl font-semibold text-center mb-12 text-gray-300 transition-all duration-1000 delay-300 ${
                  isVisible
                    ? "opacity-100 translate-y-0"
                    : "opacity-0 translate-y-10"
                }`}
              >
                새벽에도, 주말에도, 마감 직전에도... AI 버디는 24시간 대기 중입니다.
              </h2>

              <div className="grid md:grid-cols-2 gap-8 mb-12">
                {/* 일보 버디 Card - Left */}
                <div
                  className={`relative group transition-all duration-500 delay-400 ${
                    isVisible
                      ? "opacity-100 translate-y-0"
                      : "opacity-0 translate-y-10"
                  }`}
                  onClick={() => onEngineSelect("11")}
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-orange-600 to-amber-600 rounded-2xl blur-xl opacity-20 group-hover:opacity-40 transition-opacity" />
                  <div className="relative bg-gray-800/80 backdrop-blur-xl rounded-2xl p-8 border border-gray-600 hover:border-orange-400/50 transition-all cursor-pointer hover:transform hover:scale-105 min-h-[550px] flex flex-col">
                    <div className="flex justify-between items-start mb-6">
                      <div className="flex items-center gap-4">
                        <div className="p-3 bg-gradient-to-br from-orange-500 to-amber-500 rounded-xl">
                          <span className="text-2xl">🔶</span>
                        </div>
                        <div>
                          <h3 className="text-3xl font-bold text-white mb-1">
                            일보 버디
                          </h3>
                          <p className="text-orange-400 text-sm font-medium">
                            Daily Brief
                          </p>
                        </div>
                      </div>
                    </div>

                    <p className="text-gray-200 mb-6 font-semibold">
                      일보 작성, 이제 혼자가 아닙니다
                    </p>

                    <div className="space-y-3 mb-6 flex-grow">
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-orange-400 flex-shrink-0" />
                        <span className="text-gray-200 text-sm">
                          막연한 아이템 → 구체적 일보로
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-orange-400 flex-shrink-0" />
                        <span className="text-gray-200 text-sm">
                          평범한 팩트 → 특별한 각도로
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-orange-400 flex-shrink-0" />
                        <span className="text-gray-200 text-sm">
                          혼자 고민 → 함께 브레인스토밍
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-orange-400 flex-shrink-0" />
                        <span className="text-gray-200 text-sm">
                          취재 막막 → 취재원 추천
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-orange-400 flex-shrink-0" />
                        <span className="text-gray-200 text-sm">
                          중복 불안 → 차별화 전략 제시
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-orange-400 flex-shrink-0" />
                        <span className="text-gray-200 text-sm">
                          데스크 걱정 → OK 받는 포인트
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-orange-400 flex-shrink-0" />
                        <span className="text-gray-200 text-sm">
                          매일 반복 → 매번 새로운 시각
                        </span>
                      </div>
                    </div>

                    <button className="w-full bg-gradient-to-r from-orange-500 to-amber-500 text-white font-semibold py-3 px-6 rounded-xl hover:from-orange-600 hover:to-amber-600 transition-all flex items-center justify-center gap-2 group mt-auto">
                      아이디어로 일보 작성하기
                      <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                    </button>
                  </div>
                </div>

                {/* 기사 버디 Card - Right */}
                <div
                  className={`relative group transition-all duration-500 delay-500 ${
                    isVisible
                      ? "opacity-100 translate-y-0"
                      : "opacity-0 translate-y-10"
                  }`}
                  onClick={() => onEngineSelect("22")}
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl blur-xl opacity-20 group-hover:opacity-40 transition-opacity" />
                  <div className="relative bg-gray-800/80 backdrop-blur-xl rounded-2xl p-8 border border-gray-600 hover:border-blue-400/50 transition-all cursor-pointer hover:transform hover:scale-105 min-h-[550px] flex flex-col">
                    <div className="flex justify-between items-start mb-6">
                      <div className="flex items-center gap-4">
                        <div className="p-3 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-xl">
                          <span className="text-2xl">🔷</span>
                        </div>
                        <div>
                          <h3 className="text-3xl font-bold text-white mb-1">
                            기사 버디
                          </h3>
                          <p className="text-blue-400 text-sm font-medium">
                            Article Draft
                          </p>
                        </div>
                      </div>
                    </div>

                    <p className="text-gray-200 mb-6 font-semibold">
                      초안 작성, 이제 막막하지 않습니다
                    </p>

                    <div className="space-y-3 mb-6 flex-grow">
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <span className="text-gray-200 text-sm">
                          빈 화면 → 3분 만에 초안
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <span className="text-gray-200 text-sm">
                          첫 문장 막막 → 5가지 시작법
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <span className="text-gray-200 text-sm">
                          팩트만 덩그러니 → 자연스러운 기사로
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <span className="text-gray-200 text-sm">
                          AI 불안 → 투명한 출처 표시
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <span className="text-gray-200 text-sm">
                          분량 고민 → 자동 조절
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <span className="text-gray-200 text-sm">
                          시간 부족 → 긴급 모드 가동
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <span className="text-gray-200 text-sm">
                          송고 불안 → 최종 체크까지
                        </span>
                      </div>
                    </div>

                    <button className="w-full bg-gradient-to-r from-blue-500 to-indigo-500 text-white font-semibold py-3 px-6 rounded-xl hover:from-blue-600 hover:to-indigo-600 transition-all flex items-center justify-center gap-2 group mt-auto">
                      일보로 기사 초안 작성하기
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
