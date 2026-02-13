import React from 'react';
import {
  Calendar, TrendingUp, Clock, Package, BarChart, Activity,
  ChevronLeft, RefreshCw, Zap, Award, Target, Sparkles,
  TrendingDown, AlertCircle, CheckCircle, Crown
} from "lucide-react";
import clsx from "clsx";
import { motion, AnimatePresence } from "framer-motion";
import {
  LineChart, Line, AreaChart, Area, BarChart as ReBarChart, Bar,
  PieChart, Pie, Cell, RadarChart, Radar, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, ResponsiveContainer, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, RadialBarChart, RadialBar
} from "recharts";

// 애니메이션 설정
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: { type: "spring", stiffness: 100 }
  }
};

const DashboardPresenter = ({
  userRole,
  selectedPeriod,
  isRefreshing,
  usageData,
  chartData,
  statistics,
  currentChartData,
  onPeriodChange,
  onRefresh,
  onBackToLanding,
  onLogout
}) => {
  return (
    <div className="min-h-screen" style={{ backgroundColor: 'hsl(30, 3.3%, 11.8%)' }}>
      {/* Header */}
      <DashboardHeader
        userRole={userRole}
        isRefreshing={isRefreshing}
        onRefresh={onRefresh}
        onBackToLanding={onBackToLanding}
      />

      {/* Main Content */}
      <motion.main
        className="container mx-auto px-6 py-8"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Stats Cards */}
        <StatsSection statistics={statistics} userRole={userRole} />

        {/* Period Selector */}
        <PeriodSelector
          selectedPeriod={selectedPeriod}
          onPeriodChange={onPeriodChange}
        />

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <UsageChartCard
            data={currentChartData}
            period={selectedPeriod}
          />
          <EngineComparisonCard data={chartData.engineComparison} />
          <CostTrendCard data={chartData.costTrend} />
          <PerformanceRadarCard data={chartData.successRate} />
        </div>

        {/* Usage Overview */}
        <UsageOverviewSection usageData={usageData} />
      </motion.main>
    </div>
  );
};

// Header Component
const DashboardHeader = ({ userRole, isRefreshing, onRefresh, onBackToLanding }) => (
  <header className="border-b" style={{ borderColor: 'hsl(48, 2.9%, 26.5%)/0.3' }}>
    <div className="container mx-auto px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={onBackToLanding}
            className="p-2 rounded-lg hover:bg-bg-300/50 transition-colors"
          >
            <ChevronLeft size={20} style={{ color: 'hsl(48, 33.3%, 97.1%)' }} />
          </button>
          <h1 className="text-2xl font-bold" style={{ color: 'hsl(48, 33.3%, 97.1%)' }}>
            대시보드
          </h1>
          {userRole === 'admin' && (
            <span className="px-2 py-1 rounded-full text-xs font-medium bg-gradient-to-r from-yellow-500 to-amber-500 text-white flex items-center gap-1">
              <Crown size={12} />
              Admin
            </span>
          )}
        </div>
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className={clsx(
            "p-2 rounded-lg transition-all",
            isRefreshing ? "opacity-50 cursor-not-allowed" : "hover:bg-bg-300/50"
          )}
        >
          <RefreshCw
            size={20}
            className={isRefreshing ? "animate-spin" : ""}
            style={{ color: 'hsl(48, 33.3%, 97.1%)' }}
          />
        </button>
      </div>
    </div>
  </header>
);

// Stats Section
const StatsSection = ({ statistics, userRole }) => (
  <motion.div
    className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
    variants={containerVariants}
  >
    <StatCard
      icon={Activity}
      title="전체 사용량"
      value={statistics.totalUsage}
      suffix=" 요청"
      gradient="linear-gradient(135deg, hsl(251, 40.2%, 24.1%) 0%, hsl(251, 40%, 18.1%) 100%)"
    />
    <StatCard
      icon={Clock}
      title="평균 응답시간"
      value={statistics.avgRequestTime}
      suffix="초"
      gradient="linear-gradient(135deg, hsl(210, 70.9%, 21.6%) 0%, hsl(210, 55.9%, 14.6%) 100%)"
    />
    <StatCard
      icon={CheckCircle}
      title="성공률"
      value={statistics.successRate}
      suffix="%"
      gradient="linear-gradient(135deg, hsl(160, 60%, 25%) 0%, hsl(160, 50%, 18%) 100%)"
    />
    {userRole === 'admin' ? (
      <StatCard
        icon={Sparkles}
        title="활성 사용자"
        value={statistics.activeUsers}
        suffix="명"
        gradient="linear-gradient(135deg, hsl(15, 63.1%, 29.6%) 0%, hsl(15, 55.6%, 22.4%) 100%)"
      />
    ) : (
      <StatCard
        icon={Award}
        title="사용 가능"
        value={100 - Math.floor((statistics.totalUsage / 3000) * 100)}
        suffix="%"
        gradient="linear-gradient(135deg, hsl(15, 63.1%, 29.6%) 0%, hsl(15, 55.6%, 22.4%) 100%)"
      />
    )}
  </motion.div>
);

