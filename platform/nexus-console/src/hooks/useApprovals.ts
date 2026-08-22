import { fetchWithAuth } from '../api/fetchWithAuth';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useConfig } from '../config/ConfigContext';
import type { ApprovalAction } from '../api/types/approvals';

export function sortApprovalsBySubmittedAt(approvals: ApprovalAction[]): ApprovalAction[] {
  return [...approvals].sort((a, b) => new Date(a.submittedAt).getTime() - new Date(b.submittedAt).getTime());
}

export function countPendingApprovals(approvals: ApprovalAction[]): number {
  return approvals.filter((a) => a.status === 'pending').length;
}

export function useApprovals() {
  const config = useConfig();
  const queryClient = useQueryClient();

  const { data: pending = [], isLoading } = useQuery<ApprovalAction[]>({
    queryKey: ['approvals', 'pending'],
    queryFn: async () => {
      const response = await fetchWithAuth(`${config.apiGatewayUrl}/api/v1/approvals?status=pending`);
      if (!response.ok) throw new Error(`Approvals fetch failed: ${response.status}`);
      return response.json();
    },
    refetchInterval: 5_000,
    select: sortApprovalsBySubmittedAt,
  });

  const mutation = useMutation({
    mutationFn: async ({ id, decision }: { id: string; decision: 'approve' | 'reject' }) => {
      const response = await fetchWithAuth(`${config.apiGatewayUrl}/api/v1/approvals/${id}/decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision }),
      });
      if (!response.ok) throw new Error(`Decision failed: ${response.status}`);
      return response.json();
    },
    onMutate: async ({ id }) => {
      await queryClient.cancelQueries({ queryKey: ['approvals', 'pending'] });
      const previous = queryClient.getQueryData<ApprovalAction[]>(['approvals', 'pending']);
      queryClient.setQueryData<ApprovalAction[]>(
        ['approvals', 'pending'],
        (old) => old?.filter((a) => a.id !== id) || []
      );
      return { previous };
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(['approvals', 'pending'], context.previous);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['approvals'] });
    },
  });

  return {
    pending,
    pendingCount: countPendingApprovals(pending),
    approve: (id: string) => mutation.mutateAsync({ id, decision: 'approve' }),
    reject: (id: string) => mutation.mutateAsync({ id, decision: 'reject' }),
    isSubmitting: mutation.isPending,
    submitError: mutation.error,
    isLoading,
  };
}
