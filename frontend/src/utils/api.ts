// API utilities and HTTP client
import { authUtils } from './auth';
import { AppError, NetworkError, AuthenticationError, AuthorizationError, NotFoundError, RateLimitError } from './error';

// API Response types
export interface ApiResponse<T = unknown> {
  data: T;
  message?: string;
  success: boolean;
  errors?: string[];
  meta?: {
    page?: number;
    limit?: number;
    total?: number;
    totalPages?: number;
  };
}

export interface ApiError {
  message: string;
  code?: string;
  field?: string;
  details?: Record<string, unknown>;
}

export interface PaginationParams {
  page?: number;
  limit?: number;
  sort?: string;
  order?: 'asc' | 'desc';
  search?: string;
  filters?: Record<string, unknown>;
}

export interface RequestConfig extends RequestInit {
  timeout?: number;
  retries?: number;
  retryDelay?: number;
  skipAuth?: boolean;
  skipErrorHandling?: boolean;
}

// HTTP Status Code helpers
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
  GATEWAY_TIMEOUT: 504,
} as const;

// Request interceptors
type RequestInterceptor = (config: RequestConfig) => RequestConfig | Promise<RequestConfig>;
type ResponseInterceptor = (response: Response) => Response | Promise<Response>;
type ErrorInterceptor = (error: Error) => Error | Promise<Error>;

class ApiClient {
  private baseURL: string;
  private defaultConfig: RequestConfig;
  private requestInterceptors: RequestInterceptor[] = [];
  private responseInterceptors: ResponseInterceptor[] = [];
  private errorInterceptors: ErrorInterceptor[] = [];

  constructor(baseURL: string = '', defaultConfig: RequestConfig = {}) {
    this.baseURL = baseURL;
    this.defaultConfig = {
      timeout: 30000,
      retries: 3,
      retryDelay: 1000,
      headers: {
        'Content-Type': 'application/json',
      },
      ...defaultConfig,
    };
  }

  // Add request interceptor
  addRequestInterceptor(interceptor: RequestInterceptor): void {
    this.requestInterceptors.push(interceptor);
  }

  // Add response interceptor
  addResponseInterceptor(interceptor: ResponseInterceptor): void {
    this.responseInterceptors.push(interceptor);
  }

  // Add error interceptor
  addErrorInterceptor(interceptor: ErrorInterceptor): void {
    this.errorInterceptors.push(interceptor);
  }

  // Apply request interceptors
  private async applyRequestInterceptors(config: RequestConfig): Promise<RequestConfig> {
    let finalConfig = config;
    for (const interceptor of this.requestInterceptors) {
      finalConfig = await interceptor(finalConfig);
    }
    return finalConfig;
  }

  // Apply response interceptors
  private async applyResponseInterceptors(response: Response): Promise<Response> {
    let finalResponse = response;
    for (const interceptor of this.responseInterceptors) {
      finalResponse = await interceptor(finalResponse);
    }
    return finalResponse;
  }


