// Re-export utilities without conflicts
export * from './api';
export * from './auth';
export * from './date';
export * from './file';
export * from './storage';
export * from './validation';
export { cn } from './cn';

// Export constants with alias to avoid HTTP_STATUS conflict
export { API_ENDPOINTS, STORAGE_KEYS, FILE_UPLOAD, CREDENTIAL_TYPES, PROCESSING_STATUS, EXTRACTION_METHODS, AI_PROVIDERS, TOAST_DURATION, ANIMATION_DURATION, BREAKPOINTS, Z_INDEX, VALIDATION, DATE_FORMATS, ERROR_MESSAGES, SUCCESS_MESSAGES, LOADING_MESSAGES, PAGINATION, CACHE, WS_EVENTS, FEATURES, ROUTES, EXTERNAL_LINKS, APP_METADATA } from './constants';
export { HTTP_STATUS as CONSTANTS_HTTP_STATUS } from './constants';

// Import and re-export with aliases to avoid naming conflicts
import * as CryptoUtils from './crypto';
import * as UrlUtils from './url';
import * as HelperUtils from './helpers';
import * as DeviceUtils from './device';
import * as ErrorUtils from './error';
import * as FormatUtils from './format';

// Export namespaced utilities
export { CryptoUtils, UrlUtils, HelperUtils, DeviceUtils, ErrorUtils, FormatUtils };

// Export specific utilities with aliases
export const cryptoHash = CryptoUtils.hash;
export const urlHashUtil = UrlUtils.urlHash;
export const helperUtils = HelperUtils.utils;
export const helperBrowser = HelperUtils.browser;
export const deviceBrowser = DeviceUtils.browser;
export const formatErrorUtil = FormatUtils.formatError;
export const errorFormatter = ErrorUtils.formatError;

// Common utility types
export type Nullable<T> = T | null;
export type Optional<T> = T | undefined;
export type Maybe<T> = T | null | undefined;

// Generic utility functions
export const noop = (): void => {};

export const identity = <T>(value: T): T => value;

export const delay = (ms: number): Promise<void> =>
  new Promise(resolve => setTimeout(resolve, ms));

export const debounce = <T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

export const throttle = <T extends (...args: unknown[]) => unknown>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean;
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
};

export const once = <T extends (...args: unknown[]) => unknown>(
  func: T
): ((...args: Parameters<T>) => ReturnType<T> | undefined) => {
  let called = false;
  let result: ReturnType<T> | undefined;
  return (...args: Parameters<T>) => {
    if (!called) {
      called = true;
      result = func(...args) as ReturnType<T>;
    }
    return result;
  };
};

// Object utilities
export const pick = <T extends Record<string, unknown>, K extends keyof T>(
  obj: T,
  keys: K[]
): Pick<T, K> => {
  const result = {} as Pick<T, K>;
  keys.forEach(key => {
    if (key in obj) {
      result[key] = obj[key];
    }
  });
  return result;
};

export const omit = <T extends Record<string, unknown>, K extends keyof T>(
  obj: T,
  keys: K[]
): Omit<T, K> => {
  const result = { ...obj };
  keys.forEach(key => {
    delete result[key];
  });
  return result;
};

export const deepClone = <T>(obj: T): T => {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj.getTime()) as unknown as T;
  if (obj instanceof Array) return obj.map(item => deepClone(item)) as unknown as T;
  if (typeof obj === 'object') {
    const clonedObj = {} as T;
    Object.keys(obj).forEach(key => {
      (clonedObj as Record<string, unknown>)[key] = deepClone((obj as Record<string, unknown>)[key]);
    });
    return clonedObj;
  }
  return obj;
};

export const isEmpty = (value: unknown): boolean => {
  if (value == null) return true;
  if (typeof value === 'string') return value.trim().length === 0;
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === 'object') return Object.keys(value).length === 0;
  return false;
};

