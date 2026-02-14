import React from 'react';
import clsx from 'clsx';
import { Home } from 'lucide-react';
import { motion } from 'framer-motion';

const LoginPresenter = ({
  // Data props
  formData,
  isLoading,
  error,
  selectedEngine,
  needsVerification,
  verificationCode,
  rememberMe,
  
  // Action props
  onSubmit,
  onVerification,
  onResendCode,
  onInputChange,
  onForgotPassword,
  onVerificationCodeChange,
  onRememberMeChange,
  onBackToLogin,
  onGoToSignUp,
}) => {
  // 이메일 인증 폼
  if (needsVerification) {
    return (
      <VerificationForm
        verificationCode={verificationCode}
        error={error}
        isLoading={isLoading}
        onSubmit={onVerification}
        onVerificationCodeChange={onVerificationCodeChange}
        onResendCode={onResendCode}
        onBackToLogin={onBackToLogin}
      />
    );
  }

  // 로그인 폼
  return (
    <LoginForm
      formData={formData}
      isLoading={isLoading}
      error={error}
      selectedEngine={selectedEngine}
      rememberMe={rememberMe}
      onSubmit={onSubmit}
      onInputChange={onInputChange}
      onForgotPassword={onForgotPassword}
      onRememberMeChange={onRememberMeChange}
      onGoToSignUp={onGoToSignUp}
    />
  );
};

