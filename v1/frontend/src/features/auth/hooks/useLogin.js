import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import authService from '../services/authService';
import { ADMIN_EMAIL, COMPANY_DOMAIN } from '../../../config';

export const useLogin = (propEngine) => {
  const location = useLocation();
  
  // State management
  const [formData, setFormData] = useState({
    username: "",
    password: "",
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedEngine, setSelectedEngine] = useState(propEngine || "11");
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

        if (formData.username === ADMIN_EMAIL || result.user.email === ADMIN_EMAIL) {
          console.log('🔐 Admin email matched:', ADMIN_EMAIL);
          userRole = 'admin';
          userPlan = 'premium';
        }

        console.log('🔐 Final userRole:', userRole);
        localStorage.setItem('userRole', userRole);
        localStorage.setItem('userPlan', userPlan);
        
        // Clear usage cache
        localStorage.removeItem('usage_percentage_11');
        localStorage.removeItem('usage_percentage_time_11');
        localStorage.removeItem('usage_percentage_22');
        localStorage.removeItem('usage_percentage_time_22');
        
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
          let userPlan = 'free';
          if (formData.username === ADMIN_EMAIL || loginResult.user.email === ADMIN_EMAIL) {
            userRole = 'admin';
            userPlan = 'premium';
          }
          localStorage.setItem('userRole', userRole);
          localStorage.setItem('userPlan', userPlan);
          
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