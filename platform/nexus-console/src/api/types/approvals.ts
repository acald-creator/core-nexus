export interface ApprovalAction {
  id: string;
  sessionId: string;
  proposedTool: string;
  target: string;
  argumentsSummary: string;
  submittedAt: string;
  status: 'pending' | 'approved' | 'rejected';
  /** OPAR default; factory reviews set source=factory (ADR 0009). */
  source?: 'opar' | 'factory' | string;
  riskMax?: string | number | null;
  checkRunUrl?: string | null;
}

export interface ApprovalDecision {
  actionId: string;
  decision: 'approve' | 'reject';
}
