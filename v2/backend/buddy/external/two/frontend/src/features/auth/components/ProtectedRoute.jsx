import React, { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import authService from "../services/authService";

const ProtectedRoute = ({ children, requiredRole = null }) => {
  // 초기값을 localStorage에서 바로 확인하여 불필요한 로딩 방지
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return localStorage.getItem('isLoggedIn') === 'true';
  });
  const [isLoading, setIsLoading] = useState(true); // SSO 체크 중에는 로딩 표시
  const [userRole, setUserRole] = useState(() => {
    return localStorage.getItem('userRole');
  });
  const [ssoChecked, setSsoChecked] = useState(false); // SSO 체크 완료 여부

  useEffect(() => {
    // SSO 토큰 체크 (최초 1회만)
    if (!ssoChecked) {
      checkSSOToken();
      return;
    }

    // SSO 체크 완료 후에만 진행
    setIsLoading(false);

    // 이미 로그인 상태가 확인되면 바로 children 렌더링
    if (isAuthenticated) {
      // 백그라운드에서 세션 유효성 확인
      checkAuthInBackground();
    } else {
      // 로그인되지 않은 경우에만 로딩 표시
      setIsLoading(true);
      checkAuth();
    }
  }, [ssoChecked]);

  // SSO 토큰 자동 로그인 체크
  const checkSSOToken = async () => {
    try {
      console.log('🔍 SSO 토큰 체크 시작...');

      // 1. URL에서 토큰 확인
      const urlTokens = authService.getSSOTokenFromURL();

      if (urlTokens && urlTokens.idToken && urlTokens.accessToken) {
        console.log('✅ URL에서 SSO 토큰 발견, 자동 로그인 시도');
        const result = await authService.signInWithSSOToken(
          urlTokens.idToken,
          urlTokens.accessToken
        );

        if (result.success) {
          setIsAuthenticated(true);
          setUserRole('user');
          setSsoChecked(true);

          // localStorage에도 로그인 상태 저장
          localStorage.setItem('isLoggedIn', 'true');
          localStorage.setItem('userRole', 'user');

          // URL에서 토큰 파라미터 제거
          const url = new URL(window.location.href);
          url.searchParams.delete('idToken');
          url.searchParams.delete('accessToken');
          url.searchParams.delete('token'); // 기존 방식 호환
          window.history.replaceState({}, '', url.toString());

          console.log('✅ SSO 자동 로그인 성공!');
          return;
        }
      }

      // 2. LocalStorage에서 토큰 확인
      const storageTokens = authService.getSSOTokenFromStorage();

      if (storageTokens && storageTokens.idToken && storageTokens.accessToken) {
        console.log('✅ LocalStorage에서 SSO 토큰 발견, 자동 로그인 시도');
        const result = await authService.signInWithSSOToken(
          storageTokens.idToken,
          storageTokens.accessToken
        );

        if (result.success) {
          setIsAuthenticated(true);
          setUserRole('user');
          setSsoChecked(true);

          // localStorage에도 로그인 상태 저장
          localStorage.setItem('isLoggedIn', 'true');
          localStorage.setItem('userRole', 'user');

          console.log('✅ SSO 자동 로그인 성공!');
          return;
        }
      }

      console.log('ℹ️ SSO 토큰 없음, 일반 인증 체크로 진행');
      setSsoChecked(true);
    } catch (error) {
      console.error('❌ SSO 토큰 체크 오류:', error);
      setSsoChecked(true);
    }
  };

  // 백그라운드에서 세션 확인 (UI 블로킹 없이)
  const checkAuthInBackground = async () => {
    try {
      const authenticated = await authService.isAuthenticated();
      
      if (!authenticated) {
        // 세션이 만료된 경우만 처리
        localStorage.removeItem('isLoggedIn');
        localStorage.removeItem('userRole');
        localStorage.removeItem('userInfo');
        localStorage.removeItem('authToken');
        setIsAuthenticated(false);
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
      
      if (!isLoggedIn) {
        setIsAuthenticated(false);
        setIsLoading(false);
        return;
      }

      // Cognito 세션 확인
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
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
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
};

export default ProtectedRoute;