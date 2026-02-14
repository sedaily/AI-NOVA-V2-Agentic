import React, { useState, useEffect } from "react";
import { 
  Calendar, TrendingUp, Clock, Package, BarChart, Activity, 
  ChevronLeft, RefreshCw, Zap, Award, Target, Sparkles,
  TrendingDown, AlertCircle, CheckCircle, XCircle, Crown
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import clsx from "clsx";
import { motion, AnimatePresence } from "framer-motion";
import {
  LineChart, Line, AreaChart, Area, BarChart as ReBarChart, Bar,
  PieChart, Pie, Cell, RadarChart, Radar, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, ResponsiveContainer, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, RadialBarChart, RadialBar
} from "recharts";
import usageService from "../../chat/services/usageService";

// 색상 팔레트 - 다크 테마
const COLORS = {
  primary: 'hsl(251, 40.2%, 54.1%)',
  secondary: 'hsl(210, 70.9%, 51.6%)',
  accent: 'hsl(15, 63.1%, 59.6%)',
  warning: '#F59E0B',
  danger: '#EF4444',
  info: '#06B6D4',
  success: '#10B981',
  // 다크 테마 배경색
  bg100: 'hsl(60, 2.7%, 14.5%)',
  bg200: 'hsl(30, 3.3%, 11.8%)',
  bg300: 'hsl(60, 2.6%, 7.6%)',
  // 텍스트 색상
  text100: 'hsl(48, 33.3%, 97.1%)',
  text200: 'hsl(50, 9%, 73.7%)',
  text300: 'hsl(48, 4.3%, 53.3%)',
  // 보더 색상
  border: 'hsl(48, 2.9%, 26.5%)',
  // 카드 그라데이션 - 다크톤
  gradient1: 'linear-gradient(135deg, hsl(251, 40.2%, 24.1%) 0%, hsl(251, 40%, 18.1%) 100%)',
  gradient2: 'linear-gradient(135deg, hsl(210, 70.9%, 21.6%) 0%, hsl(210, 55.9%, 14.6%) 100%)',
  gradient3: 'linear-gradient(135deg, hsl(15, 63.1%, 29.6%) 0%, hsl(15, 55.6%, 22.4%) 100%)',
  gradient4: 'linear-gradient(135deg, hsl(160, 60%, 25%) 0%, hsl(160, 50%, 18%) 100%)',
};

// 애니메이션 설정
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      type: "spring",
      stiffness: 100
    }
  }
};

// 커스텀 툴팁
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-bg-300/95 backdrop-blur-sm p-3 rounded-lg shadow-xl border border-bg-300/50">
        <p className="text-sm font-semibold text-text-100">{label}</p>
        {payload.map((entry, index) => (
          <p key={index} className="text-xs text-text-200">
            {entry.name}: {entry.value.toLocaleString()}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

// 숫자 애니메이션 컴포넌트
const AnimatedNumber = ({ value, duration = 1000, prefix = "", suffix = "" }) => {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    let startTime;
    let animationFrame;

    const animate = (timestamp) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);
      
      setDisplayValue(Math.floor(progress * value));
      
      if (progress < 1) {
        animationFrame = requestAnimationFrame(animate);
      }
    };

    animationFrame = requestAnimationFrame(animate);
    
    return () => {
      if (animationFrame) {
        cancelAnimationFrame(animationFrame);
      }
    };
  }, [value, duration]);

  return <span>{prefix}{displayValue.toLocaleString()}{suffix}</span>;
};

