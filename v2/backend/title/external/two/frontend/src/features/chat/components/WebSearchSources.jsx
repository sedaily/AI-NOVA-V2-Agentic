import React, { useState } from "react";
import { Globe, ChevronDown } from "lucide-react";

/**
 * 웹검색 출처 표시 컴포넌트 (Claude.ai 스타일)
 * AI 응답 상단에 검색 쿼리와 결과 출처를 접을 수 있는 형태로 표시
 */
const WebSearchSources = ({ query, sources = [] }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!sources || sources.length === 0) return null;

  // URL에서 도메인 추출
  const getDomain = (url) => {
    try {
      const domain = new URL(url).hostname.replace('www.', '');
      return domain;
    } catch {
      return url;
    }
  };

  // Google Favicon API URL
  const getFaviconUrl = (url) => {
    const domain = getDomain(url);
    return `https://www.google.com/s2/favicons?sz=64&domain=${domain}`;
  };

  return (
    <div className="transition-all duration-400 ease-out rounded-lg border border-bg-300 flex flex-col leading-normal my-3 min-h-[2.625rem] overflow-hidden">
      {/* 헤더 (검색 쿼리 + 결과 수) */}
      <div className="flex flex-row min-h-[2.125rem] shrink-0 bg-bg-100">
        <div className="flex flex-col items-center justify-center pl-3 box-border">
          <div className="transition-all w-[1px]" style={{ minHeight: 'calc(-8px + 1.0625rem)' }}></div>
          <div className="transition-all flex items-center justify-center my-1 shrink-0 w-4 h-4 text-text-300">
            <Globe size={16} />
          </div>
          <div
            className={`transition-all grow w-[1px] ${isExpanded ? 'bg-bg-300' : ''}`}
            style={{ minHeight: 'calc(-8px + 1.0625rem)' }}
          ></div>
        </div>

        <div className="w-full flex flex-col min-w-0">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="group/row flex flex-row items-center justify-between gap-4 rounded-lg text-text-300 h-[2.625rem] py-2 px-3 cursor-pointer transition-colors duration-200 hover:text-text-100"
          >
            <div className="flex flex-row items-center gap-2 min-w-0">
              <div className="flex gap-2 text-sm text-left leading-tight overflow-hidden text-ellipsis whitespace-nowrap flex-grow text-text-200">
                {query}
              </div>
            </div>
            <div className="flex flex-row items-center gap-1.5 min-w-0 shrink-0">
              <span className="text-xs text-text-400 pl-1 shrink-0 whitespace-nowrap">
                {sources.length} results
              </span>
              <span className={`inline-flex transition-transform duration-300 ${isExpanded ? 'rotate-180' : 'rotate-0'}`}>
                <ChevronDown size={16} className="text-text-300" />
              </span>
            </div>
          </button>

          {/* 확장 가능한 결과 목록 */}
          <div
            className={`overflow-hidden shrink-0 transition-all duration-300 ${isExpanded ? 'opacity-100' : 'opacity-0 h-0'}`}
            style={{ height: isExpanded ? 'auto' : 0 }}
          >
            <div
              className="min-h-0 overflow-y-auto overflow-x-hidden max-h-[240px]"
              style={{
                maskImage: 'linear-gradient(transparent 0%, black 0px, black calc(100% - 16px), transparent 100%)',
                scrollbarGutter: 'stable'
              }}
            >
              <div className="flex flex-nowrap p-2 pt-0 flex-col">
                {sources.map((source, idx) => (
                  <div key={idx}>
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block"
                    >
                      <div className="flex flex-row gap-4 items-center justify-between rounded-md shrink-0 h-8 px-1.5 mx-0.5 w-full min-w-0 cursor-pointer hover:bg-bg-200 transition-colors">
                        <div className="flex flex-row items-center gap-2 min-w-0">
                          <div className="h-5 w-5 flex items-center justify-center shrink-0">
                            <img
                              alt="favicon"
                              loading="lazy"
                              width={16}
                              height={16}
                              src={getFaviconUrl(source.url)}
                              className="transition duration-500"
                              style={{ maxWidth: 16, maxHeight: 16 }}
                              onError={(e) => {
                                e.target.style.display = 'none';
                              }}
                            />
                          </div>
                          <p className="text-sm whitespace-nowrap overflow-hidden text-ellipsis shrink text-text-100">
                            {source.title}
                          </p>
                          <p className="text-xs text-text-400 line-clamp-1 shrink-0">
                            {getDomain(source.url)}
                          </p>
                        </div>
                      </div>
                    </a>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WebSearchSources;
