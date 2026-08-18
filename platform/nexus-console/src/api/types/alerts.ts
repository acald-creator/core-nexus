export type AlertSeverity = 'critical' | 'high' | 'medium' | 'low' | 'informational';
export type AlertSource = 'wazuh' | 'suricata';

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
  wazuhDashboardUrl?: string;
  triageResult?: AITriageResult;
}

export interface AlertFilters {
  severity?: AlertSeverity[];
  source?: AlertSource;
  timeRange?: { start: string; end: string };
}
