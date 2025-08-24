// Pagination hook
import { useState, useCallback, useMemo } from 'react';
import { type UsePaginationReturn } from './types';
import { UI_CONFIG } from '../config';

interface UsePaginationOptions {
  initialPage?: number;
  initialPageSize?: number;
  totalItems?: number;
  maxVisiblePages?: number;
  boundaryCount?: number;
  siblingCount?: number;
}

const usePagination = (options: UsePaginationOptions = {}): UsePaginationReturn => {
  const {
    initialPage = 1,
    initialPageSize = UI_CONFIG.PAGINATION.DEFAULT_PAGE_SIZE,
    totalItems = 0,
    maxVisiblePages = UI_CONFIG.PAGINATION.MAX_VISIBLE_PAGES,
    boundaryCount = 1,
  } = options;

  const [currentPage, setCurrentPage] = useState(initialPage);
  const [pageSize, setPageSize] = useState(initialPageSize);

  // Calculate derived values
  const totalPages = useMemo(() => {
    return Math.ceil(totalItems / pageSize) || 1;
  }, [totalItems, pageSize]);

  const startIndex = useMemo(() => {
    return (currentPage - 1) * pageSize;
  }, [currentPage, pageSize]);

  const endIndex = useMemo(() => {
    return Math.min(startIndex + pageSize - 1, totalItems - 1);
  }, [startIndex, pageSize, totalItems]);

  // Generate visible page numbers
  const visiblePages = useMemo(() => {
    const pages: number[] = [];
    
    if (totalPages <= maxVisiblePages) {
      // Show all pages if total is less than max visible
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Calculate start and end of visible range
      const halfVisible = Math.floor(maxVisiblePages / 2);
      let startPage = Math.max(1, currentPage - halfVisible);
      const endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
      
      // Adjust if we're near the end
      if (endPage - startPage + 1 < maxVisiblePages) {
        startPage = Math.max(1, endPage - maxVisiblePages + 1);
      }
      
      // Add boundary pages at the beginning
      for (let i = 1; i <= Math.min(boundaryCount, startPage - 1); i++) {
        pages.push(i);
      }
      
      // Add ellipsis if there's a gap
      if (startPage > boundaryCount + 1) {
        pages.push(-1); // -1 represents ellipsis
      }
      
      // Add pages around current page
      for (let i = startPage; i <= endPage; i++) {
        if (i > boundaryCount && i <= totalPages - boundaryCount) {
          pages.push(i);
        }
      }
      
      // Add ellipsis if there's a gap
      if (endPage < totalPages - boundaryCount) {
        pages.push(-1); // -1 represents ellipsis
      }
      
      // Add boundary pages at the end
      for (let i = Math.max(totalPages - boundaryCount + 1, endPage + 1); i <= totalPages; i++) {
        pages.push(i);
      }
    }
    
    return pages;
  }, [totalPages, currentPage, maxVisiblePages, boundaryCount]);

  // Navigation functions
  const goToPage = useCallback((page: number): void => {
    const targetPage = Math.max(1, Math.min(page, totalPages));
    setCurrentPage(targetPage);
  }, [totalPages]);

  const goToFirstPage = useCallback((): void => {
    setCurrentPage(1);
  }, []);

  const goToLastPage = useCallback((): void => {
    setCurrentPage(totalPages);
  }, [totalPages]);

  const goToPreviousPage = useCallback((): void => {
    setCurrentPage(prev => Math.max(1, prev - 1));
  }, []);

  const goToNextPage = useCallback((): void => {
    setCurrentPage(prev => Math.min(totalPages, prev + 1));
  }, [totalPages]);

  // Page size functions
  const changePageSize = useCallback((newPageSize: number): void => {
    const newTotalPages = Math.ceil(totalItems / newPageSize) || 1;
    const newCurrentPage = Math.min(currentPage, newTotalPages);
    
    setPageSize(newPageSize);
    setCurrentPage(newCurrentPage);
  }, [totalItems, currentPage]);

  // Check if navigation is possible
  const hasNextPage = currentPage < totalPages;
  const hasPreviousPage = currentPage > 1;

  // Reset pagination
  const reset = useCallback((): void => {
    setCurrentPage(1);
  }, []);

  return {
    // Current state
    currentPage,
    pageSize,
    totalPages,
    totalItems,
    startIndex,
    endIndex,
    visiblePages,
    
    // Navigation capabilities
    hasNextPage,
    hasPreviousPage,
    
    // Navigation functions
    goToPage,
    goToFirstPage,
    goToLastPage,
    goToPreviousPage,
    goToNextPage,
    
    // Page size functions
    setPageSize: changePageSize,
    
    // Utility functions
    reset,
  };
};

