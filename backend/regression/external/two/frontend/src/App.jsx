import React, { useState, useEffect, useRef, Suspense, lazy } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import { motion } from 'framer-motion';
import { AnimatePresence } from 'framer-motion';
import ProtectedRoute from "./features/auth/components/ProtectedRoute";
import { PageTransition } from "./shared/components/ui/PageTransition";
import { ThemeProvider } from "./shared/contexts/ThemeContext";
// ThemeToggle removed - dark mode is now default

// Lazy load components for better performance
// Features 폴더의 컴포넌트 사용
const MainContent = lazy(() => import("./features/dashboard/components/MainContent"));
const ChatPage = lazy(() => import("./features/chat/containers/ChatPageContainer"));
const LoginPage = lazy(() => import("./features/auth/containers/LoginContainer").then(module => ({ default: module.default })));
const SignUpPage = lazy(() => import("./features/auth/components/SignUpPage"));
const LandingPage = lazy(() => import("./features/landing/containers/LandingContainer").then(module => ({ default: module.default })));
const Sidebar = lazy(() => import("./shared/components/layout/Sidebar"));
const Dashboard = lazy(() => import("./features/dashboard/containers/DashboardContainer").then(module => ({ default: module.default })));
const SubscriptionPage = lazy(() => import("./features/subscription/components/SubscriptionPage"));
const ProfilePage = lazy(() => import("./features/profile/components/ProfilePage"));

// Loading component - 제거됨
const LoadingSpinner = () => null;

