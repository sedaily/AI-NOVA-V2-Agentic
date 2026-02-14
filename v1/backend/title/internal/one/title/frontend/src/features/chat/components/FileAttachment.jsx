import React from 'react';

const FileAttachment = ({ fileName, fileType, fileSize, pageCount, onClick }) => {
  return (
    <div className="relative">
      <div className="group/thumbnail" data-testid="file-thumbnail">
        <div
          className="rounded-lg text-left block cursor-pointer font-ui transition-all rounded-lg border-0.5 border-border-300/25 flex flex-col justify-between gap-2.5 overflow-hidden px-2.5 py-2 bg-bg-100 hover:border-border-200/50 hover:shadow-always-black/10 shadow-sm shadow-always-black/5"
          style={{
            width: "120px",
            height: "120px",
            minWidth: "120px",
            backgroundColor: "hsl(var(--bg-100))",
            borderColor: "hsl(var(--border-300)/25%)",
          }}
          onClick={onClick}
        >
          <div className="relative flex flex-col gap-1 min-h-0">
            <h3
              className="text-[12px] tracking-tighter break-words text-text-100 line-clamp-3"
              style={{
                opacity: 1,
                color: "hsl(var(--text-100))",
              }}
            >
              {fileName}
            </h3>
            <p
              className="text-[10px] line-clamp-1 tracking-tighter break-words text-text-500"
              style={{
                opacity: 1,
                color: "hsl(var(--text-500))",
              }}
            >
              {pageCount
                ? `${pageCount}페이지`
                : `${Math.ceil(fileSize / 1024)}KB`}
            </p>
          </div>

          <div className="relative flex flex-row items-center gap-1 justify-between">
            <div
              className="flex flex-row gap-1 shrink min-w-0"
              style={{ opacity: 1 }}
            >
              <div className="min-w-0 h-[18px] flex flex-row items-center justify-center gap-0.5 px-1 border-0.5 border-border-300/25 shadow-sm rounded bg-bg-000/70 backdrop-blur-sm font-medium">
                <p className="uppercase truncate font-ui text-text-300 text-[11px] leading-[13px]">
                  {fileType === "pdf" ? "PDF" : "TXT"}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FileAttachment;