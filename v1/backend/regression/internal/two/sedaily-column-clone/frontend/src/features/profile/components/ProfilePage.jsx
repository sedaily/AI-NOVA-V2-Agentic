import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Calendar, CreditCard, AlertCircle, ArrowLeft, Shield, Mail, Building } from 'lucide-react';
import Header from '../../../shared/components/layout/Header';

const ProfilePage = () => {
  const navigate = useNavigate();
  const [userInfo, setUserInfo] = useState(null);
  const [subscriptionInfo, setSubscriptionInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedEngine, setSelectedEngine] = useState('11');

  useEffect(() => {
    // localStorage에서 사용자 정보 가져오기
    const storedUserInfo = localStorage.getItem('userInfo');
    const storedUserRole = localStorage.getItem('userRole');
    const storedEngine = localStorage.getItem('selectedEngine') || '11';
    
    if (storedUserInfo) {
      const parsedInfo = JSON.parse(storedUserInfo);
      setUserInfo(parsedInfo);
      setSelectedEngine(storedEngine);
      
      // 관리자는 ENTERPRISE 플랜
      const isAdmin = storedUserRole === 'admin';
      
      // 구독 정보 설정
      setSubscriptionInfo({
        plan: isAdmin ? 'ENTERPRISE' : (parsedInfo.subscriptionPlan || 'PREMIUM'),
        status: parsedInfo.subscriptionStatus || 'ACTIVE',
        startDate: parsedInfo.createdAt || '2025-01-01',
        endDate: parsedInfo.subscriptionEndDate || null,
        nextBillingDate: parsedInfo.nextBillingDate || '2025-02-01',
        cancelDate: parsedInfo.cancelDate || null
      });
    }
    setLoading(false);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userInfo');
    navigate('/');
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  };

  const getPlanDisplayName = (plan) => {
    const planNames = {
      'BASIC': '베이직',
      'STANDARD': '스탠다드',
      'PREMIUM': '프리미엄',
      'ENTERPRISE': '엔터프라이즈'
    };
    return planNames[plan] || plan;
  };

  const getStatusColor = (status) => {
    switch(status) {
      case 'ACTIVE': return 'text-green-400';
      case 'CANCELLED': return 'text-red-400';
      case 'EXPIRED': return 'text-gray-400';
      default: return 'text-yellow-400';
    }
  };

  const getStatusDisplayName = (status) => {
    const statusNames = {
      'ACTIVE': '활성',
      'CANCELLED': '해지',
      'EXPIRED': '만료',
      'PENDING': '대기중'
    };
    return statusNames[status] || status;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-bg-50 flex items-center justify-center">
        <div className="text-text-200">로딩중...</div>
      </div>
    );
  }

  if (!userInfo) {
    navigate('/login');
    return null;
  }

  return (
    <div className="min-h-screen bg-bg-50">
      <Header
        onLogout={handleLogout}
        onHome={() => navigate('/')}
      />
      
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 mt-16">
        {/* 페이지 헤더 */}
        <div className="mb-8">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center text-text-200 hover:text-text-100 transition-colors mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            뒤로가기
          </button>
          <h1 className="text-3xl font-bold text-text-100">프로필</h1>
          <p className="text-text-200 mt-2">계정 정보 및 구독 상태를 확인하세요</p>
        </div>

        {/* 계정 정보 섹션 */}
        <div className="bg-bg-100 rounded-xl border border-bg-300 p-6 mb-6">
          <div className="flex items-center mb-6">
            <div className="w-12 h-12 bg-gradient-to-br from-accent-main-100 to-purple-500 rounded-full flex items-center justify-center">
              <User className="w-6 h-6 text-white" />
            </div>
            <div className="ml-4">
              <h2 className="text-xl font-semibold text-text-100">계정 정보</h2>
              <p className="text-sm text-text-200">기본 계정 정보입니다</p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="text-xs text-text-300 uppercase tracking-wider mb-1 block">이메일</label>
              <div className="flex items-center text-text-100">
                <Mail className="w-4 h-4 mr-2 text-text-300" />
                {userInfo.email || userInfo.userId}
              </div>
            </div>
            
            <div>
              <label className="text-xs text-text-300 uppercase tracking-wider mb-1 block">사용자 ID</label>
              <div className="flex items-center text-text-100">
                <Shield className="w-4 h-4 mr-2 text-text-300" />
                {userInfo.username || userInfo.userId}
              </div>
            </div>
            
            <div>
              <label className="text-xs text-text-300 uppercase tracking-wider mb-1 block">가입일</label>
              <div className="flex items-center text-text-100">
                <Calendar className="w-4 h-4 mr-2 text-text-300" />
                {formatDate(userInfo.createdAt || '2025-01-01')}
              </div>
            </div>
            
            <div>
              <label className="text-xs text-text-300 uppercase tracking-wider mb-1 block">조직</label>
              <div className="flex items-center text-text-100">
                <Building className="w-4 h-4 mr-2 text-text-300" />
                {userInfo.organization || '서울경제신문'}
              </div>
            </div>
          </div>
        </div>

        {/* 구독 정보 섹션 */}
        <div className="bg-bg-100 rounded-xl border border-bg-300 p-6 mb-6">
          <div className="flex items-center mb-6">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-full flex items-center justify-center">
              <CreditCard className="w-6 h-6 text-white" />
            </div>
            <div className="ml-4">
              <h2 className="text-xl font-semibold text-text-100">구독 정보</h2>
              <p className="text-sm text-text-200">현재 구독 플랜 및 결제 정보</p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="text-xs text-text-300 uppercase tracking-wider mb-1 block">현재 플랜</label>
              <div className="text-text-100 flex items-center">
                <span className="text-lg font-semibold">{getPlanDisplayName(subscriptionInfo?.plan)}</span>
                <span className={`ml-2 px-2 py-0.5 text-xs rounded-full bg-bg-200 ${getStatusColor(subscriptionInfo?.status)}`}>
                  {getStatusDisplayName(subscriptionInfo?.status)}
                </span>
              </div>
            </div>
            
            <div>
              <label className="text-xs text-text-300 uppercase tracking-wider mb-1 block">구독 시작일</label>
              <div className="text-text-100">
                {formatDate(subscriptionInfo?.startDate)}
              </div>
            </div>
            
            <div>
              <label className="text-xs text-text-300 uppercase tracking-wider mb-1 block">다음 결제일</label>
              <div className="text-text-100">
                {subscriptionInfo?.status === 'ACTIVE' 
                  ? formatDate(subscriptionInfo?.nextBillingDate) 
                  : '-'}
              </div>
            </div>
            
            <div>
              <label className="text-xs text-text-300 uppercase tracking-wider mb-1 block">해지 예정일</label>
              <div className="text-text-100">
                {subscriptionInfo?.cancelDate 
                  ? formatDate(subscriptionInfo?.cancelDate) 
                  : '-'}
              </div>
            </div>
          </div>

          {subscriptionInfo?.status === 'CANCELLED' && (
            <div className="mt-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
              <div className="flex items-center text-red-400">
                <AlertCircle className="w-5 h-5 mr-2" />
                <span>구독이 해지되었습니다. {formatDate(subscriptionInfo?.cancelDate)}에 서비스가 종료됩니다.</span>
              </div>
            </div>
          )}
        </div>

        {/* 플랜 기능 섹션 */}
        <div className="bg-bg-100 rounded-xl border border-bg-300 p-6">
          <h3 className="text-lg font-semibold text-text-100 mb-4">플랜 기능</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between py-2">
              <span className="text-text-200">월 생성 가능 제목 수</span>
              <span className="text-text-100 font-medium">
                {subscriptionInfo?.plan === 'ENTERPRISE' ? '무제한' : '10,000개'}
              </span>
            </div>
            <div className="flex items-center justify-between py-2 border-t border-bg-300 pt-3">
              <span className="text-text-200">API 액세스</span>
              <span className="text-text-100 font-medium">
                {['PREMIUM', 'ENTERPRISE'].includes(subscriptionInfo?.plan) ? '허용' : '제한'}
              </span>
            </div>
            <div className="flex items-center justify-between py-2 border-t border-bg-300 pt-3">
              <span className="text-text-200">우선 지원</span>
              <span className="text-text-100 font-medium">
                {subscriptionInfo?.plan === 'ENTERPRISE' ? '24/7' : '업무 시간'}
              </span>
            </div>
            <div className="flex items-center justify-between py-2 border-t border-bg-300 pt-3">
              <span className="text-text-200">데이터 보관 기간</span>
              <span className="text-text-100 font-medium">
                {subscriptionInfo?.plan === 'ENTERPRISE' ? '영구' : '1년'}
              </span>
            </div>
          </div>
        </div>

        {/* 액션 버튼들 */}
        <div className="mt-8 flex flex-col sm:flex-row gap-4">
          <button
            onClick={() => navigate('/subscription')}
            className="flex-1 bg-accent-main-100 text-white py-3 px-6 rounded-lg font-medium hover:bg-accent-main-200 transition-colors"
          >
            플랜 변경
          </button>
          <button
            onClick={() => {
              const enginePath = selectedEngine.toLowerCase();
              navigate(`/${enginePath}/dashboard`);
            }}
            className="flex-1 bg-bg-200 text-text-100 py-3 px-6 rounded-lg font-medium hover:bg-bg-300 transition-colors"
          >
            대시보드로 돌아가기
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;