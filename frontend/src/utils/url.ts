// URL utilities for parsing, building, and manipulating URLs

// URL parsing and manipulation
export const url = {
  // Parse URL into components
  parse: (urlString: string): {
    protocol: string;
    hostname: string;
    port: string;
    pathname: string;
    search: string;
    hash: string;
    origin: string;
    params: Record<string, string>;
  } | null => {
    try {
      const url = new URL(urlString);
      const params: Record<string, string> = {};
      
      url.searchParams.forEach((value, key) => {
        params[key] = value;
      });
      
      return {
        protocol: url.protocol,
        hostname: url.hostname,
        port: url.port,
        pathname: url.pathname,
        search: url.search,
        hash: url.hash,
        origin: url.origin,
        params,
      };
    } catch {
      return null;
    }
  },

  // Build URL from components
  build: (components: {
    protocol?: string;
    hostname?: string;
    port?: string | number;
    pathname?: string;
    params?: Record<string, string | number | boolean>;
    hash?: string;
  }): string => {
    const {
      protocol = 'https:',
      hostname = 'localhost',
      port,
      pathname = '/',
      params = {},
      hash,
    } = components;
    
    let url = `${protocol}//${hostname}`;
    
    if (port) {
      url += `:${port}`;
    }
    
    url += pathname;
    
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        searchParams.append(key, String(value));
      }
    });
    
    const queryString = searchParams.toString();
    if (queryString) {
      url += `?${queryString}`;
    }
    
    if (hash) {
      url += `#${hash}`;
    }
    
    return url;
  },

  // Add or update query parameters
  addParams: (urlString: string, params: Record<string, string | number | boolean>): string => {
    try {
      const url = new URL(urlString);
      
      Object.entries(params).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
          url.searchParams.set(key, String(value));
        }
      });
      
      return url.toString();
    } catch {
      return urlString;
    }
  },

  // Remove query parameters
  removeParams: (urlString: string, paramNames: string[]): string => {
    try {
      const url = new URL(urlString);
      
      paramNames.forEach(name => {
        url.searchParams.delete(name);
      });
      
      return url.toString();
    } catch {
      return urlString;
    }
  },

  // Get query parameter value
  getParam: (urlString: string, paramName: string): string | null => {
    try {
      const url = new URL(urlString);
      return url.searchParams.get(paramName);
    } catch {
      return null;
    }
  },

  // Get all query parameters
  getParams: (urlString: string): Record<string, string> => {
    const params: Record<string, string> = {};
    
    try {
      const url = new URL(urlString);
      url.searchParams.forEach((value, key) => {
        params[key] = value;
      });
    } catch {
      // Fallback for relative URLs or invalid URLs
      const queryString = urlString.split('?')[1];
      if (queryString) {
        const urlParams = new URLSearchParams(queryString);
        urlParams.forEach((value, key) => {
          params[key] = value;
        });
      }
    }
    
    return params;
  },

  // Check if URL is absolute
  isAbsolute: (urlString: string): boolean => {
    try {
      new URL(urlString);
      return true;
    } catch {
      return false;
    }
  },

  // Check if URL is relative
  isRelative: (urlString: string): boolean => {
    return !url.isAbsolute(urlString);
  },

  // Convert relative URL to absolute
  toAbsolute: (relativeUrl: string, baseUrl: string = window.location.origin): string => {
    try {
      return new URL(relativeUrl, baseUrl).toString();
    } catch {
      return relativeUrl;
    }
  },

  // Get domain from URL
  getDomain: (urlString: string): string | null => {
    try {
      const url = new URL(urlString);
      return url.hostname;
    } catch {
      return null;
    }
  },

  // Get subdomain from URL
  getSubdomain: (urlString: string): string | null => {
    const domain = url.getDomain(urlString);
    if (!domain) return null;
    
    const parts = domain.split('.');
    if (parts.length > 2) {
      return parts.slice(0, -2).join('.');
    }
    
    return null;
  },

  // Check if URLs have same origin
  isSameOrigin: (url1: string, url2: string): boolean => {
    try {
      const urlObj1 = new URL(url1);
      const urlObj2 = new URL(url2);
      return urlObj1.origin === urlObj2.origin;
    } catch {
      return false;
    }
  },

  // Normalize URL (remove trailing slash, etc.)
  normalize: (urlString: string): string => {
    try {
      const url = new URL(urlString);
      
      // Remove trailing slash from pathname (except root)
      if (url.pathname !== '/' && url.pathname.endsWith('/')) {
        url.pathname = url.pathname.slice(0, -1);
      }
      
      return url.toString();
    } catch {
      return urlString;
    }
  },

  // Join URL paths
  join: (...paths: string[]): string => {
    return paths
      .map((path, index) => {
        if (index === 0) {
          return path.replace(/\/+$/, '');
        }
        return path.replace(/^\/+/, '').replace(/\/+$/, '');
      })
      .filter(path => path.length > 0)
      .join('/');
  },
};

