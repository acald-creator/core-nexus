import { describe, expect, it } from 'vitest';
import fc from 'fast-check';
import { countUnacknowledgedCriticalHigh } from '../useAlerts';
import { countPendingApprovals } from '../useApprovals';
import type { SOCAlert } from '../../api/types/alerts';
import type { ApprovalAction } from '../../api/types/approvals';

const severityArb = fc.constantFrom(
  'critical',
  'high',
  'medium',
  'low',
  'informational',
) as fc.Arbitrary<SOCAlert['severity']>;

const alertArb: fc.Arbitrary<SOCAlert> = fc.record({
  id: fc.uuid(),
  timestamp: fc.integer({ min: 0, max: 1_700_000_000_000 }).map((ms) => new Date(ms).toISOString()),
  severity: severityArb,
  source: fc.constantFrom(
    'wazuh',
    'suricata',
    'zeek',
    'falco',
    'tetragon',
    'ai-inference',
  ) as fc.Arbitrary<SOCAlert['source']>,
  ruleName: fc.string({ maxLength: 40 }),
  affectedHost: fc.string({ maxLength: 40 }),
  acknowledged: fc.boolean(),
  payload: fc.constant({}),
  athenaScenario: fc.option(fc.string({ minLength: 1, maxLength: 24 }), { nil: undefined }),
});

const approvalArb: fc.Arbitrary<ApprovalAction> = fc.record({
  id: fc.uuid(),
  sessionId: fc.uuid(),
  proposedTool: fc.string({ maxLength: 32 }),
  target: fc.string({ maxLength: 32 }),
  argumentsSummary: fc.string({ maxLength: 64 }),
  submittedAt: fc.integer({ min: 0, max: 1_700_000_000_000 }).map((ms) => new Date(ms).toISOString()),
  status: fc.constantFrom('pending', 'approved', 'rejected') as fc.Arbitrary<ApprovalAction['status']>,
  source: fc.option(fc.constantFrom('opar', 'factory'), { nil: undefined }),
});

describe('Property 16: Badge count accuracy', () => {
  it('alerts badge equals unacknowledged critical+high count', () => {
    fc.assert(
      fc.property(fc.array(alertArb, { maxLength: 50 }), (alerts) => {
        const expected = alerts.filter(
          (a) => !a.acknowledged && (a.severity === 'critical' || a.severity === 'high'),
        ).length;
        expect(countUnacknowledgedCriticalHigh(alerts)).toBe(expected);
      }),
    );
  });

  it('approvals badge equals pending count', () => {
    fc.assert(
      fc.property(fc.array(approvalArb, { maxLength: 50 }), (approvals) => {
        const expected = approvals.filter((a) => a.status === 'pending').length;
        expect(countPendingApprovals(approvals)).toBe(expected);
      }),
    );
  });
});
