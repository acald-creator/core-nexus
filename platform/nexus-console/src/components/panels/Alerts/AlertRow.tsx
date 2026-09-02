import type { SOCAlert } from '../../../api/types/alerts';
import { formatTimestamp } from '../../../utils/formatters';
import { severityToColor, shouldShowSimulatedTag } from '../../../hooks/useAlerts';
import styles from './Alerts.module.css';

interface AlertRowProps {
  alert: SOCAlert;
  selected: boolean;
  onSelect: () => void;
}

export function AlertRow({ alert, selected, onSelect }: AlertRowProps) {
  return (
    <tr
      className={`${styles.row} ${selected ? styles.selected : ''}`}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onSelect()}
    >
      <td className={styles.timestamp}>{formatTimestamp(alert.timestamp)}</td>
      <td>
        <span className={styles.severity} style={{ color: severityToColor(alert.severity) }}>
          {alert.severity}
        </span>
      </td>
      <td className={styles.source}>{alert.source}</td>
      <td className={styles.ruleName}>
        {alert.ruleName}
        {shouldShowSimulatedTag(alert) && (
          <span
            className={styles.simulatedTag}
            title={alert.athenaScenario ? `Athena scenario: ${alert.athenaScenario}` : 'Athena-labeled'}
          >
            {alert.athenaScenario
              ? `Athena · ${alert.athenaScenario.length > 24 ? `${alert.athenaScenario.slice(0, 24)}…` : alert.athenaScenario}`
              : 'Simulated'}
          </span>
        )}
      </td>
      <td className={styles.host}>{alert.affectedHost}</td>
    </tr>
  );
}