// Stat Card Component
const StatCard = ({ icon: Icon, title, value, suffix, gradient }) => (
  <motion.div
    variants={itemVariants}
    className="relative p-6 rounded-2xl shadow-xl overflow-hidden"
    style={{ background: gradient }}
  >
    <div className="absolute top-0 right-0 w-32 h-32 rounded-full opacity-10"
         style={{ background: 'white', transform: 'translate(30%, -30%)' }} />
    <div className="relative">
      <div className="flex items-center justify-between mb-3">
        <Icon size={24} className="text-white/80" />
        <TrendingUp size={16} className="text-green-400" />
      </div>
      <p className="text-sm text-white/70">{title}</p>
      <p className="text-2xl font-bold text-white">
        <AnimatedNumber value={value} suffix={suffix} />
      </p>
    </div>
  </motion.div>
);

// Period Selector
const PeriodSelector = ({ selectedPeriod, onPeriodChange }) => (
  <div className="flex items-center space-x-2 mb-6">
    {[
      { value: 'day', label: '일간' },
      { value: 'week', label: '주간' },
      { value: 'month', label: '월간' }
    ].map((period) => (
      <button
        key={period.value}
        onClick={() => onPeriodChange(period.value)}
        className={clsx(
          "px-4 py-2 rounded-lg text-sm font-medium transition-all",
          selectedPeriod === period.value
            ? "bg-accent-main-000 text-white shadow-lg"
            : "bg-bg-300/50 text-text-200 hover:bg-bg-300"
        )}
      >
        {period.label}
      </button>
    ))}
  </div>
);

// Usage Chart Card
const UsageChartCard = ({ data, period }) => (
  <motion.div
    variants={itemVariants}
    className="p-6 rounded-2xl shadow-xl"
    style={{ backgroundColor: 'hsl(60, 2.6%, 7.6%)' }}
  >
    <h3 className="text-lg font-semibold mb-4" style={{ color: 'hsl(48, 33.3%, 97.1%)' }}>
      엔진별 사용 추이
    </h3>
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id="colorEngine11" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="hsl(251, 40.2%, 54.1%)" stopOpacity={0.3}/>
            <stop offset="95%" stopColor="hsl(251, 40.2%, 54.1%)" stopOpacity={0}/>
          </linearGradient>
          <linearGradient id="colorEngine22" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="hsl(210, 70.9%, 51.6%)" stopOpacity={0.3}/>
            <stop offset="95%" stopColor="hsl(210, 70.9%, 51.6%)" stopOpacity={0}/>
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(48, 2.9%, 26.5%)" opacity={0.2} />
        <XAxis dataKey="name" stroke="hsl(50, 9%, 73.7%)" fontSize={12} />
        <YAxis stroke="hsl(50, 9%, 73.7%)" fontSize={12} />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        <Area type="monotone" dataKey="11" stroke="hsl(251, 40.2%, 54.1%)" fillOpacity={1} fill="url(#colorEngine11)" strokeWidth={2} />
        <Area type="monotone" dataKey="22" stroke="hsl(210, 70.9%, 51.6%)" fillOpacity={1} fill="url(#colorEngine22)" strokeWidth={2} />
      </AreaChart>
    </ResponsiveContainer>
  </motion.div>
);

// Engine Comparison Card
const EngineComparisonCard = ({ data }) => (
  <motion.div
    variants={itemVariants}
    className="p-6 rounded-2xl shadow-xl"
    style={{ backgroundColor: 'hsl(60, 2.6%, 7.6%)' }}
  >
    <h3 className="text-lg font-semibold mb-4" style={{ color: 'hsl(48, 33.3%, 97.1%)' }}>
      엔진 사용 비율
    </h3>
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={100}
          paddingAngle={5}
          dataKey="value"
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.fill} />
          ))}
        </Pie>
        <Tooltip />
      </PieChart>
    </ResponsiveContainer>
    <div className="flex justify-center space-x-6 mt-4">
      {data.map((item) => (
        <div key={item.name} className="flex items-center space-x-2">
          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.fill }} />
          <span className="text-sm" style={{ color: 'hsl(50, 9%, 73.7%)' }}>
            {item.name}: {item.value}%
          </span>
        </div>
      ))}
    </div>
  </motion.div>
);

