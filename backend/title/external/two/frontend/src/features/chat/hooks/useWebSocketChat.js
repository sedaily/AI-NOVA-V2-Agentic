import { useState, useRef, useEffect, useCallback } from 'react';
import {
  connectWebSocket,
  sendChatMessage,
  addMessageHandler,
  removeMessageHandler,
  isWebSocketConnected,
  updateConversationHistory,
  setConversationId,
} from '../services/websocketService';

/**
 * Custom hook for managing WebSocket chat functionality
 * Extracts complex WebSocket logic from ChatPage component
 */
export const useWebSocketChat = ({
  selectedEngine,
  conversationId,
  currentConversationId,
  initialMessage,
  hasProcessedInitial,
  onConversationIdUpdate,
  onError
}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  
  // Refs for managing streaming state
  const streamingContentRef = useRef("");
  const currentAssistantMessageId = useRef(null);
  const expectedChunkIndex = useRef(0);
  const streamingTimeoutRef = useRef(null);
  const chunkBuffer = useRef(new Map());
  const processBufferTimeoutRef = useRef(null);
  const processedIndices = useRef(new Set());

  // Process chunk buffer function
  const processChunkBuffer = useCallback(() => {
    const buffer = chunkBuffer.current;
    let nextExpectedIndex = expectedChunkIndex.current;
    let processedChunks = [];

    // Find and process consecutive chunks
    while (buffer.has(nextExpectedIndex)) {
      if (!processedIndices.current.has(nextExpectedIndex)) {
        const chunkText = buffer.get(nextExpectedIndex);
        processedChunks.push(chunkText);
        processedIndices.current.add(nextExpectedIndex);
      }
      buffer.delete(nextExpectedIndex);
      nextExpectedIndex++;
    }

    if (processedChunks.length > 0) {
      const combinedText = processedChunks.join("");
      expectedChunkIndex.current = nextExpectedIndex;

      // Update streaming content
      setStreamingContent((prev) => {
        const newContent = prev + combinedText;
        streamingContentRef.current = newContent;
        return newContent;
      });
    }

    // Set timeout for remaining chunks if any
    if (buffer.size > 0) {
      processBufferTimeoutRef.current = setTimeout(processChunkBuffer, 50);
    }
  }, []);

  // WebSocket message handler
  const handleWebSocketMessage = useCallback((message) => {
    switch (message.type) {
      case "chat_start":
      case "data_loaded":
        // Ignore - don't display in UI
        return;

      case "ai_start":
        // Already streaming - ignore to prevent duplicates
        if (currentAssistantMessageId.current) {
          return;
        }
        
        // AI response started
        const newMessageId = Date.now();
        
        // Reset streaming state
        setStreamingContent("");
        setIsLoading(true);
        currentAssistantMessageId.current = newMessageId;
        expectedChunkIndex.current = 0;
        chunkBuffer.current.clear();
        processedIndices.current.clear();

        // Clear existing buffer processing timeout
        if (processBufferTimeoutRef.current) {
          clearTimeout(processBufferTimeoutRef.current);
          processBufferTimeoutRef.current = null;
        }

        // Set streaming timeout (10 minutes)
        streamingTimeoutRef.current = setTimeout(() => {
          setIsLoading(false);
          if (onError) onError("응답 시간이 초과되었습니다. 다시 시도해주세요.");
          currentAssistantMessageId.current = null;
          setStreamingContent("");
          expectedChunkIndex.current = 0;
        }, 600000);

        return {
          type: 'ai_start',
          messageId: newMessageId,
          message: {
            id: newMessageId,
            type: "assistant",
            content: "",
            timestamp: new Date(),
            isStreaming: true,
          }
        };

      case "ai_chunk":
        if (message.chunk && currentAssistantMessageId.current) {
          // Reset timeout on each chunk received
          if (streamingTimeoutRef.current) {
            clearTimeout(streamingTimeoutRef.current);
            streamingTimeoutRef.current = setTimeout(() => {
              setIsLoading(false);
              if (onError) onError("응답 시간이 초과되었습니다. 다시 시도해주세요.");
              currentAssistantMessageId.current = null;
              setStreamingContent("");
              expectedChunkIndex.current = 0;
            }, 600000);
          }
          
          const chunkText = message.chunk;
          const receivedIndex = message.chunk_index || 0;

          // Process chunk immediately if it matches expected index
          if (receivedIndex === expectedChunkIndex.current && !processedIndices.current.has(receivedIndex)) {
            processedIndices.current.add(receivedIndex);
            
            setStreamingContent((prev) => {
              const newContent = prev + chunkText;
              streamingContentRef.current = newContent;
              return newContent;
            });
            
            expectedChunkIndex.current++;
            processChunkBuffer();
            
            return {
              type: 'ai_chunk',
              messageId: currentAssistantMessageId.current,
              content: streamingContentRef.current
            };
          } else {
            // Store in buffer if out of order
            chunkBuffer.current.set(receivedIndex, chunkText);
          }
        }
        break;

      case "chat_end":
        // Streaming ended - save conversation ID
        if (message.conversationId && onConversationIdUpdate) {
          onConversationIdUpdate(message.conversationId);
        }
        
        if (currentAssistantMessageId.current) {
          // Clear all timeouts
          if (streamingTimeoutRef.current) {
            clearTimeout(streamingTimeoutRef.current);
            streamingTimeoutRef.current = null;
          }
          if (processBufferTimeoutRef.current) {
            clearTimeout(processBufferTimeoutRef.current);
            processBufferTimeoutRef.current = null;
          }

          // Force process remaining buffer
          processChunkBuffer();

          const finalContent = streamingContentRef.current;
          const messageIdToUpdate = currentAssistantMessageId.current;
          
          // Reset streaming state
          currentAssistantMessageId.current = null;
          setStreamingContent("");
          streamingContentRef.current = "";
          expectedChunkIndex.current = 0;
          chunkBuffer.current.clear();
          processedIndices.current.clear();
          
          setIsLoading(false);
          
          return {
            type: 'chat_end',
            messageId: messageIdToUpdate,
            content: finalContent,
            conversationId: message.conversationId
          };
        }
        setIsLoading(false);
        break;

      case "chat_error":
      case "error":
        if (onError) onError(message.message || "오류가 발생했습니다");
        setIsLoading(false);

        // Clear all timeouts
        if (streamingTimeoutRef.current) {
          clearTimeout(streamingTimeoutRef.current);
          streamingTimeoutRef.current = null;
        }
        if (processBufferTimeoutRef.current) {
          clearTimeout(processBufferTimeoutRef.current);
          processBufferTimeoutRef.current = null;
        }

        // Reset streaming state
        currentAssistantMessageId.current = null;
        setStreamingContent("");
        expectedChunkIndex.current = 0;
        chunkBuffer.current.clear();
        break;
    }
    
    return null;
  }, [processChunkBuffer, onError, onConversationIdUpdate]);

  // Initialize WebSocket connection
  const initWebSocket = useCallback(async () => {
    try {
      if (!isWebSocketConnected()) {
        await connectWebSocket();
        setIsConnected(true);

        // Reset streaming state on new connection
        setStreamingContent("");
        currentAssistantMessageId.current = null;
        expectedChunkIndex.current = 0;
        setIsLoading(false);
      } else {
        setIsConnected(true);
      }
      
      // Initialize conversation history for new chat
      if (!conversationId) {
        updateConversationHistory([]);
        setConversationId(currentConversationId);
      }

      // Auto-send initial message if available
      const messageToSend = initialMessage || localStorage.getItem('pendingMessage');
      if (messageToSend && !hasProcessedInitial.current) {
        hasProcessedInitial.current = true;

        // Delay for handler registration completion
        setTimeout(async () => {
          setIsLoading(true);
          try {
            // Send initial message without conversation history
            await sendChatMessage(messageToSend, selectedEngine, [], currentConversationId);
            localStorage.removeItem('pendingMessage');
          } catch (error) {
            setIsLoading(false);
            if (onError) onError("초기 메시지 전송에 실패했습니다.");
          }
        }, 500);
      }
    } catch (error) {
      setIsConnected(false);
      if (onError) onError("WebSocket 연결에 실패했습니다.");
    }
  }, [conversationId, currentConversationId, initialMessage, selectedEngine, hasProcessedInitial, onError]);

  // Send chat message
  const sendMessage = useCallback(async (messageText, conversationHistory) => {
    if (!messageText?.trim() || isLoading) return false;
    
    try {
      if (isConnected) {
        await sendChatMessage(messageText, selectedEngine, conversationHistory, currentConversationId);
        return true;
      } else {
        // WebSocket not connected - attempt reconnection
        await connectWebSocket();
        setIsConnected(true);
        await sendChatMessage(messageText, selectedEngine, conversationHistory, currentConversationId);
        return true;
      }
    } catch (err) {
      if (onError) onError(err.message || "메시지 전송 중 오류가 발생했습니다.");
      return false;
    }
  }, [isConnected, isLoading, selectedEngine, currentConversationId, onError]);

  // Setup WebSocket on mount
  useEffect(() => {
    // Register message handler
    addMessageHandler(handleWebSocketMessage);
    
    // Initialize WebSocket
    initWebSocket();

    // Cleanup on unmount
    return () => {
      removeMessageHandler(handleWebSocketMessage);

      // Clear all timeouts
      if (streamingTimeoutRef.current) {
        clearTimeout(streamingTimeoutRef.current);
        streamingTimeoutRef.current = null;
      }
      if (processBufferTimeoutRef.current) {
        clearTimeout(processBufferTimeoutRef.current);
        processBufferTimeoutRef.current = null;
      }

      // Reset streaming state
      setStreamingContent("");
      currentAssistantMessageId.current = null;
      expectedChunkIndex.current = 0;
      chunkBuffer.current.clear();
      setIsLoading(false);
    };
  }, [handleWebSocketMessage, initWebSocket]);

  return {
    isConnected,
    isLoading,
    streamingContent,
    sendMessage,
    handleWebSocketMessage, // For direct access if needed
  };
};