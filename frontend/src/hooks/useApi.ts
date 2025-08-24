// API hook for making HTTP requests
import { useState, useCallback, useRef, useEffect } from 'react';
import { apiClient } from '../utils/api';
import type { UseApiReturn, UseApiOptions } from './types';
import useNotifications from './useNotifications';
import { apiUtils } from '../utils/api';

const useApi = <T = unknown>(
  apiFunction: (...args: unknown[]) => Promise<unknown>,
  options: UseApiOptions = {}
): UseApiReturn<T> => {
  const {
    immediate = false,
    onSuccess,
    onError,
    retries = 0,
    retryDelay = 1000,
  } = options;

  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const { addNotification } = useNotifications();
  const abortControllerRef = useRef<AbortController | null>(null);
  const mountedRef = useRef(true);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      mountedRef.current = false;
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // Execute API call
  const execute = useCallback(async (...args: unknown[]): Promise<T> => {
    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller
    abortControllerRef.current = new AbortController();

    if (!mountedRef.current) return null as T;

    setLoading(true);
    setError(null);

    try {
      // Execute with retry logic
      const result = await apiUtils.retryRequest(
        () => apiFunction(...args),
        {
          maxRetries: retries,
          baseDelay: retryDelay,
          shouldRetry: (error) => {
            // Don't retry on abort or auth errors
            if ((error as any).name === 'AbortError') return false;
            if (apiUtils.isAuthError(error)) return false;
            if (apiUtils.isAuthorizationError(error)) return false;
            return apiUtils.isNetworkError(error);
          },
        }
      );

      if (!mountedRef.current) return null as T;

      // Extract data from API response
      const responseData = (result as any)?.data || result;
      setData(responseData);

      // Call success callback
      if (onSuccess) {
        onSuccess(responseData);
      }

      return responseData;
    } catch (err: unknown) {
      if (!mountedRef.current) return null as T;

      // Don't handle aborted requests
      if ((err as any).name === 'AbortError') {
        return null as T;
      }

      const errorMessage = apiUtils.parseErrorResponse(err).message;
      setError(errorMessage);

      // Call error callback
      if (onError) {
        onError(err);
      } else {
        // Show error notification if no custom error handler
        addNotification({
          type: 'error',
          title: 'Request Failed',
          message: errorMessage,
        });
      }

      throw err;
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
      abortControllerRef.current = null;
    }
  }, [apiFunction, retries, retryDelay, onSuccess, onError, addNotification]);

  // Reset state
  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  // Cancel current request
  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setLoading(false);
  }, []);

  // Execute immediately if requested
  useEffect(() => {
    if (immediate) {
      execute().catch(() => {
        // Error is already handled in execute function
      });
    }
  }, [immediate, execute]);

  return {
    data,
    loading,
    error,
    execute,
    reset,
    cancel,
  };
};

// Specialized hooks for common API patterns

// Hook for GET requests
export const useApiGet = <T = unknown>(
  endpoint: string,
  options: UseApiOptions & { params?: Record<string, unknown> } = {}
): UseApiReturn<T> => {
  const { params, ...apiOptions } = options;
  
  return useApi<T>(
    () => apiClient.get<T>(`${endpoint}${params ? '?' + new URLSearchParams(params as Record<string, string>).toString() : ''}`),
    apiOptions
  );
};

// Hook for POST requests
export const useApiPost = <T = unknown, D = unknown>(
  endpoint: string,
  options: UseApiOptions = {}
): UseApiReturn<T> & { post: (data: D) => Promise<T> } => {
  const apiHook = useApi<T>(
    (...args: unknown[]) => {
      const data = args[0] as D;
      return apiClient.post<T>(endpoint, data);
    },
    options
  );

  const post = useCallback(
    (data: D) => apiHook.execute(data),
    [apiHook]
  );

  return {
    ...apiHook,
    post,
  };
};

// Hook for PUT requests
export const useApiPut = <T = unknown, D = unknown>(
  endpoint: string,
  options: UseApiOptions = {}
): UseApiReturn<T> & { put: (data: D) => Promise<T> } => {
  const apiHook = useApi<T>(
    (...args: unknown[]) => {
      const data = args[0] as D;
      return apiClient.put<T>(endpoint, data);
    },
    options
  );

  const put = useCallback(
    (data: D) => apiHook.execute(data),
    [apiHook]
  );

  return {
    ...apiHook,
    put,
  };
};