// Cost Trend Card
const CostTrendCard = ({ data }) => (
  <motion.div
    variants={itemVariants}
    className="p-6 rounded-2xl shadow-xl"
    style={{ backgroundColor: 'hsl(60, 2.6%, 7.6%)' }}
  >
    <h3 className="text-lg font-semibold mb-4" style={{ color: 'hsl(48, 33.3%, 97.1%)' }}>
      비용 트렌드
    </h3>
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(48, 2.9%, 26.5%)" opacity={0.2} />
        <XAxis dataKey="name" stroke="hsl(50, 9%, 73.7%)" fontSize={12} />
        <YAxis stroke="hsl(50, 9%, 73.7%)" fontSize={12} />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        <Line type="monotone" dataKey="cost" stroke="hsl(15, 63.1%, 59.6%)" strokeWidth={2} dot={{ fill: 'hsl(15, 63.1%, 59.6%)' }} />
        <Line type="monotone" dataKey="budget" stroke="#10B981" strokeWidth={2} strokeDasharray="5 5" dot={false} />
      </LineChart>
    </ResponsiveContainer>
  </motion.div>
);

// Performance Radar Card
const PerformanceRadarCard = ({ data }) => (
  <motion.div
    variants={itemVariants}
    className="p-6 rounded-2xl shadow-xl"
    style={{ backgroundColor: 'hsl(60, 2.6%, 7.6%)' }}
  >
    <h3 className="text-lg font-semibold mb-4" style={{ color: 'hsl(48, 33.3%, 97.1%)' }}>
      성능 비교
    </h3>
    <ResponsiveContainer width="100%" height={300}>
      <RadarChart data={data}>
        <PolarGrid stroke="hsl(48, 2.9%, 26.5%)" />
        <PolarAngleAxis dataKey="subject" stroke="hsl(50, 9%, 73.7%)" fontSize={12} />
        <PolarRadiusAxis angle={90} domain={[0, 100]} stroke="hsl(50, 9%, 73.7%)" fontSize={10} />
        <Radar name="11" dataKey="11" stroke="hsl(251, 40.2%, 54.1%)" fill="hsl(251, 40.2%, 54.1%)" fillOpacity={0.3} strokeWidth={2} />
        <Radar name="22" dataKey="22" stroke="hsl(210, 70.9%, 51.6%)" fill="hsl(210, 70.9%, 51.6%)" fillOpacity={0.3} strokeWidth={2} />
        <Legend />
      </RadarChart>
    </ResponsiveContainer>
  </motion.div>
);

// Usage Overview Section
const UsageOverviewSection = ({ usageData }) => (
  <motion.div
    variants={itemVariants}
    className="grid grid-cols-1 md:grid-cols-2 gap-6"
  >
    <EngineUsageCard engine="11" data={usageData[11]} color="hsl(251, 40.2%, 54.1%)" />
    <EngineUsageCard engine="22" data={usageData[22]} color="hsl(210, 70.9%, 51.6%)" />
  </motion.div>
);

// Engine Usage Card
const EngineUsageCard = ({ engine, data, color }) => (
  <div className="p-6 rounded-2xl" style={{ backgroundColor: 'hsl(60, 2.6%, 7.6%)' }}>
    <div className="flex items-center justify-between mb-4">
      <h3 className="text-lg font-semibold" style={{ color: 'hsl(48, 33.3%, 97.1%)' }}>
        {engine} 엔진
      </h3>
      <Zap size={20} style={{ color }} />
    </div>
    <div className="space-y-3">
      <div>
        <div className="flex justify-between text-sm mb-1">
          <span style={{ color: 'hsl(50, 9%, 73.7%)' }}>사용량</span>
          <span style={{ color: 'hsl(48, 33.3%, 97.1%)' }}>{data.used} / {data.limit}</span>
        </div>
        <div className="w-full bg-bg-200 rounded-full h-2">
          <div
            className="h-2 rounded-full transition-all duration-500"
            style={{
              width: `${data.percentage}%`,
              backgroundColor: color
            }}
          />
        </div>
      </div>
      <div className="flex justify-between">
        <span className="text-sm" style={{ color: 'hsl(50, 9%, 73.7%)' }}>예상 비용</span>
        <span className="font-semibold" style={{ color: 'hsl(48, 33.3%, 97.1%)' }}>
          ${data.cost}
        </span>
      </div>
    </div>
  </div>
);

// Custom Tooltip
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

// Animated Number Component
const AnimatedNumber = ({ value, suffix = "" }) => {
  const [displayValue, setDisplayValue] = React.useState(0);

  React.useEffect(() => {
    let startTime;
    let animationFrame;

    const animate = (timestamp) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / 1000, 1);
      
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
  }, [value]);

  return <>{displayValue}{suffix}</>;
};

export default DashboardPresenter;