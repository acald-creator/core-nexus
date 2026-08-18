import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider } from './config/ConfigContext';
import { AuthProvider } from './auth/AuthContext';
import { AuthGuard } from './auth/AuthGuard';
import { AppRouter, AppRoutes } from './routes';
import { DashboardLayout } from './components/Layout/DashboardLayout';
import { Sidebar } from './components/Sidebar/Sidebar';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 3,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  return (
    <ConfigProvider>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <AuthGuard>
            <AppRouter>
              <DashboardLayout sidebar={<Sidebar />}>
                <AppRoutes />
              </DashboardLayout>
            </AppRouter>
          </AuthGuard>
        </AuthProvider>
      </QueryClientProvider>
    </ConfigProvider>
  );
}
