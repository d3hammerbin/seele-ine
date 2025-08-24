// Async hook
import { useState, useCallback, useEffect, useRef } from 'react';
import type { UseAsyncReturn, AsyncState } from './types';

interface UseAsyncOptions<T> {
  immediate?: boolean;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
  resetOnExecute?: boolean;
}

const useAsync = <T = unknown, Args extends unknown[] = unknown[]>(
  asyncFunction: (...args: Args) => Promise<T>,
  options: UseAsyncOptions<T> = {}
): UseAsyncReturn<T, Args> => {
  const {
    immediate = false,
    onSuccess,
    onError,
    resetOnExecute = true,
  } = options;

  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    error: null,
    loading: false,
  });

  const mountedRef = useRef(true);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Set mounted to false on unmount
  useEffect(() => {
    return () => {
      mountedRef.current = false;
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // Execute function
  const execute = useCallback(async (...args: Args): Promise<T | null> => {
    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller
    abortControllerRef.current = new AbortController();

    // Reset state if needed
    if (resetOnExecute) {
      setState({
        data: null,
        error: null,
        loading: true,
      });
    } else {
      setState(prev => ({
        ...prev,
        loading: true,
        error: null,
      }));
    }

    try {
      const result = await asyncFunction(...args);
      
      // Only update state if component is still mounted
      if (mountedRef.current && !abortControllerRef.current.signal.aborted) {
        setState({
          data: result,
          error: null,
          loading: false,
        });
        
        onSuccess?.(result);
        return result;
      }
      
      return null;
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Unknown error occurred');
      
      // Only update state if component is still mounted and not aborted
      if (mountedRef.current && !abortControllerRef.current.signal.aborted) {
        setState({
          data: null,
          error: err,
          loading: false,
        });
        
        onError?.(err);
      }
      
      throw err;
    } finally {
      abortControllerRef.current = null;
    }
  }, [asyncFunction, resetOnExecute, onSuccess, onError]);

  // Reset state
  const reset = useCallback(() => {
    // Cancel ongoing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }

    setState({
      data: null,
      error: null,
      loading: false,
    });
  }, []);

  // Cancel ongoing request
  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }

    if (mountedRef.current) {
      setState(prev => ({
        ...prev,
        loading: false,
      }));
    }
  }, []);

  // Execute immediately if requested
  useEffect(() => {
    if (immediate) {
      execute(...([] as unknown as Args));
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    ...state,
    execute,
    reset,
    cancel,
  };
};

// Async utilities
export const asyncUtils = {
  // Create a delay function
  delay: (ms: number): Promise<void> => {
    return new Promise(resolve => setTimeout(resolve, ms));
  },

  // Retry function with exponential backoff
  retry: async <T>(
    fn: () => Promise<T>,
    options: {
      attempts?: number;
      delay?: number;
      backoff?: number;
      shouldRetry?: (error: Error, attempt: number) => boolean;
    } = {}
  ): Promise<T> => {
    const {
      attempts = 3,
      delay = 1000,
      backoff = 2,
      shouldRetry = () => true,
    } = options;

    let lastError: Error;

    for (let attempt = 1; attempt <= attempts; attempt++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error instanceof Error ? error : new Error('Unknown error');
        
        if (attempt === attempts || !shouldRetry(lastError, attempt)) {
          throw lastError;
        }

        // Wait before retrying
        const waitTime = delay * Math.pow(backoff, attempt - 1);
        await asyncUtils.delay(waitTime);
      }
    }

    throw lastError!;
  },

  // Timeout wrapper
  timeout: <T>(promise: Promise<T>, ms: number): Promise<T> => {
    return Promise.race([
      promise,
      new Promise<never>((_, reject) => {
        setTimeout(() => reject(new Error(`Operation timed out after ${ms}ms`)), ms);
      }),
    ]);
  },

  // Debounce async function
  debounce: <Args extends unknown[], Return>(
    fn: (...args: Args) => Promise<Return>,
    delay: number
  ) => {
    let timeoutId: NodeJS.Timeout;

    return (...args: Args): Promise<Return> => {
      return new Promise((resolve, reject) => {
        clearTimeout(timeoutId);
        
        timeoutId = setTimeout(async () => {
          try {
            const result = await fn(...args);
            resolve(result);
          } catch (error) {
            reject(error);
          }
        }, delay);
      });
    };
  },

  // Throttle async function
  throttle: <Args extends unknown[], Return>(
    fn: (...args: Args) => Promise<Return>,
    delay: number
  ) => {
    let lastExecution = 0;
    let timeoutId: NodeJS.Timeout | null = null;

    return (...args: Args): Promise<Return> => {
      return new Promise((resolve, reject) => {
        const now = Date.now();
        const timeSinceLastExecution = now - lastExecution;

        const executeFunction = async () => {
          lastExecution = Date.now();
          try {
            const result = await fn(...args);
            resolve(result);
          } catch (error) {
            reject(error);
          }
        };

        if (timeSinceLastExecution >= delay) {
          executeFunction();
        } else {
          if (timeoutId) {
            clearTimeout(timeoutId);
          }
          timeoutId = setTimeout(executeFunction, delay - timeSinceLastExecution);
        }
      });
    };
  },

  // Batch async operations
  batch: async <T>(
    operations: (() => Promise<T>)[],
    options: {
      concurrency?: number;
      failFast?: boolean;
    } = {}
  ): Promise<T[]> => {
    const { concurrency = 5, failFast = false } = options;
    
    if (concurrency >= operations.length) {
      // Run all operations concurrently
      if (failFast) {
        return Promise.all(operations.map(op => op()));
      } else {
        const results = await Promise.allSettled(operations.map(op => op()));
        return results.map(result => {
          if (result.status === 'fulfilled') {
            return result.value;
          } else {
            throw result.reason;
          }
        });
      }
    }

    // Run operations with limited concurrency
    const results: T[] = [];
    const executing: Promise<void>[] = [];
    
    for (let i = 0; i < operations.length; i++) {
      const operation = operations[i];
      
      const promise = operation().then(
        result => {
          results[i] = result;
        },
        error => {
          if (failFast) {
            throw error;
          }
          results[i] = error;
        }
      );
      
      executing.push(promise);
      
      if (executing.length >= concurrency) {
        await Promise.race(executing);
        executing.splice(executing.findIndex(p => p === promise), 1);
      }
    }
    
    await Promise.all(executing);
    return results;
  },

  // Create cancellable promise
  cancellable: <T>(promise: Promise<T>): {
    promise: Promise<T>;
    cancel: () => void;
  } => {
    let cancelled = false;
    
    const cancellablePromise = new Promise<T>((resolve, reject) => {
      promise.then(
        value => {
          if (!cancelled) {
            resolve(value);
          }
        },
        error => {
          if (!cancelled) {
            reject(error);
          }
        }
      );
    });
    
    return {
      promise: cancellablePromise,
      cancel: () => {
        cancelled = true;
      },
    };
  },

  // Memoize async function
  memoize: <Args extends unknown[], Return>(
    fn: (...args: Args) => Promise<Return>,
    options: {
      keyGenerator?: (...args: Args) => string;
      ttl?: number;
    } = {}
  ) => {
    const cache = new Map<string, { value: Return; timestamp: number }>();
    const { keyGenerator = (...args) => JSON.stringify(args), ttl } = options;

    return async (...args: Args): Promise<Return> => {
      const key = keyGenerator(...args);
      const cached = cache.get(key);
      
      if (cached) {
        if (!ttl || Date.now() - cached.timestamp < ttl) {
          return cached.value;
        } else {
          cache.delete(key);
        }
      }
      
      const result = await fn(...args);
      cache.set(key, { value: result, timestamp: Date.now() });
      return result;
    };
  },

  // Chain async operations
  chain: <T>(...operations: ((input: T) => Promise<T>)[]): ((input: T) => Promise<T>) => {
    return async (input: T): Promise<T> => {
      let result = input;
      for (const operation of operations) {
        result = await operation(result);
      }
      return result;
    };
  },

  // Parallel execution with results mapping
  parallel: async <T, R>(
    items: T[],
    mapper: (item: T, index: number) => Promise<R>,
    concurrency = 5
  ): Promise<R[]> => {
    const results: R[] = new Array(items.length);
    const executing: Promise<void>[] = [];
    
    for (let i = 0; i < items.length; i++) {
      const promise = mapper(items[i], i).then(result => {
        results[i] = result;
      });
      
      executing.push(promise);
      
      if (executing.length >= concurrency) {
        await Promise.race(executing);
        const completedIndex = executing.findIndex(p => p === promise);
        if (completedIndex !== -1) {
          executing.splice(completedIndex, 1);
        }
      }
    }
    
    await Promise.all(executing);
    return results;
  },
};

export default useAsync;