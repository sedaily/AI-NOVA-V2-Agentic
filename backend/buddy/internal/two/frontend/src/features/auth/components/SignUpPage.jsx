import React, { useState } from "react";
import clsx from "clsx";
import { Home } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import authService from "../services/authService";

const SignUpPage = ({ onSignUp, onBackToLogin }) => {
  const [step, setStep] = useState("signup"); // 'signup' or 'verify'
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [verificationCode, setVerificationCode] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    // 비밀번호 일치 확인
    if (formData.password !== formData.confirmPassword) {
      setError("비밀번호가 일치하지 않습니다.");
      return;
    }

    // 비밀번호 정책 확인
    const passwordRegex =
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
    if (!passwordRegex.test(formData.password)) {
      setError(
        "비밀번호는 8자 이상이며, 대소문자, 숫자, 특수문자(~ # 제외)를 포함해야 합니다."
      );
      return;
    }

    // 이메일 형식 확인
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setError("올바른 이메일 주소를 입력해주세요.");
      return;
    }

    setIsLoading(true);

    try {
      // 회원가입 데이터 로그
      console.log("회원가입 시도:", {
        email: formData.email,
        passwordLength: formData.password.length,
      });

      // Cognito 회원가입 - 이메일을 username으로, 이름은 이메일에서 추출
      const emailName = formData.email.split("@")[0]; // 이메일에서 @ 앞부분을 이름으로 사용
      const result = await authService.signUp(
        formData.email, // username으로 이메일 사용
        formData.password,
        formData.email,
        emailName // 이메일에서 추출한 이름 사용
      );

      console.log("회원가입 결과:", result);

      if (result.success) {
        if (result.needsConfirmation) {
          // 이메일 인증이 필요한 경우
          setStep("verify");
          setSuccessMessage(
            "이메일로 인증 코드가 발송되었습니다. 인증 코드를 입력해주세요."
          );
        } else {
          // 인증이 필요 없는 경우 (자동 인증 설정 시)
          onSignUp();
        }
      } else {
        setError(result.error || "회원가입에 실패했습니다.");
      }
    } catch (err) {
      console.error("회원가입 오류:", err);
      setError("회원가입 중 오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerification = async (e) => {
    e.preventDefault();
    setError("");

    if (!verificationCode || verificationCode.length !== 6) {
      setError("6자리 인증 코드를 입력해주세요.");
      return;
    }

    setIsLoading(true);

    try {
      const result = await authService.confirmSignUp(
        formData.email,
        verificationCode
      );

      if (result.success) {
        setSuccessMessage("이메일 인증이 완료되었습니다!");

        // 자동 로그인 시도
        const loginResult = await authService.signIn(
          formData.email,
          formData.password
        );

        if (loginResult.success) {
          // 로그인 성공 - LoginPage와 동일한 형식으로 저장
          const userInfo = {
            ...loginResult.user,
            selectedEngine: "T5", // 기본값
          };

          // 사용자 정보 저장
          localStorage.setItem("userInfo", JSON.stringify(userInfo));
          localStorage.setItem("authToken", loginResult.tokens.accessToken); // accessToken 사용
          localStorage.setItem("idToken", loginResult.tokens.idToken);
          localStorage.setItem("refreshToken", loginResult.tokens.refreshToken);
          localStorage.setItem("isLoggedIn", "true");
          localStorage.setItem("selectedEngine", "T5");

          // 사용자 역할 결정 - Only ai@sedaily.com is admin
          let userRole = "user";
          if (loginResult.user.email === "ai@sedaily.com") {
            userRole = "admin";
          }
          localStorage.setItem("userRole", userRole);

          // Header에 사용자 정보 업데이트 알림
          window.dispatchEvent(new CustomEvent("userInfoUpdated"));

          onSignUp();
        } else {
          // 로그인 페이지로 이동
          setTimeout(() => {
            onBackToLogin();
          }, 2000);
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

  const handleResendCode = async () => {
    setError("");
    setSuccessMessage("");
    setIsLoading(true);

    try {
      const result = await authService.resendConfirmationCode(formData.email);

      if (result.success) {
        setSuccessMessage(result.message || "인증 코드가 재발송되었습니다.");
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

  const handleInputChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
    setError(""); // 입력 시 에러 메시지 제거
  };

  // 회원가입 폼
  if (step === "signup") {
    return (
      <motion.div
        className="min-h-screen flex items-center relative overflow-hidden"
        style={{
          background: 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)',
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          zIndex: 50
        }}
        initial={{
          x: '100%',
          filter: 'blur(20px)'
        }}
        animate={{
          x: 0,
          filter: 'blur(0px)'
        }}
        exit={{
          x: '100%',
          filter: 'blur(20px)'
        }}
        transition={{
          duration: 2.2,
          ease: [0.16, 1.0, 0.3, 1.0],
          filter: {
            duration: 1.8,
            ease: [0.22, 1.0, 0.36, 1.0]
          }
        }}
      >
        {/* 배경 - 우측에 대표 문양 (pen4) */}
        <div className="absolute inset-0 pointer-events-none" style={{ overflow: 'visible' }}>
          {/* 우측 중앙 - 대표 펜 일러스트 */}
          <div
            className="absolute top-1/2 right-[5%] transform -translate-y-1/2 w-[900px] h-[900px] opacity-[0.12]"
            style={{
              maskImage: 'linear-gradient(to left, transparent 0%, black 15%, black 100%)',
              WebkitMaskImage: 'linear-gradient(to left, transparent 0%, black 15%, black 100%)'
            }}
          >
            <img
              src="/images/illustrations/pen4.png"
              alt=""
              className="w-full h-full object-contain"
              style={{
                transform: 'rotate(-8deg)',
                filter: 'grayscale(100%) contrast(1.15) brightness(0.92)'
              }}
            />
          </div>

          {/* 우아한 그라데이션 - 우측 집중 */}
          <div
            className="absolute top-1/4 right-1/4 w-[900px] h-[900px]"
            style={{
              background: 'radial-gradient(circle, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.10) 40%, rgba(90, 103, 216, 0.05) 60%, transparent 80%)',
              filter: 'blur(120px)'
            }}
          />

          <div
            className="absolute bottom-1/3 right-1/3 w-[700px] h-[700px]"
            style={{
              background: 'radial-gradient(circle, rgba(79, 172, 254, 0.12) 0%, rgba(0, 242, 254, 0.08) 40%, rgba(102, 126, 234, 0.04) 60%, transparent 80%)',
              filter: 'blur(100px)'
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

        {/* 회원가입 카드 - 좌측 배치 */}
        <div className="w-full lg:w-1/2 px-6 sm:px-12 lg:px-20 py-20 sm:py-12 z-10">
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
              <div className="flex flex-col items-center mb-8">
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
                    className="w-48 h-48 object-contain relative z-10 transform transition-all duration-300 group-hover:scale-105"
                  />
                </div>
              </div>

              <form className="space-y-5" onSubmit={handleSubmit}>
                <div className="space-y-4">
                  {/* 이메일 입력 */}
                  <div>
                    <label
                      htmlFor="email"
                      className="block text-sm font-bold mb-2.5"
                      style={{ color: "#1a202c", letterSpacing: "-0.01em" }}
                    >
                      이메일
                    </label>
                    <input
                      id="email"
                      name="email"
                      type="email"
                      autoComplete="email"
                      required
                      value={formData.email}
                      onChange={(e) => handleInputChange("email", e.target.value)}
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
                      placeholder="이메일 주소를 입력하세요"
                    />
                  </div>

                  {/* 비밀번호 입력 */}
                  <div>
                    <label
                      htmlFor="password"
                      className="block text-sm font-bold mb-2.5"
                      style={{ color: "#1a202c", letterSpacing: "-0.01em" }}
                    >
                      비밀번호
                    </label>
                    <input
                      id="password"
                      name="password"
                      type="password"
                      autoComplete="new-password"
                      required
                      value={formData.password}
                      onChange={(e) => handleInputChange("password", e.target.value)}
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
                      placeholder="비밀번호 (8자 이상)"
                    />
                    <p className="mt-2 text-xs" style={{ color: "#718096" }}>
                      * 대소문자, 숫자, 특수문자(~ # 제외)를 포함해야 합니다
                    </p>
                  </div>

                  {/* 비밀번호 확인 입력 */}
                  <div>
                    <label
                      htmlFor="confirmPassword"
                      className="block text-sm font-bold mb-2.5"
                      style={{ color: "#1a202c", letterSpacing: "-0.01em" }}
                    >
                      비밀번호 확인
                    </label>
                    <input
                      id="confirmPassword"
                      name="confirmPassword"
                      type="password"
                      autoComplete="new-password"
                      required
                      value={formData.confirmPassword}
                      onChange={(e) => handleInputChange("confirmPassword", e.target.value)}
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
                      placeholder="비밀번호 재입력"
                    />
                  </div>
                </div>

                {/* 에러 메시지 */}
                {error && (
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
                      {error}
                    </p>
                  </div>
                )}

                {/* 성공 메시지 */}
                {successMessage && (
                  <div
                    className="rounded-xl p-4 flex items-start gap-3"
                    style={{
                      backgroundColor: "#f0fdf4",
                      border: "1px solid #86efac"
                    }}
                  >
                    <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="#22c55e" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <p className="text-sm flex-1" style={{ color: "#15803d" }}>
                      {successMessage}
                    </p>
                  </div>
                )}

                {/* 회원가입 버튼 */}
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
                  {isLoading ? "처리중..." : "회원가입"}
                </button>

                {/* 구분선 */}
                <div className="relative py-4">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t" style={{ borderColor: "#e2e8f0" }}></div>
                  </div>
                  <div className="relative flex justify-center text-xs uppercase">
                    <span className="px-3" style={{ backgroundColor: "rgba(255, 255, 255, 0.98)", color: "#a0aec0" }}>
                      또는
                    </span>
                  </div>
                </div>

                {/* 로그인 링크 */}
                <div className="text-center">
                  <span className="text-sm" style={{ color: "#718096" }}>
                    이미 계정이 있으신가요?{" "}
                  </span>
                  <button
                    type="button"
                    onClick={onBackToLogin}
                    className="text-sm font-semibold hover:underline transition-colors"
                    style={{ color: "#667eea" }}
                    onMouseEnter={(e) => e.target.style.color = "#764ba2"}
                    onMouseLeave={(e) => e.target.style.color = "#667eea"}
                  >
                    로그인
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </motion.div>
    );
  }

  // 이메일 인증 폼
  return (
    <motion.div
      className="min-h-screen flex flex-col items-center justify-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden"
      style={{
        background: 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)'
      }}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
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

      {/* 인증 카드 */}
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
            <div className="flex flex-col items-center mb-8">
              <div className="relative group">
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
                  className="w-40 h-40 object-contain relative z-10 transform transition-all duration-300 group-hover:scale-105"
                />
              </div>
              <h2
                className="mt-6 text-2xl font-bold text-center"
                style={{ color: "#1a202c" }}
              >
                이메일 인증
              </h2>
              <p
                className="mt-2 text-center text-sm"
                style={{ color: "#718096" }}
              >
                {formData.email}로 발송된<br />6자리 인증 코드를 입력해주세요
              </p>
            </div>

            <form className="space-y-5" onSubmit={handleVerification}>
              {/* 인증 코드 입력 */}
              <div>
                <label
                  htmlFor="code"
                  className="block text-sm font-bold mb-2.5"
                  style={{ color: "#1a202c", letterSpacing: "-0.01em" }}
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
                  onChange={(e) => setVerificationCode(e.target.value.replace(/[^0-9]/g, ""))}
                  className="appearance-none relative block w-full px-4 py-4 text-center text-2xl tracking-widest rounded-xl focus:outline-none transition-all duration-300"
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
                  placeholder="000000"
                />
              </div>

              {/* 에러 메시지 */}
              {error && (
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
                    {error}
                  </p>
                </div>
              )}

              {/* 성공 메시지 */}
              {successMessage && (
                <div
                  className="rounded-xl p-4 flex items-start gap-3"
                  style={{
                    backgroundColor: "#f0fdf4",
                    border: "1px solid #86efac"
                  }}
                >
                  <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="#22c55e" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <p className="text-sm flex-1" style={{ color: "#15803d" }}>
                    {successMessage}
                  </p>
                </div>
              )}

              <div className="space-y-3">
                {/* 인증하기 버튼 */}
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
                  {isLoading ? "인증 중..." : "인증하기"}
                </button>

                {/* 인증 코드 재발송 */}
                <button
                  type="button"
                  onClick={handleResendCode}
                  disabled={isLoading}
                  className="w-full text-sm hover:underline"
                  style={{ color: "#718096" }}
                >
                  인증 코드 재발송
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default SignUpPage;
