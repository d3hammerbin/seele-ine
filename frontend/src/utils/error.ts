// Error handling utilities
import React from 'react';

// Custom error classes
export class AppError extends Error {
  public readonly code: string;
  public readonly statusCode?: number;
  public readonly isOperational: boolean;
  public readonly timestamp: Date;
  public readonly context?: Record<string, unknown>;

  constructor(
    message: string,
    code: string = 'UNKNOWN_ERROR',
    statusCode?: number,
    isOperational: boolean = true,
    context?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'AppError';
    this.code = code;
    this.statusCode = statusCode;
    this.isOperational = isOperational;
    this.timestamp = new Date();
    this.context = context;

    // Maintains proper stack trace for where our error was thrown (only available on V8)
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, AppError);
    }
  }

  toJSON(): Record<string, unknown> {
    return {
      name: this.name,
      message: this.message,
      code: this.code,
      statusCode: this.statusCode,
      isOperational: this.isOperational,
      timestamp: this.timestamp.toISOString(),
      context: this.context,
      stack: this.stack,
    };
  }
}

export class ValidationError extends AppError {
  public readonly field?: string;
  public readonly value?: unknown;

  constructor(
    message: string,
    field?: string,
    value?: unknown,
    context?: Record<string, unknown>
  ) {
    super(message, 'VALIDATION_ERROR', 400, true, context);
    this.name = 'ValidationError';
    this.field = field;
    this.value = value;
  }

  toJSON(): Record<string, unknown> {
    return {
      ...super.toJSON(),
      field: this.field,
      value: this.value,
    };
  }
}

export class NetworkError extends AppError {
  public readonly url?: string;
  public readonly method?: string;
  public readonly response?: Response | unknown;

  constructor(
    message: string,
    statusCode?: number,
    url?: string,
    method?: string,
    response?: Response | unknown,
    context?: Record<string, unknown>
  ) {
    super(message, 'NETWORK_ERROR', statusCode, true, context);
    this.name = 'NetworkError';
    this.url = url;
    this.method = method;
    this.response = response;
  }

  toJSON(): Record<string, unknown> {
    return {
      ...super.toJSON(),
      url: this.url,
      method: this.method,
      response: this.response,
    };
  }
}

export class AuthenticationError extends AppError {
  constructor(message: string = 'Authentication required', context?: Record<string, unknown>) {
    super(message, 'AUTHENTICATION_ERROR', 401, true, context);
    this.name = 'AuthenticationError';
  }
}

export class AuthorizationError extends AppError {
  constructor(message: string = 'Access denied', context?: Record<string, unknown>) {
    super(message, 'AUTHORIZATION_ERROR', 403, true, context);
    this.name = 'AuthorizationError';
  }
}

export class NotFoundError extends AppError {
  public readonly resource?: string;
  public readonly id?: string | number;

  constructor(
    message: string = 'Resource not found',
    resource?: string,
    id?: string | number,
    context?: Record<string, unknown>
  ) {
    super(message, 'NOT_FOUND_ERROR', 404, true, context);
    this.name = 'NotFoundError';
    this.resource = resource;
    this.id = id;
  }

  toJSON(): Record<string, unknown> {
    return {
      ...super.toJSON(),
      resource: this.resource,
      id: this.id,
    };
  }
}

export class RateLimitError extends AppError {
  public readonly retryAfter?: number;

  constructor(
    message: string = 'Rate limit exceeded',
    retryAfter?: number,
    context?: Record<string, unknown>
  ) {
    super(message, 'RATE_LIMIT_ERROR', 429, true, context);
    this.name = 'RateLimitError';
    this.retryAfter = retryAfter;
  }

  toJSON(): Record<string, unknown> {
    return {
      ...super.toJSON(),
      retryAfter: this.retryAfter,
    };
  }
}

export class ConflictError extends AppError {
  public readonly resource?: string;

  constructor(
    message: string = 'Resource conflict',
    resource?: string,
    context?: Record<string, unknown>
  ) {
    super(message, 'CONFLICT_ERROR', 409, true, context);
    this.name = 'ConflictError';
    this.resource = resource;
  }

  toJSON(): Record<string, unknown> {
    return {
      ...super.toJSON(),
      resource: this.resource,
    };
  }
}

export class FileError extends AppError {
  public readonly fileName?: string;
  public readonly fileSize?: number;
  public readonly fileType?: string;

