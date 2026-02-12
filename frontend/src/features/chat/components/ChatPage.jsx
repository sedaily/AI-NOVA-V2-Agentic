import React, {
  useState,
  useRef,
  useEffect,
} from "react";
import { ArrowUp, Square, Globe } from "lucide-react";
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
import { getBuddyConfig } from "../../../config/buddyServiceConfig";
// LoadingSpinner import 제거됨
import StreamingAssistantMessage from "./StreamingAssistantMessage";
import AssistantMessage from "./AssistantMessage";
import UserMessage from "./UserMessage";
import ChatSkeleton from "./ChatSkeleton";
import FileViewer from "./FileViewer";
import WebSearchSources from "./WebSearchSources";

const ChatPage = ({
  initialMessage: propsInitialMessage,
  userRole,
  selectedEngine = "11",
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
    console.log("🔍 pendingMessage 확인:", pendingMessage);
    console.log("🔍 propsInitialMessage 확인:", propsInitialMessage);
    if (pendingMessage) {
      console.log("📦 localStorage에서 메시지 복원:", pendingMessage);
      localStorage.removeItem('pendingMessage'); // 사용 후 즉시 삭제
      return pendingMessage;
    }
    return propsInitialMessage;
  });

  // localStorage에서 pendingFiles 확인
  const [initialFiles] = useState(() => {
    const pendingFiles = localStorage.getItem('pendingFiles');
    console.log("🔍 pendingFiles 확인:", pendingFiles);
    if (pendingFiles) {
      try {
        const files = JSON.parse(pendingFiles);
        console.log("📦 localStorage에서 파일 복원:", files);
        // pendingFiles는 메시지 전송 시에만 삭제하도록 변경
        // setTimeout(() => {
        //   localStorage.removeItem('pendingFiles');
        //   console.log("🗑️ pendingFiles 삭제됨");
        // }, 5000);
        return files;
      } catch (error) {
        console.error("파일 데이터 파싱 실패:", error);
        localStorage.removeItem('pendingFiles');
        return [];
      }
    }
    return [];
  });


  
  // URL에서 conversationId를 명시적으로 확인
  const urlConversationId = conversationId || window.location.pathname.split('/').pop();
  
  console.log("🔍 URL 확인:", {
    conversationId,
    urlConversationId,
    pathname: window.location.pathname,
    hasConversationId: !!urlConversationId && urlConversationId !== 'chat',
    locationState: location.state
  });
  
  // URL에 conversationId가 있으면 그것을 사용, 없으면 localStorage에서 확인
  const [currentConversationId, setCurrentConversationId] = useState(() => {
    if (urlConversationId && urlConversationId !== 'chat') {
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
    
    // 둘 다 없으면 새로 생성
    const newId = `${selectedEngine}_${Date.now()}`;
    console.log("🆕 새 conversationId 생성:", newId);
    return newId;
  });
  const [isLoadingConversation, setIsLoadingConversation] = useState(false);
  const [conversationSaved, setConversationSaved] = useState(false); // 대화 저장 여부 추적
  const [messages, setMessages] = useState(() => {
    console.log("🎯 ChatPage 초기화 - initialMessage:", initialMessage);
    console.log("🎯 URL conversationId:", urlConversationId);

    let hasCachedData = false;

    // URL에 conversationId가 있으면 먼저 캐시에서 복원 시도
    if (urlConversationId && urlConversationId !== 'chat' && urlConversationId !== selectedEngine.toLowerCase()) {
      console.log("🌐 URL에서 conversationId 감지, 캐시 확인 중...");
      
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
    // initialMessage가 있거나 파일이 있고, 캐시된 대화가 없는 경우
    if ((initialMessage || initialFiles.length > 0) && !hasCachedData) {
      // UI용 메시지 생성 - 파일이 있으면 content는 비우고 상자만 표시
      const initialUserMessage = {
        id: crypto.randomUUID(),
        type: "user",
        content: initialMessage || "", // content를 비우지 않고 그대로 유지
        files: initialFiles || [], // 파일 정보만 저장
        timestamp: new Date(),
      };
      
      console.log("📝 초기 사용자 메시지 생성:", {
        id: initialUserMessage.id,
        type: initialUserMessage.type,
        content: initialUserMessage.content,
        contentLength: initialUserMessage.content?.length,
        filesCount: initialFiles?.length || 0,
        files: initialFiles?.map(f => f.fileName) || [],
        fullFiles: initialFiles
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
    const loadConversationId = urlConversationId && urlConversationId !== 'chat' ? urlConversationId : null;
    
    console.log("🔄 대화 로딩 useEffect 트리거:", {
      loadConversationId,
      conversationId,
      urlConversationId,
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
            // 응답 null 체크 - 새로운 대화인 경우 초기 메시지 사용
            if (!response) {
              console.log("🆕 새로운 대화 - 초기 메시지 사용");
              console.log("🔍 초기 데이터 확인:", {
                initialMessage: initialMessage,
                initialMessageLength: initialMessage?.length,
                initialFiles: initialFiles,
                initialFilesLength: initialFiles?.length,
                hasInitialMessage: !!initialMessage,
                hasInitialFiles: initialFiles?.length > 0
              });
              
              // 초기 메시지가 있으면 사용
              if (initialMessage || initialFiles.length > 0) {
                const initialUserMessage = {
                  id: crypto.randomUUID(),
                  type: "user",
                  content: initialMessage || "",
                  files: initialFiles || [],
                  timestamp: new Date(),
                };
                console.log("📝 새 대화 초기 메시지 설정:", initialUserMessage);
                setMessages([initialUserMessage]);
              } else {
                console.warn("⚠️ 초기 메시지와 파일이 모두 비어있습니다");
              }
              setIsLoading(false);
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
              
              // 중복 메시지 제거
              const deduplicatedServerMessages = [];
              let lastServerMessage = null;

              for (const msg of conversationData.messages) {
                // 이전 메시지와 같은 타입이고 같은 내용이면 스킵
                if (lastServerMessage &&
                    lastServerMessage.type === msg.type &&
                    lastServerMessage.type === 'assistant' &&
                    lastServerMessage.content === msg.content) {
                  console.log("🔄 서버에서 받은 중복 AI 메시지 제거:", {
                    id: msg.id,
                    content: msg.content.substring(0, 50) + '...'
                  });
                  continue;
                }
                deduplicatedServerMessages.push(msg);
                lastServerMessage = msg;
              }

              const processedMessages = deduplicatedServerMessages.map((msg) => {
                let cleanContent = msg.content;
                let extractedFiles = msg.files || [];
                
                // 서버에서 복원된 사용자 메시지에서 파일 정보 추출
                if (msg.type === 'user' && cleanContent && cleanContent.includes('[파일:')) {
                  // 파일 이름 추출
                  const fileMatches = cleanContent.match(/\[파일: ([^\]]+)\]/g);
                  if (fileMatches && extractedFiles.length === 0) {
                    extractedFiles = fileMatches.map((match, index) => {
                      const fileName = match.replace(/\[파일: ([^\]]+)\]/, '$1');
                      const extension = fileName.split('.').pop().toLowerCase();
                      return {
                        id: Date.now() + index,
                        fileName: fileName,
                        fileType: extension === 'pdf' ? 'pdf' : 'txt',
                        fileSize: 0, // 서버에서 복원 시 크기 알 수 없음
                        pageCount: null
                      };
                    });
                  }
                  cleanContent = ''; // 파일이 포함된 사용자 메시지는 content 비우기
                }
                
                return {
                  ...msg,
                  content: cleanContent,
                  timestamp: new Date(msg.timestamp),
                  files: extractedFiles, // 추출된 파일 정보
                };
              });

              console.log("✅ 처리된 메시지들 (중복 제거 후):", processedMessages);
              
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
  
  // 모델 선택 상태
  const [selectedModel, setSelectedModel] = useState(() => {
    return localStorage.getItem('selectedModel') || 'claude-opus-4-6';
  });
  const [isModelDropdownOpen, setIsModelDropdownOpen] = useState(false);

  // 드롭다운 외부 클릭 시 닫기
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (isModelDropdownOpen && !event.target.closest('.model-dropdown')) {
        setIsModelDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isModelDropdownOpen]);
  
  // 파일 뷰어 사이드 패널 상태
  const [selectedFile, setSelectedFile] = useState(null);
  const [isFileViewerOpen, setIsFileViewerOpen] = useState(false);
  const dragCounterRef = useRef(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const textareaRef = useRef(null);
  const messagesEndRef = useRef(null);
  const scrollContainerRef = useRef(null);
  const [isProcessing, setIsProcessing] = useState(false); // 전역 처리 상태

  // 웹 검색 상태
  const [webSearchEnabled, setWebSearchEnabled] = useState(() => {
    return localStorage.getItem('webSearchEnabled') === 'true';
  });

  // 웹 검색 토글 함수
  const toggleWebSearch = () => {
    const newValue = !webSearchEnabled;
    setWebSearchEnabled(newValue);
    localStorage.setItem('webSearchEnabled', newValue.toString());
    toast.success(newValue ? '🌐 웹검색 활성화' : '웹검색 비활성화', {
      duration: 2000,
      position: 'top-center',
      style: {
        background: 'hsl(var(--bg-100))',
        color: 'hsl(var(--text-100))',
        border: '1px solid hsl(var(--border-300))',
      },
    });
  };

  // 웹검색 결과 상태
  const [webSearchStatus, setWebSearchStatus] = useState(null);
  const [webSearchResults, setWebSearchResults] = useState(null);
  const [searchMessageIndex, setSearchMessageIndex] = useState(0);
  const webSearchResultsRef = useRef(null);
  const searchIntervalRef = useRef(null);

  // 웹검색 상태 메시지 순환
  const SEARCH_MESSAGES = [
    "관련 뉴스를 찾고 있습니다...",
    "최신 기사를 수집하고 있습니다...",
    "출처를 확인하고 있습니다...",
    "정보를 정리하고 있습니다...",
  ];

  const [isConnected, setIsConnected] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const currentAssistantMessageId = useRef(null);
  const hasProcessedInitial = useRef(false);
  const expectedChunkIndex = useRef(0); // 청크 순서 추적
  const [usagePercentage, setUsagePercentage] = useState(null); // 사용량 퍼센티지 - null로 시작하여 로딩 상태 표시
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

  // WebSocket 메시지 핸들러를 useEffect 밖에서 정의
  const handleWebSocketMessageRef = useRef();

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

    // WebSocket 메시지 핸들러 정의
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

        case "web_search_start":
          // 웹검색 시작
          console.log("🔍 웹검색 시작:", message);
          setWebSearchStatus(message.message || SEARCH_MESSAGES[0]);

          // 기존 인터벌 클리어
          if (searchIntervalRef.current) {
            clearInterval(searchIntervalRef.current);
          }

          // 상태 메시지 순환 인터벌
          searchIntervalRef.current = setInterval(() => {
            setSearchMessageIndex((prev) => {
              const nextIndex = (prev + 1) % SEARCH_MESSAGES.length;
              setWebSearchStatus(SEARCH_MESSAGES[nextIndex]);
              return nextIndex;
            });
          }, 2000);

          // 인터벌 정리를 위한 타임아웃 (최대 30초)
          setTimeout(() => {
            if (searchIntervalRef.current) {
              clearInterval(searchIntervalRef.current);
              searchIntervalRef.current = null;
            }
          }, 30000);
          break;

        case "web_search_results":
          // 웹검색 결과 수신
          console.log("🌐 웹검색 결과 수신:", message);

          // 인터벌 클리어
          if (searchIntervalRef.current) {
            clearInterval(searchIntervalRef.current);
            searchIntervalRef.current = null;
          }
          setWebSearchStatus(null);

          // citations 또는 sources 필드 확인
          const citations = message.citations || message.sources || [];
          if (citations.length > 0) {
            const results = {
              query: message.query,
              sources: citations.map((c) => ({
                url: c.url,
                title: c.title || new URL(c.url).hostname,
                date: c.date,
              })),
            };
            setWebSearchResults(results);
            webSearchResultsRef.current = results;
            console.log("📚 웹검색 결과 저장:", results.sources.length, "개 출처");
          }
          break;

        case "ai_start":
          // AI 응답 시작 - 새 메시지 생성
          const newMessageId = Date.now();

          // 웹검색 인터벌/상태는 web_search_results에서 클리어 (메시지 순환 유지)

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

          // 웹검색이 꺼져있을 때 "답변 생성중..." 상태 표시
          if (!webSearchEnabled) {
            setWebSearchStatus("답변을 생성하고 있습니다...");
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
            
            // 타임아웃 오류 메시지 표시
            if (currentAssistantMessageId.current) {
              setMessages((prev) => 
                prev.map((msg) =>
                  msg.id === currentAssistantMessageId.current
                    ? { 
                        ...msg, 
                        content: "응답 시간이 초과되었습니다. 다시 시도해주세요.", 
                        isStreaming: false,
                        isError: true
                      }
                    : msg
                )
              );
            }
            
            setIsLoading(false);
            setError("응답 시간이 초과되었습니다. 다시 시도해주세요.");
            currentAssistantMessageId.current = null;
            setStreamingContent("");
            streamingContentRef.current = "";
            expectedChunkIndex.current = 0;
            chunkBuffer.current.clear();
            setIsProcessing(false); // 타임아웃 시 처리 상태 해제
          }, 300000);

          setMessages((prev) => {
            const newMessages = [
              ...prev,
              {
                id: newMessageId,
                type: "assistant",
                content: "",
                timestamp: new Date(),
                isStreaming: true,
              },
            ];
            console.log("✅ AI 메시지 컨테이너 추가:", {
              totalMessages: newMessages.length,
              assistantMessageId: newMessageId,
              messages: newMessages.map(m => ({
                id: m.id,
                type: m.type,
                content: m.content?.substring(0, 20),
                isStreaming: m.isStreaming
              }))
            });
            return newMessages;
          });

          // AI 응답 시작 시 해당 메시지가 보이도록 스크롤
          setTimeout(() => {
            if (scrollContainerRef.current) {
              scrollContainerRef.current.scrollTo({
                top: scrollContainerRef.current.scrollHeight,
                behavior: 'smooth'
              });
            }
          }, 100);
          break;

        case "ai_chunk":
          // 스트리밍이 종료되었으면 청크 무시
          if (!currentAssistantMessageId.current) {
            return; // 조용히 무시
          }

          // 첫 번째 청크 도착 시 "답변 생성중..." 상태 클리어 (웹검색 꺼진 경우)
          if ((message.chunk_index === 0 || message.chunk_index === undefined) && !webSearchEnabled) {
            setWebSearchStatus(null);
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
            const finalWebSearchResults = webSearchResultsRef.current;
            setMessages((prev) => {
              const updated = prev.map((msg) =>
                msg.id === currentAssistantMessageId.current
                  ? {
                      ...msg,
                      content: finalContent || msg.content,
                      isStreaming: false,
                      webSearchResults: finalWebSearchResults,
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
              console.log("🔍 대화 저장 조건 확인:", {
                currentConversationId,
                hasFinalContent: !!finalContent,
                finalContentLength: finalContent?.length,
                conversationSaved,
                willSave: !!(currentConversationId && finalContent && !conversationSaved)
              });
              
              if (currentConversationId && finalContent && !conversationSaved) {
                const messagesToSave = updated.filter((m) => !m.isStreaming && m.content);

                // 중복 메시지 제거 (같은 content를 가진 연속된 assistant 메시지 제거)
                const deduplicatedMessages = [];
                let lastMessage = null;

                for (const msg of messagesToSave) {
                  // 이전 메시지와 같은 타입이고 같은 내용이면 스킵
                  if (lastMessage &&
                      lastMessage.type === msg.type &&
                      lastMessage.type === 'assistant' &&
                      lastMessage.content === msg.content) {
                    console.log("🔄 중복 AI 메시지 제거:", {
                      id: msg.id,
                      content: msg.content.substring(0, 50) + '...'
                    });
                    continue;
                  }
                  deduplicatedMessages.push(msg);
                  lastMessage = msg;
                }

                // 메시지 형식 정규화 (프론트엔드와 백엔드 호환성)
                const normalizedMessages = deduplicatedMessages.map(msg => ({
                  id: msg.id,
                  role: msg.type === 'user' ? 'user' : 'assistant', // DynamoDB 저장용
                  type: msg.type, // 프론트엔드 호환성
                  content: msg.content,
                  files: msg.files || [], // 파일 정보 포함
                  timestamp: msg.timestamp || new Date().toISOString()
                }));
                
                const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
                // conversationService.js와 동일한 순서로 userId 가져오기
                const userId = userInfo.username || userInfo.userId || userInfo.email || 'anonymous';  // UUID 우선
                
                const conversationData = {
                  conversationId: currentConversationId,
                  userId: userId,
                  engineType: message.engine || selectedEngine,
                  messages: normalizedMessages,
                  title: messagesToSave[0]?.content?.substring(0, 50) || "New Conversation",
                };

                console.log("💾 AI 응답 완료, 전체 대화 저장:", {
                  conversationId: currentConversationId,
                  userId: userId,
                  engineType: conversationData.engineType,
                  messageCount: normalizedMessages.length,
                  messages: normalizedMessages.map(m => ({
                    role: m.role,
                    preview: m.content.substring(0, 30) + '...'
                  }))
                });

                import("../services/conversationService").then(
                  ({ saveConversation }) => {
                    saveConversation(conversationData)
                      .then((result) => {
                        console.log("✅ 대화 저장 성공:", result);
                        setConversationSaved(true); // 대화 저장됨 표시
                        // 사이드바 새로고침
                        window.dispatchEvent(new CustomEvent("refreshSidebar"));
                        if (onNewConversation) {
                          onNewConversation();
                        }
                      })
                      .catch((error) =>
                        console.error("❌ 대화 저장 실패:", error)
                      );
                  }
                );
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
            setIsProcessing(false); // 처리 상태 해제

            // 🔑 웹검색 상태 초기화 (다음 메시지에 영향 안주도록)
            setWebSearchStatus(null);
            setWebSearchResults(null);
            webSearchResultsRef.current = null;

            console.log("🧹 스트리밍 상태 완전 초기화 완료");
          });
          break;

        case "chat_error":
        case "error":
          console.error("❌ WebSocket 오류:", message.message);
          
          // 오류 메시지를 UI에 표시
          if (currentAssistantMessageId.current) {
            setMessages((prev) => 
              prev.map((msg) =>
                msg.id === currentAssistantMessageId.current
                  ? { 
                      ...msg, 
                      content: `오류가 발생했습니다: ${message.message || "알 수 없는 오류"}`, 
                      isStreaming: false,
                      isError: true
                    }
                  : msg
              )
            );
          } else {
            // 스트리밍 중이 아니면 새 오류 메시지 추가
            const errorMessage = {
              id: crypto.randomUUID(),
              type: "assistant",
              content: `오류가 발생했습니다: ${message.message || "알 수 없는 오류"}`,
              timestamp: new Date(),
              isError: true,
            };
            setMessages((prev) => [...prev, errorMessage]);
          }
          
          setError(message.message || "오류가 발생했습니다");
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
          setIsProcessing(false); // 오류 시 처리 상태 해제
          break;
      }
    };

    // ref에 저장하여 cleanup에서 동일한 참조 사용
    handleWebSocketMessageRef.current = handleWebSocketMessage;

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
        // 초기 메시지가 있거나 파일이 있는 경우 자동 전송
        const hasInitialText = !!(initialMessage && initialMessage.trim());
        const hasInitialFiles = initialFiles && initialFiles.length > 0;
        const hasInitialContent = hasInitialText || hasInitialFiles;
        const shouldSendInitial = hasInitialContent && !hasProcessedInitial.current && isFromMainPage && !alreadyProcessed && hasOnlyInitialUserMessage;
        
        console.log("🔍 초기 메시지 전송 여부 확인:", {
          initialMessage: !!initialMessage,
          hasInitialText,
          initialFiles: initialFiles.length,
          hasInitialFiles,
          hasInitialContent,
          hasProcessedInitial: hasProcessedInitial.current,
          isFromMainPage,
          alreadyProcessed,
          hasOnlyInitialUserMessage,
          shouldSendInitial,
          urlConversationId,
          locationState: location.state
        });
        
        if (shouldSendInitial) {
          hasProcessedInitial.current = true;
          // sessionStorage에 처리 완료 표시
          sessionStorage.setItem(processedKey, 'true');
          console.log(
            "📝 초기 콘텐츠 감지 및 자동 전송 시작:",
            {
              hasText: !!(initialMessage?.trim()),
              hasFiles: initialFiles?.length > 0,
              textPreview: initialMessage?.substring(0, 50),
              fileNames: initialFiles?.map(f => f.fileName) || []
            }
          );

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
              
              // UI용 메시지 생성 - 사용자 텍스트는 항상 표시
              const displayContent = initialMessage || ""; // 사용자 텍스트는 항상 표시
              
              setMessages((currentMessages) => {
                const existingUserMessage = currentMessages.find(m => 
                  m.type === 'user' && m.content === displayContent
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
                    content: displayContent, // UI용 텍스트만 저장
                    files: initialFiles, // 파일 정보는 별도로 처리
                    timestamp: new Date(),
                    idempotencyKey,
                  };
                  userMessageRef.current = newUserMessage;
                  console.log("➕ 새 사용자 메시지 추가:", {
                    ...newUserMessage,
                    filesDetail: newUserMessage.files
                  });
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
                  // 서버로 전송할 전체 메시지 구성 (파일 내용 포함)
                  let fullMessageForServer = initialMessage?.trim() || '';
                  
                  if (initialFiles && initialFiles.length > 0) {
                    const fileContents = initialFiles.map(file => 
                      `[파일: ${file.fileName}]\n${file.content}`
                    ).join('\n\n');
                    
                    if (fullMessageForServer) {
                      fullMessageForServer = fullMessageForServer + '\n\n' + fileContents;
                    } else {
                      // 파일만 있고 텍스트가 없으면 기본 메시지 추가
                      fullMessageForServer = '이 파일을 분석해주세요.\n\n' + fileContents;
                    }
                  }
                  
                  console.log("📤 초기 메시지 서버 전송:", {
                    hasText: !!(initialMessage?.trim()),
                    hasFiles: initialFiles?.length > 0,
                    fileCount: initialFiles?.length || 0,
                    messageLength: fullMessageForServer.length,
                    preview: fullMessageForServer.substring(0, 100) + "..."
                  });
                  
                  // 버디 서비스 설정 가져오기
                  const currentBuddyType = localStorage.getItem('currentBuddyType');
                  const buddyService = currentBuddyType ? getBuddyConfig(currentBuddyType) : null;
                  
                  console.log('🎯 버디 서비스 전송:', { currentBuddyType, buddyService });
                  
                  // 서버에는 파일 내용이 포함된 전체 메시지 전송
                  await sendChatMessage(
                    fullMessageForServer,
                    selectedEngine,
                    [],
                    currentConversationId,
                    userMessage?.idempotencyKey || crypto.randomUUID(),
                    selectedModel,
                    webSearchEnabled,
                    buddyService
                  );
                  sendSuccess = true;
                  console.log("✅ Initial message 전송 완료");
                  
                  // === 초기 메시지 전송 후 임시 저장소 정리 ===
                  localStorage.removeItem('pendingFiles'); // 임시 파일 저장소 비우기
                  console.log("🧹 초기 메시지 전송 후 임시 저장소 정리 완료");

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

      // WebSocket 메시지 핸들러 제거 - ref의 동일한 참조 사용
      if (handleWebSocketMessageRef.current) {
        removeMessageHandler(handleWebSocketMessageRef.current);
        handleWebSocketMessageRef.current = null;
      }

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

  const handleStopGeneration = () => {
    // 스트리밍 중단
    if (currentAssistantMessageId.current) {
      const currentContent = streamingContentRef.current || streamingContent;
      
      // 스트리밍 중인 메시지를 완료 상태로 변경 (현재 내용 유지)
      setMessages((prev) => 
        prev.map((msg) =>
          msg.isStreaming
            ? { ...msg, isStreaming: false, content: currentContent }
            : msg
        )
      );
      
      // 모든 타임아웃 클리어
      if (streamingTimeoutRef.current) {
        clearTimeout(streamingTimeoutRef.current);
        streamingTimeoutRef.current = null;
      }
      if (processBufferTimeoutRef.current) {
        clearTimeout(processBufferTimeoutRef.current);
        processBufferTimeoutRef.current = null;
      }
      
      // 상태 초기화
      currentAssistantMessageId.current = null;
      setStreamingContent("");
      streamingContentRef.current = "";
      expectedChunkIndex.current = 0;
      chunkBuffer.current.clear();
      setIsLoading(false);
      setIsProcessing(false);
    }
  };

  const handleSendMessage = async (messageText, fileInfo) => {
    console.error("🔥🔥🔥 handleSendMessage 호출됨!", { messageText, fileInfo });
    
    // 이전 응답이 진행 중이면 자동 중지
    if (currentAssistantMessageId.current || isLoading) {
      console.log("이전 AI 응답 중지 후 새 메시지 전송");
      handleStopGeneration();
      // 중지 후 짧은 대기 시간
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    // 이미 처리 중이면 차단
    if (isProcessing) {
      console.log("이미 처리 중이므로 메시지 전송 차단");
      return;
    }
    
    // 처리 시작 플래그 설정
    setIsProcessing(true);
    
    // 텍스트가 없어도 파일이 있으면 전송 가능
    if ((!messageText?.trim() && (!fileInfo || fileInfo.length === 0))) return;

    // === 데이터 분리 구조 ===
    // 1. 임시 텍스트 저장소
    const userInputText = messageText?.trim() || '';
    
    // 2. 임시 파일 저장소 (파일 내용) - 새로운 파일만 처리
    const fileContentsForServer = fileInfo && fileInfo.length > 0 ? 
      fileInfo.map(file => `\n\n--- 파일: ${file.fileName} ---\n${file.content}`).join('\n') : '';
    
    // 3. 서버에 보낼 저장소 (임시 텍스트 + 새로운 파일 내용만)
    let fullMessageForServer = userInputText + fileContentsForServer;
    
    // 파일만 있고 텍스트가 없으면 기본 메시지 추가
    if (!userInputText && fileInfo && fileInfo.length > 0) {
      fullMessageForServer = '이 파일을 분석해주세요.' + fileContentsForServer;
    }
    
    // 4. UI 채팅에 보낼 저장소 (텍스트 + 파일 카드만)
    const fileCardsForUI = fileInfo ? fileInfo.map(file => ({
      fileName: file.fileName,
      fileType: file.fileType,
      fileSize: file.fileSize,
      // content는 UI에 포함하지 않음 (카드만 표시)
    })) : [];

    const id = crypto.randomUUID();
    const idempotencyKey = crypto.randomUUID();
    
    // UI에 표시할 메시지 (사용자 입력 텍스트 + 파일 카드)
    const userMessage = {
      id,
      type: "user",
      content: userInputText || (fileInfo && fileInfo.length > 0 ? "이 파일을 분석해주세요." : ""), // 파일만 있으면 기본 메시지 표시
      files: fileCardsForUI, // 파일 카드만 (내용 제외)
      timestamp: new Date(),
      idempotencyKey,
    };
    
    // 데이터 분리 확인 로그
    console.log("📤 서버 전송용 (텍스트+파일내용):", {
      userInputText: userInputText,
      hasNewFiles: fileInfo && fileInfo.length > 0,
      fullMessageForServer: fullMessageForServer.substring(0, 100) + "...",
      messageLength: fullMessageForServer.length,
      fileCount: fileInfo?.length || 0
    });
    
    console.log("📱 UI 표시용 (텍스트+파일카드):", {
      userInputText: userInputText,
      fileCards: fileCardsForUI.map(f => ({ fileName: f.fileName, fileType: f.fileType })),
      fileCardCount: fileCardsForUI.length
    });

    setMessages((prev) => [...prev, userMessage]);
    lastUserMessageRef.current = userMessage; // 마지막 사용자 메시지 저장
    
    // === 임시 저장소 정리 (다음 채팅과 중복 방지) ===
    // 1. UI 입력 필드 초기화
    setCurrentMessage(""); // 임시 텍스트 저장소 비우기
    setUploadedFiles([]); // UI 파일 목록 초기화
    
    // 2. localStorage 임시 데이터 정리
    localStorage.removeItem('pendingFiles'); // 임시 파일 저장소 비우기
    
    // 3. 상태 초기화
    setIsTyping(false);
    setIsLoading(true);
    setError(null);
    
    console.log("🧹 임시 저장소 정리 완료 - 다음 채팅 준비됨");

    // textarea 높이 리셋
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    // 새 메시지가 화면에 보이도록 스크롤 (한 번만)
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
        console.log(
          `${selectedEngine} 엔진으로 메시지 전송:`,
          userMessage.content
        );

        // WebSocket으로 메시지 전송 시에도 ref 업데이트
        lastUserMessageRef.current = userMessage;

        // 버디 서비스 설정 가져오기
        const currentBuddyType = localStorage.getItem('currentBuddyType');
        const buddyService = currentBuddyType ? getBuddyConfig(currentBuddyType) : null;
        
        console.log('🎯 버디 서비스 전송:', { currentBuddyType, buddyService });

        await sendChatMessage(
          fullMessageForServer, // 파일 내용이 포함된 메시지를 서버로 전송
          selectedEngine,
          [], // 대화 히스토리 제거 - 마지막 메시지만 처리
          currentConversationId,
          userMessage.idempotencyKey,
          selectedModel,
          webSearchEnabled,
          buddyService
        );

        // WebSocket 응답은 메시지 핸들러에서 처리됨
        // 스크롤은 메시지가 추가될 때 자동으로 처리
      } else {
        // WebSocket 연결이 안된 경우 재연결 시도
        console.warn("WebSocket이 연결되지 않았습니다. 재연결 시도 중...");
        await connectWebSocket();
        setIsConnected(true);

        // 버디 서비스 설정 가져오기
        const currentBuddyType = localStorage.getItem('currentBuddyType');
        const buddyService = currentBuddyType ? getBuddyConfig(currentBuddyType) : null;
        
        // 재연결 후 메시지 전송 (대화 히스토리 제거)
        await sendChatMessage(
          userMessage.content,
          selectedEngine,
          [], // 대화 히스토리 제거 - 마지막 메시지만 처리
          currentConversationId,
          userMessage.idempotencyKey,
          selectedModel,
          webSearchEnabled,
          buddyService
        );
      }
    } catch (err) {
      console.error("메시지 전송 오류:", err);
      setError(err.message || "메시지 전송 중 오류가 발생했습니다.");
      setIsLoading(false);
      setIsProcessing(false); // 오류 시 처리 상태 해제

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

  // 파일 뷰어 핸들러
  const handleFileCardClick = (file) => {
    console.log("📄 파일 카드 클릭:", file.fileName);
    setSelectedFile(file);
    setIsFileViewerOpen(true);
  };

  const handleCloseFileViewer = () => {
    setIsFileViewerOpen(false);
    setSelectedFile(null);
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

    // 파일 확장자 추출
    const extension = fileInfo.fileName.split('.').pop().toLowerCase();

    // 파일 정보를 배열에 추가
    const newFile = {
      id: Date.now() + Math.random(),
      fileName: fileInfo.fileName,
      fileType: extension === 'pdf' ? 'pdf' : 'txt',  // 확장자 기반으로 타입 설정
      fileSize: fileInfo.fileSize,
      pageCount: fileInfo.pageCount,
      content: content,
    };
    setUploadedFiles((prev) => [...prev, newFile]);

    // 파일이 업로드되면 전송 버튼 활성화
    setIsTyping(true);

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
    // 텍스트가 있거나 파일이 업로드되면 typing 상태로 설정
    setIsTyping(e.target.value.length > 0 || uploadedFiles.length > 0);

    // 자동 크기 조절
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      // 생성 중일 때는 아무 동작 안함
      if (currentAssistantMessageId.current) {
        return;
      }
      
      // 현재 업로드된 파일만 전달 (이전 파일 제외)
      console.log("🔍 Enter 키 전송 - 현재 uploadedFiles:", uploadedFiles);
      const currentFiles = uploadedFiles.filter(file => file.id); // 유효한 파일만
      handleSendMessage(currentMessage, currentFiles.map(file => ({
        fileName: file.fileName,
        fileType: file.fileType,
        fileSize: file.fileSize,
        pageCount: file.pageCount,
        content: file.content
      })));
    }
  };

  // 파일 업로드 상태 변경 시 전송 버튼 활성화
  useEffect(() => {
    if (uploadedFiles.length > 0) {
      setIsTyping(true);
    } else if (!currentMessage.trim()) {
      setIsTyping(false);
    }
  }, [uploadedFiles.length, currentMessage]);

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
    <div className="flex h-screen" 
         onDragEnter={handleDragEnter}
         onDragLeave={handleDragLeave}
         onDragOver={handleDragOver}
         onDrop={handleDrop}>
      {/* 메인 채팅 영역 */}
      <div className={`flex flex-col transition-all duration-300 ${isFileViewerOpen ? 'w-1/2' : 'w-full'}`}>
      {/* Drag Overlay */}
      {isDragging && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-lg">
          <div className="relative">
            <div
              className="w-96 h-48 rounded-2xl flex flex-col items-center justify-center gap-4 transition-all duration-200"
              style={{
                background: "transparent",
              }}
            >
              <div className="flex flex-col items-center gap-3">
                <div className="w-16 h-16 rounded-full bg-white/10 flex items-center justify-center animate-bounce">
                  <svg
                    className="w-8 h-8 text-white"
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
                  <h3 className="text-lg text-white mb-1">
                    여기에 파일을 드롭하여 대화에 추가하세요
                  </h3>
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
        <div 
          className="flex-1 overflow-y-auto" 
          ref={scrollContainerRef}

        >
          <div
            className={clsx(
              "mx-auto px-16 pt-6 pb-10",
              userRole === "admin" ? "max-w-3xl" : "max-w-4xl"
            )}
          >
            {/* Loading Skeleton */}
            {isLoadingConversation && (
              <ChatSkeleton />
            )}
            
            {/* AI 응답 대기 중 표시 */}
            {isLoading && !currentAssistantMessageId.current && (
              <div className="mb-6 last:mb-0 flex justify-start px-4">
                <div className="max-w-[80%] flex flex-col items-start gap-3">
                  <div
                    className="px-4 py-3 rounded-2xl break-words"
                    style={{
                      backgroundColor: "hsl(var(--bg-200))",
                      color: "hsl(var(--text-100))",
                      fontFamily: '"Tiempos Text", "Source Serif 4", "Noto Serif KR", serif',
                      fontSize: "1rem",
                      lineHeight: "1.5rem",
                    }}
                  >
                    답변 생성중...
                  </div>
                </div>
              </div>
            )}

            {/* Messages */}
            {!isLoadingConversation && (
              <>
                {messages.map((message) => {
                  return (
                    <div
                      key={message.id}
                      data-test-render-count="8"
                      data-message-type={message.type}
                    >
                      {message.type === "user" ? (
                        <UserMessage 
                          content={message.content}
                          timestamp={message.timestamp}
                          files={message.files}
                          onFileClick={handleFileCardClick}
                        />
                      ) : message.isStreaming ? (
                        <StreamingAssistantMessage
                          content={streamingContent || ""}
                          isStreaming={message.isStreaming}
                          timestamp={message.timestamp}
                          messageId={message.id}
                          webSearchStatus={webSearchStatus}
                          webSearchResultsUI={
                            webSearchResults && (
                              <WebSearchSources
                                query={webSearchResults.query}
                                sources={webSearchResults.sources}
                              />
                            )
                          }
                        />
                      ) : (
                        <AssistantMessage
                          content={message.content}
                          timestamp={message.timestamp}
                          messageId={message.id}
                          webSearchResultsUI={
                            message.webSearchResults && (
                              <WebSearchSources
                                query={message.webSearchResults.query}
                                sources={message.webSearchResults.sources}
                              />
                            )
                          }
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
          "mx-auto w-full pb-7 -mt-6",
          userRole === "admin" ? "max-w-3xl" : "max-w-4xl"
        )}>

          <fieldset className="flex w-full min-w-0 flex-col px-16">
            <div
              className="!box-content flex flex-col items-stretch transition-all duration-200 relative cursor-text z-10 rounded-2xl border border-transparent hover:border-border-300/25"
              style={{
                backgroundColor: "hsl(var(--bg-000))",
                boxShadow: "0 0.25rem 1.25rem hsl(var(--always-black)/3.5%)",
                overflow: "visible",
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
              {/* File Preview Section - 채팅박스 내부 상단 */}
              {uploadedFiles.length > 0 && (
                <div className="p-3.5 pb-0">
                  <div className="flex flex-row overflow-x-auto gap-3 pb-3.5">
                    {uploadedFiles.map((file) => (
                      <div key={file.id} className="relative">
                        <div
                          className="group/thumbnail"
                          data-testid="file-thumbnail"
                        >
                          <div
                            className="rounded-lg text-left block cursor-pointer font-ui transition-all rounded-lg border-0.5 border-border-300/25 flex flex-col justify-between gap-2.5 overflow-hidden px-2.5 py-2 bg-bg-100 hover:border-border-200/50 hover:shadow-always-black/10 shadow-sm shadow-always-black/5"
                            style={{
                              width: "120px",
                              height: "120px",
                              minWidth: "120px",
                              backgroundColor: "hsl(var(--bg-100))",
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
                              setUploadedFiles((prev) => {
                                const newFiles = prev.filter((f) => f.id !== file.id);
                                // 파일이 모두 삭제되고 텍스트도 없으면 전송 버튼 비활성화
                                if (newFiles.length === 0 && !currentMessage.trim()) {
                                  setIsTyping(false);
                                }
                                return newFiles;
                              });
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
              
              <div className="flex flex-col gap-1 mx-2.5 mt-0.5 mb-1" style={{ overflow: "visible" }}>
                <div className="relative">
                  <div className="max-h-96 w-full overflow-y-auto font-large break-words transition-opacity duration-200 min-h-[1.5rem]">
                    <textarea
                      ref={textareaRef}
                      value={currentMessage}
                      onChange={handleInputChange}
                      onKeyDown={handleKeyDown}
                      placeholder={
                        selectedEngine === "11"
                          ? '아이디어를 입력하세요. 막연해도 괜찮습니다.\n단어 하나, 메모, 보도자료, "오늘 뭐 쓰지?"... 모두 OK'
                          : '일보와 취재 내용을 입력하세요. 부족해도 괜찮습니다.\n일보만, 팩트 추가, 보도자료, "첫 문장이 안 써져"... 모두 OK'
                      }
                      className="w-full min-h-[1.5rem] max-h-96 resize-none bg-transparent border-none outline-none text-text-100 placeholder-text-500 font-large leading-relaxed"
                      rows={1}
                      style={{
                        paddingTop: "10px",
                        paddingBottom: "20px",
                        fieldSizing: "content",
                        overflow: "hidden",
                      }}
                    />
                  </div>
                </div>

                <div className="flex gap-2.5 w-full items-center" style={{ overflow: "visible" }}>
                  <div className="relative flex-1 flex items-center gap-2 shrink min-w-0">
                    {/* File Upload Button */}
                    <div className="relative shrink-0">
                      <FileUploadButton
                        ref={fileUploadRef}
                        onFileContent={handleFileContent}
                        disabled={false}
                      />
                    </div>

                    {/* Web Search Toggle */}
                    <button
                      onClick={toggleWebSearch}
                      className={clsx(
                        "inline-flex items-center justify-center h-8 w-8 rounded-md transition-all duration-200",
                        webSearchEnabled
                          ? "bg-blue-500/20 text-blue-500 hover:bg-blue-500/30"
                          : "text-text-400 hover:text-text-200 hover:bg-bg-200"
                      )}
                      title={webSearchEnabled ? "웹검색 끄기" : "웹검색 켜기"}
                    >
                      <Globe size={16} />
                    </button>
                  </div>

                  {/* Model Selector - 화살표 버튼 왼쪽 */}
                  <div className="relative shrink-0 model-dropdown">
                    <button
                      onClick={() => setIsModelDropdownOpen(!isModelDropdownOpen)}
                      className="inline-flex items-center justify-center gap-1 px-2 py-1.5 text-xs font-medium rounded-md border transition-colors"
                      style={{
                        backgroundColor: "hsl(var(--bg-100))",
                        borderColor: "hsl(var(--border-300)/25%)",
                        color: "hsl(var(--text-300))",
                      }}
                    >
                      <span className="truncate max-w-20">
                        {selectedModel === 'claude-opus-4-6' ? 'Opus 4.6' :
                         selectedModel === 'claude-opus-4-5-20251101' ? 'Opus 4.5' : 'Opus 4.6'}
                      </span>
                      <svg
                        className={`w-3 h-3 transition-transform ${
                          isModelDropdownOpen ? 'rotate-180' : ''
                        }`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M19 9l-7 7-7-7"
                        />
                      </svg>
                    </button>
                    
                    {/* Dropdown Menu */}
                    {isModelDropdownOpen && (
                      <div
                        className="absolute bottom-full mb-2 left-0 rounded-lg border shadow-lg"
                        style={{
                          minWidth: "227px",
                          backgroundColor: "hsl(var(--bg-000))",
                          borderColor: "hsl(var(--border-300)/25%)",
                          boxShadow: "0 4px 12px hsl(var(--always-black)/10%)",
                          zIndex: 9999,
                        }}
                      >
                        <div className="p-1">
                          {[
                            { id: 'claude-opus-4-6', name: 'Opus 4.6', desc: 'Latest & most capable (default)' },
                            { id: 'claude-opus-4-5-20251101', name: 'Opus 4.5', desc: 'Previous flagship model' }
                          ].map((model) => (
                            <button
                              key={model.id}
                              onClick={() => {
                                setSelectedModel(model.id);
                                localStorage.setItem('selectedModel', model.id);
                                setIsModelDropdownOpen(false);
                              }}
                              style={{
                                width: '100%',
                                textAlign: 'left',
                                padding: '0.5rem 0.75rem',
                                borderRadius: '0.375rem',
                                transition: 'all 0.2s',
                                backgroundColor: selectedModel === model.id ? 'hsl(var(--accent-main-100) / 0.1)' : 'transparent',
                                color: selectedModel === model.id ? 'hsl(var(--accent-main-100))' : 'hsl(var(--text-100))',
                                cursor: 'pointer',
                                border: 'none',
                              }}
                              onMouseEnter={(e) => {
                                if (selectedModel !== model.id) {
                                  e.currentTarget.style.backgroundColor = 'hsl(var(--bg-100))';
                                }
                              }}
                              onMouseLeave={(e) => {
                                if (selectedModel !== model.id) {
                                  e.currentTarget.style.backgroundColor = 'transparent';
                                }
                              }}
                            >
                              <div className="flex flex-col">
                                <span className="text-sm font-medium">{model.name}</span>
                                <span className="text-xs opacity-70">{model.desc}</span>
                              </div>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Send/Stop Button */}
                  <div style={{ opacity: 1, transform: "none" }}>
                    {currentAssistantMessageId.current ? (
                      <button
                        className="inline-flex items-center justify-center relative shrink-0 can-focus select-none font-base-bold transition-colors h-8 w-8 rounded-md active:scale-95 !rounded-lg !h-8 !w-8 bg-gray-500 text-white hover:bg-black"
                        type="button"
                        onClick={handleStopGeneration}
                        aria-label="생성 중단"
                      >
                        <Square size={12} fill="currentColor" />
                      </button>
                    ) : (
                      <button
                        className="inline-flex items-center justify-center relative shrink-0 can-focus select-none disabled:pointer-events-none disabled:opacity-50 disabled:shadow-none disabled:drop-shadow-none font-base-bold transition-colors h-8 w-8 rounded-md active:scale-95 !rounded-lg !h-8 !w-8"
                        style={{
                          background: (isTyping || uploadedFiles.length > 0) && !currentAssistantMessageId.current && !isLoading
                            ? "#ff6b35"
                            : "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",
                          color: "white",
                          opacity: (!isTyping && uploadedFiles.length === 0) || isProcessing || currentAssistantMessageId.current || isLoading ? "0.5" : "1",
                          cursor: (!isTyping && uploadedFiles.length === 0) || isProcessing || currentAssistantMessageId.current || isLoading ? "not-allowed" : "pointer"
                        }}
                        onMouseEnter={(e) => {
                          if ((isTyping || uploadedFiles.length > 0) && !currentAssistantMessageId.current && !isLoading) {
                            e.target.style.background = "#e55a2b";
                          }
                        }}
                        onMouseLeave={(e) => {
                          if ((isTyping || uploadedFiles.length > 0) && !currentAssistantMessageId.current && !isLoading) {
                            e.target.style.background = "#ff6b35";
                          }
                        }}
                        disabled={(!isTyping && uploadedFiles.length === 0) || isProcessing || currentAssistantMessageId.current || isLoading}
                        type="button"
                        onClick={() => {
                          // 현재 업로드된 파일만 전달 (이전 파일 제외)
                          console.log("🔍 전송 버튼 클릭 - 현재 uploadedFiles:", uploadedFiles);
                          const currentFiles = uploadedFiles.filter(file => file.id); // 유효한 파일만
                          handleSendMessage(currentMessage, currentFiles.map(file => ({
                            fileName: file.fileName,
                            fileType: file.fileType,
                            fileSize: file.fileSize,
                            pageCount: file.pageCount,
                            content: file.content
                          })));
                        }}
                        aria-label="메시지 보내기"
                      >
                        <ArrowUp size={16} />
                      </button>
                    )}
                  </div>
                </div>
              </div>


            </div>
          </fieldset>
        </div>
      </div>
      
      </div>
      
      {/* 파일 뷰어 사이드 패널 */}
      {isFileViewerOpen && (
        <div className="w-1/2 border-l" style={{ borderColor: "hsl(var(--border-300)/25%)" }}>
          <FileViewer 
            file={selectedFile}
            isOpen={isFileViewerOpen}
            onClose={handleCloseFileViewer}
          />
        </div>
      )}
    </div>
  );
};



export default ChatPage;
