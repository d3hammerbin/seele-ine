// Simple auth types
export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role?: string;
  permissions?: string[];
  isActive: boolean;
  isVerified: boolean;
  createdAt: string;
  updatedAt: string;
  limits?: {
    dailyRequests: number;
    monthlyRequests: number;
    dailyCost: number;
    monthlyCost: number;
    totalCost: number;
    remainingCredits: number;
  };
}

export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface RegisterData {
  email: string;
  password: string;
  confirmPassword: string;
  firstName: string;
  lastName: string;
  acceptTerms: boolean;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresIn: number;
}

export interface AuthResponse {
  user: User;
  tokens: AuthTokens;
}

export interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}