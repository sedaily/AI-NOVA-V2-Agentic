// Column Service Configuration
export const SERVICE_TYPE = 'column';

// API Endpoints (from .env)
export const API_BASE_URL = import.meta.env.VITE_API_URL;
export const WS_URL = import.meta.env.VITE_WEBSOCKET_URL;
export const PROMPT_API_URL = import.meta.env.VITE_PROMPT_API_URL;
export const USAGE_API_URL = import.meta.env.VITE_USAGE_API_URL;
export const CONVERSATION_API_URL = import.meta.env.VITE_CONVERSATION_API_URL;

// Service Configuration
export const DEFAULT_ENGINE = 'C1'; // Column engine 1
export const AVAILABLE_ENGINES = ['C1', 'C2', 'C3'];

// Engine Display Names
export const ENGINE_NAMES = {
  C1: '칼럼 기본형',
  C2: '오피니언 칼럼형',
  C3: '경제 분석 칼럼형'
};

// Engine Descriptions
export const ENGINE_DESCRIPTIONS = {
  C1: '전문적이고 균형잡힌 칼럼을 작성합니다',
  C2: '독창적인 시각과 날카로운 분석을 제공합니다',
  C3: '경제 데이터와 시장 분석 중심의 칼럼을 작성합니다'
};

// Service Texts
export const SERVICE_TEXTS = {
  mainTitle: '전문 칼럼 작성 서비스',
  subTitle: 'AI가 도와주는 고품질 칼럼 작성',
  inputPlaceholder: '칼럼 주제나 내용을 입력하세요...',
  generateButton: '칼럼 생성',
  features: {
    title: '칼럼 작성 기능',
    items: [
      '전문적인 칼럼 구조 생성',
      '다양한 관점 제시',
      '데이터 기반 분석',
      '논리적 전개와 결론'
    ]
  }
};

// Usage Limits Configuration
export const USAGE_LIMITS = {
  free: {
    C1: { daily: 5, monthly: 100 },
    C2: { daily: 3, monthly: 50 },
    C3: { daily: 2, monthly: 30 }
  },
  pro: {
    C1: { daily: 50, monthly: 1500 },
    C2: { daily: 30, monthly: 900 },
    C3: { daily: 20, monthly: 600 }
  },
  enterprise: {
    C1: { daily: -1, monthly: -1 }, // unlimited
    C2: { daily: -1, monthly: -1 },
    C3: { daily: -1, monthly: -1 }
  }
};

// AWS Configuration
export const AWS_REGION = import.meta.env.VITE_AWS_REGION || 'us-east-1';
export const COGNITO_USER_POOL_ID = import.meta.env.VITE_COGNITO_USER_POOL_ID;
export const COGNITO_CLIENT_ID = import.meta.env.VITE_COGNITO_CLIENT_ID;

export default {
  SERVICE_TYPE,
  DEFAULT_ENGINE,
  AVAILABLE_ENGINES,
  ENGINE_NAMES,
  ENGINE_DESCRIPTIONS,
  SERVICE_TEXTS,
  USAGE_LIMITS
};