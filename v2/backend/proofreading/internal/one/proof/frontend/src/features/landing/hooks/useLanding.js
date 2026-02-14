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

  // 통계 데이터 (사용하지 않음)
  const stats = [];

  // 엔진 데이터
  const engines = [
    {
      id: 'Basic',
      name: '비즈니스 모드',
      subtitle: '빠른 교열',
      description: '효율적이고 정확한 문서 교열',
      features: [
        '초고속 처리 (1-3초)',
        '맞춤법 및 문법 검사',
        '문체 일관성 확인',
        '실시간 최적화'
      ],
      color: 'from-blue-500 to-purple-600',
      icon: 'Zap'
    },
    {
      id: 'Pro',
      name: '종합 뉴스 모드',
      subtitle: '정밀 교열',
      description: '심층적이고 세밀한 문서 교정',
      features: [
        '고품질 교정 결과',
        '문맥 기반 교정',
        '전문 용어 검증',
        '스타일 가이드 적용'
      ],
      color: 'from-purple-500 to-pink-600',
      icon: 'Sparkles'
    }
  ];

  // 특징 데이터
  const features = [
    {
      icon: 'TrendingUp',
      title: '전문 교열 서비스',
      description: '언론사 수준의 전문 교정 제공'
    },
    {
      icon: 'Users',
      title: '맞춤형 교정',
      description: '문서 유형별 최적화된 교열'
    },
    {
      icon: 'Shield',
      title: '검증된 품질',
      description: '수만 건의 문서로 학습된 AI'
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