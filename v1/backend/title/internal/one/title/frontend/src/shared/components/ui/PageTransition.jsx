import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// Modern, subtle page variants with natural movement
const pageVariants = {
  initial: {
    opacity: 0,
  },
  in: {
    opacity: 1,
  },
  out: {
    opacity: 0,
  },
};

// Smooth cubic-bezier for natural feel
const pageTransition = {
  type: "tween",
  ease: [0.25, 0.1, 0.25, 1], // Smoother ease for natural motion
  duration: 0.08, // 매우 빠른 전환 (80ms)
};

// Fade-only variant for subtle transitions
const fadeVariants = {
  initial: {
    opacity: 0,
  },
  in: {
    opacity: 1,
  },
  out: {
    opacity: 0,
  },
};

const fadeTransition = {
  type: "tween",
  ease: "easeOut",
  duration: 0.1, // 더 빠른 페이드 (100ms)
};

// Slide variants for navigation transitions
const slideVariants = {
  initial: (direction) => ({
    x: direction > 0 ? 20 : -20,
    opacity: 0,
  }),
  in: {
    x: 0,
    opacity: 1,
  },
  out: (direction) => ({
    x: direction < 0 ? 20 : -20,
    opacity: 0,
  }),
};

const slideTransition = {
  type: "tween",
  ease: [0.25, 0.46, 0.45, 0.94], // easeOutQuad
  duration: 0.22,
};

// Scale fade for modal-like transitions
const scaleFadeVariants = {
  initial: {
    opacity: 0,
    scale: 0.95,
  },
  in: {
    opacity: 1,
    scale: 1,
  },
  out: {
    opacity: 0,
    scale: 0.95,
  },
};

const scaleFadeTransition = {
  type: "tween",
  ease: [0.16, 1, 0.3, 1], // Smooth elastic curve
  duration: 0.18,
};

export const PageTransition = ({ children, pageKey, variant = 'default' }) => {
  // Select animation based on variant
  let selectedVariants = pageVariants;
  let selectedTransition = pageTransition;

  switch (variant) {
    case 'fade':
      selectedVariants = fadeVariants;
      selectedTransition = fadeTransition;
      break;
    case 'slide':
      selectedVariants = slideVariants;
      selectedTransition = slideTransition;
      break;
    case 'scale':
      selectedVariants = scaleFadeVariants;
      selectedTransition = scaleFadeTransition;
      break;
    default:
      selectedVariants = pageVariants;
      selectedTransition = pageTransition;
  }

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={pageKey}
        initial="initial"
        animate="in"
        exit="out"
        variants={selectedVariants}
        transition={selectedTransition}
        style={{ 
          width: '100%', 
          height: '100%',
          willChange: 'transform, opacity, filter',
        }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
};

// Micro-interaction for content appearance
export const ContentFade = ({ children, delay = 0 }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        type: "tween",
        ease: [0.25, 0.1, 0.25, 1],
        duration: 0.35,
        delay,
      }}
    >
      {children}
    </motion.div>
  );
};

// Stagger children animation for lists
export const StaggerContainer = ({ children }) => {
  return (
    <motion.div
      initial="hidden"
      animate="show"
      variants={{
        hidden: { opacity: 0 },
        show: {
          opacity: 1,
          transition: {
            staggerChildren: 0.03,
          },
        },
      }}
    >
      {children}
    </motion.div>
  );
};

export const StaggerItem = ({ children }) => {
  return (
    <motion.div
      variants={{
        hidden: { opacity: 0, y: 8 },
        show: { 
          opacity: 1, 
          y: 0,
          transition: {
            type: "tween",
            ease: [0.25, 0.1, 0.25, 1],
            duration: 0.3,
          },
        },
      }}
    >
      {children}
    </motion.div>
  );
};

// Shared Element Transition with smoother spring
export const SharedElementTransition = ({ children, layoutId }) => {
  return (
    <motion.div
      layoutId={layoutId}
      transition={{
        type: "spring",
        stiffness: 200,
        damping: 25,
        mass: 0.8,
      }}
    >
      {children}
    </motion.div>
  );
};

// Smooth presence animation for appearing/disappearing elements
export const SmoothPresence = ({ children, isVisible }) => {
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ 
            opacity: 1, 
            height: 'auto',
            transition: {
              height: {
                type: "spring",
                stiffness: 300,
                damping: 30,
              },
              opacity: {
                duration: 0.2,
                ease: "easeOut",
              },
            },
          }}
          exit={{ 
            opacity: 0, 
            height: 0,
            transition: {
              height: {
                type: "spring",
                stiffness: 300,
                damping: 30,
              },
              opacity: {
                duration: 0.15,
                ease: "easeIn",
              },
            },
          }}
        >
          {children}
        </motion.div>
      )}
    </AnimatePresence>
  );
};