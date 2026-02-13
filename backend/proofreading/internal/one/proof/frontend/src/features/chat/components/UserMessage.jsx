import React from 'react';
import FileAttachment from './FileAttachment';

const UserMessage = ({ content, timestamp, files, onFileClick }) => {
  // 파일이 있으면 항상 표시 (파일 상자를 위해)
  const hasFiles = files && files.length > 0;
  const hasText = content && content.trim();
  
  if (!hasFiles && !hasText) {
    return null; // 파일도 텍스트도 없으면 렌더링하지 않음
  }

  return (
    <div className="mb-6 last:mb-0 flex justify-end px-4">
      <div className="max-w-[80%] flex flex-col items-end gap-3">
        {/* 첨부파일들 - 파일이 있으면 항상 표시 */}
        {hasFiles && (
          <div className="flex flex-wrap gap-3 justify-end">
            {files.map((file, index) => (
              <FileAttachment
                key={index}
                fileName={file.fileName}
                fileType={file.fileType}
                fileSize={file.fileSize}
                pageCount={file.pageCount}
                onClick={() => onFileClick && onFileClick(file)}
              />
            ))}
          </div>
        )}
        
        {/* 텍스트 메시지 표시 - 사용자 입력 텍스트는 항상 표시 */}
        {hasText && (
          <div
            className="px-4 py-3 rounded-2xl break-words"
            style={{
              backgroundColor: "black",
              color: "white",
              fontFamily: '-apple-system, BlinkMacSystemFont, "Malgun Gothic", "맑은 고딕", sans-serif',
              fontSize: "1rem",
              lineHeight: "1.5rem",
              whiteSpace: "pre-wrap",
            }}
          >
            {content}
          </div>
        )}
        
        {/* 타임스탬프 */}
        {timestamp && (
          <div className="text-xs text-text-400 px-2">
            {new Date(timestamp).toLocaleTimeString('ko-KR', {
              hour: '2-digit',
              minute: '2-digit'
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default UserMessage;