const Dashboard = ({ selectedEngine = "T5", onBack }) => {
  const navigate = useNavigate();
  const [usageData, setUsageData] = useState(null);
  const [timeRange, setTimeRange] = useState("month");
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedMetric, setSelectedMetric] = useState("tokens");
  const [apiStatus, setApiStatus] = useState('checking'); // 'online', 'offline', 'checking'

  useEffect(() => {
    // 처음 로드시 강제 새로고침으로 최신 데이터 가져오기
    loadUsageData(true);
    
    const handleStorageChange = (e) => {
      if (e.key === 'user_usage_data') {
        loadUsageData();
      }
    };
    
    const handleUsageUpdate = () => {
      loadUsageData(true); // 사용량 업데이트시 강제 새로고침
    };
    
    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('usageUpdated', handleUsageUpdate);
    
    const interval = setInterval(() => loadUsageData(), 10000); // 10초마다 체크
    
    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('usageUpdated', handleUsageUpdate);
      clearInterval(interval);
    };
  }, []);

  const loadUsageData = async (forceRefresh = false) => {
    try {
      setApiStatus('checking');
      console.log(`📊 ${selectedEngine} 사용량 데이터 로딩 중...`);
      const data = await usageService.getAllUsageData(forceRefresh);
      console.log('✅ 사용량 데이터 로드 완료:', data);
      
      // API 연결 상태 확인
      if (data && data[selectedEngine]) {
        console.log(`✅ ${selectedEngine} 엔진 데이터 확인:`, data[selectedEngine]);
        setApiStatus('online');
      } else {
        console.warn(`⚠️ ${selectedEngine} 엔진 데이터 없음`);
        setApiStatus('online'); // 데이터는 없지만 API는 연결됨
      }
      
      setUsageData(data);
    } catch (error) {
      console.error('❌ 대시보드 사용량 데이터 로딩 실패:', error);
      setApiStatus('offline');
      // 기본 데이터 설정
      setUsageData({
        userId: getCurrentUser(),
        userPlan: 'free',
        T5: { monthlyTokensUsed: 0, inputTokens: 0, outputTokens: 0, charactersProcessed: 0 },
        C7: { monthlyTokensUsed: 0, inputTokens: 0, outputTokens: 0, charactersProcessed: 0 }
      });
    }
  };
  
  // 현재 사용자 정보 가져오기
  const getCurrentUser = () => {
    try {
      const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
      return userInfo.username || userInfo.email || 'anonymous';  // UUID 우선
    } catch {
      return 'anonymous';
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await usageService.clearUsageCache();
      await loadUsageData(true);
    } catch (error) {
      console.error('❌ 새로고침 실패:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleBack = () => {
    // "새 채팅" 버튼과 동일한 동작 - 메인 페이지로 이동
    
    // 현재 대화의 캐시 정리
    const pathParts = window.location.pathname.split('/');
    const conversationId = pathParts[pathParts.length - 1];
    
    if (conversationId && conversationId !== 'dashboard') {
      const cacheKey = `conv:${conversationId}`;
      localStorage.removeItem(cacheKey);
      console.log(`🗑️ 현재 대화 캐시 삭제: ${cacheKey}`);
    }
    
    // 임시 데이터 정리
    localStorage.removeItem('pendingMessage');
    localStorage.removeItem('pendingConversationId');
    
    // sessionStorage 정리 (모든 processed 키 제거)
    Object.keys(sessionStorage).forEach(key => {
      if (key.startsWith('processed_')) {
        sessionStorage.removeItem(key);
      }
    });
    
    console.log("🔄 대시보드에서 나가기 - 메인 페이지로 이동");
    
    // 메인 페이지로 이동 (conversationId 없이)
    const enginePath = selectedEngine === 'T5' ? '11' : '22';
    window.location.href = `/${enginePath}`;
  };

  if (!usageData) {
    return (
      <div className="flex items-center justify-center h-screen bg-bg-100">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        >
          <RefreshCw className="w-8 h-8 text-accent" />
        </motion.div>
      </div>
    );
  }

  const engineData = usageData[selectedEngine] || {
    monthlyTokensUsed: 0,
    inputTokens: 0,
    outputTokens: 0,
    charactersProcessed: 0
  };

  const planLimits = usageService.getPlanLimits(usageData.userPlan);
  const currentPlanLimits = planLimits[selectedEngine] || {
    monthlyTokens: 10000,
    monthlyCharacters: 100000,
    dailyTokens: 1000,
    dailyCharacters: 10000
  };
  
  const percentage = engineData.monthlyTokensUsed > 0 ? 
    Math.round((engineData.monthlyTokensUsed / currentPlanLimits.monthlyTokens) * 100) : 0;

  // 차트 데이터 준비
  const dailyData = [
    { name: 'Mon', tokens: 1200, characters: 5400 },
    { name: 'Tue', tokens: 2100, characters: 8300 },
    { name: 'Wed', tokens: 1800, characters: 6200 },
    { name: 'Thu', tokens: 2780, characters: 9800 },
    { name: 'Fri', tokens: 1890, characters: 7200 },
    { name: 'Sat', tokens: 2390, characters: 8600 },
    { name: 'Sun', tokens: 3490, characters: 12400 },
  ];

  const pieData = [
    { name: '입력 토큰', value: engineData.inputTokens > 0 ? engineData.inputTokens : 1 },
    { name: '출력 토큰', value: engineData.outputTokens > 0 ? engineData.outputTokens : 1 },
  ];

  const radarData = [
    { subject: '속도', A: 85, fullMark: 100 },
    { subject: '정확도', A: 92, fullMark: 100 },
    { subject: '효율성', A: 78, fullMark: 100 },
    { subject: '안정성', A: 95, fullMark: 100 },
    { subject: '응답성', A: 88, fullMark: 100 },
  ];

  const radialData = [
    { name: '사용률', value: percentage, fill: percentage > 80 ? COLORS.danger : percentage > 50 ? COLORS.warning : COLORS.success }
  ];

  return (
    <motion.div 
      className="min-h-screen bg-bg-100"
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      {/* 헤더 */}
      <motion.div 
        className="sticky top-0 z-50 bg-bg-200/80 backdrop-blur-xl border-b border-bg-300/50"
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ type: "spring", stiffness: 100 }}
      >
        <div className="px-3 sm:px-6 py-3 sm:py-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="flex items-center gap-2 sm:gap-4">
              <button
                onClick={handleBack}
                className="p-1.5 sm:p-2 hover:bg-bg-300/50 rounded-lg transition-colors text-text-100"
              >
                <ChevronLeft className="w-4 h-4 sm:w-5 sm:h-5" />
              </button>
              <div>
                <h1 className="text-lg sm:text-2xl font-bold text-text-100 whitespace-nowrap">
                  {selectedEngine} 사용량
                </h1>
                <div className="flex items-center gap-2 mt-0.5 sm:mt-1">
                  <p className="text-xs sm:text-sm text-text-300 hidden sm:block">실시간 사용량 분석</p>
                  <span className="text-text-300 hidden sm:block">•</span>
                  <div className="flex items-center gap-1">
                    <div className={clsx(
                      "w-2 h-2 rounded-full",
                      apiStatus === 'online' ? "bg-success animate-pulse" : 
                      apiStatus === 'offline' ? "bg-danger" : 
                      "bg-warning animate-pulse"
                    )} />
                    <span className="text-xs text-text-300">
                      {apiStatus === 'online' ? 'API 연결됨' : 
                       apiStatus === 'offline' ? 'API 오프라인' : 
                       'API 확인 중...'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-2 sm:gap-3">
              {/* 엔진 선택 */}
              <div className="flex gap-1 sm:gap-2 bg-bg-300/50 rounded-lg p-0.5 sm:p-1">
                {[
                  { id: 'T5', label: 'T5', fullLabel: 'T5 엔진', path: '/11/dashboard' },
                  { id: 'C7', label: 'C7', fullLabel: 'C7 엔진', path: '/22/dashboard' }
                ].map((engine) => (
                  <button
                    key={engine.id}
                    onClick={() => navigate(engine.path)}
                    className={clsx(
                      "px-2 sm:px-4 py-1 sm:py-2 rounded-md text-xs sm:text-sm font-medium transition-all whitespace-nowrap",
                      selectedEngine === engine.id
                        ? "bg-bg-100 text-accent"
                        : "text-text-300 hover:text-text-100"
                    )}
                  >
                    <span className="sm:hidden">{engine.label}</span>
                    <span className="hidden sm:inline">{engine.fullLabel}</span>
                  </button>
                ))}
              </div>
              
              {/* 구독 플랜 버튼 - 모바일에서는 아이콘만 */}
              <motion.button
                onClick={() => navigate('/subscription')}
                className="flex items-center gap-1 sm:gap-2 px-2 sm:px-4 py-1.5 sm:py-2 bg-gradient-to-r from-warning/20 to-warning/10 text-warning rounded-lg hover:from-warning/30 hover:to-warning/20 transition-all"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Crown className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                <span className="text-xs sm:text-sm font-medium hidden sm:inline">플랜 업그레이드</span>
              </motion.button>
              
              <motion.button
                onClick={handleRefresh}
                className="p-1.5 sm:p-2 bg-accent/20 text-accent rounded-lg hover:bg-accent/30 transition-colors"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                animate={isRefreshing ? { rotate: 360 } : {}}
                transition={isRefreshing ? { duration: 1, repeat: Infinity, ease: "linear" } : {}}
              >
                <RefreshCw className="w-4 h-4 sm:w-5 sm:h-5" />
              </motion.button>
            </div>
          </div>
        </div>
      </motion.div>

      {/* 메인 콘텐츠 */}
      <div className="p-3 sm:p-6 max-w-7xl mx-auto">
        {/* 주요 지표 카드들 */}
        <motion.div 
          className="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6 mb-6 sm:mb-8"
          variants={containerVariants}
        >
          {/* 총 사용량 */}
          <motion.div
            variants={itemVariants}
            className="relative overflow-hidden bg-bg-200 border border-bg-300/50 rounded-xl sm:rounded-2xl p-3 sm:p-6 shadow-xl col-span-2 md:col-span-1"
            whileHover={{ scale: 1.02 }}
          >
            <div className="absolute top-0 right-0 -mt-4 -mr-4 w-16 sm:w-24 h-16 sm:h-24 bg-accent/5 rounded-full blur-xl" />
            <div className="relative">
              <div className="flex items-center justify-between mb-2 sm:mb-4">
                <div className="p-2 sm:p-3 bg-accent/10 rounded-lg backdrop-blur-sm">
                  <Zap className="w-4 h-4 sm:w-6 sm:h-6 text-accent" />
                </div>
                <span className="text-xs bg-bg-300/50 px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full text-text-200">
                  {percentage > 80 ? '높음' : percentage > 50 ? '보통' : '양호'}
                </span>
              </div>
              <p className="text-xs sm:text-sm text-text-200 mb-0.5 sm:mb-1">월간 토큰 사용량</p>
              <p className="text-xl sm:text-3xl font-bold text-text-100">
                <AnimatedNumber 
                  value={engineData.monthlyTokensUsed || 0} 
                  suffix=" 토큰"
                />
              </p>
              <div className="mt-2 sm:mt-4">
                <div className="flex justify-between text-xs mb-0.5 sm:mb-1 text-text-300">
                  <span>사용률</span>
                  <span>{percentage}%</span>
                </div>
                <div className="w-full bg-bg-300/50 rounded-full h-1.5 sm:h-2">
                  <motion.div 
                    className="bg-accent rounded-full h-1.5 sm:h-2"
                    initial={{ width: 0 }}
                    animate={{ width: `${percentage}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                  />
                </div>
              </div>
            </div>
          </motion.div>

          {/* 입력/출력 비율 */}
          <motion.div
            variants={itemVariants}
            className="relative overflow-hidden bg-bg-200 border border-bg-300/50 rounded-xl sm:rounded-2xl p-3 sm:p-6 shadow-xl"
            whileHover={{ scale: 1.02 }}
          >
            <div className="absolute top-0 right-0 -mt-4 -mr-4 w-16 sm:w-24 h-16 sm:h-24 bg-primary/5 rounded-full blur-xl" />
            <div className="relative">
              <div className="flex items-center justify-between mb-2 sm:mb-4">
                <div className="p-2 sm:p-3 bg-primary/10 rounded-lg backdrop-blur-sm">
                  <Activity className="w-4 h-4 sm:w-6 sm:h-6 text-primary" />
                </div>
                <span className="text-xs bg-bg-300/50 px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full text-text-200">실시간</span>
              </div>
              <p className="text-xs sm:text-sm text-text-200 mb-0.5 sm:mb-1">입출력 비율</p>
              <div className="flex items-baseline gap-1 sm:gap-2">
                <p className="text-sm sm:text-2xl font-bold text-text-100">
                  {(engineData.inputTokens || 0).toLocaleString()}
                </p>
                <span className="text-xs sm:text-sm text-text-300">/</span>
                <p className="text-sm sm:text-2xl font-bold text-text-100">
                  {(engineData.outputTokens || 0).toLocaleString()}
                </p>
              </div>
              <div className="mt-4 flex gap-2">
                <div className="flex-1">
                  <p className="text-xs text-text-300">입력</p>
                  <div className="w-full bg-bg-300/50 rounded-full h-1 mt-1">
                    <div 
                      className="bg-primary rounded-full h-1"
                      style={{ width: `${(engineData.inputTokens / (engineData.inputTokens + engineData.outputTokens)) * 100 || 50}%` }}
                    />
                  </div>
                </div>
                <div className="flex-1">
                  <p className="text-xs text-text-300">출력</p>
                  <div className="w-full bg-bg-300/50 rounded-full h-1 mt-1">
                    <div 
                      className="bg-secondary rounded-full h-1"
                      style={{ width: `${(engineData.outputTokens / (engineData.inputTokens + engineData.outputTokens)) * 100 || 50}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          </motion.div>

          {/* 일일 한도 */}
          <motion.div
            variants={itemVariants}
            className="relative overflow-hidden bg-bg-200 border border-bg-300/50 rounded-xl sm:rounded-2xl p-3 sm:p-6 shadow-xl"
            whileHover={{ scale: 1.02 }}
          >
            <div className="absolute top-0 right-0 -mt-4 -mr-4 w-16 sm:w-24 h-16 sm:h-24 bg-success/5 rounded-full blur-xl" />
            <div className="relative">
              <div className="flex items-center justify-between mb-2 sm:mb-4">
                <div className="p-2 sm:p-3 bg-success/10 rounded-lg backdrop-blur-sm">
                  <Target className="w-4 h-4 sm:w-6 sm:h-6 text-success" />
                </div>
                <span className="text-xs bg-bg-300/50 px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full text-text-200">오늘</span>
              </div>
              <p className="text-xs sm:text-sm text-text-200 mb-0.5 sm:mb-1">일일 한도</p>
              <p className="text-xl sm:text-3xl font-bold text-text-100">
                {currentPlanLimits.dailyTokens?.toLocaleString() || "1,000"}
              </p>
              <div className="mt-2 sm:mt-4 flex items-center gap-1 sm:gap-2">
                <CheckCircle className="w-3 h-3 sm:w-4 sm:h-4 text-success" />
                <span className="text-xs text-text-300">정상 운영 중</span>
              </div>
            </div>
          </motion.div>

          {/* 효율성 점수 */}
          <motion.div
            variants={itemVariants}
            className="relative overflow-hidden bg-bg-200 border border-bg-300/50 rounded-xl sm:rounded-2xl p-3 sm:p-6 shadow-xl"
            whileHover={{ scale: 1.02 }}
          >
            <div className="absolute top-0 right-0 -mt-4 -mr-4 w-16 sm:w-24 h-16 sm:h-24 bg-warning/5 rounded-full blur-xl" />
            <div className="relative">
              <div className="flex items-center justify-between mb-2 sm:mb-4">
                <div className="p-2 sm:p-3 bg-warning/10 rounded-lg backdrop-blur-sm">
                  <Award className="w-4 h-4 sm:w-6 sm:h-6 text-warning" />
                </div>
                <span className="text-xs bg-bg-300/50 px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full text-text-200">AI 분석</span>
              </div>
              <p className="text-xs sm:text-sm text-text-200 mb-0.5 sm:mb-1">효율성 점수</p>
              <div className="flex items-baseline gap-1 sm:gap-2">
                <p className="text-xl sm:text-3xl font-bold text-text-100">92</p>
                <span className="text-xs sm:text-sm text-text-300">/ 100</span>
              </div>
              <div className="mt-2 sm:mt-4">
                <div className="flex gap-0.5 sm:gap-1">
                  {[...Array(5)].map((_, i) => (
                    <div
                      key={i}
                      className={clsx(
                        "h-0.5 sm:h-1 flex-1 rounded-full",
                        i < 4 ? "bg-warning" : "bg-bg-300/50"
                      )}
                    />
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>

        {/* 차트 섹션 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-6 mb-6 sm:mb-8">
          {/* 일주일 사용 트렌드 */}
          <motion.div
            variants={itemVariants}
            className="bg-bg-200 rounded-xl sm:rounded-2xl shadow-lg p-3 sm:p-6 border border-bg-300/50"
          >
            <div className="flex items-center justify-between mb-3 sm:mb-6">
              <h3 className="text-sm sm:text-lg font-semibold text-text-100">주간 사용 트렌드</h3>
              <div className="flex gap-1 sm:gap-2">
                <button 
                  onClick={() => setSelectedMetric('tokens')}
                  className={clsx(
                    "px-2 sm:px-3 py-0.5 sm:py-1 text-xs sm:text-sm rounded-lg transition-colors",
                    selectedMetric === 'tokens' 
                      ? "bg-accent/20 text-accent" 
                      : "text-text-300 hover:bg-bg-300/50"
                  )}
                >
                  토큰
                </button>
                <button 
                  onClick={() => setSelectedMetric('characters')}
                  className={clsx(
                    "px-2 sm:px-3 py-0.5 sm:py-1 text-xs sm:text-sm rounded-lg transition-colors",
                    selectedMetric === 'characters' 
                      ? "bg-accent/20 text-accent" 
                      : "text-text-300 hover:bg-bg-300/50"
                  )}
                >
                  문자
                </button>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={180}>
              <AreaChart data={dailyData}>
                <defs>
                  <linearGradient id="colorTokens" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={COLORS.primary} stopOpacity={0.3}/>
                    <stop offset="95%" stopColor={COLORS.primary} stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} opacity={0.2} />
                <XAxis 
                  dataKey="name" 
                  stroke={COLORS.text300}
                  tick={{ fontSize: 12, fill: COLORS.text300 }}
                />
                <YAxis 
                  stroke={COLORS.text300}
                  tick={{ fontSize: 12, fill: COLORS.text300 }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Area
                  type="monotone"
                  dataKey={selectedMetric}
                  stroke={COLORS.primary}
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorTokens)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </motion.div>

          {/* 입출력 비율 파이차트 */}
          <motion.div
            variants={itemVariants}
            className="bg-bg-200 rounded-2xl shadow-lg p-6 border border-bg-300/50"
          >
            <h3 className="text-lg font-semibold text-text-100 mb-6">토큰 사용 분포</h3>
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={index === 0 ? COLORS.primary : COLORS.secondary} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </motion.div>
        </div>

        {/* 성능 지표 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 레이더 차트 */}
          <motion.div
            variants={itemVariants}
            className="bg-bg-200 rounded-2xl shadow-lg p-6 border border-bg-300/50"
          >
            <h3 className="text-lg font-semibold text-text-100 mb-6">성능 지표</h3>
            <ResponsiveContainer width="100%" height={180}>
              <RadarChart data={radarData}>
                <PolarGrid stroke={COLORS.border} opacity={0.2} />
                <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12, fill: COLORS.text300 }} />
                <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10, fill: COLORS.text300 }} />
                <Radar name="성능" dataKey="A" stroke={COLORS.secondary} fill={COLORS.secondary} fillOpacity={0.6} />
              </RadarChart>
            </ResponsiveContainer>
          </motion.div>

          {/* 사용률 게이지 */}
          <motion.div
            variants={itemVariants}
            className="bg-bg-200 rounded-2xl shadow-lg p-6 border border-bg-300/50"
          >
            <h3 className="text-lg font-semibold text-text-100 mb-6">월간 사용률</h3>
            <ResponsiveContainer width="100%" height={180}>
              <RadialBarChart cx="50%" cy="50%" innerRadius="40%" outerRadius="100%" data={radialData}>
                <RadialBar
                  dataKey="value"
                  cornerRadius={10}
                  fill={percentage > 80 ? COLORS.danger : percentage > 50 ? COLORS.warning : COLORS.success}
                  background
                />
                <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle" className="text-3xl font-bold" fill={COLORS.text100}>
                  {percentage}%
                </text>
              </RadialBarChart>
            </ResponsiveContainer>
          </motion.div>

          {/* 빠른 통계 */}
          <motion.div
            variants={itemVariants}
            className="bg-bg-200 border border-bg-300/50 rounded-2xl p-6 space-y-4"
          >
            <h3 className="text-lg font-semibold text-text-100 mb-4">빠른 통계</h3>
            
            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-bg-300/30 rounded-lg">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-success rounded-full animate-pulse" />
                  <span className="text-sm text-text-200">평균 응답 시간</span>
                </div>
                <span className="text-sm font-semibold text-text-100">1.2초</span>
              </div>
              
              <div className="flex justify-between items-center p-3 bg-bg-300/30 rounded-lg">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-primary rounded-full animate-pulse" />
                  <span className="text-sm text-text-200">오늘 세션</span>
                </div>
                <span className="text-sm font-semibold text-text-100">12회</span>
              </div>
              
              <div className="flex justify-between items-center p-3 bg-bg-300/30 rounded-lg">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-secondary rounded-full animate-pulse" />
                  <span className="text-sm text-text-200">평균 토큰/세션</span>
                </div>
                <span className="text-sm font-semibold text-text-100">847</span>
              </div>
              
              <div className="flex justify-between items-center p-3 bg-bg-300/30 rounded-lg">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-warning rounded-full animate-pulse" />
                  <span className="text-sm text-text-200">예상 잔여일</span>
                </div>
                <span className="text-sm font-semibold text-text-100">18일</span>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
};

export default Dashboard;