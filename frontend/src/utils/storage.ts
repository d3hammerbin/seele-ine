import { STORAGE_KEYS, CACHE } from './constants';

// Storage interface
interface StorageInterface {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
  clear(): void;
}

// Safe storage wrapper that handles errors
class SafeStorage implements StorageInterface {
  public storage: Storage;
  private available: boolean;

  constructor(storage: Storage) {
    this.storage = storage;
    this.available = this.isAvailable();
  }

  private isAvailable(): boolean {
    try {
      const testKey = '__storage_test__';
      this.storage.setItem(testKey, 'test');
      this.storage.removeItem(testKey);
      return true;
    } catch {
      return false;
    }
  }

  getItem(key: string): string | null {
    if (!this.available) return null;
    try {
      return this.storage.getItem(key);
    } catch {
      return null;
    }
  }

  setItem(key: string, value: string): void {
    if (!this.available) return;
    try {
      this.storage.setItem(key, value);
    } catch (error) {
      // Handle quota exceeded error
      if (error instanceof DOMException && error.code === 22) {
        this.clearOldCache();
        try {
          this.storage.setItem(key, value);
        } catch {
          // Still failed, give up
        }
      }
    }
  }

  removeItem(key: string): void {
    if (!this.available) return;
    try {
      this.storage.removeItem(key);
    } catch {
      // Ignore errors
    }
  }

  clear(): void {
    if (!this.available) return;
    try {
      this.storage.clear();
    } catch {
      // Ignore errors
    }
  }

  private clearOldCache(): void {
    if (!this.available) return;
    try {
      const keys = Object.keys(this.storage);
      const cacheKeys = keys.filter(key => key.startsWith(STORAGE_KEYS.CACHE_PREFIX));
      
      // Remove oldest cache entries
      cacheKeys.forEach(key => {
        try {
          this.storage.removeItem(key);
        } catch {
          // Ignore errors
        }
      });
    } catch {
      // Ignore errors
    }
  }
}

// Create safe storage instances
const safeLocalStorage = new SafeStorage(localStorage);
const safeSessionStorage = new SafeStorage(sessionStorage);

// Generic storage utilities
export const storage = {
  // Get item from storage
  get<T = unknown>(key: string, defaultValue?: T, useSession = false): T {
    const storageInstance = useSession ? safeSessionStorage : safeLocalStorage;
    const item = storageInstance.getItem(key);
    
    if (item === null) {
      return defaultValue as T;
    }
    
    try {
      return JSON.parse(item);
    } catch {
      return item as unknown as T;
    }
  },

  // Set item in storage
  set(key: string, value: unknown, useSession = false): void {
    const storageInstance = useSession ? safeSessionStorage : safeLocalStorage;
    const serializedValue = typeof value === 'string' ? value : JSON.stringify(value);
    storageInstance.setItem(key, serializedValue);
  },

  // Remove item from storage
  remove(key: string, useSession = false): void {
    const storageInstance = useSession ? safeSessionStorage : safeLocalStorage;
    storageInstance.removeItem(key);
  },

  // Clear all storage
  clear(useSession = false): void {
    const storageInstance = useSession ? safeSessionStorage : safeLocalStorage;
    storageInstance.clear();
  },

  // Check if key exists
  has(key: string, useSession = false): boolean {
    const storageInstance = useSession ? safeSessionStorage : safeLocalStorage;
    return storageInstance.getItem(key) !== null;
  },

  // Get all keys
  keys(useSession = false): string[] {
    const storageInstance = useSession ? safeSessionStorage : safeLocalStorage;
    try {
      return Object.keys(storageInstance.storage);
    } catch {
      return [];
    }
  },

  // Get storage size
  size(useSession = false): number {
    const storageInstance = useSession ? safeSessionStorage : safeLocalStorage;
    try {
      return JSON.stringify(storageInstance.storage).length;
    } catch {
      return 0;
    }
  },
};

// Authentication token utilities
export const tokenStorage = {
  getAccessToken(): string | null {
    return storage.get(STORAGE_KEYS.ACCESS_TOKEN);
  },

  setAccessToken(token: string): void {
    storage.set(STORAGE_KEYS.ACCESS_TOKEN, token);
  },

  getRefreshToken(): string | null {
    return storage.get(STORAGE_KEYS.REFRESH_TOKEN);
  },

  setRefreshToken(token: string): void {
    storage.set(STORAGE_KEYS.REFRESH_TOKEN, token);
  },

  clearTokens(): void {
    storage.remove(STORAGE_KEYS.ACCESS_TOKEN);
    storage.remove(STORAGE_KEYS.REFRESH_TOKEN);
  },

  hasValidTokens(): boolean {
    return !!(this.getAccessToken() && this.getRefreshToken());
  },
};

// User profile utilities
export const profileStorage = {
  getProfile(): Record<string, unknown> | null {
    return storage.get(STORAGE_KEYS.USER_PROFILE);
  },

  setProfile(profile: Record<string, unknown>): void {
    storage.set(STORAGE_KEYS.USER_PROFILE, profile);
  },

  clearProfile(): void {
    storage.remove(STORAGE_KEYS.USER_PROFILE);
  },
};

// Theme utilities
export const themeStorage = {
  getTheme(): string {
    return storage.get<string>(STORAGE_KEYS.THEME, 'system');
  },

  setTheme(theme: string): void {
    storage.set(STORAGE_KEYS.THEME, theme);
  },
};

