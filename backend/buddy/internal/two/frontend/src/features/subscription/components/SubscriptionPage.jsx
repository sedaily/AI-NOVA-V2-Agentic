import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, ArrowLeft, Home, Crown, Zap, Star, Users, TrendingUp, Award, Shield, Clock, Target, MessageSquare } from 'lucide-react';
import { motion } from 'framer-motion';

const SubscriptionPage = () => {
  const navigate = useNavigate();
  const [currentPlan, setCurrentPlan] = useState('free');
  const [userInfo, setUserInfo] = useState(null);
  const [selectedEngine, setSelectedEngine] = useState('11');

  useEffect(() => {
    const loadUserInfo = () => {
      try {
        const storedUserInfo = localStorage.getItem('userInfo');
        const storedEngine = localStorage.getItem('selectedEngine') || '11';
        const storedPlan = localStorage.getItem('userPlan') || 'free';
        
        if (storedUserInfo) {
          const parsed = JSON.parse(storedUserInfo);
          setUserInfo(parsed);
        }
        setSelectedEngine(storedEngine);
        setCurrentPlan(storedPlan);
      } catch (error) {
        console.error('사용자 정보 로드 실패:', error);
      }
    };
    
    loadUserInfo();
  }, []);

  const plans = [
    {
      id: 'free',
      name: '무료 플랜',
      price: '무료',
      description: '개인 사용자를 위한\n기본 칼럼 작성 서비스',
      monthlyTokens: '10,000',
      features: [
        '월 10,000 토큰',
        'C1, 종합 뉴스 엔진 기본 접근',
        '기본 칼럼 작성 (5개)',
        '일일 20회 요청 제한',
        '기본 템플릿 제공',
        '커뮤니티 지원'
      ],
      popular: false,
      ctaText: '무료로 시작'
    },
    {
      id: 'basic',
      name: '베이직 플랜',
      price: '₩29,000',
      originalPrice: '₩39,000',
      description: '전문가를 위한\n고급 칼럼 작성 서비스',
      monthlyTokens: '100,000',
      features: [
        '월 100,000 토큰',
        'C1, 종합 뉴스 엔진 전체 접근',
        '칼럼 작성 무제한',
        '일일 100회 요청',
        '프리미엄 템플릿 20개+',
        'A/B 테스트 기능',
        '우선 기술 지원',
        '사용량 분석 대시보드'
      ],
      popular: true,
      ctaText: '14일 무료 체험'
    },
    {
      id: 'premium',
      name: '프리미엄 플랜',
      price: '₩79,000',
      originalPrice: '₩99,000',
      description: '기업 및 팀을 위한\n최고급 AI 칼럼 작성 서비스',
      monthlyTokens: '500,000',
      features: [
        '월 500,000 토큰',
        '모든 엔진 무제한 접근',
        'API 무제한 접근',
        '커스텀 모델 학습',
        '팀 협업 도구',
        '전담 계정 관리자',
        '실시간 성과 분석',
        'SEO 최적화 보고서',
        '맞춤형 AI 튜닝'
      ],
      popular: false,
      ctaText: '30일 무료 체험'
    }
  ];

  const testimonials = [
    {
      name: '김지연',
      role: '콘텐츠 마케터',
      comment: 'C1 엔진으로 작성한 칼럼의 조회수가 평균 35% 상승했습니다. 정말 놀라운 도구예요.',
      plan: '베이직 플랜'
    },
    {
      name: '박민수',
      role: '디지털 에디터',
      comment: 'C2 엔진의 창의적인 칼럼 작성 능력이 인상적입니다. 업무 효율이 3배 향상되었어요.',
      plan: '프리미엄 플랜'
    },
    {
      name: '이소영',
      role: '프리랜서 작가',
      comment: '무료 플랜만으로도 충분히 유용합니다. 특히 빠른 칼럼 작성에 큰 도움이 됩니다.',
      plan: '무료 플랜'
    }
  ];

  const handleBack = () => {
    const enginePath = selectedEngine.toLowerCase();
    navigate(`/${enginePath}`);
  };

  const handleUpgrade = (planId) => {
    if (planId === currentPlan) return;
    
    // 플랜 업그레이드 로직
    localStorage.setItem('userPlan', planId);
    setCurrentPlan(planId);
    
    // 성공 메시지 표시 후 대시보드로 이동
    setTimeout(() => {
      const enginePath = selectedEngine.toLowerCase();
      navigate(`/${enginePath}/dashboard`);
    }, 1000);
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Custom Header */}
      <header className="sticky top-0 z-50 w-full bg-white/90 backdrop-blur-sm border-b border-slate-200/60">
        <div className="max-w-5xl mx-auto px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <button
              onClick={handleBack}
              className="inline-flex items-center gap-2 text-slate-600 hover:text-slate-900 transition-colors font-medium"
            >
              <Home size={20} />
              <span>홈으로 돌아가기</span>
            </button>
            
            {userInfo && (
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-slate-900 rounded-full flex items-center justify-center text-white text-sm font-medium">
                  {userInfo?.email ? userInfo.email.charAt(0).toUpperCase() : 'U'}
                </div>
                <span className="text-sm text-slate-600 hidden sm:inline font-medium">
                  {userInfo?.email || 'Guest'}
                </span>
              </div>
            )}
          </div>
        </div>
      </header>
      
      <div className="max-w-5xl mx-auto px-6 lg:px-8">
        {/* Hero Section */}
        <div className="pt-20 pb-32 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          >
            <div className="inline-flex items-center gap-2 bg-slate-100 text-slate-700 px-4 py-2 rounded-full text-sm font-medium mb-8">
              <Zap className="w-4 h-4" />
              <span>AI 기반 칼럼 작성 서비스</span>
            </div>
            
            <h1 className="text-3xl md:text-5xl lg:text-7xl font-bold text-slate-900 mb-6 md:mb-8 tracking-tight leading-[1.1]">
              전문적인 칼럼을
              <br />
              <span className="bg-gradient-to-r from-slate-900 to-slate-600 bg-clip-text text-transparent">
                AI가 작성합니다
              </span>
            </h1>
            
            <p className="text-base md:text-lg lg:text-2xl text-slate-600 max-w-3xl mx-auto leading-relaxed mb-10 md:mb-16 font-light">
              <span className="block md:inline">C1과 C2 엔진으로</span>
              <span className="block md:inline md:ml-1">독자의 마음을 사로잡는 칼럼을</span>
              <br className="hidden sm:block" />
              <span className="text-slate-900 font-medium">전문적으로</span> 작성하세요
            </p>
            
            <div className="flex flex-wrap items-center justify-center gap-8 lg:gap-16 text-slate-500">
              <div className="flex items-center gap-3 bg-white/60 backdrop-blur-sm px-4 py-3 rounded-full border border-slate-200/50">
                <Users className="w-5 h-5 text-slate-600" />
                <span className="font-medium text-slate-700 text-sm md:text-base">10,000+ 사용자</span>
              </div>
              <div className="flex items-center gap-3 bg-white/60 backdrop-blur-sm px-4 py-3 rounded-full border border-slate-200/50">
                <Shield className="w-5 h-5 text-slate-600" />
                <span className="font-medium text-slate-700 text-sm md:text-base">14일 무료 체험</span>
              </div>
              <div className="flex items-center gap-3 bg-white/60 backdrop-blur-sm px-4 py-3 rounded-full border border-slate-200/50">
                <Clock className="w-5 h-5 text-slate-600" />
                <span className="font-medium text-slate-700 text-sm md:text-base">24시간 지원</span>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Current Plan Status */}
        {userInfo && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gradient-to-r from-slate-50/90 to-slate-100/50 rounded-3xl p-10 mb-32 border border-slate-200/60 shadow-sm"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-6">
                <div className="w-14 h-14 bg-gradient-to-br from-slate-900 to-slate-700 rounded-2xl flex items-center justify-center text-white font-semibold shadow-lg">
                  {userInfo?.email ? userInfo.email.charAt(0).toUpperCase() : 'U'}
                </div>
                <div>
                  <h3 className="text-base md:text-lg font-semibold text-slate-900 mb-1">
                    현재 플랜: {plans.find(plan => plan.id === currentPlan)?.name || '무료 플랜'}
                  </h3>
                  <p className="text-slate-600">
                    {userInfo?.email || 'Guest User'}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-slate-500 mb-1">사용 중인 엔진</div>
                <div className="font-semibold text-slate-900">
                  {selectedEngine} 엔진
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Value Proposition */}
        <div className="mb-32">
          <div className="text-center mb-20">
            <div className="inline-flex items-center gap-2 bg-slate-100 text-slate-700 px-4 py-2 rounded-full text-sm font-medium mb-6">
              <Target className="w-4 h-4" />
              <span>핵심 가치</span>
            </div>
            <h2 className="text-3xl md:text-4xl lg:text-6xl font-bold text-slate-900 mb-4 md:mb-6 leading-tight">
              왜 AI 칼럼 작성이
              <br />
              필요한가요?
            </h2>
            <p className="text-base md:text-lg lg:text-2xl text-slate-600 max-w-4xl mx-auto font-light leading-relaxed">
              <span className="block md:inline">전문성과 창의성을 겸비한 칼럼으로</span>
              <span className="block md:inline md:ml-1">콘텐츠의 가치를 극대화하세요</span>
            </p>
          </div>
          
          <div className="grid lg:grid-cols-3 gap-10 mb-20">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="group bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-3xl p-10 hover:border-slate-300/80 hover:bg-white hover:shadow-lg transition-all duration-500"
            >
              <div className="w-14 h-14 bg-gradient-to-br from-slate-900 to-slate-700 rounded-2xl flex items-center justify-center mb-8 shadow-lg group-hover:shadow-xl transition-shadow duration-300">
                <Award className="w-7 h-7 text-white" />
              </div>
              <h3 className="text-lg md:text-xl lg:text-2xl font-bold text-slate-900 mb-4 md:mb-6 leading-tight">
                C1 엔진 - 전문성
              </h3>
              <p className="text-slate-600 leading-relaxed text-sm md:text-base lg:text-lg">
                <span className="font-semibold text-slate-900">검증된 알고리즘</span>으로
                5가지 유형의 전문적인 칼럼을 작성합니다.
                <span className="font-semibold text-slate-900">독자 맞춤형 콘텐츠</span>와 가독성을 동시에 고려합니다.
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="group bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-3xl p-10 hover:border-slate-300/80 hover:bg-white hover:shadow-lg transition-all duration-500"
            >
              <div className="w-14 h-14 bg-gradient-to-br from-slate-900 to-slate-700 rounded-2xl flex items-center justify-center mb-8 shadow-lg group-hover:shadow-xl transition-shadow duration-300">
                <Shield className="w-7 h-7 text-white" />
              </div>
              <h3 className="text-lg md:text-xl lg:text-2xl font-bold text-slate-900 mb-4 md:mb-6 leading-tight">
                C2 엔진 - 창의성
              </h3>
              <p className="text-slate-600 leading-relaxed text-sm md:text-base lg:text-lg">
                <span className="font-semibold text-slate-900">창의적인 표현</span>과{' '}
                <span className="font-semibold text-slate-900">독창적인 관점</span>으로
                7가지 창의적 엔진을 통해 차별화된 칼럼을 작성합니다. 트렌드를 반영한 최신 스타일을 제공합니다.
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="group bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-3xl p-10 hover:border-slate-300/80 hover:bg-white hover:shadow-lg transition-all duration-500"
            >
              <div className="w-14 h-14 bg-gradient-to-br from-slate-900 to-slate-700 rounded-2xl flex items-center justify-center mb-8 shadow-lg group-hover:shadow-xl transition-shadow duration-300">
                <TrendingUp className="w-7 h-7 text-white" />
              </div>
              <h3 className="text-lg md:text-xl lg:text-2xl font-bold text-slate-900 mb-4 md:mb-6 leading-tight">
                효율적인 작업
              </h3>
              <p className="text-slate-600 leading-relaxed text-sm md:text-base lg:text-lg">
                <span className="block md:inline">칼럼 작성 시간을 <span className="font-semibold text-slate-900">90% 단축</span>하고</span>{' '}
                <span className="block md:inline"><span className="font-semibold text-slate-900">콘텐츠 품질은 35% 향상</span>시킵니다.</span>{' '}
                <span className="block md:inline">다양한 스타일 중 최적의 칼럼을 선택할 수 있습니다.</span>
              </p>
            </motion.div>
          </div>
        </div>

        {/* Pricing Plans */}
        <div className="mb-32">
          <div className="text-center mb-20">
            <div className="inline-flex items-center gap-2 bg-slate-100 text-slate-700 px-4 py-2 rounded-full text-sm font-medium mb-6">
              <Crown className="w-4 h-4" />
              <span>구독 플랜</span>
            </div>
            <h2 className="text-3xl md:text-4xl lg:text-6xl font-bold text-slate-900 mb-4 md:mb-6 leading-tight">
              플랜을 선택하세요
            </h2>
            <p className="text-base md:text-lg lg:text-2xl text-slate-600 font-light">
              당신의 필요에 맞는 최적의 플랜을 찾아보세요
            </p>
          </div>

          <div className="grid lg:grid-cols-3 gap-10">
            {plans.map((plan, index) => (
              <motion.div
                key={plan.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`group relative bg-white/90 backdrop-blur-sm rounded-[2rem] p-10 transition-all duration-500 ${
                  plan.popular 
                    ? 'border-2 border-slate-900 shadow-2xl scale-105 bg-white' 
                    : plan.id === currentPlan
                    ? 'border-2 border-green-500 shadow-2xl bg-white'
                    : 'border border-slate-200/60 hover:border-slate-300/80 hover:shadow-2xl hover:scale-[1.02] hover:bg-white'
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-5 left-1/2 transform -translate-x-1/2">
                    <div className="bg-gradient-to-r from-slate-900 to-slate-700 text-white px-8 py-3 rounded-full text-sm font-semibold shadow-lg">
                      🔥 가장 인기
                    </div>
                  </div>
                )}

                <div className="text-center mb-10">
                  <h3 className="text-xl md:text-2xl lg:text-3xl font-bold text-slate-900 mb-3 md:mb-4">{plan.name}</h3>
                  <p className="text-slate-600 mb-6 md:mb-8 leading-relaxed text-sm md:text-base px-2 whitespace-pre-line">{plan.description}</p>
                  
                  <div className="mb-8">
                    {plan.originalPrice && (
                      <div className="text-sm text-slate-400 line-through mb-1 text-center">
                        {plan.originalPrice}
                      </div>
                    )}
                    <div className="text-2xl md:text-3xl lg:text-4xl font-bold text-slate-900 text-center whitespace-nowrap">
                      {plan.price}
                      {plan.price !== '무료' && (
                        <span className="text-base md:text-lg text-slate-600 ml-1">/월</span>
                      )}
                    </div>
                  </div>
                  
                  <div className="text-slate-500 mb-8 md:mb-10 text-sm md:text-base">
                    월 {plan.monthlyTokens} 토큰 포함
                  </div>
                </div>

                <div className="space-y-5 mb-10">
                  {plan.features.map((feature, idx) => (
                    <div key={idx} className="flex items-start gap-4">
                      <Check size={18} className="text-green-500 mt-1 flex-shrink-0" />
                      <span className="text-slate-700 text-sm md:text-base">{feature}</span>
                    </div>
                  ))}
                </div>

                <button
                  onClick={() => handleUpgrade(plan.id)}
                  disabled={plan.id === currentPlan}
                  className={`w-full py-4 md:py-5 px-6 md:px-8 rounded-2xl font-semibold text-base md:text-lg transition-all duration-300 ${
                    plan.id === currentPlan
                      ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                      : plan.popular
                      ? 'bg-gradient-to-r from-slate-900 to-slate-700 text-white hover:from-slate-800 hover:to-slate-600 hover:shadow-2xl transform hover:scale-[1.02]'
                      : 'bg-white border-2 border-slate-900 text-slate-900 hover:bg-slate-900 hover:text-white hover:shadow-2xl transform hover:scale-[1.02]'
                  }`}
                >
                  {plan.id === currentPlan ? '현재 플랜' : plan.ctaText}
                </button>
                
                {plan.id !== currentPlan && plan.price !== '무료' && (
                  <p className="text-xs text-slate-500 text-center mt-4">
                    카드 등록 없이 무료 체험 가능
                  </p>
                )}
              </motion.div>
            ))}
          </div>
        </div>

        {/* Social Proof */}
        <div className="mb-24">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-slate-900 mb-4">
              사용자들의 선택
            </h2>
            <p className="text-xl text-slate-600">
              이미 수많은 크리에이터들이 경험한 변화를 확인해보세요
            </p>
          </div>
          
          <div className="grid lg:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.2 }}
                className="bg-white border border-slate-200 rounded-2xl p-8 hover:border-slate-300 transition-colors"
              >
                <div className="flex items-center gap-1 mb-6">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} size={16} className="fill-yellow-400 text-yellow-400" />
                  ))}
                </div>
                
                <p className="text-slate-700 mb-6 leading-relaxed text-lg">
                  "{testimonial.comment}"
                </p>
                
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-slate-900">{testimonial.name}</div>
                    <div className="text-sm text-slate-600">{testimonial.role}</div>
                  </div>
                  <div className="text-xs bg-slate-100 text-slate-700 px-3 py-1 rounded-full font-medium">
                    {testimonial.plan}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Feature Comparison */}
        <div className="mb-24">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-slate-900 mb-4">
              플랜별 기능 비교
            </h2>
          </div>
          
          <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50/80">
                  <tr>
                    <th className="px-8 py-6 text-left text-lg font-semibold text-slate-900">기능</th>
                    <th className="px-8 py-6 text-center text-lg font-semibold text-slate-900">무료</th>
                    <th className="px-8 py-6 text-center text-lg font-semibold text-slate-900 bg-slate-100">베이직</th>
                    <th className="px-8 py-6 text-center text-lg font-semibold text-slate-900">프리미엄</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {[
                    { feature: '월간 토큰', free: '10,000개', basic: '100,000개', premium: '500,000개' },
                    { feature: 'C1 엔진 (전문적)', free: '기본', basic: '고급', premium: '전문가급' },
                    { feature: 'C2 엔진 (창의적)', free: '기본', basic: '고급', premium: '전문가급' },
                    { feature: '칼럼 작성 수', free: '5개', basic: '무제한', premium: '무제한' },
                    { feature: 'A/B 테스트', free: '✗', basic: '✓', premium: '✓' },
                    { feature: 'API 접근', free: '✗', basic: '제한적', premium: '무제한' },
                    { feature: '우선 지원', free: '커뮤니티', basic: '이메일', premium: '24시간' },
                    { feature: '팀 기능', free: '✗', basic: '✗', premium: '✓' }
                  ].map((row, index) => (
                    <tr key={index} className="hover:bg-slate-50/50">
                      <td className="px-8 py-6 font-medium text-slate-900">{row.feature}</td>
                      <td className="px-8 py-6 text-center text-slate-600">{row.free}</td>
                      <td className="px-8 py-6 text-center text-slate-600 bg-slate-50/50">{row.basic}</td>
                      <td className="px-8 py-6 text-center text-slate-600">{row.premium}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="text-center bg-gradient-to-br from-slate-900 to-slate-800 rounded-[2rem] p-8 md:p-12 lg:p-16 mb-20 shadow-2xl">
          <h2 className="text-2xl md:text-3xl lg:text-5xl font-bold text-white mb-4 md:mb-6">
            지금 시작해보세요
          </h2>
          <p className="text-base md:text-lg lg:text-xl text-slate-300 mb-8 md:mb-12 max-w-2xl mx-auto font-light">
            <span className="block md:inline">AI 칼럼 작성으로</span>
            <span className="block md:inline md:ml-1">당신의 콘텐츠를 더욱 전문적으로 만들어보세요</span>
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center max-w-lg mx-auto">
            <button
              onClick={() => handleUpgrade('basic')}
              className="bg-white text-slate-900 px-6 md:px-8 py-3 md:py-4 rounded-xl font-semibold text-sm md:text-lg hover:bg-slate-100 transition-all duration-300 transform hover:scale-105 shadow-lg"
            >
              14일 무료 체험 시작
            </button>
            <button
              onClick={() => handleUpgrade('free')}
              className="border-2 border-white/80 text-white px-6 md:px-8 py-3 md:py-4 rounded-xl font-semibold text-sm md:text-lg hover:bg-white hover:text-slate-900 transition-all duration-300 transform hover:scale-105"
            >
              무료로 시작하기
            </button>
          </div>
          <p className="text-sm text-slate-400 mt-8 opacity-80">
            카드 등록 불필요 • 언제든 취소 가능 • 즉시 사용 가능
          </p>
        </div>
      </div>
      
      {/* Bottom Spacer */}
      <div className="h-20"></div>
    </div>
  );
};

export default SubscriptionPage;