import React, { useState, useRef, useEffect } from 'react';
import { cn } from '../../utils/helpers';
import type { DropdownProps, DropdownItem } from '../../types/ui';

const Dropdown: React.FC<DropdownProps> = ({
  trigger,
  items,
  placement = 'bottom-start',
  className,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen]);

  const placementClasses = {
    'top-start': 'bottom-full left-0 mb-1',
    'top-end': 'bottom-full right-0 mb-1',
    'bottom-start': 'top-full left-0 mt-1',
    'bottom-end': 'top-full right-0 mt-1',
    'left-start': 'right-full top-0 mr-1',
    'left-end': 'right-full bottom-0 mr-1',
    'right-start': 'left-full top-0 ml-1',
    'right-end': 'left-full bottom-0 ml-1',
  };

  const handleItemClick = (item: DropdownItem) => {
    if (item.onClick) {
      item.onClick();
    }
    if (!item.keepOpen) {
      setIsOpen(false);
    }
  };

  return (
    <div className={cn('relative inline-block', className)} ref={dropdownRef}>
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="cursor-pointer"
      >
        {trigger}
      </div>
      
      {isOpen && (
        <div className={cn(
          'absolute z-50 min-w-48 py-1',
          'bg-white dark:bg-gray-800',
          'border border-gray-200 dark:border-gray-700',
          'rounded-md shadow-lg',
          'animate-fade-in',
          placementClasses[placement]
        )}>
          {items.map((item, index) => {
            if (item.type === 'divider') {
              return (
                <hr
                  key={index}
                  className="my-1 border-gray-200 dark:border-gray-700"
                />
              );
            }

            return (
              <button
                key={index}
                onClick={() => handleItemClick(item)}
                disabled={item.disabled}
                className={cn(
                  'w-full px-4 py-2 text-left text-sm transition-colors',
                  'hover:bg-gray-100 dark:hover:bg-gray-700',
                  'focus:bg-gray-100 dark:focus:bg-gray-700',
                  'focus:outline-none',
                  item.disabled
                    ? 'text-gray-400 dark:text-gray-600 cursor-not-allowed'
                    : 'text-gray-700 dark:text-gray-300',
                  item.className
                )}
              >
                <div className="flex items-center gap-2">
                  {item.icon && (
                    <span className="flex-shrink-0">
                      {item.icon}
                    </span>
                  )}
                  <span className="flex-1">{item.label}</span>
                  {item.shortcut && (
                    <span className="text-xs text-gray-400 dark:text-gray-500">
                      {item.shortcut}
                    </span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default Dropdown;