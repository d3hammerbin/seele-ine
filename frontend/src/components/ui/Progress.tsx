import React from 'react';
import { cn } from '../../utils/helpers';
import type { ProgressProps } from '../../types/ui';

const Progress: React.FC<ProgressProps> = ({
  value,
  max = 100,
  size = 'md',
  color,
  showLabel = false,
  className,
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  const sizeClasses = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3',
  };

  const colorClasses = {
    primary: 'bg-primary-600',
    success: 'bg-green-500',
    warning: 'bg-yellow-500',
    error: 'bg-red-500',
  };

  const defaultColorClass = color && colorClasses[color as keyof typeof colorClasses] 
    ? colorClasses[color as keyof typeof colorClasses]
    : 'bg-primary-600';

  return (
    <div className={cn('w-full', className)}>
      {showLabel && (
        <div className="flex justify-between items-center mb-1">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Progress
          </span>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {Math.round(percentage)}%
          </span>
        </div>
      )}
      <div className={cn(
        'w-full bg-gray-200 rounded-full overflow-hidden dark:bg-gray-700',
        sizeClasses[size]
      )}>
        <div
          className={cn(
            'h-full transition-all duration-300 ease-out rounded-full',
            color ? '' : defaultColorClass
          )}
          style={{
            width: `${percentage}%`,
            backgroundColor: color && !colorClasses[color as keyof typeof colorClasses] ? color : undefined,
          }}
        />
      </div>
    </div>
  );
};

export default Progress;