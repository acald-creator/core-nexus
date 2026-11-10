import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router';
import { useAgentFeed } from '../hooks/useAgentFeed';
import { useAlerts } from '../hooks/useAlerts';
import { ErrorBanner } from '../components/common/ErrorBanner';
import { SessionSpine } from '../components/panels/Runs/SessionSpine';
import { RunDetail } from '../components/panels/Runs/RunDetail';
import { deriveSessions } from '../components/panels/Runs/sessions';
import { correlateAlertsToRun, runWindow } from '../components/panels/Runs/correlation';
import styles from '../components/panels/Runs/Runs.module.css';

/**
 * Run-centric view: one streamed agent feed, grouped into sessions. The spine
 * lists the runs; selecting one (/runs/:sessionId) scopes the detail to that
 * session's event timeline. Reuses the existing feed stream and event rows.
 */
export default function RunsPage() {
  const { sessionId } = useParams();
  const { events, isConnected, connectionError, retry } = useAgentFeed();
  const { alerts } = useAlerts();

  // `now` is seeded once via a lazy initializer and refreshed on an interval,
  // so the render stays pure and sessions age out of the live window over time.
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 30_000);
    return () => clearInterval(id);
  }, []);

  const sessions = useMemo(() => deriveSessions(events, now), [events, now]);
  const sessionEvents = useMemo(
    () => (sessionId ? events.filter((e) => e.sessionId === sessionId) : []),
    [events, sessionId],
  );
  const active = sessions.find((s) => s.sessionId === sessionId);

  const window = useMemo(() => runWindow(sessionEvents), [sessionEvents]);
  const runAlerts = useMemo(
    () => (active ? correlateAlertsToRun(active.target, window, alerts) : []),
    [active, window, alerts],
  );

  return (
    <div className={`ds-span ${styles.runs}`}>
      {connectionError && (
        <div className={styles.runsBanner}>
          <ErrorBanner message={connectionError} onRetry={retry} />
        </div>
      )}
      <div className={styles.runsBody}>
        <SessionSpine sessions={sessions} isConnected={isConnected} />
        <RunDetail session={active} events={sessionEvents} alerts={runAlerts} window={window} />
      </div>
    </div>
  );
}