// Settings utilities
export const settingsStorage = {
  getSettings(): Record<string, unknown> {
    return storage.get<Record<string, unknown>>(STORAGE_KEYS.SETTINGS, {});
  },

  setSettings(settings: Record<string, unknown>): void {
    storage.set(STORAGE_KEYS.SETTINGS, settings);
  },

  getSetting(key: string, defaultValue?: unknown): unknown {
    const settings = this.getSettings();
    return settings[key] ?? defaultValue;
  },

  setSetting(key: string, value: unknown): void {
    const settings = this.getSettings();
    settings[key] = value;
    this.setSettings(settings);
  },
};

// Cache utilities with TTL
export const cache = {
  set(key: string, data: unknown, ttl: number = CACHE.DEFAULT_TTL): void {
    const cacheKey = STORAGE_KEYS.CACHE_PREFIX + key;
    const cacheData = {
      data,
      timestamp: Date.now(),
      ttl,
    };
    storage.set(cacheKey, cacheData);
  },

  get<T = unknown>(key: string): T | null {
    const cacheKey = STORAGE_KEYS.CACHE_PREFIX + key;
    const cacheData = storage.get(cacheKey);
    
    if (!cacheData) {
      return null;
    }
    
    const { data, timestamp, ttl } = cacheData as { data: unknown; timestamp: number; ttl: number };
    const now = Date.now();
    
    if (now - timestamp > ttl) {
      this.remove(key);
      return null;
    }
    
    return data as T;
  },

  remove(key: string): void {
    const cacheKey = STORAGE_KEYS.CACHE_PREFIX + key;
    storage.remove(cacheKey);
  },

  clear(): void {
    const keys = storage.keys();
    keys.forEach(key => {
      if (key.startsWith(STORAGE_KEYS.CACHE_PREFIX)) {
        storage.remove(key);
      }
    });
  },

  has(key: string): boolean {
    return this.get(key) !== null;
  },

  // Get or set pattern
  getOrSet<T = unknown>(
    key: string,
    factory: () => T | Promise<T>,
    ttl: number = CACHE.DEFAULT_TTL
  ): T | Promise<T> {
    const cached = this.get(key) as T | null;
    if (cached !== null) {
      return cached;
    }
    
    const result = factory();
    
    if (result instanceof Promise) {
      return result.then(data => {
        this.set(key, data, ttl);
        return data;
      });
    } else {
      this.set(key, result, ttl);
      return result;
    }
  },
};

// Recent uploads utilities
export const recentUploadsStorage = {
  getRecentUploads(): Record<string, unknown>[] {
    return storage.get<Record<string, unknown>[]>(STORAGE_KEYS.RECENT_UPLOADS, []);
  },

  addRecentUpload(upload: Record<string, unknown>): void {
    const recent = this.getRecentUploads();
    const updated = [upload, ...recent.filter(item => item.id !== upload.id)].slice(0, 10);
    storage.set(STORAGE_KEYS.RECENT_UPLOADS, updated);
  },

  removeRecentUpload(uploadId: string): void {
    const recent = this.getRecentUploads();
    const updated = recent.filter(item => item.id !== uploadId);
    storage.set(STORAGE_KEYS.RECENT_UPLOADS, updated);
  },

  clearRecentUploads(): void {
    storage.remove(STORAGE_KEYS.RECENT_UPLOADS);
  },
};

// Sidebar state utilities
export const sidebarStorage = {
  isCollapsed(): boolean {
    return storage.get<boolean>(STORAGE_KEYS.SIDEBAR_COLLAPSED, false);
  },

  setCollapsed(collapsed: boolean): void {
    storage.set(STORAGE_KEYS.SIDEBAR_COLLAPSED, collapsed);
  },
};

// Language utilities
export const languageStorage = {
  getLanguage(): string {
    return storage.get<string>(STORAGE_KEYS.LANGUAGE, 'en');
  },

  setLanguage(language: string): void {
    storage.set(STORAGE_KEYS.LANGUAGE, language);
  },
};

// Cleanup utilities
export const cleanup = {
  // Remove expired cache entries
  cleanExpiredCache(): void {
    const keys = storage.keys();
    const now = Date.now();
    
    keys.forEach(key => {
      if (key.startsWith(STORAGE_KEYS.CACHE_PREFIX)) {
        const cacheData = storage.get(key);
        if (cacheData && typeof (cacheData as {timestamp?: number; ttl?: number}).timestamp === 'number' && typeof (cacheData as {timestamp?: number; ttl?: number}).ttl === 'number') {
          if (now - (cacheData as {timestamp: number; ttl: number}).timestamp > (cacheData as {timestamp: number; ttl: number}).ttl) {
            storage.remove(key);
          }
        }
      }
    });
  },

  // Remove all app data
  clearAllAppData(): void {
    Object.values(STORAGE_KEYS).forEach(key => {
      storage.remove(key);
    });
    cache.clear();
  },

  // Get storage usage info
  getStorageInfo(): {
    used: number;
    available: number;
    percentage: number;
  } {
    const used = storage.size();
    const available = 5 * 1024 * 1024; // Assume 5MB limit
    const percentage = (used / available) * 100;
    
    return { used, available, percentage };
  },
};

// Initialize cleanup on app start
if (typeof window !== 'undefined') {
  // Clean expired cache on app start
  cleanup.cleanExpiredCache();
  
  // Set up periodic cleanup
  setInterval(() => {
    cleanup.cleanExpiredCache();
  }, 60000); // Every minute
}