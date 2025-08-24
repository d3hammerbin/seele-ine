// Credential processing hook
import { useState, useCallback, useRef, useEffect } from 'react';
// Define the return type for this hook
interface UseCredentialProcessingReturn {
  jobs: ProcessingJob[];
  isProcessing: boolean;
  totalJobs: number;
  completedJobs: number;
  failedJobs: number;
  currentJob: ProcessingJob | null;
  progress: number;
  estimatedTimeRemaining: number | null;
  processingHistory: ProcessingJob[];
  processFile: (file: File, options?: ProcessingOptions) => Promise<unknown>;
  processFiles: (files: File[], options?: ProcessingOptions) => Promise<unknown[]>;
  retryJob: (jobId: string) => Promise<void>;
  cancelJob: (jobId: string) => Promise<void>;
  clearCompleted: () => void;
  clearAll: () => void;
  getJob: (jobId: string) => ProcessingJob | undefined;
  getJobsByStatus: (status: ProcessingJob['status']) => ProcessingJob[];
  isConnected: boolean;
  // Additional properties expected by Dashboard
  credentials: unknown[];
  isLoading: boolean;
  loading: boolean;
  error: string | null;
  getJobDetails: (jobId: string) => ProcessingJob | undefined;
  clearJobs: () => void;
}
import type { ProcessingOptions } from '../types/credentials';

// Define the processing job interface for this hook
export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';

export interface ProcessingJob {
  id: string;
  fileName: string;
  fileSize?: number;
  status: ProcessingStatus;
  progress: number;
  createdAt: string;
  startedAt?: Date;
  completedAt?: string;
  updatedAt?: Date;
  error?: string;
  result?: unknown;
  results?: {
    totalCost?: number;
    provider?: string;
    extracted?: number;
  };
  retryCount?: number;
  maxRetries?: number;
  options?: ProcessingOptions;
  totalFiles?: number;
  filesProcessed?: number;
}

// Define the state interface for credential processing
interface CredentialProcessingState {
  jobs: ProcessingJob[];
  isProcessing: boolean;
  totalJobs: number;
  completedJobs: number;
  failedJobs: number;
  currentJob: ProcessingJob | null;
  progress: number;
  estimatedTimeRemaining: number | null;
  processingHistory: ProcessingJob[];
}
import { config } from '../config';
import useApi from './useApi';
import useNotifications from './useNotifications';
import useWebSocket from './useWebSocket';
import useFileUpload from './useFileUpload';


interface UseCredentialProcessingOptions {
  autoStart?: boolean;
  enableWebSocket?: boolean;
  maxRetries?: number;
  retryDelay?: number;
}

