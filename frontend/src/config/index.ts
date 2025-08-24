// Application configuration
import type { Theme } from '../types/ui';

// Environment variables with defaults
export const ENV = {
  NODE_ENV: import.meta.env.MODE || 'development',
  API_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  WS_URL: import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/v1/ws',
  APP_NAME: import.meta.env.VITE_APP_NAME || 'Seele INE',
  APP_VERSION: import.meta.env.VITE_APP_VERSION || '1.0.0',
  APP_DESCRIPTION: import.meta.env.VITE_APP_DESCRIPTION || 'Sistema de procesamiento de credenciales INE con IA',
  SENTRY_DSN: import.meta.env.VITE_SENTRY_DSN,
  GOOGLE_ANALYTICS_ID: import.meta.env.VITE_GA_ID,
  HOTJAR_ID: import.meta.env.VITE_HOTJAR_ID,
} as const;

// API Configuration
export const API_CONFIG = {
  BASE_URL: ENV.API_URL,
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
  ENDPOINTS: {
    AUTH: {
      LOGIN: '/auth/login',
      REGISTER: '/auth/register',
      REFRESH: '/auth/refresh',
      LOGOUT: '/auth/logout',
      PROFILE: '/auth/profile',
      CHANGE_PASSWORD: '/auth/change-password',
      FORGOT_PASSWORD: '/auth/forgot-password',
      RESET_PASSWORD: '/auth/reset-password',
      VERIFY_EMAIL: '/auth/verify-email',
      RESEND_VERIFICATION: '/auth/resend-verification',
    },
    CREDENTIALS: {
      UPLOAD: '/credentials/upload',
      LIST: '/credentials',
      DETAIL: '/credentials/:id',
      PROCESS: '/credentials/:id/process',
      DELETE: '/credentials/:id',
      DOWNLOAD: '/credentials/:id/download',
      HISTORY: '/credentials/:id/history',
    },
    API_KEYS: {
      LIST: '/api-keys',
      CREATE: '/api-keys',
      UPDATE: '/api-keys/:id',
      DELETE: '/api-keys/:id',
      REGENERATE: '/api-keys/:id/regenerate',
    },
    USAGE: {
      CURRENT: '/usage/current',
      HISTORY: '/usage/history',
      COSTS: '/usage/costs',
      TRACK: '/usage/track',
      EXPORT: '/usage/export',
    },
    PERMISSIONS: {
      USER: '/permissions/user',
      ROLES: '/permissions/roles',
      LIST: '/permissions',
    },
    SYSTEM: {
      HEALTH: '/health',
      VERSION: '/version',
      PROVIDERS: '/providers',
    },
  },
} as const;

// WebSocket Configuration
export const WS_CONFIG = {
  URL: ENV.WS_URL,
  RECONNECT_INTERVAL: 5000,
  MAX_RECONNECT_ATTEMPTS: 10,
  HEARTBEAT_INTERVAL: 30000,
  EVENTS: {
    CONNECT: 'connect',
    DISCONNECT: 'disconnect',
    ERROR: 'error',
    CREDENTIAL_PROCESSING: 'credential_processing',
    CREDENTIAL_COMPLETED: 'credential_completed',
    CREDENTIAL_FAILED: 'credential_failed',
    USAGE_UPDATE: 'usage_update',
    NOTIFICATION: 'notification',
  },
} as const;

// Authentication Configuration
export const AUTH_CONFIG = {
  TOKEN_STORAGE_KEY: 'seele_access_token',
  REFRESH_TOKEN_STORAGE_KEY: 'seele_refresh_token',
  USER_STORAGE_KEY: 'seele_user_profile',
  TOKEN_EXPIRATION_BUFFER: 300, // 5 minutes in seconds
  SESSION_WARNING_TIME: 300, // 5 minutes in seconds
  AUTO_REFRESH_ENABLED: true,
  REMEMBER_ME_DURATION: 30 * 24 * 60 * 60 * 1000, // 30 days in milliseconds
} as const;

// File Upload Configuration
export const FILE_CONFIG = {
  MAX_SIZE: 10 * 1024 * 1024, // 10MB
  ALLOWED_TYPES: [
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/webp',
    'application/pdf',
  ],
  ALLOWED_EXTENSIONS: ['.jpg', '.jpeg', '.png', '.webp', '.pdf'],
  CHUNK_SIZE: 1024 * 1024, // 1MB chunks for large file uploads
  CONCURRENT_UPLOADS: 3,
} as const;

