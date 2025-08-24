import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AuthLayout } from '../components/layout';
import { Button, Input } from '../components/ui';
import { useAuthContext } from '../hooks/useAuthContext';
import useForm from '../hooks/useForm';

interface RegisterFormData extends Record<string, unknown> {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  confirmPassword: string;
  acceptTerms: boolean;
  acceptPrivacy: boolean;
}

const Register: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { register, isLoading, error, isAuthenticated } = useAuthContext();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const {
    values,
    errors,
    touched,
    handleChange,
    handleBlur,
    handleSubmit,
    isValid,
  } = useForm<RegisterFormData>({
    initialValues: {
      firstName: '',
      lastName: '',
      email: '',
      password: '',
      confirmPassword: '',
      acceptTerms: false,
      acceptPrivacy: false,
    },
    validationRules: {
      firstName: [
        {
          type: 'required',
          validator: (value: unknown) => !!(value as string) && (value as string).trim().length > 0,
          message: 'El nombre es requerido'
        },
        {
          type: 'minLength',
          validator: (value: unknown) => !(value as string) || (value as string).length >= 2,
          message: 'El nombre debe tener al menos 2 caracteres'
        }
      ],
      lastName: [
        {
          type: 'required',
          validator: (value: unknown) => !!(value as string) && (value as string).trim().length > 0,
          message: 'El apellido es requerido'
        },
        {
          type: 'minLength',
          validator: (value: unknown) => !(value as string) || (value as string).length >= 2,
          message: 'El apellido debe tener al menos 2 caracteres'
        }
      ],
      email: [
        {
          type: 'required',
          validator: (value: unknown) => !!(value as string) && (value as string).trim().length > 0,
          message: 'El email es requerido'
        },
        {
          type: 'email',
          validator: (value: unknown) => !(value as string) || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value as string),
          message: 'Ingresa un email válido'
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
          validator: (value: unknown) => !(value as string) || (value as string).length >= 8,
          message: 'La contraseña debe tener al menos 8 caracteres'
        },
        {
          type: 'pattern',
          validator: (value: unknown) => !(value as string) || /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/.test(value as string),
          message: 'La contraseña debe contener al menos una mayúscula, una minúscula, un número y un carácter especial'
        }
      ],
      confirmPassword: [
        {
          type: 'required',
          validator: (value: unknown) => !!(value as string) && (value as string).trim().length > 0,
          message: 'La confirmación de contraseña es requerida'
        },
        {
          type: 'confirmation',
          validator: (value: unknown, formValues: unknown) => (value as string) === (formValues as RegisterFormData)?.password,
          message: 'Las contraseñas no coinciden'
        },
      ],
      acceptTerms: [
        {
          type: 'required',
          validator: (value: unknown) => !!(value as boolean),
          message: 'Debes aceptar los términos y condiciones'
        },
      ],
      acceptPrivacy: [
        {
          type: 'required',
          validator: (value: unknown) => !!(value as boolean),
          message: 'Debes aceptar la política de privacidad'
        },
      ],
    },
    onSubmit: async (formData) => {
      try {
        await register({
          firstName: formData.firstName,
          lastName: formData.lastName,
          email: formData.email,
          password: formData.password,
          confirmPassword: formData.confirmPassword,
          acceptTerms: formData.acceptTerms,
        });
      } catch (error) {
        // Error is handled by the useAuth hook
        console.error('Registration failed:', error);
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

  const handleLogin = () => {
    navigate('/login');
  };

  return (
    <AuthLayout
      title="Crear cuenta"
      subtitle="Regístrate para comenzar a procesar credenciales INE"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Global Error */}
        {error && (
          <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
            <p className="text-sm text-destructive">{error}</p>
          </div>
        )}

        {/* Name Fields */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Nombre"
            type="text"
            name="firstName"
            value={values.firstName}
            onChange={handleChange('firstName')}
            onBlur={handleBlur('firstName')}
            error={touched.firstName ? errors.firstName : undefined}
            placeholder="Tu nombre"
            leftIcon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            }
            required
            disabled={isLoading}
          />
          <Input
            label="Apellido"
            type="text"
            name="lastName"
            value={values.lastName}
            onChange={handleChange('lastName')}
            onBlur={handleBlur('lastName')}
            error={touched.lastName ? errors.lastName : undefined}
            placeholder="Tu apellido"
            leftIcon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            }
            required
            disabled={isLoading}
          />
        </div>

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

        {/* Password Fields */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
          <Input
            label="Confirmar contraseña"
            type={showConfirmPassword ? 'text' : 'password'}
            name="confirmPassword"
            value={values.confirmPassword}
            onChange={handleChange('confirmPassword')}
            onBlur={handleBlur('confirmPassword')}
            error={touched.confirmPassword ? errors.confirmPassword : undefined}
            placeholder="Confirma tu contraseña"
            leftIcon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            }
            rightIcon={
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                {showConfirmPassword ? (
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
        </div>

        {/* Password Requirements */}
        <div className="text-xs text-muted-foreground space-y-1">
          <p>La contraseña debe contener:</p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Al menos 8 caracteres</li>
            <li>Una letra mayúscula</li>
            <li>Una letra minúscula</li>
            <li>Un número</li>
            <li>Un carácter especial (@$!%*?&)</li>
          </ul>
        </div>

        {/* Terms and Privacy */}
        <div className="space-y-3">
          <label className="flex items-start space-x-3 cursor-pointer">
            <input
              type="checkbox"
              name="acceptTerms"
              checked={values.acceptTerms}
              onChange={handleChange('acceptTerms')}
              disabled={isLoading}
              className="w-4 h-4 text-primary border-border rounded focus:outline-none mt-0.5"
            />
            <span className="text-sm text-foreground">
              Acepto los{' '}
              <a
                href="/terms"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:text-primary/80 underline"
              >
                términos y condiciones
              </a>
            </span>
          </label>
          {touched.acceptTerms && errors.acceptTerms && (
            <p className="text-sm text-destructive ml-7">{errors.acceptTerms}</p>
          )}

          <label className="flex items-start space-x-3 cursor-pointer">
            <input
              type="checkbox"
              name="acceptPrivacy"
              checked={values.acceptPrivacy}
              onChange={handleChange('acceptPrivacy')}
              disabled={isLoading}
              className="w-4 h-4 text-primary border-border rounded focus:ring-primary-500 focus:ring-2 mt-0.5"
            />
            <span className="text-sm text-foreground">
              Acepto la{' '}
              <a
                href="/privacy"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:text-primary/80 underline"
              >
                política de privacidad
              </a>
            </span>
          </label>
          {touched.acceptPrivacy && errors.acceptPrivacy && (
            <p className="text-sm text-destructive ml-7">{errors.acceptPrivacy}</p>
          )}
        </div>

        {/* Submit Button */}
        <Button
          type="submit"
          fullWidth
          loading={isLoading}
          disabled={!isValid || isLoading}
        >
          {isLoading ? 'Creando cuenta...' : 'Crear cuenta'}
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

        {/* Login Link */}
        <div className="text-center">
          <p className="text-sm text-muted-foreground">
            ¿Ya tienes una cuenta?{' '}
            <button
              type="button"
              onClick={handleLogin}
              disabled={isLoading}
              className="text-primary hover:text-primary/80 font-medium transition-colors"
            >
              Inicia sesión aquí
            </button>
          </p>
        </div>
      </form>
    </AuthLayout>
  );
};

export default Register;