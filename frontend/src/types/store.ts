import type { AuthState } from './auth';
import type { CredentialState } from './credential';
import type { Toast } from './ui';

// Root state interface
export interface RootState {
  auth: AuthState;
  credentials: CredentialState;
  ui: UIState;
  app: AppState;
}

// UI State
export interface UIState {
  theme: 'light' | 'dark' | 'system';
  sidebarCollapsed: boolean;
  loading: {
    global: boolean;
    [key: string]: boolean;
  };
  toasts: Toast[];
  modals: {
    [key: string]: {
      isOpen: boolean;
      data?: unknown;
    };
  };
  notifications: Notification[];
}

// App State
export interface AppState {
  initialized: boolean;
  version: string;
  config: {
    apiUrl: string;
    features: {
      darkMode: boolean;
      analytics: boolean;
      debug: boolean;
    };
    fileUpload: {
      maxSize: number;
      allowedTypes: string[];
    };
  };
  connectivity: {
    online: boolean;
    lastSync: string | null;
  };
}

// Notification interface
export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  actions?: Array<{
    label: string;
    action: string;
    data?: unknown;
  }>;
}

// Redux Action Types
export interface Action<T = unknown> {
  type: string;
  payload?: T;
}

// Async Action States
export interface AsyncActionState<T = unknown> {
  data: T | null;
  loading: boolean;
  error: string | null;
  lastUpdated: string | null;
}

// Generic async thunk state
export interface ThunkState<T = unknown> {
  pending: boolean;
  fulfilled: boolean;
  rejected: boolean;
  data: T | null;
  error: string | null;
}

// Store configuration
export interface StoreConfig {
  preloadedState?: Partial<RootState>;
  middleware?: unknown[];
  devTools?: boolean;
}

// Selector types
export type Selector<T> = (state: RootState) => T;
export type ParametricSelector<P, T> = (state: RootState, params: P) => T;

// Action creator types
export type ActionCreator<P = void> = P extends void
  ? () => Action
  : (payload: P) => Action<P>;

export type AsyncActionCreator<P = void, R = unknown> = P extends void
  ? () => Promise<R>
  : (payload: P) => Promise<R>;

// Middleware types
export interface MiddlewareAPI {
  dispatch: (action: Action) => void;
  getState: () => RootState;
}

export type Middleware = (api: MiddlewareAPI) => (next: (action: Action) => void) => (action: Action) => void;

// Store slice state interfaces
export type AuthSliceState = AuthState;

export type CredentialSliceState = CredentialState;

export type UISliceState = UIState;

export type AppSliceState = AppState;

// Action payload types
export interface SetLoadingPayload {
  key: string;
  loading: boolean;
}

export type AddToastPayload = Omit<Toast, 'id'>;

export interface RemoveToastPayload {
  id: string;
}

export interface OpenModalPayload {
  key: string;
  data?: unknown;
}

export interface CloseModalPayload {
  key: string;
}

export type AddNotificationPayload = Omit<Notification, 'id' | 'timestamp' | 'read'>;

export interface MarkNotificationReadPayload {
  id: string;
}

export interface SetThemePayload {
  theme: 'light' | 'dark' | 'system';
}

export interface ToggleSidebarPayload {
  collapsed?: boolean;
}

// Error handling types
export interface ErrorState {
  message: string;
  code?: string | number;
  details?: unknown;
  timestamp: string;
}

export interface GlobalError extends ErrorState {
  id: string;
  dismissed: boolean;
}

// Cache types
export interface CacheState<T = unknown> {
  data: Record<string, T>;
  timestamps: Record<string, number>;
  ttl: number;
}

// Persistence types
export interface PersistConfig {
  key: string;
  storage: Storage;
  whitelist?: string[];
  blacklist?: string[];
  transforms?: unknown[];
}

// WebSocket state
export interface WebSocketState {
  connected: boolean;
  connecting: boolean;
  error: string | null;
  lastMessage: unknown;
  subscriptions: string[];
}

// Feature flags
export interface FeatureFlags {
  [key: string]: boolean;
}

// Analytics state
export interface AnalyticsState {
  enabled: boolean;
  userId?: string;
  sessionId: string;
  events: AnalyticsEvent[];
}

export interface AnalyticsEvent {
  id: string;
  name: string;
  properties: Record<string, unknown>;
  timestamp: string;
  sent: boolean;
}

// Performance monitoring
export interface PerformanceState {
  metrics: {
    [key: string]: {
      duration: number;
      timestamp: string;
    };
  };
  errors: {
    [key: string]: {
      count: number;
      lastOccurred: string;
    };
  };
}

// Export utility types
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type StrictOmit<T, K extends keyof T> = Omit<T, K>;

export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;