import React, { useState, useEffect, useRef, Suspense, lazy } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import { motion } from 'framer-motion';
import { AnimatePresence } from 'framer-motion';
import ProtectedRoute from "./features/auth/components/ProtectedRoute";
import { PageTransition } from "./shared/components/ui/PageTransition";
import { ThemeProvider } from "./shared/contexts/ThemeContext";
import ThemeToggle from "./shared/components/ui/ThemeToggle";

// Lazy load components for better performance
// Features 폴더의 컴포넌트 사용
const MainContent = lazy(() => import("./features/dashboard/components/MainContent"));
const ChatPage = lazy(() => import("./features/chat/containers/ChatPageContainer"));
const LoginPage = lazy(() => import("./features/auth/containers/LoginContainer").then(module => ({ default: module.default })));
const SignUpPage = lazy(() => import("./features/auth/components/SignUpPage"));
// LandingPage 제거됨 - / 접속 시 /11로 바로 리다이렉트
const Sidebar = lazy(() => import("./shared/components/layout/Sidebar"));
const Dashboard = lazy(() => import("./features/dashboard/containers/DashboardContainer").then(module => ({ default: module.default })));
const SubscriptionPage = lazy(() => import("./features/subscription/components/SubscriptionPage"));
const ProfilePage = lazy(() => import("./features/profile/components/ProfilePage"));

// Loading component - 제거됨
const LoadingSpinner = () => null;