// Hook for DELETE requests
export const useApiDelete = <T = unknown>(
  endpoint: string,
  options: UseApiOptions = {}
): UseApiReturn<T> & { del: (id?: string) => Promise<T> } => {
  const apiHook = useApi<T>(
    (...args: unknown[]) => {
      const id = args[0] as string | undefined;
      const url = id ? `${endpoint}/${id}` : endpoint;
      return apiClient.delete<T>(url);
    },
    options
  );

  const del = useCallback(
    (id?: string) => apiHook.execute(id),
    [apiHook]
  );

  return {
    ...apiHook,
    del,
  };
};

// Hook for file uploads
export const useApiUpload = <T = unknown>(
  endpoint: string,
  options: UseApiOptions & {
    fieldName?: string;
    additionalData?: Record<string, unknown>;
    onProgress?: (progress: number) => void;
  } = {}
): UseApiReturn<T> & { upload: (file: File) => Promise<T> } => {
  const { fieldName, additionalData, onProgress, ...apiOptions } = options;
  
  const apiHook = useApi<T>(
    (...args: unknown[]) => {
      const file = args[0] as File;
      return apiClient.upload<T>(endpoint, file, {
        fieldName,
        additionalData,
        onProgress,
      });
    },
    apiOptions
  );

  const upload = useCallback(
    (file: File) => apiHook.execute(file),
    [apiHook]
  );

  return {
    ...apiHook,
    upload,
  };
};

// Hook for paginated requests
export const useApiPaginated = <T = unknown>(
  endpoint: string,
  options: UseApiOptions & {
    initialPage?: number;
    initialPageSize?: number;
    params?: Record<string, unknown>;
  } = {}
) => {
  const {
    initialPage = 1,
    initialPageSize = 20,
    params = {},
    ...apiOptions
  } = options;

  const [page, setPage] = useState(initialPage);
  const [pageSize, setPageSize] = useState(initialPageSize);
  const [allData, setAllData] = useState<T[]>([]);
  const [hasMore, setHasMore] = useState(true);
  const [total, setTotal] = useState(0);

  const apiHook = useApi(
    (...args: unknown[]) => {
      const currentPage = args[0] as number;
      const currentPageSize = args[1] as number;
      const url = `${endpoint}?page=${currentPage}&limit=${currentPageSize}${params ? '&' + new URLSearchParams(params as Record<string, string>).toString() : ''}`;
       return apiClient.get(url);
    },
    {
      ...apiOptions,
      onSuccess: (response) => {
        const { data, meta } = response as any;
        
        if (page === 1) {
          setAllData(data);
        } else {
          setAllData(prev => [...prev, ...data]);
        }
        
        setTotal(meta?.total || 0);
        setHasMore(page < (meta?.totalPages || 1));
        
        if (apiOptions.onSuccess) {
          apiOptions.onSuccess(response);
        }
      },
    }
  );

  const loadPage = useCallback(
    (targetPage: number) => {
      setPage(targetPage);
      return apiHook.execute(targetPage, pageSize);
    },
    [apiHook, pageSize]
  );

  const loadMore = useCallback(() => {
    if (hasMore && !apiHook.loading) {
      return loadPage(page + 1);
    }
    return Promise.resolve();
  }, [hasMore, apiHook.loading, loadPage, page]);

  const refresh = useCallback(() => {
    setAllData([]);
    return loadPage(1);
  }, [loadPage]);

  const changePageSize = useCallback(
    (newPageSize: number) => {
      setPageSize(newPageSize);
      setAllData([]);
      return loadPage(1);
    },
    [loadPage]
  );

  return {
    data: allData,
    loading: apiHook.loading,
    error: apiHook.error,
    page,
    pageSize,
    total,
    hasMore,
    loadPage,
    loadMore,
    refresh,
    changePageSize,
    reset: () => {
      setAllData([]);
      setPage(initialPage);
      setPageSize(initialPageSize);
      setHasMore(true);
      setTotal(0);
      apiHook.reset();
    },
    cancel: apiHook.cancel,
  };
};

// Hook for infinite scroll
export const useApiInfiniteScroll = <T = unknown>(
  endpoint: string,
  options: UseApiOptions & {
    pageSize?: number;
    params?: Record<string, unknown>;
    threshold?: number;
  } = {}
) => {
  const { threshold = 100, ...paginatedOptions } = options;
  const paginatedHook = useApiPaginated<T>(endpoint, paginatedOptions);
  
  // Auto-load more when scrolling near bottom
  useEffect(() => {
    const handleScroll = () => {
      if (
        window.innerHeight + window.scrollY >= 
        document.documentElement.offsetHeight - threshold &&
        paginatedHook.hasMore &&
        !paginatedHook.loading
      ) {
        paginatedHook.loadMore();
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [paginatedHook, threshold]);

  return paginatedHook;
};

export default useApi;