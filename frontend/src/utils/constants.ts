// API Constants
export const API_ENDPOINTS = {
  // Authentication
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    LOGOUT: '/auth/logout',
    REFRESH: '/auth/refresh',
    PROFILE: '/auth/me',
    FORGOT_PASSWORD: '/auth/password/reset',
    RESET_PASSWORD: '/auth/password/reset/confirm',
    VERIFY_EMAIL: '/auth/activate',
    CHANGE_PASSWORD: '/auth/password/change',
    RESEND_VERIFICATION: '/auth/resend-verification',
  },
  // API Keys
  API_KEYS: {
    LIST: '/api-keys',
    CREATE: '/api-keys',
    UPDATE: '/api-keys',
    DELETE: '/api-keys',
    REGENERATE: '/api-keys/regenerate',
  },
  // Credentials
  CREDENTIALS: {
    UPLOAD: '/credentials/upload',
    LIST: '/credentials',
    GET: '/credentials',
    DELETE: '/credentials',
    VALIDATE: '/credentials/validate',
    CLASSIFY: '/credentials/classify',
    EXTRACT_OCR: '/credentials/extract-ocr',
    EXTRACT_QR: '/credentials/extract-qr',
    PROCESS: '/credentials/process',
    RETRY: '/credentials/retry',
    HISTORY: '/credentials/history',
    STATS: '/credentials/stats',
  },
} as const;

// HTTP Status Codes
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  UNPROCESSABLE_ENTITY: 422,
  TOO_MANY_REQUESTS: 429,
  INTERNAL_SERVER_ERROR: 500,
  BAD_GATEWAY: 502,
  SERVICE_UNAVAILABLE: 503,
} as const;

// Local Storage Keys
export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'seele_access_token',
  REFRESH_TOKEN: 'seele_refresh_token',
  USER_PROFILE: 'seele_user_profile',
  THEME: 'seele_theme',
  LANGUAGE: 'seele_language',
  SIDEBAR_COLLAPSED: 'seele_sidebar_collapsed',
  RECENT_UPLOADS: 'seele_recent_uploads',
  SETTINGS: 'seele_settings',
  CACHE_PREFIX: 'seele_cache_',
  REDIRECT_URL: 'seele_redirect_url',
  OAUTH_STATE: 'seele_oauth_state',
  TOKEN_EXPIRATION: 'seele_token_expiration',
} as const;

// Theme Constants
export const THEMES = {
  LIGHT: 'light',
  DARK: 'dark',
  SYSTEM: 'system',
} as const;

// File Upload Constants
export const FILE_UPLOAD = {
  MAX_SIZE: 10 * 1024 * 1024, // 10MB
  ALLOWED_TYPES: [
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/webp',
    'image/gif',
    'application/pdf',
  ],
  ALLOWED_EXTENSIONS: ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.pdf'],
} as const;

// Credential Types
export const CREDENTIAL_TYPES = {
  INE_FRONT: 'ine_front',
  INE_BACK: 'ine_back',
  PASSPORT: 'passport',
  DRIVERS_LICENSE: 'drivers_license',
  VOTER_ID: 'voter_id',
  OTHER: 'other',
} as const;

// Processing Status
export const PROCESSING_STATUS = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled',
} as const;

// Extraction Methods
export const EXTRACTION_METHODS = {
  OCR: 'ocr',
  QR: 'qr',
  HYBRID: 'hybrid',
} as const;

// AI Providers
export const AI_PROVIDERS = {
  OPENAI: 'openai',
  DEEPSEEK: 'deepseek',
  GEMINI: 'gemini',
  CLAUDE: 'claude',
} as const;

// Toast Duration
export const TOAST_DURATION = {
  SHORT: 3000,
  MEDIUM: 5000,
  LONG: 8000,
  PERSISTENT: 0,
} as const;

// Animation Durations
export const ANIMATION_DURATION = {
  FAST: 150,
  NORMAL: 300,
  SLOW: 500,
} as const;

// Breakpoints (matching Tailwind CSS)
export const BREAKPOINTS = {
  SM: 640,
  MD: 768,
  LG: 1024,
  XL: 1280,
  '2XL': 1536,
} as const;

// Z-Index Layers
export const Z_INDEX = {
  DROPDOWN: 1000,
  STICKY: 1020,
  FIXED: 1030,
  MODAL_BACKDROP: 1040,
  MODAL: 1050,
  POPOVER: 1060,
  TOOLTIP: 1070,
  TOAST: 1080,
} as const;

// Form Validation
export const VALIDATION = {
  EMAIL_REGEX: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  PASSWORD_MIN_LENGTH: 8,
  PASSWORD_REGEX: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/,
  PHONE_REGEX: /^[+]?[1-9][\d]{0,15}$/,
  NAME_MIN_LENGTH: 2,
  NAME_MAX_LENGTH: 50,
} as const;

