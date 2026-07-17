import type { LucideIcon } from "lucide-react";

export interface StatCardProps {
  title: string;
  value: number;
  icon: LucideIcon;
  subtitle?: string;
  loading?: boolean;
  emptyLabel?: string;
  /**
   * Theme color variant for the icon container:
   * - "primary"  → đỏ #C62828 (Employees, People)
   * - "secondary" → xanh #1565C0 (Departments, Structure)
   * - "accent"   → amber #FF8F00 (Positions, Roles)
   * - "muted"    → neutral gray (default)
   */
  color?: "primary" | "secondary" | "accent" | "muted";
}

const iconColorMap: Record<NonNullable<StatCardProps["color"]>, string> = {
  primary:   "bg-primary/10 text-primary dark:bg-primary/15",
  secondary: "bg-secondary/10 text-secondary dark:bg-secondary/15",
  accent:    "bg-amber-500/10 text-amber-600 dark:bg-amber-500/15 dark:text-amber-400",
  muted:     "bg-secondary text-muted-foreground",
};

export function StatCard({
  title,
  value,
  icon: Icon,
  subtitle,
  loading,
  emptyLabel = "Chưa có dữ liệu",
  color = "muted",
}: StatCardProps) {
  const isEmpty = !loading && value === 0;

  return (
    <div className="rounded-xl border border-border/30 bg-card p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 space-y-1.5">
          <p className="font-label text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground">
            {title}
          </p>
          {loading ? (
            <div className="h-8 w-16 animate-pulse rounded-md bg-muted" />
          ) : (
            <p className="font-heading text-3xl font-bold tracking-tight text-foreground tabular-nums">
              {value}
            </p>
          )}
          {!loading && subtitle && (
            <p className="text-xs text-muted-foreground">{subtitle}</p>
          )}
          {isEmpty && (
            <span className="inline-block rounded-md bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
              {emptyLabel}
            </span>
          )}
        </div>
        <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${iconColorMap[color]}`}>
          <Icon className="h-5.5 w-5.5" aria-hidden="true" strokeWidth={1.5} />
        </div>
      </div>
    </div>
  );
}
