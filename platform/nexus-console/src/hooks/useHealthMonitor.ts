import { fetchWithAuth } from '../api/fetchWithAuth';
import { useQuery } from '@tanstack/react-query';
import { useConfig } from '../config/ConfigContext';
import type { HealthStatus, HealthStatusValue, HealthSummary } from '../api/types/health';

export function deriveHealthStatus(consecutiveFailures: number, hasEndpoint: boolean): HealthStatusValue {
  if (!hasEndpoint) return 'unknown';
  if (consecutiveFailures === 0) return 'healthy';
  if (consecutiveFailures <= 2) return 'degraded';
  return 'offline';
}

export function computeHealthSummary(statuses: HealthStatus[]): HealthSummary {
  const summary: HealthSummary = { healthy: 0, degraded: 0, offline: 0, unknown: 0 };
  for (const s of statuses) {
    summary[s.status]++;
  }
  return summary;
}

export function useHealthMonitor() {
  const config = useConfig();

  const { data: statuses = [] } = useQuery<HealthStatus[]>({
    queryKey: ['health-status'],
    queryFn: async () => {
      const results: HealthStatus[] = [];
      for (const service of config.services) {
        if (!service.healthEndpoint) {
          results.push({
            serviceId: service.id,
            status: 'unknown',
            lastChecked: Date.now(),
            consecutiveFailures: 0,
          });
          continue;
        }

        try {
          const start = performance.now();
          const controller = new AbortController();
          const timeout = setTimeout(() => controller.abort(), 5000);

          const response = await fetchWithAuth(
            `${config.apiGatewayUrl}/api/v1/health/${service.id}`,
            { signal: controller.signal }
          );
          clearTimeout(timeout);

          const elapsed = performance.now() - start;
          const isHealthy = response.ok;

          results.push({
            serviceId: service.id,
            status: isHealthy ? 'healthy' : 'degraded',
            lastChecked: Date.now(),
            consecutiveFailures: isHealthy ? 0 : 1,
            responseTimeMs: elapsed,
          });
        } catch {
          results.push({
            serviceId: service.id,
            status: 'offline',
            lastChecked: Date.now(),
            consecutiveFailures: 3,
          });
        }
      }
      return results;
    },
    refetchInterval: config.healthPollIntervalMs,
  });

  const summary = computeHealthSummary(statuses);
  const statusMap = new Map(statuses.map((s) => [s.serviceId, s]));

  return { statuses, summary, statusMap };
}
