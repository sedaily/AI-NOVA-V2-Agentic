import React from "react";
import clsx from "clsx";
import { Home } from "lucide-react";

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
      background: `linear-gradient(135deg, hsl(var(--bg-100)) 0%, hsl(var(--bg-200)) 50%, hsl(var(--bg-100)) 100%)`,
    }}
  >
    {/* 배경 장식 요소 */}
    <div className="absolute inset-0 overflow-hidden">
      <div
        className="absolute -top-40 -right-40 w-80 h-80 rounded-full opacity-5"
        style={{
          background: `radial-gradient(circle, hsl(var(--accent-main-000)), transparent)`,
        }}
      />
      <div
        className="absolute -bottom-40 -left-40 w-80 h-80 rounded-full opacity-5"
        style={{
          background: `radial-gradient(circle, hsl(var(--accent-main-000)), transparent)`,
        }}
      />
    </div>

    {/* 홈 버튼 - 모바일 반응형 개선 */}
    <a
      href="/"
      className="absolute top-4 sm:top-8 left-4 sm:left-8 flex items-center gap-2 px-3 sm:px-4 py-2 rounded-full backdrop-blur-sm transition-all hover:scale-105 z-10"
      style={{
        backgroundColor: "hsl(var(--bg-200)/0.8)",
        color: "hsl(var(--text-200))",
        border: "1px solid hsl(var(--bg-300)/0.3)",
      }}
    >
      <Home size={18} />
      <span className="font-medium text-sm hidden sm:inline">홈으로</span>
    </a>

    <div className="max-w-md w-full z-10">
      <div className="p-10 space-y-8">
        <div>
          <div className="flex flex-col items-center">
            <div className="mb-6 relative group">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full blur-lg opacity-5 group-hover:opacity-10 transition-opacity" />
              <img
                src="/images/logo.png"
                alt="Logo"
                className="w-32 h-32 object-contain relative z-10 transform transition-transform group-hover:scale-105"
              />
            </div>
            <div
              className="px-6 py-2.5 rounded-full mb-6 backdrop-blur-sm animate-pulse"
              style={{
                background: `linear-gradient(135deg, hsl(var(--accent-main-000))/15, hsl(var(--accent-main-000))/5)`,
                border: "1px solid hsl(var(--accent-main-000))/30",
                boxShadow: "0 4px 15px hsl(var(--accent-main-000))/10",
              }}
            >
              <span
                className="text-lg font-bold tracking-wide"
                style={{ color: "hsl(var(--accent-main-000))" }}
              >
                {selectedEngine} ENGINE
              </span>
            </div>
          </div>
          <a
            href="/"
            className="block text-center text-3xl font-extrabold tracking-tight hover:opacity-90 transition-all mb-2"
            style={{
              color: "hsl(var(--text-100))",
              textDecoration: "none",
              textShadow: "0 2px 4px hsl(var(--always-black)/0.1)",
            }}
          >
            COLUMN-HUB
          </a>
          <p
            className="text-center text-xs tracking-widest uppercase opacity-60 mb-4"
            style={{ color: "hsl(var(--text-300))" }}
          >
            AI Column Generator
          </p>
          <p
            className="mt-2 text-center text-sm"
            style={{ color: "hsl(var(--text-400))" }}
          >
            <span className="block md:inline">AI 기반 칼럼 작성 서비스에</span>
            <span className="block md:inline md:ml-1">
              오신 것을 환영합니다
            </span>
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={onSubmit}>
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

          <SubmitButton
            isLoading={isLoading}
            text={isLoading ? "로그인 중..." : "로그인"}
          />

          <div className="text-center">
            <span className="text-sm" style={{ color: "hsl(var(--text-300))" }}>
              아직 계정이 없으신가요?{" "}
            </span>
            <button
              type="button"
              className="text-sm font-medium hover:underline"
              style={{ color: "hsl(var(--accent-main-100))" }}
              onClick={onGoToSignUp}
            >
              회원가입
            </button>
          </div>
        </form>
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
        <p
          className="mt-2 text-center text-sm"
          style={{ color: "hsl(var(--text-300))" }}
        >
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
            onChange={(e) =>
              onVerificationCodeChange(e.target.value.replace(/[^0-9]/g, ""))
            }
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
          <SubmitButton
            isLoading={isLoading}
            text={isLoading ? "인증 중..." : "인증하기"}
          />

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
const InputField = ({
  id,
  label,
  type,
  value,
  onChange,
  autoComplete,
  placeholder,
}) => (
  <div>
    <label
      htmlFor={id}
      className="block text-sm font-medium mb-2"
      style={{ color: "hsl(var(--text-200))" }}
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
      className="appearance-none relative block w-full px-4 py-3 rounded-lg focus:outline-none focus:z-10 text-sm transition-all duration-200"
      style={{
        backgroundColor: "hsl(var(--bg-100))",
        border: "1px solid hsl(var(--bg-300))",
        color: "hsl(var(--text-100))",
      }}
      onFocus={(e) => {
        e.target.style.borderColor = "hsl(var(--accent-main-100))";
        e.target.style.boxShadow = "0 0 0 3px hsl(var(--accent-main-100)/0.1)";
        e.target.style.backgroundColor = "hsl(var(--bg-000))";
      }}
      onBlur={(e) => {
        e.target.style.borderColor = "hsl(var(--bg-300))";
        e.target.style.boxShadow = "none";
        e.target.style.backgroundColor = "hsl(var(--bg-100))";
      }}
      placeholder={placeholder}
    />
  </div>
);

// 에러 메시지 컴포넌트
const ErrorMessage = ({ message }) => (
  <div
    className="rounded-md p-4"
    style={{ backgroundColor: "hsl(var(--danger-100))" }}
  >
    <p className="text-sm" style={{ color: "hsl(var(--danger-000))" }}>
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
      "group relative w-full flex justify-center py-3 px-4 text-base font-semibold rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2 transition-all duration-200",
      isLoading
        ? "opacity-50 cursor-not-allowed"
        : "hover:scale-[1.01] active:scale-[0.99] hover:shadow-lg"
    )}
    style={{
      backgroundColor: "hsl(var(--accent-main-000))",
      color: "white",
      border: "none",
      boxShadow:
        "0 4px 6px -1px hsl(var(--always-black)/0.1), 0 2px 4px -1px hsl(var(--always-black)/0.06)",
    }}
    onMouseEnter={(e) => {
      if (!isLoading) {
        e.target.style.backgroundColor = "hsl(var(--accent-main-200))";
        e.target.style.transform = "translateY(-1px)";
      }
    }}
    onMouseLeave={(e) => {
      if (!isLoading) {
        e.target.style.backgroundColor = "hsl(var(--accent-main-000))";
        e.target.style.transform = "translateY(0)";
      }
    }}
  >
    {text}
  </button>
);

export default LoginPresenter;