const useCredentialProcessing = (
  options: UseCredentialProcessingOptions = {}
): UseCredentialProcessingReturn => {
  const {
    enableWebSocket = true,
    maxRetries = 3,
    retryDelay = 1000,
  } = options;

  const [state, setState] = useState<CredentialProcessingState>({
    jobs: [],
    isProcessing: false,
    totalJobs: 0,
    completedJobs: 0,
    failedJobs: 0,
    currentJob: null,
    progress: 0,
    estimatedTimeRemaining: null,
    processingHistory: [],
  });

  const { execute: apiExecute } = useApi(() => Promise.resolve({}));
  const { addNotification } = useNotifications();
  const { uploadFiles } = useFileUpload();
  const retryCountRef = useRef<Map<string, number>>(new Map());
  const startTimeRef = useRef<number | null>(null);

  // WebSocket connection for real-time updates
  const { isConnected } = useWebSocket(
    enableWebSocket ? {
      url: `${config.ws.URL}/processing`,
      reconnect: true,
      heartbeat: true,
    } : {}
  );

  // Subscribe to processing updates via WebSocket
  useEffect(() => {
    if (!enableWebSocket || !isConnected) return;

    // Note: WebSocket event handling would need to be implemented differently
    // as the current useWebSocket implementation doesn't support subscribe/unsubscribe
    
    return () => {
      // Cleanup if needed
    };
  }, [isConnected, enableWebSocket]);

  // Update job status
  const updateJobStatus = useCallback((
    jobId: string,
    status: ProcessingJob['status'],
    progress?: number,
    result?: unknown,
    error?: string
  ) => {
    setState((prev: CredentialProcessingState) => ({
      ...prev,
      jobs: prev.jobs.map((job: ProcessingJob) => {
        if (job.id === jobId) {
          return {
            ...job,
            status,
            progress: progress ?? job.progress,
            result: result ?? job.result,
            error: error ?? job.error,
            updatedAt: new Date(),
          };
        }
        return job;
      }),
      currentJob: prev.currentJob?.id === jobId ? {
        ...prev.currentJob,
        status,
        progress: progress ?? prev.currentJob.progress,
        result: result ?? prev.currentJob.result,
        error: error ?? prev.currentJob.error,
        updatedAt: new Date(),
      } : prev.currentJob,
    }));
  }, []);

  // Complete job
  const completeJob = useCallback((jobId: string, result: unknown) => {
    setState((prev: CredentialProcessingState) => {
      const updatedJobs = prev.jobs.map((job: ProcessingJob) => {
        if (job.id === jobId) {
          return {
            ...job,
            status: 'completed' as const,
            progress: 100,
            result,
            completedAt: new Date().toISOString(),
            updatedAt: new Date(),
          };
        }
        return job;
      });

      const completedCount = updatedJobs.filter((job: ProcessingJob) => job.status === 'completed').length;
    const failedCount = updatedJobs.filter((job: ProcessingJob) => job.status === 'failed').length;
      const totalProgress = (completedCount + failedCount) / prev.totalJobs * 100;

      return {
        ...prev,
        jobs: updatedJobs,
        completedJobs: completedCount,
        progress: totalProgress,
        currentJob: prev.currentJob?.id === jobId ? null : prev.currentJob,
        processingHistory: [
          ...prev.processingHistory,
          {
            id: jobId,
            fileName: updatedJobs.find((job: ProcessingJob) => job.id === jobId)?.fileName || '',
            status: 'completed' as const,
            progress: 100,
            createdAt: new Date().toISOString(),
            result,
            completedAt: new Date().toISOString(),
          } as ProcessingJob,
        ]
      };
    });

    addNotification({
      type: 'success',
      title: 'Processing Complete',
      message: `Successfully processed credential: ${(result as any)?.extractedData?.name || 'Unknown'}`,
    });
  }, [addNotification]);

  // Fail job
  const failJob = useCallback((jobId: string, error: string) => {
    setState((prev: CredentialProcessingState) => {
      const updatedJobs = prev.jobs.map((job: ProcessingJob) => {
        if (job.id === jobId) {
          return {
            ...job,
            status: 'failed' as const,
            error,
            updatedAt: new Date(),
          };
        }
        return job;
      });

      const completedCount = updatedJobs.filter((job: ProcessingJob) => job.status === 'completed').length;
    const failedCount = updatedJobs.filter((job: ProcessingJob) => job.status === 'failed').length;
      const totalProgress = (completedCount + failedCount) / prev.totalJobs * 100;

      return {
        ...prev,
        jobs: updatedJobs,
        failedJobs: failedCount,
        progress: totalProgress,
        currentJob: prev.currentJob?.id === jobId ? null : prev.currentJob,
      };
    });

    addNotification({
      type: 'error',
      title: 'Processing Failed',
      message: error,
    });
  }, [addNotification]);

  // Process single file
  const processFile = useCallback(async (
    file: File,
    options: ProcessingOptions = {}
  ): Promise<unknown> => {
    const jobId = `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // Create job
    const job: ProcessingJob = {
      id: jobId,
      fileName: file.name,
      fileSize: file.size,
      status: 'pending',
      progress: 0,
      options,
      createdAt: new Date().toISOString(),
      updatedAt: new Date(),
    };

    // Add job to state
    setState((prev: CredentialProcessingState) => ({
      ...prev,
      jobs: [...prev.jobs, job],
      totalJobs: prev.totalJobs + 1,
    }));

    try {
      // Upload file first
      updateJobStatus(jobId, 'pending');
      const uploadResult = await uploadFiles([file], {
        onProgress: (progress: number) => {
          updateJobStatus(jobId, 'pending', progress * 0.2); // Upload is 20% of total progress
        },
      });

      if (!uploadResult || uploadResult.length === 0) {
        throw new Error('Failed to upload file');
      }

      const uploadedFile = uploadResult[0];
      updateJobStatus(jobId, 'processing', 20);

      // Start processing
      const processingData = {
        fileId: (uploadedFile as any).id,
        fileName: file.name,
        options: {
          aiProvider: options.aiProvider || 'openai',
          enableQR: options.enableQR ?? true,
          enableOCR: options.enableOCR ?? true,
          validateData: options.validateData ?? true,
          enableAI: options.enableAI ?? true,
          ocrLanguage: options.ocrLanguage,
          extractStructuredData: options.extractStructuredData ?? true,
          concurrency: options.concurrency,
        },
      };

      // Send processing request
      const result = await apiExecute({
        url: '/api/credentials/process',
        method: 'POST',
        data: processingData,
      });

      if (!enableWebSocket) {
        // Poll for results if WebSocket is not available
        await pollProcessingStatus(jobId, (result as any)?.data?.jobId);
      }

      return (result as any)?.data;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Processing failed';
      failJob(jobId, errorMessage);
      throw error;
    }
  }, [apiExecute, uploadFiles, updateJobStatus, failJob, enableWebSocket]);

  // Poll processing status (fallback when WebSocket is not available)
  const pollProcessingStatus = useCallback(async (jobId: string, serverJobId: string) => {
    const pollInterval = 2000; // 2 seconds
    const maxPollTime = 300000; // 5 minutes
    const startTime = Date.now();

    const poll = async (): Promise<void> => {
      try {
        const response = await apiExecute({
          url: `/api/credentials/status/${serverJobId}`,
          method: 'GET',
        });

        const { status, progress, result, error } = (response as any)?.data || {};

        updateJobStatus(jobId, status, progress);

        if (status === 'completed') {
          completeJob(jobId, result);
          return;
        }

        if (status === 'failed') {
          failJob(jobId, error || 'Processing failed');
          return;
        }

        // Continue polling if still processing
        if (status === 'processing' && Date.now() - startTime < maxPollTime) {
          setTimeout(poll, pollInterval);
        } else if (Date.now() - startTime >= maxPollTime) {
          failJob(jobId, 'Processing timeout');
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to check status';
        failJob(jobId, errorMessage);
      }
    };

    poll();
  }, [apiExecute, updateJobStatus, completeJob, failJob]);

  // Process multiple files
  const processFiles = useCallback(async (
    files: File[],
    options: ProcessingOptions = {}
  ): Promise<unknown[]> => {
    setState((prev: CredentialProcessingState) => ({
      ...prev,
      isProcessing: true,
      totalJobs: prev.totalJobs + files.length,
    }));

    startTimeRef.current = Date.now();
    const results: unknown[] = [];
    const concurrency = (options as ProcessingOptions & { concurrency?: number }).concurrency || 3;

    try {
      // Process files with limited concurrency
      const processPromises = files.map(async (file, index) => {
        // Add delay between batches to avoid overwhelming the server
        if (index > 0 && index % concurrency === 0) {
          await new Promise((resolve: (value: unknown) => void) => setTimeout(resolve, 1000));
        }

        try {
          const result = await processFile(file, options);
          results.push(result);
          return result;
        } catch (error) {
          console.error(`Failed to process file ${file.name}:`, error);
          throw error;
        }
      });

      // Wait for all processing to complete
      await Promise.allSettled(processPromises);

      return results;
    } finally {
      setState((prev: CredentialProcessingState) => ({
        ...prev,
        isProcessing: false,
        estimatedTimeRemaining: null,
      }));
    }
  }, [processFile]);

  // Retry failed job
  const retryJob = useCallback(async (jobId: string): Promise<void> => {
    const job = state.jobs.find((j: ProcessingJob) => j.id === jobId);
    if (!job || job.status !== 'failed') return;

    const retryCount = retryCountRef.current.get(jobId) || 0;
    if (retryCount >= maxRetries) {
      addNotification({
        type: 'error',
        title: 'Retry Limit Reached',
        message: `Maximum retry attempts (${maxRetries}) reached for ${job.fileName}`,
      });
      return;
    }

    retryCountRef.current.set(jobId, retryCount + 1);
    
    try {
      // Send retry request to server
      await apiExecute({
        url: '/api/credentials/retry',
        method: 'POST',
        data: { jobId },
      });

      // Reset job status
      updateJobStatus(jobId, 'pending', 0);
      
      // Add delay before retry
      await new Promise((resolve: (value: unknown) => void) => setTimeout(resolve, retryDelay * Math.pow(2, retryCount)));
      
      addNotification({
        type: 'info',
        title: 'Retrying Processing',
        message: `Retrying processing for ${job.fileName} (attempt ${retryCount + 1}/${maxRetries})`,
      });
    } catch (error) {
      console.error('Failed to retry job:', error);
      addNotification({
        type: 'error',
        title: 'Retry Failed',
        message: 'Failed to retry processing job',
      });
    }
  }, [state.jobs, maxRetries, retryDelay, addNotification, updateJobStatus, apiExecute]);

  // Cancel job
  const cancelJob = useCallback(async (jobId: string): Promise<void> => {
    const job = state.jobs.find((j: ProcessingJob) => j.id === jobId);
    if (!job || job.status === 'completed' || job.status === 'failed') return;

    try {
      // Send cancellation request to server
      await apiExecute({
        url: `/api/credentials/cancel/${jobId}`,
        method: 'POST',
      });

      updateJobStatus(jobId, 'cancelled');
      
      addNotification({
        type: 'info',
        title: 'Job Cancelled',
        message: `Processing cancelled for ${job.fileName}`,
      });
    } catch (error) {
      console.error('Failed to cancel job:', error);
      addNotification({
        type: 'error',
        title: 'Cancellation Failed',
        message: 'Failed to cancel processing job',
      });
    }
  }, [state.jobs, apiExecute, updateJobStatus, addNotification]);

  // Clear completed jobs
  const clearCompleted = useCallback(() => {
    setState((prev: CredentialProcessingState) => ({
      ...prev,
      jobs: prev.jobs.filter((job: ProcessingJob) => job.status !== 'completed' && job.status !== 'failed'),
      completedJobs: 0,
      failedJobs: 0,
    }));
  }, []);

  // Clear all jobs
  const clearAll = useCallback(() => {
    setState({
      jobs: [],
      isProcessing: false,
      totalJobs: 0,
      completedJobs: 0,
      failedJobs: 0,
      currentJob: null,
      progress: 0,
      estimatedTimeRemaining: null,
      processingHistory: [],
    });
    retryCountRef.current.clear();
  }, []);

  // Get job by ID
  const getJob = useCallback((jobId: string): ProcessingJob | undefined => {
    return state.jobs.find((job: ProcessingJob) => job.id === jobId);
  }, [state.jobs]);

  // Get jobs by status
  const getJobsByStatus = useCallback((status: ProcessingJob['status']): ProcessingJob[] => {
    return state.jobs.filter((job: ProcessingJob) => job.status === status);
  }, [state.jobs]);

  // Calculate estimated time remaining
  useEffect(() => {
    if (!state.isProcessing || !startTimeRef.current) return;

    const elapsed = Date.now() - startTimeRef.current;
    const completedCount = state.completedJobs + state.failedJobs;
    const remainingCount = state.totalJobs - completedCount;

    if (completedCount > 0 && remainingCount > 0) {
      const avgTimePerJob = elapsed / completedCount;
      const estimatedRemaining = avgTimePerJob * remainingCount;
      
      setState((prev: CredentialProcessingState) => ({
        ...prev,
        estimatedTimeRemaining: estimatedRemaining,
      }));
    }
  }, [state.isProcessing, state.completedJobs, state.failedJobs, state.totalJobs]);

  return {
    ...state,
    processFile,
    processFiles,
    retryJob,
    cancelJob,
    clearCompleted,
    clearAll,
    getJob,
    getJobsByStatus,
    isConnected: enableWebSocket ? isConnected : true,
    // Additional properties expected by Dashboard
    credentials: state.jobs, // Map jobs to credentials for compatibility
    isLoading: state.isProcessing,
    loading: state.isProcessing, // Add loading property
    error: null, // Add error property
    getJobDetails: getJob, // Map getJobDetails to existing getJob method
    clearJobs: clearAll, // Map clearJobs to existing clearAll method
  };
};

// Processing utilities
export const processingUtils = {
  // Validate file for processing
  validateFile: (file: File): { isValid: boolean; error?: string } => {
    const maxSize = config.file.MAX_SIZE;
     const allowedTypes = config.file.ALLOWED_TYPES;

    if (file.size > maxSize) {
      const sizeMB = (maxSize / (1024 * 1024)).toFixed(1);
      return {
        isValid: false,
        error: `File size must be less than ${sizeMB}MB`,
      };
    }

    if (!allowedTypes.includes(file.type as any)) {
      return {
        isValid: false,
        error: `File type must be one of: ${allowedTypes.join(', ')}`,
      };
    }

    return { isValid: true };
  },

  // Format processing time
  formatProcessingTime: (milliseconds: number): string => {
    const seconds = Math.floor(milliseconds / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
      return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  },

  // Calculate processing statistics
  calculateStats: (jobs: ProcessingJob[]) => {
    const total = jobs.length;
    const completed = jobs.filter((job: ProcessingJob) => job.status === 'completed').length;
    const failed = jobs.filter((job: ProcessingJob) => job.status === 'failed').length;
    const processing = jobs.filter((job: ProcessingJob) => job.status === 'processing').length;
    const pending = jobs.filter((job: ProcessingJob) => job.status === 'pending').length;
    const cancelled = jobs.filter((job: ProcessingJob) => job.status === 'cancelled').length;

    const successRate = total > 0 ? (completed / total) * 100 : 0;
    const failureRate = total > 0 ? (failed / total) * 100 : 0;

    return {
      total,
      completed,
      failed,
      processing,
      pending,
      cancelled,
      successRate,
      failureRate,
    };
  },

  // Generate processing report
  generateReport: (jobs: ProcessingJob[], history: ProcessingJob[]) => {
    const stats = processingUtils.calculateStats(jobs);
    const totalProcessingTime = jobs
      .filter((job: ProcessingJob) => job.completedAt && job.createdAt)
      .reduce((total, job) => {
        return total + (new Date(job.completedAt!).getTime() - new Date(job.createdAt).getTime());
      }, 0);

    const avgProcessingTime = stats.completed > 0 ? totalProcessingTime / stats.completed : 0;

    return {
      ...stats,
      totalProcessingTime,
      avgProcessingTime,
      avgProcessingTimeFormatted: processingUtils.formatProcessingTime(avgProcessingTime),
      historyCount: history.length,
      generatedAt: new Date(),
    };
  },

  // Export processing data
  exportData: (jobs: ProcessingJob[], format: 'json' | 'csv' = 'json') => {
    if (format === 'json') {
      return JSON.stringify(jobs, null, 2);
    }

    // CSV format
    const headers = ['ID', 'File Name', 'Status', 'Progress', 'Created At', 'Completed At', 'Error'];
    const rows = jobs.map((job: ProcessingJob) => [
      job.id,
      job.fileName,
      job.status,
      `${job.progress}%`,
      job.createdAt || '',
      job.completedAt || '',
      job.error || '',
    ]);

    return [headers, ...rows]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');
  },
};

export default useCredentialProcessing;