import React from 'react';
import ChatPresenter from '../presenters/ChatPresenter';
import { useChat } from '../hooks/useChat';

const ChatContainer = ({
  initialMessage,
  userRole,
  selectedEngine = "T5",
  onLogout,
  onBackToLanding,
  onToggleSidebar,
  isSidebarOpen = false,
  onNewConversation,
  onDashboard,
}) => {
  const {
    messages,
    input,
    isLoading,
    isLoadingConversation,
    streamingMessage,
    hasResponded,
    usage,
    currentConversationId,
    setInput,
    sendMessage,
    startNewConversation,
    messagesEndRef,
  } = useChat(initialMessage, selectedEngine);

  return (
    <ChatPresenter
      // Data
      messages={messages}
      input={input}
      isLoading={isLoading}
      isLoadingConversation={isLoadingConversation}
      streamingMessage={streamingMessage}
      hasResponded={hasResponded}
      usage={usage}
      currentConversationId={currentConversationId}
      selectedEngine={selectedEngine}
      userRole={userRole}
      isSidebarOpen={isSidebarOpen}
      
      // Actions
      onInputChange={setInput}
      onSendMessage={sendMessage}
      onNewConversation={startNewConversation}
      onLogout={onLogout}
      onBackToLanding={onBackToLanding}
      onToggleSidebar={onToggleSidebar}
      onDashboard={onDashboard}
      
      // Refs
      messagesEndRef={messagesEndRef}
    />
  );
};

export default ChatContainer;