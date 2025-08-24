import { FILE_UPLOAD } from './constants';

// File validation utilities
export const validateFile = (file: File): { valid: boolean; error?: string } => {
  // Check file size
  if (file.size > FILE_UPLOAD.MAX_SIZE) {
    return {
      valid: false,
      error: `File size (${formatFileSize(file.size)}) exceeds maximum allowed size (${formatFileSize(FILE_UPLOAD.MAX_SIZE)})`,
    };
  }

  // Check file type
  if (!(FILE_UPLOAD.ALLOWED_TYPES as readonly string[]).includes(file.type)) {
    return {
      valid: false,
      error: `File type "${file.type}" is not supported. Allowed types: ${FILE_UPLOAD.ALLOWED_TYPES.join(', ')}`,
    };
  }

  // Check file extension
  const extension = getFileExtension(file.name);
  if (!(FILE_UPLOAD.ALLOWED_EXTENSIONS as readonly string[]).includes(extension)) {
    return {
      valid: false,
      error: `File extension "${extension}" is not supported. Allowed extensions: ${FILE_UPLOAD.ALLOWED_EXTENSIONS.join(', ')}`,
    };
  }

  return { valid: true };
};

// Format file size to human readable format
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Get file extension
export const getFileExtension = (filename: string): string => {
  return filename.slice(((filename.lastIndexOf('.') - 1) >>> 0) + 2).toLowerCase();
};

// Get file name without extension
export const getFileNameWithoutExtension = (filename: string): string => {
  return filename.replace(/\.[^/.]+$/, '');
};

// Check if file is image
export const isImageFile = (file: File): boolean => {
  return file.type.startsWith('image/');
};

// Check if file is PDF
export const isPdfFile = (file: File): boolean => {
  return file.type === 'application/pdf';
};

// Get file type category
export const getFileTypeCategory = (file: File): 'image' | 'pdf' | 'other' => {
  if (isImageFile(file)) return 'image';
  if (isPdfFile(file)) return 'pdf';
  return 'other';
};

// Convert file to base64
export const fileToBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      if (typeof reader.result === 'string') {
        resolve(reader.result);
      } else {
        reject(new Error('Failed to convert file to base64'));
      }
    };
    reader.onerror = error => reject(error);
  });
};

// Convert file to array buffer
export const fileToArrayBuffer = (file: File): Promise<ArrayBuffer> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsArrayBuffer(file);
    reader.onload = () => {
      if (reader.result instanceof ArrayBuffer) {
        resolve(reader.result);
      } else {
        reject(new Error('Failed to convert file to array buffer'));
      }
    };
    reader.onerror = error => reject(error);
  });
};

// Convert file to text
export const fileToText = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsText(file);
    reader.onload = () => {
      if (typeof reader.result === 'string') {
        resolve(reader.result);
      } else {
        reject(new Error('Failed to convert file to text'));
      }
    };
    reader.onerror = error => reject(error);
  });
};

// Create file from base64
export const base64ToFile = (base64: string, filename: string): File => {
  const arr = base64.split(',');
  const mime = arr[0].match(/:(.*?);/)![1];
  const bstr = atob(arr[1]);
  let n = bstr.length;
  const u8arr = new Uint8Array(n);
  
  while (n--) {
    u8arr[n] = bstr.charCodeAt(n);
  }
  
  return new File([u8arr], filename, { type: mime });
};

// Download file
export const downloadFile = (data: Blob | string, filename: string, mimeType?: string): void => {
  let blob: Blob;
  
  if (typeof data === 'string') {
    blob = new Blob([data], { type: mimeType || 'text/plain' });
  } else {
    blob = data;
  }
  
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

// Download file from URL
export const downloadFileFromUrl = async (url: string, filename?: string): Promise<void> => {
  try {
    const response = await fetch(url);
    const blob = await response.blob();
    const downloadFilename = filename || url.split('/').pop() || 'download';
    downloadFile(blob, downloadFilename);
  } catch (error) {
    throw new Error(`Failed to download file: ${error}`);
  }
};

// Create image preview URL
export const createImagePreview = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    if (!isImageFile(file)) {
      reject(new Error('File is not an image'));
      return;
    }
    
    const reader = new FileReader();
    reader.onload = (e) => {
      if (e.target?.result) {
        resolve(e.target.result as string);
      } else {
        reject(new Error('Failed to create image preview'));
      }
    };
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsDataURL(file);
  });
};