export const isEqual = (a: unknown, b: unknown): boolean => {
  if (a === b) return true;
  if (a == null || b == null) return false;
  if (typeof a !== typeof b) return false;
  
  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) return false;
    return a.every((item, index) => isEqual(item, b[index]));
  }
  
  if (typeof a === 'object' && typeof b === 'object') {
    const objA = a as Record<string, unknown>;
    const objB = b as Record<string, unknown>;
    const keysA = Object.keys(objA);
    const keysB = Object.keys(objB);
    if (keysA.length !== keysB.length) return false;
    return keysA.every(key => isEqual(objA[key], objB[key]));
  }
  
  return false;
};

// Array utilities
export const unique = <T>(array: T[]): T[] => [...new Set(array)];

export const groupBy = <T, K extends keyof T>(
  array: T[],
  key: K
): Record<string, T[]> => {
  return array.reduce((groups, item) => {
    const groupKey = String(item[key]);
    if (!groups[groupKey]) {
      groups[groupKey] = [];
    }
    groups[groupKey].push(item);
    return groups;
  }, {} as Record<string, T[]>);
};

export const sortBy = <T>(
  array: T[],
  keyOrFn: keyof T | ((item: T) => unknown),
  order: 'asc' | 'desc' = 'asc'
): T[] => {
  const getValue = typeof keyOrFn === 'function' ? keyOrFn : (item: T) => item[keyOrFn];
  return [...array].sort((a, b) => {
    const valueA = getValue(a);
    const valueB = getValue(b);
    
    // Handle comparison of unknown types safely
    if (valueA == null && valueB == null) return 0;
    if (valueA == null) return -1;
    if (valueB == null) return 1;
    
    // Convert to string for comparison if not primitive
    const strA = typeof valueA === 'string' || typeof valueA === 'number' ? valueA : String(valueA);
    const strB = typeof valueB === 'string' || typeof valueB === 'number' ? valueB : String(valueB);
    
    const comparison = strA < strB ? -1 : strA > strB ? 1 : 0;
    return order === 'asc' ? comparison : -comparison;
  });
};

// String utilities
export const capitalize = (str: string): string =>
  str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();

export const camelCase = (str: string): string =>
  str.replace(/[-_\s]+(.)?/g, (_, char) => (char ? char.toUpperCase() : ''));

export const kebabCase = (str: string): string =>
  str.replace(/([a-z])([A-Z])/g, '$1-$2').toLowerCase();

export const snakeCase = (str: string): string =>
  str.replace(/([a-z])([A-Z])/g, '$1_$2').toLowerCase();

export const truncate = (str: string, length: number, suffix = '...'): string =>
  str.length <= length ? str : str.slice(0, length - suffix.length) + suffix;

// Number utilities
export const clamp = (value: number, min: number, max: number): number =>
  Math.min(Math.max(value, min), max);

export const random = (min: number, max: number): number =>
  Math.floor(Math.random() * (max - min + 1)) + min;

export const round = (value: number, decimals = 0): number => {
  const factor = Math.pow(10, decimals);
  return Math.round(value * factor) / factor;
};

// Promise utilities
export const sleep = (ms: number): Promise<void> =>
  new Promise(resolve => setTimeout(resolve, ms));

export const timeout = <T>(
  promise: Promise<T>,
  ms: number,
  errorMessage = 'Operation timed out'
): Promise<T> => {
  return Promise.race([
    promise,
    new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error(errorMessage)), ms)
    )
  ]);
};

export const retry = async <T>(
  fn: () => Promise<T>,
  attempts = 3,
  delay = 1000
): Promise<T> => {
  try {
    return await fn();
  } catch (error) {
    if (attempts <= 1) throw error;
    await sleep(delay);
    return retry(fn, attempts - 1, delay * 2);
  }
};

// Environment utilities
export const isDevelopment = (): boolean => import.meta.env.DEV;
export const isProduction = (): boolean => import.meta.env.PROD;
export const getEnvVar = (key: string, defaultValue?: string): string =>
  import.meta.env[key] || defaultValue || '';