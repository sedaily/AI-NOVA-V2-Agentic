import React from 'react';
import { X } from 'lucide-react';

const FileViewer = ({ file, isOpen, onClose }) => {
  if (!isOpen || !file) return null;

  return (
    <div className="h-full flex flex-col" style={{ backgroundColor: "hsl(var(--bg-100))" }}>
      {/* 헤더 */}
      <div className="flex items-center justify-between p-4 border-b" style={{ borderColor: "hsl(var(--border-300)/25%)" }}>
        <div className="flex-1 min-w-0">
          <h2 className="text-lg font-semibold truncate" style={{ color: "hsl(var(--text-100))" }}>
            {file.fileName}
          </h2>
          <p className="text-sm" style={{ color: "hsl(var(--text-500))" }}>
            {file.fileType?.toUpperCase()} • {file.pageCount ? `${file.pageCount}페이지` : `${Math.ceil(file.fileSize / 1024)}KB`}
          </p>
        </div>
        <button
          onClick={onClose}
          className="ml-4 p-2 rounded-full transition-colors hover:bg-opacity-10"
          style={{ 
            color: "hsl(var(--text-400))",
            backgroundColor: "transparent"
          }}
          onMouseEnter={(e) => e.target.style.backgroundColor = "hsl(var(--bg-000))"}
          onMouseLeave={(e) => e.target.style.backgroundColor = "transparent"}
        >
          <X size={20} />
        </button>
      </div>
      
      {/* 파일 내용 */}
      <div className="flex-1 overflow-auto p-4">
        <div className="rounded-lg p-4 h-full" style={{ backgroundColor: "hsl(var(--bg-000))" }}>
          <pre className="whitespace-pre-wrap text-sm font-mono leading-relaxed" style={{ color: "white" }}>
            {file.content || '파일 내용을 불러올 수 없습니다.'}
          </pre>
        </div>
      </div>
    </div>
  );
};

export default FileViewer;