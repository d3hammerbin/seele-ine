import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
// import type { PayloadAction } from '@reduxjs/toolkit'; // Temporarily commented out
import type { ApiKey, CreateApiKeyData } from '../../types/apiKeys';
import { apiKeysApi } from '../../services/api';

interface ApiKeysState {
  apiKeys: ApiKey[];
  isLoading: boolean;
  error: string | null;
  stats: {
    total: number;
    active: number;
    inactive: number;
    monthlyUsage: number;
  };
  selectedKey: ApiKey | null;
}

const initialState: ApiKeysState = {
  apiKeys: [],
  isLoading: false,
  error: null,
  stats: {
    total: 0,
    active: 0,
    inactive: 0,
    monthlyUsage: 0,
  },
  selectedKey: null,
};

// Async thunks
export const fetchApiKeys = createAsyncThunk(
  'apiKeys/fetchApiKeys',
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiKeysApi.getApiKeys();
      return response;
    } catch (error: unknown) {
      return rejectWithValue((error as Error).message || 'Failed to fetch API keys');
    }
  }
);

export const createApiKey = createAsyncThunk(
  'apiKeys/createApiKey',
  async (data: CreateApiKeyData, { rejectWithValue }) => {
    try {
      const response = await apiKeysApi.createApiKey(data);
      return response;
    } catch (error: unknown) {
      return rejectWithValue((error as Error).message || 'Failed to create API key');
    }
  }
);

export const deleteApiKey = createAsyncThunk(
  'apiKeys/deleteApiKey',
  async (id: string, { rejectWithValue }) => {
    try {
      await apiKeysApi.deleteApiKey(id);
      return id;
    } catch (error: unknown) {
      return rejectWithValue((error as Error).message || 'Failed to delete API key');
    }
  }
);

export const regenerateApiKey = createAsyncThunk(
  'apiKeys/regenerateApiKey',
  async (id: string, { rejectWithValue }) => {
    try {
      const response = await apiKeysApi.regenerateApiKey(id);
      return response;
    } catch (error: unknown) {
      return rejectWithValue((error as Error).message || 'Failed to regenerate API key');
    }
  }
);

export const toggleApiKeyStatus = createAsyncThunk(
  'apiKeys/toggleApiKeyStatus',
  async ({ id, data }: { id: string; data: Record<string, unknown> }, { rejectWithValue }) => {
    try {
      const response = await apiKeysApi.toggleApiKeyStatus(id, data);
      return response;
    } catch (error: unknown) {
      return rejectWithValue((error as Error).message || 'Failed to toggle API key status');
    }
  }
);

export const fetchApiKeyStats = createAsyncThunk(
  'apiKeys/fetchStats',
  async (keyId: string, { rejectWithValue }) => {
    try {
      const response = await apiKeysApi.getApiKeyStats(keyId);
      return response;
    } catch (error: unknown) {
      return rejectWithValue((error as Error).message || 'Failed to fetch API key stats');
    }
  }
);

const apiKeysSlice = createSlice({
  name: 'apiKeys',
  initialState,
  reducers: {
    setSelectedKey: (state, action: { payload: ApiKey | null }) => {
      state.selectedKey = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
    updateApiKeyUsage: (state, action: { payload: { id: string; usage: ApiKey['usage'] } }) => {
      const apiKey = state.apiKeys.find(key => key.id === action.payload.id);
      if (apiKey) {
        apiKey.usage = action.payload.usage;
      }
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch API keys
      .addCase(fetchApiKeys.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchApiKeys.fulfilled, (state, action) => {
        state.isLoading = false;
        state.apiKeys = action.payload.data as ApiKey[];
      })
      .addCase(fetchApiKeys.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Create API key
      .addCase(createApiKey.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(createApiKey.fulfilled, (state, action) => {
        state.isLoading = false;
        const apiKey = action.payload.data as ApiKey;
        state.apiKeys.push(apiKey);
        state.stats.total += 1;
        if (apiKey.status === 'active') {
          state.stats.active += 1;
        } else {
          state.stats.inactive += 1;
        }
      })
      .addCase(createApiKey.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Delete API key
      .addCase(deleteApiKey.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(deleteApiKey.fulfilled, (state, action) => {
        state.isLoading = false;
        const deletedKey = state.apiKeys.find(key => key.id === action.payload);
        state.apiKeys = state.apiKeys.filter(key => key.id !== action.payload);
        state.stats.total -= 1;
        if (deletedKey?.status === 'active') {
          state.stats.active -= 1;
        } else {
          state.stats.inactive -= 1;
        }
      })
      .addCase(deleteApiKey.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Regenerate API key
      .addCase(regenerateApiKey.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(regenerateApiKey.fulfilled, (state, action) => {
        state.isLoading = false;
        const apiKey = action.payload.data as ApiKey;
        const keyIndex = state.apiKeys.findIndex(key => key.id === apiKey.id);
        if (keyIndex !== -1) {
          state.apiKeys[keyIndex] = apiKey;
        }
      })
      .addCase(regenerateApiKey.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Toggle API key status
      .addCase(toggleApiKeyStatus.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(toggleApiKeyStatus.fulfilled, (state, action) => {
        state.isLoading = false;
        const apiKey = action.payload.data as ApiKey;
        const keyIndex = state.apiKeys.findIndex(key => key.id === apiKey.id);
        if (keyIndex !== -1) {
          const wasActive = state.apiKeys[keyIndex].status === 'active';
          state.apiKeys[keyIndex] = apiKey;
          
          // Update stats
          if (wasActive && apiKey.status !== 'active') {
            state.stats.active -= 1;
            state.stats.inactive += 1;
          } else if (!wasActive && apiKey.status === 'active') {
            state.stats.active += 1;
            state.stats.inactive -= 1;
          }
        }
      })
      .addCase(toggleApiKeyStatus.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Fetch API key stats
      .addCase(fetchApiKeyStats.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchApiKeyStats.fulfilled, (state, action) => {
        state.isLoading = false;
        state.stats = action.payload.data as { total: number; active: number; inactive: number; monthlyUsage: number; };
      })
      .addCase(fetchApiKeyStats.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  },
});

export const apiKeysActions = apiKeysSlice.actions;
export default apiKeysSlice.reducer;