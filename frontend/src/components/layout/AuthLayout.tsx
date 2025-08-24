import React from 'react';
import { cn } from '../../utils/helpers';
import { Card, CardContent } from '../ui';
import useTheme from '../../hooks/useTheme';

export interface AuthLayoutProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  showLogo?: boolean;
  className?: string;
}

const AuthLayout: React.FC<AuthLayoutProps> = ({
  children,
  title,
  subtitle,
  showLogo = true,
  className,
}) => {
  const { toggleTheme, mode } = useTheme();

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary/5 via-background to-secondary/5 flex items-center justify-center p-4">
      {/* Theme toggle */}
      <div className="absolute top-4 right-4">
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg bg-card border border-border hover:bg-accent transition-colors"
          aria-label="Toggle theme"
        >
          {mode === 'dark' ? (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          )}
        </button>
      </div>

      <div className="w-full max-w-md">
        <Card className={cn('shadow-xl', className)}>
          <CardContent className="p-8">
            {/* Logo and branding */}
            {showLogo && (
              <div className="text-center mb-8">
                <div className="inline-flex items-center justify-center w-16 h-16 mb-4">
                  <img 
                    src="/src/assets/logo.svg" 
                    alt="Seele INE Logo" 
                    className="w-12 h-12"
                  />
                </div>
                <h1 className="text-2xl font-bold text-foreground mb-2">
                  Seele INE
                </h1>
                <p className="text-sm text-muted-foreground">
                  Procesamiento inteligente de credenciales INE
                </p>
              </div>
            )}

            {/* Page title and subtitle */}
            {(title || subtitle) && (
              <div className="text-center mb-6">
                {title && (
                  <h2 className="text-xl font-semibold text-foreground mb-2">
                    {title}
                  </h2>
                )}
                {subtitle && (
                  <p className="text-sm text-muted-foreground">
                    {subtitle}
                  </p>
                )}
              </div>
            )}

            {/* Content */}
            {children}
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center mt-6">
          <p className="text-xs text-muted-foreground">
            © 2024 Seele INE. Todos los derechos reservados.
          </p>
        </div>
      </div>

      {/* Background decoration */}
      <div className="absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute -top-40 -right-32 w-80 h-80 bg-primary/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-32 w-80 h-80 bg-secondary/10 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-accent/5 rounded-full blur-3xl" />
      </div>
    </div>
  );
};

export default AuthLayout;