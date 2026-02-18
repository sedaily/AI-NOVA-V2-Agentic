import React from "react";
import { motion } from "framer-motion";
import { Check, Home } from "lucide-react";

const PHASES = [
  { id: 1, label: "소재", step: "01" },
  { id: 2, label: "구성", step: "02" },
  { id: 3, label: "초안", step: "03" },
  { id: 4, label: "교열", step: "04" },
  { id: 5, label: "제목", step: "05" },
];

const PhaseIndicator = ({ currentPhase = 1, onPhaseClick, onHomeClick }) => {
  return (
    <div className="w-full px-6 py-5">
      <div className="max-w-4xl mx-auto flex items-start">
        {/* Logo as Home Button - Left, aligned with circles */}
        <motion.button
          onClick={onHomeClick}
          className="
            flex items-center gap-1.5 h-9
            text-text-300 hover:text-text-100
            transition-colors duration-200
          "
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          title="홈으로"
        >
          <Home className="w-4 h-4" />
          <span className="text-sm font-semibold tracking-tight">NOVA</span>
        </motion.button>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Phases Container - Center */}
        <div className="relative flex items-start justify-between" style={{ width: '420px' }}>
          {/* Background line */}
          <div
            className="absolute left-0 right-0 h-px bg-border-200/40"
            style={{ top: '18px', marginLeft: '18px', marginRight: '18px' }}
          />

          {PHASES.map((phase) => {
            const isActive = phase.id === currentPhase;
            const isCompleted = phase.id < currentPhase;
            const isClickable = phase.id <= currentPhase && onPhaseClick;

            return (
              <motion.button
                key={phase.id}
                onClick={() => isClickable && onPhaseClick(phase.id)}
                disabled={!isClickable}
                className={`
                  relative z-10 flex flex-col items-center gap-2
                  ${isClickable ? "cursor-pointer" : "cursor-default"}
                `}
                whileHover={isClickable ? { y: -2 } : {}}
              >
                {/* Circle */}
                <motion.div
                  className={`
                    w-9 h-9 rounded-full flex items-center justify-center
                    text-sm font-medium transition-all duration-300
                    ${isActive || isCompleted
                      ? "bg-text-100 text-bg-000"
                      : "bg-bg-200 text-text-400"
                    }
                  `}
                  initial={false}
                  animate={{ scale: isActive ? 1.05 : 1 }}
                  transition={{ duration: 0.2 }}
                >
                  {isCompleted ? (
                    <Check className="w-4 h-4" strokeWidth={2.5} />
                  ) : (
                    <span style={{ fontFamily: "system-ui" }}>{phase.step}</span>
                  )}
                </motion.div>

                {/* Label */}
                <span
                  className={`
                    text-xs transition-all duration-300
                    ${isActive
                      ? "text-text-100 font-medium"
                      : isCompleted
                        ? "text-text-200"
                        : "text-text-400/60"
                    }
                  `}
                >
                  {phase.label}
                </span>
              </motion.button>
            );
          })}

          {/* Progress line overlay */}
          <motion.div
            className="absolute left-0 h-px bg-text-100"
            style={{ top: '18px', marginLeft: '18px' }}
            initial={{ width: 0 }}
            animate={{
              width: `calc(${((currentPhase - 1) / (PHASES.length - 1)) * 100}% - 36px)`,
            }}
            transition={{ duration: 0.4, ease: "easeOut" }}
          />
        </div>

        {/* Spacer - to balance the logo on left */}
        <div className="flex-1" />
      </div>
    </div>
  );
};

export default PhaseIndicator;
