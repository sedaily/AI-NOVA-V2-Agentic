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

  // 로그인 기능 비활성화 - 항상 로그인 상태로 표시
  const [userInfo, setUserInfo] = useState({ email: "guest@example.com", name: "Guest User" });
  const [userRole, setUserRole] = useState("user");
  const [isLoggedIn, setIsLoggedIn] = useState(true); // 항상 true

  useEffect(() => {
    const loadUserInfo = () => {
      try {
        const storedUserInfo = localStorage.getItem("userInfo");
        const storedUserRole = localStorage.getItem("userRole") || "user";
        const loggedIn = localStorage.getItem("isLoggedIn") === "true";

        // 로그인 비활성화 - 항상 로그인 상태로 유지
        setIsLoggedIn(true);
        setUserInfo({ email: "guest@example.com", name: "Guest User" });
        setUserRole("user");
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
            {/* 사이드바 토글 버튼 비활성화 */}

            {/* 홈 버튼 */}
            {onHome && (
              <button
                className="flex items-center space-x-2 p-2 rounded-md text-text-300 hover:bg-bg-300 hover:text-text-100 transition-colors"
                onClick={onHome}
              >
                <Home size={20} />
                <span className="hidden sm:inline text-sm font-medium">
                  AI-HUB
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
            {/* 대시보드 버튼 비활성화 */}

            {/* 사용자 메뉴 완전 제거 */}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
