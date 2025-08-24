// Notifications hook
import { useState, useCallback, useEffect, useRef } from 'react';
import type { UseNotificationsReturn } from './types';
import type { Notification } from './types';
import { UI_CONFIG } from '../config';

const useNotifications = (): UseNotificationsReturn => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const timeoutsRef = useRef<Map<string, NodeJS.Timeout>>(new Map());

  // Generate unique ID for notifications
  const generateId = useCallback((): string => {
    return `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  // Add notification
  const addNotification = useCallback((
    notification: Omit<Notification, 'id' | 'timestamp' | 'read'>
  ): string => {
    const id = generateId();
    const newNotification: Notification = {
      ...notification,
      id,
      timestamp: Date.now(),
      read: false,
    };

    setNotifications(prev => {
      // Limit the number of notifications
      const updated = [newNotification, ...prev];
      if (updated.length > UI_CONFIG.TOAST.MAX_TOASTS) {
        // Remove oldest notifications
        const toRemove = updated.slice(UI_CONFIG.TOAST.MAX_TOASTS);
        toRemove.forEach(notif => {
          const timeout = timeoutsRef.current.get(notif.id);
          if (timeout) {
            clearTimeout(timeout);
            timeoutsRef.current.delete(notif.id);
          }
        });
        return updated.slice(0, UI_CONFIG.TOAST.MAX_TOASTS);
      }
      return updated;
    });

    // Auto-remove notification after duration (unless persistent)
    if (!notification.persistent) {
      const timeout = setTimeout(() => {
        removeNotification(id);
      }, UI_CONFIG.TOAST.DURATION);
      
      timeoutsRef.current.set(id, timeout);
    }

    return id;
  }, [generateId]);

  // Remove notification
  const removeNotification = useCallback((id: string): void => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
    
    // Clear timeout if exists
    const timeout = timeoutsRef.current.get(id);
    if (timeout) {
      clearTimeout(timeout);
      timeoutsRef.current.delete(id);
    }
  }, []);

  // Clear all notifications
  const clearNotifications = useCallback((): void => {
    setNotifications([]);
    
    // Clear all timeouts
    timeoutsRef.current.forEach(timeout => clearTimeout(timeout));
    timeoutsRef.current.clear();
  }, []);

  // Mark notification as read
  const markAsRead = useCallback((id: string): void => {
    setNotifications(prev => 
      prev.map(notification => 
        notification.id === id 
          ? { ...notification, read: true }
          : notification
      )
    );
  }, []);

  // Mark all notifications as read
  const markAllAsRead = useCallback((): void => {
    setNotifications(prev => 
      prev.map(notification => ({ ...notification, read: true }))
    );
  }, []);

  // Get unread count
  const getUnreadCount = useCallback((): number => {
    return notifications.filter(notification => !notification.read).length;
  }, [notifications]);

  // Cleanup timeouts on unmount
  useEffect(() => {
    const timeouts = timeoutsRef.current;
    return () => {
      timeouts.forEach(timeout => clearTimeout(timeout));
      timeouts.clear();
    };
  }, []);

  return {
    notifications,
    addNotification,
    removeNotification,
    clearNotifications,
    markAsRead,
    markAllAsRead,
    getUnreadCount,
  };
};

// Singleton instance for global notifications
let globalNotificationsHook: UseNotificationsReturn | null = null;

export const useGlobalNotifications = (): UseNotificationsReturn => {
  if (!globalNotificationsHook) {
    // This will be initialized by the NotificationProvider
    throw new Error('useGlobalNotifications must be used within NotificationProvider');
  }
  return globalNotificationsHook;
};

export const setGlobalNotificationsHook = (hook: UseNotificationsReturn): void => {
  globalNotificationsHook = hook;
};

// Utility functions for common notification types
export const notificationUtils = {
  success: (title: string, message?: string, options?: Partial<Notification>) => ({
    type: 'success' as const,
    title,
    message,
    ...options,
  }),

  error: (title: string, message?: string, options?: Partial<Notification>) => ({
    type: 'error' as const,
    title,
    message,
    persistent: true, // Errors should be persistent by default
    ...options,
  }),

  warning: (title: string, message?: string, options?: Partial<Notification>) => ({
    type: 'warning' as const,
    title,
    message,
    ...options,
  }),

  info: (title: string, message?: string, options?: Partial<Notification>) => ({
    type: 'info' as const,
    title,
    message,
    ...options,
  }),

  // Specific notification types for the application
  uploadSuccess: (filename: string) => ({
    type: 'success' as const,
    title: 'Upload Successful',
    message: `${filename} has been uploaded successfully.`,
  }),

  uploadError: (filename: string, error: string) => ({
    type: 'error' as const,
    title: 'Upload Failed',
    message: `Failed to upload ${filename}: ${error}`,
    persistent: true,
  }),

  processingStarted: (filename: string) => ({
    type: 'info' as const,
    title: 'Processing Started',
    message: `Processing ${filename}...`,
  }),

  processingCompleted: (filename: string) => ({
    type: 'success' as const,
    title: 'Processing Completed',
    message: `${filename} has been processed successfully.`,
  }),

  processingFailed: (filename: string, error: string) => ({
    type: 'error' as const,
    title: 'Processing Failed',
    message: `Failed to process ${filename}: ${error}`,
    persistent: true,
  }),

  sessionExpiring: (onExtend: () => void) => ({
    type: 'warning' as const,
    title: 'Session Expiring',
    message: 'Your session will expire in 5 minutes.',
    persistent: true,
    action: {
      label: 'Extend Session',
      onClick: onExtend,
    },
  }),

  sessionExpired: () => ({
    type: 'error' as const,
    title: 'Session Expired',
    message: 'Your session has expired. Please log in again.',
    persistent: true,
  }),

  networkError: () => ({
    type: 'error' as const,
    title: 'Network Error',
    message: 'Unable to connect to the server. Please check your internet connection.',
    persistent: true,
  }),

  maintenanceMode: () => ({
    type: 'warning' as const,
    title: 'Maintenance Mode',
    message: 'The system is currently under maintenance. Some features may be unavailable.',
    persistent: true,
  }),

  newFeature: (feature: string) => ({
    type: 'info' as const,
    title: 'New Feature Available',
    message: `Check out the new ${feature} feature!`,
  }),

  quotaWarning: (percentage: number) => ({
    type: 'warning' as const,
    title: 'Quota Warning',
    message: `You have used ${percentage}% of your monthly quota.`,
    persistent: true,
  }),

  quotaExceeded: () => ({
    type: 'error' as const,
    title: 'Quota Exceeded',
    message: 'You have exceeded your monthly quota. Please upgrade your plan.',
    persistent: true,
  }),

  apiKeyCreated: (keyName: string) => ({
    type: 'success' as const,
    title: 'API Key Created',
    message: `API key "${keyName}" has been created successfully.`,
  }),

  apiKeyDeleted: (keyName: string) => ({
    type: 'info' as const,
    title: 'API Key Deleted',
    message: `API key "${keyName}" has been deleted.`,
  }),

  profileUpdated: () => ({
    type: 'success' as const,
    title: 'Profile Updated',
    message: 'Your profile has been updated successfully.',
  }),

  passwordChanged: () => ({
    type: 'success' as const,
    title: 'Password Changed',
    message: 'Your password has been changed successfully.',
  }),

  emailVerified: () => ({
    type: 'success' as const,
    title: 'Email Verified',
    message: 'Your email address has been verified successfully.',
  }),

  backupCompleted: () => ({
    type: 'success' as const,
    title: 'Backup Completed',
    message: 'Your data has been backed up successfully.',
  }),

  exportReady: (format: string, onDownload: () => void) => ({
    type: 'success' as const,
    title: 'Export Ready',
    message: `Your ${format} export is ready for download.`,
    action: {
      label: 'Download',
      onClick: onDownload,
    },
  }),
};

export default useNotifications;