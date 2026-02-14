import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
// services 파일들을 features/chat/services에서 import
import {
  connectWebSocket,
  sendChatMessage,
  addMessageHandler,
  removeMessageHandler,
  isWebSocketConnected,
} from '../services/websocketService';
import {
  autoSaveConversation,
  getConversation,
} from '../services/conversationService';
import conversationService from '../services/conversationService';
import { updateLocalUsage, fetchUsageFromServer } from '../services/usageService';
import * as usageService from '../services/usageService';

export const useChat = (initialMessage, selectedEngine = "11") => {
  const { conversationId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  
  // URL에서 conversationId를 명시적으로 확인
  const urlConversationId = conversationId || window.location.pathname.split('/').pop();
  
  // 상태 관리 - conversationId 생성 로직 개선
  const [currentConversationId, setCurrentConversationId] = useState(() => {
    // URL에 명시적인 conversationId가 있으면 사용
    if (urlConversationId && urlConversationId !== 'chat') {
      return urlConversationId;
    }
    
    // 기존 대화가 진행 중이면 재사용
    const pendingId = localStorage.getItem('pendingConversationId');
    if (pendingId) {
      localStorage.removeItem('pendingConversationId');
      return pendingId;
    }
    
    // 현재 세션에서 진행 중인 대화가 있으면 재사용
    const sessionId = sessionStorage.getItem('currentConversationId');
    if (sessionId) {
      return sessionId;
    }
    
    // 완전히 새로운 경우에만 UUID 생성
    const newId = crypto.randomUUID();
    sessionStorage.setItem('currentConversationId', newId);
    return newId;
  });
  
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingConversation, setIsLoadingConversation] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState(null);
  const [hasResponded, setHasResponded] = useState(false);
  const [streamingShouldEnd, setStreamingShouldEnd] = useState(false);
  const [usage, setUsage] = useState({ percentage: 0, unit: '%' });
  
  // Refs
  const messagesEndRef = useRef(null);
  const currentConversationIdRef = useRef(currentConversationId);
  
  // currentConversationId가 변경될 때마다 ref와 세션 스토리지도 업데이트
  useEffect(() => {
    currentConversationIdRef.current = currentConversationId;
    // 세션 스토리지에도 저장하여 탭 간 공유
    if (currentConversationId) {
      sessionStorage.setItem('currentConversationId', currentConversationId);
    }
  }, [currentConversationId]);
  // loadedConversationsRef 제거 - 대화 전환 시 항상 새로 불러오도록 변경
  const streamingTimeoutRef = useRef(null);
  const messageIdCounterRef = useRef(0);
  
  // WebSocket 메시지 핸들러
  const handleWebSocketMessage = useCallback((data) => {
    console.log("📨 WebSocket 메시지 수신:", data);
    
    if (data.type === 'chunk') {
      setStreamingMessage(prev => {
        const updated = prev ? prev + data.content : data.content;
        return updated;
      });
      
      if (streamingTimeoutRef.current) {
        clearTimeout(streamingTimeoutRef.current);
      }
      streamingTimeoutRef.current = setTimeout(() => {
        console.log("⏰ 스트리밍 타임아웃 - 메시지 완료 처리");
        handleStreamEnd();
      }, 5000);
    } else if (data.type === 'end') {
      handleStreamEnd();
    } else if (data.type === 'error') {
      console.error("❌ WebSocket 오류:", data.message);
      setIsLoading(false);
      setStreamingMessage(null);
    }
  }, []);
  
  // 스트림 종료 처리
  const handleStreamEnd = useCallback(() => {
    if (streamingTimeoutRef.current) {
      clearTimeout(streamingTimeoutRef.current);
      streamingTimeoutRef.current = null;
    }
    
    setStreamingMessage(prev => {
      if (prev) {
        const assistantMessage = {
          id: `msg-${Date.now()}-${messageIdCounterRef.current++}`,
          role: "assistant",
          content: prev,
          timestamp: new Date().toISOString(),
        };
        
        setMessages(prevMessages => {
          const newMessages = [...prevMessages, assistantMessage];
          const conversationData = {
            conversationId: currentConversationIdRef.current,
            userId: conversationService.getUserId(),
            engineType: selectedEngine,
            messages: newMessages,
            title: newMessages[0]?.content?.substring(0, 50) || "새 대화",
            createdAt: newMessages[0]?.timestamp || new Date().toISOString(),
            updatedAt: new Date().toISOString()
          };
          
          // 첫 번째 대화(메시지가 2개일 때: user + assistant)일 때만 서버에 저장
          if (newMessages.length === 2 && !hasResponded) {
            // 처음 대화 생성 시에만 서버에 저장
            conversationService.saveConversation(conversationData)
              .then(() => console.log("✅ 첫 대화 서버 저장 완료"))
              .catch(err => console.error("❌ 첫 대화 서버 저장 실패:", err));
          } else {
            // 이후 메시지는 localStorage에만 저장
            conversationService.saveToLocalStorage(conversationData);
          }
          
          return newMessages;
        });
      }
      return null;
    });
    
    setIsLoading(false);
    setHasResponded(true);
    setStreamingShouldEnd(false);
  }, [selectedEngine, hasResponded]);
  
  // 메시지 전송
  const sendMessage = useCallback(async () => {
    const trimmedInput = input.trim();
    
    if (!trimmedInput || isLoading) {
      return;
    }
    
    if (!isWebSocketConnected()) {
      console.log("🔄 WebSocket 재연결 시도...");
      const connected = await connectWebSocket(selectedEngine);
      if (!connected) {
        alert("서버 연결에 실패했습니다. 잠시 후 다시 시도해주세요.");
        return;
      }
    }
    
    setIsLoading(true);
    const timestamp = new Date().toISOString();
    
    const userMessage = {
      id: `msg-${Date.now()}-${messageIdCounterRef.current++}`,
      role: "user",
      content: trimmedInput,
      timestamp: timestamp,
    };
    
    console.log("📝 Adding user message:", userMessage);
    setMessages(prev => {
      const newMessages = [...prev, userMessage];
      console.log("📚 Total messages after adding:", newMessages.length, newMessages);
      return newMessages;
    });
    setInput("");
    setStreamingMessage("");
    setStreamingShouldEnd(false);
    
    // WebSocket으로 메시지 전송 - 올바른 매개변수 순서로 수정
    sendChatMessage(
      trimmedInput,                           // message
      selectedEngine,                         // engineType  
      messages,                              // conversationHistory
      currentConversationIdRef.current,      // conversationId
      null                                   // idempotencyKey
    );
    
    // 사용자 메시지는 저장하지 않음 - AI 응답 완료 시에만 저장
    // 중복 저장 방지를 위해 여기서는 제거
    console.log("📝 사용자 메시지 추가됨, AI 응답 대기 중...");
    
    // 사용량 업데이트
    await updateLocalUsage(selectedEngine);
  }, [input, isLoading, messages, selectedEngine]);
  
  // 대화 불러오기
  const loadConversation = useCallback(async (convId) => {
    if (!convId || convId === 'chat') {
      return;
    }
    
    // 현재 대화와 동일한 경우에도 새로 불러오기 (대화 전환 시 필요)
    setIsLoadingConversation(true);
    
    try {
      const conversation = await getConversation(convId);
      console.log("📥 Loaded conversation:", conversation);
      if (conversation && conversation.messages) {
        console.log("📚 Loading messages:", conversation.messages.length, conversation.messages);
        setMessages(conversation.messages);
        setHasResponded(true);
        // 성공적으로 로드된 대화 ID 업데이트
        setCurrentConversationId(convId);
        currentConversationIdRef.current = convId;
      }
    } catch (error) {
      console.error("대화 불러오기 실패:", error);
    } finally {
      setIsLoadingConversation(false);
    }
  }, []);
  
  // 새 대화 시작 - 세션 스토리지도 업데이트
  const startNewConversation = useCallback(() => {
    const newId = crypto.randomUUID();
    setCurrentConversationId(newId);
    currentConversationIdRef.current = newId;
    
    // 세션 스토리지 업데이트
    sessionStorage.setItem('currentConversationId', newId);
    
    setMessages([]);
    setInput("");
    setStreamingMessage(null);
    setHasResponded(false);
    
    // URL 업데이트
    navigate(`/chat/${newId}`, { replace: false });
  }, [selectedEngine, navigate]);
  
  // 스크롤 관리
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);
  
  // WebSocket 초기화
  useEffect(() => {
    let messageHandler;
    
    const initWebSocket = async () => {
      const connected = await connectWebSocket(selectedEngine);
      if (connected) {
        messageHandler = handleWebSocketMessage;
        addMessageHandler(messageHandler);
      }
    };
    
    initWebSocket();
    
    return () => {
      if (messageHandler) {
        removeMessageHandler(messageHandler);
      }
      if (streamingTimeoutRef.current) {
        clearTimeout(streamingTimeoutRef.current);
      }
    };
  }, [selectedEngine, handleWebSocketMessage]);
  
  // conversationId 변경 감지
  useEffect(() => {
    if (urlConversationId && urlConversationId !== 'chat') {
      // URL의 conversationId가 변경되면 항상 새로 불러오기
      loadConversation(urlConversationId);
    }
  }, [urlConversationId, loadConversation]);
  
  // 초기 메시지 처리
  useEffect(() => {
    if (initialMessage && messages.length === 0 && !hasResponded) {
      setInput(initialMessage);
      // 자동 전송은 하지 않고 사용자가 전송 버튼을 누르도록 함
    }
  }, [initialMessage, messages.length, hasResponded]);
  
  // 사용량 업데이트
  useEffect(() => {
    const updateUsage = async () => {
      const percentage = await usageService.getUsagePercentage(selectedEngine);
      setUsage({ percentage, unit: '%' });
    };
    
    updateUsage();
    fetchUsageFromServer(selectedEngine);
    
    const interval = setInterval(updateUsage, 30000);
    return () => clearInterval(interval);
  }, [selectedEngine]);
  
  // 스크롤
  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage, scrollToBottom]);
  
  return {
    // State
    messages,
    input,
    isLoading,
    isLoadingConversation,
    streamingMessage,
    hasResponded,
    usage,
    currentConversationId,
    
    // Actions
    setInput,
    sendMessage,
    startNewConversation,
    
    // Refs
    messagesEndRef,
  };
};