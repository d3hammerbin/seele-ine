import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthContext } from '../hooks/useAuthContext';
import { Loading } from './ui';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredPermissions?: string[];
  fallbackPath?: string;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredPermissions = [],
  fallbackPath = '/login',
}) => {
  const { isAuthenticated, loading, user } = useAuthContext();
  const location = useLocation();

  // Show loading spinner while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loading size="lg" text="Verificando autenticación..." />
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return (
      <Navigate 
        to={fallbackPath} 
        state={{ from: location }} 
        replace 
      />
    );
  }

  // Check permissions if required
  if (requiredPermissions.length > 0 && user) {
    const hasRequiredPermissions = requiredPermissions.every(permission => {
      // Simple permission check - in a real app, this would be more sophisticated
      return user.permissions?.includes(permission) || user.role === 'admin';
    });

    if (!hasRequiredPermissions) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-background">
          <div className="text-center space-y-4">
            <div className="text-destructive">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-foreground">Acceso denegado</h2>
            <p className="text-muted-foreground max-w-md">
              No tienes los permisos necesarios para acceder a esta página.
            </p>
            <button
              onClick={() => window.history.back()}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
            >
              Volver atrás
            </button>
          </div>
        </div>
      );
    }
  }

  // Render the protected content
  return <>{children}</>;
};

export default ProtectedRoute;