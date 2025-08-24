import React, { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { cn } from '../../utils/helpers';
import Button from './Button';

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  closeOnOverlayClick?: boolean;
  closeOnEscape?: boolean;
  showCloseButton?: boolean;
  className?: string;
  overlayClassName?: string;
  contentClassName?: string;
}

const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  description,
  children,
  size = 'md',
  closeOnOverlayClick = true,
  closeOnEscape = true,
  showCloseButton = true,
  className,
  overlayClassName,
  contentClassName,
}) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const previousActiveElement = useRef<HTMLElement | null>(null);

  // Handle escape key
  useEffect(() => {
    if (!closeOnEscape) return;

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, closeOnEscape, onClose]);

  // Handle focus management
  useEffect(() => {
    if (isOpen) {
      previousActiveElement.current = document.activeElement as HTMLElement;
      modalRef.current?.focus();
    } else {
      previousActiveElement.current?.focus();
    }
  }, [isOpen]);

  // Handle body scroll lock
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  const handleOverlayClick = (event: React.MouseEvent) => {
    if (closeOnOverlayClick && event.target === event.currentTarget) {
      onClose();
    }
  };

  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    full: 'max-w-[95vw] max-h-[95vh]',
  };

  const overlayClasses = cn(
    'fixed inset-0 z-50 flex items-center justify-center p-4',
    'bg-black/50 backdrop-blur-sm',
    'animate-in fade-in-0 duration-300',
    overlayClassName
  );

  const contentClasses = cn(
    'relative w-full rounded-lg border bg-background p-6 shadow-lg',
    'animate-in fade-in-0 zoom-in-95 duration-300',
    sizeClasses[size],
    size === 'full' && 'h-full overflow-auto',
    contentClassName
  );

  const modalClasses = cn(
    'flex flex-col',
    size === 'full' && 'h-full',
    className
  );

  if (!isOpen) return null;

  return createPortal(
    <div
      className={overlayClasses}
      onClick={handleOverlayClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? 'modal-title' : undefined}
      aria-describedby={description ? 'modal-description' : undefined}
    >
      <div className={contentClasses}>
        <div
          ref={modalRef}
          className={modalClasses}
          tabIndex={-1}
        >
          {/* Header */}
          {(title || showCloseButton) && (
            <div className="flex items-center justify-between pb-4">
              <div className="space-y-1">
                {title && (
                  <h2 id="modal-title" className="text-lg font-semibold">
                    {title}
                  </h2>
                )}
                {description && (
                  <p id="modal-description" className="text-sm text-muted-foreground">
                    {description}
                  </p>
                )}
              </div>
              {showCloseButton && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onClose}
                  className="h-8 w-8 p-0"
                  aria-label="Close modal"
                >
                  <svg
                    className="h-4 w-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </Button>
              )}
            </div>
          )}

          {/* Content */}
          <div className={cn(
            'flex-1',
            size === 'full' && 'overflow-auto'
          )}>
            {children}
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
};

// Modal Footer Component
export interface ModalFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  justify?: 'start' | 'center' | 'end' | 'between';
}

const ModalFooter: React.FC<ModalFooterProps> = ({
  className,
  justify = 'end',
  ...props
}) => {
  const justifyClasses = {
    start: 'justify-start',
    center: 'justify-center',
    end: 'justify-end',
    between: 'justify-between',
  };

  const classes = cn(
    'flex items-center space-x-2 pt-4 mt-4 border-t',
    justifyClasses[justify],
    className
  );

  return <div className={classes} {...props} />;
};

export { Modal, ModalFooter };
export default Modal;