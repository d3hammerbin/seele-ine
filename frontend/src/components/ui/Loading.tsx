import React from 'react';
import { cn } from '../../utils/helpers';

export interface LoadingProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'spinner' | 'dots' | 'pulse' | 'skeleton';
  text?: string;
  fullScreen?: boolean;
  overlay?: boolean;
  className?: string;
}

const Loading: React.FC<LoadingProps> = ({
  size = 'md',
  variant = 'spinner',
  text,
  fullScreen = false,
  overlay = false,
  className,
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
    xl: 'w-12 h-12',
  };

  const textSizeClasses = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
    xl: 'text-xl',
  };

  const renderSpinner = () => (
    <svg
      className={cn(
        'animate-spin text-primary',
        sizeClasses[size]
      )}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );

  const renderDots = () => (
    <div className="flex space-x-1">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className={cn(
            'bg-primary rounded-full animate-pulse',
            size === 'sm' && 'w-1 h-1',
            size === 'md' && 'w-2 h-2',
            size === 'lg' && 'w-3 h-3',
            size === 'xl' && 'w-4 h-4'
          )}
          style={{
            animationDelay: `${i * 0.2}s`,
            animationDuration: '1.4s',
          }}
        />
      ))}
    </div>
  );

  const renderPulse = () => (
    <div
      className={cn(
        'bg-primary rounded-full animate-pulse',
        sizeClasses[size]
      )}
    />
  );

  const renderSkeleton = () => (
    <div className="space-y-2">
      <div className="h-4 bg-muted rounded animate-pulse" />
      <div className="h-4 bg-muted rounded animate-pulse w-3/4" />
      <div className="h-4 bg-muted rounded animate-pulse w-1/2" />
    </div>
  );

  const renderLoader = () => {
    switch (variant) {
      case 'dots':
        return renderDots();
      case 'pulse':
        return renderPulse();
      case 'skeleton':
        return renderSkeleton();
      default:
        return renderSpinner();
    }
  };

  const containerClasses = cn(
    'flex flex-col items-center justify-center space-y-2',
    fullScreen && 'fixed inset-0 z-50 bg-background',
    overlay && 'absolute inset-0 z-10 bg-background/80 backdrop-blur-sm',
    className
  );

  return (
    <div className={containerClasses}>
      {renderLoader()}
      {text && (
        <p className={cn(
          'text-muted-foreground font-medium',
          textSizeClasses[size]
        )}>
          {text}
        </p>
      )}
    </div>
  );
};

// Skeleton component for content placeholders
export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  width?: string | number;
  height?: string | number;
  rounded?: boolean;
  animate?: boolean;
}

const Skeleton: React.FC<SkeletonProps> = ({
  className,
  width,
  height,
  rounded = false,
  animate = true,
  style,
  ...props
}) => {
  const classes = cn(
    'bg-muted',
    animate && 'animate-pulse',
    rounded ? 'rounded-full' : 'rounded',
    className
  );

  const skeletonStyle = {
    width,
    height,
    ...style,
  };

  return (
    <div
      className={classes}
      style={skeletonStyle}
      {...props}
    />
  );
};

// Loading overlay component
export interface LoadingOverlayProps {
  isLoading: boolean;
  children: React.ReactNode;
  loadingProps?: Omit<LoadingProps, 'overlay'>;
}

const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  isLoading,
  children,
  loadingProps = {},
}) => {
  return (
    <div className="relative">
      {children}
      {isLoading && (
        <Loading
          {...loadingProps}
          overlay
        />
      )}
    </div>
  );
};

export { Loading, Skeleton, LoadingOverlay };
export default Loading;