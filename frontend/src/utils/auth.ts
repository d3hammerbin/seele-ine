// Authentication utilities
import type { User, LoginCredentials, RegisterData, AuthTokens } from '../types/auth';
import { storage } from './storage';
import { jwt } from './crypto';
import { STORAGE_KEYS, API_ENDPOINTS } from './constants';

// Token management
export const tokenManager = {
  // Get access token
  getAccessToken: (): string | null => {
    return storage.get(STORAGE_KEYS.ACCESS_TOKEN);
  },

  // Get refresh token
  getRefreshToken: (): string | null => {
    return storage.get(STORAGE_KEYS.REFRESH_TOKEN);
  },

  // Set tokens
  setTokens: (tokens: AuthTokens): void => {
    storage.set(STORAGE_KEYS.ACCESS_TOKEN, tokens.accessToken);
    storage.set(STORAGE_KEYS.REFRESH_TOKEN, tokens.refreshToken);
    
    if (tokens.expiresIn) {
      const expirationTime = Date.now() + (tokens.expiresIn * 1000);
      storage.set(STORAGE_KEYS.TOKEN_EXPIRATION, expirationTime.toString());
    }
  },

  // Clear tokens
  clearTokens: (): void => {
    storage.remove(STORAGE_KEYS.ACCESS_TOKEN);
    storage.remove(STORAGE_KEYS.REFRESH_TOKEN);
    storage.remove(STORAGE_KEYS.TOKEN_EXPIRATION);
  },

  // Check if access token exists
  hasAccessToken: (): boolean => {
    return !!tokenManager.getAccessToken();
  },

  // Check if refresh token exists
  hasRefreshToken: (): boolean => {
    return !!tokenManager.getRefreshToken();
  },

  // Check if access token is expired
  isAccessTokenExpired: (): boolean => {
    const token = tokenManager.getAccessToken();
    if (!token) return true;

    // Check stored expiration time first
    const storedExpiration = storage.get(STORAGE_KEYS.TOKEN_EXPIRATION);
    if (storedExpiration && typeof storedExpiration === 'string') {
      return Date.now() >= parseInt(storedExpiration);
    }

    // Fallback to JWT parsing
    return jwt.isExpired(token);
  },

  // Get time until token expiration (in seconds)
  getTimeUntilExpiration: (): number => {
    const token = tokenManager.getAccessToken();
    if (!token) return 0;

    const storedExpiration = storage.get(STORAGE_KEYS.TOKEN_EXPIRATION);
    if (storedExpiration && typeof storedExpiration === 'string') {
      const expirationTime = parseInt(storedExpiration);
      return Math.max(0, Math.floor((expirationTime - Date.now()) / 1000));
    }

    return jwt.getTimeUntilExpiration(token);
  },

  // Get token payload
  getTokenPayload: (): Record<string, unknown> | null => {
    const token = tokenManager.getAccessToken();
    if (!token) return null;

    const parsed = jwt.parse(token);
    return parsed?.payload || null;
  },

  // Get user ID from token
  getUserIdFromToken: (): string | null => {
    const payload = tokenManager.getTokenPayload();
    const sub = typeof payload?.sub === 'string' ? payload.sub : null;
    const userId = typeof payload?.userId === 'string' ? payload.userId : null;
    const id = typeof payload?.id === 'string' ? payload.id : null;
    return sub || userId || id || null;
  },

  // Get user roles from token
  getUserRolesFromToken: (): string[] => {
    const payload = tokenManager.getTokenPayload();
    const roles = payload?.roles;
    const permissions = payload?.permissions;
    if (Array.isArray(roles)) return roles;
    if (Array.isArray(permissions)) return permissions;
    return [];
  },

  // Check if token has specific role
  hasRole: (role: string): boolean => {
    const roles = tokenManager.getUserRolesFromToken();
    return roles.includes(role);
  },

  // Check if token has any of the specified roles
  hasAnyRole: (roles: string[]): boolean => {
    const userRoles = tokenManager.getUserRolesFromToken();
    return roles.some(role => userRoles.includes(role));
  },

  // Check if token has all specified roles
  hasAllRoles: (roles: string[]): boolean => {
    const userRoles = tokenManager.getUserRolesFromToken();
    return roles.every(role => userRoles.includes(role));
  },
};