// 로그인 폼 컴포넌트
const LoginForm = ({
  formData,
  isLoading,
  error,
  selectedEngine,
  rememberMe,
  onSubmit,
  onInputChange,
  onForgotPassword,
  onRememberMeChange,
  onGoToSignUp,
}) => (
  <div
    className="min-h-screen flex flex-col items-center justify-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden"
    style={{
      background: 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)'
    }}
  >
    {/* 배경 - 저널리즘의 예술 (중앙으로 모인 균형 구도) */}
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {/* 좌측 상단 - 중앙으로 */}
      <div className="absolute top-0 left-0 w-[550px] h-[550px] opacity-[0.12]">
        <img
          src="/images/illustrations/pen1.png"
          alt=""
          className="w-full h-full object-contain"
          style={{
            transform: 'rotate(-15deg) translate(10%, 10%)',
            filter: 'grayscale(100%) contrast(1.15) brightness(0.95)'
          }}
        />
      </div>

      {/* 우측 상단 - 중앙으로 */}
      <div className="absolute top-0 right-0 w-[550px] h-[550px] opacity-[0.12]">
        <img
          src="/images/illustrations/pen2.png"
          alt=""
          className="w-full h-full object-contain"
          style={{
            transform: 'rotate(15deg) translate(-10%, 10%)',
            filter: 'grayscale(100%) contrast(1.15) brightness(0.95)'
          }}
        />
      </div>

      {/* 좌측 하단 - 중앙으로 */}
      <div className="absolute bottom-0 left-0 w-[550px] h-[550px] opacity-[0.12]">
        <img
          src="/images/illustrations/pen3.png"
          alt=""
          className="w-full h-full object-contain"
          style={{
            transform: 'rotate(15deg) translate(10%, -10%)',
            filter: 'grayscale(100%) contrast(1.15) brightness(0.95)'
          }}
        />
      </div>

      {/* 우측 하단 - 중앙으로 */}
      <div className="absolute bottom-0 right-0 w-[550px] h-[550px] opacity-[0.12]">
        <img
          src="/images/illustrations/pen4.png"
          alt=""
          className="w-full h-full object-contain"
          style={{
            transform: 'rotate(-15deg) translate(-10%, -10%)',
            filter: 'grayscale(100%) contrast(1.15) brightness(0.95)'
          }}
        />
      </div>

      {/* 우아한 그라데이션 - 깊이와 공간감 (강화) */}
      <div
        className="absolute top-1/4 right-1/4 w-[750px] h-[750px]"
        style={{
          background: 'radial-gradient(circle, rgba(102, 126, 234, 0.12) 0%, rgba(118, 75, 162, 0.08) 40%, rgba(90, 103, 216, 0.04) 60%, transparent 80%)',
          filter: 'blur(100px)'
        }}
      />

      <div
        className="absolute bottom-1/4 left-1/4 w-[700px] h-[700px]"
        style={{
          background: 'radial-gradient(circle, rgba(79, 172, 254, 0.10) 0%, rgba(0, 242, 254, 0.06) 40%, rgba(102, 126, 234, 0.03) 60%, transparent 80%)',
          filter: 'blur(100px)'
        }}
      />

      <div
        className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px]"
        style={{
          background: 'radial-gradient(circle, rgba(118, 75, 162, 0.08) 0%, rgba(102, 126, 234, 0.04) 50%, transparent 70%)',
          filter: 'blur(80px)'
        }}
      />

    </div>

    {/* 홈 버튼 - 세련된 디자인 */}
    <a
      href="/"
      className="absolute top-6 sm:top-8 left-6 sm:left-8 flex items-center gap-2 px-4 sm:px-5 py-2.5 rounded-xl transition-all hover:scale-105 z-10 group"
      style={{
        backgroundColor: "rgba(255, 255, 255, 0.9)",
        color: "#4a5568",
        border: "1px solid rgba(226, 232, 240, 0.8)",
        boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)"
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = "0 4px 12px rgba(0, 0, 0, 0.08)";
        e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 1)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = "0 2px 8px rgba(0, 0, 0, 0.04)";
        e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.9)";
      }}
    >
      <Home size={18} className="transition-transform group-hover:-translate-x-0.5" />
      <span className="font-medium text-sm hidden sm:inline">홈으로</span>
    </a>

    {/* 로그인 카드 */}
    <div className="max-w-md w-full z-10">
      <div
        className="rounded-2xl shadow-xl overflow-hidden transform transition-all duration-300 hover:shadow-2xl"
        style={{
          backgroundColor: "rgba(255, 255, 255, 0.98)",
          backdropFilter: "blur(25px)",
          border: "1px solid rgba(255, 255, 255, 0.9)",
          boxShadow: "0 10px 40px rgba(0, 0, 0, 0.08), 0 4px 12px rgba(102, 126, 234, 0.05), 0 0 1px rgba(0, 0, 0, 0.1)"
        }}
      >
        <div className="p-8 sm:p-10">
          {/* 로고 섹션 */}
          <div className="flex flex-col items-center mb-10">
            <div className="relative group">
              {/* 로고 배경 glow 효과 */}
              <div
                className="absolute inset-0 rounded-full blur-3xl opacity-0 group-hover:opacity-30 transition-opacity duration-500"
                style={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  transform: 'scale(1.5)'
                }}
              />
              <img
                src="/images/ainova.png"
                alt="AI NOVA Logo"
                className="w-56 h-56 object-contain relative z-10 transform transition-all duration-300 group-hover:scale-105"
              />
            </div>
          </div>

      <form className="space-y-5" onSubmit={onSubmit}>
        <div className="space-y-4">
          <InputField
            id="username"
            label="이메일"
            type="text"
            value={formData.username}
            onChange={(e) => onInputChange("username", e.target.value)}
            autoComplete="username"
            placeholder="이메일 주소를 입력하세요"
          />

          <InputField
            id="password"
            label="비밀번호"
            type="password"
            value={formData.password}
            onChange={(e) => onInputChange("password", e.target.value)}
            autoComplete="current-password"
            placeholder="비밀번호를 입력하세요"
          />
        </div>

        {error && <ErrorMessage message={error} />}

        <SubmitButton isLoading={isLoading} text={isLoading ? "로그인 중..." : "로그인"} />

        {/* 구분선 */}
        <div className="relative py-4">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t" style={{ borderColor: "#e2e8f0" }}></div>
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="px-3" style={{ backgroundColor: "rgba(255, 255, 255, 0.95)", color: "#a0aec0" }}>
              또는
            </span>
          </div>
        </div>

        {/* 회원가입 */}
        <div className="text-center">
          <span className="text-sm" style={{ color: "#718096" }}>
            아직 계정이 없으신가요?{" "}
          </span>
          <button
            type="button"
            className="text-sm font-semibold hover:underline transition-colors"
            style={{ color: "#667eea" }}
            onClick={onGoToSignUp}
            onMouseEnter={(e) => e.target.style.color = "#764ba2"}
            onMouseLeave={(e) => e.target.style.color = "#667eea"}
          >
            회원가입
          </button>
        </div>
      </form>
        </div>
      </div>
    </div>
  </div>
);

// 인증 폼 컴포넌트
const VerificationForm = ({
  verificationCode,
  error,
  isLoading,
  onSubmit,
  onVerificationCodeChange,
  onResendCode,
  onBackToLogin,
}) => (
  <div
    className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8"
    style={{ backgroundColor: "hsl(var(--bg-100))" }}
  >
    <div className="max-w-md w-full space-y-8">
      <div>
        <h2
          className="mt-6 text-center text-3xl font-extrabold"
          style={{ color: "hsl(var(--text-100))" }}
        >
          이메일 인증
        </h2>
        <p className="mt-2 text-center text-sm" style={{ color: "hsl(var(--text-300))" }}>
          등록된 이메일로 발송된 6자리 인증 코드를 입력해주세요
        </p>
      </div>
      <form className="mt-8 space-y-6" onSubmit={onSubmit}>
        <div>
          <label
            htmlFor="code"
            className="block text-sm font-medium mb-1"
            style={{ color: "hsl(var(--text-200))" }}
          >
            인증 코드
          </label>
          <input
            id="code"
            name="code"
            type="text"
            maxLength="6"
            required
            value={verificationCode}
            onChange={(e) => onVerificationCodeChange(e.target.value.replace(/[^0-9]/g, ''))}
            className="appearance-none relative block w-full px-3 py-2 text-center text-2xl tracking-widest rounded-md focus:outline-none focus:ring-2"
            style={{
              backgroundColor: "hsl(var(--bg-000))",
              border: "0.5px solid hsl(var(--border-300)/0.15)",
              color: "hsl(var(--text-100))",
            }}
            placeholder="000000"
          />
        </div>

        {error && <ErrorMessage message={error} />}

        <div className="space-y-3">
          <SubmitButton isLoading={isLoading} text={isLoading ? "인증 중..." : "인증하기"} />

          <button
            type="button"
            onClick={onResendCode}
            disabled={isLoading}
            className="w-full text-sm hover:underline"
            style={{ color: "hsl(var(--text-300))" }}
          >
            인증 코드 재발송
          </button>

          <button
            type="button"
            onClick={onBackToLogin}
            className="w-full text-sm hover:underline"
            style={{ color: "hsl(var(--text-300))" }}
          >
            로그인 화면으로 돌아가기
          </button>
        </div>
      </form>
    </div>
  </div>
);

