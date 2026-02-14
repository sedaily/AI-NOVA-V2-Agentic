import React, { useState, useRef, useEffect } from "react";
import {
  Menu,
  PanelLeft,
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
            {/* 사이드바 패널 버튼 (사이드바 토글) - 주석 처리 */}
            {/* {onToggleSidebar && (
              <button
                className="flex items-center justify-center p-2 rounded-md text-text-300 hover:bg-bg-300 hover:text-text-100 transition-colors"
                onClick={onToggleSidebar}
                aria-label="사이드바 토글"
              >
                <PanelLeft 
                  size={20} 
                  style={{ transform: 'scaleY(0.7)' }}
                />
              </button>
            )} */}

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
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
