'use client';

import { useQuery } from '@tanstack/react-query';
import {
  getOnboardingTimeline,
  type OnboardingTimelineItem,
} from '@/lib/api/onboarding';
import { cn } from '@/lib/utils';
import {
  AlertTriangle,
  CalendarClock,
  CheckCircle2,
  Clock3,
  FileSignature,
  FileText,
  Loader2,
} from 'lucide-react';

const KIND_META: Record<string, { label: string; icon: typeof FileText; tone: string }> = {
  milestone: { label: 'Mốc', icon: CheckCircle2, tone: 'bg-emerald-100 text-emerald-700 border-emerald-200' },
  reminder: { label: 'Nhắc việc', icon: AlertTriangle, tone: 'bg-amber-50 text-amber-700 border-amber-200' },
  task: { label: 'Task', icon: Clock3, tone: 'bg-blue-50 text-blue-700 border-blue-200' },
  document: { label: 'Tài liệu', icon: FileText, tone: 'bg-slate-100 text-slate-700 border-slate-200' },
  contract: { label: 'Hợp đồng', icon: FileSignature, tone: 'bg-violet-100 text-violet-700 border-violet-200' },
};

function groupEvents(items: OnboardingTimelineItem[]) {
  return {
    milestone: items.filter((item) => item.kind === 'milestone'),
    reminder: items.filter((item) => item.kind === 'reminder'),
    task: items.filter((item) => item.kind === 'task'),
    document: items.filter((item) => item.kind === 'document'),
    contract: items.filter((item) => item.kind === 'contract'),
  };
}

function TimelineRow({ item }: { item: OnboardingTimelineItem }) {
  const meta = KIND_META[item.kind] ?? KIND_META.task;
  const Icon = meta.icon;

  return (
    <div className="flex gap-3 rounded-xl border bg-card p-4">
      <div
        className={cn(
          'mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full border',
          item.is_overdue
            ? 'bg-red-100 text-red-700 border-red-200'
            : meta.tone,
        )}
      >
        <Icon className="size-4" />
      </div>
      <div className="min-w-0 flex-1 space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-sm font-medium">{item.title}</p>
          <span className={cn('inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-medium', meta.tone)}>
            {meta.label}
          </span>
          {item.is_overdue && (
            <span className="inline-flex items-center rounded-full border border-red-200 bg-red-50 px-2 py-0.5 text-[10px] font-medium text-red-700">
              Quá hạn
            </span>
          )}
        </div>
        {item.description && <p className="text-xs text-muted-foreground">{item.description}</p>}
        <div className="flex flex-wrap items-center gap-3 text-[11px] text-muted-foreground">
          <span className="inline-flex items-center gap-1">
            <CalendarClock className="size-3.5" />
            {new Date(item.timestamp).toLocaleString('vi-VN')}
          </span>
          {item.actor_name && <span>Bởi {item.actor_name}</span>}
          {item.due_at && <span>Hạn: {new Date(item.due_at).toLocaleDateString('vi-VN')}</span>}
          {item.status && <span>Trạng thái: {item.status}</span>}
        </div>
      </div>
    </div>
  );
}

function Section({ title, items }: { title: string; items: OnboardingTimelineItem[] }) {
  if (items.length === 0) return null;
  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">{title}</h3>
        <span className="text-xs text-muted-foreground">{items.length}</span>
      </div>
      <div className="space-y-3">
        {items.map((item) => (
          <TimelineRow key={`${item.event_type}-${item.timestamp}-${item.title}`} item={item} />
        ))}
      </div>
    </section>
  );
}

export function TimelinePanel({ processId }: { processId: string }) {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['onboarding', 'timeline', processId],
    queryFn: () => getOnboardingTimeline(processId),
    enabled: !!processId,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-10 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-10 text-sm text-muted-foreground">
        <p>{(error as Error).message}</p>
        <button onClick={() => refetch()} className="text-primary hover:underline">
          Thử lại
        </button>
      </div>
    );
  }

  const items = [...(data?.events ?? [])].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
  );
  const grouped = groupEvents(items);

  if (items.length === 0) {
    return <p className="py-10 text-center text-sm text-muted-foreground">Chưa có timeline.</p>;
  }

  return (
    <div className="space-y-6">
      <Section title="Mốc chính" items={grouped.milestone} />
      <Section title="Nhắc việc" items={grouped.reminder} />
      <Section title="Hoạt động" items={[...grouped.task, ...grouped.document, ...grouped.contract]} />
    </div>
  );
}
