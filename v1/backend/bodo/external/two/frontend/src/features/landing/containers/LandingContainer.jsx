import React from 'react';
import LandingPresenter from '../presenters/LandingPresenter';
import { useLanding } from '../hooks/useLanding';

const LandingContainer = ({ onSelectEngine, userRole, onLogout, onLogin }) => {
  console.log('🔍 LandingContainer props:', { onSelectEngine, userRole, onLogout, onLogin });
  const {
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
  } = useLanding();

  return (
    <LandingPresenter
      // Data
      isVisible={isVisible}
      selectedEngine={selectedEngine}
      articleInput={articleInput}
      showArticleInput={showArticleInput}
      stats={stats}
      engines={engines}
      features={features}
      userRole={userRole}
      
      // Actions
      onEngineSelect={(engine) => handleEngineSelect(engine, onSelectEngine)}
      onArticleInputChange={setArticleInput}
      onProceedWithArticle={() => handleProceedWithArticle(onSelectEngine)}
      onCancelArticleInput={handleCancelArticleInput}
      onLogout={onLogout}
      onLogin={onLogin}
    />
  );
};

export default LandingContainer;