import React, { useState, useEffect } from 'react';
import { cn } from '../../utils/helpers';
import { Card, CardContent, CardHeader, Button, Loading } from '../ui';
import useUsageTracking from '../../hooks/useUsageTracking';
// Removed unused imports: UsageData, UsageMetrics, CostBreakdown

export interface UsageChartProps {
  period?: 'day' | 'week' | 'month' | 'year';
  showCosts?: boolean;
  showProviders?: boolean;
  className?: string;
}

const UsageChart: React.FC<UsageChartProps> = ({
  period = 'month',
  showCosts = true,
  showProviders = true,
  className,
}) => {
  const [selectedPeriod, setSelectedPeriod] = useState(period);
  const [selectedTab, setSelectedTab] = useState<'usage' | 'costs' | 'providers'>('usage');

  const {
    usage,
    metrics,
    costs,
    loading,
    error,
    fetchUsage,
    fetchMetrics,
    fetchCosts,
    exportData,
    // getUsagePercentage, // Commented out as it's not used
  } = useUsageTracking();

  useEffect(() => {
    fetchUsage({ period: selectedPeriod });
    fetchMetrics({ period: selectedPeriod });
    if (showCosts) {
      fetchCosts({ period: selectedPeriod });
    }
  }, [selectedPeriod, showCosts, fetchUsage, fetchMetrics, fetchCosts]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 4,
    }).format(amount);
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('es-ES').format(num);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('es-ES', {
      month: 'short',
      day: 'numeric',
    });
  };

  const getProviderColor = (provider: string) => {
    const colors: Record<string, string> = {
      openai: 'bg-green-500',
      deepseek: 'bg-blue-500',
      gemini: 'bg-purple-500',
      claude: 'bg-orange-500',
    };
    return colors[provider.toLowerCase()] || 'bg-gray-500';
  };

  const renderUsageChart = () => {
    if (!usage || usage.length === 0) {
      return (
        <div className="text-center py-8">
          <p className="text-muted-foreground">No hay datos de uso disponibles</p>
        </div>
      );
    }

    const maxRequests = Math.max(...usage.map((d: { requests: number }) => d.requests));

    return (
      <div className="space-y-4">
        <div className="h-64 flex items-end space-x-2">
          {usage.map((data: { requests: number; date: string }, index: number) => (
            <div key={index} className="flex-1 flex flex-col items-center">
              <div
                className="w-full bg-primary rounded-t transition-all duration-300 hover:bg-primary/80"
                style={{
                  height: `${(data.requests / maxRequests) * 200}px`,
                  minHeight: '4px',
                }}
                title={`${formatNumber(data.requests)} solicitudes`}
              />
              <span className="text-xs text-muted-foreground mt-2">
                {formatDate(data.date)}
              </span>
            </div>
          ))}
        </div>
        <div className="text-center">
          <p className="text-sm text-muted-foreground">
            Solicitudes por {selectedPeriod === 'day' ? 'hora' : 'día'}
          </p>
        </div>
      </div>
    );
  };

  const renderCostsChart = () => {
    if (!costs || costs.length === 0) {
      return (
        <div className="text-center py-8">
          <p className="text-muted-foreground">No hay datos de costos disponibles</p>
        </div>
      );
    }

    const maxCost = Math.max(...costs.map((d: { totalCost: number }) => d.totalCost));

    return (
      <div className="space-y-4">
        <div className="h-64 flex items-end space-x-2">
          {costs.map((data: { totalCost: number; date: string }, index: number) => (
            <div key={index} className="flex-1 flex flex-col items-center">
              <div
                className="w-full bg-green-500 rounded-t transition-all duration-300 hover:bg-green-400"
                style={{
                  height: `${(data.totalCost / maxCost) * 200}px`,
                  minHeight: '4px',
                }}
                title={`${formatCurrency(data.totalCost)}`}
              />
              <span className="text-xs text-muted-foreground mt-2">
                {formatDate(data.date)}
              </span>
            </div>
          ))}
        </div>
        <div className="text-center">
          <p className="text-sm text-muted-foreground">
            Costos por {selectedPeriod === 'day' ? 'hora' : 'día'}
          </p>
        </div>
      </div>
    );
  };

  const renderProvidersChart = () => {
    if (!metrics?.providerBreakdown || Object.keys(metrics.providerBreakdown).length === 0) {
      return (
        <div className="text-center py-8">
          <p className="text-muted-foreground">No hay datos de proveedores disponibles</p>
        </div>
      );
    }

    const providers = Object.entries(metrics.providerBreakdown) as [string, { requests: number; cost: number }][];
    const totalRequests = providers.reduce((sum, [, data]) => sum + data.requests, 0);

    return (
      <div className="space-y-6">
        {/* Pie Chart Representation */}
        <div className="flex justify-center">
          <div className="w-48 h-48 rounded-full border-8 border-gray-200 relative overflow-hidden">
            {providers.map(([provider, data], index) => {
              const percentage = (data.requests / totalRequests) * 100;
              const rotation = providers
                .slice(0, index)
                .reduce((sum, [, d]) => sum + (d.requests / totalRequests) * 360, 0);
              
              return (
                <div
                  key={provider}
                  className={cn(
                    'absolute inset-0 rounded-full',
                    getProviderColor(provider)
                  )}
                  style={{
                    clipPath: `polygon(50% 50%, 50% 0%, ${50 + 50 * Math.cos((rotation - 90) * Math.PI / 180)}% ${50 + 50 * Math.sin((rotation - 90) * Math.PI / 180)}%, ${50 + 50 * Math.cos((rotation + percentage * 3.6 - 90) * Math.PI / 180)}% ${50 + 50 * Math.sin((rotation + percentage * 3.6 - 90) * Math.PI / 180)}%)`,
                  }}
                />
              );
            })}
          </div>
        </div>

        {/* Legend */}
        <div className="space-y-3">
          {providers.map(([provider, data]) => {
            const percentage = (data.requests / totalRequests) * 100;
            return (
              <div key={provider} className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className={cn('w-4 h-4 rounded', getProviderColor(provider))} />
                  <span className="text-sm font-medium text-foreground capitalize">
                    {provider}
                  </span>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-foreground">
                    {formatNumber(data.requests)} ({percentage.toFixed(1)}%)
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {formatCurrency(data.cost)}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const handleExport = async () => {
    try {
      await exportData({
        period: selectedPeriod,
        format: 'csv',
        includeMetrics: true,
        includeCosts: showCosts,
      });
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  if (loading && !usage && !metrics) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <Loading size="lg" text="Cargando datos de uso..." />
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
      {/* Summary Cards */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-foreground">
                {formatNumber(metrics.totalRequests)}
              </p>
              <p className="text-sm text-muted-foreground">Solicitudes totales</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-foreground">
                {formatNumber(metrics.successfulRequests)}
              </p>
              <p className="text-sm text-muted-foreground">Exitosas</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-red-600">
                {formatNumber(metrics.failedRequests)}
              </p>
              <p className="text-sm text-muted-foreground">Fallidas</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-green-600">
                {formatCurrency(metrics.totalCost)}
              </p>
              <p className="text-sm text-muted-foreground">Costo total</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Chart */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-foreground">
              Análisis de uso y costos
            </h3>
            <div className="flex items-center space-x-2">
              {/* Period Selector */}
              <div className="flex bg-secondary rounded-lg p-1">
                {(['day', 'week', 'month', 'year'] as const).map((p) => (
                  <button
                    key={p}
                    onClick={() => setSelectedPeriod(p)}
                    className={cn(
                      'px-3 py-1 text-sm rounded transition-colors',
                      selectedPeriod === p
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted-foreground hover:text-foreground'
                    )}
                  >
                    {p === 'day' ? 'Día' : p === 'week' ? 'Semana' : p === 'month' ? 'Mes' : 'Año'}
                  </button>
                ))}
              </div>
              <Button variant="outline" size="sm" onClick={handleExport}>
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Exportar
              </Button>
            </div>
          </div>
          {/* Tab Selector */}
          <div className="flex bg-secondary rounded-lg p-1">
            <button
              onClick={() => setSelectedTab('usage')}
              className={cn(
                'flex-1 px-3 py-2 text-sm rounded transition-colors',
                selectedTab === 'usage'
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:text-foreground'
              )}
            >
              Uso
            </button>
            {showCosts && (
              <button
                onClick={() => setSelectedTab('costs')}
                className={cn(
                  'flex-1 px-3 py-2 text-sm rounded transition-colors',
                  selectedTab === 'costs'
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                )}
              >
                Costos
              </button>
            )}
            {showProviders && (
              <button
                onClick={() => setSelectedTab('providers')}
                className={cn(
                  'flex-1 px-3 py-2 text-sm rounded transition-colors',
                  selectedTab === 'providers'
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                )}
              >
                Proveedores
              </button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {selectedTab === 'usage' && renderUsageChart()}
          {selectedTab === 'costs' && renderCostsChart()}
          {selectedTab === 'providers' && renderProvidersChart()}
        </CardContent>
      </Card>
    </div>
  );
};

export default UsageChart;