// Date Formats
export const DATE_FORMATS = {
  ISO: 'YYYY-MM-DDTHH:mm:ss.SSSZ',
  DATE: 'YYYY-MM-DD',
  TIME: 'HH:mm:ss',
  DATETIME: 'YYYY-MM-DD HH:mm:ss',
  DISPLAY_DATE: 'MMM DD, YYYY',
  DISPLAY_DATETIME: 'MMM DD, YYYY HH:mm',
  RELATIVE: 'relative',
} as const;

// Error Messages
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network error. Please check your connection.',
  UNAUTHORIZED: 'You are not authorized to perform this action.',
  FORBIDDEN: 'Access denied.',
  NOT_FOUND: 'The requested resource was not found.',
  VALIDATION_ERROR: 'Please check your input and try again.',
  SERVER_ERROR: 'An unexpected error occurred. Please try again later.',
  TIMEOUT: 'Request timed out. Please try again.',
  FILE_TOO_LARGE: 'File size exceeds the maximum allowed limit.',
  INVALID_FILE_TYPE: 'Invalid file type. Please select a supported file.',
  UPLOAD_FAILED: 'File upload failed. Please try again.',
  PROCESSING_FAILED: 'Processing failed. Please try again.',
} as const;

// Success Messages
export const SUCCESS_MESSAGES = {
  LOGIN_SUCCESS: 'Successfully logged in!',
  LOGOUT_SUCCESS: 'Successfully logged out!',
  REGISTER_SUCCESS: 'Account created successfully!',
  PROFILE_UPDATED: 'Profile updated successfully!',
  PASSWORD_CHANGED: 'Password changed successfully!',
  EMAIL_VERIFIED: 'Email verified successfully!',
  FILE_UPLOADED: 'File uploaded successfully!',
  PROCESSING_COMPLETE: 'Processing completed successfully!',
  SETTINGS_SAVED: 'Settings saved successfully!',
} as const;

// Loading Messages
export const LOADING_MESSAGES = {
  LOGGING_IN: 'Logging in...',
  REGISTERING: 'Creating account...',
  UPLOADING: 'Uploading file...',
  PROCESSING: 'Processing credential...',
  SAVING: 'Saving changes...',
  LOADING: 'Loading...',
  VALIDATING: 'Validating...',
  EXTRACTING: 'Extracting information...',
} as const;

// Pagination
export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 10,
  PAGE_SIZE_OPTIONS: [10, 20, 50, 100],
  MAX_PAGE_SIZE: 100,
} as const;

// Cache
export const CACHE = {
  DEFAULT_TTL: 5 * 60 * 1000, // 5 minutes
  LONG_TTL: 60 * 60 * 1000, // 1 hour
  SHORT_TTL: 60 * 1000, // 1 minute
} as const;

// WebSocket Events
export const WS_EVENTS = {
  CONNECT: 'connect',
  DISCONNECT: 'disconnect',
  ERROR: 'error',
  CREDENTIAL_UPDATE: 'credential_update',
  PROCESSING_STATUS: 'processing_status',
  NOTIFICATION: 'notification',
} as const;

// Feature Flags
export const FEATURES = {
  DARK_MODE: 'darkMode',
  ANALYTICS: 'analytics',
  DEBUG: 'debug',
  WEBSOCKETS: 'websockets',
  NOTIFICATIONS: 'notifications',
  FILE_PREVIEW: 'filePreview',
  BATCH_PROCESSING: 'batchProcessing',
} as const;

// Routes
export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  FORGOT_PASSWORD: '/forgot-password',
  RESET_PASSWORD: '/reset-password',
  VERIFY_EMAIL: '/verify-email',
  DASHBOARD: '/dashboard',
  CREDENTIALS: '/credentials',
  CREDENTIAL_DETAIL: '/credentials/:id',
  PROFILE: '/profile',
  SETTINGS: '/settings',
  API_KEYS: '/api-keys',
  HELP: '/help',
  PRIVACY: '/privacy',
  TERMS: '/terms',
} as const;

// External Links
export const EXTERNAL_LINKS = {
  DOCUMENTATION: 'https://docs.seele-ine.com',
  SUPPORT: 'https://support.seele-ine.com',
  GITHUB: 'https://github.com/seele-ine',
  PRIVACY_POLICY: 'https://seele-ine.com/privacy',
  TERMS_OF_SERVICE: 'https://seele-ine.com/terms',
} as const;

// Application Metadata
export const APP_METADATA = {
  NAME: 'Seele INE',
  DESCRIPTION: 'Advanced INE credential processing platform',
  VERSION: '1.0.0',
  AUTHOR: 'Seele Team',
  KEYWORDS: ['ine', 'credential', 'ocr', 'ai', 'processing'],
} as const;