import type { AITriageResult } from '../../../api/types/alerts';
import styles from './Alerts.module.css';

interface TriageSummaryProps {
  triage: AITriageResult;
}

export function TriageSummary({ triage }: TriageSummaryProps) {
  const confidencePercent = Math.round(triage.confidenceScore * 100);

  return (
    <div className={styles.triage}>
      <h4 className={styles.triageHeader}>AI Triage</h4>
      <div className={styles.triageGrid}>
        <div>
          <span className={styles.triageLabel}>Confidence</span>
          <span className={styles.triageValue}>{confidencePercent}%</span>
        </div>
        <div>
          <span className={styles.triageLabel}>Action</span>
          <span className={styles.triageValue}>{triage.recommendedAction}</span>
        </div>
      </div>
      <p className={styles.triageReasoning}>{triage.reasoningExcerpt}</p>
    </div>
  );
}
