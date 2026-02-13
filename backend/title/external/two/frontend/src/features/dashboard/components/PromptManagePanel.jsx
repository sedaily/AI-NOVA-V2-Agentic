import React, { useState, useRef, useEffect } from "react";
import {
  Plus,
  Search,
  Upload,
  FileText,
  Paperclip,
  Type,
  ChevronDown,
} from "lucide-react";
import clsx from "clsx";
import * as promptService from '../../../shared/utils/promptService';

const PromptManagePanel = ({ engineType = "T5" }) => {
  const [instructions, setInstructions] = useState("");
  const [files, setFiles] = useState([]);
  const [showInstructionsModal, setShowInstructionsModal] = useState(false);
  const [showFileDropdown, setShowFileDropdown] = useState(false);
  const [showTextModal, setShowTextModal] = useState(false);
  const [textContent, setTextContent] = useState("");
  const [textTitle, setTextTitle] = useState("");
  const [showFilePreview, setShowFilePreview] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const fileDropdownRef = useRef(null);

  // 엔진 타입 변경 시 데이터 로드
  useEffect(() => {
    loadPromptData();
  }, [engineType]);

  const loadPromptData = async () => {
    setLoading(true);
    try {
      const data = await promptService.getPrompt(engineType);
      if (data.prompt) {
        setInstructions(data.prompt.instruction || "");
      }
      if (data.files) {
        setFiles(data.files);
      }
    } catch (error) {
      console.error("Failed to load prompt data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event) => {
    const uploadedFiles = Array.from(event.target.files);
    setShowFileDropdown(false);

    for (const file of uploadedFiles) {
      try {
        const reader = new FileReader();
        reader.onload = async (e) => {
          const content = e.target.result;
          const newFile = await promptService.addFile(engineType, {
            fileName: file.name,
            fileContent: content,
          });
          setFiles((prev) => [...prev, newFile]);
        };
        reader.readAsText(file);
      } catch (error) {
        console.error("Failed to upload file:", error);
      }
    }
  };

  const handleFileDropdownClick = () => {
    setShowFileDropdown(!showFileDropdown);
  };

  const handleDeviceUpload = () => {
    document.getElementById("project-doc-upload").click();
    setShowFileDropdown(false);
  };

  const handleTextAdd = () => {
    setShowTextModal(true);
    setShowFileDropdown(false);
  };

  const handleDeleteFile = async (fileId) => {
    try {
      await promptService.deleteFile(engineType, fileId);
      setFiles((prev) => prev.filter((f) => f.fileId !== fileId));
    } catch (error) {
      console.error("Failed to delete file:", error);
    }
  };

  const handleSaveInstructions = async () => {
    setSaving(true);
    try {
      await promptService.updatePrompt(engineType, {
        instruction: instructions,
      });
      setShowInstructionsModal(false);
    } catch (error) {
      console.error("Failed to save instructions:", error);
    } finally {
      setSaving(false);
    }
  };

  // 외부 클릭 시 파일 드롭다운 닫기
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        fileDropdownRef.current &&
        !fileDropdownRef.current.contains(event.target)
      ) {
        setShowFileDropdown(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  return (
    <div className="w-full xl:w-96 2xl:w-[28rem] flex-shrink-0 mt-6 xl:mt-0">
      <div className="relative">
        <div className="claude-border transition-all duration-300 ease-out flex flex-col">
          {/* Instructions Section */}
          <div
            className="w-full px-[1.375rem] py-4 border-b-[0.5px] flex flex-row items-center justify-between gap-4 mt-1"
            style={{ borderColor: "hsl(var(--border-300)/0.15)" }}
          >
            <div className="w-full flex flex-col gap-1">
              <div className="w-full flex flex-row items-center justify-between gap-4">
                <h3 className="text-text-300 font-base-bold">지침</h3>
                <div className="flex flex-row items-center gap-2">
                  <button
                    className="claude-button -mr-2"
                    type="button"
                    onClick={() => setShowInstructionsModal(true)}
                  >
                    <div
                      className="flex items-center justify-center"
                      style={{ width: "16px", height: "16px" }}
                    >
                      <svg
                        width="20"
                        height="20"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                      >
                        <path d="M10 3C10.2761 3 10.5 3.22386 10.5 3.5V9.5H16.5L16.6006 9.50977C16.8286 9.55629 17 9.75829 17 10C17 10.2417 16.8286 10.4437 16.6006 10.4902L16.5 10.5H10.5V16.5C10.5 16.7761 10.2761 17 10 17C9.72386 17 9.5 16.7761 9.5 16.5V10.5H3.5C3.22386 10.5 3 10.2761 3 10C3 9.72386 3.22386 9.5 3.5 9.5H9.5V3.5C9.5 3.22386 9.72386 3 10 3Z"></path>
                      </svg>
                    </div>
                  </button>
                </div>
              </div>
              <p className="text-text-500 font-small line-clamp-2">
                <span className="opacity-60">
                  {loading
                    ? "로딩 중..."
                    : instructions || `Claude의 응답을 맞춤화하는 지침 추가`}
                </span>
              </p>
            </div>
          </div>

          {/* Files Section */}
          <div className="w-full px-[1.375rem] py-4 !border-none flex flex-col gap-2 mb-1">
            <div className="w-full flex flex-row items-center justify-between gap-4">
              <h3 className="text-text-300 font-base-bold">파일</h3>
              <div className="flex flex-row items-center gap-2">
                <input
                  data-testid="project-doc-upload"
                  className="hidden"
                  accept=".pdf,.docx,.rtf,.epub,.odt,.odp,.txt,.py,.ipynb,.js,.jsx,.html,.css,.java,.cs,.php,.c,.cc,.cpp,.cxx,.cts,.h,.hh,.hpp,.rs,.R,.Rmd,.swift,.go,.rb,.kt,.kts,.ts,.tsx,.m,.mm,.mts,.scala,.dart,.lua,.pl,.pm,.t,.sh,.bash,.zsh,.csv,.log,.ini,.cfg,.config,.json,.proto,.yaml,.yml,.toml,.sql,.bat,.md,.coffee,.tex,.latex,.gd,.gdshader,.tres,.tscn,.jpg,.jpeg,.png,.gif,.webp,.csv,.xls,.xlsx,.xlsb,.xlm,.xlsm,.xlt,.xltm,.xltx,.ods"
                  multiple
                  type="file"
                  onChange={handleFileUpload}
                  id="project-doc-upload"
                />
                <div className="relative" ref={fileDropdownRef}>
                  <button
                    className="claude-button -mr-2"
                    type="button"
                    aria-haspopup="menu"
                    aria-expanded={showFileDropdown}
                    data-testid="project-doc-uploader-dropdown-trigger"
                    onClick={handleFileDropdownClick}
                  >
                    <div
                      className="flex items-center justify-center"
                      style={{ width: "16px", height: "16px" }}
                    >
                      <Plus size={20} />
                    </div>
                  </button>

                  {/* File Upload Dropdown */}
                  {showFileDropdown && (
                    <div
                      className="absolute right-0 top-full mt-2 z-50 min-w-[12rem] overflow-hidden p-1.5 text-text-300 rounded-xl border-0.5"
                      style={{
                        backgroundColor: "hsl(var(--bg-000))",
                        borderColor: "hsl(var(--border-300)/0.15)",
                        backdropFilter: "blur(12px)",
                        boxShadow: "0 0 0 1px hsl(var(--always-black)/4%)",
                        maxHeight:
                          "min(var(--radix-dropdown-menu-content-available-height), var(--dropdown-max-height))",
                        overflowY: "auto",
                      }}
                      role="menu"
                      aria-orientation="vertical"
                    >
                      <div
                        role="menuitem"
                        className="font-base py-1.5 px-2 rounded-lg cursor-pointer whitespace-nowrap overflow-hidden text-ellipsis grid grid-cols-[minmax(0,_1fr)_auto] gap-2 items-center outline-none select-none hover:bg-bg-200 hover:text-text-000 text-left"
                        onClick={handleDeviceUpload}
                        tabIndex="0"
                      >
                        <div className="flex items-center gap-2.5 w-full py-0.5 text-sm group">
                          <div
                            className="flex items-center justify-center"
                            style={{ width: "20px", height: "20px" }}
                          >
                            <Paperclip size={20} />
                          </div>
                          <span>기기에서 업로드</span>
                        </div>
                      </div>

                      <div
                        role="menuitem"
                        className="font-base py-1.5 px-2 rounded-lg cursor-pointer whitespace-nowrap overflow-hidden text-ellipsis grid grid-cols-[minmax(0,_1fr)_auto] gap-2 items-center outline-none select-none hover:bg-bg-200 hover:text-text-000 text-left"
                        onClick={handleTextAdd}
                        tabIndex="-1"
                      >
                        <div className="flex items-center gap-2.5 w-full py-0.5 text-sm group">
                          <div
                            className="flex items-center justify-center"
                            style={{ width: "20px", height: "20px" }}
                          >
                            <Type size={20} />
                          </div>
                          <span>텍스트 내용 추가</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* File Upload Area */}
            {loading ? (
              <div className="text-center h-[10rem] bg-bg-200 rounded-2xl flex items-center justify-center">
                <span className="text-text-500">로딩 중...</span>
              </div>
            ) : files.length === 0 ? (
              <div className="text-center h-[10rem] bg-bg-200 rounded-2xl flex flex-col gap-3 items-center justify-center text-text-500 font-small">
                <img
                  alt=""
                  loading="lazy"
                  width="105"
                  height="56"
                  decoding="async"
                  className="dark:hidden"
                  src="/images/illustrations/project-knowledge-light-mode.svg"
                  style={{ color: "transparent" }}
                />
                <img
                  alt=""
                  loading="lazy"
                  width="105"
                  height="56"
                  decoding="async"
                  className="hidden dark:block"
                  src="/images/illustrations/project-knowledge-dark-mode.svg"
                  style={{ color: "transparent" }}
                />
                <div className="max-w-[14.5rem]">
                  이 프로젝트에서 참조할 PDF, 문서 또는 기타 텍스트를
                  추가하세요.
                </div>
              </div>
            ) : (
              <ul className="grid grid-cols-[repeat(auto-fill,minmax(120px,1fr))] gap-3 mt-2">
                {files.map((file) => (
                  <FileCard
                    key={file.fileId}
                    file={file}
                    onRemove={() => handleDeleteFile(file.fileId)}
                    onClick={() => {
                      setSelectedFile(file);
                      setShowFilePreview(true);
                    }}
                  />
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>

      {/* Instructions Modal */}
      {showInstructionsModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50"
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              setShowInstructionsModal(false);
            }
          }}
        >
          <div
            role="dialog"
            className="flex flex-col focus:outline-none relative text-text-100 text-left shadow-xl border-0.5 rounded-2xl md:p-6 p-4 align-middle min-w-0 w-full max-w-3xl max-h-[85vh] animate-[zoom_250ms_ease-in_forwards]"
            style={{
              backgroundColor: "hsl(var(--bg-100))",
              borderColor: "hsl(var(--border-300)/0.15)",
              pointerEvents: "auto",
            }}
            tabIndex="-1"
          >
            <div className="flex flex-col h-full overflow-y-auto max-h-[calc(85vh-6rem)]">
              <div className="flex flex-col gap-1">
                <h2 className="font-xl-bold">{engineType} 엔진 지침 설정</h2>
                <p className="text-text-300 text-sm">
                  {engineType} 엔진이 제목을 생성할 때 사용할 지침을 입력하세요.
                </p>
              </div>

              <div className="mb-6 mt-3">
                <div className="group relative">
                  <div className="grid">
                    <textarea
                      className="p-3 leading-5 rounded-[0.6rem] transition-colors placeholder:text-text-500 can-focus disabled:cursor-not-allowed disabled:opacity-50 whitespace-pre-wrap resize-none row-start-1 row-end-2 col-start-1 col-end-2 max-h-80 overflow-x-visible overflow-y-auto scroll-pb-6 min-h-[0px] instructions-textarea"
                      style={{
                        backgroundColor: "hsl(var(--bg-000))",
                        border: "0.5px solid hsl(var(--border-300)/0.15)",
                        color: "hsl(var(--text-100))",
                      }}
                      rows="16"
                      value={instructions}
                      onChange={(e) => setInstructions(e.target.value)}
                      placeholder={`${engineType} 엔진의 제목 생성 지침을 입력하세요.`}
                    />
                  </div>
                </div>
              </div>

              <div className="mt-2 flex justify-end gap-2">
                <button
                  className="inline-flex items-center justify-center relative shrink-0 can-focus select-none disabled:pointer-events-none disabled:opacity-50 disabled:shadow-none disabled:drop-shadow-none text-text-000 font-base-bold border-0.5 border-border-200 relative overflow-hidden transition duration-100 hover:border-border-300/0 bg-bg-300/0 hover:bg-bg-400 backface-hidden h-9 px-4 py-2 rounded-lg min-w-[5rem] active:scale-[0.985] whitespace-nowrap"
                  type="button"
                  onClick={() => setShowInstructionsModal(false)}
                >
                  취소
                </button>
                <button
                  className="inline-flex items-center justify-center relative shrink-0 can-focus select-none disabled:pointer-events-none disabled:opacity-50 disabled:shadow-none disabled:drop-shadow-none bg-text-000 text-bg-000 font-base-bold relative overflow-hidden transition-transform will-change-transform ease-[cubic-bezier(0.165,0.85,0.45,1)] duration-150 hover:scale-y-[1.015] hover:scale-x-[1.005] backface-hidden after:absolute after:inset-0 after:bg-[radial-gradient(at_bottom,hsla(var(--bg-000)/20%),hsla(var(--bg-000)/0%))] after:opacity-0 after:transition after:duration-200 after:translate-y-2 hover:after:opacity-100 hover:after:translate-y-0 h-9 px-4 py-2 rounded-lg min-w-[5rem] active:scale-[0.985] whitespace-nowrap"
                  type="button"
                  onClick={handleSaveInstructions}
                  disabled={!instructions.trim() || saving}
                >
                  {saving ? "저장 중..." : "지침 저장"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Text Content Modal */}
      {showTextModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50"
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              setShowTextModal(false);
              setTextTitle("");
              setTextContent("");
            }
          }}
        >
          <div
            role="dialog"
            className="flex flex-col focus:outline-none relative text-text-100 text-left shadow-xl border-0.5 rounded-2xl align-middle min-w-0 p-7 pt-6 w-full max-w-3xl max-h-[85vh] animate-[zoom_250ms_ease-in_forwards]"
            style={{
              backgroundColor: "hsl(var(--bg-100))",
              borderColor: "hsl(var(--border-300)/0.15)",
              pointerEvents: "auto",
            }}
            tabIndex="-1"
          >
            <div className="flex flex-col h-full overflow-y-auto max-h-[calc(85vh-6rem)]">
              <form
                onSubmit={async (e) => {
                  e.preventDefault();
                  console.log("Submitting text file:", {
                    textTitle,
                    textContent,
                    engineType,
                  });
                  try {
                    const newFile = await promptService.addFile(engineType, {
                      fileName: `${textTitle || "제목없음"}.txt`,
                      fileContent: textContent,
                    });
                    console.log("File added successfully:", newFile);
                    setFiles((prev) => {
                      const updated = [...prev, newFile];
                      console.log("Updated files:", updated);
                      return updated;
                    });
                    setShowTextModal(false);
                    setTextTitle("");
                    setTextContent("");
                  } catch (error) {
                    console.error("Failed to add text file:", error);
                    alert("파일 추가 실패: " + error.message);
                  }
                }}
              >
                <h2 className="font-claude-response mb-3 text-xl">
                  텍스트 내용 추가
                </h2>

                <label
                  htmlFor="text-title"
                  className="text-text-200 mb-1 block font-base"
                >
                  제목
                </label>
                <input
                  id="text-title"
                  className="h-11 px-3 rounded-[0.6rem] mb-2 w-full font-large transition-colors placeholder:text-text-500 can-focus disabled:cursor-not-allowed disabled:opacity-50"
                  style={{
                    backgroundColor: "hsl(var(--bg-000))",
                    border: "0.5px solid hsl(var(--border-300)/0.15)",
                    color: "hsl(var(--text-100))",
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.borderColor = "hsl(var(--border-300)/0.3)";
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.borderColor = "hsl(var(--border-300)/0.15)";
                  }}
                  onFocus={(e) => {
                    e.target.style.borderColor = "hsl(var(--accent-main-100))";
                    e.target.style.boxShadow =
                      "0 0 0 2px hsl(var(--accent-main-100)/0.2)";
                  }}
                  onBlur={(e) => {
                    e.target.style.borderColor = "hsl(var(--border-300)/0.15)";
                    e.target.style.boxShadow = "none";
                  }}
                  placeholder="콘텐츠 이름 지정"
                  required
                  value={textTitle}
                  onChange={(e) => setTextTitle(e.target.value)}
                />

                <div className="group relative">
                  <label
                    htmlFor="text-content"
                    className="text-text-200 mb-1 block font-base"
                  >
                    콘텐츠
                  </label>
                  <div className="grid">
                    <div
                      aria-hidden="true"
                      className="p-3 leading-5 rounded-[0.6rem] transition-colors placeholder:text-text-500 can-focus disabled:cursor-not-allowed disabled:opacity-50 whitespace-pre-wrap resize-none row-start-1 row-end-2 col-start-1 col-end-2 max-h-[50vh] overflow-y-auto pointer-events-none invisible"
                      style={{
                        backgroundColor: "hsl(var(--bg-000))",
                        border: "0.5px solid hsl(var(--border-300)/0.15)",
                      }}
                    >
                      {textContent || " "}
                    </div>
                    <textarea
                      id="text-content"
                      className="p-3 leading-5 rounded-[0.6rem] transition-colors placeholder:text-text-500 can-focus disabled:cursor-not-allowed disabled:opacity-50 whitespace-pre-wrap resize-none row-start-1 row-end-2 col-start-1 col-end-2 max-h-[50vh] overflow-y-auto"
                      style={{
                        backgroundColor: "hsl(var(--bg-000))",
                        border: "0.5px solid hsl(var(--border-300)/0.15)",
                        color: "hsl(var(--text-100))",
                      }}
                      onMouseEnter={(e) => {
                        e.target.style.borderColor =
                          "hsl(var(--border-300)/0.3)";
                      }}
                      onMouseLeave={(e) => {
                        e.target.style.borderColor =
                          "hsl(var(--border-300)/0.15)";
                      }}
                      onFocus={(e) => {
                        e.target.style.borderColor =
                          "hsl(var(--accent-main-100))";
                        e.target.style.boxShadow =
                          "0 0 0 2px hsl(var(--accent-main-100)/0.2)";
                      }}
                      onBlur={(e) => {
                        e.target.style.borderColor =
                          "hsl(var(--border-300)/0.15)";
                        e.target.style.boxShadow = "none";
                      }}
                      rows="12"
                      placeholder="내용을 입력하거나 붙여넣으세요."
                      required
                      value={textContent}
                      onChange={(e) => setTextContent(e.target.value)}
                    />
                  </div>
                </div>

                <div className="mt-4 flex justify-end gap-2">
                  <button
                    className="inline-flex items-center justify-center relative shrink-0 can-focus select-none disabled:pointer-events-none disabled:opacity-50 disabled:shadow-none disabled:drop-shadow-none text-text-000 font-base-bold border-0.5 border-border-200 relative overflow-hidden transition duration-100 hover:border-border-300/0 bg-bg-300/0 hover:bg-bg-400 backface-hidden h-9 px-4 py-2 rounded-lg min-w-[5rem] active:scale-[0.985] whitespace-nowrap"
                    type="button"
                    onClick={() => {
                      setShowTextModal(false);
                      setTextTitle("");
                      setTextContent("");
                    }}
                  >
                    취소
                  </button>
                  <button
                    className="inline-flex items-center justify-center relative shrink-0 can-focus select-none disabled:pointer-events-none disabled:opacity-50 disabled:shadow-none disabled:drop-shadow-none bg-text-000 text-bg-000 font-base-bold relative overflow-hidden transition-transform will-change-transform ease-[cubic-bezier(0.165,0.85,0.45,1)] duration-150 hover:scale-y-[1.015] hover:scale-x-[1.005] backface-hidden after:absolute after:inset-0 after:bg-[radial-gradient(at_bottom,hsla(var(--bg-000)/20%),hsla(var(--bg-000)/0%))] after:opacity-0 after:transition after:duration-200 after:translate-y-2 hover:after:opacity-100 hover:after:translate-y-0 h-9 px-4 py-2 rounded-lg min-w-[5rem] active:scale-[0.985] whitespace-nowrap"
                    type="submit"
                    disabled={!textTitle.trim() || !textContent.trim()}
                  >
                    콘텐츠 추가
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* File Preview Modal */}
      {showFilePreview && selectedFile && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50"
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              setShowFilePreview(false);
            }
          }}
        >
          <div
            role="dialog"
            className="flex flex-col focus:outline-none relative text-text-100 text-left shadow-xl border-0.5 rounded-2xl md:p-6 p-4 align-middle min-w-0 w-full max-w-3xl max-h-[85vh] animate-[zoom_250ms_ease-in_forwards]"
            style={{
              backgroundColor: "hsl(var(--bg-100))",
              borderColor: "hsl(var(--border-300)/0.15)",
              pointerEvents: "auto",
            }}
            tabIndex="-1"
          >
            <div className="flex flex-col h-full overflow-hidden">
              <div className="flex items-center gap-4 justify-between">
                <h2 className="font-xl-bold text-text-100 flex w-full min-w-0 items-center leading-6 break-words">
                  <span className="[overflow-wrap:anywhere]">
                    {(selectedFile.fileName || selectedFile.name || "").replace(
                      ".txt",
                      ""
                    )}
                  </span>
                </h2>
                <div className="flex items-center gap-2">
                  <button
                    className="inline-flex items-center justify-center relative shrink-0 can-focus select-none disabled:pointer-events-none disabled:opacity-50 disabled:shadow-none disabled:drop-shadow-none text-text-300 border-transparent transition font-ui tracking-tight duration-300 ease-[cubic-bezier(0.165,0.85,0.45,1)] hover:bg-bg-300 hover:text-text-100 h-8 w-8 rounded-md active:scale-95 !text-text-500 hover:!text-text-400 -mx-2 !rounded-xl"
                    type="button"
                    onClick={() => setShowFilePreview(false)}
                  >
                    <div
                      className="flex items-center justify-center"
                      style={{ width: "16px", height: "16px" }}
                    >
                      <svg
                        width="20"
                        height="20"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                        xmlns="http://www.w3.org/2000/svg"
                        className="shrink-0"
                        aria-hidden="true"
                      >
                        <path d="M15.1465 4.14642C15.3418 3.95121 15.6583 3.95118 15.8536 4.14642C16.0487 4.34168 16.0488 4.65822 15.8536 4.85346L10.7071 9.99997L15.8536 15.1465C16.0487 15.3417 16.0488 15.6583 15.8536 15.8535C15.6828 16.0244 15.4187 16.0461 15.2247 15.918L15.1465 15.8535L10 10.707L4.85352 15.8535C4.65827 16.0486 4.34168 16.0486 4.14648 15.8535C3.95129 15.6583 3.95142 15.3418 4.14648 15.1465L9.293 9.99997L4.14648 4.85346C3.95142 4.65818 3.95129 4.34162 4.14648 4.14642C4.34168 3.95128 4.65825 3.95138 4.85352 4.14642L10 9.29294L15.1465 4.14642Z"></path>
                      </svg>
                    </div>
                  </button>
                </div>
              </div>

              <p className="text-text-300 mb-2 text-sm">
                <span className="text-text-500 mb-3 mt-0.5 flex flex-wrap gap-y-2 items-start items-center text-xs">
                  <span>
                    <span>
                      {(
                        (selectedFile.size ||
                          (selectedFile.fileContent || "").length) / 1024
                      ).toFixed(2)}{" "}
                      KB&nbsp;
                      <span className="opacity-50 mx-1">•</span>
                      {(
                        selectedFile.fileName ||
                        selectedFile.name ||
                        ""
                      ).endsWith(".txt")
                        ? `${
                            (
                              selectedFile.fileContent ||
                              selectedFile.content ||
                              ""
                            ).split("\n").length
                          }줄`
                        : "파일"}
                    </span>
                  </span>
                  <span className="mx-1.5 opacity-50 hidden lg:inline">•</span>
                  <span>원본과 형식이 일치하지 않을 수 있습니다</span>
                </span>
              </p>

              <div
                className="rounded-lg border-0.5 shadow-sm whitespace-pre-wrap break-all text-xs p-4 font-mono overflow-y-auto flex-1 min-h-0"
                style={{
                  backgroundColor: "hsl(var(--bg-000))",
                  borderColor: "hsl(var(--border-300)/0.15)",
                }}
              >
                {(selectedFile.fileName || selectedFile.name || "").endsWith(
                  ".txt"
                )
                  ? selectedFile.fileContent ||
                    selectedFile.content ||
                    "텍스트 내용을 불러올 수 없습니다."
                  : "이 파일 형식은 미리보기를 지원하지 않습니다."}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const FileUploadIcon = () => (
  <svg
    width="105"
    height="56"
    viewBox="0 0 105 56"
    fill="none"
    className="text-text-400"
  >
    <rect
      x="20"
      y="10"
      width="65"
      height="36"
      rx="4"
      stroke="currentColor"
      strokeWidth="2"
      fill="none"
    />
    <path
      d="M30 20h45M30 28h35M30 36h25"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
    />
    <circle cx="35" cy="45" r="2" fill="currentColor" />
    <circle cx="45" cy="45" r="2" fill="currentColor" />
    <circle cx="55" cy="45" r="2" fill="currentColor" />
  </svg>
);

const FileCard = ({ file, onRemove, onClick }) => {
  const getFileExtension = (filename) => {
    return filename.split(".").pop().toLowerCase();
  };

  const getFileLines = (content) => {
    if (typeof content === "string") {
      return content.split("\n").length;
    }
    return 1;
  };

  const fileName = file.fileName || file.name || "untitled";
  const fileContent = file.fileContent || file.content || "";
  const isTextFile = fileName.endsWith(".txt");
  const displayName = isTextFile ? fileName.replace(".txt", "") : fileName;
  const lines = isTextFile ? getFileLines(fileContent) : 1;
  const fileSize = file.size || (fileContent ? fileContent.length : 0);

  return (
    <div>
      <div className="relative">
        <div className="group/thumbnail" data-testid="file-thumbnail">
          <button
            className="rounded-lg text-left block cursor-pointer font-ui transition-all border-0.5 flex flex-col justify-between gap-2.5 overflow-hidden px-2.5 py-2 shadow-sm"
            onClick={onClick}
            style={{
              width: "100%",
              height: "120px",
              minWidth: "100%",
              borderColor: "hsl(var(--border-300)/0.25)",
              backgroundColor: "hsl(var(--bg-000))",
              boxShadow: "0 1px 2px 0 hsl(var(--always-black)/0.05)",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "hsl(var(--border-200)/0.5)";
              e.currentTarget.style.boxShadow =
                "0 4px 6px -1px hsl(var(--always-black)/0.1)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = "hsl(var(--border-300)/0.25)";
              e.currentTarget.style.boxShadow =
                "0 1px 2px 0 hsl(var(--always-black)/0.05)";
            }}
          >
            <div className="relative flex flex-col gap-1 min-h-0">
              <h3
                className="text-[12px] tracking-tighter break-words text-text-100 line-clamp-3"
                style={{ opacity: 1 }}
              >
                {displayName}
              </h3>
              <p
                className="text-[10px] line-clamp-1 tracking-tighter break-words text-text-500"
                style={{ opacity: 1 }}
              >
                {isTextFile ? `${lines}줄` : `${Math.round(fileSize / 1024)}KB`}
              </p>
            </div>
            <div>
              <div className="relative flex flex-row items-center gap-1 justify-between">
                <div
                  className="flex flex-row gap-1 shrink min-w-0"
                  style={{ opacity: 1 }}
                >
                  <div
                    className="min-w-0 h-[18px] flex flex-row items-center justify-center gap-0.5 px-1 border-0.5 shadow-sm rounded font-medium"
                    style={{
                      borderColor: "hsl(var(--border-300)/0.25)",
                      backgroundColor: "hsl(var(--bg-000)/0.7)",
                      backdropFilter: "blur(4px)",
                    }}
                  >
                    <p className="uppercase truncate font-ui text-text-300 text-[11px] leading-[13px]">
                      {getFileExtension(fileName)}
                    </p>
                  </div>
                </div>
                <div className="flex flex-row gap-1 shrink-0">
                  <div className="flex flex-row gap-1 h-[18px] right-0 top-0 absolute opacity-0">
                    <label className="select-none flex flex-row gap-3 cursor-pointer text-left shrink-0 items-center">
                      <input className="sr-only peer" type="checkbox" />
                      <div
                        className="shrink-0 w-4 h-4 flex items-center justify-center border rounded transition-colors duration-100 ease-in-out cursor-pointer border-0.5 shadow-sm"
                        style={{
                          width: "18px",
                          height: "18px",
                          borderColor: "hsl(var(--border-300)/0.25)",
                          backgroundColor: "hsl(var(--bg-000))",
                        }}
                      ></div>
                      <span className="leading-none sr-only">Select file</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </button>
          <button
            className="transition-all hover:bg-bg-000/50 text-text-500 hover:text-text-200 group-focus-within/thumbnail:opacity-100 group-hover/thumbnail:opacity-100 opacity-0 w-5 h-5 absolute -top-2 -left-2 rounded-full border-0.5 flex items-center justify-center"
            style={{
              borderColor: "hsl(var(--border-300)/0.25)",
              backgroundColor: "hsl(var(--bg-000)/0.9)",
              backdropFilter: "blur(4px)",
            }}
            onClick={onRemove}
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
    </div>
  );
};

export default PromptManagePanel;
