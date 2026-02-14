/**
 * 쿠키 유틸리티 함수들
 * 서브도메인 간 SSO를 위한 쿠키 관리
 */

/**
 * 쿠키 설정
 * @param {string} name - 쿠키 이름
 * @param {string} value - 쿠키 값
 * @param {Object} options - 쿠키 옵션
 */
export const setCookie = (name, value, options = {}) => {
  const defaults = {
    path: '/',
    // .sedaily.ai 도메인으로 설정하여 모든 서브도메인에서 접근 가능
    domain: '.sedaily.ai',
    // 24시간 (초 단위)
    maxAge: 86400,
    // HTTPS에서만 전송
    secure: true,
    // CORS 요청 시에도 쿠키 전송 (SSO에 필요)
    sameSite: 'none'
  };

  // 개발 환경에서는 localhost 사용
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    delete defaults.domain;
    defaults.secure = false;
    defaults.sameSite = 'lax';
  }

  const finalOptions = { ...defaults, ...options };
  
  let cookieString = `${name}=${encodeURIComponent(value)}`;
  
  if (finalOptions.domain) {
    cookieString += `; domain=${finalOptions.domain}`;
  }
  
  if (finalOptions.path) {
    cookieString += `; path=${finalOptions.path}`;
  }
  
  if (finalOptions.maxAge) {
    cookieString += `; max-age=${finalOptions.maxAge}`;
  }
  
  if (finalOptions.expires) {
    cookieString += `; expires=${finalOptions.expires.toUTCString()}`;
  }
  
  if (finalOptions.secure) {
    cookieString += '; secure';
  }
  
  if (finalOptions.sameSite) {
    cookieString += `; samesite=${finalOptions.sameSite}`;
  }
  
  document.cookie = cookieString;
  
  console.log(`🍪 쿠키 설정: ${name} (도메인: ${finalOptions.domain || 'current'})`);
};

/**
 * 쿠키 가져오기
 * @param {string} name - 쿠키 이름
 * @returns {string|null} 쿠키 값
 */
export const getCookie = (name) => {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  
  if (parts.length === 2) {
    const cookieValue = parts.pop().split(';').shift();
    return decodeURIComponent(cookieValue);
  }
  
  return null;
};

/**
 * 쿠키 삭제
 * @param {string} name - 쿠키 이름
 * @param {Object} options - 쿠키 옵션
 */
export const deleteCookie = (name, options = {}) => {
  const defaults = {
    path: '/',
    domain: '.sedaily.ai'
  };

  // 개발 환경에서는 localhost 사용
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    delete defaults.domain;
  }

  const finalOptions = { ...defaults, ...options };
  
  // 쿠키 삭제는 만료 시간을 과거로 설정
  setCookie(name, '', {
    ...finalOptions,
    maxAge: -1
  });
  
  // 도메인 없이도 한 번 더 삭제 (로컬 쿠키 삭제)
  document.cookie = `${name}=; path=/; max-age=-1`;
  
  console.log(`🗑️ 쿠키 삭제: ${name}`);
};

/**
 * SSO 토큰을 쿠키에 저장
 * @param {string} idToken - ID 토큰
 * @param {string} accessToken - Access 토큰
 * @param {string} refreshToken - Refresh 토큰 (선택사항)
 */
export const setSSOCookies = (idToken, accessToken, refreshToken = null) => {
  console.log('🔐 SSO 쿠키 설정 시작');
  
  // 7일간 유지 (604800초)
  const cookieOptions = {
    maxAge: 604800
  };
  
  if (idToken) {
    setCookie('sso_id_token', idToken, cookieOptions);
  }
  
  if (accessToken) {
    setCookie('sso_access_token', accessToken, cookieOptions);
  }
  
  if (refreshToken) {
    setCookie('sso_refresh_token', refreshToken, cookieOptions);
  }
  
  // SSO 플래그 설정
  setCookie('sso_enabled', 'true', cookieOptions);
  
  console.log('✅ SSO 쿠키 설정 완료');
};

/**
 * SSO 토큰을 쿠키에서 가져오기
 * @returns {Object|null} { idToken, accessToken, refreshToken } 또는 null
 */
export const getSSOCookies = () => {
  const ssoEnabled = getCookie('sso_enabled');
  
  if (!ssoEnabled) {
    return null;
  }
  
  const idToken = getCookie('sso_id_token');
  const accessToken = getCookie('sso_access_token');
  const refreshToken = getCookie('sso_refresh_token');
  
  if (!idToken && !accessToken) {
    return null;
  }
  
  console.log('🍪 SSO 쿠키 발견');
  return {
    idToken,
    accessToken,
    refreshToken
  };
};

/**
 * SSO 쿠키 삭제
 */
export const clearSSOCookies = () => {
  console.log('🗑️ SSO 쿠키 삭제 시작');
  
  deleteCookie('sso_id_token');
  deleteCookie('sso_access_token');
  deleteCookie('sso_refresh_token');
  deleteCookie('sso_enabled');
  
  console.log('✅ SSO 쿠키 삭제 완료');
};

/**
 * 쿠키 지원 여부 확인
 * @returns {boolean} 쿠키 지원 여부
 */
export const areCookiesEnabled = () => {
  try {
    // 테스트 쿠키 설정
    document.cookie = 'test_cookie=1; samesite=lax';
    const enabled = document.cookie.includes('test_cookie');
    // 테스트 쿠키 삭제
    document.cookie = 'test_cookie=; max-age=-1';
    return enabled;
  } catch (e) {
    return false;
  }
};

/**
 * 모든 쿠키 출력 (디버깅용)
 */
export const debugCookies = () => {
  console.log('🍪 현재 쿠키 목록:');
  const cookies = document.cookie.split(';');
  cookies.forEach(cookie => {
    const [name, value] = cookie.trim().split('=');
    if (name) {
      console.log(`  - ${name}: ${value ? value.substring(0, 50) + '...' : '(empty)'}`);
    }
  });
};