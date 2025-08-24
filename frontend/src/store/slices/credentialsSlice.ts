import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
// import type { PayloadAction } from '@reduxjs/toolkit'; // Temporarily commented out
import type { CredentialData, ProcessingJob } from '../../types/credentials';
import { credentialsApi } from '../../services/api';

interface CredentialsState {
  credentials: CredentialData[];
  currentJob: ProcessingJob | null;
  jobs: ProcessingJob[];
  isLoading: boolean;
  error: string | null;
  filters: {
    status: 'all' | 'processed' | 'processing' | 'error';
    search: string;
    sortBy: 'date' | 'name' | 'confidence';
    sortOrder: 'asc' | 'desc';
  };
  pagination: {
    page: number;
    limit: number;
    total: number;
  };
  selectedIds: string[];
}

const initialState: CredentialsState = {
  credentials: [],
  currentJob: null,
  jobs: [],
  isLoading: false,
  error: null,
  filters: {
    status: 'all',
    search: '',
    sortBy: 'date',
    sortOrder: 'desc',
  },
  pagination: {
    page: 1,
    limit: 20,
    total: 0,
  },
  selectedIds: [],
};

// Async thunks
export const fetchCredentials = createAsyncThunk(
  'credentials/fetchCredentials',
  async (params: Record<string, unknown>, { rejectWithValue }) => {
    try {
      const response = await credentialsApi.getCredentials(params);
      return response;
    } catch (error: unknown) {
      return rejectWithValue((error as Error).message || 'Failed to fetch credentials');
    }
  }
);

export const uploadFiles = createAsyncThunk(
  'credentials/uploadFiles',
  async (files: File[], { rejectWithValue }) => {
    try {
      const response = await credentialsApi.uploadFiles(files);
      return response;
    } catch (error: unknown) {
      return rejectWithValue((error as Error).message || 'Failed to upload files');
    }
  }
);

export const deleteCredentials = createAsyncThunk(
  'credentials/deleteCredentials',
  async (ids: string[], { rejectWithValue }) => {
    try {
      await credentialsApi.deleteCredentials(ids);
      return ids;
    } catch (error: unknown) {
      return rejectWithValue((error as Error).message || 'Failed to delete credentials');
    }
  }
);

const credentialsSlice = createSlice({
  name: 'credentials',
  initialState,
  reducers: {
    setFilters: (state, action: { payload: Partial<CredentialsState['filters']> }) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    setPagination: (state, action: { payload: Partial<CredentialsState['pagination']> }) => {
      state.pagination = { ...state.pagination, ...action.payload };
    },
    setSelectedIds: (state, action: { payload: string[] }) => {
      state.selectedIds = action.payload;
    },
    toggleSelected: (state, action: { payload: string }) => {
      const id = action.payload;
      if (state.selectedIds.includes(id)) {
        state.selectedIds = state.selectedIds.filter(selectedId => selectedId !== id);
      } else {
        state.selectedIds.push(id);
      }
    },
    selectAll: (state) => {
      state.selectedIds = state.credentials.map(cred => cred.id);
    },
    clearSelection: (state) => {
      state.selectedIds = [];
    },
    setCurrentJob: (state, action: { payload: ProcessingJob | null }) => {
      state.currentJob = action.payload;
    },
    updateJob: (state, action: { payload: ProcessingJob }) => {
      const jobIndex = state.jobs.findIndex(job => job.id === action.payload.id);
      if (jobIndex !== -1) {
        state.jobs[jobIndex] = action.payload;
      } else {
        state.jobs.push(action.payload);
      }
      
      if (state.currentJob?.id === action.payload.id) {
        state.currentJob = action.payload;
      }
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch credentials
      .addCase(fetchCredentials.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchCredentials.fulfilled, (state, action) => {
        state.isLoading = false;
        const data = action.payload.data as { credentials: CredentialData[]; total?: number };
        state.credentials = data.credentials || (action.payload.data as CredentialData[]);
        state.pagination.total = data.total || 0;
      })
      .addCase(fetchCredentials.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Upload files
      .addCase(uploadFiles.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(uploadFiles.fulfilled, (state, action) => {
        state.isLoading = false;
        state.currentJob = action.payload.data as ProcessingJob;
        state.jobs.push(action.payload.data as ProcessingJob);
      })
      .addCase(uploadFiles.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Delete credentials
      .addCase(deleteCredentials.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(deleteCredentials.fulfilled, (state, action) => {
        state.isLoading = false;
        state.credentials = state.credentials.filter(
          cred => !action.payload.includes(cred.id)
        );
        state.selectedIds = state.selectedIds.filter(
          id => !action.payload.includes(id)
        );
      })
      .addCase(deleteCredentials.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  },
});

export const credentialsActions = credentialsSlice.actions;
export default credentialsSlice.reducer;