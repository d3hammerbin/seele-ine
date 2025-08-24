// Theme hook
import { useState, useEffect, useCallback } from 'react';
import type { UseThemeReturn, Theme, ThemeMode } from './types';

const THEME_STORAGE_KEY = 'seele-ine-theme';
const THEME_MODE_STORAGE_KEY = 'seele-ine-theme-mode';

// Default themes
const defaultThemes: Record<string, Theme> = {
  light: {
    id: 'light',
    name: 'Light',
    mode: 'light',
    colors: {
      primary: '#3b82f6',
      secondary: '#64748b',
      accent: '#ff6b6b',
      background: '#ffffff',
      surface: '#f8fafc',
      text: '#1e293b',
      textSecondary: '#64748b',
      border: '#e2e8f0',
      error: '#ef4444',
      warning: '#f59e0b',
      success: '#10b981',
      info: '#3b82f6',
    },
    spacing: {
      xs: '0.25rem',
      sm: '0.5rem',
      md: '1rem',
      lg: '1.5rem',
      xl: '2rem',
      '2xl': '3rem',
    },
    typography: {
      fontFamily: 'Inter, system-ui, sans-serif',
      fontSize: {
        xs: '0.75rem',
        sm: '0.875rem',
        base: '1rem',
        lg: '1.125rem',
        xl: '1.25rem',
        '2xl': '1.5rem',
        '3xl': '1.875rem',
      },
      fontWeight: {
        normal: '400',
        medium: '500',
        semibold: '600',
        bold: '700',
      },
      lineHeight: {
        tight: '1.25',
        normal: '1.5',
        relaxed: '1.75',
      },
    },
    borderRadius: {
      none: '0',
      sm: '0.125rem',
      md: '0.375rem',
      lg: '0.5rem',
      xl: '0.75rem',
      full: '9999px',
    },
    shadows: {
      sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
      md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
      lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
      xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
    },
  },
  dark: {
    id: 'dark',
    name: 'Dark',
    mode: 'dark',
    colors: {
      primary: '#58a6ff',
      secondary: '#8b949e',
      accent: '#ff4757',
      background: '#0d1117',
      surface: '#21262d',
      text: '#f0f6fc',
      textSecondary: '#8b949e',
      border: '#30363d',
      error: '#f85149',
      warning: '#d29922',
      success: '#3fb950',
      info: '#58a6ff',
    },
    spacing: {
      xs: '0.25rem',
      sm: '0.5rem',
      md: '1rem',
      lg: '1.5rem',
      xl: '2rem',
      '2xl': '3rem',
    },
    typography: {
      fontFamily: 'Inter, system-ui, sans-serif',
      fontSize: {
        xs: '0.75rem',
        sm: '0.875rem',
        base: '1rem',
        lg: '1.125rem',
        xl: '1.25rem',
        '2xl': '1.5rem',
        '3xl': '1.875rem',
      },
      fontWeight: {
        normal: '400',
        medium: '500',
        semibold: '600',
        bold: '700',
      },
      lineHeight: {
        tight: '1.25',
        normal: '1.5',
        relaxed: '1.75',
      },
    },
    borderRadius: {
      none: '0',
      sm: '0.125rem',
      md: '0.375rem',
      lg: '0.5rem',
      xl: '0.75rem',
      full: '9999px',
    },
    shadows: {
      sm: '0 1px 2px 0 rgb(0 0 0 / 0.3)',
      md: '0 4px 6px -1px rgb(0 0 0 / 0.3), 0 2px 4px -2px rgb(0 0 0 / 0.3)',
      lg: '0 10px 15px -3px rgb(0 0 0 / 0.3), 0 4px 6px -4px rgb(0 0 0 / 0.3)',
      xl: '0 20px 25px -5px rgb(0 0 0 / 0.3), 0 8px 10px -6px rgb(0 0 0 / 0.3)',
    },
  },
};

// Detect system theme preference
const getSystemTheme = (): ThemeMode => {
  if (typeof window === 'undefined') return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
};

// Get stored theme preference
const getStoredTheme = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(THEME_STORAGE_KEY);
};

