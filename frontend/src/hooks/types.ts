// Hook types and interfaces
import type { User, RegisterData as AuthRegisterData } from '../types/auth';
import type { ValidationResult, FieldValidationResult } from '../utils/validation';
// Theme mode type
export type ThemeMode = 'light' | 'dark' | 'system';

// Theme interface for useTheme hook
export interface Theme {
  id: string;
  name: string;
  mode: ThemeMode;
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    border: string;
    error: string;
    warning: string;
    success: string;
    info: string;
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    '2xl': string;
  };
  typography: {
    fontFamily: string;
    fontSize: {
      xs: string;
      sm: string;
      base: string;
      lg: string;
      xl: string;
      '2xl': string;
      '3xl': string;
    };
    fontWeight: {
      normal: string;
      medium: string;
      semibold: string;
      bold: string;
    };
    lineHeight: {
      tight: string;
      normal: string;
      relaxed: string;
    };
  };
  borderRadius: {
    none: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    full: string;
  };
  shadows: {
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
}

// useAuth hook types
export interface UseAuthReturn {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string, rememberMe?: boolean) => Promise<void>;
  register: (userData: AuthRegisterData) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  updateProfile: (updates: Partial<User>) => Promise<void>;
  changePassword: (currentPassword: string, newPassword: string) => Promise<void>;
  requestPasswordReset: (email: string) => Promise<void>;
  resetPassword: (token: string, newPassword: string) => Promise<void>;
  verifyEmail: (token: string) => Promise<void>;
  resendVerificationEmail: () => Promise<void>;
  hasRole: (role: string) => boolean;
  hasAnyRole: (roles: string[]) => boolean;
  hasAllRoles: (roles: string[]) => boolean;
  clearError: () => void;
}

// RegisterData is imported from '../types/auth' as AuthRegisterData
// Removed duplicate definition to avoid type conflicts

// useApi hook types
export interface UseApiReturn<T = unknown> {
  data: T | null;
  loading: boolean;
  error: string | null;
  execute: (...args: unknown[]) => Promise<T>;
  reset: () => void;
  cancel: () => void;
}

export interface UseApiOptions {
  immediate?: boolean;
  onSuccess?: (data: unknown) => void;
  onError?: (error: unknown) => void;
  retries?: number;
  retryDelay?: number;
}

// useAsync hook types
export interface UseAsyncReturn<T, P extends unknown[] = unknown[]> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  execute: (...args: P) => Promise<T | null>;
  reset: () => void;
  cancel: () => void;
}

export interface UseAsyncOptions {
  immediate?: boolean;
  onSuccess?: (data: unknown) => void;
  onError?: (error: Error) => void;
}

// useWebSocket hook types
export interface UseWebSocketReturn {
  socket: WebSocket | null;
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  send: (data: unknown) => void;
  connect: () => void;
  disconnect: () => void;
  subscribe: (event: string, handler: (data: unknown) => void) => () => void;
  unsubscribe: (event: string, handler?: (data: unknown) => void) => void;
}

export interface UseWebSocketOptions {
  autoConnect?: boolean;
  reconnectAttempts?: number;
  reconnectInterval?: number;
  heartbeatInterval?: number;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  onMessage?: (data: unknown) => void;
}

// useNotifications hook types
export interface UseNotificationsReturn {
  notifications: Notification[];
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => string;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  getUnreadCount: () => number;
}

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  timestamp: number;
  read: boolean;
  persistent?: boolean;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

// useTheme hook types
export interface UseThemeReturn {
  currentTheme: Theme;
  themes: Theme[];
  themeMode: ThemeMode;
  mode: ThemeMode;
  isDark: boolean;
  setTheme: (themeId: string) => void;
  setMode: (mode: ThemeMode) => void;
  toggleTheme: () => void;
  addTheme: (theme: Theme) => void;
  removeTheme: (themeId: string) => void;
  getTheme: (themeId: string) => Theme | undefined;
}

// useFileUpload hook types
export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

