import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from 'react';
import type { AuthState, LoginCredentials } from '../api/types/auth';
import { useConfig } from '../config/ConfigContext';

const AuthContext = createContext<AuthState>({
  token: null,
  isAuthenticated: false,
  login: async () => {},
  logout: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const config = useConfig();
  const tokenRef = useRef<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const login = useCallback(async (credentials: LoginCredentials) => {
    const response = await fetch(`${config.apiGatewayUrl}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      throw new Error('Authentication failed');
    }

    const data = await response.json();
    tokenRef.current = data.token;
    setIsAuthenticated(true);
  }, [config.apiGatewayUrl]);

  const logout = useCallback(() => {
    tokenRef.current = null;
    setIsAuthenticated(false);
  }, []);

  const state: AuthState = {
    token: tokenRef.current,
    isAuthenticated,
    login,
    logout,
  };

  return (
    <AuthContext.Provider value={state}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  return useContext(AuthContext);
}

export function useToken(): () => string | null {
  const { token } = useContext(AuthContext);
  const tokenRef = useRef(token);
  tokenRef.current = token;
  return () => tokenRef.current;
}
