import React, { memo, useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { useSmoothStreaming } from "../hooks/useSmoothStreaming";
import { Copy, ThumbsUp, ThumbsDown, Check } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";
import remarkMath from "remark-math";
import remarkEmoji from "remark-emoji";
import rehypeKatex from "rehype-katex";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import "../styles/markdown.css";

/**
 * 교열 진행 상태 컴포넌트
 */
const ProofreadingProgress = ({ step }) => {
  const steps = [
    "텍스트 분석 중",
    "맞춤법 및 문법 검사 중",
    "문장 구조 검토 중",
    "최종본 작성 중",
  ];

  return (
    <div className="space-y-3">
      {steps.slice(0, Math.min(step + 1, 4)).map((text, index) => (
        <motion.div
          key={index}
          className="flex items-center gap-2"
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: index * 0.25 }}
        >
          <span
            className={`text-sm ${
              index === step ? "text-text-200" : "text-text-400"
            }`}
          >
            {text}
          </span>

          {index === step && (
            <div className="flex space-x-0.5">
              {[0, 1, 2].map((i) => (
                <motion.div
                  key={i}
                  className="w-1 h-1 bg-accent-main-100 rounded-full"
                  animate={{
                    opacity: [0.3, 1, 0.3],
                  }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    delay: i * 0.2,
                  }}
                />
              ))}
            </div>
          )}

          {index < step && (
            <motion.div
              className="h-px bg-border-100 flex-1 ml-2"
              initial={{ width: 0 }}
              animate={{ width: "100%" }}
              transition={{ duration: 0.4, delay: index * 0.25 + 0.15 }}
            />
          )}
        </motion.div>
      ))}
    </div>
  );
};

/**
 * 최적화된 스트리밍 어시스턴트 메시지 컴포넌트
 * - 부드러운 텍스트 애니메이션
 * - 메모이제이션으로 리렌더링 최소화
 * - 가상 타이핑 효과
 */
