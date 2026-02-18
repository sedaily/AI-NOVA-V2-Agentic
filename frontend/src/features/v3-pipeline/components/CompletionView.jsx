import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  Check,
  Copy,
  Download,
  Plus,
  FileText,
  CheckCircle,
  Save,
} from "lucide-react";

const CompletionView = ({ articleData, onNewArticle, onSaveArticle }) => {
  const [copied, setCopied] = useState(false);
  const [copiedTitle, setCopiedTitle] = useState(false);
  const [saved, setSaved] = useState(false);

  const title = articleData?.title || "";
  const body = articleData?.finalArticle || articleData?.draft || "";
  const fullArticle = `${title}\n\n${body}`;

  const handleCopyAll = async () => {
    await navigator.clipboard.writeText(fullArticle);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCopyTitle = async () => {
    await navigator.clipboard.writeText(title);
    setCopiedTitle(true);
    setTimeout(() => setCopiedTitle(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([fullArticle], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `기사_${new Date().toLocaleDateString("ko-KR").replace(/\./g, "").replace(/ /g, "_")}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleSave = () => {
    if (onSaveArticle) {
      onSaveArticle({
        id: Date.now().toString(),
        title,
        body,
        fullArticle,
        wordCount: body.length,
        createdAt: new Date().toISOString(),
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-bg-100">
      {/* Main Content */}
      <main className="flex-1 flex flex-col items-center px-6 py-12">
        <motion.div
          className="w-full max-w-3xl mx-auto"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {/* Success Header */}
          <motion.div
            className="text-center mb-10"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1, duration: 0.4 }}
          >
            <motion.div
              className="w-16 h-16 mx-auto mb-6 rounded-full bg-green-100 flex items-center justify-center"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
            >
              <CheckCircle className="w-8 h-8 text-green-600" />
            </motion.div>
            <h1
              className="text-3xl md:text-4xl text-text-100 mb-3 tracking-tight"
              style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
            >
              기사 작성 완료
            </h1>
            <p
              className="text-text-300 text-lg"
              style={{ fontFamily: "'Noto Sans KR', sans-serif" }}
            >
              아래에서 최종 기사를 확인하고 복사하세요
            </p>
          </motion.div>

          {/* Article Preview Card */}
          <motion.div
            className="bg-always-white rounded-2xl shadow-xl shadow-text-100/10 overflow-hidden mb-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.4 }}
          >
            {/* Title Section */}
            <div className="p-6 border-b border-border-200/30">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <span className="text-xs text-text-400 uppercase tracking-wider mb-2 block">
                    제목
                  </span>
                  <h2
                    className="text-xl font-medium text-text-100 leading-relaxed"
                    style={{ fontFamily: "Georgia, 'Noto Serif KR', serif" }}
                  >
                    {title}
                  </h2>
                </div>
                <button
                  onClick={handleCopyTitle}
                  className="flex-shrink-0 p-2 text-text-400 hover:text-text-200 hover:bg-bg-100 rounded-lg transition-all"
                  title="제목 복사"
                >
                  {copiedTitle ? (
                    <Check className="w-4 h-4 text-green-500" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>

            {/* Body Section */}
            <div className="p-6">
              <span className="text-xs text-text-400 uppercase tracking-wider mb-3 block">
                본문
              </span>
              <div
                className="text-text-100 leading-loose whitespace-pre-wrap max-h-[400px] overflow-y-auto"
                style={{ fontFamily: "Georgia, 'Noto Serif KR', serif" }}
              >
                {body}
              </div>
            </div>

            {/* Stats Bar */}
            <div className="px-6 py-4 bg-bg-100/50 flex items-center justify-between text-sm text-text-400">
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1.5">
                  <FileText className="w-4 h-4" />
                  {body.length.toLocaleString()}자
                </span>
              </div>
              <span>
                {new Date().toLocaleDateString("ko-KR", {
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </span>
            </div>
          </motion.div>

          {/* Action Buttons */}
          <motion.div
            className="flex flex-col sm:flex-row items-center justify-center gap-3"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5, duration: 0.4 }}
          >
            {/* Copy All Button - Primary */}
            <motion.button
              onClick={handleCopyAll}
              className={`
                flex items-center justify-center gap-2 px-8 py-3.5
                rounded-full font-medium text-sm w-full sm:w-auto
                transition-all duration-300
                ${copied
                  ? "bg-green-500 text-white"
                  : "bg-text-100 text-bg-000 hover:bg-text-200 shadow-lg shadow-text-100/20"
                }
              `}
              whileHover={!copied ? { scale: 1.02, y: -1 } : {}}
              whileTap={!copied ? { scale: 0.98 } : {}}
            >
              {copied ? (
                <>
                  <Check className="w-4 h-4" />
                  <span>복사됨</span>
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4" />
                  <span>전체 복사</span>
                </>
              )}
            </motion.button>

            {/* Save Button - Secondary */}
            <motion.button
              onClick={handleSave}
              disabled={saved}
              className={`
                flex items-center justify-center gap-2 px-6 py-3.5
                rounded-full font-medium text-sm w-full sm:w-auto
                transition-all duration-300
                ${saved
                  ? "bg-green-500 text-white"
                  : "bg-bg-200 text-text-200 hover:bg-bg-300"
                }
              `}
              whileHover={!saved ? { scale: 1.02 } : {}}
              whileTap={!saved ? { scale: 0.98 } : {}}
            >
              {saved ? (
                <>
                  <Check className="w-4 h-4" />
                  <span>저장됨</span>
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  <span>저장</span>
                </>
              )}
            </motion.button>

            {/* Download Button - Secondary */}
            <motion.button
              onClick={handleDownload}
              className="
                flex items-center justify-center gap-2 px-6 py-3.5
                rounded-full font-medium text-sm w-full sm:w-auto
                bg-bg-200 text-text-200 hover:bg-bg-300
                transition-all duration-200
              "
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Download className="w-4 h-4" />
              <span>다운로드</span>
            </motion.button>

            {/* New Article Button - Ghost */}
            <motion.button
              onClick={onNewArticle}
              className="
                flex items-center justify-center gap-2 px-6 py-3.5
                rounded-full font-medium text-sm w-full sm:w-auto
                text-text-400 hover:text-text-200 hover:bg-bg-200
                transition-all duration-200
              "
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Plus className="w-4 h-4" />
              <span>새 기사 작성</span>
            </motion.button>
          </motion.div>
        </motion.div>
      </main>
    </div>
  );
};

export default CompletionView;
