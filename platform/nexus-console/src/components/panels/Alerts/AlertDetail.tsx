import type { SOCAlert } from '../../../api/types/alerts';
import { TriageSummary } from './TriageSummary';
import styles from './Alerts.module.css';

interface AlertDetailProps {
  alert: SOCAlert;
}

export function AlertDetail({ alert }: AlertDetailProps) {
  return (
    <tr>
      <td colSpan={5} className={styles.detailCell}>
        <div className={styles.detail}>
          {alert.triageResult ? (
            <TriageSummary triage={alert.triageResult} />
          ) : (
            <p className={styles.noTriage}>No AI triage available</p>
          )}

          {alert.wazuhDashboardUrl && (
            <a
              href={alert.wazuhDashboardUrl}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.wazuhLink}
            >
              Open in Wazuh Dashboard →
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
