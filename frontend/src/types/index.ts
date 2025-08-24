// Re-export all types from individual modules
export * from './auth';
export * from './credentials';
export * from './apiKeys';
export * from './usage';
export * from './api';
export * from './ui';
export * from './store';

// Common utility types
export type Nullable<T> = T | null;
export type Optional<T> = T | undefined;
export type Maybe<T> = T | null | undefined;

// API Response wrapper
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
  };
}

// Generic pagination
export interface PaginationParams {
  page?: number;
  limit?: number;
  search?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

// File upload types
export interface FileUpload {
  file: File;
  preview?: string;
  progress?: number;
  status?: 'pending' | 'uploading' | 'success' | 'error';
  error?: string;
}

// Theme types
export type Theme = 'light' | 'dark' | 'system';

// Loading states
export type LoadingState = 'idle' | 'loading' | 'succeeded' | 'failed';

// Form validation
export interface ValidationError {
  field: string;
  message: string;
}

// Environment configuration
export interface AppConfig {
  apiBaseUrl: string;
  apiVersion: string;
  appName: string;
  appVersion: string;
  enableDarkMode: boolean;
  enableAnalytics: boolean;
  enableDebug: boolean;
  maxFileSize: number;
  allowedFileTypes: string[];
  defaultAiProvider: string;
  enableAiFallback: boolean;
  defaultTheme: Theme;
  enableAnimations: boolean;
  toastDuration: number;
}