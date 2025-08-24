import React, { useState, useEffect } from 'react';
import { MainLayout } from '../components/layout';
import { Button, Card, Loading, Modal, Input } from '../components/ui';
import { UsageChart } from '../components/features';
import useUsageTracking from '../hooks/useUsageTracking';
import usePermissions from '../hooks/usePermissions';
import { cn } from '../utils';

const Usage: React.FC = () => {
  const {
    usageData,
    costBreakdown,
    isLoading,
    error,
    fetchUsageData,
    exportUsageData,
  } = useUsageTracking();

  const { hasPermission } = usePermissions();
  const [selectedPeriod, setSelectedPeriod] = useState<'day' | 'week' | 'month' | 'year'>('month');
  const [showExportModal, setShowExportModal] = useState(false);
  const [showBillingModal, setShowBillingModal] = useState(false);
  const [dateRange, setDateRange] = useState({
    startDate: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0],
    endDate: new Date().toISOString().split('T')[0],
  });

  // Load data on mount and when period changes
  useEffect(() => {
    fetchUsageData();
  }, [selectedPeriod, fetchUsageData]);

  // Check permissions
  const canViewBilling = hasPermission('billing', 'read');
  const canExportReports = hasPermission('reports', 'export');

  // Calculate totals
  const totalRequests = usageData?.total?.requests || 0;
  const totalCost = usageData?.total?.cost || 0;
  const averageResponseTime = 0; // Will be calculated from usage history if needed
  const successRate = usageData?.total ? (usageData.total.successfulRequests / Math.max(usageData.total.successfulRequests + usageData.total.failedRequests, 1)) * 100 : 0;

  // Get current month data for comparison
  const currentMonthRequests = usageData?.monthly?.requests || 0;
  const currentMonthCost = usageData?.monthly?.cost || 0;

  // Get most used provider
  const mostUsedProvider = costBreakdown?.byProvider 
    ? Object.entries(costBreakdown.byProvider).reduce((prev, [name, cost]) => 
        (!prev || cost > prev.cost) ? { name, cost } : prev
      , null as { name: string; cost: number } | null)
    : null;

  const handleExportReport = async (format: 'pdf' | 'excel' | 'csv') => {
    try {
      const exportFormat = format === 'excel' ? 'csv' : format as 'csv' | 'json' | 'pdf';
      await exportUsageData(exportFormat);
      setShowExportModal(false);
    } catch (error) {
      console.error('Error exporting report:', error);
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Uso y Facturación</h1>
            <p className="text-muted-foreground">
              Monitorea el uso de la API y los costos de procesamiento
            </p>
          </div>
          <div className="flex items-center gap-2">
            {canExportReports && (
              <Button
                variant="outline"
                onClick={() => setShowExportModal(true)}
                leftIcon={
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                }
              >
                Exportar reporte
              </Button>
            )}
            {canViewBilling && (
              <Button
                onClick={() => setShowBillingModal(true)}
                leftIcon={
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                }
              >
                Ver facturación
              </Button>
            )}
            <Button
              onClick={() => {
                fetchUsageData();
              }}
              leftIcon={
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              }
              disabled={isLoading}
            >
              Actualizar
            </Button>
          </div>
        </div>

        {/* Period Selector */}
        <Card>
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-foreground">Período de análisis</h3>
            <div className="flex border border-border rounded-lg p-1">
              {(['day', 'week', 'month', 'year'] as const).map((period) => (
                <button
                  key={period}
                  onClick={() => setSelectedPeriod(period)}
                  className={cn(
                    'px-3 py-1 rounded text-sm transition-colors capitalize',
                    selectedPeriod === period
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:text-foreground'
                  )}
                >
                  {period === 'day' ? 'Día' : period === 'week' ? 'Semana' : period === 'month' ? 'Mes' : 'Año'}
                </button>
              ))}
            </div>
          </div>
        </Card>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Requests totales</p>
                <p className="text-2xl font-bold text-foreground">
                  {totalRequests.toLocaleString()}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {currentMonthRequests.toLocaleString()} este mes
                </p>
              </div>
              <div className="text-primary">
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Costo total</p>
                <p className="text-2xl font-bold text-foreground">
                  ${totalCost.toFixed(2)}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  ${currentMonthCost.toFixed(2)} este mes
                </p>
              </div>
              <div className="text-green-600">
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Tiempo promedio</p>
                <p className="text-2xl font-bold text-foreground">
                  {averageResponseTime.toFixed(0)}ms
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  Tiempo de respuesta
                </p>
              </div>
              <div className="text-blue-600">
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Tasa de éxito</p>
                <p className="text-2xl font-bold text-foreground">
                  {successRate.toFixed(1)}%
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  Requests exitosos
                </p>
              </div>
              <div className="text-green-600">
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </Card>
        </div>

        {/* Provider Statistics */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-foreground">Proveedores de IA</h3>
              {isLoading ? (
            <div className="flex justify-center py-8">
              <Loading size="md" />
            </div>
          ) : costBreakdown?.byProvider ? (
            <div className="space-y-3">
              {Object.entries(costBreakdown.byProvider).map(([name, cost]: [string, number]) => (
                    <div key={name} className="flex items-center justify-between p-3 bg-secondary/20 rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className={cn(
                          'w-3 h-3 rounded-full',
                          'bg-green-500' // Assume active for now
                        )} />
                        <div>
                          <p className="font-medium text-foreground">{name}</p>
                          <p className="text-sm text-muted-foreground">
                            Provider
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-medium text-foreground">
                          ${cost.toFixed(2)}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          Provider
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-muted-foreground py-8">
                  No hay datos de proveedores disponibles
                </p>
              )}
            </div>
          </Card>

          <Card>
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-foreground">Resumen del período</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-secondary/20 rounded-lg">
                  <span className="text-foreground">Proveedor más usado:</span>
                  <span className="font-medium text-foreground">
                    {mostUsedProvider?.name || 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between items-center p-3 bg-secondary/20 rounded-lg">
                  <span className="text-foreground">Costo promedio por request:</span>
                  <span className="font-medium text-foreground">
                    ${totalRequests > 0 ? (totalCost / totalRequests).toFixed(4) : '0.0000'}
                  </span>
                </div>
                <div className="flex justify-between items-center p-3 bg-secondary/20 rounded-lg">
                  <span className="text-foreground">Requests fallidos:</span>
                  <span className="font-medium text-foreground">
                    {(usageData?.total?.failedRequests || 0).toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between items-center p-3 bg-secondary/20 rounded-lg">
                  <span className="text-foreground">Ahorro por fallback:</span>
                  <span className="font-medium text-green-600">
                    $0.00
                  </span>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Usage Charts */}
        <Card>
          {isLoading && !usageData ? (
            <div className="flex justify-center py-12">
              <Loading size="lg" text="Cargando datos de uso..." />
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <div className="text-destructive mb-2">
                <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-foreground mb-2">Error al cargar datos</h3>
              <p className="text-muted-foreground mb-4">{error}</p>
              <Button onClick={() => {
                fetchUsageData();
              }}>
                Reintentar
              </Button>
            </div>
          ) : (
            <UsageChart period={selectedPeriod} />
          )}
        </Card>

        {/* Cost Optimization Tips */}
<Card>
          <div className="flex items-start gap-3">
            <div className="text-blue-600 mt-0.5">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h3 className="font-medium text-foreground mb-2">Consejos para optimizar costos</h3>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Configura límites de uso para controlar gastos</li>
                <li>• Utiliza el sistema de fallback para reducir costos</li>
                <li>• Monitorea regularmente el uso por proveedor</li>
                <li>• Considera ajustar la calidad de procesamiento según tus necesidades</li>
                <li>• Implementa caché para evitar requests duplicados</li>
              </ul>
            </div>
          </div>
        </Card>
      </div>

      {/* Export Report Modal */}
      <Modal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        title="Exportar reporte de uso"
        size="md"
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Fecha inicio"
              type="date"
              value={dateRange.startDate}
              onChange={(e) => setDateRange(prev => ({ ...prev, startDate: e.target.value }))}
            />
            <Input
              label="Fecha fin"
              type="date"
              value={dateRange.endDate}
              onChange={(e) => setDateRange(prev => ({ ...prev, endDate: e.target.value }))}
            />
          </div>
          
          <div className="space-y-2">
            <p className="text-sm font-medium text-foreground">Formato de exportación:</p>
            <div className="grid grid-cols-1 gap-2">
              <Button
                variant="outline"
                onClick={() => handleExportReport('pdf')}
                leftIcon={
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                }
              >
                PDF (Reporte completo)
              </Button>
              <Button
                variant="outline"
                onClick={() => handleExportReport('excel')}
                leftIcon={
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                }
              >
                Excel (Datos detallados)
              </Button>
              <Button
                variant="outline"
                onClick={() => handleExportReport('csv')}
                leftIcon={
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                }
              >
                CSV (Datos básicos)
              </Button>
            </div>
          </div>
        </div>
      </Modal>

      {/* Billing Modal */}
      <Modal
        isOpen={showBillingModal}
        onClose={() => setShowBillingModal(false)}
        title="Información de facturación"
        size="lg"
      >
        <div className="space-y-6">
          <div className="text-center">
            <p className="text-3xl font-bold text-foreground">${currentMonthCost.toFixed(2)}</p>
            <p className="text-muted-foreground">Costo del mes actual</p>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-4 bg-secondary/20 rounded-lg">
              <p className="text-xl font-bold text-foreground">{currentMonthRequests.toLocaleString()}</p>
              <p className="text-sm text-muted-foreground">Requests este mes</p>
            </div>
            <div className="text-center p-4 bg-secondary/20 rounded-lg">
              <p className="text-xl font-bold text-foreground">
                ${currentMonthRequests > 0 ? (currentMonthCost / currentMonthRequests).toFixed(4) : '0.0000'}
              </p>
              <p className="text-sm text-muted-foreground">Costo por request</p>
            </div>
          </div>
          
          <div className="space-y-2">
            <h4 className="font-medium text-foreground">Desglose por proveedor (mes actual):</h4>
            {costBreakdown?.byProvider ? Object.entries(costBreakdown.byProvider).map(([name, cost]: [string, number]) => {
              
              return (
                <div key={name} className="flex justify-between items-center p-2 bg-secondary/10 rounded">
                  <span className="text-foreground">{name}</span>
                  <span className="font-medium text-foreground">${(cost || 0).toFixed(2)}</span>
                </div>
              );
            }) : []}
          </div>
          
          <div className="flex justify-end">
            <Button onClick={() => setShowBillingModal(false)}>Cerrar</Button>
          </div>
        </div>
      </Modal>
    </MainLayout>
  );
};

export default Usage;