// Compress image file
export const compressImage = (
  file: File,
  maxWidth: number = 1920,
  maxHeight: number = 1080,
  quality: number = 0.8
): Promise<File> => {
  return new Promise((resolve, reject) => {
    if (!isImageFile(file)) {
      reject(new Error('File is not an image'));
      return;
    }
    
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    
    img.onload = () => {
      // Calculate new dimensions
      let { width, height } = img;
      
      if (width > height) {
        if (width > maxWidth) {
          height = (height * maxWidth) / width;
          width = maxWidth;
        }
      } else {
        if (height > maxHeight) {
          width = (width * maxHeight) / height;
          height = maxHeight;
        }
      }
      
      canvas.width = width;
      canvas.height = height;
      
      // Draw and compress
      ctx?.drawImage(img, 0, 0, width, height);
      
      canvas.toBlob(
        (blob) => {
          if (blob) {
            const compressedFile = new File([blob], file.name, {
              type: file.type,
              lastModified: Date.now(),
            });
            resolve(compressedFile);
          } else {
            reject(new Error('Failed to compress image'));
          }
        },
        file.type,
        quality
      );
    };
    
    img.onerror = () => reject(new Error('Failed to load image'));
    img.src = URL.createObjectURL(file);
  });
};

// Get image dimensions
export const getImageDimensions = (file: File): Promise<{ width: number; height: number }> => {
  return new Promise((resolve, reject) => {
    if (!isImageFile(file)) {
      reject(new Error('File is not an image'));
      return;
    }
    
    const img = new Image();
    img.onload = () => {
      resolve({ width: img.width, height: img.height });
      URL.revokeObjectURL(img.src);
    };
    img.onerror = () => {
      reject(new Error('Failed to load image'));
      URL.revokeObjectURL(img.src);
    };
    img.src = URL.createObjectURL(file);
  });
};

// Generate unique filename
export const generateUniqueFilename = (originalName: string): string => {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 8);
  const extension = getFileExtension(originalName);
  const nameWithoutExt = getFileNameWithoutExtension(originalName);
  
  return `${nameWithoutExt}_${timestamp}_${random}.${extension}`;
};

// Validate multiple files
export const validateFiles = (files: File[]): { valid: File[]; invalid: Array<{ file: File; error: string }> } => {
  const valid: File[] = [];
  const invalid: Array<{ file: File; error: string }> = [];
  
  files.forEach(file => {
    const validation = validateFile(file);
    if (validation.valid) {
      valid.push(file);
    } else {
      invalid.push({ file, error: validation.error! });
    }
  });
  
  return { valid, invalid };
};

// Create file hash (simple hash for client-side)
export const createFileHash = async (file: File): Promise<string> => {
  const buffer = await fileToArrayBuffer(file);
  const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
};

// Check if files are identical
export const areFilesIdentical = async (file1: File, file2: File): Promise<boolean> => {
  if (file1.size !== file2.size || file1.name !== file2.name || file1.type !== file2.type) {
    return false;
  }
  
  try {
    const hash1 = await createFileHash(file1);
    const hash2 = await createFileHash(file2);
    return hash1 === hash2;
  } catch {
    return false;
  }
};

// Get file icon based on type
export const getFileIcon = (file: File): string => {
  const type = getFileTypeCategory(file);
  
  switch (type) {
    case 'image':
      return '🖼️';
    case 'pdf':
      return '📄';
    default:
      return '📎';
  }
};

// Format file info for display
export const formatFileInfo = (file: File): string => {
  const size = formatFileSize(file.size);
  const type = file.type || 'Unknown';
  return `${file.name} (${size}, ${type})`;
};