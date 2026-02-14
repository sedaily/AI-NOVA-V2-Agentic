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
} from '../services/websocketService';

// Claude 모델 목록
const CLAUDE_MODELS = [
  { id: "opus-4-20250514", name: "Opus 4.6", desc: "Latest & most capable (default)" },
  { id: "claude-opus-4-5-20251101", name: "Opus 4.5", desc: "Previous flagship model" },
  { id: "claude-sonnet-4-5-20250929", name: "Sonnet 4.5", desc: "Best for everyday tasks" },
];

const ChatInput = forwardRef(
  (
    { onSendMessage, onStartChat, onTitlesGenerated, engineType = "T5", showModelSelector = false, selectedModel, onModelChange },
    ref
  ) => {
    const [message, setMessage] = useState("");
    const [isTyping, setIsTyping] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [isConnected, setIsConnected] = useState(false);
    const [uploadedFiles, setUploadedFiles] = useState([]);
    const [isDragging, setIsDragging] = useState(false);
    const [isModelDropdownOpen, setIsModelDropdownOpen] = useState(false);
    const [webSearchEnabled, setWebSearchEnabled] = useState(() => {
      // localStorage에서 웹검색 상태 복원
      const saved = localStorage.getItem('webSearchEnabled');
      return saved === 'true';
    });
    const textareaRef = useRef(null);
    const fileUploadRef = useRef(null);
    const dragCounterRef = useRef(0);
    const modelDropdownRef = useRef(null);

    // WebSocket 연결 관리
    useEffect(() => {
      const initWebSocket = async () => {
        try {
          if (!isWebSocketConnected()) {
            console.log("WebSocket 연결 시도...");
            await connectWebSocket();
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

    // 웹검색 상태를 localStorage에 저장
    useEffect(() => {
      localStorage.setItem('webSearchEnabled', webSearchEnabled.toString());
    }, [webSearchEnabled]);

    // 모델 드롭다운 외부 클릭 처리
    useEffect(() => {
      const handleClickOutside = (event) => {
        if (modelDropdownRef.current && !modelDropdownRef.current.contains(event.target)) {
          setIsModelDropdownOpen(false);
        }
      };
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
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
      setUploadedFiles((prev) => prev.filter((f) => f.id !== fileId));
    };

    const isProcessingRef = useRef(false); // 중복 제출 방지용
    
    const handleSubmit = async (e) => {
      e.preventDefault();
      
      // 이미 처리 중이면 무시
      if (isProcessingRef.current) {
        console.log("⚠️ 이미 메시지 처리 중, 중복 호출 방지");
        return;
      }
      
      if (message.trim() && !isLoading) {
        const messageText = message.trim();
        
        // 처리 시작 표시
        isProcessingRef.current = true;

        // onStartChat가 있으면 ChatPage로 네비게이션 (MainContent에서 사용)
        // 이 경우 WebSocket 메시지는 ChatPage에서 전송됨
        if (onStartChat) {
          // 파일 내용을 메시지에 포함
          let fullMessage = messageText;
          if (uploadedFiles.length > 0) {
            const fileContents = uploadedFiles.map(file => {
              return `\n\n--- 파일: ${file.fileName} ---\n${file.content}`;
            }).join('\n');
            fullMessage = messageText + fileContents;
            
            // 파일 데이터를 localStorage에 저장 (ChatPage에서 사용)
            localStorage.setItem('pendingFiles', JSON.stringify(uploadedFiles));
          }
          
          console.log("🔀 ChatPage로 네비게이션 - 메시지:", fullMessage, "웹검색:", webSearchEnabled);

          // 웹검색 상태를 localStorage에 저장 (ChatPage에서 사용)
          if (webSearchEnabled) {
            localStorage.setItem('pendingWebSearch', 'true');
          } else {
            localStorage.removeItem('pendingWebSearch');
          }

          // 메시지 초기화를 먼저 하여 중복 호출 방지
          setMessage("");
          setIsTyping(false);
          setUploadedFiles([]);
          setWebSearchEnabled(false); // 웹검색 상태도 초기화
          if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
            textareaRef.current.value = ""; // textarea 값도 직접 초기화
          }
          // 그 다음 페이지 전환 (파일 내용이 포함된 메시지 전달)
          onStartChat(fullMessage);
          
          // 약간의 지연 후 플래그 리셋
          setTimeout(() => {
            isProcessingRef.current = false;
          }, 1000);
          
          return; // 여기서 종료
        }

        // onSendMessage가 있으면 현재 페이지에서 처리 (ChatPage에서 사용)
        if (onSendMessage) {
          onSendMessage(messageText);
        }

        // ChatPage에서만 WebSocket으로 메시지 전송
        if (!onStartChat && isConnected) {
          setIsLoading(true);
          try {
            console.log(`${engineType} 엔진으로 메시지 전송:`, messageText, webSearchEnabled ? "(웹검색 ON)" : "");
            await sendChatMessage(messageText, engineType, webSearchEnabled);

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
          console.warn("WebSocket이 연결되지 않았습니다. 재연결 시도 중...");
          // 재연결 시도
          try {
            await connectWebSocket();
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
      setIsTyping(value.length > 0);

      // Auto-resize textarea up to max height
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
        const scrollHeight = textareaRef.current.scrollHeight;
        // 최대 400px까지만 늘어나고 그 이후는 스크롤
        textareaRef.current.style.height = `${Math.min(scrollHeight, 400)}px`;
      }
    };

    useEffect(() => {
      if (textareaRef.current) {
        textareaRef.current.focus();
      }
    }, []);

    return (
      <fieldset
        className="flex w-full min-w-0 flex-col relative"
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
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

        <div
          className="!box-content flex flex-col bg-bg-000 mx-0 items-stretch transition-all duration-200 relative cursor-text z-10 rounded-2xl border border-border-300/15"
          style={{
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
          onFocus={(e) => {
            e.currentTarget.style.boxShadow =
              "0 0.25rem 1.25rem hsl(var(--always-black)/7.5%)";
          }}
        >
          <div className="flex flex-col gap-3.5 m-3.5">
            {/* Input Area */}
            <div className="relative">
              <div className="w-full font-large break-words transition-opacity duration-200 min-h-[1.5rem]">
                <textarea
                  ref={textareaRef}
                  value={message}
                  onChange={handleInputChange}
                  onKeyDown={handleKeyDown}
                  placeholder={
                    isConnected
                      ? "오늘 어떤 도움을 드릴까요?"
                      : "서버 연결 중..."
                  }
                  className="w-full min-h-[1.5rem] max-h-[400px] overflow-y-auto resize-none bg-transparent border-none outline-none text-text-100 placeholder-text-500 font-large leading-relaxed scrollbar-thin scrollbar-thumb-gray-400 scrollbar-track-transparent"
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
                  disabled={!isConnected || isLoading}
                >
                  <Globe size={16} />
                </button>
                {webSearchEnabled && (
                  <span className="text-xs text-blue-500 font-medium">웹검색 ON</span>
                )}
              </div>

              {/* Claude Model Selector */}
              {showModelSelector && (
                <div className="relative shrink-0 model-dropdown" ref={modelDropdownRef}>
                  <button
                    type="button"
                    onClick={() => setIsModelDropdownOpen(!isModelDropdownOpen)}
                    className="inline-flex items-center justify-center gap-1 px-2 py-1.5 text-xs font-medium rounded-md border transition-colors"
                    style={{
                      backgroundColor: "hsl(var(--bg-100))",
                      borderColor: "hsl(var(--border-300)/25%)",
                      color: "hsl(var(--text-300))",
                    }}
                  >
                    <span className="truncate max-w-20">
                      {CLAUDE_MODELS.find(m => m.id === selectedModel)?.name || "Opus 4.5"}
                    </span>
                    <svg
                      className={`w-3 h-3 transition-transform ${isModelDropdownOpen ? 'rotate-180' : ''}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  {/* Dropdown Menu */}
                  {isModelDropdownOpen && (
                    <div
                      className="absolute bottom-full mb-2 right-0 z-50 rounded-lg border shadow-lg"
                      style={{
                        minWidth: "200px",
                        backgroundColor: "hsl(var(--bg-000))",
                        borderColor: "hsl(var(--border-300)/25%)",
                        boxShadow: "0 4px 12px hsl(var(--always-black)/10%)",
                      }}
                    >
                      <div className="p-1">
                        {CLAUDE_MODELS.map((model) => (
                          <button
                            key={model.id}
                            type="button"
                            onClick={() => {
                              onModelChange?.(model.id);
                              setIsModelDropdownOpen(false);
                            }}
                            className={`w-full text-left px-3 py-2 rounded-md transition-colors ${
                              selectedModel === model.id
                                ? 'bg-accent-main-100/10 text-accent-main-100'
                                : 'hover:bg-bg-100 text-text-100'
                            }`}
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
              )}

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
                  className={clsx(
                    "inline-flex items-center justify-center relative shrink-0 select-none transition-colors h-8 w-8 rounded-md active:scale-95 !rounded-lg !h-8 !w-8",
                    isLoading
                      ? "bg-accent-main-100 text-white cursor-wait"
                      : isTyping && isConnected
                      ? "bg-accent-main-000 text-white hover:bg-accent-main-200"
                      : "bg-gray-600 text-gray-400 cursor-not-allowed"
                  )}
                  disabled={!isTyping || isLoading || !isConnected}
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
        </div>
      </fieldset>
    );
  }
);

ChatInput.displayName = "ChatInput";

export default ChatInput;
