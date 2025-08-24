import { useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import type { UseAuthReturn } from './types';

// Hook to use the auth context
export const useAuthContext = (): UseAuthReturn => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  
  return context;
};

export default useAuthContext;