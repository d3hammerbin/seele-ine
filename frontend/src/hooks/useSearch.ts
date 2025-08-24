// Search hook
import { useState, useCallback, useEffect, useMemo } from 'react';
import type { UseSearchReturn, SearchConfig, SearchResult } from './types';
import { useDebounce } from './useDebounce';
import { apiClient } from '../utils/api';

interface UseSearchOptions<T> {
  initialQuery?: string;
  debounceMs?: number;
  minQueryLength?: number;
  searchFields?: (keyof T)[];
  caseSensitive?: boolean;
  exactMatch?: boolean;
  highlightMatches?: boolean;
  maxResults?: number;
  searchOnMount?: boolean;
  endpoint?: string;
  transform?: (data: unknown) => T[];
}

const useSearch = <T = unknown>(options: UseSearchOptions<T> = {}): UseSearchReturn<T> => {
  const {
    initialQuery = '',
    debounceMs = 300,
    minQueryLength = 1,
    searchFields = [],
    caseSensitive = false,
    exactMatch = false,
    highlightMatches = false,
    maxResults = 100,
    searchOnMount = false,
    endpoint,
    transform,
  } = options;

  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState<T[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalResults, setTotalResults] = useState(0);
  const [searchHistory, setSearchHistory] = useState<string[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);

  // Debounced query for API calls
  const debouncedQuery = useDebounce(query, debounceMs);

  // Search configuration
  const searchConfig: SearchConfig = useMemo(() => ({
    query: debouncedQuery,
    fields: searchFields,
    caseSensitive,
    exactMatch,
    highlightMatches,
    maxResults,
  }), [debouncedQuery, searchFields, caseSensitive, exactMatch, highlightMatches, maxResults]);

  // Perform search
  const performSearch = useCallback(async (searchQuery: string): Promise<SearchResult<T>> => {
    if (!searchQuery || searchQuery.length < minQueryLength) {
      return {
        query: searchQuery,
        results: [],
        total: 0,
        searchTime: 0,
        hasMore: false,
      };
    }

    const startTime = Date.now();
    setIsSearching(true);
    setError(null);

    try {
      let searchResults: T[] = [];
      let total = 0;

      if (endpoint) {
        // API search
        const queryParams = {
          q: searchQuery,
          fields: searchFields.join(','),
          caseSensitive: caseSensitive.toString(),
          exactMatch: exactMatch.toString(),
          limit: maxResults.toString(),
        };
        const queryString = new URLSearchParams(queryParams).toString();
        const url = `${endpoint}?${queryString}`;
        const response = await apiClient.get(url);

        if (transform) {
          searchResults = transform(response?.data);
        } else {
          searchResults = (response as any)?.data?.results || (response as any)?.data?.items || (response as any)?.data || [];
          total = (response as any)?.data?.total || (response as any)?.data?.totalResults || searchResults.length;
        }
      }

      const searchTime = Date.now() - startTime;
      const result: SearchResult<T> = {
        query: searchQuery,
        results: searchResults,
        total,
        searchTime,
        hasMore: total > maxResults,
      };

      setResults(searchResults);
      setTotalResults(total);

      // Add to search history
      if (searchQuery.trim()) {
        setSearchHistory(prev => {
          const updated = [searchQuery, ...prev.filter(q => q !== searchQuery)];
          return updated.slice(0, 10); // Keep last 10 searches
        });
      }

      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Search failed');
      setError(error.message);
      setResults([]);
      setTotalResults(0);
      throw error;
    } finally {
      setIsSearching(false);
    }
  }, [endpoint, searchFields, caseSensitive, exactMatch, maxResults, minQueryLength, transform]);

  // Local search function
  const searchLocal = useCallback((searchQuery: string, data: T[]): SearchResult<T> => {
    if (!searchQuery || searchQuery.length < minQueryLength) {
      return {
        query: searchQuery,
        results: [],
        total: 0,
        searchTime: 0,
        hasMore: false,
      };
    }

    const startTime = Date.now();
    const queryLower = caseSensitive ? searchQuery : searchQuery.toLowerCase();

    const filteredResults = data.filter(item => {
      if (searchFields.length === 0) {
        // Search all string fields if no specific fields provided
        return Object.values(item as Record<string, unknown>).some(value => {
          if (typeof value === 'string') {
            const valueToSearch = caseSensitive ? value : value.toLowerCase();
            return exactMatch 
              ? valueToSearch === queryLower
              : valueToSearch.includes(queryLower);
          }
          return false;
        });
      }

      // Search specific fields
      return searchFields.some(field => {
        const value = item[field];
        if (typeof value === 'string') {
          const valueToSearch = caseSensitive ? value : value.toLowerCase();
          return exactMatch 
            ? valueToSearch === queryLower
            : valueToSearch.includes(queryLower);
        }
        return false;
      });
    });

    const limitedResults = filteredResults.slice(0, maxResults);
    const searchTime = Date.now() - startTime;

    return {
      query: searchQuery,
      results: limitedResults,
      total: filteredResults.length,
      searchTime,
      hasMore: filteredResults.length > maxResults,
    };
  }, [searchFields, caseSensitive, exactMatch, maxResults, minQueryLength]);

  // Update query
  const updateQuery = useCallback((newQuery: string): void => {
    setQuery(newQuery);
  }, []);

  // Clear search
  const clearSearch = useCallback((): void => {
    setQuery('');
    setResults([]);
    setTotalResults(0);
    setError(null);
  }, []);

  // Clear history
  const clearHistory = useCallback((): void => {
    setSearchHistory([]);
  }, []);

  // Get suggestions based on history and current query
  const getSuggestions = useCallback((currentQuery: string): string[] => {
    if (!currentQuery.trim()) {
      return searchHistory.slice(0, 5);
    }

    const queryLower = currentQuery.toLowerCase();
    return searchHistory
      .filter(historyItem => 
        historyItem.toLowerCase().includes(queryLower) && 
        historyItem !== currentQuery
      )
      .slice(0, 5);
  }, [searchHistory]);

  // Update suggestions when query changes
  useEffect(() => {
    setSuggestions(getSuggestions(query));
  }, [query, getSuggestions]);

  // Perform search when debounced query changes
  useEffect(() => {
    if (endpoint && (debouncedQuery || searchOnMount)) {
      performSearch(debouncedQuery);
    }
  }, [debouncedQuery, performSearch, endpoint, searchOnMount]);

  // Search on mount if enabled
  useEffect(() => {
    if (searchOnMount && initialQuery) {
      performSearch(initialQuery);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    // Current state
    query,
    results,
    isSearching,
    error,
    totalResults,
    hasMore: false, // Add missing property
    searchHistory,
    suggestions,
    searchConfig,

    // Actions
    setQuery: updateQuery, // Map to expected name
    updateQuery,
    search: async (query?: string) => {
      await performSearch(query || '');
    },
    performSearch: async (query: string) => {
      await performSearch(query);
      return {
        query,
        results: results,
        total: totalResults,
        hasMore: false,
        searchTime: 0
      };
    },
    searchLocal,
    loadMore: async () => {}, // Add missing function
    clearResults: clearSearch, // Map to expected name
    reset: clearSearch, // Map to expected name
    clearSearch,
    clearHistory,
    getSuggestions,
  };
};

// Search utilities
export const searchUtils = {
  // Highlight search matches in text
  highlightMatches: (text: string, query: string, caseSensitive = false): string => {
    if (!query.trim()) return text;

    const flags = caseSensitive ? 'g' : 'gi';
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, flags);
    
    return text.replace(regex, '<mark>$1</mark>');
  },

  // Extract search terms from query
  extractSearchTerms: (query: string): string[] => {
    return query
      .trim()
      .split(/\s+/)
      .filter(term => term.length > 0)
      .map(term => term.toLowerCase());
  },

  // Calculate search relevance score
  calculateRelevance: <T>(
    item: T,
    query: string,
    searchFields: (keyof T)[],
    caseSensitive = false
  ): number => {
    if (!query.trim()) return 0;

    const queryLower = caseSensitive ? query : query.toLowerCase();
    let score = 0;

    searchFields.forEach((field, fieldIndex) => {
      const value = item[field];
      if (typeof value === 'string') {
        const valueToSearch = caseSensitive ? value : value.toLowerCase();
        
        // Exact match gets highest score
        if (valueToSearch === queryLower) {
          score += 100 - fieldIndex * 10;
        }
        // Starts with query gets high score
        else if (valueToSearch.startsWith(queryLower)) {
          score += 50 - fieldIndex * 5;
        }
        // Contains query gets lower score
        else if (valueToSearch.includes(queryLower)) {
          score += 25 - fieldIndex * 2;
        }
      }
    });

    return score;
  },

  // Sort results by relevance
  sortByRelevance: <T>(
    results: T[],
    query: string,
    searchFields: (keyof T)[],
    caseSensitive = false
  ): T[] => {
    return results
      .map(item => ({
        item,
        relevance: searchUtils.calculateRelevance(item, query, searchFields, caseSensitive),
      }))
      .sort((a, b) => b.relevance - a.relevance)
      .map(({ item }) => item);
  },

  // Create search index for faster searching
  createSearchIndex: <T>(
    data: T[],
    searchFields: (keyof T)[]
  ): Map<string, T[]> => {
    const index = new Map<string, T[]>();

    data.forEach(item => {
      searchFields.forEach(field => {
        const value = item[field];
        if (typeof value === 'string') {
          const words = value.toLowerCase().split(/\s+/);
          words.forEach(word => {
            if (word.length > 0) {
              const existing = index.get(word) || [];
              existing.push(item);
              index.set(word, existing);
            }
          });
        }
      });
    });

    return index;
  },

  // Search using pre-built index
  searchWithIndex: <T>(
    index: Map<string, T[]>,
    query: string,
    maxResults = 100
  ): T[] => {
    if (!query.trim()) return [];

    const terms = searchUtils.extractSearchTerms(query);
    if (terms.length === 0) return [];

    // Get items that match all terms (AND operation)
    let results = index.get(terms[0]) || [];
    
    for (let i = 1; i < terms.length; i++) {
      const termResults = index.get(terms[i]) || [];
      results = results.filter(item => termResults.includes(item));
    }

    // Remove duplicates and limit results
    const uniqueResults = Array.from(new Set(results));
    return uniqueResults.slice(0, maxResults);
  },

  // Fuzzy search implementation
  fuzzySearch: <T>(
    data: T[],
    query: string,
    searchFields: (keyof T)[],
    threshold = 0.6
  ): T[] => {
    if (!query.trim()) return [];

    const calculateSimilarity = (str1: string, str2: string): number => {
      const longer = str1.length > str2.length ? str1 : str2;
      const shorter = str1.length > str2.length ? str2 : str1;
      
      if (longer.length === 0) return 1.0;
      
      const editDistance = levenshteinDistance(longer, shorter);
      return (longer.length - editDistance) / longer.length;
    };

    const levenshteinDistance = (str1: string, str2: string): number => {
      const matrix = [];
      
      for (let i = 0; i <= str2.length; i++) {
        matrix[i] = [i];
      }
      
      for (let j = 0; j <= str1.length; j++) {
        matrix[0][j] = j;
      }
      
      for (let i = 1; i <= str2.length; i++) {
        for (let j = 1; j <= str1.length; j++) {
          if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
            matrix[i][j] = matrix[i - 1][j - 1];
          } else {
            matrix[i][j] = Math.min(
              matrix[i - 1][j - 1] + 1,
              matrix[i][j - 1] + 1,
              matrix[i - 1][j] + 1
            );
          }
        }
      }
      
      return matrix[str2.length][str1.length];
    };

    return data
      .map(item => {
        let maxSimilarity = 0;
        
        searchFields.forEach(field => {
          const value = item[field];
          if (typeof value === 'string') {
            const similarity = calculateSimilarity(
              query.toLowerCase(),
              value.toLowerCase()
            );
            maxSimilarity = Math.max(maxSimilarity, similarity);
          }
        });
        
        return { item, similarity: maxSimilarity };
      })
      .filter(({ similarity }) => similarity >= threshold)
      .sort((a, b) => b.similarity - a.similarity)
      .map(({ item }) => item);
  },
};

export default useSearch;