// Route utilities
export const route = {
  // Build route with parameters
  build: (pattern: string, params: Record<string, string | number> = {}): string => {
    let route = pattern;
    
    // Replace path parameters (:param)
    Object.entries(params).forEach(([key, value]) => {
      route = route.replace(`:${key}`, String(value));
    });
    
    return route;
  },

  // Extract parameters from route pattern
  extractParams: (pattern: string, path: string): Record<string, string> | null => {
    const patternParts = pattern.split('/');
    const pathParts = path.split('/');
    
    if (patternParts.length !== pathParts.length) {
      return null;
    }
    
    const params: Record<string, string> = {};
    
    for (let i = 0; i < patternParts.length; i++) {
      const patternPart = patternParts[i];
      const pathPart = pathParts[i];
      
      if (patternPart.startsWith(':')) {
        const paramName = patternPart.slice(1);
        params[paramName] = pathPart;
      } else if (patternPart !== pathPart) {
        return null;
      }
    }
    
    return params;
  },

  // Check if path matches pattern
  matches: (pattern: string, path: string): boolean => {
    return route.extractParams(pattern, path) !== null;
  },

  // Get current route from window location
  getCurrent: (): string => {
    return window.location.pathname;
  },

  // Navigate to route (using history API)
  navigate: (path: string, replace: boolean = false): void => {
    if (replace) {
      window.history.replaceState(null, '', path);
    } else {
      window.history.pushState(null, '', path);
    }
    
    // Dispatch popstate event to notify route changes
    window.dispatchEvent(new PopStateEvent('popstate'));
  },

  // Go back in history
  back: (): void => {
    window.history.back();
  },

  // Go forward in history
  forward: (): void => {
    window.history.forward();
  },

  // Reload current page
  reload: (): void => {
    window.location.reload();
  },
};

// Query string utilities
export const queryString = {
  // Parse query string to object
  parse: (queryStr: string): Record<string, string | string[]> => {
    const params: Record<string, string | string[]> = {};
    const urlParams = new URLSearchParams(queryStr.startsWith('?') ? queryStr.slice(1) : queryStr);
    
    for (const [key, value] of urlParams) {
      if (params[key]) {
        // Handle multiple values for same key
        if (Array.isArray(params[key])) {
          (params[key] as string[]).push(value);
        } else {
          params[key] = [params[key] as string, value];
        }
      } else {
        params[key] = value;
      }
    }
    
    return params;
  },

  // Stringify object to query string
  stringify: (params: Record<string, string | number | boolean | string[]>, options: {
    encode?: boolean;
    arrayFormat?: 'brackets' | 'indices' | 'comma';
  } = {}): string => {
    const { encode = true, arrayFormat = 'brackets' } = options;
    const urlParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value === null || value === undefined) {
        return;
      }
      
      if (Array.isArray(value)) {
        value.forEach((item, index) => {
          let paramKey = key;
          
          switch (arrayFormat) {
            case 'brackets':
              paramKey = `${key}[]`;
              break;
            case 'indices':
              paramKey = `${key}[${index}]`;
              break;
            case 'comma':
              if (index === 0) {
                urlParams.set(key, value.join(','));
                return;
              }
              return;
          }
          
          urlParams.append(paramKey, String(item));
        });
      } else {
        urlParams.set(key, String(value));
      }
    });
    
    let result = urlParams.toString();
    
    if (!encode) {
      result = decodeURIComponent(result);
    }
    
    return result;
  },

  // Add parameters to existing query string
  add: (queryStr: string, params: Record<string, string | number | boolean>): string => {
    const existing = queryString.parse(queryStr);
    const merged = { ...existing, ...params };
    return queryString.stringify(merged);
  },

  // Remove parameters from query string
  remove: (queryStr: string, keys: string[]): string => {
    const params = queryString.parse(queryStr);
    
    keys.forEach(key => {
      delete params[key];
    });
    
    return queryString.stringify(params);
  },

  // Get parameter value from query string
  get: (queryStr: string, key: string): string | string[] | undefined => {
    const params = queryString.parse(queryStr);
    return params[key];
  },

  // Check if parameter exists in query string
  has: (queryStr: string, key: string): boolean => {
    const params = queryString.parse(queryStr);
    return key in params;
  },
};

// Hash utilities
export const urlHash = {
  // Get current hash from URL
  get: (): string => {
    return window.location.hash.slice(1); // Remove #
  },

  // Set hash in URL
  set: (hashValue: string): void => {
    window.location.hash = hashValue;
  },

  // Remove hash from URL
  remove: (): void => {
    window.history.replaceState(null, '', window.location.pathname + window.location.search);
  },

  // Parse hash as query string
  parseAsQuery: (hashValue?: string): Record<string, string> => {
    const hashStr = hashValue || urlHash.get();
    return queryString.parse(hashStr) as Record<string, string>;
  },

  // Build hash from object
  buildFromQuery: (params: Record<string, string | number | boolean>): string => {
    return queryString.stringify(params);
  },
};

