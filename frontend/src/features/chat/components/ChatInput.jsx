import React, {
  useState,
  useRef,
  useEffect,
  useCallback,
  forwardRef,
  useImperativeHandle,
} from "react";
import { ArrowUp, Globe } from "lucide-react";
import clsx from "clsx";
import FileUploadButton from "./FileUploadButton";
import toast from "react-hot-toast";
import {
  connectWebSocket,
  sendChatMessage,
  isWebSocketConnected,
  reconnectForBuddy,
} from '../services/websocketService';
import { getBuddyConfig } from '../../../config/buddyServiceConfig';

const ChatInput = forwardRef(
  (
    { onSendMessage, onStartChat, onTitlesGenerated, engineType = "11", showModelSelector = false },
    ref
  ) => {
    const [message, setMessage] = useState("");
    const [isTyping, setIsTyping] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [isConnected, setIsConnected] = useState(false);
    const [uploadedFiles, setUploadedFiles] = useState([]);
    const [isDragging, setIsDragging] = useState(false);
    const [selectedBuddyInfo, setSelectedBuddyInfo] = useState(null);
    const [currentBuddyService, setCurrentBuddyService] = useState(null);
    const [showAllTools, setShowAllTools] = useState(false);
    const textareaRef = useRef(null);
    const fileUploadRef = useRef(null);
    const dragCounterRef = useRef(0);
    
    // Claude 모델 선택 상태
    const [selectedModel, setSelectedModel] = useState('claude-opus-4-6');
    const [isModelDropdownOpen, setIsModelDropdownOpen] = useState(false);

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

    // WebSocket 연결 관리
    useEffect(() => {
      const initWebSocket = async () => {
        try {
          // 현재 버디 타입 가져오기
          const currentBuddyType = localStorage.getItem('currentBuddyType');

          if (!isWebSocketConnected()) {
            console.log("WebSocket 연결 시도... 버디:", currentBuddyType || "기본");
            await connectWebSocket(currentBuddyType);
            setIsConnected(true);
            console.log("WebSocket 연결 성공!");
          } else {
            setIsConnected(true);
          }
        } catch (error) {
          console.error("WebSocket 연결 실패:", error);
          setIsConnected(false);
        }
      };

      initWebSocket();

      // 컴포넌트 언마운트 시 정리
      return () => {
        // disconnectWebSocket(); // 앱 전체에서 공유하므로 여기서 끊지 않음
      };
    }, []);

    // 드래그 앤 드롭 이벤트 핸들러
    const handleDragEnter = useCallback((e) => {
      e.preventDefault();
      e.stopPropagation();
      dragCounterRef.current += 1;
      if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
        setIsDragging(true);
      }
    }, []);

    const handleDragLeave = useCallback((e) => {
      e.preventDefault();
      e.stopPropagation();
      dragCounterRef.current -= 1;
      if (dragCounterRef.current === 0) {
        setIsDragging(false);
      }
    }, []);

    const handleDragOver = useCallback((e) => {
      e.preventDefault();
      e.stopPropagation();
    }, []);

    // 파일 처리 함수 (외부에서도 호출 가능)
    const handleDroppedFiles = async (files) => {
      if (files.length > 0) {
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
      }
    };

    const handleDrop = useCallback(async (e) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);
      dragCounterRef.current = 0;

      const files = Array.from(e.dataTransfer.files);
      await handleDroppedFiles(files);
    }, []);

    // 외부에서 사용할 수 있도록 ref로 노출
    useImperativeHandle(ref, () => ({
      handleDroppedFiles,
    }));

    // 파일 업로드 처리
    const handleFileContent = (content, fileInfo) => {
      console.log("파일 업로드됨:", fileInfo);

      // 파일 정보를 배열에 추가 (내용은 입력창에 추가하지 않음)
      const newFile = {
        id: Date.now() + Math.random(),
        fileName: fileInfo.fileName,
        fileType: fileInfo.fileType,
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
        // 높이 자동 조절
        textareaRef.current.style.height = "auto";
        textareaRef.current.style.height =
          textareaRef.current.scrollHeight + "px";
      }
    };

    // 파일 제거
    const removeFile = (fileId) => {
      setUploadedFiles((prev) => {
        const newFiles = prev.filter((f) => f.id !== fileId);
        // 파일이 모두 삭제되고 텍스트도 없으면 전송 버튼 비활성화
        if (newFiles.length === 0 && !message.trim()) {
          setIsTyping(false);
        }
        return newFiles;
      });
    };

    const isProcessingRef = useRef(false); // 중복 제출 방지용
    
    const handleSubmit = async (e) => {
      e.preventDefault();
      
      // 이미 처리 중이면 무시
      if (isProcessingRef.current) {
        console.log("⚠️ 이미 메시지 처리 중, 중복 호출 방지");
        return;
      }

      // 텍스트가 있거나 파일이 업로드되어 있으면 전송 가능
      if ((message.trim() || uploadedFiles.length > 0) && !isLoading) {
        const messageText = message.trim();
        
        // 처리 시작 표시
        isProcessingRef.current = true;

        // onStartChat가 있으면 ChatPage로 네비게이션 (MainContent에서 사용)
        // 이 경우 WebSocket 메시지는 ChatPage에서 전송됨
        if (onStartChat) {
          console.log("🔄 ChatInput: onStartChat 경로 사용");
          if (uploadedFiles.length > 0) {
            // 파일 데이터를 localStorage에 저장 (ChatPage에서 사용)
            const fileData = uploadedFiles.map(file => ({
              fileName: file.fileName,
              fileType: file.fileType,
              fileSize: file.fileSize,
              pageCount: file.pageCount,
              content: file.content
            }));
            localStorage.setItem('pendingFiles', JSON.stringify(fileData));
            console.log("💾 파일 데이터 localStorage 저장:", fileData.length, "개");
          }
          
          // 선택된 모델도 localStorage에 저장
          localStorage.setItem('selectedModel', selectedModel);
          console.log("🎯 선택된 모델 저장:", selectedModel);
          
          console.log("🔀 ChatPage로 네비게이션 - 메시지:", messageText);
          // 메시지 초기화를 먼저 하여 중복 호출 방지
          setMessage("");
          setIsTyping(false);
          setUploadedFiles([]);
          if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
            textareaRef.current.value = ""; // textarea 값도 직접 초기화
          }
          
          // 페이지 전환 후 즉시 플래그 리셋
          setTimeout(() => {
            isProcessingRef.current = false;
          }, 100);
          
          // 사용자 텍스트만 전달 (파일은 localStorage로 분리)
          onStartChat(messageText, selectedModel);
          
          return; // 여기서 종료
        }

        // onSendMessage가 있으면 현재 페이지에서 처리 (ChatPage에서 사용)
        if (onSendMessage && typeof onSendMessage === 'function') {
          console.log("🔄 ChatInput: onSendMessage 경로 사용");
          // 파일 정보를 별도로 전달 (ChatPage와 동일한 구조)
          const fileInfo = uploadedFiles.length > 0 ? uploadedFiles.map(file => ({
            fileName: file.fileName,
            fileType: file.fileType,
            fileSize: file.fileSize,
            pageCount: file.pageCount,
            content: file.content
          })) : null;
          
          console.log("📤 ChatInput에서 전달:", { messageText, fileInfo });
          // 사용자 텍스트만 전달 (파일 내용은 fileInfo로 분리)
          onSendMessage(messageText, fileInfo);
        }

        // ChatPage에서만 WebSocket으로 메시지 전송
        if (!onStartChat && isConnected) {
          setIsLoading(true);
          try {
            // 파일 내용을 포함한 전체 메시지 생성
            let fullMessage = messageText;
            if (uploadedFiles.length > 0) {
              const fileContents = uploadedFiles.map(file => 
                `[파일: ${file.fileName}]\n${file.content}`
              ).join('\n\n');
              
              if (messageText?.trim()) {
                fullMessage = `${messageText}\n\n${fileContents}`;
              } else {
                fullMessage = fileContents;
              }
            }
            
            // currentBuddyService에서 engineType을 가져오거나 기본값 사용
            const actualEngineType = currentBuddyService?.engineType || engineType;
            console.log(`${actualEngineType} 엔진으로 메시지 전송:`, fullMessage, '| 버디:', currentBuddyService);
            await sendChatMessage(fullMessage, actualEngineType, [], null, null, selectedModel, webSearchEnabled, currentBuddyService);

            // WebSocket 응답은 별도의 리스너에서 처리
            // onTitlesGenerated는 WebSocket 메시지 핸들러에서 호출됨
          } catch (error) {
            console.error("메시지 전송 실패:", error);
            // 에러 메시지 표시
            if (onTitlesGenerated) {
              onTitlesGenerated({
                error: true,
                message: "메시지 전송에 실패했습니다. 연결을 확인해주세요.",
              });
            }
          } finally {
            setIsLoading(false);
          }
        } else if (!onStartChat && !isConnected) {
          // 재연결 시도
          const currentBuddyType = localStorage.getItem('currentBuddyType');
          console.warn("WebSocket이 연결되지 않았습니다. 재연결 시도 중... 버디:", currentBuddyType || "기본");
          try {
            await connectWebSocket(currentBuddyType);
            setIsConnected(true);
            // 재연결 후 다시 시도
            handleSubmit(e);
          } catch (error) {
            console.error("WebSocket 재연결 실패:", error);
            if (onTitlesGenerated) {
              onTitlesGenerated({
                error: true,
                message:
                  "서버와 연결할 수 없습니다. 잠시 후 다시 시도해주세요.",
              });
            }
          }
        }

        setMessage("");
        setUploadedFiles([]);
        if (textareaRef.current) {
          textareaRef.current.style.height = "auto";
        }
        
        // 처리 완료 후 플래그 리셋
        isProcessingRef.current = false;
      }
    };

    const handleKeyDown = (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSubmit(e);
      }
    };

    const handleInputChange = (e) => {
      const value = e.target.value;
      setMessage(value);
      // 텍스트가 있거나 파일이 업로드되면 타이핑 상태로
      setIsTyping(value.length > 0 || uploadedFiles.length > 0);

      // Auto-resize textarea up to max height
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
        const scrollHeight = textareaRef.current.scrollHeight;
        // 최대 200px까지만 늘어나고 그 이후는 스크롤 (기존 400px에서 200px로 축소)
        textareaRef.current.style.height = `${Math.min(scrollHeight, 200)}px`;
      }
    };

    useEffect(() => {
      if (textareaRef.current) {
        textareaRef.current.focus();
      }
    }, []);

    // 파일 업로드 상태 변경 시 전송 버튼 활성화
    useEffect(() => {
      if (uploadedFiles.length > 0) {
        setIsTyping(true);
      } else if (!message.trim()) {
        setIsTyping(false);
      }
    }, [uploadedFiles.length, message]);

    return (
      <fieldset
        className="flex w-full min-w-0 flex-col relative"
        style={{ overflow: "visible" }}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
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



        <div
          className="!box-content flex flex-col bg-bg-000 mx-0 items-stretch transition-all duration-200 relative cursor-text z-10 rounded-2xl border-0.5 border-transparent hover:border-border-300/25"
          style={{
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
          onFocus={(e) => {
            e.currentTarget.style.boxShadow =
              "0 0.25rem 1.25rem hsl(var(--always-black)/7.5%)";
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
                        onClick={() => removeFile(file.id)}
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
          
          <div className="flex flex-col gap-3.5 m-3.5">
            {/* Input Area */}
            <div className="relative">
              <div className="w-full font-large break-words transition-opacity duration-200 min-h-[2rem]">
                <textarea
                  ref={textareaRef}
                  value={message}
                  onChange={handleInputChange}
                  onKeyDown={handleKeyDown}
                  placeholder={
                    isConnected
                      ? engineType === "11"
                        ? '아이디어를 입력하세요. 막연해도 괜찮습니다.\n단어 하나, 메모, 보도자료, "오늘 뭐 쓰지?"... 모두 OK'
                        : '일보와 취재 내용을 입력하세요. 부족해도 괜찮습니다.\n일보만, 팩트 추가, 보도자료, "첫 문장이 안 써져"... 모두 OK'
                      : "서버 연결 중..."
                  }
                  className="w-full min-h-[2rem] max-h-[400px] overflow-y-auto resize-none bg-transparent border-none outline-none text-text-100 placeholder-text-500 font-large leading-relaxed scrollbar-thin scrollbar-thumb-gray-400 scrollbar-track-transparent"
                  rows={1}
                  disabled={!isConnected}
                  style={{
                    fieldSizing: "content",
                  }}
                />
              </div>
            </div>

            {/* Controls */}
            <div className="flex gap-2.5 w-full items-center">
              <div className="relative flex-1 flex items-center gap-2 shrink min-w-0">
                {/* File Upload Button */}
                <div className="relative shrink-0">
                  <FileUploadButton
                    ref={fileUploadRef}
                    onFileContent={handleFileContent}
                    disabled={!isConnected || isLoading}
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

              {/* Claude Model Selector - regression 동일 */}
              <div className="relative shrink-0 model-dropdown">
                  <button
                    onClick={() => setIsModelDropdownOpen(!isModelDropdownOpen)}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = 'hsl(var(--border-200))';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = 'hsl(var(--border-300)/25%)';
                    }}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '0.25rem',
                      padding: '0.375rem 0.5rem',
                      fontSize: '0.75rem',
                      fontWeight: '500',
                      borderRadius: '0.375rem',
                      border: '1px solid',
                      transition: 'all 0.2s',
                      backgroundColor: "hsl(var(--bg-100))",
                      borderColor: "hsl(var(--border-300)/25%)",
                      color: "hsl(var(--text-300))",
                      cursor: 'pointer',
                    }}
                  >
                    <span style={{ maxWidth: '5rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {selectedModel === 'claude-opus-4-6' ? 'Opus 4.6' :
                       selectedModel === 'claude-opus-4-5-20251101' ? 'Opus 4.5' : 'Opus 4.6'}
                    </span>
                    <svg
                      style={{
                        width: '0.75rem',
                        height: '0.75rem',
                        transition: 'transform 0.2s',
                        transform: isModelDropdownOpen ? 'rotate(180deg)' : 'rotate(0deg)',
                      }}
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

                  {/* Dropdown Menu - regression 동일 */}
                  {isModelDropdownOpen && (
                    <div
                      style={{
                        position: 'absolute',
                        top: '100%',
                        marginTop: '0.5rem',
                        left: '0',
                        minWidth: '227px',
                        backgroundColor: 'hsl(var(--bg-000))',
                        border: '1px solid hsl(var(--border-300)/25%)',
                        borderRadius: '0.5rem',
                        boxShadow: '0 4px 12px hsl(var(--always-black)/10%)',
                        zIndex: 9999,
                      }}
                    >
                      <div style={{ padding: '0.25rem' }}>
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
                            <div style={{ display: 'flex', flexDirection: 'column' }}>
                              <span style={{ fontSize: '0.875rem', fontWeight: '500' }}>{model.name}</span>
                              <span style={{ fontSize: '0.75rem', opacity: '0.7' }}>{model.desc}</span>
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

              {/* Connection Status Indicator */}
              <div className="flex items-center gap-1">
                <div
                  className={clsx(
                    "w-2 h-2 rounded-full",
                    isConnected ? "bg-green-500" : "bg-red-500 animate-pulse"
                  )}
                />
              </div>

              {/* Send Button */}
              <div className="opacity-100">
                <button
                  className="inline-flex items-center justify-center relative shrink-0 select-none transition-colors h-8 w-8 rounded-md active:scale-95 !rounded-lg !h-8 !w-8"
                  style={{
                    background: isLoading
                      ? "#ff6b35"
                      : (isTyping || uploadedFiles.length > 0) && isConnected
                      ? "#ff6b35"
                      : "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",
                    color: "white",
                    opacity: (!isTyping && uploadedFiles.length === 0) || isLoading || !isConnected ? "0.5" : "1",
                    cursor: (!isTyping && uploadedFiles.length === 0) || isLoading || !isConnected ? "not-allowed" : "pointer"
                  }}
                  onMouseEnter={(e) => {
                    if ((isTyping || uploadedFiles.length > 0) && isConnected && !isLoading) {
                      e.target.style.background = "#e55a2b";
                    }
                  }}
                  onMouseLeave={(e) => {
                    if ((isTyping || uploadedFiles.length > 0) && isConnected && !isLoading) {
                      e.target.style.background = "#ff6b35";
                    }
                  }}
                  disabled={(!isTyping && uploadedFiles.length === 0) || isLoading || !isConnected}
                  type="button"
                  onClick={handleSubmit}
                  aria-label="메시지 보내기"
                >
                  {isLoading ? (
                    <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                  ) : (
                    <ArrowUp size={16} />
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
        
        {/* 버디 버튼들 */}
        <div className="mt-4 flex justify-center">
          <div className="flex flex-wrap gap-2 justify-center">
            {/* 기본 표시 버튼들 */}
            {[
              { label: '일보버디', info: '막연한 아이디어 → 데스크 OK 일보\n\n시작하는 방법: 입력창에 주제나 키워드를 입력하고 전송 버튼을 클릭하세요\n\n엔진 특성: 일본어 전문, 7가지 언론사 스타일' },
              { label: '제목생성_5종', info: '기사 제목 5가지 유형 생성\n\n시작하는 방법: 기사 본문을 입력하고 전송 버튼을 클릭하세요\n\n엔진 특성: 저널리즘/균형/클릭/SEO/소셜 5종' },
              { label: '교열_경제분야', info: '경제 분야 전문 교열\n\n시작하는 방법: 교열할 경제 기사를 입력하고 전송 버튼을 클릭하세요\n\n엔진 특성: 경제 용어, 수치 표기, 전문 용어 검증' },
              { label: '보도자료_기업', info: '기업 보도자료 → 경제 기사\n\n시작하는 방법: 기업 보도자료를 입력하고 전송 버튼을 클릭하세요\n\n엔진 특성: 보도자료 기반 충실성, 적응형 제안' },
              { label: '외신_영어', info: '영어 기사 → 서울경제 스타일 번역\n\n시작하는 방법: 영어 기사 URL 또는 원문을 입력하고 전송 버튼을 클릭하세요\n\n엔진 특성: 외신 출처 자동 표기, Quick/Standard/Thorough 모드' },
              { label: '퇴고_단문', info: '단문 기사 퇴고 및 개선\n\n시작하는 방법: 퇴고할 단문 기사를 입력하고 전송 버튼을 클릭하세요\n\n엔진 특성: 600자 이하 최적화' },
            ].map(({ label, info }) => {
              const buddyConfig = getBuddyConfig(label);
              return (
              <button
                key={label}
                onClick={async () => {
                  setSelectedBuddyInfo(selectedBuddyInfo?.label === label ? null : { label, info });
                  if (buddyConfig) {
                    setCurrentBuddyService(buddyConfig);
                    localStorage.setItem('currentBuddyType', label);
                    console.log('🎯 버디 선택:', label, buddyConfig);
                    // 서비스가 변경되면 WebSocket 재연결
                    try {
                      await reconnectForBuddy(label);
                      setIsConnected(true);
                    } catch (error) {
                      console.error('WebSocket 재연결 실패:', error);
                      setIsConnected(false);
                    }
                  }
                }}
                className="px-2.5 py-1 text-sm font-medium transition-all duration-200 whitespace-nowrap"
                style={{
                  fontFamily: '"Tiempos Text", "Source Serif 4", "Noto Serif KR", serif',
                  color: '#000000',
                  backgroundColor: selectedBuddyInfo?.label === label ? 'hsl(var(--bg-200))' : 'transparent',
                  border: '1px solid hsl(var(--border-300)/25%)',
                  borderRadius: '24px',
                  boxShadow: selectedBuddyInfo?.label === label ? '0 2px 8px rgba(0,0,0,0.08)' : '0 2px 8px rgba(0,0,0,0.05)',
                  transform: 'translateY(0)',
                }}
                onMouseEnter={(e) => {
                  if (selectedBuddyInfo?.label !== label) {
                    e.currentTarget.style.backgroundColor = 'hsl(var(--bg-200))';
                    e.currentTarget.style.borderColor = 'hsl(var(--border-300)/50%)';
                  }
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
                }}
                onMouseLeave={(e) => {
                  if (selectedBuddyInfo?.label !== label) {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.borderColor = 'hsl(var(--border-300)/25%)';
                  }
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = selectedBuddyInfo?.label === label ? '0 2px 8px rgba(0,0,0,0.08)' : '0 2px 8px rgba(0,0,0,0.05)';
                }}
              >
                {label}
              </button>
            );
            })}
            
            {/* 펼치기/접기 버튼 */}
            <button
              onClick={() => setShowAllTools(!showAllTools)}
              className="w-8 h-8 text-base font-medium transition-all duration-200 flex items-center justify-center"
              style={{
                color: '#000000',
                backgroundColor: showAllTools ? 'hsl(var(--bg-200))' : 'transparent',
                border: '1px solid hsl(var(--border-300)/25%)',
                borderRadius: '50%',
                boxShadow: showAllTools ? '0 2px 8px rgba(0,0,0,0.08)' : '0 2px 8px rgba(0,0,0,0.05)',
                transform: 'translateY(0)',
              }}
              onMouseEnter={(e) => {
                if (!showAllTools) {
                  e.currentTarget.style.backgroundColor = 'hsl(var(--bg-200))';
                  e.currentTarget.style.borderColor = 'hsl(var(--border-300)/50%)';
                }
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
              }}
              onMouseLeave={(e) => {
                if (!showAllTools) {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.borderColor = 'hsl(var(--border-300)/25%)';
                }
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = showAllTools ? '0 2px 8px rgba(0,0,0,0.08)' : '0 2px 8px rgba(0,0,0,0.05)';
              }}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                style={{
                  transform: showAllTools ? 'rotate(180deg)' : 'rotate(0deg)',
                  transition: 'transform 0.2s'
                }}
              >
                <polyline points="6 9 12 15 18 9"></polyline>
              </svg>
            </button>
            
            {/* 추가 도구들 (더보기 버튼 클릭 시 표시) */}
            {showAllTools && [
              { label: '기사버디', info: '보도자료 → 서울경제 스타일 기사\n\n시작하는 방법: 보도자료를 붙여넣고 전송 버튼을 클릭하세요\n\n엔진 특성: 기업/경제부 디지털 기자 전문성' },
              { label: '퇴고_장문', info: '장문 기사 퇴고 및 개선\n\n시작하는 방법: 퇴고할 장문 기사를 입력하고 전송 버튼을 클릭하세요\n\n엔진 특성: 1000자 이상 심층 분석' },
              { label: '제목창의_7종', info: '창의적 제목 7가지 생성\n\n시작하는 방법: 기사 본문을 입력하고 전송 버튼을 클릭하세요\n\n엔진 특성: 추천 2개 + 5가지 유형' },
              { label: '교열_사회분야', info: '사회 분야 전문 교열\n\n시작하는 방법: 교열할 사회 기사를 입력하고 전송 버튼을 클릭하세요\n\n엔진 특성: 사회 이슈, 인명 표기, 법률 용어 검증' },
              { label: '보도자료_공공', info: '정부/공공 보도자료 → 경제 기사\n\n시작하는 방법: 정부 보도자료를 입력하고 전송 버튼을 클릭하세요\n\n엔진 특성: 정치적 중립성, 경제적 관점 우선' },
              { label: '외신_일어', info: '일본어 기사 → 서울경제 스타일 번역\n\n시작하는 방법: 일본어 기사 URL 또는 원문을 입력하고 전송 버튼을 클릭하세요\n\n엔진 특성: 일본 외신 출처 자동 표기, 12개 주요 매체 매핑' }
            ].map(({ label, info }) => {
              const buddyConfig = getBuddyConfig(label);
              return (
              <button
                key={label}
                onClick={async () => {
                  setSelectedBuddyInfo(selectedBuddyInfo?.label === label ? null : { label, info });
                  if (buddyConfig) {
                    setCurrentBuddyService(buddyConfig);
                    localStorage.setItem('currentBuddyType', label);
                    console.log('🎯 버디 선택:', label, buddyConfig);
                    // 서비스가 변경되면 WebSocket 재연결
                    try {
                      await reconnectForBuddy(label);
                      setIsConnected(true);
                    } catch (error) {
                      console.error('WebSocket 재연결 실패:', error);
                      setIsConnected(false);
                    }
                  }
                }}
                className="px-2.5 py-1 text-sm font-medium transition-all duration-200 whitespace-nowrap"
                style={{
                  fontFamily: '"Tiempos Text", "Source Serif 4", "Noto Serif KR", serif',
                  color: '#000000',
                  backgroundColor: selectedBuddyInfo?.label === label ? 'hsl(var(--bg-200))' : 'transparent',
                  border: '1px solid hsl(var(--border-300)/25%)',
                  borderRadius: '24px',
                  boxShadow: selectedBuddyInfo?.label === label ? '0 2px 8px rgba(0,0,0,0.08)' : '0 2px 8px rgba(0,0,0,0.05)',
                  transform: 'translateY(0)',
                }}
                onMouseEnter={(e) => {
                  if (selectedBuddyInfo?.label !== label) {
                    e.currentTarget.style.backgroundColor = 'hsl(var(--bg-200))';
                    e.currentTarget.style.borderColor = 'hsl(var(--border-300)/50%)';
                  }
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
                }}
                onMouseLeave={(e) => {
                  if (selectedBuddyInfo?.label !== label) {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.borderColor = 'hsl(var(--border-300)/25%)';
                  }
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = selectedBuddyInfo?.label === label ? '0 2px 8px rgba(0,0,0,0.08)' : '0 2px 8px rgba(0,0,0,0.05)';
                }}
              >
                {label}
              </button>
            );
            })}
          </div>
        </div>

        {/* 버디 정보 표시 영역 */}
        {selectedBuddyInfo && (
          <div className="w-full max-w-4xl pt-6">
            <div className="mb-4">
              <h2 className="text-xl font-semibold text-text-100 mb-2">
                {selectedBuddyInfo.label}
              </h2>
              <p className="text-sm text-text-300">
                {selectedBuddyInfo.info.split('\n\n')[0]}
              </p>
            </div>

            <div className="space-y-4">
              <div
                className="flex items-start p-3 rounded-lg"
                style={{ backgroundColor: "hsl(var(--bg-200))" }}
              >
                <div className="mr-3 mt-1">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth="1.5"
                    stroke="currentColor"
                    className="h-5 w-5 text-blue-500"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z"
                    />
                  </svg>
                </div>
                <div>
                  <p className="text-sm text-text-200">
                    <span className="font-medium">시작하는 방법:</span> {selectedBuddyInfo.info.split('\n\n')[1].replace('시작하는 방법: ', '')}
                  </p>
                </div>
              </div>

              <div
                className="flex items-start p-3 rounded-lg"
                style={{ backgroundColor: "hsl(var(--bg-200))" }}
              >
                <div className="mr-3 mt-1">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth="1.5"
                    stroke="currentColor"
                    className="h-5 w-5 text-green-500"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M8.25 3v1.5M4.5 8.25H3m18 0h-1.5M4.5 12H3m18 0h-1.5m-15 3.75H3m18 0h-1.5M8.25 19.5V21M12 3v1.5m0 15V21m3.75-18v1.5m0 15V21m-9-1.5h10.5a2.25 2.25 0 0 0 2.25-2.25V6.75a2.25 2.25 0 0 0-2.25-2.25H6.75A2.25 2.25 0 0 0 4.5 6.75v10.5a2.25 2.25 0 0 0 2.25 2.25Zm.75-12h9v9h-9v-9Z"
                    />
                  </svg>
                </div>
                <div>
                  <p className="text-sm text-text-200">
                    <span className="font-medium">엔진 특성:</span> {selectedBuddyInfo.info.split('\n\n')[2].replace('엔진 특성: ', '')}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </fieldset>
    );
  }
);

ChatInput.displayName = "ChatInput";

export default ChatInput;
