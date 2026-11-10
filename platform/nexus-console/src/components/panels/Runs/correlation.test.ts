import { describe, expect, it } from 'vitest';
import { correlateAlertsToRun, countActs, hostOf, runWindow } from './correlation';
import type { OPAREvent } from '../../../api/types/opar-events';
import type { SOCAlert } from '../../../api/types/alerts';

function ev(p: Partial<OPAREvent> & { timestamp: string }): OPAREvent {
  return {
    id: p.timestamp,
    sessionId: 's1',
    phase: 'act',
    target: 'juice-shop:3000',
    outcomeStatus: 'success',
    payload: {},
    ...p,
  };
}
function al(p: Partial<SOCAlert> & { timestamp: string; affectedHost: string }): SOCAlert {
  return {
    id: p.timestamp + p.affectedHost,
    severity: 'high',
    source: 'suricata',
    ruleName: 'rule',
    acknowledged: false,
    payload: {},
    ...p,
  };
}

describe('hostOf', () => {
  it('strips scheme, path, and port', () => {
    expect(hostOf('http://juice-shop:3000/rest')).toBe('juice-shop');
    expect(hostOf('juice-shop:3000')).toBe('juice-shop');
    expect(hostOf('JUICE-SHOP')).toBe('juice-shop');
  });
});

describe('countActs', () => {
  it('counts only act-phase events', () => {
    expect(countActs([ev({ timestamp: '1', phase: 'observe' }), ev({ timestamp: '2', phase: 'act' })])).toBe(1);
  });
});

describe('correlateAlertsToRun', () => {
  const win = runWindow([ev({ timestamp: '2026-11-09T12:00:00Z' })]);

  it('matches alerts on the same target host within the window', () => {
    const matched = correlateAlertsToRun('juice-shop:3000', win, [
      al({ timestamp: '2026-11-09T12:00:10Z', affectedHost: 'juice-shop' }),
      al({ timestamp: '2026-11-09T12:00:10Z', affectedHost: 'other-host' }),
    ]);
    expect(matched).toHaveLength(1);
    expect(matched[0].affectedHost).toBe('juice-shop');
  });

  it('excludes alerts outside the time window', () => {
    const matched = correlateAlertsToRun('juice-shop:3000', win, [
      al({ timestamp: '2026-11-09T15:00:00Z', affectedHost: 'juice-shop' }),
    ]);
    expect(matched).toHaveLength(0);
  });
});
