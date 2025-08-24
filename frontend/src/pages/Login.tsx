import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AuthLayout } from '../components/layout';
import { Button, Input } from '../components/ui';
import { useAuthContext } from '../hooks/useAuthContext';
import useForm from '../hooks/useForm';


interface LoginFormData extends Record<string, unknown> {
  email: string;
  password: string;
  rememberMe: boolean;
}

const Login: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isLoading, error, isAuthenticated } = useAuthContext();
  const [showPassword, setShowPassword] = useState(false);



  const {
    values,
    errors,
    touched,
    handleChange,
    handleBlur,
    handleSubmit,
    isValid,
  } = useForm<LoginFormData>({
    initialValues: {
      email: '',
      password: '',
      rememberMe: false,
    },
    validationRules: {
      email: [
        {
          type: 'required',
          validator: (value: unknown) => !!(value as string) && (value as string).trim().length > 0,
          message: 'El email es requerido'
        },
        {
          type: 'email',
          validator: (value: unknown) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value as string),
          message: 'El email no es válido'
        }
      ],
      password: [
        {
          type: 'required',
          validator: (value: unknown) => !!(value as string) && (value as string).trim().length > 0,
          message: 'La contraseña es requerida'
        },
        {
          type: 'minLength',
          validator: (value: unknown) => !!(value as string) && (value as string).length >= 6,
          message: 'La contraseña debe tener al menos 6 caracteres'
        }
      ],
    },
    onSubmit: async (formData: LoginFormData) => {
      // Clear any existing corrupted tokens before login
      console.log('=== CLEARING EXISTING TOKENS ===');
      localStorage.removeItem('seele_access_token');
      localStorage.removeItem('seele_refresh_token');
      localStorage.removeItem('seele_token_expiration');
      localStorage.removeItem('seele_current_user');
      console.log('Tokens cleared');

      try {
        await login(formData.email, formData.password);
        
        // Debug tokens after login
        console.log('=== TOKEN DEBUG AFTER LOGIN ===');
        const newRefreshToken = localStorage.getItem('seele_refresh_token');
        const newAccessToken = localStorage.getItem('seele_access_token');
        
        console.log('New Access Token exists:', !!newAccessToken);
        console.log('New Refresh Token exists:', !!newRefreshToken);
        
        if (newAccessToken) {
          console.log('Access Token segments:', newAccessToken.split('.').length);
          console.log('Access Token preview:', newAccessToken.substring(0, 50) + '...');
        }
        
        if (newRefreshToken) {
          console.log('Refresh Token segments:', newRefreshToken.split('.').length);
          console.log('Refresh Token preview:', newRefreshToken.substring(0, 50) + '...');
          
          // Check if it's a valid JWT format
          const segments = newRefreshToken.split('.');
          if (segments.length !== 3) {
            console.error('❌ INVALID REFRESH TOKEN: Not enough segments!');
            console.log('Expected 3 segments, got:', segments.length);
            console.log('Full token:', newRefreshToken);
          } else {
            console.log('✅ Refresh token has correct JWT format');
            try {
              const payload = JSON.parse(atob(segments[1]));
              console.log('Token payload:', payload);
              console.log('Token expiration:', new Date(payload.exp * 1000));
            } catch (e) {
              console.error('Error parsing token payload:', e);
            }
          }
        }
        
        // Force navigation after successful login
        const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/dashboard';
        navigate(from, { replace: true });
      } catch (error) {
        // Error is handled by the useAuth hook
        console.error('Login failed:', error);
      }
    },
  });

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location]);

  const handleForgotPassword = () => {
    navigate('/forgot-password');
  };

  const handleSignUp = () => {
    navigate('/register');
  };

  return (
    <AuthLayout
      title="Iniciar sesión"
      subtitle="Accede a tu cuenta para procesar credenciales INE"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Global Error */}
        {error && (
          <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
            <p className="text-sm text-destructive">{error}</p>
          </div>
        )}

        {/* Email Field */}
        <Input
          label="Correo electrónico"
          type="email"
          name="email"
          value={values.email}
          onChange={handleChange('email')}
          onBlur={handleBlur('email')}
          error={touched.email ? errors.email : undefined}
          placeholder="tu@email.com"
          leftIcon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
            </svg>
          }
          required
          disabled={isLoading}
        />

        {/* Password Field */}
        <Input
          label="Contraseña"
          type={showPassword ? 'text' : 'password'}
          name="password"
          value={values.password}
          onChange={handleChange('password')}
          onBlur={handleBlur('password')}
          error={touched.password ? errors.password : undefined}
          placeholder="Tu contraseña"
          leftIcon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          }
          rightIcon={
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              {showPassword ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              )}
            </button>
          }
          required
          disabled={isLoading}
        />

        {/* Remember Me & Forgot Password */}
        <div className="flex items-center justify-between">
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              name="rememberMe"
              checked={values.rememberMe}
              onChange={handleChange('rememberMe')}
              disabled={isLoading}
              className="w-4 h-4 text-primary border-border rounded focus:outline-none"
            />
            <span className="text-sm text-foreground">Recordarme</span>
          </label>
          <button
            type="button"
            onClick={handleForgotPassword}
            disabled={isLoading}
            className="text-sm text-primary hover:text-primary/80 transition-colors"
          >
            ¿Olvidaste tu contraseña?
          </button>
        </div>

        {/* Submit Button */}
        <Button
          type="submit"
          fullWidth
          loading={isLoading}
          disabled={!isValid || isLoading}
        >
            {isLoading ? 'Iniciando sesión...' : 'Iniciar sesión'}
        </Button>

        {/* Divider */}
        <div className="relative my-6">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-border" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-card text-muted-foreground">o</span>
          </div>
        </div>

        {/* Sign Up Link */}
        <div className="text-center">
          <p className="text-sm text-muted-foreground">
            ¿No tienes una cuenta?{' '}
            <button
              type="button"
              onClick={handleSignUp}
              disabled={isLoading}
              className="text-primary hover:text-primary/80 font-medium transition-colors"
            >
              Regístrate aquí
            </button>
          </p>
        </div>
      </form>

      {/* Demo Credentials */}
      <div className="mt-6 p-4 bg-secondary/30 rounded-lg">
        <h4 className="text-sm font-medium text-foreground mb-2">
          Credenciales de demostración:
        </h4>
        <div className="text-xs text-muted-foreground space-y-1">
          <p><strong>Email:</strong> test@example.com</p>
          <p><strong>Contraseña:</strong> testpassword123</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="mt-2 w-full"
          onClick={() => {
            handleChange('email')({ target: { name: 'email', value: 'test@example.com' } } as React.ChangeEvent<HTMLInputElement>);
            handleChange('password')({ target: { name: 'password', value: 'testpassword123' } } as React.ChangeEvent<HTMLInputElement>);
          }}
          disabled={isLoading}
        >
          Usar credenciales de demo
        </Button>
      </div>
    </AuthLayout>
  );
};

export default Login;