import React from 'react';
import { ArrowUp, Plus } from "lucide-react";
import Header from "../../../shared/components/layout/Header";
import clsx from "clsx";
// LoadingSpinner import 제거됨
import StreamingAssistantMessage from "../components/StreamingAssistantMessage";
import AssistantMessage from "../components/AssistantMessage";

const ChatPresenter = ({
  // Data props
  messages,
  input,
  isLoading,
  isLoadingConversation,
  streamingMessage,
  hasResponded,
  usage,
  currentConversationId,
  selectedEngine,
  userRole,
  isSidebarOpen,
  
  // Action props
  onInputChange,
  onSendMessage,
  onNewConversation,
  onLogout,
  onBackToLanding,
  onToggleSidebar,
  onDashboard,
  
  // Refs
  messagesEndRef,
}) => {
  const handleSubmit = (e) => {
    e.preventDefault();
    onSendMessage();
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-screen" style={{ backgroundColor: "hsl(var(--bg-200))" }}>
      <Header
        userRole={userRole}
        selectedEngine={selectedEngine}
        onLogout={onLogout}
        onBackToLanding={onBackToLanding}
        onToggleSidebar={onToggleSidebar}
        onDashboard={onDashboard}
      />

      <div className="flex-1 overflow-hidden flex flex-col">
        <div className="flex-1 overflow-y-auto px-4">
          <div className="max-w-4xl mx-auto py-8">
            {isLoadingConversation ? (
              <div className="flex justify-center items-center py-8">
                <span className="animate-pulse">처리 중...</span>
              </div>
            ) : messages.length === 0 && !hasResponded ? (
              <WelcomeMessage selectedEngine={selectedEngine} />
            ) : (
              <MessageList 
                messages={messages}
                streamingMessage={streamingMessage}
                isLoading={isLoading}
              />
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        <InputArea
          input={input}
          isLoading={isLoading}
          usage={usage}
          hasMessages={messages.length > 0}
          onInputChange={onInputChange}
          onSubmit={handleSubmit}
          onKeyDown={handleKeyDown}
          onNewConversation={onNewConversation}
        />
      </div>
    </div>
  );
};

// 환영 메시지 컴포넌트
const WelcomeMessage = ({ selectedEngine }) => (
  <div className="text-center py-16">
    <div className="inline-flex items-center justify-center w-20 h-20 rounded-full mb-6"
         style={{ backgroundColor: "hsl(var(--accent-main-100)/0.1)" }}>
      <span className="text-3xl font-bold" style={{ color: "hsl(var(--accent-main-000))" }}>
        {selectedEngine}
      </span>
    </div>
    <h1 className="text-3xl font-bold mb-4" style={{ color: "hsl(var(--text-000))" }}>
      무엇을 도와드릴까요?
    </h1>
    <p className="text-lg" style={{ color: "hsl(var(--text-200))" }}>
      {selectedEngine === "22"
        ? "일본어 외신기사 엔진은 일본 언론 스타일로 전문적인 기사를 작성합니다"
        : "영어 외신기사 엔진은 영미권 언론 스타일로 전문적인 기사를 작성합니다"}
    </p>
  </div>
);

// 메시지 목록 컴포넌트
const MessageList = ({ messages, streamingMessage, isLoading }) => (
  <>
    {messages.map((message) => (
      <div key={message.id} className="mb-6">
        {message.role === "user" ? (
          <UserMessage content={message.content} />
        ) : (
          <AssistantMessage content={message.content} />
        )}
      </div>
    ))}
    
    {streamingMessage && (
      <div className="mb-6">
        <StreamingAssistantMessage content={streamingMessage} />
      </div>
    )}
    
    {isLoading && !streamingMessage && (
      <div className="mb-6 flex items-start space-x-3">
        <div className="w-8 h-8 rounded-full flex items-center justify-center"
             style={{ backgroundColor: "hsl(var(--accent-main-100)/0.1)" }}>
          <span className="text-sm font-medium" style={{ color: "hsl(var(--accent-main-000))" }}>
            AI
          </span>
        </div>
        <div className="flex-1">
          <span className="text-sm text-gray-500">로딩 중...</span>
        </div>
      </div>
    )}
  </>
);

// 사용자 메시지 컴포넌트
const UserMessage = ({ content }) => {
  // localStorage에서 사용자 정보 가져오기
  const userInfo = JSON.parse(localStorage.getItem("userInfo") || "{}");
  const userInitials = userInfo.email ? userInfo.email.substring(0, 2).toUpperCase() : "U";
  
  return (
    <div className="flex justify-end mb-4">
      <div className="group relative inline-flex gap-2 rounded-xl px-3 py-2.5 max-w-2xl"
           style={{ backgroundColor: "hsl(var(--bg-300))" }}>
        <div className="flex flex-row gap-2">
          <div className="grid grid-cols-1 gap-2">
            <p className="whitespace-pre-wrap break-words text-sm"
               style={{ color: "hsl(var(--text-000))" }}>
              {content}
            </p>
          </div>
          <div className="shrink-0">
            <div className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-medium"
                 style={{ backgroundColor: "hsl(var(--accent-main-000))" }}>
              {userInitials}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// 입력 영역 컴포넌트
const InputArea = ({ 
  input, 
  isLoading, 
  usage, 
  hasMessages, 
  onInputChange, 
  onSubmit, 
  onKeyDown,
  onNewConversation 
}) => (
  <div className="border-t" style={{ borderColor: "hsl(var(--border-300)/0.15)" }}>
    <div className="max-w-4xl mx-auto px-4 py-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-4">
          {hasMessages && (
            <button
              onClick={onNewConversation}
              className="flex items-center space-x-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
              style={{
                backgroundColor: "hsl(var(--bg-100))",
                color: "hsl(var(--text-200))",
                border: "1px solid hsl(var(--border-300)/0.15)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = "hsl(var(--bg-000))";
                e.currentTarget.style.color = "hsl(var(--text-000))";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = "hsl(var(--bg-100))";
                e.currentTarget.style.color = "hsl(var(--text-200))";
              }}
            >
              <Plus size={16} />
              <span>새 대화</span>
            </button>
          )}
        </div>
        
        <UsageIndicator usage={usage} />
      </div>

      <form onSubmit={onSubmit} className="relative">
        <textarea
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="메시지를 입력하세요..."
          rows={3}
          disabled={isLoading}
          className={clsx(
            "w-full px-4 py-3 pr-16 rounded-xl resize-none focus:outline-none transition-all",
            isLoading && "opacity-50 cursor-not-allowed"
          )}
          style={{
            backgroundColor: "hsl(var(--bg-000))",
            border: "1px solid hsl(var(--border-300)/0.15)",
            color: "hsl(var(--text-000))",
          }}
        />
        
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className={clsx(
            "absolute right-2 bottom-2 p-2.5 rounded-lg transition-all",
            (isLoading || !input.trim())
              ? "opacity-30 cursor-not-allowed"
              : "hover:scale-110 active:scale-95"
          )}
          style={{
            backgroundColor: "hsl(var(--accent-main-000))",
            color: "white",
          }}
        >
          <ArrowUp size={20} />
        </button>
      </form>
    </div>
  </div>
);

// 사용량 표시 컴포넌트
const UsageIndicator = ({ usage }) => (
  <div className="flex items-center space-x-2">
    <span className="text-xs" style={{ color: "hsl(var(--text-300))" }}>
      사용량
    </span>
    <div className="relative w-32 h-2 rounded-full overflow-hidden"
         style={{ backgroundColor: "hsl(var(--bg-100))" }}>
      <div
        className="absolute left-0 top-0 h-full rounded-full transition-all duration-500"
        style={{
          width: `${Math.min(usage.percentage, 100)}%`,
          backgroundColor: usage.percentage > 80 
            ? "hsl(var(--danger-000))" 
            : usage.percentage > 50 
            ? "hsl(var(--warning-000))" 
            : "hsl(var(--success-000))",
        }}
      />
    </div>
    <span className="text-xs font-medium" style={{ color: "hsl(var(--text-200))" }}>
      {usage.percentage}{usage.unit}
    </span>
  </div>
);

export default ChatPresenter;