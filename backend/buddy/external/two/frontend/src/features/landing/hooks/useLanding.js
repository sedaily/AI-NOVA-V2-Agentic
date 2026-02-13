import { useState, useEffect } from "react";

export const useLanding = () => {
  const [isVisible, setIsVisible] = useState(false);
  const [selectedEngine, setSelectedEngine] = useState(null);
  const [articleInput, setArticleInput] = useState("");
  const [showArticleInput, setShowArticleInput] = useState(false);

  // 애니메이션을 위한 가시성 설정
  useEffect(() => {
    setIsVisible(true);
  }, []);

  // 엔진 선택 핸들러
  const handleEngineSelect = (engine, onSelectEngine) => {
    console.log("🎯 useLanding handleEngineSelect called:", engine);
    setSelectedEngine(engine);
    // 바로 엔진 선택 콜백 호출하여 리다이렉션
    if (onSelectEngine) {
      console.log("✅ Calling onSelectEngine with:", engine);
      onSelectEngine(engine);
    } else {
      console.log("❌ onSelectEngine is not provided");
    }
  };

  // 기사와 함께 진행
  const handleProceedWithArticle = (onSelectEngine) => {
    if (selectedEngine && articleInput.trim()) {
      onSelectEngine(selectedEngine, articleInput.trim());
    } else if (selectedEngine) {
      onSelectEngine(selectedEngine);
    }
  };

  // 기사 입력 취소
  const handleCancelArticleInput = () => {
    setShowArticleInput(false);
    setArticleInput("");
    setSelectedEngine(null);
  };

  // 통계 데이터
  const stats = [
    { value: "30초", label: "초안 생성 시간" },
    { value: "100%", label: "투명성" },
    { value: "70-80%", label: "완성도" },
    { value: "24/7", label: "상시 이용" },
  ];

  // 엔진 데이터
  const engines = [
    {
      id: "11",
      name: "일보 버디",
      subtitle: "막연한 아이디어 → 데스크 OK 일보",
      description:
        '아이디어를 입력하세요. 막연해도 괜찮습니다.\n단어 하나, 메모, 보도자료, "오늘 뭐 쓰지?"... 모두 OK',
      features: [
        "막연한 아이템 → 구체적 일보로",
        "평범한 팩트 → 특별한 각도로",
        "혼자 고민 → 함께 브레인스토밍",
        "취재 막막 → 취재원 추천",
        "중복 불안 → 차별화 전략 제시",
        "데스크 걱정 → OK 받는 포인트",
        "매일 반복 → 매번 새로운 시각",
      ],
      color: "from-orange-500 to-amber-500",
      icon: "Sparkles",
    },
    {
      id: "22",
      name: "기사 버디",
      subtitle: "일보와 팩트 → 투명한 기사 초안",
      description:
        '일보와 취재 내용을 입력하세요. 부족해도 괜찮습니다.\n일보만, 팩트 추가, 보도자료, "첫 문장이 안 써져"... 모두 OK',
      features: [
        "빈 화면 → 3분 만에 초안",
        "첫 문장 막막 → 5가지 시작법",
        "팩트만 덩그러니 → 자연스러운 기사로",
        "AI 불안 → 투명한 출처 표시",
        "분량 고민 → 자동 조절",
        "시간 부족 → 긴급 모드 가동",
        "송고 불안 → 최종 체크까지",
      ],
      color: "from-blue-500 to-indigo-500",
      icon: "Zap",
    },
  ];

  // 특징 데이터
  const features = [
    {
      icon: "TrendingUp",
      title: "투명한 정보 구분",
      description: "확인 팩트, 추론 맥락, 가상 작성 100% 구분",
    },
    {
      icon: "Users",
      title: "오보 방지 시스템",
      description: "모든 가상 내용 [대괄호] 표시로 실수 방지",
    },
    {
      icon: "Shield",
      title: "서울경제 스타일",
      description: "경제지 특유의 간결하고 정확한 문체 자동 적용",
    },
  ];

  return {
    isVisible,
    selectedEngine,
    articleInput,
    showArticleInput,
    stats,
    engines,
    features,
    setArticleInput,
    handleEngineSelect,
    handleProceedWithArticle,
    handleCancelArticleInput,
  };
};
