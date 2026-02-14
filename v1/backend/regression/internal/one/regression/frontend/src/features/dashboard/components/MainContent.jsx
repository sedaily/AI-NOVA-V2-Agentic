import React, { useState, useRef, useEffect } from "react";
import { MoreHorizontal, Star, Edit3 } from "lucide-react";
import clsx from "clsx";
import ChatInput from "../../chat/components/ChatInput";
import PromptManagePanel from "./PromptManagePanel";
import C1C2GuideSection from "./C1C2GuideSection";
import Header from "../../../shared/components/layout/Header";
import * as promptService from "../../../shared/utils/promptService";
import usageService from "../../chat/services/usageService";

const MainContent = ({
  project,
  userRole,
  selectedEngine = "11",
  onToggleStar,
  onStartChat,
  onLogout,
  onBackToLanding,
  onToggleSidebar,
  isSidebarOpen = false,
  onDashboard,
}) => {
  const [showDropdown, setShowDropdown] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editTitle, setEditTitle] = useState(project.title);
  const [editDescription, setEditDescription] = useState("");
  const [currentDescription, setCurrentDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [usagePercentage, setUsagePercentage] = useState(() => {
    const cachedValue = localStorage.getItem(
      `usage_percentage_${selectedEngine}`
    );
    return cachedValue ? parseInt(cachedValue) : 0;
  });

  const dropdownRef = useRef(null);
  const dragCounterRef = useRef(0);
  const chatInputRef = useRef(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const data = await promptService.getPrompt(selectedEngine);
        if (data.prompt) {
          setCurrentDescription(data.prompt.description || "");
          setEditDescription(data.prompt.description || "");
        }

        localStorage.removeItem(`usage_percentage_${selectedEngine}`);
        localStorage.removeItem(`usage_percentage_time_${selectedEngine}`);

        const percentage = await usageService.getUsagePercentage(
          selectedEngine,
          true
        );
        setUsagePercentage(percentage);

        window.dispatchEvent(new CustomEvent("usageUpdated"));
      } catch (error) {
        console.error("Failed to load data:", error);
      }
    };
    loadData();
  }, [selectedEngine]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleTitlesGenerated = () => {};

  return (
    <div className="min-h-screen flex flex-col">
      <Header
        onLogout={onLogout}
        onHome={onBackToLanding}
        onToggleSidebar={onToggleSidebar}
        isSidebarOpen={isSidebarOpen}
        onDashboard={onDashboard}
        selectedEngine={selectedEngine}
        usagePercentage={usagePercentage}
      />

      <main
        className={clsx(
          "mx-auto mt-4 w-full flex-1 lg:mt-6 flex gap-6",
          userRole === "admin"
            ? "max-w-7xl flex-col xl:flex-row px-6 lg:px-8"
            : "max-w-none flex-col px-4 lg:px-6"
        )}
      >
        <div className="flex-1 flex flex-col gap-4">

          {/* ================= HERO SECTION (✅ 수정) ================= */}
          {userRole === "user" && (
            <section className="mt-40 mb-10 flex items-center justify-center gap-4">
              <img
                src="/images/ainova.png"
                alt="AI NOVA"
                className="w-20 h-16"
              />
              <h1 
                className="text-3xl md:text-4xl font-light text-text-200"
                style={{ 
                  fontFamily: '"Tiempos Text", "Source Serif 4", "Noto Serif KR", serif',
                  fontSize: 'calc(1.875rem + 8px)' // text-3xl (30px) + 8px = 38px
                }}
              >
                안녕하세요, 기자님
              </h1>
            </section>
          )}
          {/* ========================================================== */}

          <div
            className={clsx(
              "flex flex-col gap-3 max-md:pt-4 -mt-4 w-full",
              userRole === "admin"
                ? "items-start max-w-none"
                : "items-center max-w-none mx-auto"
            )}
          >
            {/* ================= ADMIN HEADER (기존 그대로) ================= */}
            {userRole === "admin" && (
              <div className="flex items-start gap-3 w-full">
                <h1 className="flex-1 text-left text-text-200 text-xl">
                  {project.title}
                </h1>

                <div className="flex items-center gap-1 ml-auto">
                  <div className="relative" ref={dropdownRef}>
                    <button onClick={() => setShowDropdown(!showDropdown)}>
                      <MoreHorizontal size={20} />
                    </button>

                    {showDropdown && (
                      <div className="absolute right-0 mt-2 z-50">
                        <button onClick={() => setShowEditModal(true)}>
                          <Edit3 size={14} /> 세부사항 수정
                        </button>
                      </div>
                    )}
                  </div>

                  <button onClick={onToggleStar}>
                    <Star
                      size={20}
                      fill={project.isStarred ? "currentColor" : "none"}
                    />
                  </button>
                </div>
              </div>
            )}

            {/* ================= CHAT INPUT (✅ 중앙 카드화) ================= */}
            <section className="w-full flex justify-center">
              <div className="z-10 w-full" style={{ maxWidth: '680px' }}>
                <ChatInput
                  ref={chatInputRef}
                  onSendMessage={null}
                  onStartChat={onStartChat}
                  onTitlesGenerated={handleTitlesGenerated}
                  engineType={selectedEngine}
                  showModelSelector={true}
                />
              </div>
            </section>
            {/* =============================================================== */}

            {/* ================= GUIDE (✅ 입력창 아래 이동) ================= */}
            {userRole === "user" && (
              <section className="-mt-2 w-full flex justify-center">
                <div className="w-full" style={{ maxWidth: '680px' }}>
                  <C1C2GuideSection selectedEngine={selectedEngine} />
                </div>
              </section>
            )}
            {/* =============================================================== */}

            {userRole === "admin" && (
              <div className="w-full xl:hidden">
                <PromptManagePanel engineType={selectedEngine} />
              </div>
            )}
          </div>
        </div>

        {userRole === "admin" && (
          <div className="hidden xl:block">
            <PromptManagePanel engineType={selectedEngine} />
          </div>
        )}
      </main>
    </div>
  );
};

export default MainContent;
