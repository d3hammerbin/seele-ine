import React from 'react';
import { cn } from '../../utils/helpers';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({
    className,
    type = 'text',
    label,
    error,
    helperText,
    leftIcon,
    rightIcon,
    fullWidth = false,
    id,
    ...props
  }, ref) => {
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

    const inputClasses = cn(
      'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm',
      'ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium',
      'placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2',
      'focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
      leftIcon && 'pl-10',
      rightIcon && 'pr-10',
      error && 'border-destructive focus-visible:ring-destructive',
      className
    );

    const containerClasses = cn(
      'space-y-2',
      fullWidth && 'w-full'
    );

    return (
      <div className={containerClasses}>
        {label && (
          <label
            htmlFor={inputId}
            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
          >
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <div className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground">
              {leftIcon}
            </div>
          )}
          <input
            type={type}
            className={inputClasses}
            ref={ref}
            id={inputId}
            {...props}
          />
          {rightIcon && (
            <div className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground">
              {rightIcon}
            </div>
          )}
        </div>
        {error && (
          <p className="text-sm text-destructive">{error}</p>
        )}
        {helperText && !error && (
          <p className="text-sm text-muted-foreground">{helperText}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;