import type { AxiosRequestConfig, AxiosResponse } from 'axios';

// HTTP Methods
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

// API Error types
export interface ApiError {
  message: string;
  code?: string;
  status?: number;
  details?: Record<string, unknown>;
  timestamp?: string;
}

// Generic API response wrapper
export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  message?: string;
  errors?: Record<string, string[]>;
  meta?: {
    page?: number;
    limit?: number;
    total?: number;
    totalPages?: number;
    hasNext?: boolean;
    hasPrev?: boolean;
  };
}

// Paginated response
export interface PaginatedResponse<T> {
  items: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
}

// Request configuration
export interface ApiRequestConfig extends AxiosRequestConfig {
  skipAuth?: boolean;
  skipErrorHandling?: boolean;
  retries?: number;
  timeout?: number;
}

// Upload progress callback
export type UploadProgressCallback = (progress: number) => void;

// File upload configuration
export interface FileUploadConfig {
  onProgress?: UploadProgressCallback;
  maxSize?: number;
  allowedTypes?: string[];
  multiple?: boolean;
}

// API endpoints configuration
export interface ApiEndpoints {
  // Auth endpoints
  auth: {
    login: string;
    register: string;
    logout: string;
    refresh: string;
    forgotPassword: string;
    resetPassword: string;
    verifyEmail: string;
    changePassword: string;
    profile: string;
  };
  
  // API Key endpoints
  apiKeys: {
    list: string;
    create: string;
    update: (id: string) => string;
    delete: (id: string) => string;
    regenerate: (id: string) => string;
  };
  
  // Credential endpoints
  credentials: {
    upload: string;
    validate: string;
    classify: string;
    extractOcr: string;
    extractQr: string;
    process: string;
    history: string;
    stats: string;
    get: (id: string) => string;
    retry: (id: string) => string;
    delete: (id: string) => string;
  };
  
  // Health check
  health: string;
}

// Rate limiting information
export interface RateLimitInfo {
  limit: number;
  remaining: number;
  reset: number;
  retryAfter?: number;
}

// API client configuration
export interface ApiClientConfig {
  baseURL: string;
  timeout: number;
  retries: number;
  retryDelay: number;
  headers?: Record<string, string>;
}

// Request interceptor types
export type RequestInterceptor = (config: ApiRequestConfig) => ApiRequestConfig | Promise<ApiRequestConfig>;
export type ResponseInterceptor = (response: AxiosResponse) => AxiosResponse | Promise<AxiosResponse>;
export type ErrorInterceptor = (error: unknown) => Promise<unknown>;

// API service interface
export interface ApiService {
  get<T = unknown>(url: string, config?: ApiRequestConfig): Promise<T>;
  post<T = unknown>(url: string, data?: unknown, config?: ApiRequestConfig): Promise<T>;
  put<T = unknown>(url: string, data?: unknown, config?: ApiRequestConfig): Promise<T>;
  patch<T = unknown>(url: string, data?: unknown, config?: ApiRequestConfig): Promise<T>;
  delete<T = unknown>(url: string, config?: ApiRequestConfig): Promise<T>;
  upload<T = unknown>(url: string, file: File | FormData, config?: FileUploadConfig): Promise<T>;
}

// WebSocket types
export interface WebSocketMessage<T = unknown> {
  type: string;
  data: T;
  timestamp: string;
  id?: string;
}

export interface WebSocketConfig {
  url: string;
  protocols?: string[];
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export type WebSocketEventHandler<T = unknown> = (message: WebSocketMessage<T>) => void;

// Cache types
export interface CacheConfig {
  ttl: number; // Time to live in milliseconds
  maxSize?: number;
  strategy?: 'lru' | 'fifo';
}

export interface CacheEntry<T = unknown> {
  data: T;
  timestamp: number;
  ttl: number;
}

// API state for Redux
export interface ApiState {
  isOnline: boolean;
  rateLimits: Record<string, RateLimitInfo>;
  cache: Record<string, CacheEntry>;
  pendingRequests: Record<string, AbortController>;
}