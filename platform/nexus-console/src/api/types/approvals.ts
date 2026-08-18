export interface ApprovalAction {
  id: string;
  sessionId: string;
  proposedTool: string;
  target: string;
  argumentsSummary: string;
  submittedAt: string;
  status: 'pending' | 'approved' | 'rejected';
}

export interface ApprovalDecision {
  actionId: string;
  decision: 'approve' | 'reject';
}
