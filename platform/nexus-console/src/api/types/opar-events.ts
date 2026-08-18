export type OPARPhase = 'observe' | 'plan' | 'act' | 'reflect';
export type OutcomeStatus = 'success' | 'failure' | 'pending' | 'blocked';

export interface OPAREvent {
  id: string;
  timestamp: string;
  sessionId: string;
  phase: OPARPhase;
  target: string;
  toolName?: string;
  outcomeStatus: OutcomeStatus;
  payload: Record<string, unknown>;
}

export interface AgentFeedFilters {
  phase?: OPARPhase;
  target?: string;
  outcomeStatus?: OutcomeStatus;
}
