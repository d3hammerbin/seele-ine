import React, { useCallback, useState } from 'react';
import { cn } from '../../utils/helpers';
import { Button, Card, CardContent, Loading } from '../ui';
import useFileUpload from '../../hooks/useFileUpload';
import useCredentialProcessing from '../../hooks/useCredentialProcessing';

export interface FileUploadProps {
  onUploadComplete?: (files: File[]) => void;
  onProcessingStart?: (jobId: string) => void;
  maxFiles?: number;
  maxSize?: number;
  acceptedTypes?: string[];
  className?: string;
}

const FileUpload: React.FC<FileUploadProps> = ({
  onUploadComplete,
  onProcessingStart,
  maxSize = 10 * 1024 * 1024, // 10MB
  acceptedTypes = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf'],
  className,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const {
    files,
    isUploading,
    progress,
    error: uploadError,
    uploadFiles,
    removeFile,
    clearFiles,
  } = useFileUpload();

  const {
    processFiles,
    loading: processing,
    error: processingError,
  } = useCredentialProcessing();

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);

      const droppedFiles = Array.from(e.dataTransfer.files);
      if (droppedFiles.length > 0) {
        try {
          await uploadFiles(droppedFiles);
          onUploadComplete?.(droppedFiles);
        } catch (error) {
          console.error('Upload failed:', error);
        }
      }
    },
    [uploadFiles, onUploadComplete]
  );

  const handleFileInput = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const selectedFiles = Array.from(e.target.files || []);
      if (selectedFiles.length > 0) {
        try {
          await uploadFiles(selectedFiles);
          onUploadComplete?.(selectedFiles);
        } catch (error) {
          console.error('Upload failed:', error);
        }
      }
      // Reset input
      e.target.value = '';
    },
    [uploadFiles, onUploadComplete]
  );

  const handleProcessFiles = useCallback(async () => {
    if (files.length === 0) return;

    try {
      const fileObjects = files.map(fileState => fileState.file);
      const results = await processFiles(fileObjects);
      if (results && results.length > 0) {
        // Assuming the first result contains job information
        const firstResult = results[0] as any;
        if (firstResult?.jobId) {
          onProcessingStart?.(firstResult.jobId);
        }
      }
    } catch (error) {
      console.error('Processing failed:', error);
    }
  }, [files, processFiles, onProcessingStart]);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (type: string) => {
    if (type.startsWith('image/')) {
      return (
        <svg className="w-8 h-8 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      );
    } else if (type === 'application/pdf') {
      return (
        <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
      );
    }
    return (
      <svg className="w-8 h-8 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    );
  };

  const error = uploadError || processingError;

  return (
    <div className={cn('space-y-6', className)}>
      {/* Upload Area */}
      <Card className={cn(
        'border-2 border-dashed transition-colors',
        dragActive ? 'border-primary bg-primary/5' : 'border-border',
        error ? 'border-destructive' : ''
      )}>
        <CardContent className="p-8">
          <div
            className="text-center"
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <div className="mb-4">
              <svg className="w-12 h-12 mx-auto text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-foreground mb-2">
              Arrastra archivos aquí o haz clic para seleccionar
            </h3>
            <p className="text-sm text-muted-foreground mb-4">
              Soporta imágenes (JPG, PNG) y documentos PDF hasta {formatFileSize(maxSize)}
            </p>
            <input
              type="file"
              multiple
              accept={acceptedTypes.join(',')}
              onChange={handleFileInput}
              className="hidden"
              id="file-upload"
              disabled={isUploading || processing}
            />
            <Button
              variant="outline"
              onClick={() => document.getElementById('file-upload')?.click()}
              disabled={isUploading || processing}
            >
              Seleccionar archivos
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Upload Progress */}
      {isUploading && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-3">
              <Loading size="sm" />
              <div className="flex-1">
                <p className="text-sm font-medium text-foreground">Subiendo archivos...</p>
                <div className="w-full bg-secondary rounded-full h-2 mt-1">
                  <div
                    className="bg-primary h-2 rounded-full transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
              <span className="text-sm text-muted-foreground">{progress}%</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error Display */}
      {error && (
        <Card variant="destructive">
          <CardContent className="p-4">
            <div className="flex items-center space-x-3">
              <svg className="w-5 h-5 text-destructive" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-sm text-destructive">{error}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* File List */}
      {files.length > 0 && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-sm font-medium text-foreground">
                Archivos seleccionados ({files.length})
              </h4>
              <div className="space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={clearFiles}
                  disabled={isUploading || processing}
                >
                  Limpiar
                </Button>
                <Button
                  size="sm"
                  onClick={handleProcessFiles}
                  disabled={isUploading || processing || files.length === 0}
                  loading={processing}
                >
                  Procesar archivos
                </Button>
              </div>
            </div>
            <div className="space-y-2">
              {files.map((file) => (
                <div
                  key={file.id}
                  className="flex items-center space-x-3 p-3 bg-secondary/50 rounded-lg"
                >
                  {getFileIcon(file.file.type)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">
                      {file.file.name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatFileSize(file.file.size)} • {file.file.type}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeFile(file.id)}
                    disabled={isUploading || processing}
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default FileUpload;