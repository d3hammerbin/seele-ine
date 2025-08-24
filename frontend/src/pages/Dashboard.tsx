import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, Button, Loading } from '../components/ui';
import { FileUpload, ProcessingStatus, CredentialCard, UsageChart } from '../components/features';
import type { CredentialItem } from '../hooks/types';
import type { CredentialData, CredentialStatus } from '../types/credentials';
import { useAuthContext } from '../hooks/useAuthContext';
import useCredentialProcessing from '../hooks/useCredentialProcessing';
import useUsageTracking from '../hooks/useUsageTracking';

const Dashboard: React.FC = () => {
  const [recentCredentials, setRecentCredentials] = useState<CredentialItem[]>([]);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const { user } = useAuthContext();
  const { credentials, isLoading: processingLoading } = useCredentialProcessing();
  const { usageData, isLoading: usageLoading } = useUsageTracking();

  useEffect(() => {
    // Mock recent credentials - in real app, this would come from an API
    const mockCredentials: CredentialItem[] = [
      {
        id: '1',
        filename: 'ine_001.jpg',
        fileSize: 2048000,
        fileType: 'image/jpeg',
        uploadedAt: new Date().toISOString(),
        status: 'completed',
        progress: 100,
        result: {
          extractedData: {
            nombre: 'Juan Carlos',
            apellidoPaterno: 'García',
            apellidoMaterno: 'López',
            curp: 'GALJ850315HDFRRN09',
            clave: 'GALJC85031501H200',
            fechaNacimiento: '1985-03-15',
            sexo: 'H',
            estado: 'Ciudad de México',
          },
          confidence: 0.95,
          metadata: {}
        },
        processingTime: 1250,
        provider: 'OpenAI',
        cost: 0.0045,
      },
      {
        id: '2',
        filename: 'ine_002.pdf',
        fileSize: 1856000,
        fileType: 'application/pdf',
        uploadedAt: new Date(Date.now() - 86400000).toISOString(), // Yesterday
        status: 'completed',
        progress: 100,
        result: {
          extractedData: {
            nombre: 'María Elena',
            apellidoPaterno: 'Rodríguez',
            apellidoMaterno: 'Martínez',
            curp: 'ROMM920708MDFDRR05',
            clave: 'ROMME92070802M100',
            fechaNacimiento: '1992-07-08',
            sexo: 'M',
            estado: 'Jalisco',
          },
          confidence: 0.88,
          metadata: {}
        },
        processingTime: 980,
        provider: 'DeepSeek',
        cost: 0.0032,
      },
    ];
    setRecentCredentials(mockCredentials);
  }, []);

  const handleUploadComplete = (files: File[]) => {
    console.log('Files uploaded:', files);
  };

  const handleProcessingStart = (jobId: string) => {
    setCurrentJobId(jobId);
  };

  const handleJobComplete = () => {
    // Refresh recent credentials - would call API in real app
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Buenos días';
    if (hour < 18) return 'Buenas tardes';
    return 'Buenas noches';
  };

  const getQuickStats = () => {
    const today = new Date().toDateString();
    const todayCredentials = credentials.filter((credential: any) => 
      new Date(credential.uploadedAt).toDateString() === today
    );
    
    return {
      todayJobs: todayCredentials.length,
      completedToday: todayCredentials.filter((credential: any) => credential.status === 'completed').length,
      processingJobs: credentials.filter((credential: any) => credential.status === 'processing').length,
    };
  };

  const stats = getQuickStats();

  return (
    <div className="p-6 space-y-6">
      {/* Welcome Section */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">
          {getGreeting()}, {user?.firstName || 'Usuario'}
        </h1>
        <p className="text-muted-foreground">
          Bienvenido al panel de control de Seele INE. Aquí puedes procesar credenciales y monitorear tu uso.
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-primary mb-1">
              {stats.todayJobs}
            </div>
            <div className="text-sm text-muted-foreground">
              Trabajos hoy
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-green-600 mb-1">
              ${usageData?.total?.cost?.toFixed(2) || '0.00'}
            </div>
            <div className="text-sm text-muted-foreground">
              Total Cost
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-blue-600 mb-1">
              {((usageData?.total?.successfulRequests || 0) / Math.max((usageData?.total?.successfulRequests || 0) + (usageData?.total?.failedRequests || 0), 1) * 100).toFixed(1)}%
            </div>
            <div className="text-sm text-muted-foreground">
              Success Rate
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-purple-600 mb-1">
              {usageData?.total?.requests || 0}
            </div>
            <div className="text-sm text-muted-foreground">
              Total esta semana
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* File Upload Section */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <h2 className="text-xl font-semibold text-foreground">
                Procesar credenciales
              </h2>
              <p className="text-sm text-muted-foreground">
                Sube archivos de credenciales INE para extraer información
              </p>
            </CardHeader>
            <CardContent>
              <FileUpload
                onUploadComplete={handleUploadComplete}
                onProcessingStart={handleProcessingStart}
                maxFiles={5}
              />
            </CardContent>
          </Card>

          {/* Processing Status */}
          {(currentJobId || processingLoading) && (
            <ProcessingStatus
              jobId={currentJobId || undefined}
              showHistory={false}
              onJobComplete={handleJobComplete}
            />
          )}
        </div>

        {/* Recent Activity */}
        <div className="space-y-6">
          {/* Usage Overview */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-foreground">
                  Uso esta semana
                </h2>
                <Button variant="outline" size="sm">
                  <a href="/usage" className="flex items-center">
                    Ver detalles
                    <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </a>
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {usageLoading ? (
                <div className="flex justify-center py-8">
                  <Loading size="md" />
                </div>
              ) : (
                <UsageChart
                  period="week"
                  showCosts={false}
                  showProviders={false}
                />
              )}
            </CardContent>
          </Card>

          {/* Recent Credentials */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-foreground">
                  Credenciales recientes
                </h2>
                <Button variant="outline" size="sm">
                  <a href="/credentials" className="flex items-center">
                    Ver todas
                    <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </a>
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {recentCredentials.length === 0 ? (
                <div className="text-center py-8">
                  <svg className="w-12 h-12 mx-auto text-muted-foreground mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <h3 className="text-lg font-medium text-foreground mb-2">
                    No hay credenciales procesadas
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Sube tu primera credencial para comenzar
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {recentCredentials.slice(0, 3).map((credential: CredentialItem) => {
                    // Convert CredentialItem to CredentialData format for CredentialCard
                     const credentialData: CredentialData = {
                      id: credential.id,
                      userId: 'current-user', // This should come from auth context
                      fileName: credential.filename,
                      originalName: credential.filename,
                      fileSize: credential.fileSize,
                      mimeType: credential.fileType,
                      uploadedAt: credential.uploadedAt,
                      status: credential.status as CredentialStatus,
                      extractedData: credential.result?.extractedData,
                      isArchived: false,
                      createdAt: credential.uploadedAt,
                      updatedAt: credential.uploadedAt,
                    };
                    
                    return (
                      <CredentialCard
                        key={credential.id}
                        credential={credentialData}
                        showActions={false}
                      />
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <h2 className="text-xl font-semibold text-foreground">
            Acciones rápidas
          </h2>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Button variant="outline" className="h-20 flex-col space-y-2">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
              </svg>
              <span className="text-sm">Gestionar API Keys</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col space-y-2">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <span className="text-sm">Ver reportes</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col space-y-2">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span className="text-sm">Exportar datos</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col space-y-2">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span className="text-sm">Configuración</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;