import { fetchWithAuth } from '../api/fetchWithAuth';
import { useQuery } from '@tanstack/react-query';
import { useConfig } from '../config/ConfigContext';
import type { AlertFilters, SOCAlert } from '../api/types/alerts';

export function severityToColor(severity: string): string {
  const map: Record<string, string> = {
    critical: 'var(--color-critical)',
    high: 'var(--color-high)',
    medium: 'var(--color-medium)',
    low: 'var(--color-low)',
    informational: 'var(--color-info)',
  };
  return map[severity] || map.informational;
}

export function shouldShowSimulatedTag(alert: SOCAlert): boolean {
  return !!alert.athenaScenario;
}

export function filterAlerts(alerts: SOCAlert[], filters: AlertFilters): SOCAlert[] {
  return alerts.filter((a) => {
    if (filters.severity && filters.severity.length > 0 && !filters.severity.includes(a.severity)) return false;
    if (filters.source && a.source !== filters.source) return false;
    if (filters.timeRange) {
      const t = new Date(a.timestamp).getTime();
      const start = new Date(filters.timeRange.start).getTime();
      const end = new Date(filters.timeRange.end).getTime();
      if (t < start || t > end) return false;
    }
    return true;
  });
}

export function countUnacknowledgedCriticalHigh(alerts: SOCAlert[]): number {
  return alerts.filter(
    (a) => !a.acknowledged && (a.severity === 'critical' || a.severity === 'high'),
  ).length;
}

function hasActiveFilters(filters?: AlertFilters): boolean {
  return !!(filters?.severity?.length || filters?.source || filters?.timeRange);
}

export function useAlerts(filters?: AlertFilters) {
  const config = useConfig();

  const { data, isLoading, error } = useQuery<{ alerts: SOCAlert[]; total: number }>({
    queryKey: hasActiveFilters(filters) ? ['alerts', filters] : ['alerts', 'latest'],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.severity?.length) params.set('severity', filters.severity.join(','));
      if (filters?.source) params.set('source', filters.source);
      if (filters?.timeRange?.start) params.set('from', filters.timeRange.start);
      if (filters?.timeRange?.end) params.set('to', filters.timeRange.end);
      params.set('limit', '100');

      const response = await fetchWithAuth(`${config.apiGatewayUrl}/api/v1/alerts?${params}`);
      if (!response.ok) throw new Error(`Alerts fetch failed: ${response.status}`);
      return response.json();
    },
    refetchInterval: 30_000,
  });

  const alerts = data?.alerts || [];
  const unacknowledgedCriticalHighCount = countUnacknowledgedCriticalHigh(alerts);

  return { alerts, total: data?.total || 0, unacknowledgedCriticalHighCount, isLoading, error };
}
