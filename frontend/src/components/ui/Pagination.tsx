import React from 'react';
import { cn } from '../../utils/helpers';
import type { PaginationProps } from '../../types/ui';

const Pagination: React.FC<PaginationProps> = ({
  current,
  total,
  pageSize,
  onChange,
  // showSizeChanger = false,
  // showQuickJumper = false,
  // showTotal,
  className,
}) => {
  const totalPages = Math.ceil(total / pageSize);
  const maxVisiblePages = 5;
  
  const getVisiblePages = () => {
    const pages: (number | string)[] = [];
    
    if (totalPages <= maxVisiblePages) {
      // Show all pages if total is less than max visible
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      const halfVisible = Math.floor(maxVisiblePages / 2);
      let startPage = Math.max(1, current - halfVisible);
      let endPage = Math.min(totalPages, current + halfVisible);
      
      // Adjust if we're near the beginning or end
      if (current <= halfVisible) {
        endPage = maxVisiblePages;
      } else if (current > totalPages - halfVisible) {
        startPage = totalPages - maxVisiblePages + 1;
      }
      
      // Add first page and ellipsis if needed
      if (startPage > 1) {
        pages.push(1);
        if (startPage > 2) {
          pages.push('...');
        }
      }
      
      // Add visible pages
      for (let i = startPage; i <= endPage; i++) {
        pages.push(i);
      }
      
      // Add ellipsis and last page if needed
      if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
          pages.push('...');
        }
        pages.push(totalPages);
      }
    }
    
    return pages;
  };

  const buttonBaseClasses = [
    'px-3 py-2 text-sm font-medium transition-colors',
    'border border-gray-300 dark:border-gray-600',
    'hover:bg-gray-50 dark:hover:bg-gray-700',
    'focus:outline-none focus:ring-2 focus:ring-primary-500',
    'disabled:opacity-50 disabled:cursor-not-allowed',
  ];

  const activeClasses = [
    'bg-primary-600 text-white border-primary-600',
    'hover:bg-primary-700 dark:hover:bg-primary-500',
  ];

  const inactiveClasses = [
    'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300',
  ];

  if (totalPages <= 1) {
    return null;
  }

  return (
    <nav className={cn('flex items-center justify-center space-x-1', className)}>
      {/* First page button */}
      <button
        onClick={() => onChange(1, pageSize)}
        disabled={current === 1}
        className={cn(
          buttonBaseClasses,
          inactiveClasses,
          'rounded-l-md'
        )}
        aria-label="First page"
      >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M15.707 15.707a1 1 0 01-1.414 0l-5-5a1 1 0 010-1.414l5-5a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 010 1.414zm-6 0a1 1 0 01-1.414 0l-5-5a1 1 0 010-1.414l5-5a1 1 0 011.414 1.414L5.414 10l4.293 4.293a1 1 0 010 1.414z" clipRule="evenodd" />
          </svg>
        </button>

      {/* Previous page button */}
      <button
        onClick={() => onChange(current - 1, pageSize)}
        disabled={current === 1}
        className={cn(
          buttonBaseClasses,
          inactiveClasses
        )}
        aria-label="Previous page"
      >
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
        </svg>
      </button>

      {/* Page numbers */}
      {getVisiblePages().map((page, index) => {
        if (page === '...') {
          return (
            <span
              key={`ellipsis-${index}`}
              className="px-3 py-2 text-sm text-gray-500 dark:text-gray-400"
            >
              ...
            </span>
          );
        }

        const pageNumber = page as number;
        const isActive = pageNumber === current;

        return (
          <button
            key={pageNumber}
            onClick={() => onChange(pageNumber, pageSize)}
            className={cn(
              buttonBaseClasses,
              isActive ? activeClasses : inactiveClasses
            )}
            aria-label={`Page ${pageNumber}`}
            aria-current={isActive ? 'page' : undefined}
          >
            {pageNumber}
          </button>
        );
      })}

      {/* Next page button */}
      <button
        onClick={() => onChange(current + 1, pageSize)}
        disabled={current === totalPages}
        className={cn(
          buttonBaseClasses,
          inactiveClasses
        )}
        aria-label="Next page"
      >
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
        </svg>
      </button>

      {/* Last page button */}
      <button
        onClick={() => onChange(totalPages, pageSize)}
        disabled={current === totalPages}
        className={cn(
          buttonBaseClasses,
          inactiveClasses,
          'rounded-r-md'
        )}
        aria-label="Last page"
      >
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10.293 15.707a1 1 0 010-1.414L14.586 10l-4.293-4.293a1 1 0 111.414-1.414l5 5a1 1 0 010 1.414l-5 5a1 1 0 01-1.414 0zm-6 0a1 1 0 010-1.414L8.586 10 4.293 5.707a1 1 0 011.414-1.414l5 5a1 1 0 010 1.414l-5 5a1 1 0 01-1.414 0z" clipRule="evenodd" />
        </svg>
      </button>
    </nav>
  );
};

export default Pagination;