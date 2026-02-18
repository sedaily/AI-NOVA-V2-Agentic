import React from "react";
import { motion } from "framer-motion";
import { PenLine, FileText, CheckCircle, Type, Clock, ChevronRight, Trash2, Zap } from "lucide-react";

const HomeView = ({
  onStartPipeline,
  onAutoWrite,
  onQuickAction,
  savedArticles = [],
  onLoadArticle,
  onDeleteArticle
}) => {
  const quickActions = [
    {
      id: "title",
      icon: Type,
      label: "제목 생성",
      description: "초안의 제목만 생성",
    },
    {
      id: "proofread",
      icon: CheckCircle,
      label: "교열하기",
      description: "맞춤법/문법 검사",
    },
    {
      id: "revise",
      icon: FileText,
      label: "퇴고하기",
      description: "문체/표현 다듬기",
    },
  ];

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-12 bg-bg-100">
      {/* Main Content */}
      <motion.div
        className="w-full max-w-2xl mx-auto text-center"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Logo / Branding */}
        <motion.div
          className="mb-10"
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.1, duration: 0.4 }}
        >
          <h1 className="text-3xl font-semibold tracking-tight text-text-100 mb-3">NOVA</h1>
          <p className="text-text-300 text-base">
            AI가 초안을, 기자가 기사를 완성합니다
          </p>
        </motion.div>

        {/* Main CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 w-full max-w-lg mx-auto mb-16">
          {/* Manual Pipeline Button */}
          <motion.button
            onClick={onStartPipeline}
            className="
              group relative flex-1
              bg-text-100 hover:bg-text-200
              text-bg-000 font-semibold
              py-5 px-6 rounded-2xl
              shadow-lg shadow-text-100/15
              transition-all duration-300
              flex items-center justify-center gap-3
            "
            whileHover={{ scale: 1.02, y: -2 }}
            whileTap={{ scale: 0.98 }}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.4 }}
          >
            <PenLine className="w-5 h-5" />
            <span className="text-base">단계별 작성</span>
          </motion.button>

          {/* Auto Write Button */}
          <motion.button
            onClick={onAutoWrite}
            className="
              group relative flex-1
              bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700
              text-white font-semibold
              py-5 px-6 rounded-2xl
              shadow-lg shadow-blue-500/25
              transition-all duration-300
              flex items-center justify-center gap-3
            "
            whileHover={{ scale: 1.02, y: -2 }}
            whileTap={{ scale: 0.98 }}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25, duration: 0.4 }}
          >
            <Zap className="w-5 h-5" />
            <span className="text-base">자동 작성</span>
          </motion.button>
        </div>

        {/* Divider */}
        <motion.div
          className="flex items-center gap-4 mb-8"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.4 }}
        >
          <div className="flex-1 h-px bg-border-200" />
          <span className="text-text-400 text-sm">또는 빠른 작업</span>
          <div className="flex-1 h-px bg-border-200" />
        </motion.div>

        {/* Quick Actions */}
        <motion.div
          className="grid grid-cols-3 gap-4"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.4 }}
        >
          {quickActions.map((action, index) => (
            <motion.button
              key={action.id}
              onClick={() => onQuickAction(action.id)}
              className="
                group flex flex-col items-center gap-3 p-6
                bg-always-white
                shadow-sm shadow-text-100/5 hover:shadow-md hover:shadow-text-100/10
                rounded-2xl transition-all duration-300
                border border-border-100/50 hover:border-border-200
              "
              whileHover={{ y: -4 }}
              whileTap={{ scale: 0.98 }}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 + index * 0.1, duration: 0.3 }}
            >
              <div
                className="
                  p-3 rounded-xl
                  bg-bg-200/50 text-text-300
                  group-hover:bg-text-100 group-hover:text-bg-000
                  transition-all duration-200
                "
              >
                <action.icon className="w-5 h-5" />
              </div>
              <div className="text-center">
                <p className="font-medium text-text-100 mb-1">{action.label}</p>
                <p className="text-xs text-text-400">{action.description}</p>
              </div>
            </motion.button>
          ))}
        </motion.div>

        {/* Saved Articles Section */}
        {savedArticles.length > 0 && (
          <motion.div
            className="mt-12 w-full"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.4 }}
          >
            {/* Section Header */}
            <div className="flex items-center gap-4 mb-4">
              <div className="flex-1 h-px bg-border-200" />
              <span className="text-text-400 text-sm flex items-center gap-2">
                <Clock className="w-4 h-4" />
                저장된 기사
              </span>
              <div className="flex-1 h-px bg-border-200" />
            </div>

            {/* Articles List */}
            <div className="space-y-3">
              {savedArticles.slice(0, 5).map((article, index) => (
                <motion.div
                  key={article.id}
                  className="
                    group flex items-center gap-4 p-4
                    bg-always-white rounded-2xl
                    shadow-sm shadow-text-100/5 hover:shadow-md hover:shadow-text-100/10
                    transition-all duration-300 cursor-pointer
                  "
                  onClick={() => onLoadArticle?.(article)}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.5 + index * 0.05, duration: 0.3 }}
                  whileHover={{ x: 4 }}
                >
                  {/* Article Icon */}
                  <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-bg-100 flex items-center justify-center">
                    <FileText className="w-5 h-5 text-text-400" />
                  </div>

                  {/* Article Info */}
                  <div className="flex-1 min-w-0">
                    <h4
                      className="font-medium text-text-100 truncate"
                      style={{ fontFamily: "Georgia, 'Noto Serif KR', serif" }}
                    >
                      {article.title || "제목 없음"}
                    </h4>
                    <p className="text-xs text-text-400 mt-0.5">
                      {article.createdAt
                        ? new Date(article.createdAt).toLocaleDateString("ko-KR", {
                            year: "numeric",
                            month: "short",
                            day: "numeric",
                          })
                        : "날짜 없음"
                      }
                      {article.wordCount && ` · ${article.wordCount.toLocaleString()}자`}
                    </p>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteArticle?.(article.id);
                      }}
                      className="
                        p-2 rounded-lg opacity-0 group-hover:opacity-100
                        text-text-400 hover:text-red-500 hover:bg-red-50
                        transition-all duration-200
                      "
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                    <ChevronRight className="w-5 h-5 text-text-400 group-hover:text-text-200 transition-colors" />
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Show more link if there are more articles */}
            {savedArticles.length > 5 && (
              <motion.button
                className="
                  w-full mt-3 py-3 text-sm text-text-400 hover:text-text-200
                  transition-colors duration-200
                "
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.7 }}
              >
                {savedArticles.length - 5}개 더 보기
              </motion.button>
            )}
          </motion.div>
        )}
      </motion.div>

      {/* Footer hint */}
      <motion.p
        className="mt-12 text-text-400 text-sm text-center max-w-md"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6, duration: 0.4 }}
      >
        <span className="font-medium">단계별:</span> 5단계를 직접 확인하며 작성 |
        <span className="font-medium ml-1">자동:</span> AI가 한 번에 완성
      </motion.p>
    </div>
  );
};

export default HomeView;
