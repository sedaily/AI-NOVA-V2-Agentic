import { useState, useEffect, useRef, useCallback } from 'react';

export const useSmoothStreaming = (options = {}) => {
  const {
    charDelay = 8,
    minDelay = 2,
    maxDelay = 20,
    smoothness = 0.95,
  } = options;

  const [displayText, setDisplayText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);

  const fullTextRef = useRef('');
  const currentIndexRef = useRef(0);
  const animationFrameRef = useRef(null);
  const lastTimeRef = useRef(0);
  const velocityRef = useRef(1);

  const getCharDelay = useCallback((char, nextChar) => {
    if (['.', '!', '?'].includes(char) && nextChar === ' ') {
      return maxDelay * 2;
    }
    if ([',', '、', '·', ':', ';'].includes(char)) {
      return maxDelay * 1.2;
    }
    if (char === ' ') {
      return minDelay * 1.5;
    }
    if (/[0-9\-\+\=\(\)]/.test(char)) {
      return charDelay * 0.7;
    }
    const variation = 0.8 + Math.random() * 0.4;
    return charDelay * variation;
  }, [charDelay, minDelay, maxDelay]);

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

      const targetVelocity = 1000 / delay;
      velocityRef.current = velocityRef.current * smoothness + targetVelocity * (1 - smoothness);

      const effectiveDelay = 1000 / velocityRef.current;

      if (deltaTime >= effectiveDelay) {
        currentIndexRef.current++;
        const newText = fullTextRef.current.substring(0, currentIndexRef.current);
        setDisplayText(newText);
        lastTimeRef.current = timestamp;
      }

      animationFrameRef.current = requestAnimationFrame(animate);
    } else {
      setIsStreaming(false);
      lastTimeRef.current = 0;
    }
  }, [getCharDelay, smoothness]);

  const startStreaming = useCallback((text) => {
    if (!text) return;
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    fullTextRef.current = text;
    currentIndexRef.current = 0;
    velocityRef.current = 1;
    lastTimeRef.current = 0;
    setDisplayText('');
    setIsStreaming(true);
    animationFrameRef.current = requestAnimationFrame(animate);
  }, [animate]);

  const appendText = useCallback((chunk) => {
    if (!chunk) return;
    fullTextRef.current += chunk;
    if (!isStreaming && fullTextRef.current.length > 0) {
      setIsStreaming(true);
      animationFrameRef.current = requestAnimationFrame(animate);
    }
  }, [isStreaming, animate]);

  const finish = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    setDisplayText(fullTextRef.current);
    currentIndexRef.current = fullTextRef.current.length;
    setIsStreaming(false);
  }, []);

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
