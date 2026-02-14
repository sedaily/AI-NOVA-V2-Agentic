import React, {
  useState,
  useRef,
  useEffect,
} from "react";
import { ArrowUp, ChevronDown, TrendingDown, Globe } from "lucide-react";
import FileUploadButton from "./FileUploadButton";
import toast from "react-hot-toast";
import Header from "../../../shared/components/layout/Header";
import clsx from "clsx";
import {
  connectWebSocket,
  sendChatMessage,
  addMessageHandler,
  removeMessageHandler,
  isWebSocketConnected,
} from "../services/websocketService";
import {
  getConversation,
} from "../services/conversationService";
import { updateLocalUsage, fetchUsageFromServer } from "../services/usageService";
import * as usageService from "../services/usageService";
import { useParams, useLocation } from "react-router-dom";
// LoadingSpinner import 제거됨
import StreamingAssistantMessage from "./StreamingAssistantMessage";
import AssistantMessage from "./AssistantMessage";
import ChatSkeleton from "./ChatSkeleton";
import WebSearchSources from "./WebSearchSources";
import AnimatedNumber from "../../../shared/components/AnimatedNumber";

// Claude 모델 목록 (크레딧: 1,000토큰당 NC)
const CLAUDE_MODELS = [
  { id: "opus-4-20250514", name: "Opus 4.6", desc: "Latest & most capable (default)", inputNC: 7.5, outputNC: 37.5 },
  { id: "claude-opus-4-5-20251101", name: "Opus 4.5", desc: "Previous flagship model", inputNC: 7.5, outputNC: 37.5 },
  { id: "claude-sonnet-4-5-20250929", name: "Sonnet 4.5", desc: "Best for everyday tasks", inputNC: 4.5, outputNC: 22.5 },
];

