import React, { createContext, useMemo, type ReactNode } from 'react';
import useAuth from '../hooks/useAuth';
import type { UseAuthReturn } from '../hooks/types';

// Create the context
const AuthContext = createContext<UseAuthReturn | undefined>(undefined);

// AuthProvider component
export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const auth = useAuth();
  
  // Memoize the auth value to prevent unnecessary re-renders
  const authValue = useMemo(() => auth, [
    auth.user,
    auth.isAuthenticated,
    auth.isLoading,
    auth.error,
    auth.login,
    auth.logout,
    auth.register,
    auth.refreshToken,
    auth.updateProfile,
    auth.changePassword
  ]);
  
  return (
    <AuthContext.Provider value={authValue}>
      {children}
    </AuthContext.Provider>
  );
};

// Export the context for use in the hook
export { AuthContext };

export default AuthProvider;