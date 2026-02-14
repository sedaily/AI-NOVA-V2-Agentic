import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Gemini 스타일의 초부드러운 스트리밍 훅
 * - 글자 단위 스트리밍
 * - 자연스러운 속도 변화
 * - CSS 트랜지션 활용
 */
export const useSmoothStreaming = (options = {}) => {
  const {
    charDelay = 8,           // 글자 간 기본 딜레이 (ms) - 적당한 타이핑 속도
    minDelay = 2,            // 최소 딜레이 - 빠른 부분
    maxDelay = 20,           // 최대 딜레이 (구두점 등) - 자연스러운 멈춤
    smoothness = 0.95,       // 부드러움 정도 (0-1) - 자연스러운 변화
  } = options;

  const [displayText, setDisplayText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  
  const fullTextRef = useRef('');
  const currentIndexRef = useRef(0);
  const animationFrameRef = useRef(null);
  const lastTimeRef = useRef(0);
  const velocityRef = useRef(1);

  // 글자별 딜레이 계산 (더 최적화)
  const getCharDelay = useCallback((char, nextChar) => {
    // 마침표, 느낌표, 물음표 다음이면 긴 멈춤
    if (['.', '!', '?'].includes(char) && nextChar === ' ') {
      return maxDelay * 2; // 문장 끝에서 더 긴 멈춤
    }
    
    // 일반 구두점 (쉼표, 가운뎃점 등)
    if ([',', '、', '·', ':', ';'].includes(char)) {
      return maxDelay * 1.2;
    }
    
    // 공백은 짧게
    if (char === ' ') {
      return minDelay * 1.5;
    }
    
    // 숫자나 특수문자는 약간 빠르게
    if (/[0-9\-\+\=\(\)]/.test(char)) {
      return charDelay * 0.7;
    }
    
    // 한글/영어 일반 글자 - 약간의 랜덤성 추가
    const variation = 0.8 + Math.random() * 0.4; // 0.8 ~ 1.2 배 변화
    return charDelay * variation;
  }, [charDelay, minDelay, maxDelay]);

  // 부드러운 애니메이션 루프
  const animate = useCallback((timestamp) => {
    if (!lastTimeRef.current) {
      lastTimeRef.current = timestamp;
    }

    const deltaTime = timestamp - lastTimeRef.current;
    const targetLength = fullTextRef.current.length;
    
    if (currentIndexRef.current < targetLength) {
      const currentChar = fullTextRef.current[currentIndexRef.current];
      const nextChar = fullTextRef.current[currentIndexRef.current + 1];
      const delay = getCharDelay(currentChar, nextChar);
      
      // 속도 스무딩
      const targetVelocity = 1000 / delay;
      velocityRef.current = velocityRef.current * smoothness + targetVelocity * (1 - smoothness);
      
      const effectiveDelay = 1000 / velocityRef.current;
      
      if (deltaTime >= effectiveDelay) {
        // 다음 글자 추가
        currentIndexRef.current++;
        const newText = fullTextRef.current.substring(0, currentIndexRef.current);
        
        setDisplayText(newText);
        lastTimeRef.current = timestamp;
      }
      
      animationFrameRef.current = requestAnimationFrame(animate);
    } else {
      // 스트리밍 완료
      setIsStreaming(false);
      lastTimeRef.current = 0;
    }
  }, [getCharDelay, smoothness]);

  // 텍스트 설정 및 스트리밍 시작
  const startStreaming = useCallback((text) => {
    if (!text) return;
    
    // 기존 애니메이션 중지
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    
    // 새로운 텍스트로 시작
    fullTextRef.current = text;
    currentIndexRef.current = 0;
    velocityRef.current = 1;
    lastTimeRef.current = 0;
    setDisplayText('');
    setIsStreaming(true);
    
    // 애니메이션 시작
    animationFrameRef.current = requestAnimationFrame(animate);
  }, [animate]);

  // 텍스트 추가 (증분 스트리밍)
  const appendText = useCallback((chunk) => {
    if (!chunk) return;
    
    fullTextRef.current += chunk;
    
    // 스트리밍 중이 아니면 시작
    if (!isStreaming && fullTextRef.current.length > 0) {
      setIsStreaming(true);
      animationFrameRef.current = requestAnimationFrame(animate);
    }
  }, [isStreaming, animate]);

  // 즉시 완료
  const finish = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    
    setDisplayText(fullTextRef.current);
    currentIndexRef.current = fullTextRef.current.length;
    setIsStreaming(false);
  }, []);

  // 리셋
  const reset = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    
    fullTextRef.current = '';
    currentIndexRef.current = 0;
    velocityRef.current = 1;
    lastTimeRef.current = 0;
    setDisplayText('');
    setIsStreaming(false);
  }, []);

  // 클린업
  useEffect(() => {
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  return {
    displayText,
    isStreaming,
    startStreaming,
    appendText,
    finish,
    reset,
  };
};