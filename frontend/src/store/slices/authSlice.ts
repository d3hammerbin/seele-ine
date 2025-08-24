import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import type { User, LoginCredentials, RegisterData } from '../../types/auth';
import { authApi } from '../../utils/auth';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  token: string | null;
  refreshToken: string | null;
}

const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  token: null,
  refreshToken: null,
};

// Async thunks
export const loginAsync = createAsyncThunk(
  'auth/login',
  async (credentials: LoginCredentials, { rejectWithValue }) => {
    try {
      const response = await authApi.login(credentials);
      return response;
    } catch (error: unknown) {
      return rejectWithValue((error as Error).message || 'Login failed');
    }
  }
);

export const registerAsync = createAsyncThunk(
  'auth/register',
  async (userData: RegisterData, { rejectWithValue }) => {
    try {
      const response = await authApi.register(userData);
      return response;
    } catch (error: unknown) {
      return rejectWithValue((error as Error).message || 'Registration failed');
    }
  }
);

export const logoutAsync = createAsyncThunk(
  'auth/logout',
  async (_, { rejectWithValue }) => {
    try {
      await authApi.logout();
      return true;
    } catch (error: unknown) {
      return rejectWithValue((error as Error).message || 'Logout failed');
    }
  }
);

export const refreshTokenAsync = createAsyncThunk(
  'auth/refreshToken',
  async (_, { rejectWithValue }) => {
    try {
      const response = await authApi.refreshTokens();
      return response;
    } catch (error: unknown) {
      return rejectWithValue((error as Error).message || 'Token refresh failed');
    }
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setUser: (state, action: PayloadAction<User | null>) => {
      state.user = action.payload;
    },
    setAuthenticated: (state, action: PayloadAction<boolean>) => {
      state.isAuthenticated = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    setTokens: (state, action: PayloadAction<{ token: string; refreshToken: string }>) => {
      state.token = action.payload.token;
      state.refreshToken = action.payload.refreshToken;
    },
    clearAuth: (state) => {
      state.user = null;
      state.isAuthenticated = false;
      state.token = null;
      state.refreshToken = null;
      state.error = null;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Login
      .addCase(loginAsync.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(loginAsync.fulfilled, (state, action) => {
        state.isLoading = false;
        state.isAuthenticated = true;
        state.user = action.payload.user;
        state.token = action.payload.tokens.accessToken;
        state.refreshToken = action.payload.tokens.refreshToken;
        state.error = null;
      })
      .addCase(loginAsync.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Register
      .addCase(registerAsync.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(registerAsync.fulfilled, (state, action) => {
        state.isLoading = false;
        state.isAuthenticated = true;
        state.user = action.payload.user;
        state.token = action.payload.tokens.accessToken;
        state.refreshToken = action.payload.tokens.refreshToken;
        state.error = null;
      })
      .addCase(registerAsync.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Logout
      .addCase(logoutAsync.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(logoutAsync.fulfilled, (state) => {
        state.isLoading = false;
        state.user = null;
        state.isAuthenticated = false;
        state.token = null;
        state.refreshToken = null;
        state.error = null;
      })
      .addCase(logoutAsync.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Refresh token
      .addCase(refreshTokenAsync.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(refreshTokenAsync.fulfilled, (state, action) => {
        state.isLoading = false;
        state.token = action.payload.accessToken;
        state.refreshToken = action.payload.refreshToken;
        state.error = null;
      })
      .addCase(refreshTokenAsync.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
        // Clear auth on refresh token failure
        state.user = null;
        state.isAuthenticated = false;
        state.token = null;
        state.refreshToken = null;
      });
  },
});

export const authActions = authSlice.actions;
export default authSlice.reducer;