  constructor(
    message: string,
    fileName?: string,
    fileSize?: number,
    fileType?: string,
    context?: Record<string, unknown>
  ) {
    super(message, 'FILE_ERROR', 400, true, context);
    this.name = 'FileError';
    this.fileName = fileName;
    this.fileSize = fileSize;
    this.fileType = fileType;
  }

  toJSON(): Record<string, unknown> {
    return {
      ...super.toJSON(),
      fileName: this.fileName,
      fileSize: this.fileSize,
      fileType: this.fileType,
    };
  }
}

// Error type guards
export const isAppError = (error: unknown): error is AppError => {
  return error instanceof AppError;
};

export const isValidationError = (error: unknown): error is ValidationError => {
  return error instanceof ValidationError;
};

export const isNetworkError = (error: unknown): error is NetworkError => {
  return error instanceof NetworkError;
};

export const isAuthenticationError = (error: unknown): error is AuthenticationError => {
  return error instanceof AuthenticationError;
};

export const isAuthorizationError = (error: unknown): error is AuthorizationError => {
  return error instanceof AuthorizationError;
};

export const isNotFoundError = (error: unknown): error is NotFoundError => {
  return error instanceof NotFoundError;
};

export const isRateLimitError = (error: unknown): error is RateLimitError => {
  return error instanceof RateLimitError;
};

export const isConflictError = (error: unknown): error is ConflictError => {
  return error instanceof ConflictError;
};

export const isFileError = (error: unknown): error is FileError => {
  return error instanceof FileError;
};

// Error parsing utilities
export const parseError = (error: unknown): {
  message: string;
  code: string;
  statusCode?: number;
  details?: unknown;
} => {
  // Handle AppError instances
  if (isAppError(error)) {
    return {
      message: error.message,
      code: error.code,
      statusCode: error.statusCode,
      details: error.context,
    };
  }

  // Handle fetch/network errors
  if (error instanceof TypeError && error.message.includes('fetch')) {
    return {
      message: 'Network connection failed',
      code: 'NETWORK_ERROR',
      statusCode: 0,
    };
  }

  // Handle standard Error instances
  if (error instanceof Error) {
    return {
      message: error.message,
      code: 'UNKNOWN_ERROR',
    };
  }

  // Handle string errors
  if (typeof error === 'string') {
    return {
      message: error,
      code: 'UNKNOWN_ERROR',
    };
  }

  // Handle object errors (e.g., from API responses)
  if (typeof error === 'object' && error !== null) {
    const errorObj = error as Record<string, unknown>;
    
    // Helper function to safely extract string from potentially nested object
    const extractMessage = (obj: Record<string, unknown>): string => {
      // Try direct message property
      if (typeof obj.message === 'string' && obj.message.trim()) {
        return obj.message;
      }
      
      // Try error property
      if (typeof obj.error === 'string' && obj.error.trim()) {
        return obj.error;
      }
      
      // Try nested error.message
      if (typeof obj.error === 'object' && obj.error !== null) {
        const nestedError = obj.error as Record<string, unknown>;
        if (typeof nestedError.message === 'string' && nestedError.message.trim()) {
          return nestedError.message;
        }
      }
      
      // Try data.message
      if (typeof obj.data === 'object' && obj.data !== null) {
        const dataObj = obj.data as Record<string, unknown>;
        if (typeof dataObj.message === 'string' && dataObj.message.trim()) {
          return dataObj.message;
        }
      }
      
      // Try response.data.message (for axios errors)
      if (typeof obj.response === 'object' && obj.response !== null) {
        const responseObj = obj.response as Record<string, unknown>;
        if (typeof responseObj.data === 'object' && responseObj.data !== null) {
          const responseData = responseObj.data as Record<string, unknown>;
          if (typeof responseData.message === 'string' && responseData.message.trim()) {
            return responseData.message;
          }
        }
      }
      
      return 'An unknown error occurred';
    };
    
    return {
      message: extractMessage(errorObj),
      code: (typeof errorObj.code === 'string' ? errorObj.code : 
             typeof errorObj.type === 'string' ? errorObj.type : 'UNKNOWN_ERROR'),
      statusCode: (typeof errorObj.statusCode === 'number' ? errorObj.statusCode : 
                   typeof errorObj.status === 'number' ? errorObj.status : undefined),
      details: errorObj.details || errorObj.data,
    };
  }

  // Fallback for unknown error types
  return {
    message: 'An unknown error occurred',
    code: 'UNKNOWN_ERROR',
  };
};

