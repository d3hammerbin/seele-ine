import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
// import type { PayloadAction } from '@reduxjs/toolkit'; // Temporarily commented out
import type { UsageData, UsageStats, BillingInfo } from '../../types/usage';
import { usageApi } from '../../services/api';

interface UsageState {
  currentPeriod: UsageData | null;
  historicalData: UsageData[];
  stats: UsageStats | null;
  billing: BillingInfo | null;
  isLoading: boolean;
  error: string | null;
  filters: {
    period: 'day' | 'week' | 'month' | 'year';
    startDate: string;
    endDate: string;
    provider?: string;
  };
}

const initialState: UsageState = {
  currentPeriod: null,
  historicalData: [],
  stats: null,
  billing: null,
  isLoading: false,
  error: null,
  filters: {
    period: 'month',
    startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    endDate: new Date().toISOString().split('T')[0],
  },
};

// Async thunks
export const fetchUsageData = createAsyncThunk(
  'usage/fetchUsageData',
  async (params: Record<string, unknown>, { rejectWithValue }) => {
    try {
      const response = await usageApi.getUsageData(params);
      return response;
    } catch (error: unknown) {
      return rejectWithValue((error as Error).message || 'Failed to fetch usage data');
    }
  }
);

export const fetchUsageStats = createAsyncThunk(
  'usage/fetchUsageStats',
  async (params: Record<string, unknown>, { rejectWithValue }) => {
    try {
      const response = await usageApi.getUsageStats(params);
      return response;
    } catch (error: unknown) {
      return rejectWithValue((error as Error).message || 'Failed to fetch usage stats');
    }
  }
);

export const fetchBillingInfo = createAsyncThunk(
  'usage/fetchBillingInfo',
  async (_, { rejectWithValue }) => {
    try {
      const response = await usageApi.getBillingInfo();
      return response;
    } catch (error: unknown) {
      return rejectWithValue((error as Error).message || 'Failed to fetch billing info');
    }
  }
);

export const exportUsageReport = createAsyncThunk(
  'usage/exportUsageReport',
  async (params: { format: 'pdf' | 'excel' | 'csv'; filters: Record<string, unknown> }, { rejectWithValue }) => {
    try {
      const response = await usageApi.exportUsageReport(params.format, params.filters);
      return response;
    } catch (error: unknown) {
      return rejectWithValue((error as Error).message || 'Failed to export usage report');
    }
  }
);

const usageSlice = createSlice({
  name: 'usage',
  initialState,
  reducers: {
    setFilters: (state, action: { payload: Partial<UsageState['filters']> }) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    setPeriod: (state, action: { payload: 'day' | 'week' | 'month' | 'year' }) => {
      state.filters.period = action.payload;
      
      // Auto-adjust date range based on period
      const now = new Date();
      const endDate = now.toISOString().split('T')[0];
      let startDate: string;
      
      switch (action.payload) {
        case 'day':
          startDate = new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString().split('T')[0];
          break;
        case 'week':
          startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
          break;
        case 'month':
          startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
          break;
        case 'year':
          startDate = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
          break;
        default:
          startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
      }
      
      state.filters.startDate = startDate;
      state.filters.endDate = endDate;
    },
    setDateRange: (state, action: { payload: { startDate: string; endDate: string } }) => {
      state.filters.startDate = action.payload.startDate;
      state.filters.endDate = action.payload.endDate;
    },
    clearError: (state) => {
      state.error = null;
    },
    updateRealTimeUsage: (state, action: { payload: Partial<UsageStats> }) => {
      if (state.stats) {
        state.stats = { ...state.stats, ...action.payload };
      }
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch usage data
      .addCase(fetchUsageData.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchUsageData.fulfilled, (state, action) => {
        state.isLoading = false;
        const data = action.payload.data as { current: UsageData; historical?: UsageData[] };
        state.currentPeriod = data.current;
        state.historicalData = data.historical || [];
      })
      .addCase(fetchUsageData.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Fetch usage stats
      .addCase(fetchUsageStats.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchUsageStats.fulfilled, (state, action) => {
        state.isLoading = false;
        state.stats = action.payload.data as UsageStats;
      })
      .addCase(fetchUsageStats.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Fetch billing info
      .addCase(fetchBillingInfo.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchBillingInfo.fulfilled, (state, action) => {
        state.isLoading = false;
        state.billing = action.payload.data as BillingInfo;
      })
      .addCase(fetchBillingInfo.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Export usage report
      .addCase(exportUsageReport.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(exportUsageReport.fulfilled, (state) => {
        state.isLoading = false;
      })
      .addCase(exportUsageReport.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  },
});

export const usageActions = usageSlice.actions;
export default usageSlice.reducer;