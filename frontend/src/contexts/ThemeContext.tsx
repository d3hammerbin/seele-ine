import React, { createContext, type ReactNode } from 'react';
import useTheme from '../hooks/useTheme';
import type { UseThemeReturn } from '../hooks/types';

const ThemeContext = createContext<UseThemeReturn | undefined>(undefined);

export interface ThemeProviderProps {
  children: ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const themeValue = useTheme();

  return (
    <ThemeContext.Provider value={themeValue}>
      {children}
    </ThemeContext.Provider>
  );
};

// Export the context for use in the hook
export { ThemeContext };

export default ThemeProvider;