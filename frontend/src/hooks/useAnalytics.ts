import { useCallback, useMemo } from 'react';
import { useSelector } from 'react-redux';
import type { RootState } from '../store';

export interface AnalyticsEvent {
  name: string;
  properties?: Record<string, unknown>;
  userId?: string;
  timestamp?: number;
}

export interface AnalyticsConfig {
  enabled: boolean;
  debug: boolean;
  trackPageViews: boolean;
  trackUserInteractions: boolean;
}

const defaultConfig: AnalyticsConfig = {
  enabled: process.env.NODE_ENV === 'production',
  debug: process.env.NODE_ENV === 'development',
  trackPageViews: true,
  trackUserInteractions: true,
};

export const useAnalytics = (config: Partial<AnalyticsConfig> = {}) => {
  const user = useSelector((state: RootState) => state.auth.user);
  const finalConfig = useMemo(() => ({ ...defaultConfig, ...config }), [config]);

  const track = useCallback((event: AnalyticsEvent) => {
    if (!finalConfig.enabled) return;

    const eventData = {
      ...event,
      userId: event.userId || user?.id,
      timestamp: event.timestamp || Date.now(),
    };

    if (finalConfig.debug) {
      console.log('[Analytics]', eventData);
    }

    // In a real implementation, you would send this to your analytics service
    // For now, we'll just store it locally or send to a mock endpoint
    try {
      // Example: Send to analytics service
      // analyticsService.track(eventData);
      
      // For development, just log it
      if (finalConfig.debug) {
        console.group(`📊 Analytics Event: ${event.name}`);
        console.log('Properties:', event.properties);
        console.log('User ID:', eventData.userId);
        console.log('Timestamp:', new Date(eventData.timestamp).toISOString());
        console.groupEnd();
      }
    } catch (error) {
      if (finalConfig.debug) {
        console.error('[Analytics] Failed to track event:', error);
      }
    }
  }, [finalConfig, user?.id]);

  const trackPageView = useCallback((page: string, properties?: Record<string, unknown>) => {
    if (!finalConfig.trackPageViews) return;
    
    track({
      name: 'page_view',
      properties: {
        page,
        url: window.location.href,
        referrer: document.referrer,
        ...properties,
      },
    });
  }, [track, finalConfig.trackPageViews]);

  const trackUserAction = useCallback((action: string, properties?: Record<string, unknown>) => {
    if (!finalConfig.trackUserInteractions) return;
    
    track({
      name: 'user_action',
      properties: {
        action,
        ...properties,
      },
    });
  }, [track, finalConfig.trackUserInteractions]);

  const trackError = useCallback((error: Error, context?: Record<string, unknown>) => {
    track({
      name: 'error',
      properties: {
        error_message: error.message,
        error_stack: error.stack,
        error_name: error.name,
        ...context,
      },
    });
  }, [track]);

  const trackTiming = useCallback((name: string, duration: number, properties?: Record<string, unknown>) => {
    track({
      name: 'timing',
      properties: {
        timing_name: name,
        duration,
        ...properties,
      },
    });
  }, [track]);

  // Predefined event trackers for common actions
  const trackLogin = useCallback((method: string = 'email') => {
    track({
      name: 'login',
      properties: { method },
    });
  }, [track]);

  const trackLogout = useCallback(() => {
    track({
      name: 'logout',
    });
  }, [track]);

  const trackSignup = useCallback((method: string = 'email') => {
    track({
      name: 'signup',
      properties: { method },
    });
  }, [track]);

  const trackFileUpload = useCallback((filename: string, fileSize: number, fileType: string) => {
    track({
      name: 'file_upload',
      properties: {
        filename,
        file_size: fileSize,
        file_type: fileType,
      },
    });
  }, [track]);

  const trackProcessingStart = useCallback((filename: string, processingType: string) => {
    track({
      name: 'processing_start',
      properties: {
        filename,
        processing_type: processingType,
      },
    });
  }, [track]);

  const trackProcessingComplete = useCallback((filename: string, processingType: string, duration: number) => {
    track({
      name: 'processing_complete',
      properties: {
        filename,
        processing_type: processingType,
        duration,
      },
    });
  }, [track]);

  const trackApiKeyGenerated = useCallback((keyName: string) => {
    track({
      name: 'api_key_generated',
      properties: {
        key_name: keyName,
      },
    });
  }, [track]);

  return {
    track,
    trackPageView,
    trackUserAction,
    trackError,
    trackTiming,
    trackLogin,
    trackLogout,
    trackSignup,
    trackFileUpload,
    trackProcessingStart,
    trackProcessingComplete,
    trackApiKeyGenerated,
    config: finalConfig,
  };
};

export default useAnalytics;