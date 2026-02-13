import React, { useState, useRef, useEffect } from "react";
import {
  Menu,
  BarChart3,
  ChevronDown,
  User,
  CreditCard,
  LogOut,
  Home,
} from "lucide-react";
import clsx from "clsx";

const Header = ({
  onLogout,
  onAdminLogin,
  onHome,
  chatTitle,
  onToggleSidebar,
  isSidebarOpen = false,
  onDashboard,
  selectedEngine,
  usagePercentage,
  isLandingPage = false,
}) => {
  const [showUserDropdown, setShowUserDropdown] = useState(false);
  const userDropdownRef = useRef(null);

  // 사용자 정보 가져오기
  const [userInfo, setUserInfo] = useState(null);
  const [userRole, setUserRole] = useState("user");
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const loadUserInfo = () => {
      try {
        const storedUserInfo = localStorage.getItem("userInfo");
        const storedUserRole = localStorage.getItem("userRole") || "user";
        const loggedIn = localStorage.getItem("isLoggedIn") === "true";

        setIsLoggedIn(loggedIn);

        if (storedUserInfo && loggedIn) {
          const parsed = JSON.parse(storedUserInfo);
          setUserInfo(parsed);
          setUserRole(storedUserRole);
        } else {
          // 로그아웃 상태면 정보 초기화
          setUserInfo(null);
          setUserRole("user");
        }
      } catch (error) {
        console.error("사용자 정보 로드 실패:", error);
        setUserInfo(null);
        setUserRole("user");
        setIsLoggedIn(false);
      }
    };

    loadUserInfo();

    // localStorage 변경 감지와 커스텀 이벤트 리스너
    const handleStorageChange = () => {
      loadUserInfo();
    };

    const handleUserInfoUpdate = () => {
      loadUserInfo();
    };

    window.addEventListener("storage", handleStorageChange);
    window.addEventListener("userInfoUpdated", handleUserInfoUpdate);

    return () => {
      window.removeEventListener("storage", handleStorageChange);
      window.removeEventListener("userInfoUpdated", handleUserInfoUpdate);
    };
  }, []);

  // 외부 클릭 시 사용자 드롭다운 닫기
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        userDropdownRef.current &&
        !userDropdownRef.current.contains(event.target)
      ) {
        setShowUserDropdown(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const handleUserMenuClick = (action) => {
    console.log(`사용자 메뉴: ${action}`);
    setShowUserDropdown(false);

    if (action === "logout" && onLogout) {
      onLogout();
    } else if (action === "dashboard" && onDashboard) {
      onDashboard();
    } else if (action === "dashboard" && onAdminLogin) {
      onAdminLogin();
    } else if (action === "subscription") {
      // 구독 플랜 페이지로 이동
      window.location.href = "/subscription";
    } else if (action === "profile") {
      // 프로필 페이지로 이동
      window.location.href = "/profile";
    }
  };

  return (
    <header
      className={`sticky top-0 z-50 w-full transition-all duration-200 ${
        isLandingPage ? "border-b border-gray-800" : ""
      }`}
      style={{
        backdropFilter: "blur(12px)",
        backgroundColor: isLandingPage
          ? "rgba(15, 15, 15, 0.95)"
          : "hsl(var(--bg-100)/0.95)",
      }}
    >
      <div className="w-full px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 relative">
          <div className="flex items-center space-x-4">
            {/* 사이드바 토글 버튼 - 사이드바가 닫혀있을 때만 표시 */}
            {onToggleSidebar && !isSidebarOpen && (
              <button
                className="p-2 rounded-md text-text-300 hover:bg-bg-300 hover:text-text-100 transition-colors"
                onClick={onToggleSidebar}
                aria-label="사이드바 열기"
              >
                <Menu size={24} />
              </button>
            )}

            {/* 홈 버튼 */}
            {onHome && (
              <button
                className="flex items-center space-x-2 p-2 rounded-md text-text-300 hover:bg-bg-300 hover:text-text-100 transition-colors"
                onClick={onHome}
              >
                <Home size={20} />
                <span className="hidden sm:inline text-sm font-medium">
                  COLUMN-HUB
                </span>
              </button>
            )}
          </div>

          {/* 채팅 제목 (가운데) */}
          {chatTitle && (
            <div className="flex-1 flex justify-center mx-4">
              <h1 className="text-text-100 font-medium text-sm lg:text-base truncate max-w-md">
                {chatTitle}
              </h1>
            </div>
          )}

          <div className="ml-auto flex items-center space-x-4">
            {/* 사용량 표시 - 비활성화됨 */}
            {/* {selectedEngine && usagePercentage !== undefined && usagePercentage !== null && (
              <div className="flex items-center space-x-2 px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg" 
                   style={{ backgroundColor: "hsl(var(--bg-200)/0.8)", backdropFilter: "blur(8px)" }}>
                <span className="text-xs text-text-300 font-medium hidden sm:inline">
                  {selectedEngine} 사용량
                </span>
                <span className="text-xs text-text-300 font-medium sm:hidden">
                  {selectedEngine}
                </span>
                <div className="flex items-center space-x-2">
                  <div 
                    className="w-16 sm:w-24 h-1.5 sm:h-2 rounded-full overflow-hidden"
                    style={{ backgroundColor: "hsl(var(--bg-300))" }}
                  >
                    <div
                      className={clsx(
                        "h-full transition-all duration-500 ease-out rounded-full",
                        usagePercentage > 80
                          ? "bg-red-500"
                          : usagePercentage > 50
                          ? "bg-yellow-500"
                          : "bg-green-500"
                      )}
                      style={{ width: `${Math.min(usagePercentage, 100)}%` }}
                    />
                  </div>
                  <span
                    className={clsx(
                      "text-sm font-bold min-w-[40px] text-right",
                      usagePercentage > 80
                        ? "text-red-500"
                        : usagePercentage > 50
                        ? "text-yellow-500"
                        : "text-green-500"
                    )}
                  >
                    {usagePercentage || 0}%
                  </span>
                </div>
              </div>
            )} */}
            {onDashboard && (
              <div className="hidden md:block">
                <button
                  className="flex items-center space-x-2 px-5 py-3 rounded-lg text-sm font-semibold transition-all duration-200 text-text-300 hover:bg-bg-300 hover:text-text-100"
                  onClick={() => handleUserMenuClick("dashboard")}
                >
                  <BarChart3 size={20} />
                  <span>대시보드</span>
                </button>
              </div>
            )}

            {isLoggedIn && userInfo ? (
              <div className="relative" ref={userDropdownRef}>
                <button
                  className="flex items-center space-x-2 p-2 rounded-full hover:bg-bg-300 transition-colors duration-200"
                  aria-expanded={showUserDropdown}
                  aria-haspopup="true"
                  onClick={() => setShowUserDropdown(!showUserDropdown)}
                >
                  <div
                    className="w-8 h-8 rounded-full flex items-center justify-center text-white font-medium text-sm"
                    style={{ backgroundColor: "hsl(var(--accent-main-000))" }}
                  >
                    {userInfo?.name
                      ? userInfo.name.charAt(0).toUpperCase()
                      : userInfo?.email
                      ? userInfo.email.charAt(0).toUpperCase()
                      : "U"}
                  </div>
                  <ChevronDown
                    size={16}
                    className={clsx(
                      "text-text-500 transition-transform duration-200",
                      showUserDropdown ? "rotate-180" : ""
                    )}
                  />
                </button>

                {/* User Dropdown */}
                {showUserDropdown && (
                  <div
                    className="absolute right-0 mt-2 w-64 rounded-lg py-2 z-50"
                    style={{
                      backgroundColor: "hsl(var(--bg-000))",
                      border: "1px solid hsl(var(--bg-300))",
                      boxShadow:
                        "0 0.25rem 1.25rem hsl(var(--always-black)/15%), 0 0 0 0.5px hsla(var(--bg-300)/0.5)",
                    }}
                  >
                    <div
                      className="px-4 py-3 border-b"
                      style={{ borderColor: "hsl(var(--bg-300))" }}
                    >
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-accent-main-000 rounded-full flex items-center justify-center text-white font-medium">
                          {userInfo?.name
                            ? userInfo.name.charAt(0).toUpperCase()
                            : userInfo?.email
                            ? userInfo.email.charAt(0).toUpperCase()
                            : "U"}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-text-100 truncate">
                            {userInfo?.name || userInfo?.username || "사용자"}
                          </p>
                          <p className="text-xs text-text-300 truncate">
                            {userInfo?.email || "이메일 없음"}
                          </p>
                          <span
                            className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium mt-1"
                            style={{
                              backgroundColor:
                                userRole === "admin"
                                  ? "hsl(var(--success-000)/0.1)"
                                  : "hsl(var(--accent-main-000)/0.1)",
                              color:
                                userRole === "admin"
                                  ? "hsl(var(--success-000))"
                                  : "hsl(var(--accent-main-000))",
                            }}
                          >
                            {userRole === "admin" ? "관리자" : "사용자"}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="py-1">
                      {onDashboard && (
                        <button
                          className="flex items-center px-4 py-2 text-sm text-text-200 hover:bg-bg-200 w-full text-left transition-colors duration-150 md:hidden"
                          onClick={() => handleUserMenuClick("dashboard")}
                        >
                          <BarChart3 className="h-4 w-4 mr-3" />
                          대시보드
                        </button>
                      )}
                      <button
                        className="flex items-center px-4 py-2 text-sm text-text-200 hover:bg-bg-200 w-full text-left transition-colors duration-150"
                        onClick={() => handleUserMenuClick("profile")}
                      >
                        <User className="h-4 w-4 mr-3" />
                        프로필
                      </button>
                      <button
                        className="flex items-center px-4 py-2 text-sm text-text-200 hover:bg-bg-200 w-full text-left transition-colors duration-150"
                        onClick={() => handleUserMenuClick("subscription")}
                      >
                        <CreditCard className="h-4 w-4 mr-3" />
                        구독 플랜
                      </button>
                    </div>
                    <div
                      className="border-t my-1"
                      style={{ borderColor: "hsl(var(--bg-300))" }}
                    ></div>
                    <button
                      onClick={() => handleUserMenuClick("logout")}
                      className="flex items-center px-4 py-2 text-sm w-full text-left transition-colors duration-150"
                      style={{ color: "hsl(var(--danger-000))" }}
                    >
                      <LogOut className="h-4 w-4 mr-3" />
                      로그아웃
                    </button>
                  </div>
                )}
              </div>
            ) : (
              // 로그아웃 상태일 때 로그인 버튼 표시
              <button
                onClick={() => (window.location.href = "/login")}
                className="flex items-center space-x-2 px-4 py-2 bg-accent-main-000 text-white rounded-lg hover:bg-accent-main-100 transition-colors duration-200 font-medium text-sm"
              >
                <LogOut size={16} className="rotate-180" />
                <span>로그인</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
