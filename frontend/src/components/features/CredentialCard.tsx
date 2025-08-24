import React, { useState } from 'react';
import { cn } from '../../utils/helpers';
import { Card, CardContent, CardHeader, Button, Modal } from '../ui';
import type { CredentialData } from '../../types/credentials';

export interface CredentialCardProps {
  credential: CredentialData;
  onEdit?: (credential: CredentialData) => void;
  onDelete?: (credentialId: string) => void;
  onExport?: (credential: CredentialData) => void;
  showActions?: boolean;
  className?: string;
}

const CredentialCard: React.FC<CredentialCardProps> = ({
  credential,
  onEdit,
  onDelete,
  onExport,
  showActions = true,
  className,
}) => {
  const [showDetails, setShowDetails] = useState(false);


  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
    } catch {
      return dateString;
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-green-600 bg-green-50 border-green-200';
    if (confidence >= 0.7) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  const getConfidenceText = (confidence: number) => {
    if (confidence >= 0.9) return 'Alta';
    if (confidence >= 0.7) return 'Media';
    return 'Baja';
  };

  const mainFields = [
    { key: 'fullName', label: 'Nombre Completo' },
    { key: 'firstName', label: 'Nombre' },
    { key: 'lastName', label: 'Apellido' },
    { key: 'curp', label: 'CURP' },
    { key: 'voterKey', label: 'Clave de Elector' },
    { key: 'dateOfBirth', label: 'Fecha de Nacimiento' },
  ];

  const additionalFields = [
    { key: 'gender', label: 'Sexo' },
    { key: 'placeOfBirth', label: 'Lugar de Nacimiento' },
    { key: 'nationality', label: 'Nacionalidad' },
    { key: 'credentialNumber', label: 'Número de Credencial' },
    { key: 'issueDate', label: 'Fecha de Emisión' },
    { key: 'expirationDate', label: 'Fecha de Expiración' },
    { key: 'issuingAuthority', label: 'Autoridad Emisora' },
    { key: 'documentType', label: 'Tipo de Documento' },
  ];

  return (
    <>
      <Card className={cn('hover:shadow-md transition-shadow', className)}>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <h3 className="text-lg font-semibold text-foreground truncate">
                {credential.extractedData?.fullName || `${credential.extractedData?.firstName || ''} ${credential.extractedData?.lastName || ''}`.trim() || 'Sin nombre'}
              </h3>
              <p className="text-sm text-muted-foreground truncate">
                {credential.fileName}
              </p>
              <p className="text-xs text-muted-foreground">
                Procesado el {formatDate(credential.createdAt)}
              </p>
            </div>
            <div className="flex items-center space-x-2 ml-4">
              <span className={cn(
                'px-2 py-1 text-xs font-medium rounded-full border',
                getConfidenceColor(credential.extractedData?.confidence?.overall || 0)
              )}>
                {getConfidenceText(credential.extractedData?.confidence?.overall || 0)} ({Math.round((credential.extractedData?.confidence?.overall || 0) * 100)}%)
              </span>

            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Main Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {mainFields.map(({ key, label }) => {
              const value = credential.extractedData?.[key as keyof typeof credential.extractedData];
              if (!value) return null;
              return (
                <div key={key} className="space-y-1">
                  <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    {label}
                  </label>
                  <p className="text-sm text-foreground font-medium">
                    {key === 'dateOfBirth' ? formatDate(value as string) : 
                     typeof value === 'object' ? JSON.stringify(value) : String(value || 'N/A')}
                  </p>
                </div>
              );
            })}
          </div>

          {/* Processing Information */}
          <div className="flex items-center justify-between pt-3 border-t border-border">
            <div className="flex items-center space-x-4 text-xs text-muted-foreground">
              <span>Estado: {credential.status}</span>
              <span>Archivo: {credential.fileName}</span>
              <span>Tamaño: {(credential.fileSize / 1024).toFixed(1)}KB</span>
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowDetails(true)}
              >
                Ver detalles
              </Button>
              {showActions && (
                <>
                  {onExport && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onExport(credential)}
                      title="Exportar datos"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </Button>
                  )}
                  {onEdit && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onEdit(credential)}
                      title="Editar datos"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </Button>
                  )}
                  {onDelete && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onDelete(credential.id)}
                      title="Eliminar credencial"
                      className="text-destructive hover:text-destructive"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </Button>
                  )}
                </>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Details Modal */}
      <Modal
          isOpen={showDetails}
          onClose={() => setShowDetails(false)}
          title="Detalles de credencial"
          size="lg"
        >
        <div className="space-y-6">
          {/* All extracted data */}
          <div>
            <h4 className="text-sm font-semibold text-foreground mb-3">Información extraída</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[...mainFields, ...additionalFields].map(({ key, label }) => {
                const value = credential.extractedData?.[key as keyof typeof credential.extractedData];
                if (!value) return null;
                return (
                  <div key={key} className="space-y-1">
                    <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      {label}
                    </label>
                    <p className="text-sm text-muted-foreground">
                      {key === 'dateOfBirth' ? formatDate(value as string) : 
                       typeof value === 'object' ? JSON.stringify(value) : String(value || 'N/A')}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Processing metadata */}
          <div className="pt-4 border-t border-border">
            <h4 className="text-sm font-semibold text-foreground mb-3">Información de procesamiento</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Confianza:</span>
                <p className="font-medium">{Math.round((credential.extractedData?.confidence?.overall || 0) * 100)}%</p>
              </div>
              <div>
                <span className="text-muted-foreground">Proveedor:</span>
                <p className="font-medium">{credential.processingJob?.aiProvider || 'N/A'}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Tiempo:</span>
                <p className="font-medium">{credential.processingJob?.processingTime || 0}ms</p>
              </div>
              <div>
                <span className="text-muted-foreground">Costo:</span>
                <p className="font-medium">${(credential.processingJob?.cost || credential.aiAnalysis?.cost || 0).toFixed(4)}</p>
              </div>
            </div>
          </div>

          {/* Raw data */}
          <div className="pt-4 border-t border-border">
            <h4 className="text-sm font-semibold text-foreground mb-3">Datos sin procesar</h4>
            <pre className="text-xs bg-secondary p-3 rounded-lg overflow-auto max-h-40">
              {JSON.stringify(credential.extractedData, null, 2)}
            </pre>
          </div>
        </div>
      </Modal>

      {/* Image Modal - Removed since imageUrl is not available in CredentialData */}
    </>
  );
};

export default CredentialCard;