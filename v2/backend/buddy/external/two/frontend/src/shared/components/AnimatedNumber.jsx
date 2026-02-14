import React, { useEffect, useRef, useState } from "react";
import { motion, useSpring, AnimatePresence } from "framer-motion";

/**
 * 숫자가 부드럽게 카운팅되는 애니메이션 컴포넌트
 * 은행 앱처럼 숫자가 자연스럽게 바뀌는 효과
 */
const AnimatedNumber = ({
  value,
  duration = 0.5,
  formatOptions = { minimumFractionDigits: 0, maximumFractionDigits: 0 },
  className = "",
  prefix = "",
  suffix = "",
  showChange = false,
}) => {
  const [displayValue, setDisplayValue] = useState(value);
  const prevValue = useRef(value);

  // Spring 애니메이션 - 더 부드럽게
  const spring = useSpring(value, {
    stiffness: 50,
    damping: 20,
  });

  // 값이 변경될 때
  useEffect(() => {
    spring.set(value);
    prevValue.current = value;
  }, [value, spring]);

  // Spring 값을 구독해서 displayValue 업데이트
  useEffect(() => {
    const unsubscribe = spring.on("change", (latest) => {
      setDisplayValue(latest);
    });
    return unsubscribe;
  }, [spring]);

  const formattedValue = displayValue.toLocaleString("ko-KR", formatOptions);

  return (
    <span className={`inline-flex items-center tabular-nums ${className}`}>
      {prefix && <span className="mr-0.5">{prefix}</span>}
      <span>{formattedValue}</span>
      {suffix && <span className="ml-0.5">{suffix}</span>}
    </span>
  );
};

export default AnimatedNumber;
