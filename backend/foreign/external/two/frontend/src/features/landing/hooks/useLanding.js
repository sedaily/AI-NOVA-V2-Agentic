import { useState, useEffect } from 'react';

export const useLanding = () => {
  const [isVisible, setIsVisible] = useState(false);
  const [selectedEngine, setSelectedEngine] = useState(null);
  const [articleInput, setArticleInput] = useState('');
  const [showArticleInput, setShowArticleInput] = useState(false);

  // 애니메이션을 위한 가시성 설정
  useEffect(() => {
    setIsVisible(true);
  }, []);

  // 엔진 선택 핸들러
  const handleEngineSelect = (engine, onSelectEngine) => {
    console.log('🎯 useLanding handleEngineSelect called:', engine);
    setSelectedEngine(engine);
    // 바로 엔진 선택 콜백 호출하여 리다이렉션
    if (onSelectEngine) {
      console.log('✅ Calling onSelectEngine with:', engine);
      onSelectEngine(engine);
    } else {
      console.log('❌ onSelectEngine is not provided');
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
    setArticleInput('');
    setSelectedEngine(null);
  };

  // 통계 데이터
  const stats = [
    { value: '10분', label: '평균 작성 시간' },
    { value: '95%', label: '만족도' },
    { value: '7종', label: '외신기사 스타일' },
    { value: '24/7', label: '상시 이용' }
  ];

  // 엔진 데이터
  const engines = [
    {
      id: '11',
      name: '영어 외신기사 엔진',
      subtitle: '전문적인 영어 기사',
      description: '영미권 언론 스타일의 고품질 영어 기사',
      features: [
        '초고속 처리 (1-3초)',
        '높은 정확도',
        '다양한 스타일 지원',
        '실시간 최적화'
      ],
      color: 'from-blue-500 to-purple-600',
      icon: 'Zap'
    },
    {
      id: '22',
      name: '일본어 외신기사 엔진',
      subtitle: '전문적인 일본어 기사',
      description: '일본 언론 스타일의 고품질 일본어 기사',
      features: [
        '고품질 결과물',
        '창의적 표현',
        '문맥 이해 강화',
        '감성적 표현 강화'
      ],
      color: 'from-purple-500 to-pink-600',
      icon: 'Sparkles'
    }
  ];

  // 특징 데이터
  const features = [
    {
      icon: 'TrendingUp',
      title: '실시간 트렌드 반영',
      description: '최신 이슈를 반영한 외신기사 작성'
    },
    {
      icon: 'Users',
      title: '독자 맞춤형',
      description: '타겟 독자층에 최적화된 외신기사'
    },
    {
      icon: 'Shield',
      title: '검증된 품질',
      description: '전문 기자들의 노하우로 학습된 AI'
    }
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
    handleCancelArticleInput
  };
};