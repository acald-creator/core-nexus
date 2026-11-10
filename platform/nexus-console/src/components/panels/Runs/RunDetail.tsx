import { EventRow } from '../AgentFeed/EventRow';
import { severityToColor } from '../../../hooks/useAlerts';
import { timeAgo } from '../../../utils/formatters';
import { countActs, hostOf } from './correlation';
import type { OPAREvent } from '../../../api/types/opar-events';
import type { SOCAlert } from '../../../api/types/alerts';
import type { SessionSummary } from './sessions';
import styles from './Runs.module.css';

interface RunDetailProps {
  /** The selected session summary, or undefined when no run is selected. */
  session: SessionSummary | undefined;
  /** This run's agent events (already filtered to the session). */
  events: OPAREvent[];
  /** SOC alerts correlated to this run (host + time match; see correlation.ts). */
  alerts: SOCAlert[];
}

const PHASE_CLASS: Record<string, string> = {
  observe: styles.phaseObserve,
  plan: styles.phasePlan,
  act: styles.phaseAct,
  reflect: styles.phaseReflect,
};

function byTimeDesc<T extends { timestamp: string }>(a: T, b: T): number {
  return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
}

function AlertRow({ alert }: { alert: SOCAlert }) {
  return (
    <div className={styles.alert}>
      <span
        className={styles.alertDot}
        style={{ background: severityToColor(alert.severity) }}
        aria-hidden="true"
      />
      <div className={styles.alertBody}>
        <span className={styles.alertRule}>{alert.ruleName}</span>
        <span className={styles.alertMeta}>
          <span>{alert.source}</span>
          <span>{alert.affectedHost}</span>
          {alert.athenaScenario && <span className={styles.alertTag}>labeled</span>}
          <span>{timeAgo(alert.timestamp)}</span>
        </span>
      </div>
      {alert.triageResult && (
        <span className={styles.alertScore} title="AI triage confidence">
          {Math.round(alert.triageResult.confidenceScore * 100)}%
        </span>
      )}
    </div>
  );
}

/** The run view: a red lane (agent actions) beside a blue lane (SOC detections). */
export function RunDetail({ session, events, alerts }: RunDetailProps) {
  if (!session) {
    return (
      <div className={styles.detailEmpty}>
        <p>Select a run</p>
        <p className={styles.detailEmptyHint}>
          Pick a session from the spine to see what the agent did and what the SOC caught.
        </p>
      </div>
    );
  }

  const redEvents = [...events].sort(byTimeDesc);
  const blueAlerts = [...alerts].sort(byTimeDesc);
  const acts = countActs(events);

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
          <span>updated {timeAgo(session.lastAt)}</span>
          <span className={styles.detailId}>{session.sessionId}</span>
        </div>
      </header>

      <div className={styles.coverage}>
        <span className={styles.coverageStat}>
          <strong>{acts}</strong> agent {acts === 1 ? 'act' : 'acts'}
        </span>
        <span className={styles.coverageStat}>
          <strong>{blueAlerts.length}</strong> alerts on {hostOf(session.target) || 'target'}
        </span>
        <span className={styles.coverageNote}>host + time match — approximate, not per-action (#16)</span>
      </div>

      <div className={styles.lanes}>
        <div className={styles.lane}>
          <div className={styles.laneHeader}>
            <span className={`${styles.laneDot} ${styles.laneRed}`} aria-hidden="true" />
            <span className={styles.laneTitle}>Red — agent actions</span>
            <span className={styles.laneCount}>{events.length}</span>
          </div>
          {redEvents.length === 0 ? (
            <p className={styles.laneEmpty}>No agent events for this run yet.</p>
          ) : (
            <div className={styles.timeline}>
              {redEvents.map((event) => (
                <EventRow key={event.id} event={event} selected={false} onSelect={() => {}} />
              ))}
            </div>
          )}
        </div>

        <div className={styles.lane}>
          <div className={styles.laneHeader}>
            <span className={`${styles.laneDot} ${styles.laneBlue}`} aria-hidden="true" />
            <span className={styles.laneTitle}>Blue — SOC detections</span>
            <span className={styles.laneCount}>{blueAlerts.length}</span>
          </div>
          {blueAlerts.length === 0 ? (
            <p className={styles.laneEmpty}>No alerts matched this run's target and window.</p>
          ) : (
            <div className={styles.alertList}>
              {blueAlerts.map((alert) => (
                <AlertRow key={alert.id} alert={alert} />
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
