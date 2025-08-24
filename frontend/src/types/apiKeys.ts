// API Keys related types
export interface ApiKey {
  id: string;
  applicationId: string;
  name?: string;
  clientKey: string;
  clientSecret?: string; // Only returned on creation
  status: ApiKeyStatus;
  permissions: ApiKeyPermission[];
  rateLimit: RateLimit;
  usage: ApiKeyUsage;
  expiresAt?: string;
  lastUsedAt?: string;
  createdAt: string;
  updatedAt: string;
  metadata?: ApiKeyMetadata;
}

export enum ApiKeyStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  EXPIRED = 'expired',
  REVOKED = 'revoked',
  SUSPENDED = 'suspended'
}

export interface ApiKeyPermission {
  resource: string;
  actions: string[];
  conditions?: Record<string, unknown>;
}

export interface RateLimit {
  requestsPerMinute: number;
  requestsPerHour: number;
  requestsPerDay: number;
  burstLimit?: number;
  windowSize?: number;
}

export interface ApiKeyUsage {
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;
  lastRequestAt?: string;
  currentPeriodRequests: number;
  currentPeriodStart: string;
  quotaUsed: number;
  quotaLimit: number;
}

export interface ApiKeyMetadata {
  description?: string;
  tags?: string[];
  environment?: 'development' | 'staging' | 'production';
  ipWhitelist?: string[];
  userAgent?: string;
  referrerWhitelist?: string[];
  [key: string]: unknown;
}

export interface Application {
  id: string;
  userId: string;
  name: string;
  description?: string;
  tier: ApplicationTier;
  status: ApplicationStatus;
  limits: ApplicationLimits;
  apiKeys: ApiKey[];
  usage: ApplicationUsage;
  createdAt: string;
  updatedAt: string;
}

export enum ApplicationTier {
  FREE = 'free',
  BASIC = 'basic',
  PREMIUM = 'premium',
  ENTERPRISE = 'enterprise'
}

export enum ApplicationStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  SUSPENDED = 'suspended',
  DELETED = 'deleted'
}

export interface ApplicationLimits {
  dailyRequests: number;
  monthlyRequests: number;
  rateLimit: number;
  maxFileSize: number;
  concurrentRequests: number;
  storageLimit: number;
  apiKeysLimit: number;
}

export interface ApplicationUsage {
  currentDayRequests: number;
  currentMonthRequests: number;
  totalRequests: number;
  lastRequestAt?: string;
  storageUsed: number;
  activeApiKeys: number;
}

// Request/Response types
export interface CreateApiKeyData extends Record<string, unknown> {
  applicationId?: string;
  name?: string;
  permissions?: ApiKeyPermission[];
  rateLimit?: Partial<RateLimit>;
  expiresAt?: string;
  metadata?: ApiKeyMetadata;
}

export interface UpdateApiKeyData extends Record<string, unknown> {
  name?: string;
  status?: ApiKeyStatus;
  permissions?: ApiKeyPermission[];
  rateLimit?: Partial<RateLimit>;
  expiresAt?: string;
  metadata?: ApiKeyMetadata;
}

export interface CreateApplicationData {
  name: string;
  description?: string;
  tier: ApplicationTier;
  limits?: Partial<ApplicationLimits>;
}

export interface UpdateApplicationData {
  name?: string;
  description?: string;
  status?: ApplicationStatus;
  limits?: Partial<ApplicationLimits>;
}

export interface ApiKeyListParams {
  applicationId?: string;
  status?: ApiKeyStatus;
  search?: string;
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  includeUsage?: boolean;
}

export interface ApplicationListParams {
  status?: ApplicationStatus;
  tier?: ApplicationTier;
  search?: string;
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  includeUsage?: boolean;
}

export interface ApiKeyRotateData {
  preserveOld?: boolean;
  expiresAt?: string;
}

export interface ApiKeyValidationResult {
  isValid: boolean;
  apiKey?: ApiKey;
  errors?: string[];
  warnings?: string[];
  remainingQuota?: number;
  rateLimitStatus?: RateLimitStatus;
}

export interface RateLimitStatus {
  limit: number;
  remaining: number;
  resetAt: string;
  retryAfter?: number;
}

export interface ApiKeyAnalytics {
  apiKeyId: string;
  period: AnalyticsPeriod;
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;
  averageResponseTime: number;
  topEndpoints: EndpointUsage[];
  errorBreakdown: ErrorBreakdown[];
  usageOverTime: UsageDataPoint[];
  geographicDistribution: GeographicUsage[];
}

export enum AnalyticsPeriod {
  LAST_HOUR = 'last_hour',
  LAST_24_HOURS = 'last_24_hours',
  LAST_7_DAYS = 'last_7_days',
  LAST_30_DAYS = 'last_30_days',
  CUSTOM = 'custom'
}

export interface EndpointUsage {
  endpoint: string;
  method: string;
  requests: number;
  averageResponseTime: number;
  errorRate: number;
}

export interface ErrorBreakdown {
  statusCode: number;
  count: number;
  percentage: number;
  message?: string;
}

export interface UsageDataPoint {
  timestamp: string;
  requests: number;
  errors: number;
  averageResponseTime: number;
}

export interface GeographicUsage {
  country: string;
  countryCode: string;
  requests: number;
  percentage: number;
}

// Security types
export interface ApiKeySecurityEvent {
  id: string;
  apiKeyId: string;
  type: SecurityEventType;
  severity: SecuritySeverity;
  description: string;
  ipAddress?: string;
  userAgent?: string;
  location?: string;
  metadata?: Record<string, unknown>;
  createdAt: string;
}

export enum SecurityEventType {
  INVALID_KEY = 'invalid_key',
  RATE_LIMIT_EXCEEDED = 'rate_limit_exceeded',
  SUSPICIOUS_ACTIVITY = 'suspicious_activity',
  UNAUTHORIZED_ACCESS = 'unauthorized_access',
  KEY_COMPROMISED = 'key_compromised',
  UNUSUAL_USAGE_PATTERN = 'unusual_usage_pattern'
}

export enum SecuritySeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}