// Error formatting utilities
export const formatError = (error: unknown): string => {
  const parsed = parseError(error);
  
  if (parsed.statusCode) {
    return `${parsed.message} (${parsed.statusCode})`;
  }
  
  return parsed.message;
};

export const formatErrorForUser = (error: unknown): string => {
  const parsed = parseError(error);
  
  // Debug logs for Playwright test
  console.log('[formatErrorForUser] Original error:', error);
  console.log('[formatErrorForUser] Parsed error:', parsed);
  console.log('[formatErrorForUser] Parsed message:', parsed.message);
  console.log('[formatErrorForUser] Parsed code:', parsed.code);
  console.log('[formatErrorForUser] Parsed statusCode:', parsed.statusCode);
  
  // Map technical errors to user-friendly messages
  const userFriendlyMessages: Record<string, string> = {
    NETWORK_ERROR: 'Unable to connect to the server. Please check your internet connection.',
    AUTHENTICATION_ERROR: 'Please log in to continue.',
    AUTHORIZATION_ERROR: 'You do not have permission to perform this action.',
    NOT_FOUND_ERROR: 'The requested resource was not found.',
    VALIDATION_ERROR: 'Please check your input and try again.',
    RATE_LIMIT_ERROR: 'Too many requests. Please wait a moment and try again.',
    FILE_ERROR: 'There was a problem with the file. Please check the file and try again.',
    CONFLICT_ERROR: 'This resource already exists. Please use different information.',
  };
  
  // If we have a user-friendly message for this error code, use it
  if (userFriendlyMessages[parsed.code]) {
    return userFriendlyMessages[parsed.code];
  }
  
  // If the message is empty or just '[object Object]', provide a fallback
  if (!parsed.message || parsed.message === '[object Object]' || parsed.message.includes('object Object')) {
    // Try to determine error type from status code
    if (parsed.statusCode === 409) {
      return 'This email is already registered. Please use a different email address.';
    }
    if (parsed.statusCode === 400) {
      return 'Please check your input and try again.';
    }
    if (parsed.statusCode === 401) {
      return 'Please log in to continue.';
    }
    if (parsed.statusCode === 403) {
      return 'You do not have permission to perform this action.';
    }
    if (parsed.statusCode === 404) {
      return 'The requested resource was not found.';
    }
    if (parsed.statusCode === 500) {
      return 'An internal server error occurred. Please try again later.';
    }
    return 'An unexpected error occurred. Please try again.';
  }
  
  return parsed.message;
};

// Error logging utilities
export const logError = (error: unknown, context?: Record<string, unknown>): void => {
  const parsed = parseError(error);
  const logData = {
    ...parsed,
    context,
    timestamp: new Date().toISOString(),
    userAgent: navigator.userAgent,
    url: window.location.href,
  };
  
  // In development, log to console
  if (import.meta.env.DEV) {
    console.error('Error logged:', logData);
    if (error instanceof Error && error.stack) {
      console.error('Stack trace:', error.stack);
    }
  }
  
  // In production, you might want to send to an error tracking service
  // Example: Sentry, LogRocket, etc.
  // sendToErrorTrackingService(logData);
};

// Error boundary utilities
export const createErrorBoundary = (fallbackComponent: React.ComponentType<{ error: Error }>) => {
  return class ErrorBoundary extends React.Component<
    { children: React.ReactNode },
    { hasError: boolean; error?: Error }
  > {
    constructor(props: { children: React.ReactNode }) {
      super(props);
      this.state = { hasError: false };
    }

    static getDerivedStateFromError(error: Error) {
      return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
      logError(error, { errorInfo });
    }

    render() {
      if (this.state.hasError && this.state.error) {
        return React.createElement(fallbackComponent, { error: this.state.error });
      }

      return this.props.children;
    }
  };
};

// Async error handling utilities
export const withErrorHandling = <T extends (...args: unknown[]) => Promise<unknown>>(
  fn: T,
  errorHandler?: (error: unknown) => void
): T => {
  return (async (...args: Parameters<T>) => {
    try {
      return await fn(...args);
    } catch (error) {
      if (errorHandler) {
        errorHandler(error);
      } else {
        logError(error, { function: fn.name, arguments: args });
      }
      throw error;
    }
  }) as T;
};

