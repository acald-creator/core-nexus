import { EventRow } from '../AgentFeed/EventRow';
import { timeAgo } from '../../../utils/formatters';
import type { OPAREvent } from '../../../api/types/opar-events';
import type { SessionSummary } from './sessions';
import styles from './Runs.module.css';

interface RunDetailProps {
  /** The selected session summary, or undefined when no run is selected. */
  session: SessionSummary | undefined;
  /** This run's events (already filtered to the session). */
  events: OPAREvent[];
}

const PHASE_CLASS: Record<string, string> = {
  observe: styles.phaseObserve,
  plan: styles.phasePlan,
  act: styles.phaseAct,
  reflect: styles.phaseReflect,
};

/** The right-hand run view: the selected session's header and its event timeline. */
export function RunDetail({ session, events }: RunDetailProps) {
  if (!session) {
    return (
      <div className={styles.detailEmpty}>
        <p>Select a run</p>
        <p className={styles.detailEmptyHint}>
          Pick a session from the spine to see its plan, act, and reflect timeline.
        </p>
      </div>
    );
  }

  const ordered = [...events].sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
  );

  return (
    <section className={styles.detail} aria-label={`Run ${session.sessionId}`}>
      <header className={styles.detailHeader}>
        <div className={styles.detailTitleRow}>
          <h2 className={styles.detailTitle}>{session.target}</h2>
          {session.live && <span className={styles.detailLive}>live</span>}
        </div>
        <div className={styles.detailMeta}>
          <span className={`${styles.phaseTag} ${PHASE_CLASS[session.latestPhase] ?? ''}`}>
            {session.latestPhase}
          </span>
          <span>{session.eventCount} events</span>
          <span>updated {timeAgo(session.lastAt)}</span>
          <span className={styles.detailId}>{session.sessionId}</span>
        </div>
      </header>

      {ordered.length === 0 ? (
        <p className={styles.detailEmptyHint}>No events for this run yet.</p>
      ) : (
        <div className={styles.timeline}>
          {ordered.map((event) => (
            <EventRow key={event.id} event={event} selected={false} onSelect={() => {}} />
          ))}
        </div>
      )}
    </section>
  );
}