// Pagination utilities
export const paginationUtils = {
  // Calculate total pages
  calculateTotalPages: (totalItems: number, pageSize: number): number => {
    return Math.ceil(totalItems / pageSize) || 1;
  },

  // Calculate start index
  calculateStartIndex: (page: number, pageSize: number): number => {
    return (page - 1) * pageSize;
  },

  // Calculate end index
  calculateEndIndex: (page: number, pageSize: number, totalItems: number): number => {
    const startIndex = paginationUtils.calculateStartIndex(page, pageSize);
    return Math.min(startIndex + pageSize - 1, totalItems - 1);
  },

  // Get page for item index
  getPageForIndex: (index: number, pageSize: number): number => {
    return Math.floor(index / pageSize) + 1;
  },

  // Validate page number
  validatePage: (page: number, totalPages: number): number => {
    return Math.max(1, Math.min(page, totalPages));
  },

  // Generate page size options
  generatePageSizeOptions: (baseSize: number = 10): number[] => {
    return [baseSize, baseSize * 2, baseSize * 5, baseSize * 10];
  },

  // Format pagination info text
  formatPaginationInfo: ({
    startIndex,
    endIndex,
    totalItems,
    currentPage,
    totalPages,
  }: {
    startIndex: number;
    endIndex: number;
    totalItems: number;
    currentPage: number;
    totalPages: number;
  }): string => {
    if (totalItems === 0) {
      return 'No items found';
    }
    
    if (totalPages === 1) {
      return `Showing ${totalItems} item${totalItems === 1 ? '' : 's'}`;
    }
    
    return `Showing ${startIndex + 1}-${endIndex + 1} of ${totalItems} items (Page ${currentPage} of ${totalPages})`;
  },

  // Create pagination metadata for API responses
  createPaginationMeta: ({
    page,
    pageSize,
    totalItems,
    totalPages,
  }: {
    page: number;
    pageSize: number;
    totalItems: number;
    totalPages: number;
  }) => {
    const startIndex = paginationUtils.calculateStartIndex(page, pageSize);
    const endIndex = paginationUtils.calculateEndIndex(page, pageSize, totalItems);
    
    return {
      page,
      pageSize,
      totalItems,
      totalPages,
      startIndex,
      endIndex,
      hasNextPage: page < totalPages,
      hasPreviousPage: page > 1,
      isFirstPage: page === 1,
      isLastPage: page === totalPages,
    };
  },

  // Slice array based on pagination
  sliceArray: <T>(array: T[], page: number, pageSize: number): T[] => {
    const startIndex = paginationUtils.calculateStartIndex(page, pageSize);
    return array.slice(startIndex, startIndex + pageSize);
  },

  // Search within paginated data
  searchAndPaginate: <T>(
    data: T[],
    searchTerm: string,
    searchFields: (keyof T)[],
    page: number,
    pageSize: number
  ): {
    items: T[];
    totalItems: number;
    totalPages: number;
  } => {
    // Filter data based on search term
    const filteredData = searchTerm
      ? data.filter(item =>
          searchFields.some(field => {
            const value = item[field];
            return value && 
              String(value).toLowerCase().includes(searchTerm.toLowerCase());
          })
        )
      : data;

    // Calculate pagination
    const totalItems = filteredData.length;
    const totalPages = paginationUtils.calculateTotalPages(totalItems, pageSize);
    const items = paginationUtils.sliceArray(filteredData, page, pageSize);

    return {
      items,
      totalItems,
      totalPages,
    };
  },

  // Sort and paginate data
  sortAndPaginate: <T>(
    data: T[],
    sortField: keyof T,
    sortDirection: 'asc' | 'desc',
    page: number,
    pageSize: number
  ): {
    items: T[];
    totalItems: number;
    totalPages: number;
  } => {
    // Sort data
    const sortedData = [...data].sort((a, b) => {
      const aValue = a[sortField];
      const bValue = b[sortField];
      
      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    // Calculate pagination
    const totalItems = sortedData.length;
    const totalPages = paginationUtils.calculateTotalPages(totalItems, pageSize);
    const items = paginationUtils.sliceArray(sortedData, page, pageSize);

    return {
      items,
      totalItems,
      totalPages,
    };
  },
};

export default usePagination;