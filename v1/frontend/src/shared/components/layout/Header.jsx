import React, { useState, useRef, useEffect } from "react";
import { PanelLeft, Home, User, ChevronDown, LogOut } from "lucide-react";

const Header = ({ onToggleSidebar, onHome, onLogout }) => {
  const [showUserDropdown, setShowUserDropdown] = useState(false);
  const userDropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (userDropdownRef.current && !userDropdownRef.current.contains(event.target)) {
        setShowUserDropdown(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);
  return (
    <header
      className="sticky top-0 z-50 w-full transition-all duration-200"
      style={{
        backdropFilter: "blur(12px)",
        backgroundColor: "hsl(var(--bg-100)/0.95)",
      }}
    >
      <div className="w-full px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 relative">
          <div className="flex items-center space-x-4">
            {onToggleSidebar && (
              <button
                className="flex items-center justify-center p-2 rounded-md text-text-300 hover:bg-bg-300 hover:text-text-100 transition-colors"
                onClick={onToggleSidebar}
                aria-label="사이드바 토글"
              >
                <PanelLeft size={20} style={{ transform: 'scaleY(0.7)' }} />
              </button>
            )}

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

          <div className="ml-auto flex items-center space-x-4">
            <div className="relative" ref={userDropdownRef}>
              <button
                onClick={() => setShowUserDropdown(!showUserDropdown)}
                className="flex items-center space-x-2 p-2 rounded-md text-text-300 hover:bg-bg-300 hover:text-text-100 transition-colors"
              >
                <User size={20} />
                <ChevronDown size={16} />
              </button>
              
              {showUserDropdown && (
                <div className="absolute right-0 mt-2 w-48 bg-bg-100 rounded-lg shadow-lg border border-bg-300 py-1 z-50">
                  <button
                    onClick={() => {
                      setShowUserDropdown(false);
                      onLogout && onLogout();
                    }}
                    className="w-full text-left px-4 py-2 text-sm hover:bg-bg-200 transition-colors flex items-center gap-2"
                  >
                    <LogOut size={16} />
                    로그아웃
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