// Authentication state management
export const authState = {
  // Check if user is authenticated
  isAuthenticated: (): boolean => {
    return tokenManager.hasAccessToken() && !tokenManager.isAccessTokenExpired();
  },

  // Check if user needs to refresh token
  needsTokenRefresh: (): boolean => {
    return tokenManager.hasRefreshToken() && tokenManager.isAccessTokenExpired();
  },

  // Check if user is completely logged out
  isLoggedOut: (): boolean => {
    return !tokenManager.hasAccessToken() && !tokenManager.hasRefreshToken();
  },

  // Get current user from storage
  getCurrentUser: (): User | null => {
    return storage.get(STORAGE_KEYS.USER_PROFILE);
  },

  // Set current user in storage
  setCurrentUser: (user: User): void => {
    storage.set(STORAGE_KEYS.USER_PROFILE, user);
  },

  // Clear current user from storage
  clearCurrentUser: (): void => {
    storage.remove(STORAGE_KEYS.USER_PROFILE);
  },

  // Get user ID
  getCurrentUserId: (): string | null => {
    const user = authState.getCurrentUser();
    return user?.id || tokenManager.getUserIdFromToken();
  },

  // Get user email
  getCurrentUserEmail: (): string | null => {
    const user = authState.getCurrentUser();
    return user?.email || null;
  },

  // Get user roles
  getCurrentUserRoles: (): string[] => {
    const user = authState.getCurrentUser();
    return user?.role ? [user.role] : tokenManager.getUserRolesFromToken();
  },

  // Check if current user has role
  currentUserHasRole: (role: string): boolean => {
    const roles = authState.getCurrentUserRoles();
    return roles.includes(role);
  },

  // Check if current user has any of the specified roles
  currentUserHasAnyRole: (roles: string[]): boolean => {
    const userRoles = authState.getCurrentUserRoles();
    return roles.some(role => userRoles.includes(role));
  },

  // Check if current user has all specified roles
  currentUserHasAllRoles: (roles: string[]): boolean => {
    const userRoles = authState.getCurrentUserRoles();
    return roles.every(role => userRoles.includes(role));
  },
};