function AppContent() {
  const navigate = useNavigate();
  const location = useLocation();
  
  // localStorage에서 상태 복원
  const [isLoggedIn, setIsLoggedIn] = useState(() => {
    return localStorage.getItem('isLoggedIn') === 'true';
  });
  const [userRole, setUserRole] = useState(() => {
    return localStorage.getItem('userRole') || "user";
  });
  const [selectedEngine, setSelectedEngine] = useState(() => {
    // 현재 경로에서 엔진 타입 추출
    if (location.pathname.includes('/11')) return "11";
    if (location.pathname.includes('/22')) return "22";
    // localStorage에서 복원
    return localStorage.getItem('selectedEngine') || "11";
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

  // URL 경로 변경 시 엔진 타입 동기화
  useEffect(() => {
    if (location.pathname.includes('/11') && selectedEngine !== '11') {
      setSelectedEngine('11');
    } else if (location.pathname.includes('/22') && selectedEngine !== '22') {
      setSelectedEngine('22');
    }
  }, [location.pathname, selectedEngine]);

  // 엔진 변경 시 프로젝트 제목 업데이트 및 localStorage 저장
  useEffect(() => {
    setCurrentProject(prev => ({
      ...prev,
      title: selectedEngine === '11' ? '속전속결 퇴고' : '구조분석 퇴고'
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
    const enginePath = selectedEngine.toLowerCase();
    navigate(`/${enginePath}/chat/${conversationId}`, {
      state: { initialMessage: message }
    });
    
    console.log('📍 대화 페이지로 이동:', `/${enginePath}/chat/${conversationId}`);
  };

  const handleBackToMain = () => {
    const enginePath = selectedEngine.toLowerCase();
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
    
    // 로컬 상태 및 스토리지 초기화
    setIsLoggedIn(false);
    setUserRole("user");
    localStorage.removeItem('isLoggedIn');
    localStorage.removeItem('userRole');
    localStorage.removeItem('selectedEngine');
    localStorage.removeItem('userInfo');
    localStorage.removeItem('authToken');
    localStorage.removeItem('idToken');
    localStorage.removeItem('refreshToken');
    
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

    // 엔진이 선택된 상태에서 로그인했다면 해당 엔진 페이지로 이동
    if (location.state?.engine) {
      const enginePath = engine.toLowerCase();
      navigate(`/${enginePath}`);
    } else {
      // 엔진이 선택되지 않은 상태(헤더 로그인 버튼 등)에서는 랜딩 페이지로 이동
      navigate("/");
    }
  };

  const handleSelectEngine = (engine) => {
    console.log('🚀 handleSelectEngine called with:', engine);
    setSelectedEngine(engine);
    setCurrentProject((prev) => ({
      ...prev,
      title: engine === '11' ? '속전속결 퇴고' : '구조분석 퇴고',
    }));

    // 로그인 상태 확인
    if (isLoggedIn) {
      // 로그인되어 있으면 해당 엔진 페이지로 이동
      const enginePath = engine.toLowerCase();
      navigate(`/${enginePath}`);
    } else {
      // 로그인되어 있지 않으면 로그인 페이지로
      navigate("/login", { state: { engine } });
    }
  };

  const handleSignUp = () => {
    setIsLoggedIn(true);
    const enginePath = selectedEngine.toLowerCase();
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
    const enginePath = engine ? engine.toLowerCase() : selectedEngine.toLowerCase();
    navigate(`/${enginePath}/dashboard`);
  };

  const handleBackFromDashboard = (engine) => {
    const enginePath = engine ? engine.toLowerCase() : selectedEngine.toLowerCase();
    navigate(`/${enginePath}/chat`);
  };

  // 사이드바를 보여줄 페이지 확인 (랜딩, 로그인, 회원가입, 대시보드, 구독, 프로필 제외)
  const showSidebar = !['/', '/login', '/signup', '/subscription', '/profile'].includes(location.pathname) && !location.pathname.includes('/dashboard');

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
              <Route 
                path="/" 
                element={
                  <PageTransition pageKey="landing">
                    <LandingPage
                      onSelectEngine={handleSelectEngine}
                      onLogin={handleLogin}
                      onLogout={handleLogout}
                    />
                  </PageTransition>
                } 
              />
          <Route 
            path="/login" 
            element={
              <LoginPage 
                onLogin={handleLogin} 
                onGoToSignUp={handleGoToSignUp}
                selectedEngine={location.state?.engine || selectedEngine}
              />
            } 
          />
          <Route 
            path="/signup" 
            element={
              <SignUpPage
                onSignUp={handleSignUp}
                onBackToLogin={handleBackToLogin}
              />
            } 
          />
            <Route
              path="/11/chat/:conversationId?"
              element={
                <ProtectedRoute>
                  <PageTransition pageKey="chat-11">
                    <ChatPage
                      initialMessage={location.state?.initialMessage}
                      userRole={userRole}
                      selectedEngine="11"
                      onLogout={handleLogout}
                      onBackToLanding={handleBackToLanding}
                      onTitleUpdate={handleTitleUpdate}
                      onToggleSidebar={toggleSidebar}
                      isSidebarOpen={isSidebarOpen}
                      onNewConversation={handleNewConversation}
                      onDashboard={() => handleDashboard("11")}
                    />
                  </PageTransition>
                </ProtectedRoute>
              }
            />
            <Route
              path="/22/chat/:conversationId?"
              element={
                <ProtectedRoute>
                  <PageTransition pageKey="chat-22">
                    <ChatPage
                      initialMessage={location.state?.initialMessage}
                      userRole={userRole}
                      selectedEngine="22"
                      onLogout={handleLogout}
                      onBackToLanding={handleBackToLanding}
                      onTitleUpdate={handleTitleUpdate}
                      onToggleSidebar={toggleSidebar}
                      isSidebarOpen={isSidebarOpen}
                      onNewConversation={handleNewConversation}
                      onDashboard={() => handleDashboard("22")}
                    />
                  </PageTransition>
                </ProtectedRoute>
              }
            />
            <Route
              path="/11"
              element={
                <ProtectedRoute>
                  <PageTransition pageKey="main-11">
                    <MainContent
                      project={currentProject}
                      userRole={userRole}
                      selectedEngine="11"
                      onToggleStar={toggleStar}
                      onStartChat={handleStartChat}
                      onLogout={handleLogout}
                      onBackToLanding={handleBackToLanding}
                      onToggleSidebar={toggleSidebar}
                      isSidebarOpen={isSidebarOpen}
                      onDashboard={() => handleDashboard("11")}
                    />
                  </PageTransition>
                </ProtectedRoute>
              }
            />
            <Route
              path="/22"
              element={
                <ProtectedRoute>
                  <PageTransition pageKey="main-22">
                    <MainContent
                      project={currentProject}
                      userRole={userRole}
                      selectedEngine="22"
                      onToggleStar={toggleStar}
                      onStartChat={handleStartChat}
                      onLogout={handleLogout}
                      onBackToLanding={handleBackToLanding}
                      onToggleSidebar={toggleSidebar}
                      isSidebarOpen={isSidebarOpen}
                      onDashboard={() => handleDashboard("22")}
                    />
                  </PageTransition>
                </ProtectedRoute>
              }
            />
            <Route
              path="/11/dashboard"
              element={
                <ProtectedRoute>
                  <PageTransition pageKey="dashboard-11">
                    <Dashboard
                      selectedEngine="11"
                      onBack={() => handleBackFromDashboard("11")}
                    />
                  </PageTransition>
                </ProtectedRoute>
              }
            />
            <Route
              path="/22/dashboard"
              element={
                <ProtectedRoute>
                  <PageTransition pageKey="dashboard-22">
                    <Dashboard
                      selectedEngine="22"
                      onBack={() => handleBackFromDashboard("22")}
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
            {/* 기존 C1/C2 경로를 새 11/22 경로로 리다이렉트 */}
            <Route path="/c1" element={<Navigate to="/11" replace />} />
            <Route path="/c1/chat/:conversationId?" element={<Navigate to="/11" replace />} />
            <Route path="/c1/dashboard" element={<Navigate to="/11/dashboard" replace />} />
            <Route path="/c2" element={<Navigate to="/22" replace />} />
            <Route path="/c2/chat/:conversationId?" element={<Navigate to="/22" replace />} />
            <Route path="/c2/dashboard" element={<Navigate to="/22/dashboard" replace />} />

            {/* 기본 리다이렉트 */}
            <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </AnimatePresence>
      </motion.div>
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
