import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Sparkles,
  Zap,
  FileText,
  Globe,
  CheckCircle,
  PenTool,
  BookOpen,
  ArrowRight,
  Play,
  Star,
  Users,
  Clock,
  Shield,
  ChevronRight,
  Check,
  X,
  Menu,
  Moon,
  Sun,
} from "lucide-react";

const MarketingLanding = () => {
  const navigate = useNavigate();
  const [isVisible, setIsVisible] = useState(false);
  const [activeTab, setActiveTab] = useState("monthly");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isDark, setIsDark] = useState(() => {
    return document.documentElement.getAttribute("data-theme") === "dark";
  });

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const toggleTheme = () => {
    const newTheme = isDark ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", newTheme);
    localStorage.setItem("theme", newTheme);
    setIsDark(!isDark);
  };

  const features = [
    {
      icon: <FileText className="w-6 h-6" />,
      title: "AI 기사버디",
      description: "보도자료를 3분 만에 기사 초안으로 변환",
      color: "from-orange-500 to-red-500",
      code: "b1",
    },
    {
      icon: <Sparkles className="w-6 h-6" />,
      title: "AI 제목생성",
      description: "클릭을 부르는 헤드라인 5개 즉시 생성",
      color: "from-purple-500 to-pink-500",
      code: "t1",
    },
    {
      icon: <PenTool className="w-6 h-6" />,
      title: "AI 교열",
      description: "맞춤법, 문법, 어색한 표현 자동 교정",
      color: "from-blue-500 to-cyan-500",
      code: "p1",
    },
    {
      icon: <BookOpen className="w-6 h-6" />,
      title: "AI 퇴고",
      description: "문장을 더 읽기 좋게 다듬기",
      color: "from-green-500 to-emerald-500",
      code: "r1",
    },
    {
      icon: <Globe className="w-6 h-6" />,
      title: "AI 외신번역",
      description: "영어/일본어 외신을 자연스러운 한국어로",
      color: "from-indigo-500 to-violet-500",
      code: "f1",
    },
    {
      icon: <Zap className="w-6 h-6" />,
      title: "AI 보도자료",
      description: "보도자료 전용 기사 작성 엔진",
      color: "from-amber-500 to-orange-500",
      code: "w1",
    },
  ];

  const stats = [
    { value: "3분", label: "평균 초안 생성 시간" },
    { value: "98%", label: "AI 분석 정확도" },
    { value: "50+", label: "도입 언론사" },
    { value: "10만+", label: "월간 기사 생성" },
  ];

  const testimonials = [
    {
      content: "마감 시간이 절반으로 줄었습니다. 이제 취재에 더 집중할 수 있어요.",
      author: "김OO 기자",
      role: "경제부",
      company: "A일보",
    },
    {
      content: "외신 번역 품질이 놀랍습니다. 기계 번역 느낌이 전혀 없어요.",
      author: "이OO 기자",
      role: "국제부",
      company: "B경제",
    },
    {
      content: "실적 발표 시즌에 정말 큰 도움이 됩니다. 숫자 정리가 정확해요.",
      author: "박OO 기자",
      role: "증권부",
      company: "C신문",
    },
  ];

  const pricingPlans = [
    {
      name: "Free",
      price: "0",
      description: "AI 기자 도구 체험하기",
      features: [
        "월 10건 기사 생성",
        "기본 AI 모델",
        "이메일 지원",
      ],
      notIncluded: [
        "무제한 기사 생성",
        "Claude Opus 4.5",
        "팀 협업",
        "API 액세스",
      ],
      cta: "무료로 시작",
      popular: false,
    },
    {
      name: "Pro",
      price: activeTab === "monthly" ? "49,000" : "39,000",
      description: "개인 기자를 위한 플랜",
      features: [
        "무제한 기사 생성",
        "Claude Opus 4.5",
        "모든 AI 도구 사용",
        "우선 지원",
        "기사 히스토리 저장",
      ],
      notIncluded: [
        "팀 협업",
        "API 액세스",
      ],
      cta: "Pro 시작하기",
      popular: true,
    },
    {
      name: "Enterprise",
      price: "문의",
      description: "언론사 맞춤 솔루션",
      features: [
        "무제한 기사 생성",
        "Claude Opus 4.5",
        "모든 AI 도구 사용",
        "팀 협업 (무제한)",
        "API 액세스",
        "CMS 연동",
        "전담 매니저",
        "맞춤 프롬프트",
      ],
      notIncluded: [],
      cta: "영업팀 문의",
      popular: false,
    },
  ];

  const handleGetStarted = () => {
    navigate("/11");
  };

  return (
    <div className="min-h-screen bg-bg-100">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-bg-100/80 backdrop-blur-lg border-b border-border-300/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-2">
              <img src="/images/ainova.png" alt="AI NOVA" className="w-8 h-6" />
              <span
                className="text-xl font-medium text-text-100"
                style={{ fontFamily: '"Source Serif 4", "Noto Serif KR", serif' }}
              >
                AI NOVA
              </span>
            </div>

            {/* Desktop Menu */}
            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-sm text-text-300 hover:text-text-100 transition">
                기능
              </a>
              <a href="#pricing" className="text-sm text-text-300 hover:text-text-100 transition">
                가격
              </a>
              <a href="#testimonials" className="text-sm text-text-300 hover:text-text-100 transition">
                후기
              </a>
              <button
                onClick={() => navigate("/")}
                className="flex items-center gap-1.5 text-sm text-text-300 hover:text-text-100 transition"
              >
                <PenTool className="w-4 h-4" />
                워크스페이스
              </button>
              <button
                onClick={toggleTheme}
                className="p-2 rounded-lg hover:bg-bg-200 transition"
              >
                {isDark ? <Sun size={18} /> : <Moon size={18} />}
              </button>
              <button
                onClick={handleGetStarted}
                className="px-4 py-2 bg-accent-main-100 text-white rounded-lg text-sm font-medium hover:opacity-90 transition"
              >
                무료로 시작
              </button>
            </div>

            {/* Mobile Menu Button */}
            <button
              className="md:hidden p-2"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              <Menu size={24} />
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-bg-100 border-t border-border-300/10 py-4 px-4">
            <div className="flex flex-col gap-4">
              <a href="#features" className="text-text-200">기능</a>
              <a href="#pricing" className="text-text-200">가격</a>
              <a href="#testimonials" className="text-text-200">후기</a>
              <button
                onClick={() => navigate("/")}
                className="flex items-center gap-2 text-text-200"
              >
                <PenTool className="w-4 h-4" />
                워크스페이스
              </button>
              <button
                onClick={handleGetStarted}
                className="w-full px-4 py-2 bg-accent-main-100 text-white rounded-lg"
              >
                무료로 시작
              </button>
            </div>
          </div>
        )}
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: isVisible ? 1 : 0, y: isVisible ? 0 : 20 }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-accent-main-100/10 border border-accent-main-100/20 rounded-full mb-6">
              <Sparkles className="w-4 h-4 text-accent-main-100" />
              <span className="text-sm text-accent-main-100">
                Claude Opus 4.5 기반 AI Agent
              </span>
            </div>

            {/* Headline */}
            <h1
              className="text-4xl md:text-6xl lg:text-7xl font-bold text-text-100 mb-6 leading-tight"
              style={{ fontFamily: '"Source Serif 4", "Noto Serif KR", serif' }}
            >
              마감 30분 전,
              <br />
              <span className="bg-gradient-to-r from-accent-main-100 via-orange-400 to-red-500 bg-clip-text text-transparent">
                AI가 당신의 데스크입니다
              </span>
            </h1>

            {/* Subheadline */}
            <p className="text-lg md:text-xl text-text-300 max-w-2xl mx-auto mb-10">
              보도자료 분석, 기사 초안, 제목 생성, 교열까지.
              <br />
              기자의 시간을 아껴 더 깊은 취재에 집중하세요.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
              <button
                onClick={handleGetStarted}
                className="group flex items-center gap-2 px-8 py-4 bg-accent-main-100 text-white rounded-xl text-lg font-medium hover:opacity-90 transition shadow-lg shadow-accent-main-100/25"
              >
                무료로 시작하기
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition" />
              </button>
              <button className="flex items-center gap-2 px-8 py-4 border border-border-300/30 rounded-xl text-text-200 hover:bg-bg-200 transition">
                <Play className="w-5 h-5" />
                데모 보기
              </button>
            </div>

            {/* Hero Image/Demo */}
            <div className="relative max-w-5xl mx-auto">
              <div className="absolute inset-0 bg-gradient-to-r from-accent-main-100/20 to-purple-500/20 rounded-2xl blur-3xl" />
              <div className="relative bg-bg-200 rounded-2xl border border-border-300/20 shadow-2xl overflow-hidden">
                <div className="bg-bg-300 px-4 py-3 flex items-center gap-2 border-b border-border-300/10">
                  <div className="flex gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-500" />
                    <div className="w-3 h-3 rounded-full bg-yellow-500" />
                    <div className="w-3 h-3 rounded-full bg-green-500" />
                  </div>
                  <span className="text-xs text-text-400 ml-2">AI NOVA - 기사 작성 중...</span>
                </div>
                <div className="p-8 md:p-12">
                  <div className="flex items-start gap-4 mb-6">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-accent-main-100 to-orange-500 flex items-center justify-center flex-shrink-0">
                      <Sparkles className="w-5 h-5 text-white" />
                    </div>
                    <div className="flex-1">
                      <div className="bg-bg-100 rounded-xl p-4 border border-border-300/10">
                        <p className="text-text-200 text-left leading-relaxed" style={{ fontFamily: '"Source Serif 4", serif' }}>
                          삼성전자가 차세대 반도체 HBM4를 공개했습니다. 기존 HBM3 대비 대역폭이 50% 향상되었으며, AI 가속기 시장 공략을 위한 핵심 제품으로...
                        </p>
                        <div className="mt-3 flex items-center gap-2">
                          <span className="px-2 py-1 bg-green-500/10 text-green-600 text-xs rounded-full">분석 완료</span>
                          <span className="px-2 py-1 bg-blue-500/10 text-blue-600 text-xs rounded-full">IT/반도체</span>
                          <span className="px-2 py-1 bg-purple-500/10 text-purple-600 text-xs rounded-full">신제품</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="flex justify-end">
                    <div className="inline-flex items-center gap-2 text-sm text-text-400">
                      <Clock className="w-4 h-4" />
                      3분 12초 소요
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-bg-200/50">
        <div className="max-w-7xl mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="text-center"
              >
                <div className="text-3xl md:text-4xl font-bold text-accent-main-100 mb-2">
                  {stat.value}
                </div>
                <div className="text-sm text-text-300">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2
              className="text-3xl md:text-4xl font-bold text-text-100 mb-4"
              style={{ fontFamily: '"Source Serif 4", "Noto Serif KR", serif' }}
            >
              6가지 AI 도구로 기사 작성의 모든 것을
            </h2>
            <p className="text-text-300 max-w-2xl mx-auto">
              초안 작성부터 교열까지, 기자의 워크플로우에 맞춘 전문 AI 도구
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="group relative bg-bg-100 rounded-2xl p-6 border border-border-300/10 hover:border-accent-main-100/30 transition-all hover:shadow-lg cursor-pointer"
                onClick={() => navigate("/11")}
              >
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center text-white mb-4`}>
                  {feature.icon}
                </div>
                <h3 className="text-lg font-semibold text-text-100 mb-2">
                  {feature.title}
                </h3>
                <p className="text-text-300 text-sm mb-4">
                  {feature.description}
                </p>
                <div className="flex items-center text-accent-main-100 text-sm font-medium group-hover:gap-2 transition-all">
                  사용해보기 <ChevronRight className="w-4 h-4" />
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section className="py-24 px-4 bg-bg-200/30">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2
              className="text-3xl md:text-4xl font-bold text-text-100 mb-4"
              style={{ fontFamily: '"Source Serif 4", "Noto Serif KR", serif' }}
            >
              3단계로 기사 완성
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: "01",
                title: "보도자료 업로드",
                description: "PDF, TXT 파일을 드래그하거나 텍스트를 붙여넣기",
                icon: <FileText className="w-8 h-8" />,
              },
              {
                step: "02",
                title: "AI가 분석 & 초안 작성",
                description: "Claude Opus 4.5가 핵심 정보를 추출하고 기사 초안 생성",
                icon: <Sparkles className="w-8 h-8" />,
              },
              {
                step: "03",
                title: "편집 & 완성",
                description: "교열, 퇴고 도구로 다듬고 제목 생성으로 마무리",
                icon: <CheckCircle className="w-8 h-8" />,
              },
            ].map((item, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.2 }}
                className="relative"
              >
                <div className="bg-bg-100 rounded-2xl p-8 border border-border-300/10 h-full">
                  <div className="text-5xl font-bold text-accent-main-100/20 mb-4">
                    {item.step}
                  </div>
                  <div className="w-14 h-14 rounded-xl bg-accent-main-100/10 flex items-center justify-center text-accent-main-100 mb-4">
                    {item.icon}
                  </div>
                  <h3 className="text-xl font-semibold text-text-100 mb-2">
                    {item.title}
                  </h3>
                  <p className="text-text-300">
                    {item.description}
                  </p>
                </div>
                {idx < 2 && (
                  <div className="hidden md:block absolute top-1/2 -right-4 transform -translate-y-1/2">
                    <ArrowRight className="w-8 h-8 text-border-300/30" />
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section id="testimonials" className="py-24 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2
              className="text-3xl md:text-4xl font-bold text-text-100 mb-4"
              style={{ fontFamily: '"Source Serif 4", "Noto Serif KR", serif' }}
            >
              현직 기자들의 솔직한 후기
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {testimonials.map((testimonial, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="bg-bg-100 rounded-2xl p-6 border border-border-300/10"
              >
                <div className="flex gap-1 mb-4">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                  ))}
                </div>
                <p className="text-text-200 mb-6 leading-relaxed">
                  "{testimonial.content}"
                </p>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-bg-300 flex items-center justify-center">
                    <Users className="w-5 h-5 text-text-400" />
                  </div>
                  <div>
                    <div className="font-medium text-text-100">{testimonial.author}</div>
                    <div className="text-sm text-text-400">
                      {testimonial.role} | {testimonial.company}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-24 px-4 bg-bg-200/30">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2
              className="text-3xl md:text-4xl font-bold text-text-100 mb-4"
              style={{ fontFamily: '"Source Serif 4", "Noto Serif KR", serif' }}
            >
              합리적인 가격, 강력한 기능
            </h2>
            <p className="text-text-300 mb-8">
              필요한 만큼만 선택하세요. 언제든 업그레이드 가능합니다.
            </p>

            {/* Billing Toggle */}
            <div className="inline-flex items-center gap-3 bg-bg-100 rounded-full p-1 border border-border-300/10">
              <button
                onClick={() => setActiveTab("monthly")}
                className={`px-4 py-2 rounded-full text-sm transition ${
                  activeTab === "monthly"
                    ? "bg-accent-main-100 text-white"
                    : "text-text-300 hover:text-text-100"
                }`}
              >
                월간 결제
              </button>
              <button
                onClick={() => setActiveTab("yearly")}
                className={`px-4 py-2 rounded-full text-sm transition ${
                  activeTab === "yearly"
                    ? "bg-accent-main-100 text-white"
                    : "text-text-300 hover:text-text-100"
                }`}
              >
                연간 결제
                <span className="ml-1 text-xs text-green-500">-20%</span>
              </button>
            </div>
          </div>

          <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {pricingPlans.map((plan, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                className={`relative bg-bg-100 rounded-2xl p-6 border ${
                  plan.popular
                    ? "border-accent-main-100 shadow-lg shadow-accent-main-100/10"
                    : "border-border-300/10"
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <span className="px-3 py-1 bg-accent-main-100 text-white text-xs font-medium rounded-full">
                      가장 인기
                    </span>
                  </div>
                )}

                <div className="mb-6">
                  <h3 className="text-xl font-semibold text-text-100 mb-2">
                    {plan.name}
                  </h3>
                  <p className="text-sm text-text-400">{plan.description}</p>
                </div>

                <div className="mb-6">
                  <span className="text-4xl font-bold text-text-100">
                    {plan.price === "문의" ? "" : "₩"}
                    {plan.price}
                  </span>
                  {plan.price !== "문의" && plan.price !== "0" && (
                    <span className="text-text-400">/월</span>
                  )}
                </div>

                <button
                  onClick={handleGetStarted}
                  className={`w-full py-3 rounded-xl font-medium mb-6 transition ${
                    plan.popular
                      ? "bg-accent-main-100 text-white hover:opacity-90"
                      : "bg-bg-200 text-text-100 hover:bg-bg-300"
                  }`}
                >
                  {plan.cta}
                </button>

                <div className="space-y-3">
                  {plan.features.map((feature, fIdx) => (
                    <div key={fIdx} className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-green-500 flex-shrink-0" />
                      <span className="text-sm text-text-200">{feature}</span>
                    </div>
                  ))}
                  {plan.notIncluded.map((feature, fIdx) => (
                    <div key={fIdx} className="flex items-center gap-2">
                      <X className="w-4 h-4 text-text-500 flex-shrink-0" />
                      <span className="text-sm text-text-500">{feature}</span>
                    </div>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-24 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-500/10 border border-green-500/20 rounded-full mb-6">
              <Shield className="w-4 h-4 text-green-500" />
              <span className="text-sm text-green-600">7일 무료 체험, 카드 등록 불필요</span>
            </div>

            <h2
              className="text-3xl md:text-5xl font-bold text-text-100 mb-6"
              style={{ fontFamily: '"Source Serif 4", "Noto Serif KR", serif' }}
            >
              지금 바로 시작하세요
            </h2>
            <p className="text-lg text-text-300 mb-8">
              5분 안에 첫 번째 AI 기사를 작성해보세요.
            </p>
            <button
              onClick={handleGetStarted}
              className="group inline-flex items-center gap-2 px-8 py-4 bg-accent-main-100 text-white rounded-xl text-lg font-medium hover:opacity-90 transition shadow-lg shadow-accent-main-100/25"
            >
              무료로 시작하기
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition" />
            </button>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 border-t border-border-300/10">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <img src="/images/ainova.png" alt="AI NOVA" className="w-8 h-6" />
                <span
                  className="text-lg font-medium text-text-100"
                  style={{ fontFamily: '"Source Serif 4", serif' }}
                >
                  AI NOVA
                </span>
              </div>
              <p className="text-sm text-text-400">
                AI 기반 기자 작성 플랫폼
              </p>
            </div>

            <div>
              <h4 className="font-medium text-text-100 mb-4">제품</h4>
              <ul className="space-y-2 text-sm text-text-400">
                <li><a href="#features" className="hover:text-text-200">기능</a></li>
                <li><a href="#pricing" className="hover:text-text-200">가격</a></li>
                <li><a href="#" className="hover:text-text-200">API</a></li>
              </ul>
            </div>

            <div>
              <h4 className="font-medium text-text-100 mb-4">회사</h4>
              <ul className="space-y-2 text-sm text-text-400">
                <li><a href="#" className="hover:text-text-200">소개</a></li>
                <li><a href="#" className="hover:text-text-200">블로그</a></li>
                <li><a href="#" className="hover:text-text-200">채용</a></li>
              </ul>
            </div>

            <div>
              <h4 className="font-medium text-text-100 mb-4">법적 고지</h4>
              <ul className="space-y-2 text-sm text-text-400">
                <li><a href="#" className="hover:text-text-200">이용약관</a></li>
                <li><a href="#" className="hover:text-text-200">개인정보처리방침</a></li>
              </ul>
            </div>
          </div>

          <div className="pt-8 border-t border-border-300/10 flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-sm text-text-500">
              &copy; 2024 AI NOVA. All rights reserved.
            </p>
            <p className="text-sm text-text-500">
              Powered by Claude Opus 4.5
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default MarketingLanding;