const ChatPage = ({
  initialMessage: propsInitialMessage,
  userRole,
  selectedEngine = "T5",
  onLogout,
  onBackToLanding,
  onToggleSidebar,
  isSidebarOpen = false,
  onNewConversation,
  onDashboard,
}) => {
  const { conversationId } = useParams();
  const location = useLocation();
  
  // localStorage에서 pendingMessage 확인 (우선순위 높음)
  const [initialMessage] = useState(() => {
    const pendingMessage = localStorage.getItem('pendingMessage');
    if (pendingMessage) {
      console.log("📦 localStorage에서 메시지 복원:", pendingMessage);
      localStorage.removeItem('pendingMessage'); // 사용 후 즉시 삭제
      return pendingMessage;
    }
    return propsInitialMessage;
  });
  
  // URL에서 conversationId를 명시적으로 확인
  const urlConversationId = conversationId || window.location.pathname.split('/').pop();

  // 엔진 경로 (11 또는 22)를 conversationId로 오해하지 않도록 체크
  const enginePath = selectedEngine === 'T5' ? '11' : '22';
  const isValidConversationId = urlConversationId &&
    urlConversationId !== 'chat' &&
    urlConversationId !== '11' &&
    urlConversationId !== '22';

  console.log("🔍 URL 확인:", {
    conversationId,
    urlConversationId,
    enginePath,
    isValidConversationId,
    pathname: window.location.pathname,
    locationState: location.state
  });

  // URL에 유효한 conversationId가 있으면 그것을 사용, 없으면 새로 생성
  const [currentConversationId, setCurrentConversationId] = useState(() => {
    // 유효한 conversationId인 경우에만 사용 (11, 22는 엔진 경로이므로 제외)
    if (isValidConversationId) {
      console.log("✅ URL에서 conversationId 사용:", urlConversationId);
      return urlConversationId;
    }

    // localStorage에서 pendingConversationId 확인
    const pendingId = localStorage.getItem('pendingConversationId');
    if (pendingId) {
      console.log("📦 localStorage에서 conversationId 복원:", pendingId);
      localStorage.removeItem('pendingConversationId');
      return pendingId;
    }

    // 새 대화인 경우 새로 생성
    const newId = `${selectedEngine}_${Date.now()}`;
    console.log("🆕 새 conversationId 생성:", newId);
    return newId;
  });
  const [isLoadingConversation, setIsLoadingConversation] = useState(false);
  const [conversationSaved, setConversationSaved] = useState(false); // 대화 저장 여부 추적

  // 모델 선택 상태 (localStorage에서 복원)
  const [selectedModel, setSelectedModel] = useState(() => {
    const storedModel = localStorage.getItem("selectedModel");
    const validModelIds = CLAUDE_MODELS.map(m => m.id);
    if (storedModel && validModelIds.includes(storedModel)) {
      return storedModel;
    }
    return 'claude-opus-4-5-20251101';
  });
  const [isModelDropdownOpen, setIsModelDropdownOpen] = useState(false);

  // 모델 변경 핸들러
  const handleModelChange = (modelId) => {
    setSelectedModel(modelId);
    localStorage.setItem('selectedModel', modelId);
    setIsModelDropdownOpen(false);

    const model = CLAUDE_MODELS.find(m => m.id === modelId);
    toast.success(`${model?.name || modelId} 모델로 변경되었습니다`, {
      duration: 2000,
      position: "top-center",
      style: {
        background: "hsl(var(--bg-100))",
        color: "hsl(var(--text-100))",
        border: "1px solid hsl(var(--border-300)/25%)",
      },
    });
    console.log("🤖 모델 변경:", modelId);
  };
  const [messages, setMessages] = useState(() => {
    console.log("🎯 ChatPage 초기화 - initialMessage:", initialMessage);
    console.log("🎯 URL conversationId:", urlConversationId, "유효:", isValidConversationId);

    let hasCachedData = false;

    // 유효한 conversationId가 있으면 먼저 캐시에서 복원 시도
    if (isValidConversationId) {
      console.log("🌐 URL에서 유효한 conversationId 감지, 캐시 확인 중...");
      
      // 1. localStorage에서 캐시된 대화 내용 확인
      const cacheKey = `conv:${urlConversationId}`;
      const cachedData = localStorage.getItem(cacheKey);
      
      if (cachedData) {
        try {
          const parsedMessages = JSON.parse(cachedData);
          console.log("💾 캐시에서 대화 복원:", parsedMessages.length, "개 메시지");
          hasCachedData = true;
          // 타임스탬프 복원
          const restoredMessages = parsedMessages.map(msg => ({
            ...msg,
            timestamp: new Date(msg.timestamp)
          }));
          return restoredMessages;
        } catch (error) {
          console.error("캐시 파싱 실패:", error);
        }
      }
      
      console.log("캐시 없음, 서버에서 로드 예정");
    }

    // 새 채팅인 경우 초기 메시지 설정
    // initialMessage가 있고, 캐시된 대화가 없는 경우
    if (initialMessage && !hasCachedData) {
      const initialUserMessage = {
        id: crypto.randomUUID(),
        type: "user",
        content: initialMessage,
        timestamp: new Date(),
      };
      console.log("📝 초기 사용자 메시지 생성:", {
        id: initialUserMessage.id,
        type: initialUserMessage.type,
        content: initialUserMessage.content,
        contentLength: initialUserMessage.content?.length
      });
      return [initialUserMessage];
    }
    
    return [];
  });

  // 대화 로드 상태 추적을 위한 ref
  const loadedConversationRef = useRef(null);
  
  // 메시지가 변경될 때마다 캐시에 저장
  useEffect(() => {
    if (messages.length > 0 && currentConversationId) {
      const cacheKey = `conv:${currentConversationId}`;
      try {
        localStorage.setItem(cacheKey, JSON.stringify(messages));
        console.log("💾 대화 캐시 저장:", messages.length, "개 메시지");
      } catch (error) {
        console.error("캐시 저장 실패:", error);
      }
    }
  }, [messages, currentConversationId]);
  
  // 컴포넌트 마운트 시 사용량 초기화
  useEffect(() => {
    const initializeUsage = async () => {
      try {
        console.log("📊 초기 사용량 데이터 로딩...");
        
        // 먼저 로컬 스토리지에서 캐시된 값 확인
        const cachedValue = localStorage.getItem(`usage_percentage_${selectedEngine}`);
        if (cachedValue !== null) {
          setUsagePercentage(parseInt(cachedValue));
          console.log(`📦 캐시된 사용량: ${cachedValue}%`);
        }
        
        // 비동기로 서버에서 최신 데이터 가져오기
        const percentage = await usageService.getUsagePercentage(selectedEngine, false); // 캐시 사용 허용
        setUsagePercentage(percentage);
        console.log(`✅ ${selectedEngine} 초기 사용량: ${percentage}%`);
        
        // 헤더 업데이트를 위한 이벤트 발생
        window.dispatchEvent(new CustomEvent("usageUpdated"));
      } catch (error) {
        console.error("초기 사용량 로딩 실패:", error);
        // 실패 시 기본값
        setUsagePercentage(0);
      }
    };
    
    initializeUsage();
  }, [selectedEngine]);
  
  // 기존 대화 불러오기 - URL 변경 또는 새로고침 시
  useEffect(() => {
    // 유효한 conversationId만 로드 (11, 22는 엔진 경로이므로 제외)
    const loadConversationId = isValidConversationId ? urlConversationId : null;

    console.log("🔄 대화 로딩 useEffect 트리거:", {
      loadConversationId,
      conversationId,
      urlConversationId,
      isValidConversationId,
      currentConversationId,
      hasLocationState: !!location.state,
      hasInitialMessage: !!location.state?.initialMessage,
      messagesLength: messages.length,
      loadedConversation: loadedConversationRef.current,
      isCurrentlyStreaming: !!currentAssistantMessageId.current,
      streamingMessageId: currentAssistantMessageId.current
    });
    
    // URL에 conversationId가 있고, 아직 로드하지 않은 경우
    if (loadConversationId && loadedConversationRef.current !== loadConversationId) {
        setIsLoadingConversation(true);
        setCurrentConversationId(loadConversationId);
        
        console.log("📞 대화 불러오기 API 호출:", loadConversationId);
        
        // 인위적인 딜레이를 추가해서 스켈레톤이 보이도록 함
        setTimeout(() => {
          getConversation(loadConversationId)
          .then((response) => {
            console.log("🔍 서버 응답 전체 데이터:", response);
            
            // 실제 conversation 데이터 추출
            // 응답 null 체크 추가
            if (!response) {
              console.warn("⚠️ 서버 응답이 null입니다");
              return;
            }
            
            const conversationData = response.conversation || response;
            console.log("📋 추출된 conversation 데이터:", conversationData);
            
            if (conversationData && conversationData.messages) {
              console.log(
                "📥 서버에서 대화 복원:",
                conversationData.messages.length,
                "개 메시지"
              );
              
              // 각 메시지 구조 로그
              conversationData.messages.forEach((msg, index) => {
                console.log(`📄 메시지 ${index + 1}:`, {
                  id: msg.id,
                  type: msg.type,
                  role: msg.role,
                  content: msg.content?.substring(0, 100) + "...",
                  timestamp: msg.timestamp
                });
              });
              
              const processedMessages = conversationData.messages.map((msg) => ({
                ...msg,
                timestamp: new Date(msg.timestamp),
              }));
              
              console.log("✅ 처리된 메시지들:", processedMessages);
              
              // 🔑 핵심 수정: 현재 스트리밍 중인 AI 메시지가 있는지 확인
              setMessages((currentMessages) => {
                const hasStreamingAI = currentMessages.some(msg => 
                  msg.type === 'assistant' && msg.isStreaming && msg.id === currentAssistantMessageId.current
                );
                
                if (hasStreamingAI) {
                  // 스트리밍 중인 AI 메시지가 있으면 서버 데이터와 병합
                  const streamingMessage = currentMessages.find(msg => 
                    msg.type === 'assistant' && msg.isStreaming && msg.id === currentAssistantMessageId.current
                  );
                  
                  console.log("🔄 스트리밍 중인 AI 메시지 보존:", {
                    streamingMessageId: streamingMessage?.id,
                    streamingContent: streamingMessage?.content?.substring(0, 50) + "...",
                    serverMessagesCount: processedMessages.length
                  });
                  
                  // 서버 메시지 + 현재 스트리밍 메시지 병합
                  return [...processedMessages, streamingMessage];
                } else {
                  // 스트리밍 중인 메시지가 없으면 서버 데이터로 교체
                  console.log("📥 스트리밍 없음, 서버 데이터로 교체");
                  return processedMessages;
                }
              });
              
              // 서버에서 가져온 데이터를 캐시에 저장
              const cacheKey = `conv:${loadConversationId}`;
              try {
                localStorage.setItem(cacheKey, JSON.stringify(processedMessages));
                console.log("💾 서버 데이터를 캐시에 저장");
              } catch (error) {
                console.error("캐시 저장 실패:", error);
              }
              
              loadedConversationRef.current = loadConversationId; // 로드 완료 표시
              setConversationSaved(true); // 기존 대화는 이미 저장됨
            } else {
              console.warn("⚠️ messages가 없음. 전체 구조:", {
                response,
                conversationData,
                hasConversation: !!response.conversation,
                hasMessages: !!(conversationData && conversationData.messages)
              });
            }
          })
          .catch((error) => {
            console.error("서버에서 대화 불러오기 실패:", error);
          })
          .finally(() => {
            setIsLoadingConversation(false);
            setTimeout(() => setIsLoadingConversation(false), 100);
          });
        }, 300); // 300ms 딜레이로 스켈레톤이 보이도록 함
    } else if (!loadConversationId) {
      // 새 대화인 경우
      setIsLoadingConversation(true);
      const newConversationId = `${selectedEngine}_${Date.now()}`;
      setCurrentConversationId(newConversationId);
      setMessages([]);
      setConversationSaved(false); // 새 대화 시작 시 초기화
      
      // 새 대화도 스켈레톤을 잠깐 보여줌
      setTimeout(() => {
        setIsLoadingConversation(false);
      }, 200);
    }
  }, [urlConversationId, location.pathname]); // URL 변경 감지
  const [currentMessage, setCurrentMessage] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileUploadRef = useRef(null);
  const dragCounterRef = useRef(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const textareaRef = useRef(null);
  const messagesEndRef = useRef(null);
  const scrollContainerRef = useRef(null);
  const [isConnected, setIsConnected] = useState(false);
  const [webSearchEnabled, setWebSearchEnabled] = useState(() => {
    // localStorage에서 웹검색 상태 복원
    const saved = localStorage.getItem('webSearchEnabled');
    return saved === 'true';
  });
  const [streamingContent, setStreamingContent] = useState("");
  const currentAssistantMessageId = useRef(null);
  const hasProcessedInitial = useRef(false);
  const expectedChunkIndex = useRef(0); // 청크 순서 추적
  const [usagePercentage, setUsagePercentage] = useState(null); // 사용량 퍼센티지 - null로 시작하여 로딩 상태 표시
  const [lastCreditsUsed, setLastCreditsUsed] = useState(null); // 마지막 응답에 사용된 크레딧
  const [creditBalance, setCreditBalance] = useState(null); // 현재 크레딧 잔액
  const [webSearchResults, setWebSearchResults] = useState(null); // 웹검색 결과 (Claude.ai 스타일 UI용)
  const streamingTimeoutRef = useRef(null); // 스트리밍 타임아웃 추적
  const chunkBuffer = useRef(new Map()); // 청크 버퍼 (index -> chunk 내용)
  const processBufferTimeoutRef = useRef(null); // 버퍼 처리 타임아웃
  const lastUserMessageRef = useRef(null); // 마지막 사용자 메시지 추적

  // 🔑 핵심 개선: 실시간 데이터 추적을 위한 ref
  const streamingContentRef = useRef(""); // 스트리밍 콘텐츠 실시간 추적
  const lastAiMessageRef = useRef(null); // 마지막 AI 메시지 추적

  // 청크 버퍼 처리 함수
  const processChunkBuffer = () => {
    const buffer = chunkBuffer.current;
    let nextExpectedIndex = expectedChunkIndex.current;
    let processedChunks = [];

    // 연속된 청크들을 찾아서 처리
    while (buffer.has(nextExpectedIndex)) {
      const chunkText = buffer.get(nextExpectedIndex);
      processedChunks.push(chunkText);
      buffer.delete(nextExpectedIndex);
      nextExpectedIndex++;
    }

    if (processedChunks.length > 0) {
      const combinedText = processedChunks.join("");
      expectedChunkIndex.current = nextExpectedIndex;

      // 먼저 ref 업데이트
      const newContent = streamingContentRef.current + combinedText;
      streamingContentRef.current = newContent;

      console.log(
        `🔄 버퍼에서 ${processedChunks.length}개 청크 처리: (길이: ${combinedText.length}, 총: ${newContent.length})`
      );

      // 스트리밍 content 상태 업데이트
      setStreamingContent(newContent);

      // 메시지 업데이트 - isStreaming 상태 유지
      setMessages((prevMessages) =>
        prevMessages.map((msg) =>
          msg.id === currentAssistantMessageId.current
            ? { ...msg, content: newContent, isStreaming: true }
            : msg
        )
      );
    }

    // 버퍼에 남은 청크가 있으면 다시 타임아웃 설정 (더 부드러운 타이핑을 위해 80ms로 조정)
    if (buffer.size > 0) {
      processBufferTimeoutRef.current = setTimeout(processChunkBuffer, 50);
    }
  };

  // 사용량 퍼센티지 초기화 및 업데이트
  useEffect(() => {
    // 컴포넌트 마운트 시 서버에서 실제 사용량 가져오기
    const loadUsage = async () => {
      try {
        const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
        // conversationService.js와 동일한 순서로 userId 가져오기
        const userId = userInfo.username || userInfo.userId || userInfo.email || 'anonymous';  // UUID 우선
        
        // 서버에서 사용량 가져오기 시도
        await fetchUsageFromServer(userId, selectedEngine);
      } catch (error) {
        console.log('서버 사용량 조회 실패, 로컬 데이터 사용:', error);
      }
      
      // 로컬 또는 서버에서 가져온 사용량으로 업데이트
      usageService.getUsagePercentage(selectedEngine, true).then(percentage => {
        setUsagePercentage(percentage);
      });
    };
    
    loadUsage();
  }, [selectedEngine, messages]);

  // 웹검색 상태를 localStorage에 저장
  useEffect(() => {
    localStorage.setItem('webSearchEnabled', webSearchEnabled.toString());
  }, [webSearchEnabled]);

  // WebSocket 초기화 및 메시지 핸들러 설정
  useEffect(() => {
    // 컴포넌트 마운트 시 모든 스트리밍 상태 완전 초기화
    console.log("🔄 ChatPage 초기화 - 모든 스트리밍 상태 리셋", {
      initialMessage,
      selectedEngine,
      timestamp: new Date().toISOString(),
    });
    setStreamingContent("");
    streamingContentRef.current = ""; // 🔑 ref도 초기화
    setIsLoading(false);
    setError(null);
    currentAssistantMessageId.current = null;
    expectedChunkIndex.current = 0;
    chunkBuffer.current.clear();

    // WebSocket 메시지 핸들러 등록
    // WebSocket 메시지 핸들러
    const handleWebSocketMessage = (message) => {
      // websocketService에서 이미 로깅하므로 중복 로깅 제거

      switch (message.type) {
        case "chat_start":
          // 무시 - UI에 표시하지 않음
          console.log(`${message.engine} 엔진 시작`);
          return; // 아무것도 하지 않고 종료

        case "data_loaded":
          // 무시 - UI에 표시하지 않음
          console.log(`데이터 로드 완료: ${message.file_count}개 파일`);
          return; // 아무것도 하지 않고 종료

        case "web_search_results":
          // 웹검색 결과 수신 (AI 응답 전에 표시)
          console.log("🌐 웹검색 결과 수신:", {
            query: message.query,
            sourcesCount: message.sources?.length || 0
          });

          if (message.sources && message.sources.length > 0) {
            setWebSearchResults({
              query: message.query,
              sources: message.sources.map(source => ({
                title: source.title || source.name || '',
                url: source.url || source.link || ''
              }))
            });
          }
          break;

        case "ai_start":
          // AI 응답 시작 - 새 메시지 생성
          const newMessageId = Date.now();

          console.log("🤖 AI 응답 시작 신호 수신:", {
            messageId: newMessageId,
            timestamp: message.timestamp,
            currentMessages: messages.length,
            previousStreamingContent: streamingContent,
            currentAssistantMessageId: currentAssistantMessageId.current,
          });

          // 이미 AI 메시지가 처리 중이면 무시 (중복 방지)
          if (currentAssistantMessageId.current) {
            console.log("⚠️ 이미 AI 메시지 처리 중, 중복 ai_start 무시");
            return;
          }

          // 이전 스트리밍 상태 완전히 정리
          setStreamingContent("");
          streamingContentRef.current = ""; // 🔑 ref도 초기화
          setIsLoading(true);
          setError(null);
          currentAssistantMessageId.current = newMessageId;
          expectedChunkIndex.current = 0; // 청크 인덱스 초기화
          chunkBuffer.current.clear(); // 청크 버퍼 초기화

          // 기존 버퍼 처리 타임아웃 클리어
          if (processBufferTimeoutRef.current) {
            clearTimeout(processBufferTimeoutRef.current);
            processBufferTimeoutRef.current = null;
          }

          console.log("🔄 스트리밍 상태 초기화 완료:", {
            messageId: newMessageId,
            expectedChunkIndex: 0,
            bufferCleared: true,
          });

          // 스트리밍 타임아웃 설정 (30초)
          streamingTimeoutRef.current = setTimeout(() => {
            console.warn("스트리밍 타임아웃! 강제 종료");
            setIsLoading(false);
            setError("응답 시간이 초과되었습니다. 다시 시도해주세요.");
            currentAssistantMessageId.current = null;
            setStreamingContent("");
            expectedChunkIndex.current = 0;
          }, 300000);

          // 현재 웹검색 결과를 캡처 (AI 메시지에 첨부)
          const currentWebSearchResults = webSearchResults;

          setMessages((prev) => {
            const newMessages = [
              ...prev,
              {
                id: newMessageId,
                type: "assistant",
                content: "",
                timestamp: new Date(),
                isStreaming: true,
                webSearchResults: currentWebSearchResults, // 웹검색 결과 저장
              },
            ];
            console.log("✅ AI 메시지 컨테이너 추가:", {
              totalMessages: newMessages.length,
              assistantMessageId: newMessageId,
              hasWebSearchResults: !!currentWebSearchResults,
              messages: newMessages.map(m => ({
                id: m.id,
                type: m.type,
                content: m.content?.substring(0, 20),
                isStreaming: m.isStreaming
              }))
            });
            return newMessages;
          });

          // 다음 검색을 위해 webSearchResults 초기화
          setWebSearchResults(null);
          break;

        case "ai_chunk":
          // 스트리밍이 종료되었으면 청크 무시
          if (!currentAssistantMessageId.current) {
            return; // 조용히 무시
          }
          
          // 스트리밍 청크 수신 - 간단하게 순차 처리
          if (message.chunk && currentAssistantMessageId.current) {
            const chunkText = message.chunk;
            const receivedIndex = message.chunk_index || 0;

            // 현재 기대하는 인덱스와 일치하면 바로 처리
            if (receivedIndex === expectedChunkIndex.current) {
              // 먼저 ref 업데이트
              const newContent = streamingContentRef.current + chunkText;
              streamingContentRef.current = newContent;
              
              console.log(`📊 스트리밍 진행:`, {
                chunkIndex: receivedIndex,
                addedLength: chunkText.length,
                totalLength: newContent.length,
                preview: newContent.substring(newContent.length - 50),
              });

              // 스트리밍 콘텐츠 상태 업데이트
              setStreamingContent(newContent);

              // 메시지 업데이트
              setMessages((prevMessages) => {
                console.log("📝 메시지 업데이트 전:", {
                  messagesCount: prevMessages.length,
                  currentAssistantId: currentAssistantMessageId.current,
                  messages: prevMessages.map(m => ({
                    id: m.id,
                    type: m.type,
                    contentLength: m.content?.length,
                    isStreaming: m.isStreaming
                  }))
                });
                
                const updated = prevMessages.map((msg) =>
                  msg.id === currentAssistantMessageId.current
                    ? { ...msg, content: newContent, isStreaming: true }
                    : msg
                );

                // 🔑 마지막 AI 메시지 ref 업데이트
                const updatedAiMsg = updated.find(
                  (msg) => msg.id === currentAssistantMessageId.current
                );
                if (updatedAiMsg) {
                  lastAiMessageRef.current = updatedAiMsg;
                }
                
                console.log("📝 메시지 업데이트 후:", {
                  messagesCount: updated.length,
                  updatedMessage: updatedAiMsg ? {
                    id: updatedAiMsg.id,
                    contentLength: updatedAiMsg.content?.length,
                    contentPreview: updatedAiMsg.content?.substring(0, 50)
                  } : null
                });

                return updated;
              });

              expectedChunkIndex.current++;

              // 버퍼에 있는 다음 청크들 확인
              processChunkBuffer();
            } else {
              // 순서가 맞지 않으면 버퍼에 저장
              console.log(`⏸️ 청크 ${receivedIndex} 버퍼에 저장:`, {
                expected: expectedChunkIndex.current,
                received: receivedIndex,
                text: chunkText,
                bufferSize: chunkBuffer.current.size + 1,
              });
              chunkBuffer.current.set(receivedIndex, chunkText);
            }
          }
          break;

        case "chat_end":
          console.log("🎯 chat_end 메시지 수신됨", message);
          console.log("💳 credits 필드:", message.credits);

          // 크레딧 사용 정보 저장 (입력창 위에 표시)
          if (message.credits && message.credits.used > 0) {
            setLastCreditsUsed({
              used: message.credits.used,
              inputTokens: message.credits.inputTokens,
              outputTokens: message.credits.outputTokens,
              modelId: message.credits.modelId,
              balance: message.credits.balance,
              totalUsed: message.credits.totalUsed
            });
            console.log("💳 크레딧 저장됨:", message.credits.used, "NC, 잔액:", message.credits.balance, "NC");

            // 크레딧 캐시 업데이트 및 이벤트 발생 (헤더 업데이트용)
            if (message.credits.balance !== undefined) {
              setCreditBalance(message.credits.balance); // 잔액 상태 업데이트
              usageService.updateCreditsCache(message.credits.balance, message.credits.totalUsed || 0);
              window.dispatchEvent(new CustomEvent('creditsUpdated', {
                detail: {
                  balance: message.credits.balance,
                  totalUsed: message.credits.totalUsed || 0
                }
              }));
            }
          }

          // conversationId는 클라이언트 것을 유지 (서버 것은 무시)
          if (message.conversationId && message.conversationId !== currentConversationId) {
            console.log("⚠️ 서버 conversationId 무시:", message.conversationId, "클라이언트 유지:", currentConversationId);
            // setCurrentConversationId(message.conversationId); // 서버 ID는 사용하지 않음

            // 사이드바 새로고침 트리거
            if (typeof window !== "undefined") {
              window.dispatchEvent(new CustomEvent("refreshSidebar"));
            }
          }

          // 스트리밍 종료 및 즉시 초기화
          if (currentAssistantMessageId.current) {
            // 모든 타임아웃 클리어
            if (streamingTimeoutRef.current) {
              clearTimeout(streamingTimeoutRef.current);
              streamingTimeoutRef.current = null;
            }
            if (processBufferTimeoutRef.current) {
              clearTimeout(processBufferTimeoutRef.current);
              processBufferTimeoutRef.current = null;
            }

            // 마지막 버퍼 처리 강제 실행
            processChunkBuffer();

            // 🔑 핵심 수정: ref에서 최종 콘텐츠 가져오기
            const finalContent =
              streamingContentRef.current || streamingContent;
            setMessages((prev) => {
              const updated = prev.map((msg) =>
                msg.id === currentAssistantMessageId.current
                  ? {
                      ...msg,
                      content: finalContent || msg.content,
                      isStreaming: false,
                    }
                  : msg
              );

              // 🔑 최종 AI 메시지 ref 업데이트
              const finalAiMsg = updated.find(
                (msg) => msg.id === currentAssistantMessageId.current
              );
              if (finalAiMsg) {
                lastAiMessageRef.current = finalAiMsg;
              }

              // AI 응답 완료 후 대화 저장 (첫 번째 대화에서만)
              console.log("=".repeat(50));
              console.log("🔍 [DEBUG] 대화 저장 조건 확인:");
              console.log("  - currentConversationId:", currentConversationId);
              console.log("  - isValidConversationId:", isValidConversationId);
              console.log("  - hasFinalContent:", !!finalContent);
              console.log("  - finalContentLength:", finalContent?.length);
              console.log("  - conversationSaved:", conversationSaved);
              console.log("  - selectedEngine:", selectedEngine);
              console.log("  - willSave:", !!(currentConversationId && finalContent && !conversationSaved));
              console.log("=".repeat(50));

              if (currentConversationId && finalContent && !conversationSaved) {
                console.log("🟢 [DEBUG] 저장 조건 충족 - 저장 시작");
                const messagesToSave = updated.filter((m) => !m.isStreaming && m.content);
                console.log("📋 [DEBUG] 저장할 메시지 수:", messagesToSave.length);

                // 메시지 형식 정규화 (프론트엔드와 백엔드 호환성)
                const normalizedMessages = messagesToSave.map(msg => ({
                  id: msg.id,
                  role: msg.type === 'user' ? 'user' : 'assistant', // DynamoDB 저장용
                  type: msg.type, // 프론트엔드 호환성
                  content: msg.content,
                  timestamp: msg.timestamp || new Date().toISOString()
                }));

                const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
                console.log("👤 [DEBUG] userInfo:", userInfo);
                // conversationService.js와 동일한 순서로 userId 가져오기
                const userId = userInfo.username || userInfo.userId || userInfo.email || 'anonymous';  // UUID 우선
                console.log("👤 [DEBUG] userId:", userId);

                const conversationData = {
                  conversationId: currentConversationId,
                  userId: userId,
                  engineType: message.engine || selectedEngine,
                  messages: normalizedMessages,
                  title: messagesToSave[0]?.content?.substring(0, 50) || "New Conversation",
                };

                console.log("💾 [DEBUG] 저장 데이터:", {
                  conversationId: conversationData.conversationId,
                  userId: conversationData.userId,
                  engineType: conversationData.engineType,
                  messageCount: normalizedMessages.length,
                  title: conversationData.title
                });

                import("../services/conversationService").then(
                  ({ saveConversation }) => {
                    console.log("📡 [DEBUG] saveConversation 함수 호출 시작...");
                    saveConversation(conversationData)
                      .then((result) => {
                        console.log("✅ [DEBUG] 대화 저장 성공:", result);
                        setConversationSaved(true); // 대화 저장됨 표시
                        // 사이드바 새로고침
                        console.log("📢 [DEBUG] refreshSidebar 이벤트 발생시킴");
                        window.dispatchEvent(new CustomEvent("refreshSidebar"));
                        console.log("📢 [DEBUG] refreshSidebar 이벤트 발생 완료");
                        if (onNewConversation) {
                          onNewConversation();
                        }
                      })
                      .catch((error) => {
                        console.error("❌ [DEBUG] 대화 저장 실패:", error);
                        console.error("❌ [DEBUG] 에러 상세:", error.message, error.stack);
                      });
                  }
                );
              } else {
                console.log("🔴 [DEBUG] 저장 조건 미충족 - 저장 건너뜀");
                if (!currentConversationId) console.log("  - 이유: currentConversationId 없음");
                if (!finalContent) console.log("  - 이유: finalContent 없음");
                if (conversationSaved) console.log("  - 이유: 이미 저장됨 (conversationSaved=true)");
              }

              return updated;
            });
            // 🔑 중요: 사용량 업데이트 후에 초기화하도록 순서 변경
            // currentAssistantMessageId.current = null;
            // setStreamingContent("");
            // streamingContentRef.current = ""; // ref 초기화를 나중에
            // expectedChunkIndex.current = 0;
            // chunkBuffer.current.clear();
          }
          setIsLoading(false);
          console.log(
            `✅ 응답 완료: ${message.total_chunks} 청크, ${message.response_length} 문자`
          );

          // 사용량 업데이트 (비동기) - ref를 사용하여 마지막 사용자 메시지 참조
          const updateUsage = async () => {
            console.log("🔍 사용량 업데이트 함수 호출됨");

            // 사용자 메시지가 없으면 빈 메시지로 처리 (기본 인사말 등)
            const lastUserMsg = lastUserMessageRef.current || {
              type: "user",
              content: "", // 빈 메시지로 처리
              timestamp: new Date(),
            };

            // 🔑 핵심 수정: ref에서 최신 AI 메시지 가져오기
            const lastAiMsg = lastAiMessageRef.current || {
              type: "assistant",
              content: streamingContentRef.current || streamingContent || "",
              timestamp: new Date(),
            };

            console.log("📝 메시지 확인:", {
              lastUserMsg,
              lastAiMsg,
              totalMessages: messages.length,
              streamingContentRefLength: streamingContentRef.current?.length,
              streamingContentLength: streamingContent?.length,
              refContent: streamingContentRef.current?.substring(0, 100),
              allMessages: messages,
            });

            if (lastAiMsg) {
              // AI 메시지만 있으면 업데이트
              try {
                const result = await updateLocalUsage(
                  selectedEngine,
                  lastUserMsg.content,
                  lastAiMsg.content
                );

                if (result && result.success) {
                  setUsagePercentage(result.percentage);
                  console.log(
                    `📊 ${selectedEngine} 사용량 업데이트: ${result.percentage}%`
                  );

                  if (result.isBackup) {
                    console.log("💾 로컬 백업 모드로 저장됨");
                  }

                  // 대시보드에 사용량 업데이트 알림
                  window.dispatchEvent(new CustomEvent("usageUpdated"));
                } else {
                  console.warn(
                    `⚠️ 사용량 업데이트 실패: ${
                      result?.reason || "알 수 없는 오류"
                    }`
                  );
                }
              } catch (error) {
                console.error("사용량 업데이트 중 오류:", error);
              }
            } else {
              console.log("⚠️ 메시지가 없어서 사용량 업데이트 스킵");
            }
          };

          // 🔑 사용량 업데이트 완료 후 상태 초기화
          updateUsage().finally(() => {
            // 사용량 업데이트가 완료된 후 스트리밍 상태 초기화
            currentAssistantMessageId.current = null;
            setStreamingContent("");
            streamingContentRef.current = ""; // 🔑 이제 안전하게 초기화
            expectedChunkIndex.current = 0;
            chunkBuffer.current.clear();
            // 웹검색 결과는 메시지에 저장되므로 여기서 초기화하지 않음
            console.log("🧹 스트리밍 상태 완전 초기화 완료");
          });
          break;

        case "chat_error":
        case "error":
          console.error("❌ WebSocket 오류:", message.message);

          // 크레딧 부족 에러 처리
          if (message.errorCode === 'INSUFFICIENT_CREDITS') {
            setCreditBalance(message.balance || 0);
            setError("크레딧이 부족합니다. 충전 후 이용해주세요.");
          } else {
            setError(message.message || "오류가 발생했습니다");
          }

          setIsLoading(false);

          // 모든 타임아웃 클리어
          if (streamingTimeoutRef.current) {
            clearTimeout(streamingTimeoutRef.current);
            streamingTimeoutRef.current = null;
          }
          if (processBufferTimeoutRef.current) {
            clearTimeout(processBufferTimeoutRef.current);
            processBufferTimeoutRef.current = null;
          }

          // 오류 시에도 스트리밍 상태 완전 초기화
          currentAssistantMessageId.current = null;
          setStreamingContent("");
          streamingContentRef.current = ""; // 🔑 ref도 초기화
          expectedChunkIndex.current = 0;
          chunkBuffer.current.clear();
          break;
      }
    };

    // WebSocket 메시지 핸들러 등록
    addMessageHandler(handleWebSocketMessage);

    // WebSocket 연결 및 초기 메시지 처리
    const initWebSocket = async () => {
      try {
        if (!isWebSocketConnected()) {
          console.log("WebSocket 연결 시도...");
          await connectWebSocket();
          setIsConnected(true);
          console.log("WebSocket 연결 성공!");

          // 새 연결 시 스트리밍 상태 완전 초기화
          setStreamingContent("");
          streamingContentRef.current = ""; // 🔑 ref도 초기화
          currentAssistantMessageId.current = null;
          expectedChunkIndex.current = 0;
          setIsLoading(false);
        } else {
          setIsConnected(true);
        }

        // initialMessage가 있고, 새로 시작하는 대화인 경우에만 자동 전송
        // localStorage에서 pendingMessage가 있었거나 location.state에 initialMessage가 있는 경우
        const isFromMainPage = !!(location.state?.initialMessage || initialMessage);
        
        // sessionStorage를 사용하여 이미 처리된 메시지 추적
        const processedKey = `processed_${currentConversationId}`;
        const alreadyProcessed = sessionStorage.getItem(processedKey) === 'true';
        
        // messages가 비어있거나 사용자 메시지만 1개 있는 경우에만 전송
        const hasOnlyInitialUserMessage = messages.length === 1 && messages[0]?.type === 'user';
        const shouldSendInitial = initialMessage && !hasProcessedInitial.current && isFromMainPage && !alreadyProcessed && hasOnlyInitialUserMessage;
        
        console.log("🔍 초기 메시지 전송 여부 확인:", {
          initialMessage: !!initialMessage,
          hasProcessedInitial: hasProcessedInitial.current,
          isFromMainPage,
          alreadyProcessed,
          shouldSendInitial,
          urlConversationId,
          locationState: location.state
        });
        
        if (shouldSendInitial) {
          hasProcessedInitial.current = true;
          // sessionStorage에 처리 완료 표시
          sessionStorage.setItem(processedKey, 'true');
          console.log(
            "📝 Initial message 감지 및 자동 전송 시작:",
            initialMessage
          );

          // 웹검색 상태 확인 (MainContent에서 전달됨)
          const pendingWebSearch = localStorage.getItem('pendingWebSearch') === 'true';
          if (pendingWebSearch) {
            console.log("🌐 웹검색 활성화 상태로 메시지 전송");
            localStorage.removeItem('pendingWebSearch'); // 사용 후 제거
          }

          // WebSocket 연결 상태를 확인하고 안정적으로 메시지 전송
          const sendInitialMessage = async (retryCount = 0) => {
            const maxRetries = 3;
            const retryDelay = 1000; // 1초
            
            try {
              // WebSocket 연결 상태 확인 - 더 빠르게 재시도
              const wsConnected = isWebSocketConnected();
              if (!wsConnected) {
                console.log(`⏳ WebSocket 연결 대기 중... (시도 ${retryCount + 1}/${maxRetries})`);
                
                if (retryCount < maxRetries) {
                  // 더 빠른 재시도
                  setTimeout(() => sendInitialMessage(retryCount + 1), 300); // 300ms로 단축
                  return;
                } else {
                  console.warn("⚠️ WebSocket 연결이 느립니다. 그래도 메시지 전송 시도...");
                  // 연결이 안 되어도 시도해보기
                }
              }
              
              console.log("✅ WebSocket 연결 확인됨, 메시지 전송 시작");
              
              // 🔑 개선된 중복 체크: 현재 messages 상태에서 동일한 내용의 사용자 메시지 확인
              let userMessage = null;
              const userMessageRef = { current: null };
              
              setMessages((currentMessages) => {
                const existingUserMessage = currentMessages.find(m => 
                  m.type === 'user' && m.content === initialMessage
                );
                
                if (existingUserMessage) {
                  userMessageRef.current = existingUserMessage;
                  console.log("✅ 기존 사용자 메시지 사용:", existingUserMessage);
                  return currentMessages; // 변경 없이 현재 상태 유지
                } else {
                  // 사용자 메시지가 없는 경우에만 추가
                  const idempotencyKey = crypto.randomUUID();
                  const newUserMessage = {
                    id: crypto.randomUUID(),
                    type: "user",
                    content: initialMessage,
                    timestamp: new Date(),
                    idempotencyKey,
                  };
                  userMessageRef.current = newUserMessage;
                  console.log("➕ 새 사용자 메시지 추가:", newUserMessage);
                  return [...currentMessages, newUserMessage];
                }
              });
              
              // ref에서 실제 사용자 메시지 참조 가져오기
              userMessage = userMessageRef.current;
              lastUserMessageRef.current = userMessage;

              // 스트리밍 상태 초기화 (AI 메시지는 ai_start에서 생성됨)
              streamingContentRef.current = "";
              setStreamingContent("");
              expectedChunkIndex.current = 0;
              chunkBuffer.current.clear();
              currentAssistantMessageId.current = null; // 명시적으로 null로 설정
              setIsLoading(false); // ai_start에서 true로 설정될 것임
              
              console.log("✅ 초기 메시지 전송 준비 완료 - AI 응답 대기 중");

              // WebSocket으로 메시지 전송 (재시도 로직 포함)
              let sendSuccess = false;
              let sendRetries = 0;
              
              while (!sendSuccess && sendRetries < 3) {
                try {
                  await sendChatMessage(
                    initialMessage,
                    selectedEngine,
                    [],
                    currentConversationId,
                    userMessage?.idempotencyKey || crypto.randomUUID(),
                    selectedModel,
                    pendingWebSearch
                  );
                  sendSuccess = true;
                  console.log("✅ Initial message 전송 완료", pendingWebSearch ? "(웹검색 ON)" : "");
                  
                  // 초기 메시지 전송 후 자동 스크롤
                  setTimeout(() => {
                    if (scrollContainerRef.current) {
                      scrollContainerRef.current.scrollTo({
                        top: scrollContainerRef.current.scrollHeight,
                        behavior: 'smooth'
                      });
                    }
                  }, 100);
                } catch (sendError) {
                  sendRetries++;
                  console.log(`⚠️ 메시지 전송 실패 (시도 ${sendRetries}/3):`, sendError);
                  
                  if (sendRetries < 3) {
                    await new Promise(resolve => setTimeout(resolve, 500));
                  } else {
                    throw sendError;
                  }
                }
              }
              
              // AI 응답 완료 후에만 저장하도록 변경 (중복 방지)
              // 초기 메시지만으로는 저장하지 않음
              console.log("📝 대화 저장은 AI 응답 완료 후에 진행됩니다");
            } catch (error) {
              console.error("❌ Initial message 전송 실패:", error);
              setIsLoading(false);
              setError("메시지 전송에 실패했습니다. 새로고침 후 다시 시도해주세요.");
              
              // 실패 시 처리 플래그 리셋 (재시도 가능하도록)
              hasProcessedInitial.current = false;
              const processedKey = `processed_${currentConversationId}`;
              sessionStorage.removeItem(processedKey);
            }
          };
          
          // 짧은 지연 후 메시지 전송 (WebSocket 연결 안정화를 위해)
          setTimeout(() => sendInitialMessage(0), 500);
        }
      } catch (error) {
        console.error("WebSocket 연결 실패:", error);
        setIsConnected(false);
      }
    };

    initWebSocket();

    // 컴포넌트 언마운트 시 정리
    return () => {
      console.log("ChatPage 언마운트 - 핸들러 및 상태 정리");
      
      // sessionStorage 정리 (새로고침 시 초기화)
      const processedKey = `processed_${currentConversationId}`;
      sessionStorage.removeItem(processedKey);

      // WebSocket 메시지 핸들러 제거
      removeMessageHandler(handleWebSocketMessage);

      // 모든 타임아웃 클리어
      if (streamingTimeoutRef.current) {
        clearTimeout(streamingTimeoutRef.current);
        streamingTimeoutRef.current = null;
      }
      if (processBufferTimeoutRef.current) {
        clearTimeout(processBufferTimeoutRef.current);
        processBufferTimeoutRef.current = null;
      }

      // 스트리밍 상태 완전 정리
      setStreamingContent("");
      streamingContentRef.current = ""; // 🔑 ref도 초기화
      currentAssistantMessageId.current = null;
      expectedChunkIndex.current = 0;
      chunkBuffer.current.clear();
      setIsLoading(false);
    };
  }, []); // 빈 dependency 배열로 한 번만 실행

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!currentMessage.trim() || isLoading) return;

    // 파일 내용을 메시지에 추가
    let fullMessage = currentMessage.trim();
    
    if (uploadedFiles.length > 0) {
      const fileContents = uploadedFiles.map(file => {
        return `\n\n--- 파일: ${file.fileName} ---\n${file.content}`;
      }).join('\n');
      fullMessage = currentMessage.trim() + fileContents;
    }

    const id = crypto.randomUUID();
    const idempotencyKey = crypto.randomUUID(); // 중복 방지용 키
    const userMessage = {
      id, // 문자열 ID
      type: "user",
      content: fullMessage,  // 파일 내용이 포함된 메시지
      timestamp: new Date(),
      idempotencyKey, // 중복 방지 키 추가
    };

    setMessages((prev) => [...prev, userMessage]);
    lastUserMessageRef.current = userMessage; // 마지막 사용자 메시지 저장
    setCurrentMessage("");
    setIsTyping(false);
    setIsLoading(true);
    setError(null);
    setUploadedFiles([]); // 파일 목록 초기화

    // textarea 높이 리셋
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    // 메시지 전송 후 자동 스크롤 (약간의 딜레이를 주어 DOM 업데이트 보장)
    setTimeout(() => {
      if (scrollContainerRef.current) {
        scrollContainerRef.current.scrollTo({
          top: scrollContainerRef.current.scrollHeight,
          behavior: 'smooth'
        });
      }
    }, 100);

    // AI 응답 완료 후에만 저장하도록 변경 (중복 방지)
    // 첫 메시지 즉시 저장 로직 제거
    if (messages.length === 0 || (messages.length === 1 && messages[0].type === 'user')) {
      console.log("📝 첫 메시지 전송 - AI 응답 완료 후 쓰레드에 추가됩니다");
    }

    try {
      // WebSocket으로 메시지 전송
      if (isConnected) {
        // 대화 히스토리 생성 - 완료된 메시지만 포함
        const conversationHistory = messages
          .filter((msg) => !msg.isStreaming && msg.content) // 스트리밍 중이 아니고 내용이 있는 메시지만
          .map((msg) => ({
            type: msg.type,
            content: msg.content,
            timestamp: msg.timestamp,
          }));

        console.log("대화 컨텍스트 생성:", {
          totalMessages: messages.length,
          historyLength: conversationHistory.length,
          recentHistory: conversationHistory.slice(-4).map((msg) => ({
            role: msg.type,
            preview: msg.content.substring(0, 50) + "...",
          })),
        });

        console.log(
          `${selectedEngine} 엔진으로 메시지 전송:`,
          userMessage.content
        );

        // WebSocket으로 메시지 전송 시에도 ref 업데이트
        lastUserMessageRef.current = userMessage;

        await sendChatMessage(
          userMessage.content,
          selectedEngine,
          conversationHistory,
          currentConversationId,
          userMessage.idempotencyKey,
          selectedModel,
          webSearchEnabled
        );

        console.log("📤 메시지 전송 완료 - 웹검색:", webSearchEnabled);

        // WebSocket 응답은 메시지 핸들러에서 처리됨
        // 스크롤은 메시지가 추가될 때 자동으로 처리
      } else {
        // WebSocket 연결이 안된 경우 재연결 시도
        console.warn("WebSocket이 연결되지 않았습니다. 재연결 시도 중...");
        await connectWebSocket();
        setIsConnected(true);

        // 재연결 후 메시지 전송 (대화 히스토리 포함)
        const conversationHistory = messages
          .filter((msg) => !msg.isStreaming && msg.content)
          .map((msg) => ({
            type: msg.type,
            content: msg.content,
            timestamp: msg.timestamp,
          }));

        await sendChatMessage(
          userMessage.content,
          selectedEngine,
          conversationHistory,
          currentConversationId,
          userMessage.idempotencyKey,
          selectedModel,
          webSearchEnabled
        );
      }
    } catch (err) {
      console.error("메시지 전송 오류:", err);
      setError(err.message || "메시지 전송 중 오류가 발생했습니다.");
      setIsLoading(false);

      const errorMessage = {
        id: crypto.randomUUID(),
        type: "assistant",
        content: `죄송합니다. 메시지 전송 중 오류가 발생했습니다: ${err.message}`,
        timestamp: new Date(),
        isError: true,
      };

      setMessages((prev) => [...prev, errorMessage]);
    }
  };

  // 파일 업로드 처리
  // 드래그 앤 드롭 이벤트 핸들러
  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounterRef.current += 1;
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounterRef.current -= 1;
    if (dragCounterRef.current === 0) {
      setIsDragging(false);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    dragCounterRef.current = 0;

    const files = Array.from(e.dataTransfer.files);
    for (const file of files) {
      if (
        file.type === "text/plain" ||
        file.name.endsWith(".txt") ||
        file.type === "application/pdf" ||
        file.name.endsWith(".pdf")
      ) {
        // 파일 처리를 위해 FileUploadButton의 ref를 통해 처리
        if (fileUploadRef.current && fileUploadRef.current.handleFile) {
          await fileUploadRef.current.handleFile(file);
        }
      } else {
        toast.error(`지원하지 않는 파일 형식: ${file.name}`, {
          duration: 4000,
          position: "top-center",
          style: {
            background: "hsl(var(--bg-100))",
            color: "hsl(var(--text-100))",
            border: "1px solid hsl(var(--border-300))",
          },
        });
      }
    }
  };

  const handleFileContent = (content, fileInfo) => {
    console.log("파일 업로드됨:", fileInfo);

    // 파일 정보를 배열에 추가
    const newFile = {
      id: Date.now() + Math.random(),
      fileName: fileInfo.fileName,
      fileType: fileInfo.fileType,
      fileSize: fileInfo.fileSize,
      pageCount: fileInfo.pageCount,
      content: content,
    };
    setUploadedFiles((prev) => [...prev, newFile]);

    // 성공 알림
    toast.success(`파일 업로드 완료: ${fileInfo.fileName}`, {
      duration: 3000,
      position: "top-center",
      style: {
        background: "hsl(var(--bg-100))",
        color: "hsl(var(--text-100))",
        border: "1px solid hsl(var(--accent-main-100))",
      },
    });

    // 텍스트 영역에 포커스
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  const handleInputChange = (e) => {
    setCurrentMessage(e.target.value);
    setIsTyping(e.target.value.length > 0);

    // 자동 크기 조절
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(e);
    }
  };

  // 메시지가 추가될 때마다 최근 사용자 메시지를 상단에 위치 & 자동 저장
  useEffect(() => {
    // 스트리밍 중이거나 비어있는 메시지는 저장하지 않음
    const hasStreamingMessage = messages.some((msg) => msg.isStreaming);
    const completedMessages = messages.filter(
      (msg) => !msg.isStreaming && msg.content
    );

    if (completedMessages.length > 0 && !hasStreamingMessage) {
      // localStorage에 대화 저장 (최대 50개 메시지만 유지)
      const conversationKey = `chat_history_${selectedEngine}`;
      const messagesToSave = completedMessages.slice(-50); // 최근 50개만 저장
      localStorage.setItem(conversationKey, JSON.stringify(messagesToSave));
      console.log(
        "localStorage에 대화 저장:",
        messagesToSave.length,
        "개 메시지"
      );

      // 자동 저장 제거 - AI 응답 완료 시에만 저장
    }
  }, [
    messages.filter((m) => !m.isStreaming).length,
    selectedEngine,
    currentConversationId,
  ]);

  return (
    <div className="flex flex-col h-screen" 
         onDragEnter={handleDragEnter}
         onDragLeave={handleDragLeave}
         onDragOver={handleDragOver}
         onDrop={handleDrop}>
      {/* Drag Overlay */}
      {isDragging && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="relative">
            <div
              className="w-96 h-48 border-2 border-dashed border-blue-400 rounded-2xl bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/30 flex flex-col items-center justify-center gap-4 transition-all duration-200 animate-pulse"
              style={{
                background:
                  "linear-gradient(135deg, hsl(var(--accent-main-100))/10%, hsl(var(--accent-main-200))/5%)",
                borderColor: "hsl(var(--accent-main-100))",
              }}
            >
              <div className="flex flex-col items-center gap-3">
                <div className="w-16 h-16 rounded-full bg-blue-100 dark:bg-blue-900/50 flex items-center justify-center animate-bounce">
                  <svg
                    className="w-8 h-8 text-blue-600 dark:text-blue-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                </div>
                <div className="text-center">
                  <h3 className="text-lg font-semibold text-blue-700 dark:text-blue-300 mb-1">
                    파일을 여기에 놓으세요
                  </h3>
                  <p className="text-sm text-blue-600 dark:text-blue-400">
                    지원 형식: TXT, PDF
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      <Header
        onLogout={onLogout}
        onHome={onBackToLanding}
        onToggleSidebar={onToggleSidebar}
        isSidebarOpen={isSidebarOpen}
        onDashboard={onDashboard}
        selectedEngine={selectedEngine}
        usagePercentage={usagePercentage}
      />

      {/* Main Chat Container */}
      <div className="flex-1 overflow-hidden flex flex-col">
        {/* Messages Container with scroll */}
        <div className="flex-1 overflow-y-auto" ref={scrollContainerRef}>
          <div
            className={clsx(
              "mx-auto px-4 pt-6 pb-4",
              userRole === "admin" ? "max-w-3xl" : "max-w-4xl"
            )}
          >
            {/* Loading Skeleton */}
            {isLoadingConversation && (
              <ChatSkeleton />
            )}

            {/* Messages */}
            {!isLoadingConversation && (
              <>
                {messages.map((message, index) => {
                  // AI 메시지에 저장된 웹검색 결과 표시
                  const hasWebSearchResults =
                    message.type === "assistant" &&
                    message.webSearchResults;

                  return (
                    <div
                      key={message.id}
                      data-test-render-count="8"
                      data-message-type={message.type}
                    >
                      {/* 웹검색 결과 (Claude.ai 스타일) - AI 응답 앞에 표시 */}
                      {hasWebSearchResults && (
                        <WebSearchSources
                          query={message.webSearchResults.query}
                          sources={message.webSearchResults.sources}
                        />
                      )}

                      {message.type === "user" ? (
                        <UserMessage message={message} />
                      ) : message.isStreaming ? (
                        <StreamingAssistantMessage
                          content={message.content}
                          isStreaming={message.isStreaming}
                          timestamp={message.timestamp}
                          messageId={message.id}
                          webSearchSources={message.webSearchResults?.sources}
                        />
                      ) : (
                        <AssistantMessage
                          content={message.content}
                          timestamp={message.timestamp}
                          messageId={message.id}
                          webSearchSources={message.webSearchResults?.sources}
                        />
                      )}
                    </div>
                  );
                })}
              </>
            )}

            {/* 스크롤 타겟 */}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Field - Fixed at bottom */}
        <div className={clsx(
          "mx-auto w-full py-4",
          userRole === "admin" ? "max-w-3xl" : "max-w-4xl"
        )}>

          {/* 크레딧 부족 경고 */}
          {creditBalance !== null && creditBalance <= 0 && (
            <div className="flex justify-center px-4 mb-3">
              <div className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-red-500/10 border border-red-500/30 text-sm">
                <span className="text-red-400">⚠️</span>
                <span className="text-red-400 font-medium">
                  크레딧이 부족합니다. 충전 후 이용해주세요.
                </span>
                <button
                  onClick={() => window.location.href = '/subscription'}
                  className="ml-2 px-3 py-1 bg-red-500 hover:bg-red-600 text-white text-xs font-medium rounded-md transition-colors"
                >
                  충전하기
                </button>
              </div>
            </div>
          )}

          {/* 크레딧 사용 정보 + 잔액 표시 */}
          {lastCreditsUsed && creditBalance > 0 && (
            <div className="flex justify-end px-4 mb-2">
              <div className="flex items-center gap-3 px-4 py-2 rounded-lg bg-bg-100/80 border border-border-300/20 text-xs">
                {/* 이번 응답 사용량 - 일반 텍스트 */}
                <div className="flex items-center gap-1.5">
                  <TrendingDown size={14} className="text-orange-400" />
                  <span className="text-text-400">사용:</span>
                  <span className="font-bold text-orange-400">
                    {(lastCreditsUsed.used || 0).toFixed(1)} NC
                  </span>
                  <span className="text-text-500 text-[10px]">
                    ({(lastCreditsUsed.inputTokens || 0) + (lastCreditsUsed.outputTokens || 0)} tokens)
                  </span>
                </div>

                {/* 구분선 + 잔액 */}
                {lastCreditsUsed.balance !== undefined && (
                  <>
                    <span className="text-border-300">|</span>
                    <div className="flex items-center gap-1.5">
                      <span className="text-text-400">잔액:</span>
                      <AnimatedNumber
                        value={lastCreditsUsed.balance || 0}
                        suffix=" NC"
                        className={clsx(
                          "font-bold",
                          lastCreditsUsed.balance > 10000
                            ? "text-green-500"
                            : lastCreditsUsed.balance > 1000
                            ? "text-yellow-500"
                            : "text-red-500"
                        )}
                        showChange={false}
                        duration={0.5}
                      />
                    </div>
                  </>
                )}
              </div>
            </div>
          )}

          <fieldset className="flex w-full min-w-0 flex-col px-4">
            <div
              className="!box-content flex flex-col items-stretch transition-all duration-200 relative cursor-text z-10 rounded-2xl border border-border-300/15"
              style={{
                backgroundColor: "hsl(var(--bg-000))",
                boxShadow: "0 0.25rem 1.25rem hsl(var(--always-black)/3.5%)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.boxShadow =
                  "0 0.25rem 1.25rem hsl(var(--always-black)/3.5%)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.boxShadow =
                  "0 0.25rem 1.25rem hsl(var(--always-black)/3.5%)";
              }}
            >
              <div className="flex flex-col gap-3.5 m-3.5">
                <div className="relative">
                  <div className="max-h-96 w-full overflow-y-auto font-large break-words transition-opacity duration-200 min-h-[1.5rem]">
                    <textarea
                      ref={textareaRef}
                      value={currentMessage}
                      onChange={handleInputChange}
                      onKeyDown={handleKeyDown}
                      placeholder={creditBalance !== null && creditBalance <= 0 ? "크레딧을 충전해주세요" : "Claude에게 답변하기"}
                      disabled={creditBalance !== null && creditBalance <= 0}
                      className={clsx(
                        "w-full min-h-[1.5rem] max-h-96 resize-none bg-transparent border-none outline-none font-large leading-relaxed",
                        creditBalance !== null && creditBalance <= 0
                          ? "text-text-500 placeholder-text-500 cursor-not-allowed"
                          : "text-text-100 placeholder-text-500"
                      )}
                      rows={1}
                      style={{
                        fieldSizing: "content",
                        overflow: "hidden",
                      }}
                    />
                  </div>
                </div>

                <div className="flex gap-2.5 w-full items-center">
                  <div className="relative flex-1 flex items-center gap-2 shrink min-w-0">
                    {/* File Upload Button */}
                    <div className="relative shrink-0">
                      <FileUploadButton
                        ref={fileUploadRef}
                        onFileContent={handleFileContent}
                        disabled={false}
                      />
                    </div>

                    {/* Web Search Toggle Button */}
                    <button
                      type="button"
                      onClick={() => setWebSearchEnabled(!webSearchEnabled)}
                      className={clsx(
                        "inline-flex items-center justify-center shrink-0 h-8 w-8 rounded-lg transition-all duration-200",
                        webSearchEnabled
                          ? "bg-blue-500 text-white shadow-md"
                          : "bg-bg-100 text-text-400 hover:bg-bg-200 hover:text-text-200 border border-border-300/25"
                      )}
                      title={webSearchEnabled ? "웹검색 활성화됨" : "웹검색 비활성화"}
                      disabled={isLoading}
                    >
                      <Globe size={16} />
                    </button>
                    {webSearchEnabled && (
                      <span className="text-xs text-blue-500 font-medium">웹검색 ON</span>
                    )}
                  </div>

                  {/* Model Selector */}
                  <div className="relative">
                    <div className="relative">
                      <button
                        type="button"
                        onClick={() => setIsModelDropdownOpen(!isModelDropdownOpen)}
                        className={clsx(
                          "flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-sm font-medium transition-all duration-200",
                          "border border-border-300/30 hover:border-border-200/50",
                          "bg-bg-100/50 hover:bg-bg-200/50",
                          "text-text-200 hover:text-text-100"
                        )}
                        disabled={isLoading}
                      >
                        <span>
                          {CLAUDE_MODELS.find(m => m.id === selectedModel)?.name || "Opus 4.5"}
                        </span>
                        <ChevronDown
                          size={14}
                          className={clsx(
                            "transition-transform duration-200",
                            isModelDropdownOpen && "rotate-180"
                          )}
                        />
                      </button>

                      {/* Dropdown Menu */}
                      {isModelDropdownOpen && (
                        <div
                          className="absolute bottom-full right-0 mb-2 w-56 rounded-xl border border-border-300/30 bg-bg-000 shadow-lg overflow-hidden z-50"
                          style={{
                            boxShadow: "0 4px 20px hsl(var(--always-black)/15%)",
                          }}
                        >
                          <div className="p-1.5">
                            {CLAUDE_MODELS.map((model) => (
                              <button
                                key={model.id}
                                type="button"
                                onClick={() => handleModelChange(model.id)}
                                className={clsx(
                                  "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-all duration-150",
                                  selectedModel === model.id
                                    ? "bg-accent-main-100/10 text-accent-main-100"
                                    : "hover:bg-bg-200/50 text-text-200 hover:text-text-100"
                                )}
                              >
                                <div className="flex-1 min-w-0">
                                  <div className="font-medium text-sm">{model.name}</div>
                                  <div className="text-xs text-text-400 truncate">
                                    {model.desc}
                                  </div>
                                </div>
                                {selectedModel === model.id && (
                                  <svg
                                    className="w-4 h-4 text-accent-main-100 shrink-0"
                                    fill="currentColor"
                                    viewBox="0 0 20 20"
                                  >
                                    <path
                                      fillRule="evenodd"
                                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                      clipRule="evenodd"
                                    />
                                  </svg>
                                )}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Send Button */}
                  <div style={{ opacity: 1, transform: "none" }}>
                    <button
                      className={clsx(
                        "inline-flex items-center justify-center relative shrink-0 can-focus select-none disabled:pointer-events-none disabled:opacity-50 disabled:shadow-none disabled:drop-shadow-none font-base-bold transition-colors h-8 w-8 rounded-md active:scale-95 !rounded-lg !h-8 !w-8",
                        isTyping && (creditBalance === null || creditBalance > 0)
                          ? "bg-accent-main-000 text-oncolor-100 hover:bg-accent-main-200"
                          : "bg-gray-600 text-gray-400 cursor-not-allowed"
                      )}
                      disabled={!isTyping || (creditBalance !== null && creditBalance <= 0)}
                      type="button"
                      onClick={handleSendMessage}
                      aria-label="메시지 보내기"
                    >
                      <ArrowUp size={16} />
                    </button>
                  </div>
                </div>
              </div>

              {/* File Preview Section */}
              {uploadedFiles.length > 0 && (
                <div
                  className="overflow-hidden rounded-b-2xl"
                  style={{ height: "auto" }}
                >
                  <div className="border-border-300/25 border-t-0.5 rounded-b-2xl bg-bg-100 !p-3.5 !m-0 flex flex-row overflow-x-auto gap-3 px-3.5 py-2.5 -my-1">
                    {uploadedFiles.map((file) => (
                      <div key={file.id} className="relative">
                        <div
                          className="group/thumbnail"
                          data-testid="file-thumbnail"
                        >
                          <div
                            className="rounded-lg text-left block cursor-pointer font-ui transition-all rounded-lg border-0.5 border-border-300/25 flex flex-col justify-between gap-2.5 overflow-hidden px-2.5 py-2 bg-bg-000 hover:border-border-200/50 hover:shadow-always-black/10 shadow-sm shadow-always-black/5"
                            style={{
                              width: "120px",
                              height: "120px",
                              minWidth: "120px",
                              backgroundColor: "hsl(var(--bg-000))",
                              borderColor: "hsl(var(--border-300)/25%)",
                            }}
                          >
                            <div className="relative flex flex-col gap-1 min-h-0">
                              <h3
                                className="text-[12px] tracking-tighter break-words text-text-100 line-clamp-3"
                                style={{
                                  opacity: 1,
                                  color: "hsl(var(--text-100))",
                                }}
                              >
                                {file.fileName}
                              </h3>
                              <p
                                className="text-[10px] line-clamp-1 tracking-tighter break-words text-text-500"
                                style={{
                                  opacity: 1,
                                  color: "hsl(var(--text-500))",
                                }}
                              >
                                {file.pageCount
                                  ? `${file.pageCount}페이지`
                                  : `${Math.ceil(file.fileSize / 1024)}KB`}
                              </p>
                            </div>

                            <div className="relative flex flex-row items-center gap-1 justify-between">
                              <div
                                className="flex flex-row gap-1 shrink min-w-0"
                                style={{ opacity: 1 }}
                              >
                                <div className="min-w-0 h-[18px] flex flex-row items-center justify-center gap-0.5 px-1 border-0.5 border-border-300/25 shadow-sm rounded bg-bg-000/70 backdrop-blur-sm font-medium">
                                  <p className="uppercase truncate font-ui text-text-300 text-[11px] leading-[13px]">
                                    {file.fileType === "pdf" ? "PDF" : "TXT"}
                                  </p>
                                </div>
                              </div>
                            </div>
                          </div>

                          {/* Remove button */}
                          <button
                            onClick={() => {
                              setUploadedFiles((prev) => prev.filter((f) => f.id !== file.id));
                            }}
                            className="transition-all hover:bg-bg-000/50 text-text-500 hover:text-text-200 group-focus-within/thumbnail:opacity-100 group-hover/thumbnail:opacity-100 opacity-0 w-5 h-5 absolute -top-2 -left-2 rounded-full border-0.5 border-border-300/25 bg-bg-000/90 backdrop-blur-sm flex items-center justify-center"
                            data-state="closed"
                          >
                            <svg
                              xmlns="http://www.w3.org/2000/svg"
                              width="12"
                              height="12"
                              fill="currentColor"
                              viewBox="0 0 256 256"
                            >
                              <path d="M208.49,191.51a12,12,0,0,1-17,17L128,145,64.49,208.49a12,12,0,0,1-17-17L111,128,47.51,64.49a12,12,0,0,1,17-17L128,111l63.51-63.52a12,12,0,0,1,17,17L145,128Z"></path>
                            </svg>
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </fieldset>
        </div>
      </div>
    </div>
  );
};

const UserMessage = ({ message }) => {
  console.log("🔍 UserMessage 렌더링:", {
    id: message.id,
    content: message.content,
    contentLength: message.content?.length,
    type: message.type
  });
  
  return (
    <div className="mb-1 mt-1">
      <div
        className="group relative inline-flex gap-2 rounded-xl pl-2.5 py-2.5 break-words text-text-100 transition-all max-w-[75ch] flex-col pr-6"
        style={{
          opacity: 1,
          transform: "none",
          backgroundColor: "hsl(var(--bg-300))",
        }}
      >
        <div className="flex flex-row gap-2">
          <div className="shrink-0">
            <div
              className="flex shrink-0 items-center justify-center rounded-full font-bold select-none h-7 w-7 text-[12px] text-oncolor-100"
              style={{ backgroundColor: "hsl(var(--accent-pro-100))" }}
            >
              WI
            </div>
          </div>
          <div
            data-testid="user-message"
            className="grid grid-cols-1 gap-2 py-0.5"
            style={{
              fontFamily: "var(--font-ui)",
              fontSize: "0.9375rem",
              lineHeight: "1.5rem",
              letterSpacing: "-0.025em",
              color: "hsl(var(--text-100))",
            }}
          >
            <p className="whitespace-pre-wrap break-words">{message.content}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