export const safeAsync = async <T>(
  fn: () => Promise<T>,
  defaultValue?: T
): Promise<T | undefined> => {
  try {
    return await fn();
  } catch (error) {
    logError(error);
    return defaultValue;
  }
};

export const retryAsync = async <T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000,
  backoff: number = 2
): Promise<T> => {
  let lastError: unknown;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      
      if (attempt === maxRetries) {
        break;
      }
      
      // Don't retry on certain error types
      if (isAuthenticationError(error) || isAuthorizationError(error) || isValidationError(error)) {
        break;
      }
      
      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, delay * Math.pow(backoff, attempt - 1)));
    }
  }
  
  throw lastError;
};

// Error recovery utilities
export const createErrorRecovery = (strategies: {
  [errorCode: string]: () => Promise<void> | void;
}) => {
  return async (error: unknown): Promise<boolean> => {
    const parsed = parseError(error);
    const strategy = strategies[parsed.code];
    
    if (strategy) {
      try {
        await strategy();
        return true;
      } catch (recoveryError) {
        logError(recoveryError, { originalError: error, recovery: true });
        return false;
      }
    }
    
    return false;
  };
};

// Error notification utilities
export const notifyError = (error: unknown, options: {
  title?: string;
  duration?: number;
  showDetails?: boolean;
} = {}): void => {
  const { title = 'Error', showDetails = false } = options;
  const message = formatErrorForUser(error);
  
  // This would integrate with your notification system
  // Example: toast notification, modal, etc.
  console.error(`${title}: ${message}`);
  
  if (showDetails && import.meta.env.DEV) {
    console.error('Error details:', parseError(error));
  }
};

// Error validation utilities
export const validateAndThrow = (condition: boolean, error: Error | string): void => {
  if (!condition) {
    throw typeof error === 'string' ? new AppError(error) : error;
  }
};

export const assertExists = <T>(value: T | null | undefined, message?: string): T => {
  if (value == null) {
    throw new AppError(message || 'Value does not exist', 'ASSERTION_ERROR');
  }
  return value;
};

export const assertType = <T>(value: unknown, type: string, message?: string): T => {
  if (typeof value !== type) {
    throw new ValidationError(
      message || `Expected ${type}, got ${typeof value}`,
      'type',
      value
    );
  }
  return value as T;
};

// Error context utilities
export const withErrorContext = <T extends (...args: unknown[]) => unknown>(
  fn: T,
  context: Record<string, unknown>
): T => {
  return ((...args: Parameters<T>) => {
    try {
      const result = fn(...args);
      
      // Handle async functions
      if (result instanceof Promise) {
        return result.catch((error) => {
          if (isAppError(error)) {
            const newError = new (error.constructor as new (...args: unknown[]) => AppError)(error.message, error.code, { ...error.context, ...context });
            throw newError;
          }
          throw error;
        });
      }
      
      return result;
    } catch (error) {
      if (isAppError(error)) {
        const newError = new (error.constructor as new (...args: unknown[]) => AppError)(error.message, error.code, { ...error.context, ...context });
        throw newError;
      }
      throw error;
    }
  }) as T;
};

// Global error handler setup
export const setupGlobalErrorHandling = (): void => {
  // Handle unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    logError(event.reason, { type: 'unhandledrejection' });
    
    // Prevent the default browser behavior (logging to console)
    event.preventDefault();
  });
  
  // Handle uncaught errors
  window.addEventListener('error', (event) => {
    logError(event.error || event.message, {
      type: 'uncaughterror',
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
    });
  });
};

// Error metrics utilities
export const errorMetrics = {
  errors: new Map<string, number>(),
  
  track: (error: unknown): void => {
    const parsed = parseError(error);
    const current = errorMetrics.errors.get(parsed.code) || 0;
    errorMetrics.errors.set(parsed.code, current + 1);
  },
  
  getStats: (): Record<string, number> => {
    return Object.fromEntries(errorMetrics.errors);
  },
  
  reset: (): void => {
    errorMetrics.errors.clear();
  },
  
  getMostCommon: (limit: number = 5): Array<{ code: string; count: number }> => {
    return Array.from(errorMetrics.errors.entries())
      .map(([code, count]) => ({ code, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, limit);
  },
};