function AppContent() {
  const navigate = useNavigate();
  const location = useLocation();
  
  // 접근 권한 체크 제거됨 - 모든 접근 허용
  const [accessAllowed] = useState(true);

  // SSO 및 로그인 기능 비활성화

  // 기본적으로 로그인 상태로 설정 (로그인 기능 비활성화)
  const [isLoggedIn, setIsLoggedIn] = useState(true);
  const [userRole, setUserRole] = useState("user");
  const [selectedEngine, setSelectedEngine] = useState(() => {
    // 현재 경로에서 엔진 타입 추출
    if (location.pathname.includes('/11')) return "T5";
    if (location.pathname.includes('/22')) return "C7";
    // localStorage에서 복원
    return localStorage.getItem('selectedEngine') || "T5";
  });
  const [currentProject, setCurrentProject] = useState({
    title: "아키텍쳐",
    isStarred: false,
  });
  const [isSidebarOpen, setIsSidebarOpen] = useState(() => {
    // 모바일에서는 기본적으로 닫힘
    if (typeof window !== 'undefined' && window.innerWidth < 768) {
      return false;
    }
    return true;
  });
  const sidebarRef = useRef(null);

  // URL 경로 변경 감지하여 엔진 상태 동기화
  useEffect(() => {
    let newEngine = selectedEngine;

    if (location.pathname.includes('/11')) {
      newEngine = "T5";
    } else if (location.pathname.includes('/22')) {
      newEngine = "C7";
    }

    if (newEngine !== selectedEngine) {
      setSelectedEngine(newEngine);
    }
  }, [location.pathname, selectedEngine]);

  // 엔진 변경 시 프로젝트 제목 업데이트 및 localStorage 저장
  useEffect(() => {
    setCurrentProject(prev => ({
      ...prev,
      title: selectedEngine === 'T5' ? '핵심을 꿰뚫는 타이틀' : '상상 그 이상의 창의적 제목'
    }));
    localStorage.setItem('selectedEngine', selectedEngine);
  }, [selectedEngine]);

  // 로그인 상태 변경 시 localStorage 저장
  useEffect(() => {
    localStorage.setItem('isLoggedIn', isLoggedIn);
  }, [isLoggedIn]);

  // 사용자 역할 변경 시 localStorage 저장
  useEffect(() => {
    localStorage.setItem('userRole', userRole);
  }, [userRole]);

  const toggleStar = () => {
    setCurrentProject((prev) => ({
      ...prev,
      isStarred: !prev.isStarred,
    }));
  };

  const handleStartChat = (message) => {
    console.log('🚀 handleStartChat called with:', message);
    
    // 새 대화 ID 생성 (엔진_타임스탬프 형식)
    const conversationId = `${selectedEngine}_${Date.now()}`;
    console.log('🆕 새 대화 ID 생성:', conversationId);
    
    // localStorage에 임시 저장 (페이지 전환 중 데이터 보존)
    localStorage.setItem('pendingMessage', message);
    localStorage.setItem('pendingConversationId', conversationId);
    
    // conversationId를 포함한 URL로 이동
    const enginePath = selectedEngine === 'T5' ? '11' : '22';
    navigate(`/${enginePath}/chat/${conversationId}`, {
      state: { initialMessage: message }
    });

    console.log('📍 대화 페이지로 이동:', `/${enginePath}/chat/${conversationId}`);
  };

  const handleBackToMain = () => {
    const enginePath = selectedEngine === 'T5' ? '11' : '22';
    navigate(`/${enginePath}`);
  };

  const handleLogout = async () => {
    console.log('🚪 App.jsx handleLogout 호출됨');
    try {
      // Cognito 로그아웃
      const authService = (await import('./features/auth/services/authService')).default;
      await authService.signOut();
      console.log('✅ Cognito 로그아웃 완료');
    } catch (error) {
      console.error('로그아웃 오류:', error);
    }

    // SSO 토큰 정리
    try {
      const { clearSSOTokens } = await import('./shared/utils/ssoAuth');
      clearSSOTokens();
    } catch (error) {
      console.error('SSO 토큰 정리 오류:', error);
    }

    // 로컬 상태 및 스토리지 초기화
    setIsLoggedIn(false);
    setUserRole("user");
    localStorage.removeItem('isLoggedIn');
    localStorage.removeItem('userRole');
    localStorage.removeItem('userPlan');
    localStorage.removeItem('selectedEngine');
    localStorage.removeItem('userInfo');
    localStorage.removeItem('authToken');
    localStorage.removeItem('idToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('ssoLogin');

    // 사용량 캐시도 정리
    localStorage.removeItem('usage_percentage_T5');
    localStorage.removeItem('usage_percentage_time_T5');
    localStorage.removeItem('usage_percentage_C7');
    localStorage.removeItem('usage_percentage_time_C7');

    // Header에 사용자 정보 업데이트 알림
    window.dispatchEvent(new CustomEvent('userInfoUpdated'));

    // 현재 페이지가 랜딩 페이지가 아닌 경우에만 랜딩 페이지로 이동
    if (location.pathname !== '/') {
      console.log('📍 랜딩 페이지로 이동');
      navigate("/");
    } else {
      console.log('📍 현재 랜딩 페이지 유지');
    }
  };

  const handleLogin = (role = "user") => {
    setIsLoggedIn(true);
    setUserRole(role);
    // location.state에서 엔진 정보 가져오기
    const engine = location.state?.engine || selectedEngine;
    setSelectedEngine(engine);

    // returnPath가 있으면 해당 경로로 이동 (ProtectedRoute에서 온 경우)
    if (location.state?.returnPath) {
      console.log('📍 원래 접속하려던 경로로 복귀:', location.state.returnPath);
      navigate(location.state.returnPath, { replace: true });
    }
    // 엔진이 선택된 상태에서 로그인했다면 해당 엔진 페이지로 이동
    else if (location.state?.engine) {
      const enginePath = engine === 'T5' ? '11' : '22';
      navigate(`/${enginePath}`);
    } else {
      // 엔진이 선택되지 않은 상태(헤더 로그인 버튼 등)에서는 랜딩 페이지로 이동
      navigate("/");
    }
  };

  const handleSelectEngine = (engine) => {
    setSelectedEngine(engine);
    setCurrentProject((prev) => ({
      ...prev,
      title: engine === 'T5' ? '핵심을 꿰뚫는 타이틀' : '상상 그 이상의 창의적 제목',
    }));

    if (isLoggedIn) {
      // 로그인되어 있으면 해당 엔진 페이지로 이동
      const enginePath = engine === 'T5' ? '11' : '22';
      navigate(`/${enginePath}`);
    } else {
      // 로그인되어 있지 않으면 로그인 페이지로
      navigate("/login", { state: { engine } });
    }
  };

  const handleSignUp = () => {
    setIsLoggedIn(true);
    const enginePath = selectedEngine === 'T5' ? '11' : '22';
    navigate(`/${enginePath}`);
  };

  const handleGoToSignUp = () => {
    navigate("/signup");
  };

  const handleBackToLogin = () => {
    navigate("/login");
  };

  const handleBackToLanding = () => {
    navigate("/");
  };

  const handleTitleUpdate = (newTitle) => {
    setCurrentProject(prev => ({
      ...prev,
      title: newTitle
    }));
    console.log("📝 앱 제목 업데이트됨:", newTitle);
  };

  const toggleSidebar = () => {
    setIsSidebarOpen(prev => !prev);
  };

  const handleNewConversation = () => {
    // 사이드바의 대화 목록 새로고침
    if (sidebarRef.current && sidebarRef.current.loadConversations) {
      sidebarRef.current.loadConversations();
    }
  };

  const handleDashboard = (engine) => {
    const targetEngine = engine || selectedEngine;
    const enginePath = targetEngine === 'T5' ? '11' : '22';
    navigate(`/${enginePath}/dashboard`);
  };

  const handleBackFromDashboard = (engine) => {
    const targetEngine = engine || selectedEngine;
    const enginePath = targetEngine === 'T5' ? '11' : '22';
    navigate(`/${enginePath}/chat`);
  };

  // 사이드바 비활성화 (회사 서비스)
  const showSidebar = false;

  return (
    <div
      className="flex w-full overflow-x-clip"
      style={{
        minHeight: "100dvh",
        backgroundColor: "hsl(var(--bg-100))",
        color: "hsl(var(--text-100))",
      }}
    >
      {/* Sidebar - show on all pages except landing, login, signup */}
      {showSidebar && (
        <Sidebar 
          ref={sidebarRef}
          selectedEngine={selectedEngine}
          isOpen={isSidebarOpen}
          onToggle={toggleSidebar}
        />
      )}
      
      <motion.div 
        className="min-h-full w-full min-w-0 flex-1"
        animate={{ 
          marginLeft: showSidebar && isSidebarOpen && window.innerWidth >= 768 ? 288 : 0 
        }}
        transition={{
          type: "tween",
          ease: "easeInOut",
          duration: 0.2
        }}
      >
        <AnimatePresence mode="wait">
          <Suspense fallback={<LoadingSpinner />}>
            <Routes location={location} key={location.pathname.split('/').slice(0, 3).join('/')}>
              {/* / 접속 시 /11로 리다이렉트 (랜딩페이지 없음) */}
              <Route path="/" element={<Navigate to="/11" replace />} />
              {/* 로그인/회원가입 비활성화 - /11로 리다이렉트 */}
              <Route path="/login" element={<Navigate to="/11" replace />} />
              <Route path="/signup" element={<Navigate to="/11" replace />} />
            <Route
              path="/11/chat/:conversationId?"
              element={
                <ProtectedRoute>
                  <PageTransition pageKey="chat-t5">
                    <ChatPage
                      initialMessage={location.state?.initialMessage}
                      userRole={userRole}
                      selectedEngine="T5"
                      onLogout={handleLogout}
                      onBackToLanding={handleBackToLanding}
                      onTitleUpdate={handleTitleUpdate}
                      isSidebarOpen={isSidebarOpen}
                      onNewConversation={handleNewConversation}
                      onDashboard={() => handleDashboard("T5")}
                    />
                  </PageTransition>
                </ProtectedRoute>
              }
            />
            <Route
              path="/22/chat/:conversationId?"
              element={
                <ProtectedRoute>
                  <PageTransition pageKey="chat-c7">
                    <ChatPage
                      initialMessage={location.state?.initialMessage}
                      userRole={userRole}
                      selectedEngine="C7"
                      onLogout={handleLogout}
                      onBackToLanding={handleBackToLanding}
                      onTitleUpdate={handleTitleUpdate}
                      isSidebarOpen={isSidebarOpen}
                      onNewConversation={handleNewConversation}
                      onDashboard={() => handleDashboard("C7")}
                    />
                  </PageTransition>
                </ProtectedRoute>
              }
            />
            <Route
              path="/11"
              element={
                <ProtectedRoute>
                  <PageTransition pageKey="main-t5">
                    <MainContent
                      project={currentProject}
                      userRole={userRole}
                      selectedEngine="T5"
                      onToggleStar={toggleStar}
                      onStartChat={handleStartChat}
                      onLogout={handleLogout}
                      onBackToLanding={handleBackToLanding}
                      isSidebarOpen={isSidebarOpen}
                      onDashboard={() => handleDashboard("T5")}
                    />
                  </PageTransition>
                </ProtectedRoute>
              }
            />
            <Route
              path="/22"
              element={
                <ProtectedRoute>
                  <PageTransition pageKey="main-c7">
                    <MainContent
                      project={currentProject}
                      userRole={userRole}
                      selectedEngine="C7"
                      onToggleStar={toggleStar}
                      onStartChat={handleStartChat}
                      onLogout={handleLogout}
                      onBackToLanding={handleBackToLanding}
                      isSidebarOpen={isSidebarOpen}
                      onDashboard={() => handleDashboard("C7")}
                    />
                  </PageTransition>
                </ProtectedRoute>
              }
            />
            <Route
              path="/11/dashboard"
              element={
                <ProtectedRoute>
                  <PageTransition pageKey="dashboard-t5">
                    <Dashboard
                      selectedEngine="T5"
                      onBack={() => handleBackFromDashboard("T5")}
                    />
                  </PageTransition>
                </ProtectedRoute>
              }
            />
            <Route
              path="/22/dashboard"
              element={
                <ProtectedRoute>
                  <PageTransition pageKey="dashboard-c7">
                    <Dashboard
                      selectedEngine="C7"
                      onBack={() => handleBackFromDashboard("C7")}
                    />
                  </PageTransition>
                </ProtectedRoute>
              }
            />
            <Route 
              path="/subscription" 
              element={
                <ProtectedRoute>
                  <PageTransition pageKey="subscription">
                    <SubscriptionPage />
                  </PageTransition>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/profile" 
              element={
                <ProtectedRoute>
                  <PageTransition pageKey="profile">
                    <ProfilePage />
                  </PageTransition>
                </ProtectedRoute>
              } 
            />
            {/* 기본 리다이렉트 */}
            <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </AnimatePresence>
      </motion.div>

      {/* 테마 토글 버튼 - 우하단 고정 */}
      <ThemeToggle />
    </div>
  );
}

function App() {
  return (
    <ThemeProvider>
      <Router>
        <AppContent />
      </Router>
    </ThemeProvider>
  );
}

export default App;
