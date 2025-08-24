// Page-specific types

// Dashboard types
export interface DashboardStats {
  todayJobs: number;
  completedToday: number;
  processingJobs: number;
  totalCredentials: number;
  successRate: number;
}

// Credentials page types
export interface CredentialsFilters {
  status?: 'all' | 'completed' | 'processing' | 'failed';
  provider?: string;
  dateRange?: {
    start: Date;
    end: Date;
  };
  confidence?: {
    min: number;
    max: number;
  };
}

export interface CredentialsSortOptions {
  field: 'createdAt' | 'confidence' | 'processingTime' | 'cost';
  order: 'asc' | 'desc';
}

// API Keys page types
export interface ApiKeyFilters {
  status?: 'all' | 'active' | 'inactive' | 'expired';
  usage?: 'high' | 'medium' | 'low' | 'unused';
}

// Usage page types
export interface UsageFilters {
  period: 'day' | 'week' | 'month' | 'year';
  provider?: string;
  costRange?: {
    min: number;
    max: number;
  };
}

// Auth page types
export interface LoginFormData {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface RegisterFormData {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
  acceptTerms: boolean;
}

// Common page props
export interface PageProps {
  className?: string;
}

// Navigation types
export interface BreadcrumbItem {
  label: string;
  href?: string;
  active?: boolean;
}

export interface PageHeader {
  title: string;
  description?: string;
  breadcrumbs?: BreadcrumbItem[];
  actions?: React.ReactNode;
}