import type { ReactNode } from 'react';
import { useAuth } from './AuthContext';
import { LoginView } from './LoginView';

const DEV_BYPASS = import.meta.env.VITE_DEV_AUTH_BYPASS === 'true';

export function AuthGuard({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();

  if (DEV_BYPASS) {
    return <>{children}</>;
  }

  if (!isAuthenticated) {
    return <LoginView />;
  }

  return <>{children}</>;
}
