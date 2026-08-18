import { BrowserRouter, Routes, Route } from 'react-router';

// Lazy-load panels for code splitting
import { lazy, Suspense } from 'react';
import { Spinner } from './components/common/Spinner';

const OverviewPage = lazy(() => import('./pages/OverviewPage'));
const AgentFeedPage = lazy(() => import('./pages/AgentFeedPage'));
const AlertsPage = lazy(() => import('./pages/AlertsPage'));
const ApprovalsPage = lazy(() => import('./pages/ApprovalsPage'));
const SkillsPage = lazy(() => import('./pages/SkillsPage'));
const ArtifactsPage = lazy(() => import('./pages/ArtifactsPage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));

function PageLoader() {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}>
      <Spinner size="lg" />
    </div>
  );
}

export function AppRoutes() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        <Route path="/" element={<OverviewPage />} />
        <Route path="/agent-feed" element={<AgentFeedPage />} />
        <Route path="/alerts" element={<AlertsPage />} />
        <Route path="/approvals" element={<ApprovalsPage />} />
        <Route path="/skills" element={<SkillsPage />} />
        <Route path="/artifacts" element={<ArtifactsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </Suspense>
  );
}

export function AppRouter({ children }: { children: React.ReactNode }) {
  return <BrowserRouter>{children}</BrowserRouter>;
}