  // Create full URL
  private createUrl(endpoint: string): string {
    if (endpoint.startsWith('http')) {
      return endpoint;
    }
    return `${this.baseURL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  }

  // Create request config
  private createRequestConfig(config: RequestConfig): RequestConfig {
    const mergedConfig = {
      ...this.defaultConfig,
      ...config,
      headers: {
        ...this.defaultConfig.headers,
        ...config.headers,
      },
    };

    // Add authentication header if not skipped
    if (!mergedConfig.skipAuth) {
      const authHeaders = authUtils.createAuthHeader();
      mergedConfig.headers = {
        ...mergedConfig.headers,
        ...authHeaders,
      };
    }

    return mergedConfig;
  }

  // Handle response errors
  private async handleResponseError(response: Response): Promise<never> {
    let errorData: Record<string, unknown>;
    
    try {
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        errorData = await response.json();
      } else {
        errorData = { message: await response.text() };
      }
    } catch {
      errorData = { message: response.statusText || 'Unknown error' };
    }

    const message = String(errorData.message || errorData.error || response.statusText || 'Request failed');
    const code = String(errorData.code || response.status.toString());

    switch (response.status) {
      case HTTP_STATUS.UNAUTHORIZED:
        throw new AuthenticationError(message, { code, response: errorData });
      case HTTP_STATUS.FORBIDDEN:
        throw new AuthorizationError(message, { code, response: errorData });
      case HTTP_STATUS.NOT_FOUND:
        throw new NotFoundError(message, undefined, undefined, { code, response: errorData });
      case HTTP_STATUS.TOO_MANY_REQUESTS:
        throw new RateLimitError(message, undefined, { code, response: errorData });
      case HTTP_STATUS.BAD_REQUEST:
      case HTTP_STATUS.UNPROCESSABLE_ENTITY:
        throw new AppError(message, code, response.status);
      default:
        if (response.status >= 500) {
          throw new NetworkError(message, response.status, response.url, 'GET', errorData);
        }
        throw new AppError(message, code, response.status);
    }
  }

  // Make HTTP request with retries
  private async makeRequest(url: string, config: RequestConfig): Promise<Response> {
    const { timeout, retries = 0, retryDelay = 1000, ...fetchConfig } = config;
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        // Create abort controller for timeout
        const controller = new AbortController();
        const timeoutId = timeout ? setTimeout(() => controller.abort(), timeout) : null;

        const response = await fetch(url, {
          ...fetchConfig,
          signal: controller.signal,
        });

        if (timeoutId) clearTimeout(timeoutId);

        return response;
      } catch (error) {
        lastError = error as Error;

        // Don't retry on certain errors
        if (
          error instanceof TypeError ||
          (error as Record<string, unknown>).name === 'AbortError' ||
          attempt === retries
        ) {
          break;
        }

        // Wait before retry
        if (attempt < retries) {
          await new Promise(resolve => setTimeout(resolve, retryDelay * Math.pow(2, attempt)));
        }
      }
    }

    throw new NetworkError(
      lastError?.message || 'Network request failed',
      undefined,
      url,
      fetchConfig.method as string || 'GET',
      undefined,
      { originalError: lastError }
    );
  }

  // Main request method
  async request<T = unknown>(endpoint: string, config: RequestConfig = {}): Promise<ApiResponse<T>> {
    // Apply request interceptors
    const interceptedConfig = await this.applyRequestInterceptors(config);
    
    // Create request config
    const requestConfig = this.createRequestConfig(interceptedConfig);
    
    // Create URL
    const url = this.createUrl(endpoint);
    
    // Make request
    let response = await this.makeRequest(url, requestConfig);
    
    // Apply response interceptors
    response = await this.applyResponseInterceptors(response);
    
    // Handle error responses
    if (!response.ok) {
      await this.handleResponseError(response);
    }
    
    // Parse response
    const contentType = response.headers.get('content-type');
    let data: unknown;
    
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }
    
    // Return standardized response
    if (typeof data === 'object' && data !== null && 'data' in data) {
      return data as ApiResponse<T>;
    }
    
    return {
      data: data as T,
      success: true,
    };
  }

  // HTTP method shortcuts
  async get<T = unknown>(endpoint: string, config: RequestConfig = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'GET' });
  }

  async post<T = unknown>(endpoint: string, data?: unknown, config: RequestConfig = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T = unknown>(endpoint: string, data?: unknown, config: RequestConfig = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async patch<T = unknown>(endpoint: string, data?: unknown, config: RequestConfig = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T = unknown>(endpoint: string, config: RequestConfig = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'DELETE' });
  }

  // Upload file
  async upload<T = unknown>(
    endpoint: string,
    file: File,
    options: {
      fieldName?: string;
      additionalData?: Record<string, unknown>;
      onProgress?: (progress: number) => void;
      config?: RequestConfig;
    } = {}
  ): Promise<ApiResponse<T>> {
    const { fieldName = 'file', additionalData = {}, config = {} } = options;
    
    const formData = new FormData();
    formData.append(fieldName, file);
    
    // Add additional data
    Object.entries(additionalData).forEach(([key, value]) => {
      formData.append(key, typeof value === 'string' ? value : JSON.stringify(value));
    });
    
    // Remove Content-Type header to let browser set it with boundary
    const { headers = {}, ...restConfig } = config;
    const uploadHeaders = { ...headers } as Record<string, string>;
    delete uploadHeaders['Content-Type'];
    
    return this.request<T>(endpoint, {
      ...restConfig,
      method: 'POST',
      body: formData,
      headers: uploadHeaders,
    });
  }

  // Download file
  async download(
    endpoint: string,
    filename?: string,
    config: RequestConfig = {}
  ): Promise<void> {
    const response = await this.request<Blob>(endpoint, {
      ...config,
      skipErrorHandling: true,
    });
    
    // Create blob URL and download
    const blob = new Blob([response.data]);
    const url = window.URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || 'download';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    window.URL.revokeObjectURL(url);
  }
}

// Create default API client
export const apiClient = new ApiClient(import.meta.env.VITE_API_URL || '/api/v1');

// Add default interceptors
apiClient.addRequestInterceptor(async (config) => {
  // Add request ID for tracking
  const requestId = Math.random().toString(36).substring(2, 15);
  config.headers = {
    ...config.headers,
    'X-Request-ID': requestId,
  };
  
  return config;
});

apiClient.addResponseInterceptor(async (response) => {
  // Log response in development
  if (import.meta.env.DEV) {
    console.log(`API Response [${response.status}]:`, response.url);
  }
  
  return response;
});

apiClient.addErrorInterceptor(async (error) => {
  // Log errors in development
  if (import.meta.env.DEV) {
    console.error('API Error:', error);
  }
  
  return error;
});

// API endpoints helpers
export const api = {
  // Authentication
  auth: {
    login: (credentials: Record<string, unknown>) => apiClient.post('/auth/login', credentials),
    register: (userData: Record<string, unknown>) => apiClient.post('/auth/register', userData),
    refresh: (refreshToken: string) => apiClient.post('/auth/refresh', { refresh_token: refreshToken }),
    logout: (refreshToken: string) => apiClient.post('/auth/logout', { refresh_token: refreshToken }),
    profile: () => apiClient.get('/auth/me'),
    updateProfile: (updates: Record<string, unknown>) => apiClient.put('/auth/me', updates),
    changePassword: (data: Record<string, unknown>) => apiClient.post('/auth/password/change', data),
    forgotPassword: (email: string) => apiClient.post('/auth/password/reset', { email }),
    resetPassword: (data: Record<string, unknown>) => apiClient.post('/auth/password/reset/confirm', data),
    verifyEmail: (token: string) => apiClient.post('/auth/activate', { token }),
    resendVerification: () => apiClient.post('/auth/resend-verification'),
  },

  // Profile management
  profile: {
    get: () => apiClient.get('/auth/me'),
    update: (updates: Record<string, unknown>) => apiClient.put('/auth/me', updates),
    updatePassword: (data: Record<string, unknown>) => apiClient.post('/auth/password/change', data),
    updateEmail: (data: Record<string, unknown>) => apiClient.put('/auth/me', data),
    delete: () => apiClient.delete('/auth/me'),
  },

  // Credentials processing
  credentials: {
    upload: (file: File, options?: Record<string, unknown>) => apiClient.upload('/credentials/upload', file, options),
    process: (credentialId: string, options?: Record<string, unknown>) => apiClient.post(`/credentials/${credentialId}/process`, options),
    get: (credentialId: string) => apiClient.get(`/credentials/${credentialId}`),
    list: (params?: PaginationParams) => {
      const queryString = params ? new URLSearchParams(params as Record<string, string>).toString() : '';
      return apiClient.get(`/credentials${queryString ? `?${queryString}` : ''}`);
    },
    delete: (credentialId: string) => apiClient.delete(`/credentials/${credentialId}`),
    deleteCredentials: (ids: string[]) => apiClient.post('/credentials/bulk-delete', { ids }),
    getCredentials: (params?: Record<string, unknown>) => {
      const queryString = params ? new URLSearchParams(params as Record<string, string>).toString() : '';
      return apiClient.get(`/credentials${queryString ? `?${queryString}` : ''}`);
    },
    uploadFiles: (files: File[]) => {
      const formData = new FormData();
      files.forEach((file, index) => {
        formData.append(`files[${index}]`, file);
      });
      return apiClient.post('/credentials/upload', formData);
    },
    download: (credentialId: string, format?: string) => {
       const queryString = format ? `?format=${encodeURIComponent(format)}` : '';
       return apiClient.get(`/credentials/${credentialId}/download${queryString}`);
     },
    history: (credentialId: string) => apiClient.get(`/credentials/${credentialId}/history`),
    export: (params?: Record<string, unknown>) => {
      const queryString = params ? new URLSearchParams(params as Record<string, string>).toString() : '';
      return apiClient.get(`/credentials/export${queryString ? `?${queryString}` : ''}`);
    },
    create: (data: Record<string, unknown>) => apiClient.post('/credentials', data),
    update: (id: string, data: Record<string, unknown>) => apiClient.put(`/credentials/${id}`, data),
  },

  // API Keys
  apiKeys: {
    list: () => apiClient.get('/api-keys'),
    create: (data: Record<string, unknown>) => apiClient.post('/api-keys', data),
    update: (keyId: string, data: Record<string, unknown>) => apiClient.put(`/api-keys/${keyId}`, data),
    delete: (keyId: string) => apiClient.delete(`/api-keys/${keyId}`),
    regenerate: (keyId: string) => apiClient.post(`/api-keys/${keyId}/regenerate`),
    getUsage: (keyId: string) => apiClient.get(`/api-keys/${keyId}/usage`),
    getApiKeyStats: (keyId: string) => apiClient.get(`/api-keys/${keyId}/stats`),
    toggleApiKeyStatus: (keyId: string, data: Record<string, unknown>) => apiClient.put(`/api-keys/${keyId}/toggle`, data),
    rotate: (keyId: string) => apiClient.post(`/api-keys/${keyId}/rotate`),
  },

  // Usage and billing
  usage: {
    current: () => apiClient.get('/usage/current'),
    history: (params?: Record<string, unknown>) => {
      const queryString = params ? new URLSearchParams(params as Record<string, string>).toString() : '';
      return apiClient.get(`/usage/history${queryString ? `?${queryString}` : ''}`);
    },
    costs: (params?: Record<string, unknown>) => {
      const queryString = params ? new URLSearchParams(params as Record<string, string>).toString() : '';
      return apiClient.get(`/usage/costs${queryString ? `?${queryString}` : ''}`);
    },
    getBillingInfo: () => apiClient.get('/billing/info'),
    getUsageStats: (params?: Record<string, unknown>) => {
      const queryString = params ? new URLSearchParams(params as Record<string, string>).toString() : '';
      return apiClient.get(`/usage/stats${queryString ? `?${queryString}` : ''}`);
    },
    getUsageData: (params?: Record<string, unknown>) => {
      const queryString = params ? new URLSearchParams(params as Record<string, string>).toString() : '';
      return apiClient.get(`/usage/data${queryString ? `?${queryString}` : ''}`);
    },
    exportUsageReport: (format: string, filters?: Record<string, unknown>) => {
      const queryString = filters ? new URLSearchParams(filters as Record<string, string>).toString() : '';
      return apiClient.get(`/usage/export/${format}${queryString ? `?${queryString}` : ''}`);
    },
  },

  // System
  system: {
    health: () => apiClient.get('/health'),
    version: () => apiClient.get('/version'),
    providers: () => apiClient.get('/providers'),
  },
};

// Utility functions
export const apiUtils = {
  // Build query string from params
  buildQueryString: (params: Record<string, unknown>): string => {
    const searchParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        if (Array.isArray(value)) {
          value.forEach(item => searchParams.append(key, item.toString()));
        } else {
          searchParams.append(key, value.toString());
        }
      }
    });
    
    return searchParams.toString();
  },

  // Parse error response
  parseErrorResponse: (error: unknown): { message: string; errors?: string[] } => {
    if (error && typeof error === 'object' && 'response' in error) {
      const errorObj = error as Record<string, any>;
      const data = errorObj.response?.data;
      if (data && typeof data === 'object') {
        return {
          message: data.message || data.error || 'An error occurred',
          errors: data.errors || data.details,
        };
      }
    }
    
    const errorObj = error as Record<string, any>;
    return {
      message: (errorObj?.message) || 'An unexpected error occurred',
    };
  },

  // Check if error is network error
  isNetworkError: (error: unknown): boolean => {
    if (error instanceof NetworkError) return true;
    if (error && typeof error === 'object') {
      const errorObj = error as Record<string, any>;
      return errorObj.code === 'NETWORK_ERROR' ||
             (typeof errorObj.message === 'string' && errorObj.message.includes('fetch'));
    }
    return false;
  },

  // Check if error is authentication error
  isAuthError: (error: unknown): boolean => {
    if (error instanceof AuthenticationError) return true;
    if (error && typeof error === 'object') {
      const errorObj = error as Record<string, any>;
      return errorObj.status === 401 || errorObj.code === 'UNAUTHORIZED';
    }
    return false;
  },

  // Check if error is authorization error
  isAuthorizationError: (error: unknown): boolean => {
    if (error instanceof AuthorizationError) return true;
    if (error && typeof error === 'object') {
      const errorObj = error as Record<string, any>;
      return errorObj.status === 403 || errorObj.code === 'FORBIDDEN';
    }
    return false;
  },

  // Retry request with exponential backoff
  retryRequest: async <T>(
    requestFn: () => Promise<T>,
    options: {
      maxRetries?: number;
      baseDelay?: number;
      maxDelay?: number;
      shouldRetry?: (error: unknown) => boolean;
    } = {}
  ): Promise<T> => {
    const {
      maxRetries = 3,
      baseDelay = 1000,
      maxDelay = 10000,
      shouldRetry = (error) => apiUtils.isNetworkError(error),
    } = options;

    let lastError: unknown;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await requestFn();
      } catch (error) {
        lastError = error;

        if (attempt === maxRetries || !shouldRetry(error)) {
          throw error;
        }

        const delay = Math.min(baseDelay * Math.pow(2, attempt), maxDelay);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }

    throw lastError;
  },

  // Create paginated request function
  createPaginatedRequest: <T>(
    requestFn: (params: PaginationParams) => Promise<ApiResponse<T[]>>
  ) => {
    return async function* (initialParams: PaginationParams = {}) {
      let page = initialParams.page || 1;
      const limit = initialParams.limit || 20;
      let hasMore = true;

      while (hasMore) {
        const response = await requestFn({ ...initialParams, page, limit });
        
        yield {
          data: response.data,
          page,
          total: response.meta?.total || 0,
          totalPages: response.meta?.totalPages || 1,
          hasMore: page < (response.meta?.totalPages || 1),
        };

        hasMore = page < (response.meta?.totalPages || 1);
        page++;
      }
    };
  },
};

// Export API client
export { ApiClient };