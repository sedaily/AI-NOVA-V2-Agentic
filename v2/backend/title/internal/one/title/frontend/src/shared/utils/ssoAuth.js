/**
 * SSO (Single Sign-On) 인증 유틸리티
 * n1.sedaily.ai에서 전달된 JWT 토큰을 처리하여 자동 로그인을 수행합니다.
 */

import { getSSOCookies, setSSOCookies } from './cookieUtils';

/**
 * URL에서 SSO 토큰 추출
 * @returns {Object|null} { idToken, accessToken } 또는 null
 */
export const getTokensFromURL = () => {
  // 방법 1: 쿠키에서 읽기 (최우선)
  const cookieTokens = getSSOCookies();
  if (cookieTokens && cookieTokens.idToken && cookieTokens.accessToken) {
    console.log('🍪 SSO: 쿠키에서 idToken과 accessToken 발견');
    return { 
      idToken: cookieTokens.idToken, 
      accessToken: cookieTokens.accessToken,
      refreshToken: cookieTokens.refreshToken 
    };
  }
  
  // 방법 2: URL에서 직접 읽기
  const urlParams = new URLSearchParams(window.location.search);
  let idToken = urlParams.get('idToken');
  let accessToken = urlParams.get('accessToken');

  if (idToken && accessToken) {
    console.log('🔑 SSO: URL에서 idToken과 accessToken 발견');
    return { idToken, accessToken };
  }

  // 방법 3: localStorage에서 읽기 (App.jsx에서 미리 저장한 것)
  idToken = localStorage.getItem('sso_pending_idToken');
  accessToken = localStorage.getItem('sso_pending_accessToken');

  if (idToken && accessToken) {
    console.log('🔑 SSO: localStorage에서 idToken과 accessToken 발견');

    // 사용 후 즉시 삭제
    localStorage.removeItem('sso_pending_idToken');
    localStorage.removeItem('sso_pending_accessToken');

    return { idToken, accessToken };
  }

  return null;
};

/**
 * JWT 토큰 디코딩 (헤더와 페이로드만)
 * @param {string} token - JWT 토큰
 * @returns {Object} 디코딩된 페이로드
 */
const decodeJWT = (token) => {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error('❌ JWT 디코딩 실패:', error);
    return null;
  }
};

/**
 * JWT 토큰 유효성 검증
 * @param {string} idToken - ID 토큰
 * @returns {boolean} 유효 여부
 */
const validateToken = (idToken) => {
  try {
    const decoded = decodeJWT(idToken);

    if (!decoded) {
      console.error('❌ 토큰 디코딩 실패');
      return false;
    }

    // 만료 시간 확인
    const currentTime = Math.floor(Date.now() / 1000);
    if (decoded.exp && decoded.exp < currentTime) {
      console.error('❌ 토큰이 만료되었습니다');
      return false;
    }

    // Cognito User Pool 확인 (us-east-1_ohLOswurY)
    const expectedIssuer = 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_ohLOswurY';
    if (decoded.iss && decoded.iss !== expectedIssuer) {
      console.error('❌ 토큰 발급자가 일치하지 않습니다:', decoded.iss);
      return false;
    }

    console.log('✅ 토큰 유효성 검증 성공');
    console.log('👤 사용자 정보:', {
      email: decoded.email,
      sub: decoded.sub,
      exp: new Date(decoded.exp * 1000).toLocaleString()
    });

    return true;
  } catch (error) {
    console.error('❌ 토큰 검증 중 오류:', error);
    return false;
  }
};

/**
 * URL에서 파라미터 제거
 * @param {Array<string>} params - 제거할 파라미터 이름 배열
 */
const removeURLParams = (params) => {
  const url = new URL(window.location.href);
  params.forEach(param => url.searchParams.delete(param));

  // URL 업데이트 (페이지 리로드 없이)
  window.history.replaceState({}, document.title, url.pathname + url.search);
  console.log('🧹 URL에서 토큰 파라미터 제거 완료');
};

/**
 * SSO 자동 로그인 시도
 * @returns {Promise<Object|null>} 로그인 성공 시 { success: true, userRole: string, userInfo: Object }, 실패 시 null
 */
