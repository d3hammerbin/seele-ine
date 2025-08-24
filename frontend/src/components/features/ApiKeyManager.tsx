import React, { useState } from 'react';
import { Card, CardContent, CardHeader, Button, Input, Modal, Loading, Toast } from '../ui';
import { cn } from '../../utils/helpers';
import useApiKeys from '../../hooks/useApiKeys';
import type { ApiKeyItem } from '../../hooks/types';

export interface ApiKeyManagerProps {
  className?: string;
}

const ApiKeyManager: React.FC<ApiKeyManagerProps> = ({ className }) => {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedKey, setSelectedKey] = useState<ApiKeyItem | null>(null);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyDescription, setNewKeyDescription] = useState('');
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [toastType, setToastType] = useState<'success' | 'error'>('success');

  const {
    apiKeys,
    isLoading,
    error,

    createApiKey,
    deleteApiKey,
    regenerateApiKey,
    updateApiKey,
  } = useApiKeys();

  const loading = isLoading;

  // API keys are automatically fetched by the useApiKeys hook

  const showToastMessage = (message: string, type: 'success' | 'error' = 'success') => {
    setToastMessage(message);
    setToastType(type);
    setShowToast(true);
  };

  const handleCreateKey = async () => {
    if (!newKeyName.trim()) {
      showToastMessage('El nombre es requerido', 'error');
      return;
    }

    try {
      await createApiKey({
        name: newKeyName.trim(),
        permissions: ['read', 'write'],
      });
      setShowCreateModal(false);
      setNewKeyName('');
      setNewKeyDescription('');
      showToastMessage('API Key creada exitosamente');
    } catch {
      showToastMessage('Error al crear la API Key', 'error');
    }
  };

  const handleDeleteKey = async () => {
    if (!selectedKey) return;

    try {
      await deleteApiKey(selectedKey.id);
      setShowDeleteModal(false);
      setSelectedKey(null);
      showToastMessage('API Key eliminada exitosamente');
    } catch {
      showToastMessage('Error al eliminar la API Key', 'error');
    }
  };

  const handleRegenerateKey = async (keyId: string) => {
    try {
      await regenerateApiKey(keyId);
      showToastMessage('API Key regenerada exitosamente');
    } catch {
      showToastMessage('Error al regenerar la API Key', 'error');
    }
  };

  const handleToggleStatus = async (keyId: string) => {
    try {
      const apiKey = apiKeys.find(key => key.id === keyId);
      if (apiKey) {
        await updateApiKey(keyId, { isActive: !apiKey.isActive });
        showToastMessage('Estado de la API Key actualizado');
      }
    } catch {
      showToastMessage('Error al actualizar el estado', 'error');
    }
  };

  const handleCopyKey = async (key: string) => {
    try {
      await navigator.clipboard.writeText(key);
      showToastMessage('API Key copiada al portapapeles');
    } catch {
      showToastMessage('Error al copiar la API Key', 'error');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const maskApiKey = (key: string) => {
    if (key.length <= 8) return key;
    return `${key.substring(0, 4)}...${key.substring(key.length - 4)}`;
  };

  const getStatusColor = (isActive: boolean, expired: boolean) => {
    if (expired) return 'text-red-600 bg-red-50 border-red-200';
    if (isActive) return 'text-green-600 bg-green-50 border-green-200';
    return 'text-gray-600 bg-gray-50 border-gray-200';
  };

  const getStatusText = (isActive: boolean, expired: boolean) => {
    if (expired) return 'Expirada';
    if (isActive) return 'Activa';
    return 'Inactiva';
  };

  if (loading && apiKeys.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <Loading size="lg" text="Cargando API Keys..." />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <div className={cn('space-y-6', className)}>
        {/* Header */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-foreground">
                  Gestión de API Keys
                </h2>
                <p className="text-sm text-muted-foreground">
                  Administra tus claves de API para acceder a los servicios de procesamiento
                </p>
              </div>
              <Button onClick={() => setShowCreateModal(true)}>
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Nueva API Key
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center p-4 bg-secondary/30 rounded-lg">
                <p className="text-2xl font-bold text-foreground">{apiKeys.length}</p>
                <p className="text-sm text-muted-foreground">Total de Keys</p>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <p className="text-2xl font-bold text-green-600">{apiKeys.filter(key => key.isActive).length}</p>
                <p className="text-sm text-green-700">Keys Activas</p>
              </div>
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <p className="text-2xl font-bold text-red-600">
                  {apiKeys.filter(key => key.expiresAt && new Date(key.expiresAt) < new Date()).length}
                </p>
                <p className="text-sm text-red-700">Keys Expiradas</p>
              </div>
            </div>
          </CardContent>
        </Card>

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

        {/* API Keys List */}
        {apiKeys.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center">
              <svg className="w-12 h-12 mx-auto text-muted-foreground mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
              </svg>
              <h3 className="text-lg font-medium text-foreground mb-2">
                No tienes API Keys
              </h3>
              <p className="text-sm text-muted-foreground mb-4">
                Crea tu primera API Key para comenzar a usar los servicios de procesamiento
              </p>
              <Button onClick={() => setShowCreateModal(true)}>
                Crear primera API Key
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {apiKeys.map((apiKey) => {
              const expired = !!(apiKey.expiresAt && new Date(apiKey.expiresAt) < new Date());
              return (
                <Card key={apiKey.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-3 mb-2">
                          <h3 className="text-lg font-semibold text-foreground truncate">
                            {apiKey.name}
                          </h3>
                          <span className={cn(
                            'px-2 py-1 text-xs font-medium rounded-full border',
                            getStatusColor(apiKey.isActive, expired)
                          )}>
                            {getStatusText(apiKey.isActive, expired)}
                          </span>
                        </div>

                        <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                          <span>Creada: {formatDate(apiKey.createdAt)}</span>
                          <span>Último uso: {apiKey.lastUsedAt ? formatDate(apiKey.lastUsedAt) : 'Nunca'}</span>
                          {apiKey.expiresAt && (
                            <span>Expira: {formatDate(apiKey.expiresAt)}</span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center space-x-2 ml-4">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleToggleStatus(apiKey.id)}
                          disabled={loading || !!expired}
                          title={apiKey.isActive ? 'Desactivar' : 'Activar'}
                        >
                          {apiKey.isActive ? (
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636" />
                            </svg>
                          ) : (
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          )}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRegenerateKey(apiKey.id)}
                          disabled={loading}
                          title="Regenerar clave"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setSelectedKey(apiKey);
                            setShowDeleteModal(true);
                          }}
                          disabled={loading}
                          title="Eliminar"
                          className="text-destructive hover:text-destructive"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </Button>
                      </div>
                    </div>
                    <div className="mt-4 p-3 bg-secondary/30 rounded-lg">
                      <div className="flex items-center justify-between">
                        <code className="text-sm font-mono text-foreground">
                          {maskApiKey(apiKey.key)}
                        </code>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleCopyKey(apiKey.key)}
                          title="Copiar clave completa"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                          </svg>
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {/* Create API Key Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Crear nueva API Key"
      >
        <div className="space-y-4">
          <Input
            label="Nombre"
            value={newKeyName}
            onChange={(e) => setNewKeyName(e.target.value)}
            placeholder="Mi API Key"
            required
          />
          <Input
            label="Descripción (opcional)"
            value={newKeyDescription}
            onChange={(e) => setNewKeyDescription(e.target.value)}
            placeholder="Descripción de la API Key"
          />
          <div className="flex justify-end space-x-2 pt-4">
            <Button
              variant="outline"
              onClick={() => setShowCreateModal(false)}
              disabled={loading}
            >
              Cancelar
            </Button>
            <Button
              onClick={handleCreateKey}
              loading={loading}
            >
              Crear API Key
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        title="Confirmar eliminación"
      >
        <div className="space-y-4">
          <p className="text-sm text-foreground">
            ¿Estás seguro de que quieres eliminar la API Key "{selectedKey?.name}"?
          </p>
          <p className="text-sm text-muted-foreground">
            Esta acción no se puede deshacer y cualquier aplicación que use esta clave dejará de funcionar.
          </p>
          <div className="flex justify-end space-x-2 pt-4">
            <Button
              variant="outline"
              onClick={() => setShowDeleteModal(false)}
              disabled={loading}
            >
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteKey}
              loading={loading}
            >
              Eliminar
            </Button>
          </div>
        </div>
      </Modal>

      {/* Toast Notification */}
      {showToast && (
        <Toast
          id="toast"
          title={toastType === 'success' ? 'Éxito' : 'Error'}
          type={toastType}
          message={toastMessage}
          onClose={() => setShowToast(false)}
          duration={3000}
        />
      )}
    </>
  );
};

export default ApiKeyManager;