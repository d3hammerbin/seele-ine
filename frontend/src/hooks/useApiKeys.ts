// API Keys management hook
import { useState, useCallback, useEffect } from 'react';
import type { UseApiKeysReturn, ApiKeyItem, CreateApiKeyData, UpdateApiKeyData } from './types';
import { API_CONFIG } from '../config';
import useApi from './useApi';
import { apiClient } from '../utils/api';
import useAuth from './useAuth';
import useNotifications from './useNotifications';

interface UseApiKeysOptions {
  autoFetch?: boolean;
  enableRealTimeUpdates?: boolean;
}

const useApiKeys = (
  options: UseApiKeysOptions = {}
): UseApiKeysReturn => {
  const {
    autoFetch = true,
  } = options;

  const [apiKeys, setApiKeys] = useState<ApiKeyItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);


  const { user } = useAuth();
  const { execute: apiExecute } = useApi(async (config: any) => {
    return await apiClient.request(config);
  });
  const { addNotification } = useNotifications();

  // Fetch API keys
  const fetchApiKeys = useCallback(async () => {
    if (!user) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await apiExecute({
        url: API_CONFIG.ENDPOINTS.API_KEYS.LIST,
        method: 'GET',
      });

      setApiKeys((response as any)?.data?.apiKeys || []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch API keys';
      setError(errorMessage);
      console.error('API keys fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [user, apiExecute]);

  // Create new API key
  const createApiKey = useCallback(async (data: CreateApiKeyData): Promise<ApiKeyItem> => {
    if (!user) throw new Error('User not authenticated');

    setIsLoading(true);
    setError(null);

    try {
      const response = await apiExecute({
        url: API_CONFIG.ENDPOINTS.API_KEYS.CREATE,
        method: 'POST',
        data: {
          ...data,
          userId: user.id,
        },
      });

      const newApiKey = (response as any)?.data?.apiKey;
      setApiKeys(prev => [...prev, newApiKey]);

      addNotification({
        type: 'success',
        title: 'API Key Created',
        message: `API key "${data.name}" has been created successfully`,
        duration: 5000,
      });

      return newApiKey;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create API key';
      setError(errorMessage);
      
      addNotification({
        type: 'error',
        title: 'Creation Failed',
        message: errorMessage,
        duration: 8000,
      });
      
      console.error('API key creation error:', err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [user, apiExecute, addNotification]);

  // Update API key
  const updateApiKey = useCallback(async (id: string, data: UpdateApiKeyData): Promise<boolean> => {
    if (!user) return false;

    setIsLoading(true);
    setError(null);

    try {
      const response = await apiExecute({
        url: `${API_CONFIG.ENDPOINTS.API_KEYS.UPDATE.replace(':id', id)}`,
        method: 'PUT',
        data,
      });

      const updatedApiKey = (response as any)?.data?.apiKey;
      setApiKeys(prev => prev.map(key => key.id === id ? updatedApiKey : key));

      addNotification({
        type: 'success',
        title: 'API Key Updated',
        message: `API key "${updatedApiKey.name}" has been updated successfully`,
        duration: 5000,
      });

      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update API key';
      setError(errorMessage);
      
      addNotification({
        type: 'error',
        title: 'Update Failed',
        message: errorMessage,
        duration: 8000,
      });
      
      console.error('API key update error:', err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [user, apiExecute, addNotification]);

  // Delete API key
  const deleteApiKey = useCallback(async (id: string): Promise<boolean> => {
    if (!user) return false;

    const apiKey = apiKeys.find(key => key.id === id);
    if (!apiKey) return false;

    setIsLoading(true);
    setError(null);

    try {
      await apiExecute({
        url: `${API_CONFIG.ENDPOINTS.API_KEYS.DELETE.replace(':id', id)}`,
        method: 'DELETE',
      });

      setApiKeys(prev => prev.filter(key => key.id !== id));

      addNotification({
        type: 'success',
        title: 'API Key Deleted',
        message: `API key "${apiKey.name}" has been deleted successfully`,
        duration: 5000,
      });

      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete API key';
      setError(errorMessage);
      
      addNotification({
        type: 'error',
        title: 'Deletion Failed',
        message: errorMessage,
        duration: 8000,
      });
      
      console.error('API key deletion error:', err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [user, apiExecute, addNotification, apiKeys]);

  // Regenerate API key
  const regenerateApiKey = useCallback(async (id: string): Promise<string | null> => {
    if (!user) return null;

    const apiKey = apiKeys.find(key => key.id === id);
    if (!apiKey) return null;

    setIsLoading(true);
    setError(null);

    try {
      const response = await apiExecute({
        url: `${API_CONFIG.ENDPOINTS.API_KEYS.REGENERATE.replace(':id', id)}`,
        method: 'POST',
      });

      const { apiKey: updatedApiKey, newKey } = (response as any)?.data || {};
      setApiKeys(prev => prev.map(key => key.id === id ? updatedApiKey : key));

      addNotification({
        type: 'success',
        title: 'API Key Regenerated',
        message: `API key "${apiKey.name}" has been regenerated. Make sure to copy the new key!`,
        duration: 10000,
      });

      return newKey;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to regenerate API key';
      setError(errorMessage);
      
      addNotification({
        type: 'error',
        title: 'Regeneration Failed',
        message: errorMessage,
        duration: 8000,
      });
      
      console.error('API key regeneration error:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [user, apiExecute, addNotification, apiKeys]);

  // Toggle API key status (enable/disable)


  // Check if API key is expiring soon
  const isApiKeyExpiringSoon = useCallback((apiKey: ApiKeyItem, daysThreshold = 7): boolean => {
    if (!apiKey.expiresAt) return false;
    const expirationDate = new Date(apiKey.expiresAt);
    const thresholdDate = new Date();
    thresholdDate.setDate(thresholdDate.getDate() + daysThreshold);
    return expirationDate <= thresholdDate && expirationDate > new Date();
  }, []);



  // Auto-fetch API keys on mount
  useEffect(() => {
    if (autoFetch && user) {
      fetchApiKeys();
    }
  }, [autoFetch, user, fetchApiKeys]);

  // Check for expiring API keys
  useEffect(() => {
    const expiringKeys = apiKeys.filter(key => 
      key.isActive && isApiKeyExpiringSoon(key)
    );

    expiringKeys.forEach(key => {
      const daysUntilExpiration = Math.ceil(
        (new Date(key.expiresAt!).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24)
      );

      addNotification({
        type: 'warning',
        title: 'API Key Expiring Soon',
        message: `API key "${key.name}" will expire in ${daysUntilExpiration} day(s)`,
        duration: 10000,
      });
    });
  }, [apiKeys, isApiKeyExpiringSoon, addNotification]);

  return {
    apiKeys,
    isLoading,
    error,
    createApiKey,
    updateApiKey,
    deleteApiKey,
    regenerateApiKey,
    refreshApiKeys: fetchApiKeys,
  };
};

// API Keys utilities
export const apiKeysUtils = {
  // Generate API key name suggestions
  generateKeyNameSuggestions: (existingNames: string[]): string[] => {
    const baseSuggestions = [
      'Production API Key',
      'Development API Key',
      'Testing API Key',
      'Mobile App Key',
      'Web App Key',
      'Integration Key',
      'Backup Key',
    ];

    return baseSuggestions.filter(name => !existingNames.includes(name));
  },

  // Mask API key for display
  maskApiKey: (key: string): string => {
    if (key.length < 12) return key;
    return `${key.substring(0, 8)}...${key.substring(key.length - 4)}`;
  },

  // Get API key strength indicator
  getKeyStrength: (apiKey: ApiKeyItem): {
    score: number;
    level: 'weak' | 'medium' | 'strong';
    issues: string[];
  } => {
    const issues: string[] = [];
    let score = 100;

    // Check expiration
    if (!apiKey.expiresAt) {
      issues.push('No expiration date set');
      score -= 20;
    } else {
      const daysUntilExpiration = Math.ceil(
        (new Date(apiKey.expiresAt).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24)
      );
      if (daysUntilExpiration < 30) {
        issues.push('Expires soon');
        score -= 15;
      }
    }

    // Check permissions
    if (!apiKey.permissions || apiKey.permissions.length === 0) {
      issues.push('No specific permissions set');
      score -= 15;
    }

    // Check rate limits
    if (!apiKey.rateLimit) {
      issues.push('No rate limit configured');
      score -= 10;
    }

    // Check IP restrictions
    if (!apiKey.permissions || apiKey.permissions.length === 0) {
      issues.push('No IP restrictions');
      score -= 10;
    }

    // Check last used
    if (apiKey.lastUsedAt) {
      const daysSinceLastUse = Math.ceil(
        (new Date().getTime() - new Date(apiKey.lastUsedAt).getTime()) / (1000 * 60 * 60 * 24)
      );
      if (daysSinceLastUse > 90) {
        issues.push('Not used recently');
        score -= 10;
      }
    } else {
      issues.push('Never used');
      score -= 5;
    }

    const level = score >= 80 ? 'strong' : score >= 60 ? 'medium' : 'weak';
    
    return { score: Math.max(score, 0), level, issues };
  },

  // Format API key permissions
  formatPermissions: (permissions: string[]): string => {
    if (!permissions || permissions.length === 0) {
      return 'No specific permissions';
    }
    
    if (permissions.length === 1) {
      return permissions[0];
    }
    
    if (permissions.length <= 3) {
      return permissions.join(', ');
    }
    
    return `${permissions.slice(0, 2).join(', ')} and ${permissions.length - 2} more`;
  },

  // Calculate API key usage percentage
  calculateUsagePercentage: (used: number, limit: number): number => {
    if (limit === 0) return 0;
    return Math.min((used / limit) * 100, 100);
  },

  // Get usage status color
  getUsageStatusColor: (percentage: number): string => {
    if (percentage >= 90) return 'red';
    if (percentage >= 75) return 'orange';
    if (percentage >= 50) return 'yellow';
    return 'green';
  },

  // Format rate limit
  formatRateLimit: (rateLimit: { requests: number; period: string }): string => {
    return `${rateLimit.requests} requests per ${rateLimit.period}`;
  },

  // Validate API key permissions
  validatePermissions: (permissions: string[]): { isValid: boolean; errors: string[] } => {
    const validPermissions = [
      'credentials:read',
      'credentials:write',
      'credentials:process',
      'usage:read',
      'api_keys:read',
      'api_keys:write',
      'profile:read',
      'profile:write',
    ];
    
    const errors: string[] = [];
    const invalidPermissions = permissions.filter(p => !validPermissions.includes(p));
    
    if (invalidPermissions.length > 0) {
      errors.push(`Invalid permissions: ${invalidPermissions.join(', ')}`);
    }
    
    return {
      isValid: errors.length === 0,
      errors,
    };
  },

  // Generate API key statistics
  generateStatistics: (apiKeys: ApiKeyItem[]) => {
    const total = apiKeys.length;
    const active = apiKeys.filter(key => key.isActive).length;
    const inactive = apiKeys.filter(key => !key.isActive).length;
    const expired = apiKeys.filter(key => {
      return key.expiresAt && new Date(key.expiresAt) < new Date();
    }).length;
    
    const expiringSoon = apiKeys.filter(key => {
      if (!key.expiresAt) return false;
      const expirationDate = new Date(key.expiresAt);
      const thresholdDate = new Date();
      thresholdDate.setDate(thresholdDate.getDate() + 7);
      return expirationDate <= thresholdDate && expirationDate > new Date();
    }).length;
    
    const neverUsed = apiKeys.filter(key => !key.lastUsedAt).length;
    
    const totalRequests = apiKeys.reduce((sum, key) => sum + (key.usage?.totalRequests || 0), 0);
    const avgRequestsPerKey = total > 0 ? totalRequests / total : 0;
    
    return {
      total,
      active,
      inactive,
      expired,
      expiringSoon,
      neverUsed,
      totalRequests,
      avgRequestsPerKey,
    };
  },

  // Export API keys data
  exportApiKeys: (apiKeys: ApiKeyItem[], format: 'json' | 'csv' = 'json'): string => {
    if (format === 'json') {
      // Remove sensitive data before export
      const exportData = apiKeys.map(key => ({
        id: key.id,
        name: key.name,
        status: key.isActive ? 'active' : 'inactive',
        permissions: key.permissions,
        createdAt: key.createdAt,
        expiresAt: key.expiresAt,
        lastUsedAt: key.lastUsedAt,
        totalRequests: key.usage?.totalRequests || 0,
        rateLimit: key.rateLimit,
      }));
      
      return JSON.stringify(exportData, null, 2);
    }
    
    // CSV format
    const headers = [
      'ID', 'Name', 'Status', 'Permissions', 'Created At', 
      'Expires At', 'Last Used At', 'Total Requests'
    ];
    
    const rows = apiKeys.map(key => [
      key.id,
      key.name,
      key.isActive ? 'active' : 'inactive',
      key.permissions?.join(';') || '',
      key.createdAt,
      key.expiresAt || '',
      key.lastUsedAt || '',
      key.usage?.totalRequests?.toString() || '0',
    ]);
    
    return [headers, ...rows]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');
  },
};

export default useApiKeys;