// UI Configuration
export const UI_CONFIG = {
  THEME: {
    DEFAULT: ('light' as unknown) as Theme,
    STORAGE_KEY: 'seele_theme',
    SYSTEM_PREFERENCE_ENABLED: true,
  },
  LANGUAGE: {
    DEFAULT: 'es',
    STORAGE_KEY: 'seele_language',
    SUPPORTED: ['es', 'en'],
  },
  LAYOUT: {
    SIDEBAR_WIDTH: 280,
    SIDEBAR_COLLAPSED_WIDTH: 80,
    HEADER_HEIGHT: 64,
    FOOTER_HEIGHT: 48,
  },
  BREAKPOINTS: {
    xs: 0,
    sm: 640,
    md: 768,
    lg: 1024,
    xl: 1280,
    '2xl': 1536,
  },
  ANIMATIONS: {
    DURATION: {
      FAST: 150,
      NORMAL: 300,
      SLOW: 500,
    },
    EASING: {
      EASE_IN: 'cubic-bezier(0.4, 0, 1, 1)',
      EASE_OUT: 'cubic-bezier(0, 0, 0.2, 1)',
      EASE_IN_OUT: 'cubic-bezier(0.4, 0, 0.2, 1)',
    },
  },
  TOAST: {
    DURATION: 5000,
    MAX_TOASTS: 5,
    POSITION: 'top-right' as const,
  },
  MODAL: {
    BACKDROP_BLUR: true,
    CLOSE_ON_BACKDROP_CLICK: true,
    CLOSE_ON_ESCAPE: true,
  },
  PAGINATION: {
    DEFAULT_PAGE_SIZE: 20,
    PAGE_SIZE_OPTIONS: [10, 20, 50, 100],
    MAX_VISIBLE_PAGES: 7,
  },
} as const;

// Processing Configuration
export const PROCESSING_CONFIG = {
  POLLING_INTERVAL: 2000, // 2 seconds
  MAX_POLLING_ATTEMPTS: 300, // 10 minutes max
  SUPPORTED_PROVIDERS: [
    'openai',
    'deepseek',
    'gemini',
    'claude',
  ],
  EXTRACTION_METHODS: [
    'ocr',
    'qr',
    'hybrid',
  ],
  CREDENTIAL_TYPES: [
    'ine_front',
    'ine_back',
    'ine_both',
  ],
  STATUS_COLORS: {
    pending: '#f59e0b',
    processing: '#3b82f6',
    completed: '#10b981',
    failed: '#ef4444',
    cancelled: '#6b7280',
  },
} as const;

// Cache Configuration
export const CACHE_CONFIG = {
  DEFAULT_TTL: 5 * 60 * 1000, // 5 minutes
  USER_PROFILE_TTL: 30 * 60 * 1000, // 30 minutes
  API_KEYS_TTL: 10 * 60 * 1000, // 10 minutes
  USAGE_DATA_TTL: 2 * 60 * 1000, // 2 minutes
  PROVIDERS_TTL: 60 * 60 * 1000, // 1 hour
  MAX_CACHE_SIZE: 100, // Maximum number of cached items
  CLEANUP_INTERVAL: 10 * 60 * 1000, // 10 minutes
} as const;

// Error Configuration
export const ERROR_CONFIG = {
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
  SHOW_STACK_TRACE: ENV.NODE_ENV === 'development',
  LOG_ERRORS: true,
  REPORT_ERRORS: ENV.NODE_ENV === 'production',
  IGNORED_ERRORS: [
    'ChunkLoadError',
    'Loading chunk',
    'Network Error',
  ],
} as const;

// Analytics Configuration
export const ANALYTICS_CONFIG = {
  ENABLED: ENV.NODE_ENV === 'production',
  GOOGLE_ANALYTICS: {
    ID: ENV.GOOGLE_ANALYTICS_ID,
    ENABLED: !!ENV.GOOGLE_ANALYTICS_ID,
  },
  HOTJAR: {
    ID: ENV.HOTJAR_ID,
    ENABLED: !!ENV.HOTJAR_ID,
  },
  EVENTS: {
    PAGE_VIEW: 'page_view',
    USER_SIGNUP: 'user_signup',
    USER_LOGIN: 'user_login',
    CREDENTIAL_UPLOAD: 'credential_upload',
    CREDENTIAL_PROCESS: 'credential_process',
    API_KEY_CREATE: 'api_key_create',
    ERROR_OCCURRED: 'error_occurred',
  },
} as const;

// Feature Flags
export const FEATURE_FLAGS = {
  DARK_MODE: true,
  MULTI_LANGUAGE: true,
  REAL_TIME_UPDATES: true,
  ADVANCED_ANALYTICS: true,
  BULK_PROCESSING: true,
  API_KEY_MANAGEMENT: true,
  USAGE_TRACKING: true,
  EXPORT_DATA: true,
  NOTIFICATIONS: true,
  HELP_CHAT: false,
  BETA_FEATURES: ENV.NODE_ENV === 'development',
} as const;

// Security Configuration
export const SECURITY_CONFIG = {
  CSP: {
    ENABLED: ENV.NODE_ENV === 'production',
    REPORT_URI: '/api/csp-report',
  },
  HTTPS: {
    ENFORCE: ENV.NODE_ENV === 'production',
    HSTS_MAX_AGE: 31536000, // 1 year
  },
  CORS: {
    ALLOWED_ORIGINS: [
      'http://localhost:3000',
      'http://localhost:5173',
      'https://seele-ine.com',
    ],
  },
  RATE_LIMITING: {
    ENABLED: true,
    REQUESTS_PER_MINUTE: 60,
    BURST_LIMIT: 10,
  },
} as const;

