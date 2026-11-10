import type { OPAREvent, OPARPhase, OutcomeStatus } from '../../../api/types/opar-events';

/** A run is one OPAR session, summarised from its stream of events. */
export interface SessionSummary {
  sessionId: string;
  target: string;
  latestPhase: OPARPhase;
  latestOutcome: OutcomeStatus;
  eventCount: number;
  /** ISO timestamp of the most recent event in the session. */
  lastAt: string;
  /** The session produced an event within [`LIVE_WINDOW_MS`] of `now`. */
  live: boolean;
}

/** A session with no event newer than this is treated as finished, not live. */
export const LIVE_WINDOW_MS = 120_000;

/**
 * Group a flat event stream into one summary per `sessionId`, ordered live-runs
 * first and then most-recently-active. `now` is injected so the `live` flag is
 * deterministic in tests.
 */
export function deriveSessions(events: OPAREvent[], now: number): SessionSummary[] {
  const groups = new Map<string, OPAREvent[]>();
  for (const event of events) {
    const arr = groups.get(event.sessionId);
    if (arr) arr.push(event);
    else groups.set(event.sessionId, [event]);
  }

  const summaries: SessionSummary[] = [];
  for (const [sessionId, group] of groups) {
    let latest = group[0];
    for (const event of group) {
      if (new Date(event.timestamp).getTime() > new Date(latest.timestamp).getTime()) {
        latest = event;
      }
    }
    summaries.push({
      sessionId,
      target: latest.target,
      latestPhase: latest.phase,
      latestOutcome: latest.outcomeStatus,
      eventCount: group.length,
      lastAt: latest.timestamp,
      live: now > 0 && now - new Date(latest.timestamp).getTime() < LIVE_WINDOW_MS,
    });
  }

  summaries.sort((a, b) => {
    if (a.live !== b.live) return a.live ? -1 : 1;
    return new Date(b.lastAt).getTime() - new Date(a.lastAt).getTime();
  });
  return summaries;
}
