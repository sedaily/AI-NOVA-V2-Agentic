import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, Paperclip, X, FileText, Image, File } from "lucide-react";
import PhaseIndicator from "./PhaseIndicator";

const Phase1View = ({ onNext, onPhaseClick, onHomeClick, initialData }) => {
  const [content, setContent] = useState(initialData?.content || "");
  const [files, setFiles] = useState(initialData?.files || []);
  const [isFocused, setIsFocused] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  }, []);

  // Global drag detection for faster response
  useEffect(() => {
    let dragCounter = 0;

    const handleGlobalDragEnter = (e) => {
      e.preventDefault();
      dragCounter++;
      if (e.dataTransfer?.types?.includes("Files")) {
        setIsDragging(true);
      }
    };

    const handleGlobalDragLeave = (e) => {
      e.preventDefault();
      dragCounter--;
      if (dragCounter === 0) {
        setIsDragging(false);
      }
    };

    const handleGlobalDragOver = (e) => {
      e.preventDefault();
    };

    const handleGlobalDrop = (e) => {
      e.preventDefault();
      dragCounter = 0;
      setIsDragging(false);

      const droppedFiles = Array.from(e.dataTransfer?.files || []);
      if (droppedFiles.length > 0) {
        setFiles((prev) => [...prev, ...droppedFiles]);
      }
    };

    document.addEventListener("dragenter", handleGlobalDragEnter);
    document.addEventListener("dragleave", handleGlobalDragLeave);
    document.addEventListener("dragover", handleGlobalDragOver);
    document.addEventListener("drop", handleGlobalDrop);

    return () => {
      document.removeEventListener("dragenter", handleGlobalDragEnter);
      document.removeEventListener("dragleave", handleGlobalDragLeave);
      document.removeEventListener("dragover", handleGlobalDragOver);
      document.removeEventListener("drop", handleGlobalDrop);
    };
  }, []);

  const handleSubmit = () => {
    if (content.trim() || files.length > 0) {
      onNext({ sourceText: content, content, files });
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    setFiles((prev) => [...prev, ...selectedFiles]);
  };

  const removeFile = (index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  // Get file icon based on type
  const getFileIcon = (file) => {
    const type = file.type || "";
    const name = file.name || "";

    if (type.startsWith("image/")) return Image;
    if (type === "application/pdf" || name.endsWith(".pdf")) return FileText;
    return File;
  };

  // Format file size
  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  const isValid = content.trim().length > 0 || files.length > 0;

  return (
    <div className="min-h-screen flex flex-col bg-bg-100">
      {/* Minimal Header */}
      <header className="flex-shrink-0 bg-bg-100">
        <PhaseIndicator currentPhase={1} onPhaseClick={onPhaseClick} onHomeClick={onHomeClick} />
      </header>

      {/* Main Content - Medium Style */}
      <main className="flex-1 flex flex-col items-center px-6 py-8">
        <motion.div
          className="w-full max-w-4xl mx-auto"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        >
          {/* Title - Serif, elegant */}
          <motion.h1
            className="text-3xl md:text-4xl font-serif text-text-100 text-center mb-3 tracking-tight"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.4 }}
            style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
          >
            소재를 입력해주세요
          </motion.h1>
          <motion.p
            className="text-text-300 text-center mb-12 text-lg"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.4 }}
            style={{ fontFamily: "'Noto Sans KR', sans-serif" }}
          >
            보도자료, 인터뷰 내용, 데이터 등을 자유롭게 입력하세요
          </motion.p>

          {/* Writing Area - with drag & drop */}
          <motion.div
            className="relative mb-8"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.4 }}
          >
            <div
              className={`
                relative transition-all duration-300 ease-out rounded-2xl
                bg-always-white
                ${isDragging
                  ? "border-2 border-dashed border-accent-main-100"
                  : "border border-border-200/20"
                }
                ${isFocused
                  ? "shadow-2xl shadow-text-100/15"
                  : "shadow-xl shadow-text-100/8"
                }
              `}
            >
              {/* Drag overlay */}
              <AnimatePresence>
                {isDragging && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="absolute inset-0 z-10 flex items-center justify-center rounded-2xl bg-accent-main-100/10 backdrop-blur-[2px]"
                  >
                    <motion.div
                      className="text-center"
                      initial={{ scale: 0.9, y: 10 }}
                      animate={{ scale: 1, y: 0 }}
                      exit={{ scale: 0.9, y: 10 }}
                      transition={{ type: "spring", stiffness: 300, damping: 25 }}
                    >
                      <motion.div
                        animate={{
                          y: [0, -8, 0],
                        }}
                        transition={{
                          repeat: Infinity,
                          duration: 1.5,
                          ease: "easeInOut"
                        }}
                        className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-accent-main-100/20 flex items-center justify-center"
                      >
                        <Paperclip className="w-8 h-8 text-accent-main-100" />
                      </motion.div>
                      <p className="text-accent-main-100 font-medium text-lg">파일을 여기에 놓으세요</p>
                      <p className="text-accent-main-100/60 text-sm mt-1">PDF, HWP, DOC, 이미지 지원</p>
                    </motion.div>
                  </motion.div>
                )}
              </AnimatePresence>

              <textarea
                ref={textareaRef}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                onKeyDown={handleKeyDown}
                onFocus={() => setIsFocused(true)}
                onBlur={() => setIsFocused(false)}
                placeholder="이야기를 시작하세요..."
                className="
                  w-full min-h-[480px] p-10 pb-20
                  bg-transparent
                  border-0 resize-none rounded-2xl
                  text-text-100 placeholder:text-text-400/40
                  focus:outline-none
                  text-xl leading-loose
                "
                style={{
                  fontFamily: "Georgia, 'Noto Serif KR', serif",
                  caretColor: "hsl(var(--accent-main-100))"
                }}
              />

              {/* Bottom area: Files + Character count */}
              <div className="absolute bottom-4 left-6 right-6 flex items-end justify-between">
                {/* File chips - small, subtle */}
                <div className="flex flex-wrap gap-1.5 max-w-[70%]">
                  <AnimatePresence>
                    {files.map((file, index) => {
                      const FileIcon = getFileIcon(file);
                      return (
                        <motion.div
                          key={`${file.name}-${index}`}
                          initial={{ opacity: 0, scale: 0.8 }}
                          animate={{ opacity: 1, scale: 1 }}
                          exit={{ opacity: 0, scale: 0.8 }}
                          className="
                            group flex items-center gap-1.5 px-2.5 py-1
                            bg-bg-100 hover:bg-bg-200 rounded-lg
                            text-xs text-text-300
                            transition-colors cursor-default
                          "
                        >
                          <FileIcon className="w-3.5 h-3.5 text-text-400" />
                          <span className="max-w-[100px] truncate">{file.name}</span>
                          <span className="text-text-400/60">{formatFileSize(file.size)}</span>
                          <button
                            onClick={() => removeFile(index)}
                            className="p-0.5 opacity-0 group-hover:opacity-100 hover:bg-bg-300 rounded transition-all"
                          >
                            <X className="w-3 h-3 text-text-400" />
                          </button>
                        </motion.div>
                      );
                    })}
                  </AnimatePresence>
                </div>

                {/* Character count */}
                <div className="text-text-400/40 text-sm flex-shrink-0">
                  {content.length > 0 && `${content.length.toLocaleString()}자`}
                </div>
              </div>
            </div>
          </motion.div>

          {/* Action Bar - Clean, minimal */}
          <motion.div
            className="flex items-center justify-between pt-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4, duration: 0.4 }}
          >
            {/* File Upload - Ghost style */}
            <button
              onClick={() => fileInputRef.current?.click()}
              className="
                flex items-center gap-2 px-4 py-2.5
                text-text-400 hover:text-text-200
                rounded-full
                transition-all duration-200
                hover:bg-bg-100
              "
            >
              <Paperclip className="w-5 h-5" />
              <span className="text-sm font-medium">첨부</span>
            </button>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              onChange={handleFileSelect}
              className="hidden"
              accept=".pdf,.doc,.docx,.txt,.hwp"
            />

            {/* Submit Button - Elegant */}
            <motion.button
              onClick={handleSubmit}
              disabled={!isValid}
              className={`
                flex items-center gap-2 px-8 py-3
                rounded-full font-medium text-sm
                transition-all duration-300
                ${isValid
                  ? "bg-text-100 text-bg-000 hover:bg-text-200 shadow-lg shadow-text-100/20"
                  : "bg-bg-200 text-text-400 cursor-not-allowed"
                }
              `}
              whileHover={isValid ? { scale: 1.02, y: -1 } : {}}
              whileTap={isValid ? { scale: 0.98 } : {}}
            >
              <span>다음 단계</span>
              <ArrowRight className="w-4 h-4" />
            </motion.button>
          </motion.div>

          {/* Keyboard Hint - Very subtle */}
          <motion.p
            className="text-center text-text-400/40 text-xs mt-8 font-light"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6, duration: 0.4 }}
          >
            <kbd className="px-1.5 py-0.5 bg-bg-100 rounded text-[10px] font-mono">⌘</kbd>
            <span className="mx-1">+</span>
            <kbd className="px-1.5 py-0.5 bg-bg-100 rounded text-[10px] font-mono">Enter</kbd>
          </motion.p>
        </motion.div>
      </main>
    </div>
  );
};

export default Phase1View;