export interface UseFileUploadReturn {
  files: FileUploadState[];
  isUploading: boolean;
  progress: number;
  error: string | null;
  uploadFile: (file: File, options?: FileUploadOptions) => Promise<unknown>;
  uploadFiles: (files: File[], options?: FileUploadOptions) => Promise<unknown[]>;
  removeFile: (fileId: string) => void;
  clearFiles: () => void;
  retryUpload: (fileId: string) => Promise<unknown>;
  cancelUpload: (fileId: string) => void;
}

export interface FileUploadState {
  id: string;
  file: File;
  status: 'pending' | 'uploading' | 'completed' | 'error' | 'cancelled';
  progress: UploadProgress;
  error?: string;
  result?: unknown;
  uploadedAt?: number;
  startTime?: number;
  endTime?: number;
}

export interface FileUploadOptions {
  endpoint?: string;
  fieldName?: string;
  additionalData?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  concurrent?: boolean;
  onProgress?: (progress: number) => void;
  onSuccess?: (result: unknown) => void;
  onError?: (error: string) => void;
  onComplete?: (result: unknown) => void;
  maxSize?: number;
  allowedTypes?: string[];
  validateFile?: (file: File) => boolean | string;
}

// usePagination hook types
export interface UsePaginationReturn {
  currentPage: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startIndex: number;
  endIndex: number;
  visiblePages: number[];
  goToPage: (page: number) => void;
  goToNextPage: () => void;
  goToPreviousPage: () => void;
  goToFirstPage: () => void;
  goToLastPage: () => void;
  setPageSize: (size: number) => void;
  reset: () => void;
}

export interface UsePaginationOptions {
  initialPage?: number;
  initialPageSize?: number;
  maxVisiblePages?: number;
  onPageChange?: (page: number) => void;
  onPageSizeChange?: (size: number) => void;
}

// useSearch hook types
export interface UseSearchReturn<T = unknown> {
  query: string;
  results: T[];
  isSearching: boolean;
  error: string | null;
  totalResults: number;
  hasMore: boolean;
  searchHistory: string[];
  suggestions: string[];
  searchConfig: SearchConfig;
  setQuery: (query: string) => void;
  updateQuery: (query: string) => void;
  search: (query?: string) => Promise<void>;
  performSearch: (query: string, options?: unknown) => Promise<SearchResult<T>>;
  searchLocal: (query: string, data: T[]) => SearchResult<T>;
  loadMore: () => Promise<void>;
  clearResults: () => void;
  reset: () => void;
  clearSearch: () => void;
  clearHistory: () => void;
  getSuggestions: (query: string) => string[];
}

export interface UseSearchOptions<T = unknown> {
  searchFn: (query: string, options?: unknown) => Promise<{ data: T[]; total: number; hasMore: boolean }>;
  debounceMs?: number;
  minQueryLength?: number;
  immediate?: boolean;
  onSearch?: (query: string) => void;
  onResults?: (results: T[]) => void;
  onError?: (error: string) => void;
}

