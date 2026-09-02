export type AlertSeverity = 'critical' | 'high' | 'medium' | 'low' | 'informational';

/** Sensor / SIEM origin for Console filters (ADR 0011 hybrid + Wazuh full-SIEM). */
export type AlertSource =
  | 'wazuh'
  | 'suricata'
  | 'zeek'
  | 'falco'
  | 'tetragon'
  | 'ai-inference'
  | 'vector';

export interface AITriageResult {
  confidenceScore: number;
  recommendedAction: string;
  reasoningExcerpt: string;
}

export interface SOCAlert {
  id: string;
  timestamp: string;
  severity: AlertSeverity;
  source: AlertSource;
  ruleName: string;
  affectedHost: string;
  acknowledged: boolean;
  athenaScenario?: string;
  payload: Record<string, unknown>;
  /** Optional deep-link when a SIEM dashboard is deployed (full Wazuh path). */
  externalDashboardUrl?: string;
  /** @deprecated Prefer externalDashboardUrl */
  wazuhDashboardUrl?: string;
  triageResult?: AITriageResult;
}

export interface AlertFilters {
  severity?: AlertSeverity[];
  source?: AlertSource;
  timeRange?: { start: string; end: string };
}

export const ALERT_SOURCE_OPTIONS: { value: AlertSource; label: string }[] = [
  { value: 'suricata', label: 'Suricata' },
  { value: 'zeek', label: 'Zeek' },
  { value: 'falco', label: 'Falco' },
  { value: 'tetragon', label: 'Tetragon' },
  { value: 'ai-inference', label: 'AI triage' },
  { value: 'vector', label: 'Vector' },
  { value: 'wazuh', label: 'Wazuh' },
];
