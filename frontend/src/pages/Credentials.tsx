import React, { useState, useEffect, useCallback } from 'react';
import { MainLayout } from '../components/layout';
import { Button, Input, Card, Loading, Modal } from '../components/ui';
import { FileUpload, ProcessingStatus, CredentialCard } from '../components/features';
import useCredentialProcessing from '../hooks/useCredentialProcessing';
import usePagination from '../hooks/usePagination';
import useSearch from '../hooks/useSearch';
import type { CredentialData } from '../types/credentials';
import { cn } from '../utils';

const Credentials: React.FC = () => {
  useCredentialProcessing(); // Keep the hook call but don't destructure anything
  
  const loading = false;
  const error = null;
  const currentJob = null;
  const jobHistory: unknown[] = [];
  
  // Mock credentials data for now
  const [credentials, setCredentials] = React.useState<CredentialData[]>([]);
  
  const fetchCredentials = useCallback(async () => {
    // TODO: Implement actual API call
    console.log('Fetching credentials...');
  }, []);
  
  const deleteCredential = async (id: string) => {
    // TODO: Implement actual API call
    setCredentials(prev => prev.filter(c => c.id !== id));
  };

  const [selectedCredentials, setSelectedCredentials] = useState<string[]>([]);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [filterStatus, setFilterStatus] = useState<'all' | 'processed' | 'processing' | 'error'>('all');
  const [sortBy, setSortBy] = useState<'date' | 'name' | 'confidence'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);

  // Search functionality
  const {
    query: searchQuery,
    results: searchResults,
    setQuery: handleSearch,
    clearResults,
  } = useSearch({
    debounceMs: 300,
  });

  // Pagination
  const {
    currentPage,
    totalPages,
    pageSize,
    startIndex,
    goToNextPage,
    goToPreviousPage,
    setPageSize,
  } = usePagination({
    initialPageSize: 12,
    totalItems: searchQuery ? searchResults.length : credentials.length,
  });

  // Filter and sort credentials
  const filteredAndSortedCredentials = React.useMemo(() => {
    let filtered = credentials;
    
    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter((credential) => 
        credential.extractedData?.fullName?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        credential.extractedData?.firstName?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        credential.extractedData?.lastName?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        credential.extractedData?.curp?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        credential.fileName?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Apply status filter
    if (filterStatus !== 'all') {
      filtered = filtered.filter((credential: CredentialData) => {
        switch (filterStatus) {
          case 'processed':
            return credential.status === 'completed';
          case 'processing':
            return credential.status === 'processing';
          case 'error':
            return credential.status === 'failed';
          default:
            return true;
        }
      });
    }

    // Apply sorting
    filtered.sort((a: CredentialData, b: CredentialData) => {
      let comparison = 0;
      
      switch (sortBy) {
        case 'date':
          comparison = new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
          break;
        case 'name': {
          const nameA = `${a.extractedData?.fullName || a.extractedData?.firstName || ''} ${a.extractedData?.lastName || ''}`;
          const nameB = `${b.extractedData?.fullName || b.extractedData?.firstName || ''} ${b.extractedData?.lastName || ''}`;
          comparison = nameA.localeCompare(nameB);
          break;
        }
        case 'confidence':
          // Use a default comparison since confidence is not directly available in CredentialData
          comparison = a.fileName.localeCompare(b.fileName);
          break;
      }
      
      return sortOrder === 'asc' ? comparison : -comparison;
    });

    return filtered.slice(startIndex, startIndex + pageSize);
  }, [searchQuery, credentials, filterStatus, sortBy, sortOrder, startIndex, pageSize]);

  // Load credentials on mount
  useEffect(() => {
    fetchCredentials();
  }, [fetchCredentials]);

  // Handle credential selection
  const handleSelectCredential = (credentialId: string) => {
    setSelectedCredentials(prev => 
      prev.includes(credentialId)
        ? prev.filter(id => id !== credentialId)
        : [...prev, credentialId]
    );
  };

  const handleSelectAll = () => {
    if (selectedCredentials.length === filteredAndSortedCredentials.length) {
      setSelectedCredentials([]);
    } else {
      setSelectedCredentials(filteredAndSortedCredentials.map((c: CredentialData) => c.id));
    }
  };

  // Handle bulk actions
  const handleBulkDelete = async () => {
    try {
      await Promise.all(selectedCredentials.map(id => deleteCredential(id)));
      setSelectedCredentials([]);
      setShowDeleteModal(false);
    } catch (error) {
      console.error('Error deleting credentials:', error);
    }
  };

  const handleBulkExport = async (format: 'json' | 'csv') => {
    try {
      const credentialsToExport = selectedCredentials.length > 0
        ? credentials.filter(c => selectedCredentials.includes(c.id))
        : filteredAndSortedCredentials;
      
      // Simple export implementation
      const dataStr = format === 'json' 
        ? JSON.stringify(credentialsToExport, null, 2)
        : 'Export functionality not implemented';
      
      const dataBlob = new Blob([dataStr], { type: format === 'json' ? 'application/json' : 'text/csv' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `credentials.${format}`;
      link.click();
      URL.revokeObjectURL(url);
      
      setShowExportModal(false);
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Credenciales</h1>
            <p className="text-muted-foreground">
              Gestiona y visualiza las credenciales INE procesadas
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={() => setShowUploadModal(true)}
              leftIcon={
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              }
            >
              Subir archivos
            </Button>
            <Button
              onClick={() => fetchCredentials()}
              leftIcon={
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              }
              disabled={loading}
            >
              Actualizar
            </Button>
          </div>
        </div>

        {/* Processing Status */}
        {(currentJob || jobHistory.length > 0) && (
          <Card>
            <ProcessingStatus />
          </Card>
        )}

        {/* Search and Filters */}
        <Card>
          <div className="space-y-4">
            {/* Search Bar */}
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <Input
                  placeholder="Buscar por nombre, CURP o archivo..."
                  value={searchQuery}
                  onChange={(e) => handleSearch(e.target.value)}
                  leftIcon={
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  }
                  rightIcon={
                    searchQuery && (
                      <button
                        onClick={clearResults}
                        className="text-muted-foreground hover:text-foreground"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    )
                  }
                />
              </div>
              
              {/* View Mode Toggle */}
              <div className="flex border border-border rounded-lg p-1">
                <button
                  onClick={() => setViewMode('grid')}
                  className={cn(
                    'px-3 py-1 rounded text-sm transition-colors',
                    viewMode === 'grid'
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:text-foreground'
                  )}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                  </svg>
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={cn(
                    'px-3 py-1 rounded text-sm transition-colors',
                    viewMode === 'list'
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:text-foreground'
                  )}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Filters and Sort */}
            <div className="flex flex-col sm:flex-row sm:items-center gap-4">
              <div className="flex items-center gap-4">
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value as 'all' | 'processed' | 'processing' | 'error')}
                  className="px-3 py-2 border border-border rounded-lg bg-background text-foreground"
                >
                  <option value="all">Todos los estados</option>
                  <option value="processed">Procesadas</option>
                  <option value="processing">Procesando</option>
                  <option value="error">Con errores</option>
                </select>

                <select
                  value={`${sortBy}-${sortOrder}`}
                  onChange={(e) => {
                    const [sort, order] = e.target.value.split('-');
                    setSortBy(sort as 'date' | 'name' | 'confidence');
                    setSortOrder(order as 'asc' | 'desc');
                  }}
                  className="px-3 py-2 border border-border rounded-lg bg-background text-foreground"
                >
                  <option value="date-desc">Más recientes</option>
                  <option value="date-asc">Más antiguos</option>
                  <option value="name-asc">Nombre A-Z</option>
                  <option value="name-desc">Nombre Z-A</option>
                  <option value="confidence-desc">Mayor confianza</option>
                  <option value="confidence-asc">Menor confianza</option>
                </select>
              </div>

              {/* Bulk Actions */}
              {selectedCredentials.length > 0 && (
                <div className="flex items-center gap-2 ml-auto">
                  <span className="text-sm text-muted-foreground">
                    {selectedCredentials.length} seleccionadas
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowExportModal(true)}
                  >
                    Exportar
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => setShowDeleteModal(true)}
                  >
                    Eliminar
                  </Button>
                </div>
              )}
            </div>
          </div>
        </Card>

        {/* Credentials List */}
        <div className="space-y-4">
          {loading && credentials.length === 0 ? (
            <div className="flex justify-center py-12">
              <Loading size="lg" text="Cargando credenciales..." />
            </div>
          ) : error ? (
            <Card>
              <div className="text-center py-12">
                <div className="text-destructive mb-2">
                  <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-foreground mb-2">Error al cargar credenciales</h3>
                <p className="text-muted-foreground mb-4">{error}</p>
                <Button onClick={() => fetchCredentials()}>Reintentar</Button>
              </div>
            </Card>
          ) : filteredAndSortedCredentials.length === 0 ? (
            <Card>
              <div className="text-center py-12">
                <div className="text-muted-foreground mb-2">
                  <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-foreground mb-2">
                  {searchQuery ? 'No se encontraron credenciales' : 'No hay credenciales'}
                </h3>
                <p className="text-muted-foreground mb-4">
                  {searchQuery 
                    ? 'Intenta con otros términos de búsqueda'
                    : 'Sube archivos de credenciales INE para comenzar'
                  }
                </p>
                {!searchQuery && (
                  <Button onClick={() => setShowUploadModal(true)}>
                    Subir archivos
                  </Button>
                )}
              </div>
            </Card>
          ) : (
            <>
              {/* Select All */}
              <div className="flex items-center gap-2">
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedCredentials.length === filteredAndSortedCredentials.length}
                    onChange={handleSelectAll}
                    className="w-4 h-4 text-primary border-border rounded focus:outline-none"
                  />
                  <span className="text-sm text-foreground">Seleccionar todas</span>
                </label>
              </div>

              {/* Credentials Grid/List */}
              <div className={cn(
                viewMode === 'grid'
                  ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'
                  : 'space-y-4'
              )}>
                {filteredAndSortedCredentials.map((credential) => (
                  <div key={credential.id} className="relative">
                    <input
                      type="checkbox"
                      checked={selectedCredentials.includes(credential.id)}
                      onChange={() => handleSelectCredential(credential.id)}
                      className="absolute top-4 left-4 w-4 h-4 text-primary border-border rounded focus:outline-none z-10"
                    />
                    <CredentialCard
                      credential={credential}
                    />
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">
                      Página {currentPage} de {totalPages}
                    </span>
                    <select
                      value={pageSize}
                      onChange={(e) => setPageSize(Number(e.target.value))}
                      className="px-2 py-1 border border-border rounded text-sm bg-background"
                    >
                      <option value={12}>12 por página</option>
                      <option value={24}>24 por página</option>
                      <option value={48}>48 por página</option>
                    </select>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={goToPreviousPage}
                      disabled={currentPage === 1}
                    >
                      Anterior
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={goToNextPage}
                      disabled={currentPage === totalPages}
                    >
                      Siguiente
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Upload Modal */}
      <Modal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        title="Subir credenciales INE"
        size="lg"
      >
        <FileUpload
          onUploadComplete={() => {
            setShowUploadModal(false);
            fetchCredentials();
          }}
        />
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        title="Confirmar eliminación"
      >
        <div className="space-y-4">
          <p className="text-foreground">
            ¿Estás seguro de que deseas eliminar {selectedCredentials.length} credencial(es)?
            Esta acción no se puede deshacer.
          </p>
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={() => setShowDeleteModal(false)}
            >
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={handleBulkDelete}
            >
              Eliminar
            </Button>
          </div>
        </div>
      </Modal>

      {/* Export Modal */}
      <Modal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        title="Exportar credenciales"
      >
        <div className="space-y-4">
          <p className="text-foreground">
            Selecciona el formato para exportar {selectedCredentials.length || filteredAndSortedCredentials.length} credencial(es):
          </p>
          <div className="grid grid-cols-1 gap-2">
            <Button
              variant="outline"
              onClick={() => handleBulkExport('json')}
              leftIcon={
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              }
            >
              JSON (Datos estructurados)
            </Button>
            <Button
              variant="outline"
              onClick={() => handleBulkExport('csv')}
              leftIcon={
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              }
            >
              CSV (Hoja de cálculo)
            </Button>

          </div>
        </div>
      </Modal>
    </MainLayout>
  );
};

export default Credentials;