const StreamingAssistantMessage = memo(
  ({
    content,
    isStreaming: propIsStreaming,
    timestamp,
    onContentUpdate,
    messageId,
  }) => {
    const { displayText, isStreaming, appendText, finish, reset } =
      useSmoothStreaming({
        charDelay: 18, // 기본 18ms/글자 (사람이 타이핑하는 듯한 속도)
        minDelay: 5, // 최소 5ms (빠른 부분)
        maxDelay: 50, // 최대 50ms (구두점에서 자연스러운 멈춤)
        smoothness: 0.88, // 약간의 속도 변화로 자연스럽게
      });

    const lastContentRef = useRef("");
    const [copied, setCopied] = useState(false);
    const [feedback, setFeedback] = useState(null); // 'like' | 'dislike' | null
    const [proofreadingStep, setProofreadingStep] = useState(0);
    const proofreadingStepsRef = useRef(null);

    // 복사 기능
    const handleCopy = async () => {
      try {
        await navigator.clipboard.writeText(displayText || content || "");
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } catch (err) {
        console.error("복사 실패:", err);
      }
    };

    // 피드백 기능
    const handleFeedback = (type) => {
      setFeedback(type === feedback ? null : type);
      // TODO: API 호출로 피드백 저장
      console.log("Feedback:", type, "for message:", messageId);
    };

    // 교열 단계 업데이트
    useEffect(() => {
      if (propIsStreaming && !displayText && !proofreadingStepsRef.current) {
        // 교열 단계 애니메이션 시작
        proofreadingStepsRef.current = setInterval(() => {
          setProofreadingStep((prev) => (prev < 3 ? prev + 1 : prev));
        }, 2000); // 2초마다 단계 변경
      } else if (displayText && proofreadingStepsRef.current) {
        // 텍스트가 시작되면 애니메이션 중지
        clearInterval(proofreadingStepsRef.current);
        proofreadingStepsRef.current = null;
        setProofreadingStep(4); // 완료 상태
      }
    }, [propIsStreaming, displayText]);

    // 컴포넌트 언마운트 시 타이머 정리
    useEffect(() => {
      return () => {
        if (proofreadingStepsRef.current) {
          clearInterval(proofreadingStepsRef.current);
        }
      };
    }, []);

    // 새로운 콘텐츠 청크 처리
    useEffect(() => {
      if (content && content !== lastContentRef.current) {
        const newChunk = content.slice(lastContentRef.current.length);
        if (newChunk) {
          appendText(newChunk);
        }
        lastContentRef.current = content;
      }
    }, [content, appendText]);

    // 스트리밍 완료 처리
    useEffect(() => {
      if (!propIsStreaming && lastContentRef.current) {
        finish();
      }
    }, [propIsStreaming, finish]);

    // 초기화
    useEffect(() => {
      return () => {
        reset();
      };
    }, [reset]);

    // 커서 애니메이션 (제거됨 - 딜레이 방식에서는 불필요)

    // 콘텐츠 업데이트 콜백
    useEffect(() => {
      if (onContentUpdate) {
        onContentUpdate(displayText);
      }
    }, [displayText, onContentUpdate]);

    return (
      <div className="mb-8 last:mb-0">
        {/* 스트리밍 인디케이터와 메시지를 같은 위치에 표시 */}
        <div className="px-4">
          <div className="pt-1">
            {/* 교열 진행 상태 또는 실제 답변 */}
            {propIsStreaming && !displayText ? (
              <ProofreadingProgress step={proofreadingStep} />
            ) : (
              <div
                className="mx-auto w-full rounded-2xl flex-1"
                style={{
                  transform: "none",
                  backgroundColor: "hsl(var(--bg-100))",
                }}
              >
                <div
                  data-testid="assistant-message"
                  className="grid grid-cols-1 gap-2 py-0.5"
                  style={{
                    fontFamily:
                      'ui-serif, Georgia, Cambria, "Times New Roman", Times, serif',
                    fontSize: "1rem",
                    lineHeight: "1.75rem",
                    letterSpacing: "normal",
                    color: "hsl(var(--text-100))",
                  }}
                >
                  {/* 텍스트 콘텐츠 - 마크다운 적용 + 부드러운 출력 */}
                  {(displayText || isStreaming) && (
                    <div
                      className="chatbot-markdown prose prose-lg max-w-none"
                      style={{
                        opacity: displayText ? 1 : 0,
                        transform: displayText
                          ? "translateY(0)"
                          : "translateY(4px)",
                        transition:
                          "opacity 0.15s ease-out, transform 0.15s ease-out",
                        color: "hsl(var(--text-100))",
                        fontFamily:
                          'ui-serif, Georgia, Cambria, "Times New Roman", Times, serif',
                      }}
                    >
                      <ReactMarkdown
                        remarkPlugins={[
                          remarkGfm,
                          remarkBreaks,
                          remarkMath,
                          remarkEmoji,
                        ]}
                        rehypePlugins={[rehypeKatex]}
                        components={{
                          p: ({ children }) => (
                            <p
                              className="mb-4 leading-relaxed"
                              style={{ fontFamily: "inherit" }}
                            >
                              {children}
                            </p>
                          ),
                          h1: ({ children }) => (
                            <h1 className="text-2xl font-bold mb-4">
                              {children}
                            </h1>
                          ),
                          h2: ({ children }) => (
                            <h2 className="text-xl font-bold mb-3">
                              {children}
                            </h2>
                          ),
                          h3: ({ children }) => (
                            <h3 className="text-lg font-semibold mb-2">
                              {children}
                            </h3>
                          ),
                          ul: ({ children }) => (
                            <ul className="list-disc pl-6 mb-4 space-y-2">
                              {children}
                            </ul>
                          ),
                          ol: ({ children }) => (
                            <ol className="list-decimal pl-6 mb-4 space-y-2">
                              {children}
                            </ol>
                          ),
                          li: ({ children }) => (
                            <li
                              className="leading-relaxed"
                              style={{ fontFamily: "inherit" }}
                            >
                              {children}
                            </li>
                          ),
                          blockquote: ({ children }) => (
                            <blockquote className="border-l-4 border-gray-300 pl-4 italic my-4">
                              {children}
                            </blockquote>
                          ),
                          code: ({ inline, className, children, ...props }) => {
                            const match = /language-(\w+)/.exec(
                              className || ""
                            );
                            return !inline && match ? (
                              <SyntaxHighlighter
                                style={vscDarkPlus}
                                language={match[1]}
                                PreTag="div"
                                className="rounded-lg overflow-x-auto my-4"
                                {...props}
                              >
                                {String(children).replace(/\n$/, "")}
                              </SyntaxHighlighter>
                            ) : (
                              <code
                                className="bg-bg-300 px-1.5 py-0.5 rounded text-sm font-mono"
                                {...props}
                              >
                                {children}
                              </code>
                            );
                          },
                          a: ({ children, href }) => (
                            <a
                              href={href}
                              className="text-accent-main-100 hover:underline"
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              {children}
                            </a>
                          ),
                          hr: () => (
                            <hr className="my-6 border-t border-gray-300" />
                          ),
                        }}
                      >
                        {displayText}
                      </ReactMarkdown>
                    </div>
                  )}

                  {/* 액션 버튼들 - 메시지 완료 시에만 표시 */}
                  {displayText && !propIsStreaming && (
                    <div className="flex items-center gap-2 mt-3">
                      {/* 복사 버튼 */}
                      <button
                        onClick={handleCopy}
                        className="p-1.5 rounded-lg transition-all duration-200 text-text-400 hover:text-text-100 hover:bg-bg-200"
                        title="복사"
                      >
                        {copied ? (
                          <Check size={16} className="text-green-400" />
                        ) : (
                          <Copy size={16} />
                        )}
                      </button>

                      {/* 좋아요 버튼 */}
                      <button
                        onClick={() => handleFeedback("like")}
                        className={`p-1.5 rounded-lg transition-all duration-200 ${
                          feedback === "like"
                            ? "text-accent-main-100 bg-accent-main-100/10"
                            : "text-text-400 hover:text-text-100 hover:bg-bg-200"
                        }`}
                        title="좋아요"
                      >
                        <ThumbsUp
                          size={16}
                          fill={feedback === "like" ? "currentColor" : "none"}
                        />
                      </button>

                      {/* 싫어요 버튼 */}
                      <button
                        onClick={() => handleFeedback("dislike")}
                        className={`p-1.5 rounded-lg transition-all duration-200 ${
                          feedback === "dislike"
                            ? "text-red-400 bg-red-400/10"
                            : "text-text-400 hover:text-text-100 hover:bg-bg-200"
                        }`}
                        title="싫어요"
                      >
                        <ThumbsDown
                          size={16}
                          fill={
                            feedback === "dislike" ? "currentColor" : "none"
                          }
                        />
                      </button>

                      {/* 복사 완료 메시지 */}
                      {copied && (
                        <span className="text-xs text-green-400 ml-2">
                          복사됨!
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }
);

StreamingAssistantMessage.displayName = "StreamingAssistantMessage";

export default StreamingAssistantMessage;
