import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import uiReducer from './slices/uiSlice';
import credentialsReducer from './slices/credentialsSlice';
import apiKeysReducer from './slices/apiKeysSlice';
import usageReducer from './slices/usageSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    ui: uiReducer,
    credentials: credentialsReducer,
    apiKeys: apiKeysReducer,
    usage: usageReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }),
  devTools: process.env.NODE_ENV !== 'production',
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export default store;