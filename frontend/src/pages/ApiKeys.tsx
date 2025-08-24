import React, { useEffect, useState } from 'react';
import { MainLayout } from '../components/layout';
import { Button, Card, Loading, Modal, Input } from '../components/ui';
import { ApiKeyManager } from '../components/features';
import useApiKeys from '../hooks/useApiKeys';
import usePermissions from '../hooks/usePermissions';
import type { CreateApiKeyData, ApiKeyItem } from '../hooks/types';


const ApiKeys: React.FC = () => {
  const {
    apiKeys,
    isLoading,
    error,
    refreshApiKeys,
    createApiKey,
  } = useApiKeys();

  const { hasPermission } = usePermissions();
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Load API keys on mount
  useEffect(() => {
    refreshApiKeys();
  }, [refreshApiKeys]);

  // Check permissions
  const canCreateApiKeys = hasPermission('api_keys', 'create');



  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-foreground">API Keys</h1>
            <p className="text-muted-foreground">
              Gestiona las claves de API para acceder a los servicios de procesamiento
            </p>
          </div>
          {canCreateApiKeys && (
            <Button
              onClick={() => setShowCreateModal(true)}
              leftIcon={
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              }
            >
              Nueva API Key
            </Button>
          )}
        </div>

        {/* API Key Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total API Keys</p>
                <p className="text-2xl font-bold text-foreground">{apiKeys.length}</p>
              </div>
              <div className="text-primary">
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                </svg>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Activas</p>
                <p className="text-2xl font-bold text-green-600">
                  {apiKeys.filter(key => key.isActive).length}
                </p>
              </div>
              <div className="text-green-600">
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Inactivas</p>
                <p className="text-2xl font-bold text-yellow-600">
                  {apiKeys.filter(key => !key.isActive).length}
                </p>
              </div>
              <div className="text-yellow-600">
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Uso este mes</p>
                <p className="text-2xl font-bold text-primary">
                  {apiKeys.reduce((total, key) => total + (key.usage?.requestsThisMonth || 0), 0)}
                </p>
              </div>
              <div className="text-primary">
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
            </div>
          </Card>
        </div>

        {/* Security Notice */}
        <Card>
          <div className="flex items-start gap-3">
            <div className="text-yellow-600 mt-0.5">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <div>
              <h3 className="font-medium text-foreground mb-1">Importante: Seguridad de API Keys</h3>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Nunca compartas tus API keys públicamente</li>
                <li>• Guarda las claves en un lugar seguro después de crearlas</li>
                <li>• Regenera las claves regularmente por seguridad</li>
                <li>• Desactiva inmediatamente cualquier clave comprometida</li>
              </ul>
            </div>
          </div>
        </Card>

        {/* API Key Manager */}
        <Card>
          {isLoading && apiKeys.length === 0 ? (
          <div className="flex justify-center py-12">
            <Loading size="lg" text="Cargando API keys..." />
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <div className="text-destructive mb-2">
                <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-foreground mb-2">Error al cargar API keys</h3>
              <p className="text-muted-foreground mb-4">{error}</p>
              <Button onClick={() => refreshApiKeys()}>Reintentar</Button>
            </div>
          ) : (
            <ApiKeyManager />
          )}
        </Card>

        {/* API Documentation */}
        <Card>
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-foreground">Documentación de la API</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <h4 className="font-medium text-foreground">Endpoints principales:</h4>
                <div className="space-y-1 text-sm text-muted-foreground">
                  <p><code className="bg-secondary px-1 rounded">POST /api/v1/credentials/process</code> - Procesar credencial</p>
                  <p><code className="bg-secondary px-1 rounded">GET /api/v1/credentials</code> - Listar credenciales</p>
                  <p><code className="bg-secondary px-1 rounded">GET /api/v1/credentials/{'{id}'}</code> - Obtener credencial</p>
                  <p><code className="bg-secondary px-1 rounded">DELETE /api/v1/credentials/{'{id}'}</code> - Eliminar credencial</p>
                </div>
              </div>
              <div className="space-y-2">
                <h4 className="font-medium text-foreground">Autenticación:</h4>
                <div className="space-y-1 text-sm text-muted-foreground">
                  <p>Incluye tu API key en el header:</p>
                  <code className="block bg-secondary p-2 rounded text-xs">
                    Authorization: Bearer YOUR_API_KEY
                  </code>
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                leftIcon={
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                }
                onClick={() => window.open('/api/docs', '_blank')}
              >
                Ver documentación completa
              </Button>
              <Button
                variant="outline"
                leftIcon={
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                  </svg>
                }
                onClick={() => window.open('/api/examples', '_blank')}
              >
                Ver ejemplos de código
              </Button>
            </div>
          </div>
        </Card>
      </div>

      {/* Create API Key Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Crear nueva API Key"
        size="md"
      >
        <CreateApiKeyForm
          onSuccess={() => {
            setShowCreateModal(false);
            refreshApiKeys();
          }}
          onCancel={() => setShowCreateModal(false)}
          createApiKey={createApiKey}
        />
      </Modal>


    </MainLayout>
  );
};

// Create API Key Form Component
interface CreateApiKeyFormProps {
  onSuccess: () => void;
  onCancel: () => void;
  createApiKey: (data: CreateApiKeyData) => Promise<ApiKeyItem>;
}

const CreateApiKeyForm: React.FC<CreateApiKeyFormProps> = ({ onSuccess, onCancel, createApiKey }) => {
  const [createLoading, setCreateLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    permissions: [] as string[],
    rateLimit: 1000,
    expiresAt: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const availablePermissions = [
    { id: 'credentials.read', label: 'Leer credenciales' },
    { id: 'credentials.write', label: 'Crear credenciales' },
    { id: 'credentials.delete', label: 'Eliminar credenciales' },
    { id: 'credentials.process', label: 'Procesar credenciales' },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    const newErrors: Record<string, string> = {};
    if (!formData.name.trim()) {
      newErrors.name = 'El nombre es requerido';
    }
    if (formData.permissions.length === 0) {
      newErrors.permissions = 'Selecciona al menos un permiso';
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      setCreateLoading(true);
      await createApiKey({
        name: formData.name,
        permissions: formData.permissions,
        rateLimit: formData.rateLimit,
        expiresAt: formData.expiresAt || undefined,
      });
      onSuccess();
    } catch (error) {
      console.error('Error creating API key:', error);
    } finally {
      setCreateLoading(false);
    }
  };

  const handlePermissionChange = (permissionId: string, checked: boolean) => {
    setFormData(prev => ({
      ...prev,
      permissions: checked
        ? [...prev.permissions, permissionId]
        : prev.permissions.filter(p => p !== permissionId)
    }));
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input
        label="Nombre"
        value={formData.name}
        onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
        error={errors.name}
        placeholder="Mi API Key"
        required
        disabled={createLoading}
      />



      <div className="space-y-2">
        <label className="block text-sm font-medium text-foreground">
          Permisos *
        </label>
        <div className="space-y-2">
          {availablePermissions.map((permission) => (
            <label key={permission.id} className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.permissions.includes(permission.id)}
                onChange={(e) => handlePermissionChange(permission.id, e.target.checked)}
                disabled={createLoading}
                className="w-4 h-4 text-primary border-border rounded focus:outline-none"
              />
              <span className="text-sm text-foreground">{permission.label}</span>
            </label>
          ))}
        </div>
        {errors.permissions && (
          <p className="text-sm text-destructive">{errors.permissions}</p>
        )}
      </div>

      <Input
        label="Límite de requests por hora"
        type="number"
        value={formData.rateLimit}
        onChange={(e) => setFormData(prev => ({ ...prev, rateLimit: Number(e.target.value) }))}
        min={1}
        max={10000}
        disabled={createLoading}
      />

      <Input
        label="Fecha de expiración (opcional)"
        type="datetime-local"
        value={formData.expiresAt}
        onChange={(e) => setFormData(prev => ({ ...prev, expiresAt: e.target.value }))}
        disabled={createLoading}
        helperText="Deja vacío para que no expire"
      />

      <div className="flex justify-end gap-2 pt-4">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={createLoading}
        >
          Cancelar
        </Button>
        <Button
          type="submit"
          loading={createLoading}
            disabled={createLoading}
        >
          Crear API Key
        </Button>
      </div>
    </form>
  );
};



export default ApiKeys;