import React from "react";

const BasicNProGuideSection = ({ selectedEngine = "Basic" }) => {
  return (
    <div className="w-full max-w-4xl pt-6">
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-text-100 mb-3">
          {selectedEngine === "Basic"
            ? "💼 비즈니스 모드"
            : "📰 종합 뉴스 모드"}
        </h2>
        <p className="text-sm text-text-300 leading-relaxed">
          {selectedEngine === "Basic"
            ? "경제·금융·산업·증권·부동산 기사에 최적화된 교열 서비스"
            : "정치·사회·문화·국제·스포츠 기사에 최적화된 교열 서비스"}
        </p>
      </div>

      <div className="space-y-5">
        <div
          className="flex items-start p-4 rounded-lg"
          style={{ backgroundColor: "hsl(var(--bg-200))" }}
        >
          <div className="mr-4 mt-0.5">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth="1.5"
              stroke="currentColor"
              className="h-5 w-5 text-blue-500"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z"
              />
            </svg>
          </div>
          <div>
            <p className="text-sm text-text-200 leading-relaxed">
              <span className="font-medium">시작하는 방법:</span> 입력창에 기사
              본문을 붙여넣고 전송 버튼을 클릭하세요
            </p>
          </div>
        </div>

        <div
          className="flex items-start p-4 rounded-lg"
          style={{ backgroundColor: "hsl(var(--bg-200))" }}
        >
          <div className="mr-4 mt-0.5">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth="1.5"
              stroke="currentColor"
              className="h-5 w-5 text-green-500"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M8.25 3v1.5M4.5 8.25H3m18 0h-1.5M4.5 12H3m18 0h-1.5m-15 3.75H3m18 0h-1.5M8.25 19.5V21M12 3v1.5m0 15V21m3.75-18v1.5m0 15V21m-9-1.5h10.5a2.25 2.25 0 0 0 2.25-2.25V6.75a2.25 2.25 0 0 0-2.25-2.25H6.75A2.25 2.25 0 0 0 4.5 6.75v10.5a2.25 2.25 0 0 0 2.25 2.25Zm.75-12h9v9h-9v-9Z"
              />
            </svg>
          </div>
          <div>
            <p className="text-sm text-text-200 leading-relaxed">
              <span className="font-medium">엔진 특성:</span>{" "}
              {selectedEngine === "Basic"
                ? "숫자 표기·경제 용어·전문 용어 중심 교열"
                : "인용문·문체 일관성·문단 연결성 중심 교열"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BasicNProGuideSection;