// 입력 필드 컴포넌트
const InputField = ({ id, label, type, value, onChange, autoComplete, placeholder }) => (
  <div>
    <label
      htmlFor={id}
      className="block text-sm font-bold mb-2.5"
      style={{ color: "#1a202c", letterSpacing: "-0.01em" }}
    >
      {label}
    </label>
    <input
      id={id}
      name={id}
      type={type}
      autoComplete={autoComplete}
      required
      value={value}
      onChange={onChange}
      className="appearance-none relative block w-full px-4 py-4 rounded-xl focus:outline-none text-base transition-all duration-300"
      style={{
        backgroundColor: "#ffffff",
        border: "2px solid #e2e8f0",
        color: "#2d3748",
        boxShadow: "0 2px 4px rgba(0, 0, 0, 0.02)"
      }}
      onFocus={(e) => {
        e.target.style.borderColor = "#667eea";
        e.target.style.boxShadow = "0 0 0 4px rgba(102, 126, 234, 0.12), 0 4px 12px rgba(102, 126, 234, 0.08)";
        e.target.style.backgroundColor = "#ffffff";
        e.target.style.transform = "translateY(-1px)";
      }}
      onBlur={(e) => {
        e.target.style.borderColor = "#e2e8f0";
        e.target.style.boxShadow = "0 2px 4px rgba(0, 0, 0, 0.02)";
        e.target.style.backgroundColor = "#ffffff";
        e.target.style.transform = "translateY(0)";
      }}
      placeholder={placeholder}
    />
  </div>
);

// 에러 메시지 컴포넌트
const ErrorMessage = ({ message }) => (
  <div
    className="rounded-xl p-4 flex items-start gap-3"
    style={{
      backgroundColor: "#fff5f5",
      border: "1px solid #feb2b2"
    }}
  >
    <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="#f56565" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
    </svg>
    <p className="text-sm flex-1" style={{ color: "#c53030" }}>
      {message}
    </p>
  </div>
);

// 제출 버튼 컴포넌트
const SubmitButton = ({ isLoading, text }) => (
  <button
    type="submit"
    disabled={isLoading}
    className={clsx(
      "group relative w-full flex justify-center items-center py-4 px-4 text-base font-bold rounded-xl focus:outline-none transition-all duration-300",
      isLoading
        ? "opacity-70 cursor-not-allowed"
        : "hover:shadow-2xl active:scale-[0.98]"
    )}
    style={{
      background: isLoading
        ? "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
        : "linear-gradient(135deg, #5a67d8 0%, #667eea 50%, #764ba2 100%)",
      color: "white",
      border: "none",
      boxShadow: isLoading
        ? "0 4px 14px rgba(102, 126, 234, 0.3)"
        : "0 6px 20px rgba(102, 126, 234, 0.45), 0 2px 8px rgba(118, 75, 162, 0.2)",
      backgroundSize: "200% 100%",
      backgroundPosition: "left center"
    }}
    onMouseEnter={(e) => {
      if (!isLoading) {
        e.target.style.transform = "translateY(-2px)";
        e.target.style.boxShadow = "0 12px 35px rgba(102, 126, 234, 0.55), 0 4px 16px rgba(118, 75, 162, 0.3)";
        e.target.style.backgroundPosition = "right center";
      }
    }}
    onMouseLeave={(e) => {
      if (!isLoading) {
        e.target.style.transform = "translateY(0)";
        e.target.style.boxShadow = "0 6px 20px rgba(102, 126, 234, 0.45), 0 2px 8px rgba(118, 75, 162, 0.2)";
        e.target.style.backgroundPosition = "left center";
      }
    }}
  >
    {isLoading && (
      <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
    )}
    {text}
  </button>
);

export default LoginPresenter;