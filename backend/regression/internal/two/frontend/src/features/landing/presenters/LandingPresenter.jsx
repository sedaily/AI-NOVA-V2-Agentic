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
        <div className="absolute inset-0 bg-gradient-to-br from-gray-900 via-emerald-950/30 to-gray-900" />
        <div className="absolute inset-0">
          <div className="absolute top-0 -left-4 w-72 h-72 bg-emerald-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob" />
          <div className="absolute top-0 -right-4 w-72 h-72 bg-teal-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000" />
          <div className="absolute -bottom-8 left-20 w-72 h-72 bg-cyan-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-4000" />
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
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-full mb-6">
              <Sparkles className="w-4 h-4 text-emerald-400" />
              <span className="text-sm text-emerald-300">
                AI 퇴고기 - 기자와 기사의 품격
              </span>
            </div>

            <h1 className="text-5xl md:text-6xl font-bold mb-6">
              <span className="bg-gradient-to-r from-white via-emerald-200 to-white bg-clip-text text-transparent animate-gradient">
                읽히는 기사, 묻히는 기사.<br/>차이는 퇴고입니다.
              </span>
            </h1>

            <p className="text-lg md:text-xl text-gray-300 mb-4 max-w-4xl mx-auto leading-relaxed">
              특종도 첫 줄에서 죽고, 죽었던 기사도 구조를 바꿔 되살아 납니다.<br/>
              퇴고 없는 기사는 영원한 초고일 뿐. 기사는 퇴고를 통해 완성됩니다.
            </p>

            <p className="text-base md:text-lg text-emerald-400 font-medium">
              퇴고할 시간이 없나요? AI 퇴고기는 3분이면 됩니다.
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
                퇴고 유형을 선택하세요
              </h2>

              <div className="grid md:grid-cols-2 gap-8 mb-12">
                {/* 속전속결 퇴고 Card */}
                <div
                  className={`relative group transition-all duration-500 delay-400 ${
                    isVisible
                      ? "opacity-100 translate-y-0"
                      : "opacity-0 translate-y-10"
                  }`}
                  onClick={() => onEngineSelect("11")}
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-orange-600 to-red-600 rounded-2xl blur-xl opacity-20 group-hover:opacity-40 transition-opacity" />
                  <div className="relative bg-gray-900/90 backdrop-blur-xl rounded-2xl p-8 border border-gray-700 hover:border-orange-500/50 transition-all cursor-pointer hover:transform hover:scale-105 min-h-[550px] flex flex-col">
                    <div className="flex justify-between items-start mb-6">
                      <div className="flex items-center gap-4">
                        <div className="p-3 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl">
                          <Zap className="w-8 h-8 text-white" />
                        </div>
                        <div>
                          <h3 className="text-2xl font-bold text-white mb-1">
                            📱 속전속결 퇴고
                          </h3>
                          <p className="text-orange-400 text-sm font-medium">
                            Quick Edit
                          </p>
                        </div>
                      </div>
                      <div className="px-3 py-1 bg-orange-500/20 border border-orange-500/30 rounded-full">
                        <span className="text-xs text-orange-300">
                          1,000자 미만
                        </span>
                      </div>
                    </div>

                    <p className="text-gray-100 mb-6 text-lg font-semibold">
                      "첫 문장 고민 끝"
                    </p>

                    <div className="space-y-3 mb-6 flex-grow">
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-orange-400 flex-shrink-0" />
                        <span className="text-gray-300 text-sm">
                          "어떻게 시작하지?" → 3가지 킬러 오프닝 제시
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-orange-400 flex-shrink-0" />
                        <span className="text-gray-300 text-sm">
                          묻혀있던 5단락 특종 → 1단락 펀치라인으로
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-orange-400 flex-shrink-0" />
                        <span className="text-gray-300 text-sm">
                          "3조원" → "국민 1인당 60만원" 체감 전환
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-orange-400 flex-shrink-0" />
                        <span className="text-gray-300 text-sm">
                          서울경제 스타일 자동 적용 (지난해/올해/%포인트)
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-orange-400 flex-shrink-0" />
                        <span className="text-gray-300 text-sm">
                          모바일 첫 화면 최적화 (2초 승부)
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-orange-400 flex-shrink-0" />
                        <span className="text-gray-300 text-sm">
                          데스크 피드백 전 선제 교정
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-orange-400 flex-shrink-0" />
                        <span className="text-gray-300 text-sm">
                          모바일 70% 이탈 → 끝까지 스크롤
                        </span>
                      </div>
                    </div>

                    <button className="w-full bg-gradient-to-r from-orange-500 to-red-500 text-white font-semibold py-3 px-6 rounded-xl hover:from-orange-600 hover:to-red-600 transition-all flex items-center justify-center gap-2 group mt-auto">
                      속전속결 퇴고하기
                      <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                    </button>
                  </div>
                </div>

                {/* 구조분석 퇴고 Card */}
                <div
                  className={`relative group transition-all duration-500 delay-500 ${
                    isVisible
                      ? "opacity-100 translate-y-0"
                      : "opacity-0 translate-y-10"
                  }`}
                  onClick={() => onEngineSelect("22")}
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl blur-xl opacity-20 group-hover:opacity-40 transition-opacity" />
                  <div className="relative bg-gray-900/90 backdrop-blur-xl rounded-2xl p-8 border border-gray-700 hover:border-blue-500/50 transition-all cursor-pointer hover:transform hover:scale-105 min-h-[550px] flex flex-col">
                    <div className="flex justify-between items-start mb-6">
                      <div className="flex items-center gap-4">
                        <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-500 rounded-xl">
                          <Sparkles className="w-8 h-8 text-white" />
                        </div>
                        <div>
                          <h3 className="text-2xl font-bold text-white mb-1">
                            📄 구조분석 퇴고
                          </h3>
                          <p className="text-blue-400 text-sm font-medium">
                            Deep Edit
                          </p>
                        </div>
                      </div>
                      <div className="px-3 py-1 bg-blue-500/20 border border-blue-500/30 rounded-full">
                        <span className="text-xs text-blue-300">1,000자 이상</span>
                      </div>
                    </div>

                    <p className="text-gray-100 mb-6 text-lg font-semibold">
                      "끝까지 읽히는 기사"
                    </p>

                    <div className="space-y-3 mb-6 flex-grow">
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <span className="text-gray-300 text-sm">
                          "중간에 다 떨어져" → 긴장감 유지 구조 설계
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <span className="text-gray-300 text-sm">
                          평평한 나열 → 극적인 서사 구조로
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <span className="text-gray-300 text-sm">
                          지루한 데이터 → 흥미로운 스토리로
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <span className="text-gray-300 text-sm">
                          "너무 길어" → "벌써 끝?"으로
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <span className="text-gray-300 text-sm">
                          타사 기자도 끝까지 읽는 구조
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <span className="text-gray-300 text-sm">
                          묻힌 킬러 팩트 발굴 → 적재적소 배치
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <span className="text-gray-300 text-sm">
                          독자 피로도 관리 (숨 쉴 곳 배치)
                        </span>
                      </div>
                    </div>

                    <button className="w-full bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold py-3 px-6 rounded-xl hover:from-blue-600 hover:to-purple-600 transition-all flex items-center justify-center gap-2 group mt-auto">
                      구조분석 퇴고하기
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
