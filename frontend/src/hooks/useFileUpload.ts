// File upload hook
import { useState, useCallback, useRef } from 'react';
import type { UseFileUploadReturn, FileUploadState, UploadProgress, FileUploadOptions } from './types';
import { apiClient } from '../utils/api';
import { config } from '../config';
import { getFileExtension } from '../utils/file';
import { FileError } from '../utils/error';

const useFileUpload = (): UseFileUploadReturn => {
  const [uploads, setUploads] = useState<Record<string, FileUploadState>>({});
  const abortControllersRef = useRef<Record<string, AbortController>>({});

  // Generate unique upload ID
  const generateUploadId = useCallback((): string => {
    return `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  // Validate file
  const validateFile = useCallback((file: File): void => {
    // Check file size
    if (file.size > config.file.MAX_SIZE) {
      throw new FileError(
        `File size exceeds maximum allowed size of ${config.file.MAX_SIZE / (1024 * 1024)}MB`,
        file.name,
        file.size,
        file.type,
        { maxSize: config.file.MAX_SIZE }
      );
    }

    // Check file type
    const allowedTypes = config.file.ALLOWED_TYPES;
    if (allowedTypes.length > 0 && !allowedTypes.includes(file.type as any)) {
      throw new FileError(
        `File type ${file.type} is not allowed`,
        file.name,
        file.size,
        file.type,
        { allowedTypes }
      );
    }

    // Check file extension
    const extension = getFileExtension(file.name).toLowerCase();
    const allowedExtensions = config.file.ALLOWED_EXTENSIONS;
    if (allowedExtensions.length > 0 && !allowedExtensions.includes(extension as any)) {
      throw new FileError(
        `File extension ${extension} is not allowed`,
        file.name,
        file.size,
        file.type,
        { extension, allowedExtensions }
      );
    }
  }, []);

  // Upload single file
  const uploadFile = useCallback(async (
    file: File,
    options: FileUploadOptions = {}
  ): Promise<string> => {
    const uploadId = generateUploadId();
    const endpoint = options.endpoint || '/api/upload';
    const { onProgress, additionalData: metadata = {}, fieldName = 'file' } = options;

    try {
      // Validate file
      validateFile(file);

      // Create abort controller
      const abortController = new AbortController();
      abortControllersRef.current[uploadId] = abortController;

      // Initialize upload state
      const initialState: FileUploadState = {
        id: uploadId,
        file,
        status: 'uploading',
        progress: { loaded: 0, total: file.size, percentage: 0 },
        startTime: Date.now(),
      };

      setUploads(prev => ({ ...prev, [uploadId]: initialState }));

      // File will be handled by apiClient.upload with metadata

      // Upload file with progress tracking
      const response = await apiClient.upload(endpoint, file, {
        fieldName,
        additionalData: metadata,
        onProgress: (percentage: number) => {
          const progress: UploadProgress = { 
            loaded: Math.round((percentage / 100) * file.size), 
            total: file.size, 
            percentage 
          };
          
          // Update upload state
          setUploads(prev => ({
            ...prev,
            [uploadId]: {
              ...prev[uploadId],
              progress,
            },
          }));

          // Call progress callback
          onProgress?.(percentage);
        },
        config: {
          signal: abortController.signal,
        },
      });

      // Update state on success
      setUploads(prev => ({
        ...prev,
        [uploadId]: {
          ...prev[uploadId],
          status: 'completed',
          result: response?.data,
          endTime: Date.now(),
        },
      }));

      // Clean up abort controller
      delete abortControllersRef.current[uploadId];

      return uploadId;
    } catch (error) {
      // Update state on error
      setUploads(prev => ({
        ...prev,
        [uploadId]: {
          ...prev[uploadId],
          status: 'error',
          error: error instanceof Error ? error.message : 'Upload failed',
          endTime: Date.now(),
        },
      }));

      // Clean up abort controller
      delete abortControllersRef.current[uploadId];

      throw error;
    }
  }, [validateFile, generateUploadId]);

  // Upload multiple files
  const uploadFiles = useCallback(async (
    files: File[],
    options: FileUploadOptions = {}
  ): Promise<string[]> => {
    const endpoint = options.endpoint || '/api/upload/multiple';
    const { onProgress, onComplete, onError, metadata, concurrent = true } = options;
    const uploadIds: string[] = [];

    const uploadSingleFile = async (file: File): Promise<string> => {
      try {
        const uploadId = await uploadFile(file, {
          endpoint,
          onProgress: (progress: number) => onProgress?.(progress),
          additionalData: metadata,
        });
        
        const upload = uploads[uploadId];
        if (upload?.result) {
          onComplete?.(upload.result);
        }
        
        return uploadId;
      } catch (error) {
        onError?.(error instanceof Error ? error.message : 'Upload failed');
        throw error;
      }
    };

    if (concurrent) {
      // Upload files concurrently
      const promises = files.map(uploadSingleFile);
      const results = await Promise.allSettled(promises);
      
      results.forEach((result) => {
        if (result.status === 'fulfilled') {
          uploadIds.push(result.value);
        }
      });
    } else {
      // Upload files sequentially
      for (const file of files) {
        try {
          const uploadId = await uploadSingleFile(file);
          uploadIds.push(uploadId);
        } catch (error) {
          // Continue with next file on error
          console.error('Failed to upload file:', file.name, error);
        }
      }
    }

    return uploadIds;
  }, [uploadFile, uploads]);

  // Cancel upload
  const cancelUpload = useCallback((uploadId: string): void => {
    const abortController = abortControllersRef.current[uploadId];
    if (abortController) {
      abortController.abort();
      delete abortControllersRef.current[uploadId];
    }

    setUploads(prev => ({
      ...prev,
      [uploadId]: {
        ...prev[uploadId],
        status: 'cancelled',
        endTime: Date.now(),
      },
    }));
  }, []);

  // Retry upload
  const retryUpload = useCallback(async (uploadId: string): Promise<void> => {
    const upload = uploads[uploadId];
    if (!upload || !upload.file) {
      throw new Error('Upload not found or file missing');
    }

    // Reset upload state
    setUploads(prev => ({
      ...prev,
      [uploadId]: {
        ...prev[uploadId],
        status: 'uploading',
        progress: { loaded: 0, total: upload.file.size, percentage: 0 },
        error: undefined,
        startTime: Date.now(),
        endTime: undefined,
      },
    }));

    await uploadFile(upload.file);
  }, [uploads, uploadFile]);

  // Remove upload from state
  const removeUpload = useCallback((uploadId: string): void => {
    // Cancel if still uploading
    const upload = uploads[uploadId];
    if (upload?.status === 'uploading') {
      cancelUpload(uploadId);
    }

    setUploads(prev => {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { [uploadId]: _, ...rest } = prev;
      return rest;
    });
  }, [uploads, cancelUpload]);

  // Clear all uploads
  const clearUploads = useCallback((): void => {
    // Cancel all active uploads
    Object.keys(uploads).forEach(uploadId => {
      const upload = uploads[uploadId];
      if (upload.status === 'uploading') {
        cancelUpload(uploadId);
      }
    });

    setUploads({});
  }, [uploads, cancelUpload]);

  // Calculate overall progress
  const calculateProgress = useCallback(() => {
    const allUploads = Object.values(uploads);
    if (allUploads.length === 0) return 0;
    
    const totalProgress = allUploads.reduce((acc, upload) => {
      return acc + upload.progress.percentage;
    }, 0);
    
    return totalProgress / allUploads.length;
  }, [uploads]);

  return {
    files: Object.values(uploads),
    isUploading: Object.values(uploads).some(upload => upload.status === 'uploading'),
    progress: calculateProgress(),
    error: Object.values(uploads).find(upload => upload.error)?.error || null,
    uploadFile,
    uploadFiles,
    removeFile: removeUpload,
    clearFiles: clearUploads,
    retryUpload,
    cancelUpload,
  };
};

// File upload utilities
export const uploadUtils = {
  // Create file input element
  createFileInput: (options: {
    accept?: string;
    multiple?: boolean;
    onSelect?: (files: FileList) => void;
  } = {}): HTMLInputElement => {
    const input = document.createElement('input');
    input.type = 'file';
    input.style.display = 'none';
    
    if (options.accept) {
      input.accept = options.accept;
    }
    
    if (options.multiple) {
      input.multiple = true;
    }
    
    if (options.onSelect) {
      input.addEventListener('change', (e) => {
        const target = e.target as HTMLInputElement;
        if (target.files) {
          options.onSelect!(target.files);
        }
      });
    }
    
    return input;
  },

  // Trigger file selection
  selectFiles: (options: {
    accept?: string;
    multiple?: boolean;
  } = {}): Promise<FileList> => {
    return new Promise((resolve, reject) => {
      const input = uploadUtils.createFileInput({
        ...options,
        onSelect: (files) => {
          document.body.removeChild(input);
          resolve(files);
        },
      });
      
      document.body.appendChild(input);
      input.click();
      
      // Handle cancel
      const handleFocus = () => {
        setTimeout(() => {
          if (!input.files || input.files.length === 0) {
            document.body.removeChild(input);
            reject(new Error('File selection cancelled'));
          }
          window.removeEventListener('focus', handleFocus);
        }, 300);
      };
      
      window.addEventListener('focus', handleFocus);
    });
  },

  // Format file size
  formatFileSize: (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  },

  // Get file icon based on type
  getFileIcon: (file: File): string => {
    const type = file.type.toLowerCase();
    
    if (type.startsWith('image/')) return '🖼️';
    if (type.startsWith('video/')) return '🎥';
    if (type.startsWith('audio/')) return '🎵';
    if (type.includes('pdf')) return '📄';
    if (type.includes('word') || type.includes('document')) return '📝';
    if (type.includes('excel') || type.includes('spreadsheet')) return '📊';
    if (type.includes('powerpoint') || type.includes('presentation')) return '📈';
    if (type.includes('zip') || type.includes('rar') || type.includes('archive')) return '📦';
    if (type.includes('text')) return '📄';
    
    return '📁';
  },

  // Create file preview URL
  createPreviewUrl: (file: File): string | null => {
    if (file.type.startsWith('image/') || file.type.startsWith('video/')) {
      return URL.createObjectURL(file);
    }
    return null;
  },

  // Revoke preview URL
  revokePreviewUrl: (url: string): void => {
    URL.revokeObjectURL(url);
  },

  // Read file as text
  readAsText: (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = () => reject(reader.error);
      reader.readAsText(file);
    });
  },

  // Read file as data URL
  readAsDataURL: (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = () => reject(reader.error);
      reader.readAsDataURL(file);
    });
  },

  // Read file as array buffer
  readAsArrayBuffer: (file: File): Promise<ArrayBuffer> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as ArrayBuffer);
      reader.onerror = () => reject(reader.error);
      reader.readAsArrayBuffer(file);
    });
  },
};

export default useFileUpload;