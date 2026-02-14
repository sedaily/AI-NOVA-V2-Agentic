import { useState, useEffect } from 'react';
import usageService from '../../chat/services/usageService';

export const useDashboard = (userRole) => {
  // 상태 관리
  const [selectedPeriod, setSelectedPeriod] = useState("day");
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [usageData, setUsageData] = useState({
    T5: { percentage: 0, used: 0, limit: 0, cost: 0 },
    C7: { percentage: 0, used: 0, limit: 0, cost: 0 },
    totalCost: 0,
    dailyLimit: 100,
    monthlyLimit: 3000
  });
  const [chartData, setChartData] = useState({
    daily: [],
    weekly: [],
    monthly: [],
    engineComparison: [],
    costTrend: [],
    hourlyDistribution: [],
    successRate: []
  });

  // Mock 데이터 생성
  const generateMockData = () => {
    // 일별 데이터
    const daily = Array.from({ length: 24 }, (_, i) => ({
      name: `${i}시`,
      T5: Math.floor(Math.random() * 100) + 20,
      C7: Math.floor(Math.random() * 80) + 10,
      cost: Math.floor(Math.random() * 50) + 10
    }));

    // 주별 데이터
    const weekly = ['월', '화', '수', '목', '금', '토', '일'].map(day => ({
      name: day,
      T5: Math.floor(Math.random() * 500) + 100,
      C7: Math.floor(Math.random() * 400) + 80,
      cost: Math.floor(Math.random() * 200) + 50
    }));

    // 월별 데이터
    const monthly = Array.from({ length: 30 }, (_, i) => ({
      name: `${i + 1}일`,
      T5: Math.floor(Math.random() * 200) + 50,
      C7: Math.floor(Math.random() * 150) + 40,
      cost: Math.floor(Math.random() * 100) + 20
    }));

    // 엔진 비교 데이터
    const engineComparison = [
      { name: 'T5', value: 65, fill: 'hsl(251, 40.2%, 54.1%)' },
      { name: 'C7', value: 35, fill: 'hsl(210, 70.9%, 51.6%)' }
    ];

    // 비용 트렌드
    const costTrend = Array.from({ length: 12 }, (_, i) => ({
      name: `${i + 1}월`,
      cost: Math.floor(Math.random() * 1000) + 500,
      budget: 1500
    }));

    // 시간대별 사용 분포
    const hourlyDistribution = [
      { hour: '00-06', usage: 20 },
      { hour: '06-12', usage: 45 },
      { hour: '12-18', usage: 80 },
      { hour: '18-24', usage: 35 }
    ];

    // 성공률 데이터
    const successRate = [
      { subject: '속도', T5: 95, C7: 80, fullMark: 100 },
      { subject: '정확도', T5: 88, C7: 92, fullMark: 100 },
      { subject: '창의성', T5: 75, C7: 90, fullMark: 100 },
      { subject: '안정성', T5: 92, C7: 85, fullMark: 100 },
      { subject: '비용효율', T5: 90, C7: 70, fullMark: 100 }
    ];

    setChartData({
      daily,
      weekly,
      monthly,
      engineComparison,
      costTrend,
      hourlyDistribution,
      successRate
    });
  };

  // 사용량 데이터 로드
  const loadUsageData = async () => {
    try {
      const t5Usage = await usageService.getUsagePercentage('T5');
      const c7Usage = await usageService.getUsagePercentage('C7');
      
      setUsageData({
        T5: {
          percentage: t5Usage || 0,
          used: Math.floor((t5Usage || 0) * 30),
          limit: 3000,
          cost: Math.floor((t5Usage || 0) * 5)
        },
        C7: {
          percentage: c7Usage || 0,
          used: Math.floor((c7Usage || 0) * 20),
          limit: 2000,
          cost: Math.floor((c7Usage || 0) * 8)
        },
        totalCost: Math.floor((t5Usage || 0) * 5) + Math.floor((c7Usage || 0) * 8),
        dailyLimit: 100,
        monthlyLimit: 3000
      });
    } catch (error) {
      console.error('사용량 데이터 로드 실패:', error);
    }
  };

  // 데이터 새로고침
  const refreshData = async () => {
    setIsRefreshing(true);
    
    try {
      await Promise.all([
        usageService.fetchUsageFromServer('T5'),
        usageService.fetchUsageFromServer('C7')
      ]);
      
      await loadUsageData();
      generateMockData();
    } catch (error) {
      console.error('데이터 새로고침 실패:', error);
    } finally {
      setTimeout(() => {
        setIsRefreshing(false);
      }, 1000);
    }
  };

  // 초기 데이터 로드
  useEffect(() => {
    loadUsageData();
    generateMockData();
    
    // 자동 새로고침 (30초마다)
    const interval = setInterval(loadUsageData, 30000);
    return () => clearInterval(interval);
  }, []);

  // 통계 데이터 계산
  const getStatistics = () => {
    const totalUsage = usageData.T5.used + usageData.C7.used;
    const avgRequestTime = 1.2;
    const successRate = 98.5;
    const activeUsers = userRole === 'admin' ? 127 : 1;

    return {
      totalUsage,
      avgRequestTime,
      successRate,
      activeUsers
    };
  };

  // 기간별 차트 데이터 반환
  const getChartDataByPeriod = () => {
    switch (selectedPeriod) {
      case 'day':
        return chartData.daily;
      case 'week':
        return chartData.weekly;
      case 'month':
        return chartData.monthly;
      default:
        return chartData.daily;
    }
  };

  return {
    // State
    selectedPeriod,
    isRefreshing,
    usageData,
    chartData,
    
    // Actions
    setSelectedPeriod,
    refreshData,
    
    // Computed
    statistics: getStatistics(),
    currentChartData: getChartDataByPeriod()
  };
};