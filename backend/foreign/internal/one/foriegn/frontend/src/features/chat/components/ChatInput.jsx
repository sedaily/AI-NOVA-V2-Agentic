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
            
            console.log(`${engineType} 엔진으로 메시지 전송:`, fullMessage, `웹검색: ${webSearchEnabled}`);
            await sendChatMessage(fullMessage, engineType, [], null, null, selectedModel, webSearchEnabled);

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
                      ? "영문 기사 텍스트를 직접 복사해서 입력해 주세요. 엔터를 누르면 한글 기사 초안을 작성해 드립니다."
                      : "서버 연결 중..."
                  }
                  className="w-full min-h-[2rem] max-h-[400px] overflow-y-auto resize-none bg-transparent border-none outline-none text-text-100 placeholder-text-500 font-large leading-relaxed scrollbar-thin scrollbar-thumb-gray-400 scrollbar-track-transparent"
                  rows={1}
                  disabled={!isConnected}
                  style={{
                    fieldSizing: "content",
                    fontSize: "15px",
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

              {/* Claude Model Selector - 화살표 버튼 왼쪽 */}
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
                      className="absolute top-full mt-2 left-0 z-50 rounded-lg border shadow-lg"
                      style={{
                        minWidth: "227px",
                        backgroundColor: "hsl(var(--bg-000))",
                        borderColor: "hsl(var(--border-300)/25%)",
                        boxShadow: "0 4px 12px hsl(var(--always-black)/10%)",
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
      </fieldset>
    );
  }
);

ChatInput.displayName = "ChatInput";

export default ChatInput;
