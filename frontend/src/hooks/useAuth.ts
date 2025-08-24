// Authentication hook
import { useState, useEffect, useCallback, useMemo } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { authState, tokenManager, sessionManager } from '../utils/auth';
import { api } from '../utils/api';
import type { UseAuthReturn } from './types';
import type { User, RegisterData, AuthTokens } from '../types/auth';
import type { RootState } from '../types/store';
import { authActions } from '../store/slices/authSlice';
import useNotifications from './useNotifications';
import { useAnalytics } from './useAnalytics';

const useAuth = (): UseAuthReturn => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { addNotification } = useNotifications();
  const { track } = useAnalytics();
  
  // Redux state
  const {
    user,
    isAuthenticated: reduxIsAuthenticated,
    isLoading,
    error,
  } = useSelector((state: RootState) => state.auth);

  // Local state for additional loading states
  const [localLoading, setLocalLoading] = useState(false);

  // Computed authentication state (combines Redux and localStorage)
  const isAuthenticated = useMemo(() => {
    // If Redux says we're authenticated, trust it (it gets updated immediately after login)
    // localStorage might have a slight delay
    return reduxIsAuthenticated || authState.isAuthenticated();
  }, [reduxIsAuthenticated]);

  // Logout function (defined early to avoid circular dependency)
  const logout = useCallback(async (): Promise<void> => {
    try {
      setLocalLoading(true);
      
      const refreshToken = tokenManager.getRefreshToken();
      if (refreshToken) {
        await api.auth.logout(refreshToken);
      }
      tokenManager.clearTokens();
      authState.clearCurrentUser();
      dispatch(authActions.clearAuth());

      addNotification({
        type: 'info',
        title: 'Logged Out',
        message: 'You have been successfully logged out.',
      });
      
      // Redirect to login page
      navigate('/login', { replace: true });
    } catch (error: unknown) {
      // Even if server logout fails, clear local state
      tokenManager.clearTokens();
      authState.clearCurrentUser();
      dispatch(authActions.clearAuth());
      navigate('/login', { replace: true });
      console.error('Logout error:', error);
    } finally {
      setLocalLoading(false);
    }
  }, [dispatch, addNotification, navigate]);

  // Initialize authentication state
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        dispatch(authActions.setLoading(true));
        
        // Check if user is authenticated
        if (authState.isAuthenticated()) {
          const currentUser = authState.getCurrentUser();
          
          if (currentUser) {
            dispatch(authActions.setUser(currentUser));
            dispatch(authActions.setAuthenticated(true));
          } else {
            // Try to fetch user profile from server
            try {
              const response = await api.auth.profile();
            const userProfile = response.data as User;
              // Store user in local storage
              authState.setCurrentUser(userProfile);
              dispatch(authActions.setUser(userProfile));
              dispatch(authActions.setAuthenticated(true));
            } catch {
              // If profile fetch fails, clear tokens
              tokenManager.clearTokens();
              authState.clearCurrentUser();
              dispatch(authActions.clearAuth());
            }
          }
        } else if (authState.needsTokenRefresh()) {
          // Try to refresh token
          try {
            const refreshToken = tokenManager.getRefreshToken();
            if (refreshToken) {
              const refreshResponse = await api.auth.refresh(refreshToken);
              const responseData = refreshResponse.data as { tokens: any };
              
              // Convert backend snake_case to frontend camelCase
              const tokens: AuthTokens = {
                accessToken: responseData.tokens.access_token,
                refreshToken: responseData.tokens.refresh_token,
                tokenType: responseData.tokens.token_type || 'Bearer',
                expiresIn: responseData.tokens.expires_in
              };
              
              tokenManager.setTokens(tokens);
            }
            const response = await api.auth.profile();
            const userProfile = response.data as User;
            // Store user in local storage
            authState.setCurrentUser(userProfile);
            dispatch(authActions.setUser(userProfile));
            dispatch(authActions.setAuthenticated(true));
          } catch {
            // Refresh failed, clear everything
            tokenManager.clearTokens();
            authState.clearCurrentUser();
            dispatch(authActions.clearAuth());
          }
        } else {
          // Not authenticated
          dispatch(authActions.clearAuth());
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
        dispatch(authActions.setError('Failed to initialize authentication'));
      } finally {
        dispatch(authActions.setLoading(false));
      }
    };

    initializeAuth();
  }, [dispatch]);

  // Setup session monitoring - Fixed to prevent re-renders
  useEffect(() => {
    if (!isAuthenticated) return;

    const cleanup = sessionManager.startSessionMonitoring({
      warningTime: 300, // 5 minutes
      onWarning: () => {
        addNotification({
          type: 'warning',
          title: 'Session Expiring',
          message: 'Your session will expire in 5 minutes. Please save your work.',
          persistent: true,
          action: {
            label: 'Extend Session',
            onClick: async () => {
              try {
                await sessionManager.extendSession();
                addNotification({
                  type: 'success',
                  title: 'Session Extended',
                  message: 'Your session has been extended.',
                });
              } catch {
                addNotification({
                  type: 'error',
                  title: 'Session Extension Failed',
                  message: 'Failed to extend session. Please log in again.',
                });
              }
            },
          },
        });
      },
      onExpired: () => {
        addNotification({
          type: 'error',
          title: 'Session Expired',
          message: 'Your session has expired. Please log in again.',
        });
        logout();
      },
    });

    return cleanup;
  }, [isAuthenticated]); // Removed addNotification and logout from dependencies

  // Login function
  const login = useCallback(async (
    email: string,
    password: string,
    rememberMe: boolean = false
  ): Promise<void> => {
    try {
      setLocalLoading(true);
      dispatch(authActions.setLoading(true));
      dispatch(authActions.clearError());

      const response = await api.auth.login({ email, password });
      const responseData = response.data as { user: User; tokens: any };
      
      // Convert backend snake_case to frontend camelCase
      const tokens: AuthTokens = {
        accessToken: responseData.tokens.access_token,
        refreshToken: responseData.tokens.refresh_token,
        tokenType: responseData.tokens.token_type || 'Bearer',
        expiresIn: responseData.tokens.expires_in
      };
      
      const loggedInUser = responseData.user;
      
      // Store tokens with appropriate expiration
      if (rememberMe) {
        // Extend token expiration for "remember me"
        const extendedTokens = {
          ...tokens,
          expiresIn: tokens.expiresIn || 30 * 24 * 60 * 60, // 30 days
        };
        tokenManager.setTokens(extendedTokens);
      } else {
        tokenManager.setTokens(tokens);
      }

      // Store user in local storage
      authState.setCurrentUser(loggedInUser);
      
      dispatch(authActions.setUser(loggedInUser));
      dispatch(authActions.setAuthenticated(true));
      
      // Set loading to false immediately
      setLocalLoading(false);

      // Track login event
      track({
        name: 'user_login',
        properties: {
          userId: loggedInUser.id,
          email: loggedInUser.email,
          rememberMe,
        },
      });

      addNotification({
        type: 'success',
        title: 'Welcome back!',
        message: `Hello ${loggedInUser.firstName}, you have successfully logged in.`,
      });
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      dispatch(authActions.setError(errorMessage));
      
      addNotification({
        type: 'error',
        title: 'Login Failed',
        message: errorMessage,
      });
      
      throw error;
    } finally {
      setLocalLoading(false);
      dispatch(authActions.setLoading(false));
    }
  }, [dispatch, addNotification, track]);

  // Register function
  const register = useCallback(async (userData: RegisterData): Promise<void> => {
    try {
      setLocalLoading(true);
      dispatch(authActions.setLoading(true));
      dispatch(authActions.clearError());

      // Transform firstName and lastName to full_name for backend compatibility
      const transformedData = {
        email: userData.email,
        password: userData.password,
        full_name: `${userData.firstName} ${userData.lastName}`.trim(),
        // Remove frontend-specific fields that backend doesn't expect
        // firstName, lastName, confirmPassword, acceptTerms are not sent to backend
      };

      const response = await api.auth.register(transformedData);
      const { user: newUser, tokens } = response.data as { user: User; tokens: AuthTokens };
      
      // Store tokens and user in local storage
      if (tokens) {
        tokenManager.setTokens(tokens);
      }
      authState.setCurrentUser(newUser);
      
      dispatch(authActions.setUser(newUser));
      dispatch(authActions.setAuthenticated(true));
      
      // Set loading to false immediately
      setLocalLoading(false);

      // Track registration event
      track({
        name: 'user_signup',
        properties: {
          userId: newUser.id,
          email: newUser.email,
        },
      });

      addNotification({
        type: 'success',
        title: 'Registration Successful',
        message: `Welcome ${newUser.firstName}! Please check your email to verify your account.`,
      });
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Registration failed';
      dispatch(authActions.setError(errorMessage));
      
      addNotification({
        type: 'error',
        title: 'Registration Failed',
        message: errorMessage,
      });
      
      throw error;
    } finally {
      setLocalLoading(false);
      dispatch(authActions.setLoading(false));
    }
  }, [dispatch, addNotification, track]);



  // Refresh token function
  const refreshToken = useCallback(async (): Promise<void> => {
    try {
      const refreshToken = tokenManager.getRefreshToken();
      if (refreshToken) {
        const refreshResponse = await api.auth.refresh(refreshToken);
        const responseData = refreshResponse.data as { tokens: any };
        
        // Convert backend snake_case to frontend camelCase
        const tokens: AuthTokens = {
          accessToken: responseData.tokens.access_token,
          refreshToken: responseData.tokens.refresh_token,
          tokenType: responseData.tokens.token_type || 'Bearer',
          expiresIn: responseData.tokens.expires_in
        };
        
        tokenManager.setTokens(tokens);
      }
      // Tokens are now properly updated in storage
    } catch (error: unknown) {
      // If refresh fails, logout user
      dispatch(authActions.clearAuth());
      throw error;
    }
  }, [dispatch]);

  // Update profile function
  const updateProfile = useCallback(async (updates: Partial<User>): Promise<void> => {
    try {
      setLocalLoading(true);
      dispatch(authActions.clearError());

      const response = await api.auth.updateProfile(updates);
      const updatedUser = response.data as User;
      dispatch(authActions.setUser(updatedUser));

      addNotification({
        type: 'success',
        title: 'Profile Updated',
        message: 'Your profile has been successfully updated.',
      });
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Profile update failed';
      dispatch(authActions.setError(errorMessage));
      
      addNotification({
        type: 'error',
        title: 'Profile Update Failed',
        message: errorMessage,
      });
      
      throw error;
    } finally {
      setLocalLoading(false);
    }
  }, [dispatch, addNotification]);

  // Change password function
  const changePassword = useCallback(async (
    currentPassword: string,
    newPassword: string
  ): Promise<void> => {
    try {
      setLocalLoading(true);
      dispatch(authActions.clearError());

      await api.auth.changePassword({ currentPassword, newPassword });

      addNotification({
        type: 'success',
        title: 'Password Changed',
        message: 'Your password has been successfully changed.',
      });
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Password change failed';
      dispatch(authActions.setError(errorMessage));
      
      addNotification({
        type: 'error',
        title: 'Password Change Failed',
        message: errorMessage,
      });
      
      throw error;
    } finally {
      setLocalLoading(false);
    }
  }, [dispatch, addNotification]);

  // Request password reset function
  const requestPasswordReset = useCallback(async (email: string): Promise<void> => {
    try {
      setLocalLoading(true);
      dispatch(authActions.clearError());

      await api.auth.forgotPassword(email);

      addNotification({
        type: 'success',
        title: 'Reset Email Sent',
        message: 'Password reset instructions have been sent to your email.',
      });
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Password reset request failed';
      dispatch(authActions.setError(errorMessage));
      
      addNotification({
        type: 'error',
        title: 'Reset Request Failed',
        message: errorMessage,
      });
      
      throw error;
    } finally {
      setLocalLoading(false);
    }
  }, [dispatch, addNotification]);

  // Reset password function
  const resetPassword = useCallback(async (
    token: string,
    newPassword: string
  ): Promise<void> => {
    try {
      setLocalLoading(true);
      dispatch(authActions.clearError());

      await api.auth.resetPassword({ token, newPassword });

      addNotification({
        type: 'success',
        title: 'Password Reset',
        message: 'Your password has been successfully reset. Please log in with your new password.',
      });
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Password reset failed';
      dispatch(authActions.setError(errorMessage));
      
      addNotification({
        type: 'error',
        title: 'Password Reset Failed',
        message: errorMessage,
      });
      
      throw error;
    } finally {
      setLocalLoading(false);
    }
  }, [dispatch, addNotification]);

  // Verify email function
  const verifyEmail = useCallback(async (token: string): Promise<void> => {
    try {
      setLocalLoading(true);
      dispatch(authActions.clearError());

      await api.auth.verifyEmail(token);

      // Refresh user profile to get updated verification status
      if (isAuthenticated) {
        const response = await api.auth.profile();
        const updatedUser = response.data as User;
        dispatch(authActions.setUser(updatedUser));
      }

      addNotification({
        type: 'success',
        title: 'Email Verified',
        message: 'Your email has been successfully verified.',
      });
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Email verification failed';
      dispatch(authActions.setError(errorMessage));
      
      addNotification({
        type: 'error',
        title: 'Email Verification Failed',
        message: errorMessage,
      });
      
      throw error;
    } finally {
      setLocalLoading(false);
    }
  }, [dispatch, addNotification, isAuthenticated]);

  // Resend verification email function
  const resendVerificationEmail = useCallback(async (): Promise<void> => {
    try {
      setLocalLoading(true);
      dispatch(authActions.clearError());

      await api.auth.resendVerification();

      addNotification({
        type: 'success',
        title: 'Verification Email Sent',
        message: 'A new verification email has been sent to your email address.',
      });
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to resend verification email';
      dispatch(authActions.setError(errorMessage));
      
      addNotification({
        type: 'error',
        title: 'Resend Failed',
        message: errorMessage,
      });
      
      throw error;
    } finally {
      setLocalLoading(false);
    }
  }, [dispatch, addNotification]);

  // Role checking functions
  const hasRole = useCallback((role: string): boolean => {
    return authState.currentUserHasRole(role);
  }, []);

  const hasAnyRole = useCallback((roles: string[]): boolean => {
    return authState.currentUserHasAnyRole(roles);
  }, []);

  const hasAllRoles = useCallback((roles: string[]): boolean => {
    return authState.currentUserHasAllRoles(roles);
  }, []);

  // Clear error function
  const clearError = useCallback((): void => {
    dispatch(authActions.clearError());
  }, [dispatch]);

  return {
    user,
    isAuthenticated,
    isLoading: isLoading || localLoading,
    loading: isLoading || localLoading,
    error,
    login,
    register,
    logout,
    refreshToken,
    updateProfile,
    changePassword,
    requestPasswordReset,
    resetPassword,
    verifyEmail,
    resendVerificationEmail,
    hasRole,
    hasAnyRole,
    hasAllRoles,
    clearError,
  };
};

export default useAuth;