import { useApprovals } from '../../../hooks/useApprovals';
import { ApprovalCard } from './ApprovalCard';
import { ErrorBanner } from '../../common/ErrorBanner';
import { Spinner } from '../../common/Spinner';
import styles from './Approvals.module.css';

export function ApprovalsPanel() {
  const { pending, isLoading, approve, reject, isSubmitting, submitError } = useApprovals();

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <h2>Approval Queue</h2>
        <span className={styles.count}>{pending.length} pending</span>
      </div>

      {submitError && <ErrorBanner message="Failed to submit decision — action retained for retry" />}

      {isLoading ? (
        <Spinner size="lg" />
      ) : pending.length === 0 ? (
        <div className={styles.empty}>
          <p>No pending approvals</p>
          <p className={styles.emptyHint}>Actions flagged `needs_review` by the OPAR agent will appear here.</p>
        </div>
      ) : (
        <div className={styles.list}>
          {pending.map((action) => (
            <ApprovalCard
              key={action.id}
              action={action}
              onApprove={() => approve(action.id)}
              onReject={() => reject(action.id)}
              isSubmitting={isSubmitting}
            />
          ))}
        </div>
      )}
    </div>
  );
}
