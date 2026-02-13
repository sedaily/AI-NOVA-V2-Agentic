import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

const SourceCard = ({ title, sources }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  
  if (!sources || sources.length === 0) return null;

  return (
    <div className="mb-4 rounded-xl bg-bg-200 border border-border-200 p-4">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 text-sm text-text-300 mb-3 w-full hover:text-text-200 transition-colors"
      >
        <span className="font-medium">{title}</span>
        <span className="opacity-60">· 출처</span>
        <div className="ml-auto">
          {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
      </button>

      <div 
        className={`overflow-hidden transition-all duration-300 ease-in-out ${
          isExpanded ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <ul className="space-y-2">
          {sources.map((src, idx) => (
            <li key={idx} className="flex items-center gap-2 text-sm">
              <img
                src={src.favicon || `https://www.google.com/s2/favicons?domain=${src.domain}`}
                className="w-4 h-4"
                alt=""
              />
              <a
                href={src.url}
                target="_blank"
                rel="noreferrer"
                className="text-text-200 hover:underline"
              >
                {src.title}
              </a>
              <span className="text-text-400 text-xs">{src.domain}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default SourceCard;