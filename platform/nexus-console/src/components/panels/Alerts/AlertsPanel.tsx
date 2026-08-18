import { useState } from 'react';
import { useAlerts } from '../../../hooks/useAlerts';
import { AlertRow } from './AlertRow';
import { AlertDetail } from './AlertDetail';
import { Spinner } from '../../common/Spinner';
import { ErrorBanner } from '../../common/ErrorBanner';
import type { AlertFilters, AlertSeverity, AlertSource } from '../../../api/types/alerts';
import styles from './Alerts.module.css';

export function AlertsPanel() {
  const [filters, setFilters] = useState<AlertFilters>({});
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { alerts, isLoading, error } = useAlerts(filters);

  const selectedAlert = alerts.find((a) => a.id === selectedId);

  return (
    <div className={styles.panel}>
      <h2>Security Alerts</h2>

      {error && <ErrorBanner message="Failed to load alerts" />}

      <div className={styles.filters}>
        <select
          value={filters.severity?.join(',') || ''}
          onChange={(e) => {
            const val = e.target.value;
            setFilters({ ...filters, severity: val ? val.split(',') as AlertSeverity[] : undefined });
          }}
          aria-label="Filter by severity"
        >
          <option value="">All severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
          <option value="informational">Info</option>
        </select>

        <select
          value={filters.source || ''}
          onChange={(e) => setFilters({ ...filters, source: (e.target.value || undefined) as AlertSource | undefined })}
          aria-label="Filter by source"
        >
          <option value="">All sources</option>
          <option value="wazuh">Wazuh</option>
          <option value="suricata">Suricata</option>
        </select>
      </div>

      {isLoading ? (
        <Spinner size="lg" />
      ) : (
        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Time</th>
                <th>Severity</th>
                <th>Source</th>
                <th>Rule</th>
                <th>Host</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map((alert) => (
                <>
                  <AlertRow
                    key={alert.id}
                    alert={alert}
                    selected={selectedId === alert.id}
                    onSelect={() => setSelectedId(selectedId === alert.id ? null : alert.id)}
                  />
                  {selectedId === alert.id && selectedAlert && (
                    <AlertDetail key={`${alert.id}-detail`} alert={selectedAlert} />
                  )}
                </>
              ))}
            </tbody>
          </table>
          {alerts.length === 0 && <p className={styles.empty}>No alerts match current filters</p>}
        </div>
      )}
    </div>
  );
}
