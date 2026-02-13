// API 설정 - TEM1 서비스
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://8u7vben959.execute-api.us-east-1.amazonaws.com/prod';
export const WS_URL = import.meta.env.VITE_WS_URL || 'wss://mq9a6wf3oj.execute-api.us-east-1.amazonaws.com/prod';

// 환경 설정
export const IS_DEVELOPMENT = import.meta.env.DEV;
export const IS_PRODUCTION = import.meta.env.PROD;

// 기타 설정
export const DEFAULT_ENGINE = '11';
export const STORAGE_PREFIX = 'tem_';

export default {
  API_BASE_URL,
  WS_URL,
  IS_DEVELOPMENT,
  IS_PRODUCTION,
  DEFAULT_ENGINE,
  STORAGE_PREFIX
};