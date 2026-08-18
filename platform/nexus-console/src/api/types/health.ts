export type HealthStatusValue = 'healthy' | 'degraded' | 'offline' | 'unknown';

export interface HealthStatus {
  serviceId: string;
  status: HealthStatusValue;
  lastChecked: number;
  consecutiveFailures: number;
  responseTimeMs?: number;
}

export interface HealthSummary {
  healthy: number;
  degraded: number;
  offline: number;
  unknown: number;
}
