import React from "react";

const C1C2GuideSection = ({ selectedEngine = "C1" }) => {
  return (
    <div className="w-full max-w-4xl pt-6">
      <div className="mb-4">
        <h2 className="text-xl font-semibold text-text-100 mb-2">
          {selectedEngine === "C1" ? "속전속결 퇴고" : "구조분석 퇴고"}
        </h2>
        <p className="text-sm text-text-300">
          {selectedEngine === "C1"
            ? "1,000자 미만의 기사를 빠르게 퇴고합니다. 첫 문장부터 클릭을 유도하는 기사로 변환합니다."
            : "1,000자 이상의 긴 기사를 끝까지 읽히는 구조로 재설계합니다. 극적인 서사와 긴장감 유지에 최적화되어 있습니다."}
        </p>
      </div>

      <div className="space-y-4">
        <div
          className="flex items-start p-3 rounded-lg"
          style={{ backgroundColor: "hsl(var(--bg-200))" }}
        >
          <div className="mr-3 mt-1">
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
            <p className="text-sm text-text-200">
              <span className="font-medium">시작하는 방법:</span> 입력창에 기사 초고를 붙여넣고 전송 버튼을 클릭하세요
            </p>
          </div>
        </div>

        <div
          className="flex items-start p-3 rounded-lg"
          style={{ backgroundColor: "hsl(var(--bg-200))" }}
        >
          <div className="mr-3 mt-1">
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
            <p className="text-sm text-text-200">
              <span className="font-medium">권장 사용:</span>
              {selectedEngine === "C1"
                ? "1,000자 미만 기사, 빠른 퇴고, 첫 문장 최적화"
                : "1,000자 이상 기사, 구조 재설계, 끝까지 읽히는 서사"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default C1C2GuideSection;
