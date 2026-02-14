// API 설정
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
export const WS_URL = import.meta.env.VITE_WS_URL || '';

// 환경 설정
export const IS_DEVELOPMENT = import.meta.env.DEV;
export const IS_PRODUCTION = import.meta.env.PROD;

// 기타 설정
export const DEFAULT_ENGINE = 'Basic';
export const STORAGE_PREFIX = 'sedaily_';

export default {
  API_BASE_URL,
  WS_URL,
  IS_DEVELOPMENT,
  IS_PRODUCTION,
  DEFAULT_ENGINE,
  STORAGE_PREFIX
};