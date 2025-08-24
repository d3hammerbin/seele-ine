// Usage and billing related types
export interface UsageData {
  id: string;
  userId: string;
  applicationId?: string;
  date: string;
  requests: number;
  successfulRequests: number;
  failedRequests: number;
  totalCost: number;
  aiProviderCosts: AIProviderCost[];
  processingTime: number;
  dataProcessed: number;
  credentialsProcessed: number;
  createdAt: string;
  updatedAt: string;
}

export interface AIProviderCost {
  provider: string;
  model?: string;
  requests: number;
  inputTokens?: number;
  outputTokens?: number;
  cost: number;
  currency: string;
}

export interface UsageStats {
  period: UsagePeriod;
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;
  successRate: number;
  totalCost: number;
  averageCostPerRequest: number;
  credentialsProcessed: number;
  averageProcessingTime: number;
  topAIProviders: ProviderUsage[];
  dailyUsage: DailyUsage[];
  monthlyUsage: MonthlyUsage[];
  costBreakdown: CostBreakdown;
  limits: UsageLimits;
  quotas: UsageQuotas;
}

export enum UsagePeriod {
  TODAY = 'today',
  YESTERDAY = 'yesterday',
  LAST_7_DAYS = 'last_7_days',
  LAST_30_DAYS = 'last_30_days',
  THIS_MONTH = 'this_month',
  LAST_MONTH = 'last_month',
  THIS_YEAR = 'this_year',
  CUSTOM = 'custom'
}

export interface ProviderUsage {
  provider: string;
  requests: number;
  cost: number;
  percentage: number;
  averageResponseTime: number;
  successRate: number;
}

export interface DailyUsage {
  date: string;
  requests: number;
  cost: number;
  credentialsProcessed: number;
  averageProcessingTime: number;
  errors: number;
}

export interface MonthlyUsage {
  month: string;
  year: number;
  requests: number;
  cost: number;
  credentialsProcessed: number;
  averageProcessingTime: number;
  errors: number;
}

export interface CostBreakdown {
  aiProviders: {
    [provider: string]: {
      cost: number;
      percentage: number;
      requests: number;
    };
  };
  services: {
    ocr: number;
    qr: number;
    ai_analysis: number;
    validation: number;
  };
  total: number;
}

export interface UsageLimits {
  dailyRequests: {
    limit: number;
    used: number;
    remaining: number;
    resetAt: string;
  };
  monthlyRequests: {
    limit: number;
    used: number;
    remaining: number;
    resetAt: string;
  };
  monthlyCost: {
    limit: number;
    used: number;
    remaining: number;
    resetAt: string;
  };
  rateLimit: {
    requestsPerMinute: number;
    currentUsage: number;
    resetAt: string;
  };
}

export interface UsageQuotas {
  fileSize: {
    maxSizeMB: number;
    totalUsedMB: number;
    remainingMB: number;
  };
  storage: {
    maxStorageGB: number;
    usedStorageGB: number;
    remainingStorageGB: number;
  };
  concurrentRequests: {
    maxConcurrent: number;
    currentActive: number;
  };
}

export interface BillingInfo {
  id: string;
  userId: string;
  period: BillingPeriod;
  startDate: string;
  endDate: string;
  status: BillingStatus;
  totalAmount: number;
  currency: string;
  itemizedCosts: BillingItem[];
  taxes: BillingTax[];
  discounts: BillingDiscount[];
  paymentMethod?: PaymentMethod;
  invoiceUrl?: string;
  paidAt?: string;
  dueDate: string;
  createdAt: string;
  updatedAt: string;
}

export enum BillingPeriod {
  DAILY = 'daily',
  WEEKLY = 'weekly',
  MONTHLY = 'monthly',
  QUARTERLY = 'quarterly',
  YEARLY = 'yearly'
}

export enum BillingStatus {
  DRAFT = 'draft',
  PENDING = 'pending',
  PAID = 'paid',
  OVERDUE = 'overdue',
  CANCELLED = 'cancelled',
  REFUNDED = 'refunded'
}

export interface BillingItem {
  description: string;
  quantity: number;
  unitPrice: number;
  totalPrice: number;
  category: BillingCategory;
  metadata?: Record<string, unknown>;
}

export enum BillingCategory {
  AI_PROCESSING = 'ai_processing',
  OCR_PROCESSING = 'ocr_processing',
  QR_PROCESSING = 'qr_processing',
  STORAGE = 'storage',
  API_REQUESTS = 'api_requests',
  PREMIUM_FEATURES = 'premium_features',
  SUBSCRIPTION = 'subscription'
}

export interface BillingTax {
  name: string;
  rate: number;
  amount: number;
}

export interface BillingDiscount {
  name: string;
  type: 'percentage' | 'fixed';
  value: number;
  amount: number;
}

export interface PaymentMethod {
  id: string;
  type: 'credit_card' | 'debit_card' | 'bank_transfer' | 'paypal' | 'stripe';
  last4?: string;
  brand?: string;
  expiryMonth?: number;
  expiryYear?: number;
  isDefault: boolean;
}

// Request/Response types
export interface UsageQueryParams {
  period?: UsagePeriod;
  startDate?: string;
  endDate?: string;
  applicationId?: string;
  groupBy?: 'day' | 'week' | 'month';
  includeDetails?: boolean;
}

export interface CostAnalysisParams {
  period?: UsagePeriod;
  startDate?: string;
  endDate?: string;
  groupBy?: 'provider' | 'service' | 'application';
  currency?: string;
}

export interface UsageExportParams {
  format: 'json' | 'csv' | 'xlsx' | 'pdf';
  period?: UsagePeriod;
  startDate?: string;
  endDate?: string;
  includeDetails?: boolean;
  includeCosts?: boolean;
}

export interface UsageAlert {
  id: string;
  userId: string;
  type: UsageAlertType;
  threshold: number;
  currentValue: number;
  isTriggered: boolean;
  message: string;
  createdAt: string;
  triggeredAt?: string;
}

export enum UsageAlertType {
  DAILY_REQUESTS = 'daily_requests',
  MONTHLY_REQUESTS = 'monthly_requests',
  MONTHLY_COST = 'monthly_cost',
  RATE_LIMIT = 'rate_limit',
  STORAGE_LIMIT = 'storage_limit'
}