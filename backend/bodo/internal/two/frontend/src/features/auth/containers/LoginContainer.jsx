import React from 'react';
import LoginPresenter from '../presenters/LoginPresenter';
import { useLogin } from '../hooks/useLogin';

const LoginContainer = ({ onLogin, onGoToSignUp, selectedEngine: propEngine }) => {
  const {
    formData,
    isLoading,
    error,
    selectedEngine,
    needsVerification,
    verificationCode,
    rememberMe,
    handleSubmit,
    handleVerification,
    handleResendCode,
    handleInputChange,
    handleForgotPassword,
    setVerificationCode,
    setRememberMe,
    setNeedsVerification,
  } = useLogin(propEngine);

  return (
    <LoginPresenter
      // Data
      formData={formData}
      isLoading={isLoading}
      error={error}
      selectedEngine={selectedEngine}
      needsVerification={needsVerification}
      verificationCode={verificationCode}
      rememberMe={rememberMe}
      
      // Actions
      onSubmit={(e) => {
        e.preventDefault();
        handleSubmit(onLogin);
      }}
      onVerification={(e) => {
        e.preventDefault();
        handleVerification(onLogin);
      }}
      onResendCode={handleResendCode}
      onInputChange={handleInputChange}
      onForgotPassword={handleForgotPassword}
      onVerificationCodeChange={setVerificationCode}
      onRememberMeChange={setRememberMe}
      onBackToLogin={() => setNeedsVerification(false)}
      onGoToSignUp={onGoToSignUp}
    />
  );
};

export default LoginContainer;