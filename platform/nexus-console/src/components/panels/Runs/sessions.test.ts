import { describe, expect, it } from 'vitest';
import { deriveSessions } from './sessions';
import type { OPAREvent } from '../../../api/types/opar-events';

function ev(partial: Partial<OPAREvent> & { sessionId: string; timestamp: string }): OPAREvent {
  return {
    id: `${partial.sessionId}-${partial.timestamp}`,
    phase: 'act',
    target: 'juice-shop:3000',
    outcomeStatus: 'success',
    payload: {},
    ...partial,
  };
}

const NOW = Date.parse('2026-11-09T12:00:00Z');

describe('deriveSessions', () => {
  it('groups events by sessionId and counts them', () => {
    const sessions = deriveSessions(
      [
        ev({ sessionId: 's1', timestamp: '2026-11-09T11:59:00Z' }),
        ev({ sessionId: 's1', timestamp: '2026-11-09T11:59:30Z' }),
        ev({ sessionId: 's2', timestamp: '2026-11-09T11:00:00Z' }),
      ],
      NOW,
    );
    expect(sessions).toHaveLength(2);
    expect(sessions.find((s) => s.sessionId === 's1')?.eventCount).toBe(2);
  });

  it('takes target/phase/outcome from the most recent event', () => {
    const [s] = deriveSessions(
      [
        ev({ sessionId: 's1', timestamp: '2026-11-09T11:00:00Z', phase: 'observe', target: 'old' }),
        ev({ sessionId: 's1', timestamp: '2026-11-09T11:59:00Z', phase: 'reflect', target: 'new' }),
      ],
      NOW,
    );
    expect(s.latestPhase).toBe('reflect');
    expect(s.target).toBe('new');
    expect(s.lastAt).toBe('2026-11-09T11:59:00Z');
  });

  it('orders live sessions first, then most-recently-active', () => {
    const sessions = deriveSessions(
      [
        ev({ sessionId: 'stale', timestamp: '2026-11-09T10:00:00Z' }), // > 2 min old
        ev({ sessionId: 'live-old', timestamp: '2026-11-09T11:59:00Z' }),
        ev({ sessionId: 'live-new', timestamp: '2026-11-09T11:59:50Z' }),
      ],
      NOW,
    );
    expect(sessions.map((s) => s.sessionId)).toEqual(['live-new', 'live-old', 'stale']);
    expect(sessions.find((s) => s.sessionId === 'stale')?.live).toBe(false);
    expect(sessions.find((s) => s.sessionId === 'live-new')?.live).toBe(true);
  });
});