// Get stored theme mode preference
const getStoredThemeMode = (): ThemeMode | null => {
  if (typeof window === 'undefined') return null;
  const stored = localStorage.getItem(THEME_MODE_STORAGE_KEY);
  if (stored === 'light' || stored === 'dark' || stored === 'system') {
    return stored;
  }
  return null;
};

// Apply theme to document
const applyThemeToDocument = (theme: Theme): void => {
  if (typeof document === 'undefined') return;

  const root = document.documentElement;
  
  // Apply CSS custom properties
  Object.entries(theme.colors).forEach(([key, value]) => {
    root.style.setProperty(`--color-${key}`, value);
  });

  Object.entries(theme.spacing).forEach(([key, value]) => {
    root.style.setProperty(`--spacing-${key}`, value);
  });

  Object.entries(theme.typography.fontSize).forEach(([key, value]) => {
    root.style.setProperty(`--font-size-${key}`, value);
  });

  Object.entries(theme.typography.fontWeight).forEach(([key, value]) => {
    root.style.setProperty(`--font-weight-${key}`, value);
  });

  Object.entries(theme.typography.lineHeight).forEach(([key, value]) => {
    root.style.setProperty(`--line-height-${key}`, value);
  });

  Object.entries(theme.borderRadius).forEach(([key, value]) => {
    root.style.setProperty(`--border-radius-${key}`, value);
  });

  Object.entries(theme.shadows).forEach(([key, value]) => {
    root.style.setProperty(`--shadow-${key}`, value);
  });

  // Set font family
  root.style.setProperty('--font-family', theme.typography.fontFamily);

  // Set theme mode class
  root.classList.remove('light', 'dark');
  root.classList.add(theme.mode);

  // Set data attribute for CSS selectors
  root.setAttribute('data-theme', theme.id);
  root.setAttribute('data-theme-mode', theme.mode);
};

