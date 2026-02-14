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

/**
 * 크레딧 전용 애니메이션 컴포넌트
 * 더 화려한 효과와 잔액 감소 시 특별 효과
 */
export const AnimatedCredits = ({
  value,
  className = "",
  size = "default", // "small" | "default" | "large"
}) => {
  const [prevValue, setPrevValue] = useState(value);
  const [isDecreasing, setIsDecreasing] = useState(false);

  useEffect(() => {
    if (value < prevValue) {
      setIsDecreasing(true);
      setTimeout(() => setIsDecreasing(false), 600);
    }
    setPrevValue(value);
  }, [value, prevValue]);

  const sizeClasses = {
    small: "text-xs",
    default: "text-sm",
    large: "text-base",
  };

  return (
    <motion.div
      className={`inline-flex items-center gap-1 ${sizeClasses[size]} ${className}`}
      animate={isDecreasing ? { scale: [1, 0.95, 1.02, 1] } : {}}
      transition={{ duration: 0.3 }}
    >
      {/* 코인 아이콘 */}
      <motion.span
        animate={isDecreasing ? { rotate: [0, -10, 10, 0] } : {}}
        transition={{ duration: 0.3 }}
        className="text-yellow-500"
      >
        💳
      </motion.span>

      {/* 숫자 */}
      <AnimatedNumber
        value={value}
        suffix=" NC"
        className="font-bold"
        showChange={true}
      />
    </motion.div>
  );
};

/**
 * 슬롯머신 스타일 숫자 애니메이션
 * 각 자릿수가 위아래로 굴러가는 효과
 */
export const SlotMachineNumber = ({
  value,
  className = "",
  digitClassName = "",
}) => {
  const formattedValue = Math.floor(value).toLocaleString("ko-KR");
  const digits = formattedValue.split("");

  return (
    <span className={`inline-flex overflow-hidden ${className}`}>
      {digits.map((digit, index) => (
        <span
          key={index}
          className={`inline-block overflow-hidden h-[1.2em] ${digitClassName}`}
        >
          {digit === "," || digit === "." ? (
            <span>{digit}</span>
          ) : (
            <motion.span
              key={`${index}-${digit}`}
              initial={{ y: "100%" }}
              animate={{ y: "0%" }}
              transition={{
                type: "spring",
                stiffness: 200,
                damping: 20,
                delay: index * 0.05,
              }}
              className="inline-block"
            >
              {digit}
            </motion.span>
          )}
        </span>
      ))}
    </span>
  );
};

export default AnimatedNumber;
