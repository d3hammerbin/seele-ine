// Class name utility
export { cn } from './cn';

// DOM utilities
export const dom = {
  // Get element by ID
  getElementById: (id: string): HTMLElement | null => {
    return document.getElementById(id);
  },

  // Query selector
  querySelector: (selector: string): Element | null => {
    return document.querySelector(selector);
  },

  // Query selector all
  querySelectorAll: (selector: string): NodeListOf<Element> => {
    return document.querySelectorAll(selector);
  },

  // Add class to element
  addClass: (element: Element, className: string): void => {
    element.classList.add(className);
  },

  // Remove class from element
  removeClass: (element: Element, className: string): void => {
    element.classList.remove(className);
  },

  // Toggle class on element
  toggleClass: (element: Element, className: string): void => {
    element.classList.toggle(className);
  },

  // Check if element has class
  hasClass: (element: Element, className: string): boolean => {
    return element.classList.contains(className);
  },

  // Set attribute
  setAttribute: (element: Element, name: string, value: string): void => {
    element.setAttribute(name, value);
  },

  // Get attribute
  getAttribute: (element: Element, name: string): string | null => {
    return element.getAttribute(name);
  },

  // Remove attribute
  removeAttribute: (element: Element, name: string): void => {
    element.removeAttribute(name);
  },

  // Set style
  setStyle: (element: HTMLElement, property: string, value: string): void => {
    element.style.setProperty(property, value);
  },

  // Get computed style
  getComputedStyle: (element: Element, property?: string): string | CSSStyleDeclaration => {
    const styles = window.getComputedStyle(element);
    return property ? styles.getPropertyValue(property) : styles;
  },

  // Check if element is visible
  isVisible: (element: Element): boolean => {
    const rect = element.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  },

  // Scroll to element
  scrollToElement: (element: Element, behavior: ScrollBehavior = 'smooth'): void => {
    element.scrollIntoView({ behavior, block: 'start' });
  },

  // Get element position
  getElementPosition: (element: Element): { top: number; left: number; width: number; height: number } => {
    const rect = element.getBoundingClientRect();
    return {
      top: rect.top + window.scrollY,
      left: rect.left + window.scrollX,
      width: rect.width,
      height: rect.height,
    };
  },
};

// Event utilities
export const events = {
  // Add event listener
  on: (element: Element | Window | Document, event: string, handler: EventListener): void => {
    element.addEventListener(event, handler);
  },

  // Remove event listener
  off: (element: Element | Window | Document, event: string, handler: EventListener): void => {
    element.removeEventListener(event, handler);
  },

  // Add event listener that runs once
  once: (element: Element | Window | Document, event: string, handler: EventListener): void => {
    element.addEventListener(event, handler, { once: true });
  },

  // Trigger custom event
  trigger: (element: Element, eventName: string, detail?: unknown): void => {
    const event = new CustomEvent(eventName, { detail });
    element.dispatchEvent(event);
  },

  // Prevent default and stop propagation
  stop: (event: Event): void => {
    event.preventDefault();
    event.stopPropagation();
  },

  // Debounced event handler
  debounce: <T extends (...args: unknown[]) => unknown>(
    func: T,
    wait: number
  ): ((...args: Parameters<T>) => void) => {
    let timeout: NodeJS.Timeout;
    return (...args: Parameters<T>) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => func(...args), wait);
    };
  },

  // Throttled event handler
  throttle: <T extends (...args: unknown[]) => unknown>(
    func: T,
    limit: number
  ): ((...args: Parameters<T>) => void) => {
    let inThrottle: boolean;
    return (...args: Parameters<T>) => {
      if (!inThrottle) {
        func(...args);
        inThrottle = true;
        setTimeout(() => (inThrottle = false), limit);
      }
    };
  },
};

