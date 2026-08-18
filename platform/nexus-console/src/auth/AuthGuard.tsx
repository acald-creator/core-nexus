import type { ReactNode } from 'react';
import { useAuth } from './AuthContext';
import { LoginView } from './LoginView';

export function AuthGuard({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <LoginView />;
  }

  return <>{children}</>;
}
