'use client';

import { getOnboardingProcess, onboardingKeys, updateTaskStatus, type OnboardingProcess, type OnboardingTask } from '@/lib/api/onboarding';
import { cn } from '@/lib/utils';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Check, Circle, Loader2, User, Calendar, Briefcase, BadgeCheck, AlertCircle } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { EmployeeSetupForm } from './EmployeeSetupForm';
import { getProcessStatusMeta, getTaskReadinessNote } from './onboarding-detail-utils';

// ─── Sub-components ──────────────────────────────────────────────────────

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
      <p className="text-sm">Không có dữ liệu</p>
    </div>
  );
}

// ─── Overview Tab ────────────────────────────────────────────────────────

function OverviewPanel({ process }: { process: OnboardingProcess }) {
  const initials = process.employee_full_name
    ?.split(' ')
    .slice(-2)
    .map((w) => w[0])
    .join('') || '?';

  const statusMeta = getProcessStatusMeta(process.status);
  const allDone = (process.tasks ?? []).length > 0 &&
    (process.tasks ?? []).every((t) => t.status === 'done');
  const pct = process.total_count > 0
    ? Math.round((process.completed_count / process.total_count) * 100)
    : 0;

  return (
    <div className="space-y-6">
      {/* Candidate info card */}
      <div className="rounded-xl border bg-card p-6">
        <div className="flex items-start gap-4">
          <div className="size-12 rounded-xl bg-muted flex items-center justify-center text-lg font-semibold shrink-0">
            {initials}
          </div>
          <div className="flex-1 min-w-0 space-y-2">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-lg font-semibold">{process.employee_full_name}</h3>
                <p className="text-sm text-muted-foreground mt-0.5">{process.employee_email}</p>
              </div>
              <span className={cn('inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium border shrink-0', statusMeta.badgeClassName)}>
                <BadgeCheck className="size-3.5" />
                {statusMeta.label}
              </span>
            </div>

            <div className="flex flex-wrap gap-x-6 gap-y-1.5 text-sm pt-1">
              {process.employee_code && (
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  <User className="size-3.5" />
                  <span>Mã NV: {process.employee_code}</span>
                </div>
              )}
              {process.accepted_at && (
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  <Calendar className="size-3.5" />
                  <span>Nhận việc: {new Date(process.accepted_at).toLocaleDateString('vi-VN')}</span>
                </div>
              )}
              {process.job_opening && (
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  <Briefcase className="size-3.5" />
                  <span>Vị trí: {process.job_opening}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Progress */}
      <div className="rounded-xl border bg-card p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-medium">Tiến độ</h4>
          <span className="text-sm text-muted-foreground">
            {process.completed_count}/{process.total_count} tasks
          </span>
        </div>
        <div className="h-2.5 rounded-full bg-secondary overflow-hidden">
          <div
            className={cn(
              'h-full transition-all duration-300 rounded-full',
              allDone ? 'bg-emerald-500' : 'bg-primary',
            )}
            style={{ width: `${pct}%` }}
          />
        </div>

        {/* Readiness indicators */}
        <div className="flex flex-wrap gap-2 pt-1">
          {process.missing_setup_fields && process.missing_setup_fields.length > 0 ? (
            <span className="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium bg-amber-50 text-amber-600 border border-amber-200">
              <AlertCircle className="size-3.5" />
              Thiếu setup: {process.missing_setup_fields.join(', ')}
            </span>
          ) : process.status === 'complete' ? (
            <span className="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium bg-emerald-50 text-emerald-600 border border-emerald-200">
              <Check className="size-3.5" />
              Đã hoàn tất
            </span>
          ) : allDone ? (
            <span className="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium bg-emerald-50 text-emerald-600 border border-emerald-200">
              <BadgeCheck className="size-3.5" />
              Sẵn sàng kích hoạt — tất cả task đã hoàn thành
            </span>
          ) : null}
        </div>
      </div>

      {/* Employee Setup */}
      <EmployeeSetupForm process={process} />
    </div>
  );
}

// ─── Tasks Tab ───────────────────────────────────────────────────────────

function TasksPanel({
  process,
  onToggle,
  isPending,
}: {
  process: OnboardingProcess;
  onToggle: (task: OnboardingTask) => void;
  isPending: boolean;
}) {
  const tasks = (process.tasks ?? []).sort((a, b) => a.order_index - b.order_index);

  if (tasks.length === 0) return <EmptyState />;

  return (
    <div className="space-y-2">
      {tasks.map((task) => (
        <button
          key={task.id}
          onClick={() => onToggle(task)}
          disabled={isPending || process.status === 'complete'}
          className={cn(
            'w-full flex items-center gap-3 p-4 rounded-xl border bg-card text-left transition-all',
            task.status === 'done' ? 'hover:bg-muted/50' : 'hover:bg-muted/30',
            (isPending || process.status === 'complete') && 'opacity-50 cursor-not-allowed',
          )}
        >
          {task.status === 'done' ? (
            <div className="size-6 rounded-full bg-emerald-100 flex items-center justify-center shrink-0">
              <Check className="size-3.5 text-emerald-600" />
            </div>
          ) : (
            <div className="size-6 rounded-full border-2 border-muted-foreground/30 flex items-center justify-center shrink-0">
              <Circle className="size-3 text-muted-foreground/30" />
            </div>
          )}
          <div className="flex-1 min-w-0">
            <p className={cn('text-sm font-medium', task.status === 'done' && 'line-through text-muted-foreground')}>
              {task.name}
            </p>
            {task.status === 'done' && task.completed_at && (
              <p className="text-xs text-muted-foreground mt-0.5">
                Bởi {task.completed_by_name ?? 'Hệ thống'} · {new Date(task.completed_at).toLocaleString('vi-VN')}
              </p>
            )}
          </div>
        </button>
      ))}
    </div>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────

interface OnboardingDetailProps {
  processId: string;
}

export function OnboardingDetail({ processId }: OnboardingDetailProps) {
  const queryClient = useQueryClient();
  const [taskToUpdate, setTaskToUpdate] = useState<OnboardingTask | null>(null);

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

  const handleToggle = (task: OnboardingTask) => {
    if (process.status === 'complete') return;
    setTaskToUpdate(task);
  };

  const confirmUpdate = () => {
    if (taskToUpdate) {
      updateMutation.mutate({
        taskId: taskToUpdate.id,
        status: taskToUpdate.status === 'done' ? 'pending' : 'done',
      });
      setTaskToUpdate(null);
    }
  };

  const getNote = (task: OnboardingTask) => getTaskReadinessNote(process, task);

  return (
    <div className="h-full flex flex-col">
      <Tabs defaultValue="overview" className="flex-1 flex flex-col">
        <div className="px-6 pt-5 pb-0 border-b">
          <TabsList>
            <TabsTrigger value="overview" className="text-sm">Thông tin</TabsTrigger>
            <TabsTrigger value="tasks" className="text-sm">
              Checklist
              <span className="ml-1.5 inline-flex items-center justify-center size-5 rounded-full bg-muted-foreground/10 text-[11px] font-medium">
                {(process.tasks ?? []).length}
              </span>
            </TabsTrigger>
          </TabsList>
        </div>

        <div className="flex-1 overflow-y-auto">
          <div className="p-6">
            <TabsContent value="overview" className="mt-0">
              <OverviewPanel process={process} />
            </TabsContent>
            <TabsContent value="tasks" className="mt-0">
              <TasksPanel
                process={process}
                onToggle={handleToggle}
                isPending={updateMutation.isPending}
              />
            </TabsContent>
          </div>
        </div>
      </Tabs>

      {/* Confirmation Dialog */}
      <AlertDialog open={!!taskToUpdate} onOpenChange={(open) => !open && setTaskToUpdate(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {taskToUpdate?.status === 'done' ? 'Xác nhận hoàn tác' : 'Xác nhận hoàn thành'}
            </AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div className="mt-2 text-sm text-muted-foreground space-y-3">
                {taskToUpdate?.status === 'done' ? (
                  <p>Đưa task <strong className="text-foreground">{taskToUpdate.name}</strong> về trạng thái chờ?</p>
                ) : (
                  taskToUpdate && (
                    <>
                      <p>Xác nhận hoàn thành: <strong className="text-foreground">{taskToUpdate.name}</strong></p>
                      <div className={cn(
                        'p-3 rounded-md border text-sm',
                        getNote(taskToUpdate).isReady
                          ? 'bg-muted/50 text-muted-foreground'
                          : 'bg-destructive/10 text-destructive border-destructive/20 font-medium',
                      )}>
                        {getNote(taskToUpdate).note}
                      </div>
                    </>
                  )
                )}
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Hủy</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmUpdate}
              disabled={taskToUpdate?.status === 'pending' && !getNote(taskToUpdate!).isReady}
              className={cn(taskToUpdate?.status === 'done' && 'bg-destructive text-destructive-foreground hover:bg-destructive/90')}
            >
              {taskToUpdate?.status === 'done' ? 'Revert' : 'Xác nhận Done'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
