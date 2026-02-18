import { useState, useCallback } from "react";

/**
 * Custom hook for managing pipeline state
 * Can be used for more complex state management scenarios
 */
export const usePipeline = () => {
  const [currentPhase, setCurrentPhase] = useState(0);
  const [pipelineData, setPipelineData] = useState({
    source: null,
    angle: null,
    draft: null,
    proofread: null,
    revised: null,
    title: null,
  });

  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);

  const goToPhase = useCallback((phase) => {
    if (phase >= 0 && phase <= 5) {
      setCurrentPhase(phase);
    }
  }, []);

  const nextPhase = useCallback(() => {
    setCurrentPhase((prev) => Math.min(prev + 1, 5));
  }, []);

  const prevPhase = useCallback(() => {
    setCurrentPhase((prev) => Math.max(prev - 1, 0));
  }, []);

  const updateData = useCallback((key, value) => {
    setPipelineData((prev) => ({
      ...prev,
      [key]: value,
    }));
  }, []);

  const reset = useCallback(() => {
    setCurrentPhase(0);
    setPipelineData({
      source: null,
      angle: null,
      draft: null,
      proofread: null,
      revised: null,
      title: null,
    });
    setError(null);
  }, []);

  return {
    // State
    currentPhase,
    pipelineData,
    isProcessing,
    error,

    // Actions
    goToPhase,
    nextPhase,
    prevPhase,
    updateData,
    setIsProcessing,
    setError,
    reset,
  };
};

export default usePipeline;
