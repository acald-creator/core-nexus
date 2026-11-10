import { NavLink } from 'react-router';
import { timeAgo } from '../../../utils/formatters';
import type { SessionSummary } from './sessions';
import styles from './Runs.module.css';

interface SessionSpineProps {
  sessions: SessionSummary[];
  isConnected: boolean;
  /** The live feed is at its retention cap, so older runs may be missing. */
  feedAtCap?: boolean;
}

const PHASE_CLASS: Record<string, string> = {
  observe: styles.phaseObserve,
  plan: styles.phasePlan,
  act: styles.phaseAct,
  reflect: styles.phaseReflect,
};

/** The run spine: one row per OPAR session, newest/live first, linking to its detail. */
export function SessionSpine({ sessions, isConnected, feedAtCap = false }: SessionSpineProps) {
  return (
    <nav className={styles.spine} aria-label="Agent runs">
      <div className={styles.spineHeader}>
        <span className={styles.spineTitle}>Runs</span>
        <span
          className={isConnected ? styles.live : styles.offline}
          title={isConnected ? 'Feed connected' : 'Feed disconnected'}
        >
          {isConnected ? 'live' : 'offline'}
        </span>
      </div>

      {sessions.length === 0 ? (
        <p className={styles.spineEmpty}>
          No agent runs yet. Sessions appear here as OPAR agents emit events.
        </p>
      ) : (
        <ul className={styles.spineList}>
          {sessions.map((s) => (
            <li key={s.sessionId}>
              <NavLink
                to={`/runs/${encodeURIComponent(s.sessionId)}`}
                className={({ isActive }) =>
                  `${styles.spineItem} ${isActive ? styles.spineItemActive : ''}`
                }
              >
                <span
                  className={`${styles.phaseDot} ${PHASE_CLASS[s.latestPhase] ?? ''}`}
                  aria-hidden="true"
                />
                <span className={styles.spineBody}>
                  <span className={styles.spineTarget}>{s.target}</span>
                  <span className={styles.spineMeta}>
                    <span className={styles.spineId}>{s.sessionId.slice(0, 8)}</span>
                    <span>{s.eventCount} events</span>
                    <span>{timeAgo(s.lastAt)}</span>
                  </span>
                </span>
                {s.live && <span className={styles.liveDot} aria-label="live" title="live" />}
              </NavLink>
            </li>
          ))}
        </ul>
      )}

      {feedAtCap && (
        <p className={styles.spineNote}>
          Showing the latest 500 events — older runs may not appear.
        </p>
      )}
    </nav>
  );
}