export const attemptSSOLogin = async () => {
  try {
    console.log('🚀 SSO 로그인 시도 시작');

    // 1. URL에서 토큰 가져오기
    const tokens = getTokensFromURL();

    if (!tokens) {
      console.log('ℹ️ URL에 SSO 토큰이 없습니다');
      return false;
    }

    const { idToken, accessToken } = tokens;

    // 2. ID 토큰 유효성 검증
    if (!validateToken(idToken)) {
      console.error('❌ 토큰 유효성 검증 실패');
      removeURLParams(['idToken', 'accessToken']);
      return false;
    }

    // 3. 토큰 디코딩하여 사용자 정보 추출
    const decoded = decodeJWT(idToken);

    if (!decoded) {
      console.error('❌ 토큰 디코딩 실패');
      removeURLParams(['idToken', 'accessToken']);
      return false;
    }

    // 4. 사용자 정보 구성
    const userInfo = {
      email: decoded.email,
      username: decoded['cognito:username'] || decoded.email,
      sub: decoded.sub,
      emailVerified: decoded.email_verified || false,
      selectedEngine: 'T5' // 기본값, URL 경로에 따라 달라질 수 있음
    };

    // 5. 사용자 역할 설정 (이메일 기반)
    // ai@sedaily.com만 관리자
    let userRole = 'user';
    let userPlan = 'free';

    console.log('🔍 이메일 확인:', userInfo.email);

    if (userInfo.email === 'ai@sedaily.com') {
      userRole = 'admin';
      userPlan = 'premium';
      console.log('🔐 관리자 권한 부여 (ai@sedaily.com)');
    } else {
      console.log('👤 일반 사용자 권한');
    }

    // 6. localStorage에 인증 정보 저장
    localStorage.setItem('userInfo', JSON.stringify(userInfo));
    localStorage.setItem('authToken', accessToken);
    localStorage.setItem('idToken', idToken);
    localStorage.setItem('refreshToken', tokens.refreshToken || accessToken); // refreshToken이 있으면 사용
    localStorage.setItem('isLoggedIn', 'true');
    localStorage.setItem('userRole', userRole);
    localStorage.setItem('userPlan', userPlan);
    localStorage.setItem('ssoLogin', 'true'); // SSO 로그인 플래그
    
    // 6-1. SSO 쿠키 설정 (다른 서브도메인과 공유)
    setSSOCookies(idToken, accessToken, tokens.refreshToken);
    console.log('🍪 SSO 쿠키 설정 완료');

    console.log('💾 localStorage 저장 완료:');
    console.log('  - userInfo:', JSON.stringify(userInfo));
    console.log('  - isLoggedIn:', 'true');
    console.log('  - userRole:', userRole);
    console.log('  - userPlan:', userPlan);

    // 7. URL에서 엔진 정보 추출
    const currentPath = window.location.pathname;
    let selectedEngine = 'T5';

    if (currentPath.includes('/11')) {
      selectedEngine = 'T5';
    } else if (currentPath.includes('/22')) {
      selectedEngine = 'C7';
    }

    localStorage.setItem('selectedEngine', selectedEngine);

    console.log('✅ SSO 로그인 성공!');
    console.log('👤 로그인된 사용자:', userInfo.email);
    console.log('🎯 선택된 엔진:', selectedEngine);
    console.log('🔑 사용자 역할:', userRole);

    // 8. URL에서 토큰 파라미터 제거 (페이지 새로고침 없이)
    removeURLParams(['idToken', 'accessToken']);

    // 9. 사용자 정보 업데이트 이벤트 발생 (여러 번, 확실하게)
    const dispatchUpdateEvent = () => {
      window.dispatchEvent(new CustomEvent('userInfoUpdated'));
      window.dispatchEvent(new Event('storage'));
    };

    // 즉시 실행
    dispatchUpdateEvent();
    console.log('📢 userInfoUpdated 이벤트 발생 (1차)');

    // 약간의 지연 후 다시 실행
    setTimeout(() => {
      dispatchUpdateEvent();
      console.log('📢 userInfoUpdated 이벤트 발생 (2차)');
    }, 100);

    setTimeout(() => {
      dispatchUpdateEvent();
      console.log('📢 userInfoUpdated 이벤트 발생 (3차)');
    }, 500);

    // 10. 성공 결과와 함께 사용자 정보 반환
    return {
      success: true,
      userRole: userRole,
      userPlan: userPlan,
      userInfo: userInfo
    };
  } catch (error) {
    console.error('❌ SSO 로그인 중 오류 발생:', error);
    removeURLParams(['idToken', 'accessToken']);
    return null;
  }
};

/**
 * SSO 토큰 정리 (로그아웃 시 사용)
 */
export const clearSSOTokens = () => {
  localStorage.removeItem('ssoToken');
  
  // SSO 쿠키도 함께 삭제
  const { clearSSOCookies } = require('./cookieUtils');
  clearSSOCookies();
  
  console.log('🧹 SSO 토큰 및 쿠키 정리 완료');
};
