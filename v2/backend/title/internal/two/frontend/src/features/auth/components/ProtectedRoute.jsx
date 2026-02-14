import React, { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import authService from "../services/authService";
import { attemptSSOLogin, getTokensFromURL } from "../../../shared/utils/ssoAuth";

const ProtectedRoute = ({ children, requiredRole = null }) => {
  // 로그인 기능 비활성화 - 항상 허용
  return children;
  
  /* 아래 코드 비활성화
  console.log('🔐 ProtectedRoute 초기화');

  // SSO 토큰이 URL에 있는지 확인
  const hasSSOTokens = () => {
    console.log('🔍 ProtectedRoute: SSO 토큰 확인 시작');
    console.log('  - 현재 URL:', window.location.href);
    console.log('  - 현재 search:', window.location.search);
    const tokens = getTokensFromURL();
    console.log('  - getTokensFromURL 결과:', tokens);
    return tokens !== null;
  };

  // 초기값을 localStorage에서 바로 확인하여 불필요한 로딩 방지
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
    console.log('🔐 초기 isLoggedIn:', isLoggedIn);
    return isLoggedIn;
  });
  // SSO 토큰이 있으면 로딩으로 시작
  const [isLoading, setIsLoading] = useState(() => {
    const hasTokens = hasSSOTokens();
    console.log('🔐 초기 hasSSOTokens:', hasTokens);
    console.log('🔐 초기 로딩 상태:', hasTokens);
    return hasTokens;
  });
  const [userRole, setUserRole] = useState(() => {
    const role = localStorage.getItem('userRole');
    console.log('🔐 초기 userRole:', role);
    return role;
  });

  useEffect(() => {
    console.log('🔐 ProtectedRoute useEffect 실행');
    console.log('  - isAuthenticated:', isAuthenticated);
    console.log('  - localStorage.isLoggedIn:', localStorage.getItem('isLoggedIn'));
    console.log('  - localStorage.ssoLogin:', localStorage.getItem('ssoLogin'));

    // SSO 토큰이 URL에 있으면 SSO 로그인 시도
    const hasTokens = hasSSOTokens();
    console.log('  - hasSSOTokens() 결과:', hasTokens);

    if (hasTokens) {
      console.log('🔑 SSO 토큰 감지 - 자동 로그인 시도');
      handleSSOLogin();
      return;
    }

    // 이미 로그인 상태가 확인되면 바로 children 렌더링
    if (isAuthenticated) {
      console.log('🔐 이미 로그인됨 - 백그라운드 세션 확인');
      setIsLoading(false); // 이미 로그인됨 - 로딩 종료
      // 백그라운드에서 세션 유효성 확인
      checkAuthInBackground();
    } else {
      console.log('🔐 로그인 안됨 - 로그인 페이지로 리디렉션');
      setIsLoading(false);
    }
  }, []);

  // SSO 로그인 처리
  const handleSSOLogin = async () => {
    try {
      console.log('🔐 ProtectedRoute: SSO 로그인 시작');
      setIsLoading(true);
      const result = await attemptSSOLogin();

      console.log('🔐 ProtectedRoute: attemptSSOLogin 결과:', result);

      if (result && result.success) {
        console.log('✅ ProtectedRoute: SSO 로그인 성공');

        // attemptSSOLogin에서 반환된 값을 직접 사용
        console.log('📦 SSO에서 받은 데이터:');
        console.log('  - userRole:', result.userRole);
        console.log('  - userPlan:', result.userPlan);
        console.log('  - userInfo:', result.userInfo);

        console.log('🔄 페이지 새로고침으로 헤더 업데이트');

        // URL에서 토큰 제거한 경로로 페이지 새로고침
        const currentPath = window.location.pathname;
        window.location.replace(currentPath);

        // 새로고침 후에는 아래 코드가 실행되지 않지만,
        // 혹시 모르니 상태도 업데이트
        setIsAuthenticated(true);
        setUserRole(result.userRole);
      } else {
        console.warn('⚠️ ProtectedRoute: SSO 로그인 실패 - 일반 로그인 필요');
        setIsAuthenticated(false);
      }
    } catch (error) {
      console.error('❌ ProtectedRoute: SSO 로그인 오류:', error);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
      console.log('🏁 ProtectedRoute: 로딩 완료');
    }
  };

  // 백그라운드에서 세션 확인 (UI 블로킹 없이)
  const checkAuthInBackground = async () => {
    try {
      // SSO 로그인인 경우 Cognito 세션 확인 건너뛰기
      const isSSOLogin = localStorage.getItem('ssoLogin') === 'true';
      if (isSSOLogin) {
        console.log('🔐 SSO 로그인 - Cognito 세션 확인 건너뜀');
        return;
      }

      const authenticated = await authService.isAuthenticated();

      if (!authenticated) {
        // 세션이 만료된 경우 localStorage만 정리하고 리디렉션은 하지 않음
        // 리디렉션은 다음 페이지 로드 시에만 발생
        localStorage.removeItem('isLoggedIn');
        localStorage.removeItem('userRole');
        localStorage.removeItem('userInfo');
        localStorage.removeItem('authToken');
        console.warn('⚠️ 세션이 만료되었습니다. 다음 탐색 시 로그인이 필요합니다.');
        // setIsAuthenticated(false); <- 이 줄을 제거하여 진행 중인 페이지에서 리디렉션 방지
      }
    } catch (error) {
      console.error('백그라운드 인증 확인 오류:', error);
    }
  };

  const checkAuth = async () => {
    try {
      // 로컬 스토리지 확인
      const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
      const storedRole = localStorage.getItem('userRole');
      const isSSOLogin = localStorage.getItem('ssoLogin') === 'true';

      if (!isLoggedIn) {
        setIsAuthenticated(false);
        setIsLoading(false);
        return;
      }

      // SSO 로그인인 경우 Cognito 세션 확인 건너뛰기
      if (isSSOLogin) {
        console.log('🔐 SSO 로그인 - Cognito 세션 확인 건너뜀 (checkAuth)');
        setIsAuthenticated(true);
        setUserRole(storedRole || 'user');
        setIsLoading(false);
        return;
      }

      // 일반 Cognito 로그인인 경우에만 세션 확인
      const authenticated = await authService.isAuthenticated();

      if (authenticated) {
        setIsAuthenticated(true);
        setUserRole(storedRole || 'user');
      } else {
        // 세션이 만료된 경우 로컬 스토리지 정리
        localStorage.removeItem('isLoggedIn');
        localStorage.removeItem('userRole');
        localStorage.removeItem('userInfo');
        localStorage.removeItem('authToken');
        setIsAuthenticated(false);
      }
    } catch (error) {
      console.error('인증 확인 오류:', error);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg font-medium">로그인 확인 중...</p>
          <p className="text-gray-400 text-sm mt-2">잠시만 기다려주세요</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    // 현재 경로 정보를 로그인 페이지로 전달
    const currentPath = window.location.pathname;
    let engineState = null;

    // 경로에서 엔진 타입 추출
    if (currentPath.includes('/11')) {
      engineState = { engine: 'T5', returnPath: currentPath };
    } else if (currentPath.includes('/22')) {
      engineState = { engine: 'C7', returnPath: currentPath };
    }

    return <Navigate to="/login" replace state={engineState} />;
  }

  // 특정 역할이 필요한 경우 확인
  if (requiredRole && userRole !== requiredRole) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-4">접근 권한이 없습니다</h2>
          <p className="text-gray-600">이 페이지에 접근하려면 {requiredRole} 권한이 필요합니다.</p>
        </div>
      </div>
    );
  }

  return children;
  */
};

export default ProtectedRoute;