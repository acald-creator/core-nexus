import type { ApprovalAction } from '../../../api/types/approvals';
import { timeAgo } from '../../../utils/formatters';
import styles from './Approvals.module.css';

interface ApprovalCardProps {
  action: ApprovalAction;
  onApprove: () => void;
  onReject: () => void;
  isSubmitting: boolean;
}

export function ApprovalCard({ action, onApprove, onReject, isSubmitting }: ApprovalCardProps) {
  const isFactory = action.source === 'factory';

  return (
    <div className={styles.card}>
      <div className={styles.cardHeader}>
        <span className={styles.tool}>{action.proposedTool}</span>
        <span className={styles.time}>{timeAgo(action.submittedAt)}</span>
      </div>

      <div className={styles.cardBody}>
        {isFactory && (
          <div className={styles.field}>
            <span className={styles.label}>Source</span>
            <span className={styles.value}>
              Factory review
              {action.riskMax != null && action.riskMax !== '' ? ` · risk ${action.riskMax}` : ''}
            </span>
          </div>
        )}
        <div className={styles.field}>
          <span className={styles.label}>Target</span>
          <span className={styles.value}>{action.target}</span>
        </div>
        <div className={styles.field}>
          <span className={styles.label}>Action</span>
          <span className={styles.value}>{action.argumentsSummary}</span>
        </div>
        <div className={styles.field}>
          <span className={styles.label}>Session</span>
          <span className={styles.valueMono}>{action.sessionId.slice(0, 12)}</span>
        </div>
        {action.checkRunUrl && (
          <div className={styles.field}>
            <span className={styles.label}>Check run</span>
            <a
              className={styles.value}
              href={action.checkRunUrl}
              target="_blank"
              rel="noopener noreferrer"
            >
              Open on GitHub →
            </a>
          </div>
        )}
      </div>

      <div className={styles.cardActions}>
        <button
          className={styles.approveBtn}
          onClick={onApprove}
          disabled={isSubmitting}
          aria-label={`Approve ${action.proposedTool} on ${action.target}`}
        >
          ✓ Approve
        </button>
        <button
          className={styles.rejectBtn}
          onClick={onReject}
          disabled={isSubmitting}
          aria-label={`Reject ${action.proposedTool} on ${action.target}`}
        >
          ✗ Reject
        </button>
      </div>
    </div>
  );
}
