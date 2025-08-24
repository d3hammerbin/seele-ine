import React from 'react';
import { cn } from '../../utils/helpers';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'outline' | 'filled' | 'destructive';
  padding?: 'none' | 'sm' | 'md' | 'lg';
  shadow?: 'none' | 'sm' | 'md' | 'lg';
  hover?: boolean;
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({
    className,
    variant = 'default',
    padding = 'md',
    shadow = 'sm',
    hover = false,
    ...props
  }, ref) => {
    const baseClasses = [
      'rounded-lg border bg-card text-card-foreground transition-all duration-200',
    ];

    const variantClasses = {
      default: 'border-border',
      outline: 'border-2 border-border',
      filled: 'border-border bg-muted/50',
      destructive: 'border-destructive bg-destructive/10',
    };

    const paddingClasses = {
      none: '',
      sm: 'p-3',
      md: 'p-6',
      lg: 'p-8',
    };

    const shadowClasses = {
      none: '',
      sm: 'shadow-sm',
      md: 'shadow-md',
      lg: 'shadow-lg',
    };

    const classes = cn(
      baseClasses,
      variantClasses[variant],
      paddingClasses[padding],
      shadowClasses[shadow],
      hover && 'hover:shadow-md hover:scale-[1.02] cursor-pointer',
      className
    );

    return (
      <div className={classes} ref={ref} {...props} />
    );
  }
);

Card.displayName = 'Card';

// Card Header Component
export interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
}

const CardHeader = React.forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ className, title, subtitle, action, children, ...props }, ref) => {
    const classes = cn(
      'flex flex-col space-y-1.5 p-6 pb-4',
      className
    );

    return (
      <div className={classes} ref={ref} {...props}>
        {(title || subtitle || action) && (
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              {title && (
                <h3 className="text-2xl font-semibold leading-none tracking-tight">
                  {title}
                </h3>
              )}
              {subtitle && (
                <p className="text-sm text-muted-foreground">
                  {subtitle}
                </p>
              )}
            </div>
            {action && (
              <div className="flex items-center space-x-2">
                {action}
              </div>
            )}
          </div>
        )}
        {children}
      </div>
    );
  }
);

CardHeader.displayName = 'CardHeader';

// Card Content Component
export type CardContentProps = React.HTMLAttributes<HTMLDivElement>;

const CardContent = React.forwardRef<HTMLDivElement, CardContentProps>(
  ({ className, ...props }, ref) => {
    const classes = cn('p-6 pt-0', className);

    return (
      <div className={classes} ref={ref} {...props} />
    );
  }
);

CardContent.displayName = 'CardContent';

// Card Footer Component
export interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  justify?: 'start' | 'center' | 'end' | 'between';
}

const CardFooter = React.forwardRef<HTMLDivElement, CardFooterProps>(
  ({ className, justify = 'end', ...props }, ref) => {
    const justifyClasses = {
      start: 'justify-start',
      center: 'justify-center',
      end: 'justify-end',
      between: 'justify-between',
    };

    const classes = cn(
      'flex items-center p-6 pt-0',
      justifyClasses[justify],
      className
    );

    return (
      <div className={classes} ref={ref} {...props} />
    );
  }
);

CardFooter.displayName = 'CardFooter';

export { Card, CardHeader, CardContent, CardFooter };
export default Card;