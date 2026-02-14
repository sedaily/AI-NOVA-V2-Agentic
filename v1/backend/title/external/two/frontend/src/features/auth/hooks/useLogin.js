import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import authService from '../services/authService';
import { setSSOCookies } from '../../../shared/utils/cookieUtils';

export const useLogin = (propEngine) => {
  const location = useLocation();
  
  // State management
  const [formData, setFormData] = useState({
    username: "",
    password: "",
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedEngine, setSelectedEngine] = useState(propEngine || "T5");
  const [needsVerification, setNeedsVerification] = useState(false);
  const [verificationCode, setVerificationCode] = useState("");
  const [rememberMe, setRememberMe] = useState(false);

  // Initialize engine and remember me
  useEffect(() => {
    if (location.state?.engine) {
      setSelectedEngine(location.state.engine);
    } else if (propEngine) {
      setSelectedEngine(propEngine);
    }

    const savedUsername = localStorage.getItem('rememberUsername');
    if (savedUsername) {
      setFormData(prev => ({ ...prev, username: savedUsername }));
      setRememberMe(true);
    }
  }, [location, propEngine]);

  // Auto-login if Cognito session exists (for SSO from n1.sedaily.ai)
  useEffect(() => {
    const checkCognitoSession = async () => {
      try {
        console.log('🔍 로그인 페이지: Cognito 세션 확인 중...');

        // Check if already logged in via localStorage
        const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
        if (isLoggedIn) {
          console.log('✅ 이미 로그인됨 - 세션 확인 건너뜀');
          return;
        }

        // 만료된 localStorage 토큰 먼저 정리
        console.log('🧹 만료된 localStorage 토큰 정리...');
        localStorage.removeItem('authToken');
        localStorage.removeItem('idToken');
        localStorage.removeItem('refreshToken');

        // Try to get current Cognito session (Amplify가 자동으로 새 세션 가져옴)
        const session = await authService.getCurrentSession();

        if (session && session.tokens) {
          console.log('✅ Cognito 세션 발견 - 자동 로그인 시도');

          // Get user info from Cognito
          const user = await authService.getCurrentUser();

          if (user) {
            const userInfo = {
              email: user.email,
              username: user.username,
              emailVerified: user.emailVerified,
              selectedEngine: propEngine || 'T5'
            };

            // Determine user role
            let userRole = 'user';
            let userPlan = 'free';

            if (user.email === 'ai@sedaily.com') {
              userRole = 'admin';
              userPlan = 'premium';
              console.log('🔐 관리자 권한 부여 (ai@sedaily.com)');
            }

            // Store to localStorage
            localStorage.setItem('userInfo', JSON.stringify(userInfo));
            localStorage.setItem('authToken', session.tokens.accessToken);
            localStorage.setItem('idToken', session.tokens.idToken);
            localStorage.setItem('refreshToken', session.tokens.refreshToken || session.tokens.accessToken);
            localStorage.setItem('isLoggedIn', 'true');
            localStorage.setItem('userRole', userRole);
            localStorage.setItem('userPlan', userPlan);
            localStorage.setItem('ssoLogin', 'true'); // Mark as SSO login
            
            // SSO 쿠키 설정 (다른 서브도메인과 공유)
            setSSOCookies(session.tokens.idToken, session.tokens.accessToken, session.tokens.refreshToken);

            console.log('💾 Cognito 세션으로 자동 로그인 완료');
            console.log('👤 사용자:', user.email);
            console.log('🔑 역할:', userRole);

            // Dispatch events to update UI
            window.dispatchEvent(new CustomEvent('userInfoUpdated'));

            // Redirect to the engine page or return path
            const enginePath = (propEngine || 'T5') === 'T5' ? '11' : '22';
            const returnPath = location.state?.returnPath;

            if (returnPath) {
              console.log('📍 원래 경로로 리디렉션:', returnPath);
              window.location.href = returnPath;
            } else {
              console.log('📍 엔진 페이지로 리디렉션:', `/${enginePath}`);
              window.location.href = `/${enginePath}`;
            }
          }
        } else {
          console.log('ℹ️ Cognito 세션 없음 - 수동 로그인 필요');
          // 세션이 없으면 ssoLogin 플래그도 제거
          localStorage.removeItem('ssoLogin');
        }
      } catch (error) {
        console.log('ℹ️ Cognito 세션 확인 실패 (정상 - 로그인 안됨):', error.message);

        // 토큰이 만료되었거나 revoked된 경우 localStorage 정리
        if (error.name === 'NotAuthorizedException' || error.message?.includes('revoked') || error.message?.includes('expired')) {
          console.log('🧹 만료된 토큰 정리 중...');
          localStorage.removeItem('authToken');
          localStorage.removeItem('idToken');
          localStorage.removeItem('refreshToken');
          localStorage.removeItem('userInfo');
          localStorage.removeItem('isLoggedIn');
          localStorage.removeItem('userRole');
          localStorage.removeItem('userPlan');
          localStorage.removeItem('ssoLogin');
          console.log('✅ 만료된 토큰 정리 완료');
        }
      }
    };

    checkCognitoSession();
  }, [propEngine, location]);

  // Handle login submission
  const handleSubmit = async (onLoginSuccess) => {
    setError("");

    if (!formData.username || !formData.password) {
      setError("사용자명과 비밀번호를 입력해주세요.");
      return;
    }

    setIsLoading(true);

    try {
      const result = await authService.signIn(formData.username, formData.password);

      if (result.success) {
        const userInfo = {
          ...result.user,
          selectedEngine: selectedEngine
        };
        
        // Store user information
        localStorage.setItem('userInfo', JSON.stringify(userInfo));
        localStorage.setItem('authToken', result.tokens.accessToken);
        localStorage.setItem('idToken', result.tokens.idToken);
        localStorage.setItem('refreshToken', result.tokens.refreshToken);
        localStorage.setItem('isLoggedIn', 'true');
        localStorage.setItem('selectedEngine', selectedEngine);
        
        // Determine user role
        let userRole = 'user';
        let userPlan = 'free';

        // Only ai@sedaily.com is admin
        if (formData.username === 'ai@sedaily.com' || result.user.email === 'ai@sedaily.com') {
          userRole = 'admin';
          userPlan = 'premium';
        }
        
        localStorage.setItem('userRole', userRole);
        localStorage.setItem('userPlan', userPlan);
        
        // SSO 쿠키 설정 (다른 서브도메인과 공유)
        setSSOCookies(result.tokens.idToken, result.tokens.accessToken, result.tokens.refreshToken);
        console.log('🍪 SSO 쿠키 설정 완료');
        
        // Clear usage cache
        localStorage.removeItem('usage_percentage_T5');
        localStorage.removeItem('usage_percentage_time_T5');
        localStorage.removeItem('usage_percentage_C7');
        localStorage.removeItem('usage_percentage_time_C7');
        
        // Handle Remember Me
        if (rememberMe) {
          localStorage.setItem('rememberUsername', formData.username);
        } else {
          localStorage.removeItem('rememberUsername');
        }

        // Update header
        window.dispatchEvent(new CustomEvent('userInfoUpdated'));

        // Login success callback
        onLoginSuccess(userRole);
      } else {
        if (result.needsNewPassword) {
          setError("새 비밀번호를 설정해야 합니다. 관리자에게 문의하세요.");
        } else {
          setError(result.error || "로그인에 실패했습니다.");
        }
      }
    } catch (err) {
      console.error("로그인 오류:", err);
      
      if (err.name === 'UserNotConfirmedException' || err.message?.includes('not confirmed')) {
        setNeedsVerification(true);
        setError("이메일 인증이 필요합니다. 인증 코드를 입력해주세요.");
      } else {
        setError(authService.getErrorMessage(err) || "로그인 중 오류가 발생했습니다.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Handle verification
  const handleVerification = async (onLoginSuccess) => {
    setError("");

    if (!verificationCode || verificationCode.length !== 6) {
      setError("6자리 인증 코드를 입력해주세요.");
      return;
    }

    setIsLoading(true);

    try {
      const result = await authService.confirmSignUp(formData.username, verificationCode);

      if (result.success) {
        // Auto login after verification
        const loginResult = await authService.signIn(formData.username, formData.password);
        
        if (loginResult.success) {
          const userInfo = {
            ...loginResult.user,
            selectedEngine: selectedEngine
          };
          
          localStorage.setItem('userInfo', JSON.stringify(userInfo));
          localStorage.setItem('authToken', loginResult.tokens.accessToken);
          localStorage.setItem('idToken', loginResult.tokens.idToken);
          localStorage.setItem('refreshToken', loginResult.tokens.refreshToken);
          localStorage.setItem('isLoggedIn', 'true');
          
          let userRole = 'user';
          // Only ai@sedaily.com is admin
          if (formData.username === 'ai@sedaily.com' || loginResult.user.email === 'ai@sedaily.com') {
            userRole = 'admin';
          }
          localStorage.setItem('userRole', userRole);
          
          window.dispatchEvent(new CustomEvent('userInfoUpdated'));
          
          onLoginSuccess(userRole);
        } else {
          setError("인증은 완료되었지만 로그인에 실패했습니다. 다시 시도해주세요.");
          setNeedsVerification(false);
        }
      } else {
        setError(result.error || "인증에 실패했습니다.");
      }
    } catch (err) {
      console.error("인증 오류:", err);
      setError("인증 중 오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  // Handle resend code
  const handleResendCode = async () => {
    setError("");
    setIsLoading(true);

    try {
      const result = await authService.resendConfirmationCode(formData.username);
      
      if (result.success) {
        alert(result.message || "인증 코드가 재발송되었습니다.");
      } else {
        setError(result.error || "인증 코드 재발송에 실패했습니다.");
      }
    } catch (err) {
      console.error("인증 코드 재발송 오류:", err);
      setError("인증 코드 재발송 중 오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  // Handle input change
  const handleInputChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
    setError("");
  };

  const handleForgotPassword = () => {
    alert("비밀번호 재설정 기능은 준비 중입니다.\n관리자에게 문의해주세요.");
  };

  return {
    // State
    formData,
    isLoading,
    error,
    selectedEngine,
    needsVerification,
    verificationCode,
    rememberMe,
    
    // Actions
    handleSubmit,
    handleVerification,
    handleResendCode,
    handleInputChange,
    handleForgotPassword,
    setVerificationCode,
    setRememberMe,
    setNeedsVerification,
  };
};