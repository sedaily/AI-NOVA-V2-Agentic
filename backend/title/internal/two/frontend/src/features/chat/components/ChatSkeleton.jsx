import React from 'react';
import { motion } from 'framer-motion';

const ChatSkeleton = () => {
  return (
    <div className="flex flex-col h-full p-4 space-y-4">
      {/* 사용자 메시지 스켈레톤 */}
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.3 }}
        className="flex justify-end"
      >
        <div className="max-w-[70%] bg-accent-main-100/10 rounded-2xl px-4 py-3 space-y-2">
          <div className="h-4 bg-accent-main-100/20 rounded-full animate-pulse" style={{ width: '200px' }} />
          <div className="h-4 bg-accent-main-100/20 rounded-full animate-pulse" style={{ width: '160px' }} />
        </div>
      </motion.div>

      {/* AI 메시지 스켈레톤 */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.3, delay: 0.1 }}
        className="flex justify-start"
      >
        <div className="flex gap-3 max-w-[80%]">
          {/* 아바타 */}
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500/20 to-blue-500/20 animate-pulse" />
          
          {/* 메시지 */}
          <div className="flex-1 bg-bg-300/50 rounded-2xl px-4 py-3 space-y-3">
            <div className="h-4 bg-bg-400/50 rounded-full animate-pulse" style={{ width: '90%' }} />
            <div className="h-4 bg-bg-400/50 rounded-full animate-pulse" style={{ width: '75%' }} />
            <div className="h-4 bg-bg-400/50 rounded-full animate-pulse" style={{ width: '85%' }} />
            
            {/* 타이틀 카드 스켈레톤 */}
            <div className="grid gap-2 mt-4">
              {[1, 2, 3].map((index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: 0.2 + index * 0.1 }}
                  className="bg-bg-200/50 rounded-xl p-3 border border-bg-300/50"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 space-y-2">
                      <div className="h-3 bg-bg-400/50 rounded-full animate-pulse" style={{ width: '40px' }} />
                      <div className="h-4 bg-bg-400/50 rounded-full animate-pulse" style={{ width: '80%' }} />
                    </div>
                    <div className="w-8 h-8 rounded-lg bg-bg-400/50 animate-pulse" />
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </motion.div>

      {/* 추가 메시지 스켈레톤 */}
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.3, delay: 0.5 }}
        className="flex justify-end"
      >
        <div className="max-w-[70%] bg-accent-main-100/10 rounded-2xl px-4 py-3">
          <div className="h-4 bg-accent-main-100/20 rounded-full animate-pulse" style={{ width: '150px' }} />
        </div>
      </motion.div>

      {/* AI 타이핑 인디케이터 */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.3, delay: 0.6 }}
        className="flex justify-start"
      >
        <div className="flex gap-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500/20 to-blue-500/20 animate-pulse" />
          <div className="bg-bg-300/50 rounded-2xl px-4 py-3 flex items-center gap-1">
            <motion.div
              animate={{ opacity: [0.3, 1, 0.3] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="w-2 h-2 bg-bg-400 rounded-full"
            />
            <motion.div
              animate={{ opacity: [0.3, 1, 0.3] }}
              transition={{ duration: 1.5, delay: 0.2, repeat: Infinity }}
              className="w-2 h-2 bg-bg-400 rounded-full"
            />
            <motion.div
              animate={{ opacity: [0.3, 1, 0.3] }}
              transition={{ duration: 1.5, delay: 0.4, repeat: Infinity }}
              className="w-2 h-2 bg-bg-400 rounded-full"
            />
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default ChatSkeleton;