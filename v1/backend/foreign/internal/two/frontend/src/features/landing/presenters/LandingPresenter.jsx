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
                AI 글로벌 뉴스 한국화 엔진
              </span>
            </div>

            <h1 className="text-5xl md:text-6xl font-bold mb-10">
              <span className="bg-gradient-to-r from-white via-pink-200 to-white bg-clip-text text-transparent animate-gradient">
                번역과 초안은 AI가, 취재와 특종은 기자가...
              </span>
            </h1>

            <p className="text-lg md:text-xl text-gray-200 mt-4 mb-4 max-w-3xl mx-auto leading-relaxed">
              외신 번역과 초안 작성은 AI에게 맡기고,<br/>
              경제에 대한 통찰과 특종은 기자가 캡니다.
            </p>

            <p className="text-lg md:text-xl text-gray-300 mt-8 max-w-3xl mx-auto italic">
              "구글 번역기와 씨름하는 사이, AI는 이미 기사 초안을 완성했습니다."
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
                          <h3 className="text-3xl font-bold text-white mb-1">
                            영문 뉴스 → 한글 기사
                          </h3>
                          <p className="text-orange-400 text-sm font-medium">
                            로이터·AP·블룸버그·WSJ
                          </p>
                        </div>
                      </div>
                      <div className="px-3 py-1 bg-orange-500/20 border border-orange-500/30 rounded-full">
                        <span className="text-xs text-orange-300">
                          English
                        </span>
                      </div>
                    </div>

                    <p className="text-gray-200 mb-6">

                    </p>

                    <div className="space-y-3 mb-6 flex-grow">
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-orange-400 flex-shrink-0" />
                        <span className="text-gray-200 text-sm">
                          실시간 외신 번역 (주요 통신사/언론사)
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-orange-400 flex-shrink-0" />
                        <span className="text-gray-200 text-sm">
                          한국 상황 맥락 추가
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-orange-400 flex-shrink-0" />
                        <span className="text-gray-200 text-sm">
                          경제 지표 자동 환산 (달러→원화)
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-orange-400 flex-shrink-0" />
                        <span className="text-gray-200 text-sm">
                          금융/산업 전문용어 표준화
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-orange-400 flex-shrink-0" />
                        <span className="text-gray-200 text-sm">
                          서울경제 스타일 문체 적용
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-orange-400 flex-shrink-0" />
                        <span className="text-gray-200 text-sm">
                          SEO 최적화 제목 5개 제안
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-orange-400 flex-shrink-0" />
                        <span className="text-gray-200 text-sm">
                          인용문 자연스러운 한글 전환
                        </span>
                      </div>
                    </div>

                    <button className="w-full bg-gradient-to-r from-orange-500 to-red-500 text-white font-semibold py-3 px-6 rounded-xl hover:from-orange-600 hover:to-red-600 transition-all flex items-center justify-center gap-2 group mt-auto">
                      영문 뉴스, 한글 기사 작성하기
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
                          <h3 className="text-3xl font-bold text-white mb-1">
                            일본 뉴스 → 한글 기사
                          </h3>
                          <p className="text-blue-400 text-sm font-medium">
                            <span className="block">
                              닛케이·NHK·아사히·요미우리
                            </span>
                          </p>
                        </div>
                      </div>
                      <div className="px-3 py-1 bg-blue-500/20 border border-blue-500/30 rounded-full">
                        <span className="text-xs text-blue-300">Japanese</span>
                      </div>
                    </div>

                    <p className="text-gray-200 mb-6">

                    </p>

                    <div className="space-y-3 mb-6 flex-grow">
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <span className="text-gray-200 text-sm">
                          일본 주요 언론 실시간 번역
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <span className="text-gray-200 text-sm">
                          한일 관계 맥락 자동 추가
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <span className="text-gray-200 text-sm">
                          엔화→원화 실시간 환산
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <span className="text-gray-200 text-sm">
                          일본식 표현 한국식 전환
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <span className="text-gray-200 text-sm">
                          정치/경제 용어 표준화
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <span className="text-gray-200 text-sm">
                          서울경제 보도 문체 적용
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <span className="text-gray-200 text-sm">
                          관련 한국 기업/정책 자동 연결
                        </span>
                      </div>
                    </div>

                    <button className="w-full bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold py-3 px-6 rounded-xl hover:from-blue-600 hover:to-purple-600 transition-all flex items-center justify-center gap-2 group mt-auto">
                      일본 뉴스, 한글 기사 작성하기
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
