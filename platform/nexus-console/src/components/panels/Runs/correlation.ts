import type { OPAREvent } from '../../../api/types/opar-events';
import type { SOCAlert } from '../../../api/types/alerts';

export interface RunWindow {
  start: number;
  end: number;
}

/** Host of a target/affectedHost string: drop scheme, path, and port. */
export function hostOf(value: string): string {
  return value
    .replace(/^\w+:\/\//, '')
    .split('/')[0]
    .split(':')[0]
    .trim()
    .toLowerCase();
}

/** The run's time span, padded, so alerts just before/after an action still match. */
export function runWindow(events: OPAREvent[], bufferMs = 60_000): RunWindow | null {
  if (events.length === 0) return null;
  let min = Infinity;
  let max = -Infinity;
  for (const e of events) {
    const t = new Date(e.timestamp).getTime();
    if (t < min) min = t;
    if (t > max) max = t;
  }
  return { start: min - bufferMs, end: max + bufferMs };
}

/**
 * Best-effort correlation of SOC alerts to one run.
 *
 * The join is COARSE: alerts carry no sessionId, so a run is matched to alerts
 * by target host (agent `target` vs alert `affectedHost`) within the run's time
 * window. This is host/time-level, NOT per-action, so any "coverage" derived
 * from it is approximate — see issue #16 (detection currently keys off the
 * agent's own Athena label, which makes per-action coverage circular).
 */
export function correlateAlertsToRun(
  target: string,
  window: RunWindow | null,
  alerts: SOCAlert[],
): SOCAlert[] {
  // No run span means no run to correlate against — host-only matching would be
  // unbounded in time, so return nothing rather than every alert for the host.
  if (!window) return [];
  const targetHost = hostOf(target);
  return alerts.filter((a) => {
    const t = new Date(a.timestamp).getTime();
    if (t < window.start || t > window.end) return false;
    return !!targetHost && hostOf(a.affectedHost) === targetHost;
  });
}

/** Count of `act`-phase events — the agent's actual moves, for the red lane. */
export function countActs(events: OPAREvent[]): number {
  return events.filter((e) => e.phase === 'act').length;
}
