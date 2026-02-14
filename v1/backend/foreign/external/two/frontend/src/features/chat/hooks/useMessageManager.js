import { useState, useCallback, useEffect } from 'react';
import { autoSaveConversation } from '../../../features/chat/services/conversationService';

/**
 * Custom hook for managing chat messages
 * Handles message state, auto-saving, and message operations
 */
export const useMessageManager = ({
  currentConversationId,
  selectedEngine,
  onNewConversation
}) => {
  const [messages, setMessages] = useState([]);

  // Add a new message to the list
  const addMessage = useCallback((message) => {
    setMessages(prev => [...prev, message]);
  }, []);

  // Update a specific message by ID
  const updateMessage = useCallback((messageId, updates) => {
    setMessages(prev => 
      prev.map(msg => 
        msg.id === messageId ? { ...msg, ...updates } : msg
      )
    );
  }, []);

  // Add user message
  const addUserMessage = useCallback((content, fileContent = null) => {
    let finalMessage = content.trim();
    if (fileContent) {
      finalMessage = `${content.trim()}\n\n[업로드된 파일 내용]\n${fileContent}`;
    }
    
    const userMessage = {
      id: crypto.randomUUID(),
      type: "user",
      content: finalMessage,
      timestamp: new Date(),
    };
    
    addMessage(userMessage);
    return userMessage;
  }, [addMessage]);

  // Add assistant message (for streaming)
  const addAssistantMessage = useCallback((messageId, isStreaming = true) => {
    const assistantMessage = {
      id: messageId,
      type: "assistant",
      content: "",
      timestamp: new Date(),
      isStreaming,
    };
    
    addMessage(assistantMessage);
    return assistantMessage;
  }, [addMessage]);

  // Update assistant message content during streaming
  const updateAssistantMessage = useCallback((messageId, content, isStreaming = true) => {
    updateMessage(messageId, { content, isStreaming });
  }, [updateMessage]);

  // Finalize assistant message (end streaming)
  const finalizeAssistantMessage = useCallback((messageId, finalContent) => {
    updateMessage(messageId, { content: finalContent, isStreaming: false });
  }, [updateMessage]);

  // Set initial messages (for loading existing conversation)
  const setInitialMessages = useCallback((initialMessages) => {
    setMessages(initialMessages || []);
  }, []);

  // Get conversation history for API calls (excludes streaming messages)
  const getConversationHistory = useCallback(() => {
    return messages
      .filter(msg => !msg.isStreaming && msg.content)
      .map(msg => ({
        type: msg.type,
        content: msg.content,
        timestamp: msg.timestamp
      }));
  }, [messages]);

  // Handle first message save (for sidebar update)
  const handleFirstMessageSave = useCallback(async (userMessage) => {
    if (messages.length === 1 || messages.length === 0) {
      const conversationData = {
        conversationId: currentConversationId,
        engineType: selectedEngine,
        messages: [userMessage],
        title: userMessage.content.substring(0, 50)
      };
      
      try {
        const { saveConversation } = await import('../services/conversationService');
        await saveConversation(conversationData);
        
        // Update sidebar with new conversation
        if (onNewConversation) {
          onNewConversation();
        }
      } catch (error) {
        // Failed to save first message
        console.error('First message save failed:', error);
      }
    }
  }, [messages.length, currentConversationId, selectedEngine, onNewConversation]);

  // Auto-save conversation when messages are added
  useEffect(() => {
    if (messages.length > 0) {
      const messagesToSave = messages.slice(-50); // Keep recent 50 messages
      const conversationData = {
        conversationId: currentConversationId,
        engineType: selectedEngine,
        messages: messagesToSave,
        title: messagesToSave[0]?.content?.substring(0, 50) || 'New Conversation'
      };
      autoSaveConversation(conversationData);
    }
  }, [messages, selectedEngine, currentConversationId]);

  // Save entire conversation after streaming completion
  const saveConversationAfterStreaming = useCallback((conversationId) => {
    setTimeout(() => {
      const messagesToSave = messages.filter(msg => !msg.isStreaming && msg.content);
      if (messagesToSave.length > 0) {
        const conversationData = {
          conversationId: conversationId || currentConversationId,
          engineType: selectedEngine,
          messages: messagesToSave,
          title: messagesToSave[0]?.content?.substring(0, 50) || 'New Conversation'
        };
        autoSaveConversation(conversationData);
      }
    }, 100);
  }, [messages, currentConversationId, selectedEngine]);

  return {
    messages,
    addMessage,
    updateMessage,
    addUserMessage,
    addAssistantMessage,
    updateAssistantMessage,
    finalizeAssistantMessage,
    setInitialMessages,
    getConversationHistory,
    handleFirstMessageSave,
    saveConversationAfterStreaming,
  };
};