// useForm hook types
export interface UseFormReturn<T = Record<string, unknown>> {
  values: T;
  errors: FormErrors<T>;
  touched: FormTouched<T>;
  isValid: boolean;
  isSubmitting: boolean;
  isValidating: boolean;
  isDirty: boolean;
  submitCount: number;
  canSubmit: boolean;
  setFieldValue: (field: keyof T, value: unknown) => Promise<void>;
  setFieldError: (field: keyof T, error: string | undefined) => void;
  setFieldTouched: (field: keyof T, touched?: boolean) => Promise<void>;
  getFieldProps: (field: keyof T) => unknown;
  handleSubmit: (event?: React.FormEvent) => Promise<void>;
  reset: (values?: Partial<T>) => void;
  setFormValues: (values: Partial<T>) => void;
  setFormErrors: (errors: Partial<FormErrors<T>>) => void;
  clearErrors: () => void;
  validateForm: () => Promise<FormErrors<T>>;
  validateField: (field: keyof T, value: unknown) => Promise<string | undefined>;
  getFormConfig: () => FormConfig<T>;
  handleChange: (field: keyof T) => (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => void;
  handleBlur: (field: keyof T) => () => void;
}

export interface UseFormOptions<T = Record<string, unknown>> {
  initialValues: T;
  validationSchema?: unknown;
  validateOnChange?: boolean;
  validateOnBlur?: boolean;
  onSubmit?: (values: T) => Promise<void> | void;
  onValidationError?: (errors: Record<keyof T, string>) => void;
}

export type FormErrors<T> = Partial<Record<keyof T, string | undefined>>;
export type FormTouched<T> = Partial<Record<keyof T, boolean>>;

export interface FormConfig<T> {
  values: T;
  errors: FormErrors<T>;
  touched: FormTouched<T>;
  isSubmitting: boolean;
  isValidating: boolean;
  isValid: boolean;
  isDirty: boolean;
  submitCount: number;
  canSubmit: boolean;
}

// useValidation hook types
export interface UseValidationReturn {
  validate: (value: unknown, rules: ValidationRule[]) => ValidationResult;
  validateField: (field: string, value: unknown, rules: ValidationRule[]) => FieldValidationResult;
  validateForm: (values: Record<string, unknown>, schema: ValidationSchema) => FormValidationResult;
  isValidEmail: (email: string) => boolean;
  isStrongPassword: (password: string) => boolean;
  getPasswordStrength: (password: string) => PasswordStrength;
}

export interface ValidationRule {
  type: string;
  message: string;
  value?: unknown;
  validator?: (value: unknown, formValues?: unknown) => boolean | Promise<boolean>;
}

export interface ValidationSchema {
  [field: string]: ValidationRule[];
}

export interface FormValidationResult {
  isValid: boolean;
  errors: Record<string, string>;
  fieldResults: Record<string, FieldValidationResult>;
}

export interface PasswordStrength {
  score: number;
  feedback: string[];
  suggestions: string[];
}

// useCredentialProcessing hook types
export interface UseCredentialProcessingReturn {
  credentials: CredentialItem[];
  isLoading: boolean;
  error: string | null;
  uploadCredential: (file: File, options?: CredentialUploadOptions) => Promise<string>;
  processCredential: (credentialId: string, options?: ProcessingOptions) => Promise<void>;
  getCredential: (credentialId: string) => Promise<CredentialItem>;
  deleteCredential: (credentialId: string) => Promise<void>;
  downloadCredential: (credentialId: string, format?: string) => Promise<void>;
  getProcessingHistory: (credentialId: string) => Promise<ProcessingHistoryItem[]>;
  subscribeToUpdates: (credentialId: string, callback: (update: ProcessingUpdate) => void) => () => void;
  refreshCredentials: () => Promise<void>;
}

export interface CredentialItem {
  id: string;
  filename: string;
  fileSize: number;
  fileType: string;
  uploadedAt: string;
  status: 'uploaded' | 'processing' | 'completed' | 'failed';
  progress?: number;
  result?: CredentialResult;
  error?: string;
  processingTime?: number;
  cost?: number;
  provider?: string;
  extractionMethod?: string;
}

export interface CredentialResult {
  extractedData: Record<string, unknown>;
  confidence: number;
  qrData?: string;
  ocrText?: string;
  metadata: Record<string, unknown>;
}

export interface CredentialUploadOptions {
  credentialType?: string;
  extractionMethod?: string;
  provider?: string;
  autoProcess?: boolean;
}

export interface ProcessingOptions {
  provider?: string;
  extractionMethod?: string;
  priority?: 'low' | 'normal' | 'high';
  webhook?: string;
}

export interface ProcessingUpdate {
  credentialId: string;
  status: string;
  progress?: number;
  result?: CredentialResult;
  error?: string;
  timestamp: string;
}

export interface ProcessingHistoryItem {
  id: string;
  credentialId: string;
  status: string;
  provider: string;
  extractionMethod: string;
  startedAt: string;
  completedAt?: string;
  duration?: number;
  cost?: number;
  result?: CredentialResult;
  error?: string;
}

// useUsageTracking hook types
export interface UseUsageTrackingReturn {
  usageData: UsageData;
  metrics: UsageMetrics;
  costBreakdown: CostBreakdown;
  isLoading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  usage: Array<{ requests: number; date: string }>;
  costs: Array<{ totalCost: number; date: string }>;
  loading: boolean;
  fetchUsageData: (filter?: UsageFilter) => Promise<void>;
  trackUsage: (event: {
    type: 'request' | 'processing' | 'upload' | 'download';
    provider?: string;
    feature?: string;
    tokens?: number;
    cost?: number;
    processingTime?: number;
    success?: boolean;
    metadata?: Record<string, unknown>;
  }) => Promise<void>;
  getUsageHistory: (filter?: {
    startDate?: Date;
    endDate?: Date;
    provider?: string;
    feature?: string;
    groupBy?: 'hour' | 'day' | 'week' | 'month';
  }) => Promise<unknown[]>;
  exportUsageData: (format?: 'json' | 'csv' | 'pdf', filter?: UsageFilter) => Promise<unknown>;
  fetchUsage: (filter?: { period?: string }) => Promise<void>;
  fetchMetrics: (filter?: { period?: string }) => Promise<void>;
  fetchCosts: (filter?: { period?: string }) => Promise<void>;
  exportData: (options?: { period?: string; format?: string; includeMetrics?: boolean; includeCosts?: boolean }) => Promise<unknown>;
  resetWarnings: () => void;
  getUsagePercentage: (type: 'daily' | 'monthly', metric: 'requests' | 'cost' | 'tokens') => number;
  isLimitExceeded: (type: 'daily' | 'monthly', metric: 'requests' | 'cost' | 'tokens') => boolean;
  getRemainingQuota: (type: 'daily' | 'monthly', metric: 'requests' | 'cost' | 'tokens') => number;
}

export interface UsageData {
  current: {
    requests: number;
    tokens: number;
    cost: number;
    processingTime: number;
    successfulRequests: number;
    failedRequests: number;
  };
  daily: {
    requests: number;
    tokens: number;
    cost: number;
    processingTime: number;
    successfulRequests: number;
    failedRequests: number;
  };
  monthly: {
    requests: number;
    tokens: number;
    cost: number;
    processingTime: number;
    successfulRequests: number;
    failedRequests: number;
  };
  total: {
    requests: number;
    tokens: number;
    cost: number;
    processingTime: number;
    successfulRequests: number;
    failedRequests: number;
  };
}

export interface ProviderUsage {
  requests: number;
  cost: number;
  averageResponseTime: number;
  successRate: number;
}

export interface UsageHistoryItem {
  date: string;
  requests: number;
  cost: number;
  successRate: number;
  averageResponseTime: number;
  providerBreakdown: Record<string, ProviderUsage>;
}

export interface CostData {
  totalCost: number;
  costByProvider: Record<string, number>;
  costByMethod: Record<string, number>;
  costTrend: CostTrendItem[];
  projectedMonthlyCost: number;
}

export interface CostTrendItem {
  date: string;
  cost: number;
  requests: number;
}

export interface UsageMetrics {
  averageRequestTime: number;
  successRate: number;
  costPerRequest: number;
  tokensPerRequest: number;
  peakUsageHour: number;
  mostUsedProvider: string;
  mostUsedFeature: string;
  trendsData: unknown[];
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;
  totalCost: number;
  providerBreakdown: Record<string, { requests: number; cost: number }>;
}

export interface CostBreakdown {
  byProvider: Record<string, number>;
  byFeature: Record<string, number>;
  byTimeOfDay: Record<string, number>;
  byDate: Record<string, number>;
  predictions: {
    dailyEstimate: number;
    monthlyEstimate: number;
    yearlyEstimate: number;
  };
}

export interface UsageFilter {
  startDate?: Date;
  endDate?: Date;
  provider?: string;
  feature?: string;
  userId?: string;
}

// useApiKeys hook types
export interface UseApiKeysReturn {
  apiKeys: ApiKeyItem[];
  isLoading: boolean;
  error: string | null;
  createApiKey: (data: CreateApiKeyData) => Promise<ApiKeyItem>;
  updateApiKey: (keyId: string, data: UpdateApiKeyData) => Promise<boolean>;
  deleteApiKey: (keyId: string) => Promise<boolean>;
  regenerateApiKey: (keyId: string) => Promise<string | null>;
  refreshApiKeys: () => Promise<void>;
}

export interface ApiKeyItem {
  id: string;
  name: string;
  key: string;
  keyPreview: string;
  permissions: string[];
  rateLimit: number;
  isActive: boolean;
  createdAt: string;
  lastUsedAt?: string;
  expiresAt?: string;
  usage: {
    totalRequests: number;
    requestsThisMonth: number;
    lastRequest?: string;
  };
}

export interface CreateApiKeyData {
  name: string;
  permissions: string[];
  rateLimit?: number;
  expiresAt?: string;
}

export interface UpdateApiKeyData {
  name?: string;
  permissions?: string[];
  rateLimit?: number;
  isActive?: boolean;
  expiresAt?: string;
}

// usePermissions hook types
export interface Permission {
  id: string;
  name: string;
  description: string;
  category: string;
  resource?: string;
  action: string;
  granted?: boolean;
  conditions?: Record<string, unknown>;
}

export interface Role {
  id: string;
  name: string;
  description: string;
  level: number;
  permissions: string[];
  isSystem: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface UserPermissions {
  userId: string;
  roles: string[];
  permissions: string[];
  effectivePermissions: string[];
  context?: Record<string, unknown>;
}

export interface PermissionCheck {
  permission: string;
  resource?: Resource;
  action?: string;
  context?: Record<string, unknown>;
}

export interface Resource {
  id: string;
  type: string;
  ownerId?: string;
  permissions?: string[];
  metadata?: Record<string, unknown>;
}

export interface UsePermissionsReturn {
  permissions: Permission[];
  roles: Role[];
  userPermissions: UserPermissions | null;
  isLoading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  fetchPermissions: () => Promise<void>;
  hasPermission: (permission: string, resource?: string, context?: Record<string, unknown>) => boolean;
  hasAllPermissions: (permissions: string[], resource?: string, context?: Record<string, unknown>) => boolean;
  hasAnyPermission: (permissions: string[], resource?: string, context?: Record<string, unknown>) => boolean;
  hasRole: (role: string) => boolean;
  hasAnyRole: (roles: string[]) => boolean;
  getEffectivePermissions: (context?: Record<string, unknown>) => string[];
  checkPermission: (check: PermissionCheck) => boolean;
  checkPermissions: (checks: PermissionCheck[]) => boolean[];
  getPermissionsByCategory: (category: string) => Permission[];
  getRolePermissions: (roleId: string) => Permission[];
  getUserRoles: () => Role[];
  getRoleLevel: (role: string) => number;
  hasRoleLevel: (role: string, level: number) => boolean;
  canPerformAction: (action: string, resourceType: string) => boolean;
  getAvailableActions: (resourceType: string) => string[];
  clearCache: () => void;
  refreshPermissions: () => Promise<void>;
  commonPermissions: Record<string, boolean>;
}

// Common utility types
export interface AsyncState<T = unknown> {
  data: T | null;
  loading: boolean;
  error: Error | null;
}

export interface PaginatedData<T = unknown> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  hasMore: boolean;
}

export interface SortConfig {
  field: string;
  direction: 'asc' | 'desc';
}

export interface FilterConfig {
  [key: string]: unknown;
}

export interface SearchConfig {
  query: string;
  fields: (string | number | symbol)[];
  caseSensitive?: boolean;
  exactMatch?: boolean;
  highlightMatches?: boolean;
  maxResults?: number;
}

export interface SearchResult<T = unknown> {
  query: string;
  results: T[];
  total: number;
  hasMore: boolean;
  searchTime?: number;
  suggestions?: string[];
}