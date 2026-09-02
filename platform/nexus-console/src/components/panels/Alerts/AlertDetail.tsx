import type { SOCAlert } from '../../../api/types/alerts';
import { TriageSummary } from './TriageSummary';
import styles from './Alerts.module.css';

interface AlertDetailProps {
  alert: SOCAlert;
}

export function AlertDetail({ alert }: AlertDetailProps) {
  const dashboardUrl = alert.externalDashboardUrl || alert.wazuhDashboardUrl;

  return (
    <tr>
      <td colSpan={5} className={styles.detailCell}>
        <div className={styles.detail}>
          {alert.athenaScenario && (
            <p className={styles.scenarioLine}>
              <span className={styles.triageLabel}>Athena scenario</span>{' '}
              <code className={styles.scenarioId}>{alert.athenaScenario}</code>
            </p>
          )}

          {alert.triageResult ? (
            <TriageSummary triage={alert.triageResult} />
          ) : (
            <p className={styles.noTriage}>No AI triage available</p>
          )}

          {dashboardUrl && (
            <a
              href={dashboardUrl}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.externalLink}
            >
              Open external SIEM dashboard →
            </a>
          )}

          <details className={styles.payloadToggle}>
            <summary>Raw payload</summary>
            <pre className={styles.payload}>{JSON.stringify(alert.payload, null, 2)}</pre>
          </details>
        </div>
      </td>
    </tr>
  );
}
