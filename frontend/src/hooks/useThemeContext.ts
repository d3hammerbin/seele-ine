import { useContext } from 'react';
import { ThemeContext } from '../contexts/ThemeContext';
import type { UseThemeReturn } from './types';

export const useThemeContext = (): UseThemeReturn => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useThemeContext must be used within a ThemeProvider');
  }
  return context;
};

export default useThemeContext;