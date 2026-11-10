import { Link } from 'react-router';
import { useApprovals } from '../../hooks/useApprovals';
import { timeAgo } from '../../utils/formatters';
import styles from './ApprovalDock.module.css';

/**
 * Persistent approval gate. Mounted in the app shell OUTSIDE the router, so a
 * pending agent-action decision is visible and answerable on every route —
 * never hidden behind the Approvals tab.
 *
 * Three states:
 *  - idle   — no pending decisions; a quiet one-line bar.
 *  - pending — decisions waiting; the oldest is pinned with inline approve/reject.
 *  - halted  — a pending OPAR agent action is holding the autonomous loop.
 *
 * NOTE: `halted` is inferred here (a non-factory pending action = the loop is
 * waiting on a human). Once the backend sets an explicit halted/needs_review
 * flag on the action (see issue #21), key off that field instead of `source`.
 */
export function ApprovalDock() {
  const { pending, approve, reject, isSubmitting } = useApprovals();

  const next = pending[0];
  if (!next) {
    return (
      <div className={styles.dock} data-state="idle" role="status">
        <span className={styles.dot} aria-hidden="true" />
        <span>No pending approvals</span>
      </div>
    );
  }

  const count = pending.length;
  const halted = pending.some((a) => a.source !== 'factory');

  return (
    <div
      className={styles.dock}
      data-state={halted ? 'halted' : 'pending'}
      role="region"
      aria-label="Pending approvals"
    >
      <div className={styles.status}>
        <span className={styles.dot} aria-hidden="true" />
        <span className={styles.statusLabel}>
          {halted ? 'Loop halted — awaiting review' : `${count} pending`}
        </span>
        {halted && <span className={styles.count}>{count}</span>}
      </div>

      <div className={styles.decision}>
        <span className={styles.tool}>{next.proposedTool}</span>
        <span className={styles.sep}>on</span>
        <span className={styles.target}>{next.target}</span>
        <span className={styles.meta}>
          {next.sessionId.slice(0, 8)} · {timeAgo(next.submittedAt)}
        </span>
      </div>

      <div className={styles.actions}>
        <button
          className={styles.approve}
          onClick={() => approve(next.id)}
          disabled={isSubmitting}
          aria-label={`Approve ${next.proposedTool} on ${next.target}`}
        >
          Approve
        </button>
        <button
          className={styles.reject}
          onClick={() => reject(next.id)}
          disabled={isSubmitting}
          aria-label={`Reject ${next.proposedTool} on ${next.target}`}
        >
          Reject
        </button>
        {count > 1 && (
          <Link className={styles.viewAll} to="/approvals">
            +{count - 1} more
          </Link>
        )}
      </div>
    </div>
  );
}
