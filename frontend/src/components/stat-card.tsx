import type { LucideIcon } from "lucide-react";

export interface StatCardProps {
  title: string;
  value: number;
  icon: LucideIcon;
  subtitle?: string;
  loading?: boolean;
  emptyLabel?: string;
}

export function StatCard({
  title,
  value,
  icon: Icon,
  subtitle,
  loading,
  emptyLabel = "Chưa có dữ liệu",
}: StatCardProps) {
  const isEmpty = !loading && value === 0;

  return (
    <div className="rounded-lg border border-border/20 bg-card p-5">
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <p className="font-label text-xs uppercase tracking-[0.08em] text-muted-foreground">
            {title}
          </p>
          {loading ? (
            <div className="h-8 w-16 animate-pulse rounded-md bg-secondary" />
          ) : (
            <p className="font-heading text-2xl font-semibold text-foreground">
              {value}
            </p>
          )}
          {!loading && subtitle && (
            <p className="text-xs text-muted-foreground">{subtitle}</p>
          )}
          {isEmpty && (
            <span className="inline-block rounded-md bg-secondary px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
              {emptyLabel}
            </span>
          )}
        </div>
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-secondary">
          <Icon className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
        </div>
      </div>
    </div>
  );
}
