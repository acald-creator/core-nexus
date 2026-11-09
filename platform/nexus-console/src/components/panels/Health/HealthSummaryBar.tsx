import type { HealthSummary } from '../../../api/types/health';
import { StatusDot } from '../../common/StatusDot';
import styles from './Health.module.css';

interface HealthSummaryBarProps {
  summary: HealthSummary;
}

export function HealthSummaryBar({ summary }: HealthSummaryBarProps) {
  return (
    <div className={styles.summaryBar}>
      <span className={styles.summaryItem}>
        <StatusDot status="healthy" /> {summary.healthy} healthy
      </span>
      <span className={styles.summaryItem}>
        <StatusDot status="degraded" /> {summary.degraded} degraded
      </span>
      <span className={styles.summaryItem}>
        <StatusDot status="offline" /> {summary.offline} offline
      </span>
      <span className={styles.summaryItem}>
        <StatusDot status="unknown" /> {summary.unknown} unknown
      </span>
    </div>
  );
}