// Authentication API helpers
export const authApi = {
  // Login user
  login: async (credentials: LoginCredentials): Promise<{ user: User; tokens: AuthTokens }> => {
    const response = await fetch(API_ENDPOINTS.AUTH.LOGIN, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Login failed' }));
      throw new Error(error.message || 'Login failed');
    }

    const data = await response.json();
    
    // Convert backend snake_case to frontend camelCase
    const tokens: AuthTokens = {
      accessToken: data.tokens.access_token,
      refreshToken: data.tokens.refresh_token,
      tokenType: data.tokens.token_type || 'Bearer',
      expiresIn: data.tokens.expires_in
    };
    
    // Store tokens and user data
    tokenManager.setTokens(tokens);
    authState.setCurrentUser(data.user);
    
    return { user: data.user, tokens };
  },

  // Register user
  register: async (userData: RegisterData): Promise<{ user: User; tokens: AuthTokens }> => {
    const response = await fetch(API_ENDPOINTS.AUTH.REGISTER, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Registration failed' }));
      throw new Error(error.message || 'Registration failed');
    }

    const data = await response.json();
    
    // Store tokens and user data
    tokenManager.setTokens(data.tokens);
    authState.setCurrentUser(data.user);
    
    return data;
  },

  // Refresh access token
  refreshTokens: async (): Promise<AuthTokens> => {
    const refreshToken = tokenManager.getRefreshToken();
    
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await fetch(API_ENDPOINTS.AUTH.REFRESH, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      // Clear tokens if refresh fails
      tokenManager.clearTokens();
      authState.clearCurrentUser();
      throw new Error('Token refresh failed');
    }

    const result = await response.json();
    
    // Convert backend snake_case to frontend camelCase
    const tokens: AuthTokens = {
      accessToken: result.tokens.access_token,
      refreshToken: result.tokens.refresh_token,
      tokenType: result.tokens.token_type || 'Bearer',
      expiresIn: result.tokens.expires_in
    };
    
    tokenManager.setTokens(tokens);
    
    return tokens;
  },

  // Logout user
  logout: async (): Promise<void> => {
    const refreshToken = tokenManager.getRefreshToken();
    
    // Try to logout on server
    if (refreshToken) {
      try {
        await fetch(API_ENDPOINTS.AUTH.LOGOUT, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${tokenManager.getAccessToken()}`,
          },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
      } catch (error) {
        // Ignore server errors during logout
        console.warn('Server logout failed:', error);
      }
    }
    
    // Clear local storage
    tokenManager.clearTokens();
    authState.clearCurrentUser();
  },

  // Get current user profile from server
  getCurrentUserProfile: async (): Promise<User> => {
    const response = await fetch(API_ENDPOINTS.AUTH.PROFILE, {
      headers: {
        'Authorization': `Bearer ${tokenManager.getAccessToken()}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch user profile');
    }

    const user = await response.json();
    authState.setCurrentUser(user);
    
    return user;
  },

  // Update user profile
  updateUserProfile: async (updates: Partial<User>): Promise<User> => {
    const response = await fetch(API_ENDPOINTS.AUTH.PROFILE, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${tokenManager.getAccessToken()}`,
      },
      body: JSON.stringify(updates),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Profile update failed' }));
      throw new Error(error.message || 'Profile update failed');
    }

    const user = await response.json();
    authState.setCurrentUser(user);
    
    return user;
  },

  // Change password
  changePassword: async (currentPassword: string, newPassword: string): Promise<void> => {
    const response = await fetch(API_ENDPOINTS.AUTH.CHANGE_PASSWORD, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${tokenManager.getAccessToken()}`,
      },
      body: JSON.stringify({ currentPassword, newPassword }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Password change failed' }));
      throw new Error(error.message || 'Password change failed');
    }
  },

  // Request password reset
  requestPasswordReset: async (email: string): Promise<void> => {
    const response = await fetch(API_ENDPOINTS.AUTH.FORGOT_PASSWORD, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Password reset request failed' }));
      throw new Error(error.message || 'Password reset request failed');
    }
  },

  // Reset password with token
  resetPassword: async (token: string, newPassword: string): Promise<void> => {
    const response = await fetch(API_ENDPOINTS.AUTH.RESET_PASSWORD, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ token, newPassword }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Password reset failed' }));
      throw new Error(error.message || 'Password reset failed');
    }
  },

  // Verify email
  verifyEmail: async (token: string): Promise<void> => {
    const response = await fetch(API_ENDPOINTS.AUTH.VERIFY_EMAIL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ token }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Email verification failed' }));
      throw new Error(error.message || 'Email verification failed');
    }
  },

  // Resend verification email
  resendVerificationEmail: async (): Promise<void> => {
    const response = await fetch(API_ENDPOINTS.AUTH.RESEND_VERIFICATION, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${tokenManager.getAccessToken()}`,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Failed to resend verification email' }));
      throw new Error(error.message || 'Failed to resend verification email');
    }
  },
};

// Authentication guards
export const authGuards = {
  // Require authentication
  requireAuth: (): void => {
    if (!authState.isAuthenticated()) {
      throw new Error('Authentication required');
    }
  },

  // Require specific role
  requireRole: (role: string): void => {
    authGuards.requireAuth();
    if (!authState.currentUserHasRole(role)) {
      throw new Error(`Role '${role}' required`);
    }
  },

  // Require any of the specified roles
  requireAnyRole: (roles: string[]): void => {
    authGuards.requireAuth();
    if (!authState.currentUserHasAnyRole(roles)) {
      throw new Error(`One of roles [${roles.join(', ')}] required`);
    }
  },

  // Require all specified roles
  requireAllRoles: (roles: string[]): void => {
    authGuards.requireAuth();
    if (!authState.currentUserHasAllRoles(roles)) {
      throw new Error(`All roles [${roles.join(', ')}] required`);
    }
  },

  // Require email verification
  requireEmailVerification: (): void => {
    authGuards.requireAuth();
    const user = authState.getCurrentUser();
    if (!user?.isVerified) {
      throw new Error('Email verification required');
    }
  },

  // Require user to be owner of resource
  requireOwnership: (resourceUserId: string): void => {
    authGuards.requireAuth();
    const currentUserId = authState.getCurrentUserId();
    if (currentUserId !== resourceUserId) {
      throw new Error('Resource ownership required');
    }
  },
};

// Authentication utilities
export const authUtils = {
  // Create authorization header
  createAuthHeader: (): Record<string, string> => {
    const token = tokenManager.getAccessToken();
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  },

  // Create authenticated fetch function
  createAuthenticatedFetch: () => {
    return async (url: string, options: RequestInit = {}): Promise<Response> => {
      const headers = {
        ...options.headers,
        ...authUtils.createAuthHeader(),
      };

      const response = await fetch(url, {
        ...options,
        headers,
      });

      // Handle token expiration
      if (response.status === 401 && authState.needsTokenRefresh()) {
        try {
          await authApi.refreshTokens();
          
          // Retry request with new token
          const newHeaders = {
            ...options.headers,
            ...authUtils.createAuthHeader(),
          };
          
          return await fetch(url, {
            ...options,
            headers: newHeaders,
          });
        } catch {
          // Refresh failed, redirect to login
          authApi.logout();
          throw new Error('Session expired');
        }
      }

      return response;
    };
  },

  // Auto-refresh token before expiration
  setupAutoRefresh: (bufferTime: number = 300): (() => void) => {
    let timeoutId: NodeJS.Timeout;

    const scheduleRefresh = () => {
      const timeUntilExpiration = tokenManager.getTimeUntilExpiration();
      const refreshTime = Math.max(0, (timeUntilExpiration - bufferTime) * 1000);

      timeoutId = setTimeout(async () => {
        if (authState.needsTokenRefresh()) {
          try {
            await authApi.refreshTokens();
            scheduleRefresh(); // Schedule next refresh
          } catch (error) {
            console.error('Auto token refresh failed:', error);
            authApi.logout();
          }
        }
      }, refreshTime);
    };

    // Start auto-refresh if authenticated
    if (authState.isAuthenticated()) {
      scheduleRefresh();
    }

    // Return cleanup function
    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  },

  // Generate secure state for OAuth
  generateOAuthState: (): string => {
    const state = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
    storage.set(STORAGE_KEYS.OAUTH_STATE, state);
    return state;
  },

  // Verify OAuth state
  verifyOAuthState: (state: string): boolean => {
    const storedState = storage.get(STORAGE_KEYS.OAUTH_STATE);
    storage.remove(STORAGE_KEYS.OAUTH_STATE);
    return storedState === state;
  },

  // Get redirect URL after login
  getRedirectUrl: (): string => {
    return storage.get(STORAGE_KEYS.REDIRECT_URL) || '/';
  },

  // Set redirect URL for after login
  setRedirectUrl: (url: string): void => {
    storage.set(STORAGE_KEYS.REDIRECT_URL, url);
  },

  // Clear redirect URL
  clearRedirectUrl: (): void => {
    storage.remove(STORAGE_KEYS.REDIRECT_URL);
  },

  // Check if user should be redirected after login
  shouldRedirectAfterLogin: (): boolean => {
    return !!storage.get(STORAGE_KEYS.REDIRECT_URL);
  },
};

// Session management
export const sessionManager = {
  // Start session monitoring
  startSessionMonitoring: (options: {
    warningTime?: number; // Time before expiration to show warning (seconds)
    onWarning?: () => void;
    onExpired?: () => void;
  } = {}): (() => void) => {
    const { warningTime = 300, onWarning, onExpired } = options;
    let warningShown = false;
    
    const checkSession = () => {
      if (!authState.isAuthenticated()) {
        if (onExpired) onExpired();
        return;
      }
      
      const timeUntilExpiration = tokenManager.getTimeUntilExpiration();
      
      if (timeUntilExpiration <= 0) {
        if (onExpired) onExpired();
        return;
      }
      
      if (timeUntilExpiration <= warningTime && !warningShown) {
        warningShown = true;
        if (onWarning) onWarning();
      }
      
      if (timeUntilExpiration > warningTime) {
        warningShown = false;
      }
    };
    
    const intervalId = setInterval(checkSession, 10000); // Check every 10 seconds
    
    return () => clearInterval(intervalId);
  },

  // Extend session
  extendSession: async (): Promise<void> => {
    if (authState.needsTokenRefresh()) {
      await authApi.refreshTokens();
    }
  },

  // Get session info
  getSessionInfo: (): {
    isAuthenticated: boolean;
    timeUntilExpiration: number;
    user: User | null;
  } => {
    return {
      isAuthenticated: authState.isAuthenticated(),
      timeUntilExpiration: tokenManager.getTimeUntilExpiration(),
      user: authState.getCurrentUser(),
    };
  },
};