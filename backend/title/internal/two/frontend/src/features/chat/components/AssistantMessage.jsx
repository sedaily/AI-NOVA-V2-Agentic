import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";
import remarkMath from "remark-math";
import remarkEmoji from "remark-emoji";
import rehypeKatex from "rehype-katex";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Copy, ThumbsUp, ThumbsDown, Check } from "lucide-react";
import "../styles/markdown.css";

const AssistantMessage = React.memo(({ content, timestamp, messageId }) => {
  const [copiedIndex, setCopiedIndex] = React.useState(null);
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState(null);

  const handleCopyTitle = (title, index) => {
    navigator.clipboard.writeText(title);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  // 전체 메시지 복사
  const handleCopyMessage = async () => {
    try {
      const textContent =
        typeof content === "string"
          ? content
          : content?.titles
          ? content.titles.join("\n")
          : "";
      await navigator.clipboard.writeText(textContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("복사 실패:", err);
    }
  };

  // 피드백 기능
  const handleFeedback = (type) => {
    setFeedback(type === feedback ? null : type);
    console.log("Feedback:", type, "for message:", messageId);
  };

  // Check if content contains titles array
  const hasValidTitles =
    content && typeof content === "object" && Array.isArray(content.titles);

  // Format message content for display
  const formatContent = () => {
    if (hasValidTitles) {
      return (
        <>
          <div className="whitespace-normal break-words mb-4 leading-relaxed">
            안녕하세요! 기사 제목을 생성했습니다.
          </div>
          <div className="whitespace-normal break-words mb-4 leading-relaxed">
            아래 {content.titles.length}개의 제목 중에서 가장 적합한 것을
            선택하시거나, 수정하여 사용하실 수 있습니다:
          </div>
          <ol className="list-decimal space-y-2 pl-7 mb-4">
            {content.titles.map((title, index) => (
              <li
                key={index}
                className="whitespace-normal break-words group/item relative leading-relaxed"
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="flex-1">{title}</span>
                  <button
                    onClick={() => handleCopyTitle(title, index)}
                    className="opacity-0 group-hover/item:opacity-100 transition-opacity duration-200 p-1 hover:bg-bg-300 rounded-md shrink-0 ml-2"
                    title="복사"
                  >
                    {copiedIndex === index ? (
                      <span className="text-xs text-accent-main-100">✓</span>
                    ) : (
                      <Copy size={14} className="text-text-400" />
                    )}
                  </button>
                </div>
              </li>
            ))}
          </ol>
          <div className="whitespace-normal break-words leading-relaxed">
            추가로 다른 스타일의 제목이 필요하시거나, 특정 톤앤매너로 수정을
            원하시면 말씀해 주세요.
          </div>
        </>
      );
    } else if (content && typeof content === "object" && content.isError) {
      return (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="text-red-800 whitespace-normal break-words">
            {content.content || content.message || "오류가 발생했습니다"}
          </div>
        </div>
      );
    } else {
      // 마크다운 렌더링 적용
      const textContent = typeof content === "string" ? content : "";
      return (
        <div
          className="chatbot-markdown prose prose-lg max-w-none"
          style={{
            fontFamily: 'ui-serif, Georgia, Cambria, "Times New Roman", Times, serif',
          }}
        >
          <ReactMarkdown
            remarkPlugins={[remarkGfm, remarkBreaks, remarkMath, remarkEmoji]}
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
                <h1 className="text-2xl font-bold mb-4">{children}</h1>
              ),
              h2: ({ children }) => (
                <h2 className="text-xl font-bold mb-3">{children}</h2>
              ),
              h3: ({ children }) => (
                <h3 className="text-lg font-semibold mb-2">{children}</h3>
              ),
              ul: ({ children }) => (
                <ul className="list-disc pl-6 mb-4 space-y-2">{children}</ul>
              ),
              ol: ({ children }) => (
                <ol className="list-decimal pl-6 mb-4 space-y-2">{children}</ol>
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
                const match = /language-(\w+)/.exec(className || "");
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
              table: ({ children }) => (
                <div className="overflow-x-auto my-4">
                  <table className="min-w-full border-collapse border border-gray-300">
                    {children}
                  </table>
                </div>
              ),
              thead: ({ children }) => (
                <thead className="bg-gray-100">{children}</thead>
              ),
              tbody: ({ children }) => <tbody>{children}</tbody>,
              tr: ({ children }) => (
                <tr className="border-b border-gray-300">{children}</tr>
              ),
              th: ({ children }) => (
                <th className="px-4 py-2 text-left font-semibold">
                  {children}
                </th>
              ),
              td: ({ children }) => (
                <td className="px-4 py-2 border-l border-gray-300">
                  {children}
                </td>
              ),
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
              hr: () => <hr className="my-6 border-t border-gray-300" />,
            }}
          >
            {textContent}
          </ReactMarkdown>
        </div>
      );
    }
  };

  return (
    <div className="mb-8 last:mb-0 transition-all duration-200">
      <div
        className="mx-auto w-full p-4 rounded-2xl"
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
          {formatContent()}
        </div>

        {/* 액션 버튼들 */}
        <div className="flex items-center gap-2 mt-3">
          {/* 복사 버튼 */}
          <button
            onClick={handleCopyMessage}
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
              fill={feedback === "dislike" ? "currentColor" : "none"}
            />
          </button>

          {/* 복사 완료 메시지 */}
          {copied && (
            <span className="text-xs text-green-400 ml-2">복사됨!</span>
          )}
        </div>
      </div>
    </div>
  );
});

AssistantMessage.displayName = "AssistantMessage";

export default AssistantMessage;
