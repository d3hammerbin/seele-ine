import React, { useEffect } from 'react';
import { cn } from '../../utils/helpers';
import { Card, CardContent, CardHeader, Loading, Button } from '../ui';
import useCredentialProcessing from '../../hooks/useCredentialProcessing';
import type { ProcessingJob, ProcessingStatus as Status } from '../../hooks/useCredentialProcessing';

export interface ProcessingStatusProps {
  jobId?: string;
  showHistory?: boolean;
  onJobComplete?: (job: ProcessingJob) => void;
  onJobError?: (job: ProcessingJob) => void;
  className?: string;
}

const ProcessingStatus: React.FC<ProcessingStatusProps> = ({
  jobId,
  showHistory = true,
  onJobComplete,
  onJobError,
  className,
}) => {
  const {
    jobs,
    currentJob,
    loading,
    error,
    getJobDetails,
    retryJob,
    cancelJob,
    clearJobs,
  } = useCredentialProcessing();

  useEffect(() => {
    if (jobId && jobId !== currentJob?.id) {
      getJobDetails(jobId);
    }
  }, [jobId, currentJob?.id, getJobDetails]);

  useEffect(() => {
    if (currentJob) {
      if (currentJob.status === 'completed') {
        onJobComplete?.(currentJob);
      } else if (currentJob.status === 'failed') {
        onJobError?.(currentJob);
      }
    }
  }, [currentJob, onJobComplete, onJobError]);

  const getStatusIcon = (status: Status) => {
    switch (status) {
      case 'pending':
        return (
          <svg className="w-5 h-5 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'processing':
        return <Loading size="sm" />;
      case 'completed':
        return (
          <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'failed':
        return (
          <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'cancelled':
        return (
          <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L18.364 5.636M5.636 18.364l12.728-12.728" />
          </svg>
        );
      default:
        return null;
    }
  };

  const getStatusText = (status: Status) => {
    switch (status) {
      case 'pending':
        return 'Pendiente';
      case 'processing':
        return 'Procesando';
      case 'completed':
        return 'Completado';
      case 'failed':
        return 'Fallido';
      case 'cancelled':
        return 'Cancelado';
      default:
        return 'Desconocido';
    }
  };

  const getStatusColor = (status: Status) => {
    switch (status) {
      case 'pending':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'processing':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'completed':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'failed':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'cancelled':
        return 'text-gray-600 bg-gray-50 border-gray-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatDuration = (startTime: string, endTime?: string) => {
    const start = new Date(startTime).getTime();
    const end = endTime ? new Date(endTime).getTime() : Date.now();
    const duration = Math.round((end - start) / 1000);
    
    if (duration < 60) {
      return `${duration}s`;
    } else if (duration < 3600) {
      return `${Math.floor(duration / 60)}m ${duration % 60}s`;
    } else {
      const hours = Math.floor(duration / 3600);
      const minutes = Math.floor((duration % 3600) / 60);
      return `${hours}h ${minutes}m`;
    }
  };

  if (loading && !currentJob) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <Loading size="lg" text="Cargando estado del procesamiento..." />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card variant="destructive" className={className}>
        <CardContent className="p-6">
          <div className="flex items-center space-x-3">
            <svg className="w-5 h-5 text-destructive" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm text-destructive">{error}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Current Job Status */}
      {currentJob && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-foreground">
                Estado del procesamiento
              </h3>
              <span className={cn(
                'px-2 py-1 text-xs font-medium rounded-full border',
                getStatusColor(currentJob.status)
              )}>
                {getStatusText(currentJob.status)}
              </span>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center space-x-3">
              {getStatusIcon(currentJob.status)}
              <div className="flex-1">
                <p className="text-sm font-medium text-foreground">
                  Job ID: {currentJob.id}
                </p>
                <p className="text-xs text-muted-foreground">
                  Iniciado: {formatDate(currentJob.createdAt)}
                </p>
                {currentJob.completedAt && (
                  <p className="text-xs text-muted-foreground">
                    Completado: {formatDate(currentJob.completedAt)}
                  </p>
                )}
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-foreground">
                  {currentJob.filesProcessed || 0} / {currentJob.totalFiles || 0} archivos
                </p>
                <p className="text-xs text-muted-foreground">
                  Duración: {formatDuration(currentJob.createdAt, currentJob.completedAt)}
                </p>
              </div>
            </div>

            {/* Progress Bar */}
            {currentJob.status === 'processing' && (
              <div className="w-full bg-secondary rounded-full h-2">
                <div
                  className="bg-primary h-2 rounded-full transition-all duration-300"
                  style={{
                    width: `${((currentJob.filesProcessed || 0) / (currentJob.totalFiles || 1)) * 100}%`
                  }}
                />
              </div>
            )}

            {/* Error Message */}
            {currentJob.status === 'failed' && currentJob.error && (
              <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
                <p className="text-sm text-destructive">{currentJob.error}</p>
              </div>
            )}

            {/* Results Summary */}
            {currentJob.status === 'completed' && currentJob.results && (
              <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-sm text-green-800 font-medium mb-2">
                  Procesamiento completado exitosamente
                </p>
                <div className="grid grid-cols-2 gap-4 text-xs text-green-700">
                  <div>
                    <span className="font-medium">Archivos procesados:</span> {currentJob.filesProcessed}
                  </div>
                  <div>
                    <span className="font-medium">Credenciales extraídas:</span> {currentJob.results.extracted || 0}
                  </div>
                  <div>
                    <span className="font-medium">Costo total:</span> ${currentJob.results.totalCost?.toFixed(4) || '0.0000'}
                  </div>
                  <div>
                    <span className="font-medium">Proveedor usado:</span> {currentJob.results.provider || 'N/A'}
                  </div>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex space-x-2">
              {currentJob.status === 'failed' && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => retryJob(currentJob.id)}
                  disabled={loading}
                >
                  Reintentar
                </Button>
              )}
              {(currentJob.status === 'pending' || currentJob.status === 'processing') && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => cancelJob(currentJob.id)}
                  disabled={loading}
                >
                  Cancelar
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Job History */}
      {showHistory && jobs.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-foreground">
                Historial de procesamiento
              </h3>
              <Button
                variant="outline"
                size="sm"
                onClick={clearJobs}
                disabled={loading}
              >
                Limpiar historial
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {jobs.slice(0, 10).map((job) => (
                <div
                  key={job.id}
                  className="flex items-center space-x-3 p-3 bg-secondary/30 rounded-lg"
                >
                  {getStatusIcon(job.status)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">
                      {job.id}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatDate(job.createdAt)} • {job.filesProcessed || 0}/{job.totalFiles || 0} archivos
                    </p>
                  </div>
                  <div className="text-right">
                    <span className={cn(
                      'px-2 py-1 text-xs font-medium rounded-full border',
                      getStatusColor(job.status)
                    )}>
                      {getStatusText(job.status)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ProcessingStatus;