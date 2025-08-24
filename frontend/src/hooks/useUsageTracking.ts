// Usage tracking hook
import { useState, useCallback, useEffect, useRef } from 'react';
import type { UsageData, UsageMetrics, CostBreakdown, UsageFilter } from './types';
import type { UseUsageTrackingReturn } from './types';
import { config } from '../config';
import useApi from './useApi';
import useAuth from './useAuth';
import useNotifications from './useNotifications';

interface UseUsageTrackingOptions {
  autoRefresh?: boolean;
  refreshInterval?: number;
  enableRealTimeUpdates?: boolean;
  warningThresholds?: {
    daily?: number;
    monthly?: number;
    quota?: number;
  };
}



const useUsageTracking = (
  options: UseUsageTrackingOptions = {}
): UseUsageTrackingReturn => {
  const {
    autoRefresh = true, // Re-enabled with proper dependency management
    refreshInterval = 60000, // 1 minute
    enableRealTimeUpdates = true, // Re-enabled with proper dependency management
    warningThresholds = {
      daily: 0.8, // 80% of daily limit
      monthly: 0.9, // 90% of monthly limit
      quota: 0.95, // 95% of quota
    },
  } = options;

  const [usageData, setUsageData] = useState<UsageData>({
    current: { requests: 0, tokens: 0, cost: 0, processingTime: 0, successfulRequests: 0, failedRequests: 0 },
    daily: { requests: 0, tokens: 0, cost: 0, processingTime: 0, successfulRequests: 0, failedRequests: 0 },
    monthly: { requests: 0, tokens: 0, cost: 0, processingTime: 0, successfulRequests: 0, failedRequests: 0 },
    total: { requests: 0, tokens: 0, cost: 0, processingTime: 0, successfulRequests: 0, failedRequests: 0 }
  });

  const [metrics, setMetrics] = useState<UsageMetrics>({
    averageRequestTime: 0,
    successRate: 0,
    costPerRequest: 0,
    tokensPerRequest: 0,
    peakUsageHour: 0,
    mostUsedProvider: '',
    mostUsedFeature: '',
    trendsData: [],
    totalRequests: 0,
    successfulRequests: 0,
    failedRequests: 0,
    totalCost: 0,
    providerBreakdown: {},
  });

  const [costBreakdown, setCostBreakdown] = useState<CostBreakdown>({
    byProvider: {},
    byFeature: {},
    byTimeOfDay: {},
    byDate: {},
    predictions: {
      dailyEstimate: 0,
      monthlyEstimate: 0,
      yearlyEstimate: 0
    }
  });

  const [usage] = useState<Array<{ requests: number; date: string }>>([]);
  const [costs] = useState<Array<{ totalCost: number; date: string }>>([]);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const { user } = useAuth();
  const { execute: apiExecute } = useApi(() => Promise.resolve({}));
  const { addNotification } = useNotifications();
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const warningsShownRef = useRef<Set<string>>(new Set());
  const fetchUsageDataRef = useRef<(() => Promise<void>) | null>(null);
  const addNotificationRef = useRef(addNotification);
  const exportUsageDataRef = useRef<any>(null);
  const checkUsageWarningsRef = useRef<((data: UsageData) => void) | null>(null);
  const enableRealTimeUpdatesRef = useRef(enableRealTimeUpdates);
  const resetWarningsRef = useRef<(() => void) | null>(null);

  // Check usage warnings - using current usage data as parameter to avoid dependency cycle
  const checkUsageWarnings = useCallback((currentUsageData: UsageData) => {
    const { daily, monthly } = currentUsageData;
    const userLimits = user?.limits;

    // Daily limit warning
    if (userLimits?.dailyRequests && warningThresholds.daily) {
      const dailyUsagePercent = daily.requests / userLimits.dailyRequests;
      if (dailyUsagePercent >= warningThresholds.daily && !warningsShownRef.current.has('daily')) {
        addNotificationRef.current({
          type: 'warning',
          title: 'Daily Usage Warning',
          message: `You've used ${(dailyUsagePercent * 100).toFixed(1)}% of your daily request limit`,
          persistent: true,
        });
        warningsShownRef.current.add('daily');
      }
    }

    // Monthly limit warning
    if (userLimits?.monthlyRequests && warningThresholds.monthly) {
      const monthlyUsagePercent = monthly.requests / userLimits.monthlyRequests;
      if (monthlyUsagePercent >= warningThresholds.monthly && !warningsShownRef.current.has('monthly')) {
        addNotificationRef.current({
          type: 'warning',
          title: 'Monthly Usage Warning',
          message: `You've used ${(monthlyUsagePercent * 100).toFixed(1)}% of your monthly request limit`,
          persistent: true,
        });
        warningsShownRef.current.add('monthly');
      }
    }

    // Cost warning
    if (userLimits?.monthlyCost && warningThresholds.quota) {
      const costUsagePercent = monthly.cost / userLimits.monthlyCost;
      if (costUsagePercent >= warningThresholds.quota && !warningsShownRef.current.has('cost')) {
        addNotificationRef.current({
          type: 'error',
          title: 'Cost Limit Warning',
          message: `You've used ${(costUsagePercent * 100).toFixed(1)}% of your monthly cost limit`,
          persistent: true,
        });
        warningsShownRef.current.add('cost');
      }
    }
  }, []);

  // Update the ref whenever checkUsageWarnings changes
  checkUsageWarningsRef.current = checkUsageWarnings;
  
  // Update enableRealTimeUpdates ref
  enableRealTimeUpdatesRef.current = enableRealTimeUpdates;

  // Fetch usage data
  const fetchUsageData = useCallback(async (filter?: UsageFilter) => {
    if (!user) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await apiExecute({
        url: config.api.ENDPOINTS.USAGE.CURRENT,
        method: 'GET',
        params: filter,
      });

      const newUsageData = (response as any)?.data?.usage || {
        current: { requests: 0, tokens: 0, cost: 0, processingTime: 0, successfulRequests: 0, failedRequests: 0 },
        daily: { requests: 0, tokens: 0, cost: 0, processingTime: 0, successfulRequests: 0, failedRequests: 0 },
        monthly: { requests: 0, tokens: 0, cost: 0, processingTime: 0, successfulRequests: 0, failedRequests: 0 },
        total: { requests: 0, tokens: 0, cost: 0, processingTime: 0, successfulRequests: 0, failedRequests: 0 }
      };
      
      setUsageData(newUsageData);
      setMetrics((response as any)?.data?.metrics);
      setCostBreakdown((response as any)?.data?.costBreakdown || {
        byProvider: {},
        byFeature: {},
        byTimeOfDay: {},
        byDate: {},
        predictions: {
          dailyEstimate: 0,
          monthlyEstimate: 0,
          yearlyEstimate: 0
        }
      });
      setLastUpdated(new Date());

      // Check for warnings with the new usage data
      checkUsageWarningsRef.current?.(newUsageData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch usage data';
      setError(errorMessage);
      console.error('Usage tracking error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [user, apiExecute]);

  // Update refs directly without useEffect to avoid re-renders
  fetchUsageDataRef.current = fetchUsageData;
  addNotificationRef.current = addNotification;

  // Track usage event
  const trackUsage = useCallback(async (event: {
    type: 'request' | 'processing' | 'upload' | 'download';
    provider?: string;
    feature?: string;
    tokens?: number;
    cost?: number;
    processingTime?: number;
    success?: boolean;
    metadata?: Record<string, unknown>;
  }) => {
    if (!user) return;

    try {
      await apiExecute({
        url: config.api.ENDPOINTS.USAGE.TRACK,
        method: 'POST',
        data: {
          ...event,
          timestamp: new Date().toISOString(),
          userId: user.id,
        },
      });

      // Update local usage data if real-time updates are enabled
      if (enableRealTimeUpdatesRef.current) {
        setUsageData(prev => ({
          ...prev,
          current: {
            ...prev.current,
            requests: prev.current.requests + 1,
            tokens: prev.current.tokens + (event.tokens || 0),
            cost: prev.current.cost + (event.cost || 0),
            processingTime: prev.current.processingTime + (event.processingTime || 0),
            successfulRequests: prev.current.successfulRequests + (event.success ? 1 : 0),
            failedRequests: prev.current.failedRequests + (event.success === false ? 1 : 0),
          },
        }));
      }
    } catch (err) {
      console.error('Failed to track usage:', err);
    }
  }, [user, apiExecute]);

  // Get usage history
  const getUsageHistory = useCallback(async (filter: {
    startDate?: Date;
    endDate?: Date;
    provider?: string;
    feature?: string;
    groupBy?: 'hour' | 'day' | 'week' | 'month';
  } = {}) => {
    if (!user) return [];

    try {
      const response = await apiExecute({
        url: config.api.ENDPOINTS.USAGE.HISTORY,
        method: 'GET',
        params: {
          ...filter,
          startDate: filter.startDate?.toISOString(),
          endDate: filter.endDate?.toISOString(),
        },
      });

      return (response as any)?.data?.history || [];
    } catch (err) {
      console.error('Failed to fetch usage history:', err);
      return [];
    }
  }, [user, apiExecute]);

  // Export usage data
  const exportUsageData = useCallback(async (format: 'json' | 'csv' | 'pdf' = 'json', filter?: UsageFilter) => {
    if (!user) return null;

    try {
      const response = await apiExecute({
        url: config.api.ENDPOINTS.USAGE.EXPORT,
        method: 'POST',
        data: { format, filter },
        responseType: format === 'pdf' ? 'blob' : 'json',
      });

      if (format === 'pdf') {
        // Create download link for PDF
        const blob = new Blob([(response as any)?.data], { type: 'application/pdf' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `usage-report-${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        return null;
      }

      return (response as any)?.data;
    } catch (err) {
      console.error('Failed to export usage data:', err);
      addNotificationRef.current({
        type: 'error',
        title: 'Export Failed',
        message: 'Failed to export usage data',
      });
      return null;
    }
  }, [user, apiExecute]);

  // Initialize the ref
  exportUsageDataRef.current = exportUsageData;

  // Reset usage warnings
  const resetWarnings = useCallback(() => {
    warningsShownRef.current.clear();
  }, []);

  // Update resetWarnings ref
  resetWarningsRef.current = resetWarnings;

  // Get usage percentage - simplified to avoid re-renders
  const getUsagePercentage = useCallback((type: 'daily' | 'monthly', metric: 'requests' | 'cost' | 'tokens') => {
    if (!user?.limits) return 0;

    const usage = type === 'daily' ? usageData.daily : usageData.monthly;
    const limit = type === 'daily' 
      ? (metric === 'requests' ? user.limits?.dailyRequests : user.limits?.monthlyCost)
      : (metric === 'requests' ? user.limits?.monthlyRequests : user.limits?.monthlyCost);

    if (!limit) return 0;

    const value = metric === 'requests' ? usage.requests : 
                  metric === 'cost' ? usage.cost : usage.tokens;
    
    return Math.min((value / limit) * 100, 100);
  }, [user, usageData]);

  // Check if limit is exceeded - simplified to avoid re-renders
  const isLimitExceeded = useCallback((type: 'daily' | 'monthly', metric: 'requests' | 'cost' | 'tokens') => {
    if (!user?.limits) return false;

    const usage = type === 'daily' ? usageData.daily : usageData.monthly;
    const limit = type === 'daily' 
      ? (metric === 'requests' ? user.limits?.dailyRequests : user.limits?.monthlyCost)
      : (metric === 'requests' ? user.limits?.monthlyRequests : user.limits?.monthlyCost);

    if (!limit) return false;

    const value = metric === 'requests' ? usage.requests : 
                  metric === 'cost' ? usage.cost : usage.tokens;
    
    return value >= limit;
  }, [user, usageData]);

  // Get remaining quota - simplified to avoid re-renders
  const getRemainingQuota = useCallback((type: 'daily' | 'monthly', metric: 'requests' | 'cost' | 'tokens') => {
    if (!user?.limits) return 0;

    const usage = type === 'daily' ? usageData.daily : usageData.monthly;
    const limit = type === 'daily' 
      ? (metric === 'requests' ? user.limits?.dailyRequests : user.limits?.monthlyCost)
      : (metric === 'requests' ? user.limits?.monthlyRequests : user.limits?.monthlyCost);

    if (!limit) return Infinity;

    const value = metric === 'requests' ? usage.requests : 
                  metric === 'cost' ? usage.cost : usage.tokens;
    
    return Math.max(limit - value, 0);
  }, [user, usageData]);

  // Setup auto-refresh - Fixed to prevent re-renders
  useEffect(() => {
    if (autoRefresh && user) {
      // Initial fetch
      fetchUsageDataRef.current?.();
      
      refreshIntervalRef.current = setInterval(() => {
        if (fetchUsageDataRef.current) {
          fetchUsageDataRef.current();
        }
      }, refreshInterval);

      return () => {
        if (refreshIntervalRef.current) {
          clearInterval(refreshIntervalRef.current);
        }
      };
    }
  }, [autoRefresh, refreshInterval]); // Removed user from dependencies to prevent re-renders

  // Reset warnings daily - Re-enabled with proper dependency management
  useEffect(() => {
    const now = new Date();
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(0, 0, 0, 0);
    
    const msUntilMidnight = tomorrow.getTime() - now.getTime();
    
    const timeout = setTimeout(() => {
      resetWarningsRef.current?.();
      
      // Set up daily reset
      const dailyReset = setInterval(() => {
        resetWarningsRef.current?.();
      }, 24 * 60 * 60 * 1000);
      
      return () => clearInterval(dailyReset);
    }, msUntilMidnight);
    
    return () => clearTimeout(timeout);
  }, []);

  // Create stable fetchUsageData function
  const stableFetchUsageData = useCallback(async () => {
    if (fetchUsageDataRef.current) {
      return fetchUsageDataRef.current();
    }
    return Promise.resolve();
  }, []);

  return {
    usageData,
    metrics,
    costBreakdown,
    isLoading,
    error,
    lastUpdated,
    usage,
    costs,
    loading: isLoading,
    fetchUsageData: stableFetchUsageData,
    trackUsage,
    getUsageHistory,
    exportUsageData,
    fetchUsage: useCallback((): Promise<void> => {
      return fetchUsageDataRef.current?.() ?? Promise.resolve();
    }, []),
    fetchMetrics: useCallback((): Promise<void> => {
      return fetchUsageDataRef.current?.() ?? Promise.resolve();
    }, []),
    fetchCosts: useCallback((): Promise<void> => {
      return fetchUsageDataRef.current?.() ?? Promise.resolve();
    }, []),
    exportData: useCallback((options?: { period?: string; format?: string; includeMetrics?: boolean; includeCosts?: boolean }) => {
      const format = (options?.format as 'json' | 'csv' | 'pdf') || 'json';
      const usageFilter: UsageFilter = {};
      if (options?.period) {
        // Convert period to date range if needed
      }
      return exportUsageDataRef.current?.(format, usageFilter);
    }, []),
    resetWarnings,
    getUsagePercentage,
    isLimitExceeded,
    getRemainingQuota,
  };
};

// Usage tracking utilities
export const usageUtils = {
  // Format cost
  formatCost: (cost: number, currency = 'USD'): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 4,
    }).format(cost);
  },

  // Format number with commas
  formatNumber: (num: number): string => {
    return new Intl.NumberFormat('en-US').format(num);
  },

  // Format processing time
  formatProcessingTime: (milliseconds: number): string => {
    if (milliseconds < 1000) {
      return `${milliseconds}ms`;
    }
    
    const seconds = milliseconds / 1000;
    if (seconds < 60) {
      return `${seconds.toFixed(1)}s`;
    }
    
    const minutes = seconds / 60;
    if (minutes < 60) {
      return `${minutes.toFixed(1)}m`;
    }
    
    const hours = minutes / 60;
    return `${hours.toFixed(1)}h`;
  },

  // Calculate success rate
  calculateSuccessRate: (successful: number, failed: number): number => {
    const total = successful + failed;
    return total > 0 ? (successful / total) * 100 : 0;
  },

  // Calculate average cost per request
  calculateCostPerRequest: (totalCost: number, totalRequests: number): number => {
    return totalRequests > 0 ? totalCost / totalRequests : 0;
  },

  // Calculate tokens per request
  calculateTokensPerRequest: (totalTokens: number, totalRequests: number): number => {
    return totalRequests > 0 ? totalTokens / totalRequests : 0;
  },

  // Get usage trend
  getUsageTrend: (current: number, previous: number): {
    percentage: number;
    direction: 'up' | 'down' | 'stable';
  } => {
    if (previous === 0) {
      return { percentage: current > 0 ? 100 : 0, direction: 'stable' };
    }
    
    const percentage = ((current - previous) / previous) * 100;
    const direction = percentage > 5 ? 'up' : percentage < -5 ? 'down' : 'stable';
    
    return { percentage: Math.abs(percentage), direction };
  },

  // Predict monthly usage
  predictMonthlyUsage: (dailyAverage: number, daysInMonth = 30): number => {
    return dailyAverage * daysInMonth;
  },

  // Get peak usage hour
  getPeakUsageHour: (hourlyData: Record<string, number>): number => {
    let maxHour = 0;
    let maxUsage = 0;
    
    Object.entries(hourlyData).forEach(([hour, usage]) => {
      if (usage > maxUsage) {
        maxUsage = usage;
        maxHour = parseInt(hour);
      }
    });
    
    return maxHour;
  },

  // Generate usage report
  generateUsageReport: (usageData: UsageData, metrics: UsageMetrics, costBreakdown: CostBreakdown) => {
    const report = {
      summary: {
        totalRequests: usageData.total.requests,
        totalCost: usageData.total.cost,
        totalTokens: usageData.total.tokens,
        successRate: metrics.successRate,
        averageRequestTime: metrics.averageRequestTime,
      },
      daily: {
        requests: usageData.daily.requests,
        cost: usageData.daily.cost,
        tokens: usageData.daily.tokens,
      },
      monthly: {
        requests: usageData.monthly.requests,
        cost: usageData.monthly.cost,
        tokens: usageData.monthly.tokens,
      },
      breakdown: {
        byProvider: costBreakdown.byProvider,
        byFeature: costBreakdown.byFeature,
      },
      predictions: costBreakdown.predictions,
      generatedAt: new Date().toISOString(),
    };
    
    return report;
  },

  // Create usage chart data
  createChartData: (trendsData: Record<string, unknown>[], metric: 'requests' | 'cost' | 'tokens') => {
    return trendsData.map(item => ({
      date: item.date,
      value: item[metric] || 0,
    }));
  },

  // Calculate cost efficiency
  calculateCostEfficiency: (successfulRequests: number, totalCost: number): number => {
    return successfulRequests > 0 ? totalCost / successfulRequests : 0;
  },

  // Get usage status color
  getUsageStatusColor: (percentage: number): string => {
    if (percentage >= 95) return 'red';
    if (percentage >= 80) return 'orange';
    if (percentage >= 60) return 'yellow';
    return 'green';
  },

  // Format usage percentage
  formatUsagePercentage: (percentage: number): string => {
    return `${Math.min(percentage, 100).toFixed(1)}%`;
  },
};

export default useUsageTracking;