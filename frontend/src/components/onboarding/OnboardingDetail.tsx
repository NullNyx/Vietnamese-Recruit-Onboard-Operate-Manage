'use client';

import { getOnboardingProcess, onboardingKeys, updateTaskStatus } from '@/lib/api/onboarding';
import { cn } from '@/lib/utils';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Check, Circle, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

interface OnboardingDetailProps {
  processId: string;
}

function LoadingState() {
  return (
    <div className="flex items-center justify-center h-full">
      <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
    </div>
  );
}

function ErrorState({ error, onRetry }: { error: Error; onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-3">
      <p className="text-sm text-destructive">{error.message}</p>
      <button onClick={onRetry} className="text-sm text-primary hover:underline">
        Thử lại
      </button>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-2 text-muted-foreground">
      <p className="text-sm">Không có task nào</p>
    </div>
  );
}

export function OnboardingDetail({ processId }: OnboardingDetailProps) {
  const queryClient = useQueryClient();

  const {
    data: process,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: onboardingKeys.detail(processId),
    queryFn: () => getOnboardingProcess(processId),
  });

  const updateMutation = useMutation({
    mutationFn: ({ taskId, status }: { taskId: string; status: 'pending' | 'done' }) =>
      updateTaskStatus(taskId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: onboardingKeys.detail(processId) });
      queryClient.invalidateQueries({ queryKey: onboardingKeys.lists() });
      queryClient.invalidateQueries({ queryKey: onboardingKeys.counts() });
      toast.success('Đã cập nhật task');
    },
    onError: (err: Error) => {
      toast.error(err.message || 'Cập nhật thất bại');
    },
  });

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error as Error} onRetry={() => refetch()} />;
  if (!process) return <EmptyState />;

  const tasks = process.tasks ?? [];
  const allDone = tasks.length > 0 && tasks.every((t) => t.status === 'done');

  const handleToggle = (taskId: string, currentStatus: 'pending' | 'done') => {
    // One-way action: only allow marking pending → done (matching backend semantics).
    if (currentStatus === 'pending') {
      updateMutation.mutate({ taskId, status: 'done' });
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="px-6 py-5 border-b">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="size-10 rounded-lg bg-muted flex items-center justify-center text-sm font-medium mt-1">
              {process.employee_full_name
                ?.split(' ')
                .slice(-2)
                .map((w) => w[0])
                .join('') || '?'}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-semibold">{process.employee_full_name}</h2>
              </div>
              <div className="flex flex-col gap-1 mt-2 text-sm text-muted-foreground">
                <div className="flex items-center gap-2">
                  <span className="truncate">{process.employee_email}</span>
                </div>
                {(process.accepted_at || process.job_opening) && (
                  <div className="flex items-center gap-3 text-xs">
                    {process.accepted_at && (
                      <span>
                        Nhận việc: {new Date(process.accepted_at).toLocaleDateString('vi-VN')}
                      </span>
                    )}
                    {process.job_opening && <span>Vị trí: {process.job_opening}</span>}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Progress summary */}
        <div className="mt-5 flex items-center gap-3">
          <div className="flex-1 h-2 rounded-full bg-secondary overflow-hidden">
            <div
              className={cn(
                'h-full transition-all duration-300',
                allDone ? 'bg-emerald-500' : 'bg-primary',
              )}
              style={{
                width: `${process.total_count > 0 ? (process.completed_count / process.total_count) * 100 : 0}%`,
              }}
            />
          </div>
          <span className="text-sm text-muted-foreground">
            {process.completed_count}/{process.total_count} tasks
          </span>
          {process.missing_setup_fields && process.missing_setup_fields.length > 0 ? (
            <span className="text-xs font-medium text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
              Thiếu setup data
            </span>
          ) : process.status === 'complete' ? (
            <span className="text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
              Đã kích hoạt
            </span>
          ) : allDone ? (
            <span className="text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
              Sẵn sàng kích hoạt
            </span>
          ) : null}
        </div>
      </div>

      {/* Task list */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="space-y-2">
          {tasks.length === 0 ? (
            <EmptyState />
          ) : (
            tasks
              .sort((a, b) => a.order_index - b.order_index)
              .map((task) => (
                <button
                  key={task.id}
                  onClick={() => handleToggle(task.id, task.status)}
                  disabled={updateMutation.isPending || task.status === 'done'}
                  className={cn(
                    'w-full flex items-center gap-3 p-3 rounded-lg border text-left transition-all',
                    task.status === 'done' ? 'bg-muted/30 cursor-default' : 'hover:bg-muted/50',
                    updateMutation.isPending && 'opacity-50 cursor-not-allowed',
                  )}
                >
                  {task.status === 'done' ? (
                    <Check className="size-5 text-emerald-500 shrink-0" />
                  ) : (
                    <Circle className="size-5 text-muted-foreground/50 shrink-0" />
                  )}
                  <span
                    className={cn(
                      'flex-1 text-sm',
                      task.status === 'done' && 'line-through text-muted-foreground',
                    )}
                  >
                    {task.name}
                  </span>
                </button>
              ))
          )}
        </div>
      </div>
    </div>
  );
}