const useTheme = (): UseThemeReturn => {
  const [themes, setThemes] = useState<Record<string, Theme>>(defaultThemes);
  const [currentThemeId, setCurrentThemeId] = useState<string>(() => {
    const stored = getStoredTheme();
    if (stored && defaultThemes[stored]) {
      return stored;
    }
    const systemMode = getSystemTheme();
    return systemMode;
  });
  const [themeMode, setThemeMode] = useState<ThemeMode>(() => {
    return getStoredThemeMode() || 'system';
  });

  const currentTheme = themes[currentThemeId] || themes.light;

  // Get effective theme based on mode
  const getEffectiveTheme = useCallback((): Theme => {
    if (themeMode === 'system') {
      const systemMode = getSystemTheme();
      return themes[systemMode] || themes.light;
    }
    return themes[themeMode] || themes.light;
  }, [themes, themeMode]);

  // Set theme
  const setTheme = useCallback((themeId: string): void => {
    if (themes[themeId]) {
      setCurrentThemeId(themeId);
      localStorage.setItem(THEME_STORAGE_KEY, themeId);
    }
  }, [themes]);

  // Set theme mode
  const setMode = useCallback((mode: ThemeMode): void => {
    setThemeMode(mode);
    localStorage.setItem(THEME_MODE_STORAGE_KEY, mode);
    
    if (mode === 'system') {
      const systemMode = getSystemTheme();
      setCurrentThemeId(systemMode);
    } else {
      setCurrentThemeId(mode);
    }
  }, []);

  // Toggle between light and dark
  const toggleTheme = useCallback((): void => {
    const newMode = currentTheme.mode === 'light' ? 'dark' : 'light';
    setMode(newMode);
  }, [currentTheme.mode, setMode]);

  // Add custom theme
  const addTheme = useCallback((theme: Theme): void => {
    setThemes(prev => ({
      ...prev,
      [theme.id]: theme,
    }));
  }, []);

  // Remove custom theme
  const removeTheme = useCallback((themeId: string): void => {
    if (themeId === 'light' || themeId === 'dark') {
      console.warn('Cannot remove default themes');
      return;
    }

    setThemes(prev => {
      const { [themeId]: removed, ...rest } = prev;
      void removed; // Acknowledge the removed theme
      return rest;
    });

    // Switch to default theme if current theme is removed
    if (currentThemeId === themeId) {
      setTheme('light');
    }
  }, [currentThemeId, setTheme]);

  // Get theme by ID
  const getTheme = useCallback((themeId: string): Theme | undefined => {
    return themes[themeId];
  }, [themes]);

  // Get all available themes
  const getAvailableThemes = useCallback((): Theme[] => {
    return Object.values(themes);
  }, [themes]);

  // Check if dark mode
  const isDark = currentTheme.mode === 'dark';

  // Apply theme to document when theme changes
  useEffect(() => {
    const effectiveTheme = getEffectiveTheme();
    applyThemeToDocument(effectiveTheme);
  }, [getEffectiveTheme]);

  // Listen for system theme changes
  useEffect(() => {
    if (themeMode !== 'system') return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      const systemMode = e.matches ? 'dark' : 'light';
      setCurrentThemeId(systemMode);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [themeMode]);

  return {
    currentTheme,
    themes: getAvailableThemes(),
    themeMode,
    mode: themeMode,
    isDark,
    setTheme,
    setMode,
    toggleTheme,
    addTheme,
    removeTheme,
    getTheme,
  };
};

// Theme utilities
export const themeUtils = {
  // Create a custom theme based on an existing theme
  createCustomTheme: (baseTheme: Theme, overrides: Partial<Theme>): Theme => {
    return {
      ...baseTheme,
      ...overrides,
      colors: {
        ...baseTheme.colors,
        ...overrides.colors,
      },
      spacing: {
        ...baseTheme.spacing,
        ...overrides.spacing,
      },
      typography: {
        ...baseTheme.typography,
        ...overrides.typography,
        fontSize: {
          ...baseTheme.typography.fontSize,
          ...overrides.typography?.fontSize,
        },
        fontWeight: {
          ...baseTheme.typography.fontWeight,
          ...overrides.typography?.fontWeight,
        },
        lineHeight: {
          ...baseTheme.typography.lineHeight,
          ...overrides.typography?.lineHeight,
        },
      },
      borderRadius: {
        ...baseTheme.borderRadius,
        ...overrides.borderRadius,
      },
      shadows: {
        ...baseTheme.shadows,
        ...overrides.shadows,
      },
    };
  },

  // Generate CSS variables from theme
  generateCSSVariables: (theme: Theme): string => {
    const variables: string[] = [];

    Object.entries(theme.colors).forEach(([key, value]) => {
      variables.push(`--color-${key}: ${value};`);
    });

    Object.entries(theme.spacing).forEach(([key, value]) => {
      variables.push(`--spacing-${key}: ${value};`);
    });

    Object.entries(theme.typography.fontSize).forEach(([key, value]) => {
      variables.push(`--font-size-${key}: ${value};`);
    });

    Object.entries(theme.typography.fontWeight).forEach(([key, value]) => {
      variables.push(`--font-weight-${key}: ${value};`);
    });

    Object.entries(theme.typography.lineHeight).forEach(([key, value]) => {
      variables.push(`--line-height-${key}: ${value};`);
    });

    Object.entries(theme.borderRadius).forEach(([key, value]) => {
      variables.push(`--border-radius-${key}: ${value};`);
    });

    Object.entries(theme.shadows).forEach(([key, value]) => {
      variables.push(`--shadow-${key}: ${value};`);
    });

    variables.push(`--font-family: ${theme.typography.fontFamily};`);

    return `:root {\n  ${variables.join('\n  ')}\n}`;
  },

  // Get color with opacity
  getColorWithOpacity: (color: string, opacity: number): string => {
    // Simple implementation for hex colors
    if (color.startsWith('#')) {
      const hex = color.slice(1);
      const r = parseInt(hex.slice(0, 2), 16);
      const g = parseInt(hex.slice(2, 4), 16);
      const b = parseInt(hex.slice(4, 6), 16);
      return `rgba(${r}, ${g}, ${b}, ${opacity})`;
    }
    return color;
  },

  // Validate theme structure
  validateTheme: (theme: Partial<Theme>): boolean => {
    const requiredFields = ['id', 'name', 'mode', 'colors'];
    return requiredFields.every(field => field in theme);
  },
};

export default useTheme;