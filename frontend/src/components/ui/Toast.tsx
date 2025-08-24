import React, { useEffect, useState, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { cn } from '../../utils/helpers';
import Button from './Button';

export interface ToastProps {
  id: string;
  type?: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
  persistent?: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
  onClose: (id: string) => void;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';
}

const Toast: React.FC<ToastProps> = ({
  id,
  type = 'info',
  title,
  message,
  duration = 5000,
  persistent = false,
  action,
  onClose,
  position = 'top-right',
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isExiting, setIsExiting] = useState(false);

  const handleClose = useCallback(() => {
    setIsExiting(true);
    setTimeout(() => {
      onClose(id);
    }, 300); // Match animation duration
  }, [onClose, id]);

  useEffect(() => {
    // Show animation
    const showTimer = setTimeout(() => setIsVisible(true), 10);

    // Auto dismiss
    let dismissTimer: NodeJS.Timeout;
    if (!persistent && duration > 0) {
      dismissTimer = setTimeout(() => {
        handleClose();
      }, duration);
    }

    return () => {
      clearTimeout(showTimer);
      if (dismissTimer) clearTimeout(dismissTimer);
    };
  }, [duration, persistent, handleClose]);

  const typeStyles = {
    success: {
      icon: (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
        </svg>
      ),
      classes: 'bg-green-50 border-green-200 text-green-800',
      iconClasses: 'text-green-400',
    },
    error: {
      icon: (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
        </svg>
      ),
      classes: 'bg-red-50 border-red-200 text-red-800',
      iconClasses: 'text-red-400',
    },
    warning: {
      icon: (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
        </svg>
      ),
      classes: 'bg-yellow-50 border-yellow-200 text-yellow-800',
      iconClasses: 'text-yellow-400',
    },
    info: {
      icon: (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
        </svg>
      ),
      classes: 'bg-blue-50 border-blue-200 text-blue-800',
      iconClasses: 'text-blue-400',
    },
  };

  const positionClasses = {
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4',
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'top-center': 'top-4 left-1/2 transform -translate-x-1/2',
    'bottom-center': 'bottom-4 left-1/2 transform -translate-x-1/2',
  };

  const animationClasses = cn(
    'transition-all duration-300 ease-in-out',
    isVisible && !isExiting && 'translate-x-0 opacity-100',
    !isVisible && 'translate-x-full opacity-0',
    isExiting && 'translate-x-full opacity-0 scale-95'
  );

  const toastClasses = cn(
    'fixed z-50 max-w-sm w-full shadow-lg rounded-lg border p-4',
    'pointer-events-auto',
    typeStyles[type].classes,
    positionClasses[position],
    animationClasses
  );

  return (
    <div className={toastClasses}>
      <div className="flex items-start">
        <div className={cn('flex-shrink-0', typeStyles[type].iconClasses)}>
          {typeStyles[type].icon}
        </div>
        <div className="ml-3 w-0 flex-1">
          <p className="text-sm font-medium">{title}</p>
          {message && (
            <p className="mt-1 text-sm opacity-90">{message}</p>
          )}
          {action && (
            <div className="mt-3">
              <Button
                variant="outline"
                size="sm"
                onClick={action.onClick}
                className="text-xs"
              >
                {action.label}
              </Button>
            </div>
          )}
        </div>
        <div className="ml-4 flex-shrink-0 flex">
          <button
            className="inline-flex text-gray-400 hover:text-gray-600 focus:outline-none focus:text-gray-600 transition ease-in-out duration-150"
            onClick={handleClose}
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

// Toast Container Component
export interface ToastContainerProps {
  toasts: Array<Omit<ToastProps, 'onClose'>>;
  onClose: (id: string) => void;
  position?: ToastProps['position'];
  maxToasts?: number;
}

const ToastContainer: React.FC<ToastContainerProps> = ({
  toasts,
  onClose,
  position = 'top-right',
  maxToasts = 5,
}) => {
  const visibleToasts = toasts.slice(0, maxToasts);

  if (visibleToasts.length === 0) return null;

  return createPortal(
    <div className="fixed inset-0 pointer-events-none z-50">
      {visibleToasts.map((toast) => (
        <Toast
          key={toast.id}
          {...toast}
          position={position}
          onClose={onClose}
        />
      ))}
    </div>,
    document.body
  );
};

export { Toast, ToastContainer };
export default Toast;