// Development Configuration
export const DEV_CONFIG = {
  MOCK_API: false,
  SHOW_REDUX_DEVTOOLS: ENV.NODE_ENV === 'development',
  SHOW_PERFORMANCE_METRICS: ENV.NODE_ENV === 'development',
  ENABLE_HOT_RELOAD: ENV.NODE_ENV === 'development',
  LOG_LEVEL: ENV.NODE_ENV === 'development' ? 'debug' : 'error',
} as const;

// Application Metadata
export const APP_METADATA = {
  NAME: ENV.APP_NAME,
  VERSION: ENV.APP_VERSION,
  DESCRIPTION: ENV.APP_DESCRIPTION,
  AUTHOR: 'Seele Team',
  HOMEPAGE: 'https://seele-ine.com',
  REPOSITORY: 'https://github.com/seele-team/seele-ine',
  SUPPORT_EMAIL: 'support@seele-ine.com',
  PRIVACY_POLICY: 'https://seele-ine.com/privacy',
  TERMS_OF_SERVICE: 'https://seele-ine.com/terms',
  LICENSE: 'MIT',
} as const;

// Export configuration object
export const config = {
  env: ENV,
  api: API_CONFIG,
  ws: WS_CONFIG,
  auth: AUTH_CONFIG,
  file: FILE_CONFIG,
  ui: UI_CONFIG,
  processing: PROCESSING_CONFIG,
  cache: CACHE_CONFIG,
  error: ERROR_CONFIG,
  analytics: ANALYTICS_CONFIG,
  features: FEATURE_FLAGS,
  security: SECURITY_CONFIG,
  dev: DEV_CONFIG,
  app: APP_METADATA,
} as const;

// Type exports
export type Config = typeof config;
export type Environment = typeof ENV.NODE_ENV;
export type SupportedLanguage = typeof UI_CONFIG.LANGUAGE.SUPPORTED[number];
export type ProcessingProvider = typeof PROCESSING_CONFIG.SUPPORTED_PROVIDERS[number];
export type ExtractionMethod = typeof PROCESSING_CONFIG.EXTRACTION_METHODS[number];
export type CredentialType = typeof PROCESSING_CONFIG.CREDENTIAL_TYPES[number];
export type AnalyticsEvent = typeof ANALYTICS_CONFIG.EVENTS[keyof typeof ANALYTICS_CONFIG.EVENTS];

// Utility functions
export const configUtils = {
  // Check if feature is enabled
  isFeatureEnabled: (feature: keyof typeof FEATURE_FLAGS): boolean => {
    return FEATURE_FLAGS[feature];
  },

  // Get API endpoint with parameters
  getApiEndpoint: (endpoint: string, params: Record<string, string> = {}): string => {
    let url = endpoint;
    Object.entries(params).forEach(([key, value]) => {
      url = url.replace(`:${key}`, value);
    });
    return url;
  },

  // Check if environment is development
  isDevelopment: (): boolean => {
    return ENV.NODE_ENV === 'development';
  },

  // Check if environment is production
  isProduction: (): boolean => {
    return ENV.NODE_ENV === 'production';
  },

  // Get full API URL
  getFullApiUrl: (endpoint: string): string => {
    return `${API_CONFIG.BASE_URL}${endpoint}`;
  },

  // Get WebSocket URL
  getWebSocketUrl: (path: string = ''): string => {
    return `${WS_CONFIG.URL}${path}`;
  },

  // Validate file type
  isValidFileType: (file: File): boolean => {
    return FILE_CONFIG.ALLOWED_TYPES.includes(file.type as typeof FILE_CONFIG.ALLOWED_TYPES[number]);
  },

  // Validate file size
  isValidFileSize: (file: File): boolean => {
    return file.size <= FILE_CONFIG.MAX_SIZE;
  },

  // Get breakpoint value
  getBreakpoint: (breakpoint: keyof typeof UI_CONFIG.BREAKPOINTS): number => {
    return UI_CONFIG.BREAKPOINTS[breakpoint];
  },

  // Check if provider is supported
  isSupportedProvider: (provider: string): boolean => {
    return PROCESSING_CONFIG.SUPPORTED_PROVIDERS.includes(provider as ProcessingProvider);
  },

  // Get status color
  getStatusColor: (status: keyof typeof PROCESSING_CONFIG.STATUS_COLORS): string => {
    return PROCESSING_CONFIG.STATUS_COLORS[status];
  },

  // Get cache TTL for specific data type
  getCacheTTL: (dataType: string): number => {
    switch (dataType) {
      case 'user_profile':
        return CACHE_CONFIG.USER_PROFILE_TTL;
      case 'api_keys':
        return CACHE_CONFIG.API_KEYS_TTL;
      case 'usage_data':
        return CACHE_CONFIG.USAGE_DATA_TTL;
      case 'providers':
        return CACHE_CONFIG.PROVIDERS_TTL;
      default:
        return CACHE_CONFIG.DEFAULT_TTL;
    }
  },
};

export default config;