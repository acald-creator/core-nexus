import { severityToColor } from '../../../hooks/useAlerts';
import { formatTimestamp } from '../../../utils/formatters';
import { placeMarks } from './ribbon';
import type { RunWindow } from './correlation';
import type { OPAREvent } from '../../../api/types/opar-events';
import type { SOCAlert } from '../../../api/types/alerts';
import styles from './Runs.module.css';

interface RunRibbonProps {
  /** This run's agent events; only `act`-phase events become red marks. */
  events: OPAREvent[];
  /** SOC alerts already correlated to this run. */
  alerts: SOCAlert[];
  /** The padded run window shared with correlation, or null when unknown. */
  window: RunWindow | null;
}

/**
 * A shared time axis for the run: agent acts (red, above the line) over SOC
 * detections (blue, below), both placed by wall-clock time across the same
 * window. It shows *temporal* alignment — which actions a detection sits near —
 * not a causal link, since alerts carry no session id (see correlation.ts).
 */
export function RunRibbon({ events, alerts, window }: RunRibbonProps) {
  if (!window) return null;

  const acts = events.filter((e) => e.phase === 'act');
  const redMarks = placeMarks(acts, window);
  const blueMarks = placeMarks(alerts, window);

  if (redMarks.length === 0 && blueMarks.length === 0) return null;

  return (
    <div
      className={styles.ribbon}
      role="img"
      aria-label={`Timeline: ${acts.length} agent acts and ${alerts.length} alerts over this run`}
    >
      <div className={styles.ribbonTrack}>
        <div className={styles.ribbonRow}>
          {redMarks.map((m) => (
            <span
              key={m.id}
              className={`${styles.ribbonMark} ${styles.ribbonMarkRed}`}
              style={{ insetInlineStart: `${m.pct}%` }}
              title={`Act · ${formatTimestamp(m.timestamp)}`}
            />
          ))}
        </div>
        <div className={styles.ribbonAxis} aria-hidden="true" />
        <div className={styles.ribbonRow}>
          {blueMarks.map((m) => (
            <span
              key={m.id}
              className={`${styles.ribbonMark} ${styles.ribbonMarkBlue}`}
              style={{
                insetInlineStart: `${m.pct}%`,
                background: severityToColor(m.item.severity),
              }}
              title={`${m.item.ruleName} · ${formatTimestamp(m.timestamp)}`}
            />
          ))}
        </div>
      </div>
      <div className={styles.ribbonScale} aria-hidden="true">
        <span>{formatTimestamp(new Date(window.start).toISOString())}</span>
        <span>{formatTimestamp(new Date(window.end).toISOString())}</span>
      </div>
    </div>
  );
}