// Browser utilities
export const browser = {
  // Get user agent
  getUserAgent: (): string => {
    return navigator.userAgent;
  },

  // Check if mobile
  isMobile: (): boolean => {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
  },

  // Check if tablet
  isTablet: (): boolean => {
    return /iPad|Android(?!.*Mobile)/i.test(navigator.userAgent);
  },

  // Check if desktop
  isDesktop: (): boolean => {
    return !browser.isMobile() && !browser.isTablet();
  },

  // Get browser name
  getBrowserName: (): string => {
    const userAgent = navigator.userAgent;
    if (userAgent.includes('Chrome')) return 'Chrome';
    if (userAgent.includes('Firefox')) return 'Firefox';
    if (userAgent.includes('Safari')) return 'Safari';
    if (userAgent.includes('Edge')) return 'Edge';
    if (userAgent.includes('Opera')) return 'Opera';
    return 'Unknown';
  },

  // Check if online
  isOnline: (): boolean => {
    return navigator.onLine;
  },

  // Get viewport size
  getViewportSize: (): { width: number; height: number } => {
    return {
      width: window.innerWidth,
      height: window.innerHeight,
    };
  },

  // Copy to clipboard
  copyToClipboard: async (text: string): Promise<boolean> => {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      const success = document.execCommand('copy');
      document.body.removeChild(textArea);
      return success;
    }
  },

  // Read from clipboard
  readFromClipboard: async (): Promise<string | null> => {
    try {
      return await navigator.clipboard.readText();
    } catch {
      return null;
    }
  },

  // Get device pixel ratio
  getPixelRatio: (): number => {
    return window.devicePixelRatio || 1;
  },

  // Check if touch device
  isTouchDevice: (): boolean => {
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  },
};

// Color utilities
export const color = {
  // Convert hex to RGB
  hexToRgb: (hex: string): { r: number; g: number; b: number } | null => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result
      ? {
          r: parseInt(result[1], 16),
          g: parseInt(result[2], 16),
          b: parseInt(result[3], 16),
        }
      : null;
  },

  // Convert RGB to hex
  rgbToHex: (r: number, g: number, b: number): string => {
    return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
  },

  // Convert hex to HSL
  hexToHsl: (hex: string): { h: number; s: number; l: number } | null => {
    const rgb = color.hexToRgb(hex);
    if (!rgb) return null;
    return color.rgbToHsl(rgb.r, rgb.g, rgb.b);
  },

  // Convert RGB to HSL
  rgbToHsl: (r: number, g: number, b: number): { h: number; s: number; l: number } => {
    r /= 255;
    g /= 255;
    b /= 255;
    
    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    let h = 0;
    let s = 0;
    const l = (max + min) / 2;
    
    if (max !== min) {
      const d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
      
      switch (max) {
        case r:
          h = (g - b) / d + (g < b ? 6 : 0);
          break;
        case g:
          h = (b - r) / d + 2;
          break;
        case b:
          h = (r - g) / d + 4;
          break;
      }
      h /= 6;
    }
    
    return { h: h * 360, s: s * 100, l: l * 100 };
  },

  // Generate random color
  randomColor: (): string => {
    return `#${Math.floor(Math.random() * 16777215).toString(16).padStart(6, '0')}`;
  },

  // Lighten color
  lighten: (hex: string, amount: number): string => {
    const rgb = color.hexToRgb(hex);
    if (!rgb) return hex;
    
    const r = Math.min(255, Math.floor(rgb.r + (255 - rgb.r) * amount));
    const g = Math.min(255, Math.floor(rgb.g + (255 - rgb.g) * amount));
    const b = Math.min(255, Math.floor(rgb.b + (255 - rgb.b) * amount));
    
    return color.rgbToHex(r, g, b);
  },

  // Darken color
  darken: (hex: string, amount: number): string => {
    const rgb = color.hexToRgb(hex);
    if (!rgb) return hex;
    
    const r = Math.max(0, Math.floor(rgb.r * (1 - amount)));
    const g = Math.max(0, Math.floor(rgb.g * (1 - amount)));
    const b = Math.max(0, Math.floor(rgb.b * (1 - amount)));
    
    return color.rgbToHex(r, g, b);
  },
};

// Math utilities
export const math = {
  // Clamp value between min and max
  clamp: (value: number, min: number, max: number): number => {
    return Math.min(Math.max(value, min), max);
  },

  // Linear interpolation
  lerp: (start: number, end: number, factor: number): number => {
    return start + (end - start) * factor;
  },

  // Map value from one range to another
  map: (value: number, inMin: number, inMax: number, outMin: number, outMax: number): number => {
    return ((value - inMin) * (outMax - outMin)) / (inMax - inMin) + outMin;
  },

  // Round to decimal places
  round: (value: number, decimals: number = 0): number => {
    const factor = Math.pow(10, decimals);
    return Math.round(value * factor) / factor;
  },

  // Generate random number between min and max
  random: (min: number, max: number): number => {
    return Math.random() * (max - min) + min;
  },

  // Generate random integer between min and max
  randomInt: (min: number, max: number): number => {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  },

  // Calculate distance between two points
  distance: (x1: number, y1: number, x2: number, y2: number): number => {
    return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
  },

  // Calculate angle between two points
  angle: (x1: number, y1: number, x2: number, y2: number): number => {
    return Math.atan2(y2 - y1, x2 - x1);
  },

  // Convert degrees to radians
  toRadians: (degrees: number): number => {
    return (degrees * Math.PI) / 180;
  },

  // Convert radians to degrees
  toDegrees: (radians: number): number => {
    return (radians * 180) / Math.PI;
  },
};