// URL validation utilities
export const validate = {
  // Check if string is valid URL
  isUrl: (str: string): boolean => {
    try {
      new URL(str);
      return true;
    } catch {
      return false;
    }
  },

  // Check if URL is HTTP/HTTPS
  isHttp: (urlString: string): boolean => {
    try {
      const url = new URL(urlString);
      return url.protocol === 'http:' || url.protocol === 'https:';
    } catch {
      return false;
    }
  },

  // Check if URL is HTTPS
  isHttps: (urlString: string): boolean => {
    try {
      const url = new URL(urlString);
      return url.protocol === 'https:';
    } catch {
      return false;
    }
  },

  // Check if URL is localhost
  isLocalhost: (urlString: string): boolean => {
    try {
      const url = new URL(urlString);
      return url.hostname === 'localhost' || url.hostname === '127.0.0.1' || url.hostname === '::1';
    } catch {
      return false;
    }
  },

  // Check if URL is external (different origin)
  isExternal: (urlString: string): boolean => {
    try {
      const url = new URL(urlString);
      return url.origin !== window.location.origin;
    } catch {
      return false;
    }
  },

  // Check if URL is email
  isEmail: (str: string): boolean => {
    return str.startsWith('mailto:');
  },

  // Check if URL is tel
  isTel: (str: string): boolean => {
    return str.startsWith('tel:');
  },

  // Check if URL is file
  isFile: (str: string): boolean => {
    return str.startsWith('file:');
  },

  // Check if URL is data URI
  isDataUri: (str: string): boolean => {
    return str.startsWith('data:');
  },

  // Check if URL is blob
  isBlob: (str: string): boolean => {
    return str.startsWith('blob:');
  },
};

// URL encoding/decoding utilities
export const encode = {
  // Encode URI component
  component: (str: string): string => {
    return encodeURIComponent(str);
  },

  // Decode URI component
  decodeComponent: (str: string): string => {
    try {
      return decodeURIComponent(str);
    } catch {
      return str;
    }
  },

  // Encode full URI
  uri: (str: string): string => {
    return encodeURI(str);
  },

  // Decode full URI
  decodeUri: (str: string): string => {
    try {
      return decodeURI(str);
    } catch {
      return str;
    }
  },

  // HTML encode (for display in HTML)
  html: (str: string): string => {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  },

  // HTML decode
  decodeHtml: (str: string): string => {
    const div = document.createElement('div');
    div.innerHTML = str;
    return div.textContent || div.innerText || '';
  },
};

// Utility functions
export const urlUtils = {
  // Get file extension from URL
  getExtension: (urlString: string): string | null => {
    try {
      const url = new URL(urlString);
      const pathname = url.pathname;
      const lastDot = pathname.lastIndexOf('.');
      
      if (lastDot === -1 || lastDot === pathname.length - 1) {
        return null;
      }
      
      return pathname.slice(lastDot + 1).toLowerCase();
    } catch {
      return null;
    }
  },

  // Get filename from URL
  getFilename: (urlString: string): string | null => {
    try {
      const url = new URL(urlString);
      const pathname = url.pathname;
      const lastSlash = pathname.lastIndexOf('/');
      
      if (lastSlash === -1) {
        return pathname;
      }
      
      return pathname.slice(lastSlash + 1) || null;
    } catch {
      return null;
    }
  },

  // Shorten URL for display
  shorten: (urlString: string, maxLength: number = 50): string => {
    if (urlString.length <= maxLength) {
      return urlString;
    }
    
    try {
      const url = new URL(urlString);
      const domain = url.hostname;
      const path = url.pathname;
      
      if (domain.length >= maxLength - 3) {
        return domain.slice(0, maxLength - 3) + '...';
      }
      
      const availableLength = maxLength - domain.length - 3; // 3 for '...'
      
      if (path.length <= availableLength) {
        return domain + path;
      }
      
      return domain + path.slice(0, availableLength) + '...';
    } catch {
      return urlString.slice(0, maxLength - 3) + '...';
    }
  },

  // Get favicon URL for domain
  getFaviconUrl: (urlString: string): string | null => {
    try {
      const url = new URL(urlString);
      return `${url.protocol}//${url.hostname}/favicon.ico`;
    } catch {
      return null;
    }
  },

  // Convert URL to safe filename
  toSafeFilename: (urlString: string): string => {
    return urlString
      .replace(/[^a-zA-Z0-9.-]/g, '_')
      .replace(/_+/g, '_')
      .replace(/^_|_$/g, '');
  },
};