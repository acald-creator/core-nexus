import type { HealthSummary } from '../../../api/types/health';
import styles from './Health.module.css';

interface HealthSummaryBarProps {
  summary: HealthSummary;
}

export function HealthSummaryBar({ summary }: HealthSummaryBarProps) {
  return (
    <div className={styles.summaryBar}>
      <span className={styles.summaryItem}>
        <span className={styles.dotHealthy} /> {summary.healthy} healthy
      </span>
      <span className={styles.summaryItem}>
        <span className={styles.dotDegraded} /> {summary.degraded} degraded
      </span>
      <span className={styles.summaryItem}>
        <span className={styles.dotOffline} /> {summary.offline} offline
      </span>
      <span className={styles.summaryItem}>
        <span className={styles.dotUnknown} /> {summary.unknown} unknown
      </span>
    </div>
  );
}