// Performance utilities
export const performance = {
  // Measure execution time
  measure: async <T>(fn: () => T | Promise<T>, label?: string): Promise<{ result: T; duration: number }> => {
    const start = Date.now();
    const result = await fn();
    const duration = Date.now() - start;
    
    if (label) {
      console.log(`${label}: ${duration}ms`);
    }
    
    return { result, duration };
  },

  // Debounce function
  debounce: <T extends (...args: unknown[]) => unknown>(
    func: T,
    wait: number
  ): ((...args: Parameters<T>) => void) => {
    let timeout: NodeJS.Timeout;
    return (...args: Parameters<T>) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => func(...args), wait);
    };
  },

  // Throttle function
  throttle: <T extends (...args: unknown[]) => unknown>(
    func: T,
    limit: number
  ): ((...args: Parameters<T>) => void) => {
    let inThrottle: boolean;
    return (...args: Parameters<T>) => {
      if (!inThrottle) {
        func(...args);
        inThrottle = true;
        setTimeout(() => (inThrottle = false), limit);
      }
    };
  },

  // Request animation frame wrapper
  raf: (callback: FrameRequestCallback): number => {
    return requestAnimationFrame(callback);
  },

  // Cancel animation frame
  cancelRaf: (id: number): void => {
    cancelAnimationFrame(id);
  },
};

// Utility functions
export const utils = {
  // Generate UUID
  generateId: (): string => {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  },

  // Generate short ID
  generateShortId: (length: number = 8): string => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  },

  // Create slug from string
  createSlug: (text: string): string => {
    return text
      .toLowerCase()
      .replace(/[^\w\s-]/g, '')
      .replace(/[\s_-]+/g, '-')
      .replace(/^-+|-+$/g, '');
  },

  // Parse query string
  parseQueryString: (queryString: string): Record<string, string> => {
    const params: Record<string, string> = {};
    const urlParams = new URLSearchParams(queryString);
    
    Array.from(urlParams.entries()).forEach(([key, value]) => {
      params[key] = value;
    });
    
    return params;
  },

  // Build query string
  buildQueryString: (params: Record<string, unknown>): string => {
    const urlParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        urlParams.append(key, String(value));
      }
    });
    
    return urlParams.toString();
  },

  // Safe JSON parse
  safeJsonParse: <T = unknown>(json: string, defaultValue?: T): T | undefined => {
    try {
      return JSON.parse(json);
    } catch {
      return defaultValue;
    }
  },

  // Safe JSON stringify
  safeJsonStringify: (obj: unknown, space?: number): string => {
    try {
      return JSON.stringify(obj, null, space);
    } catch {
      return '';
    }
  },

  // Check if value is empty
  isEmpty: (value: unknown): boolean => {
    if (value == null) return true;
    if (typeof value === 'string') return value.trim().length === 0;
    if (Array.isArray(value)) return value.length === 0;
    if (typeof value === 'object') return Object.keys(value).length === 0;
    return false;
  },

  // Get nested object property safely
  get: (obj: unknown, path: string, defaultValue?: unknown): unknown => {
    const keys = path.split('.');
    let result = obj;
    
    for (const key of keys) {
      if (result == null || typeof result !== 'object') {
        return defaultValue;
      }
      const resultObj = result as Record<string, unknown>;
      result = resultObj[key];
    }
    
    return result !== undefined ? result : defaultValue;
  },

  // Set nested object property
  set: (obj: Record<string, unknown>, path: string, value: unknown): void => {
    const keys = path.split('.');
    let current = obj;
    
    for (let i = 0; i < keys.length - 1; i++) {
      const key = keys[i];
      if (!(key in current) || typeof current[key] !== 'object') {
        current[key] = {};
      }
      current = current[key] as Record<string, unknown>;
    }
    
    current[keys[keys.length - 1]] = value;
  },
};