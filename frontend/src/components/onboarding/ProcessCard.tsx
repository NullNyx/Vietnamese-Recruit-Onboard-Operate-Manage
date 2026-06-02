"use client";

import { cn } from "@/lib/utils";
import type { OnboardingProcess } from "@/lib/api/onboarding";

interface ProcessCardProps {
  process: OnboardingProcess;
  selected: boolean;
  onClick: () => void;
}

function Progress({ value }: { value: number }) {
  return (
    <div className="h-1.5 w-full rounded-full bg-secondary overflow-hidden">
      <div
        className="h-full bg-primary transition-all duration-300 ease-in-out"
        style={{ width: `${value}%` }}
      />
    </div>
  );
}

function Badge({ status }: { status: OnboardingProcess["status"] }) {
  const styles = {
    in_progress: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
    complete: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400",
  } as const;

  const labels = { in_progress: "Đang làm", complete: "Hoàn thành" } as const;

  return (
    <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium", styles[status])}>
      {labels[status]}
    </span>
  );
}

export function ProcessCard({ process, selected, onClick }: ProcessCardProps) {
  const pct = process.total_count > 0
    ? Math.round((process.completed_count / process.total_count) * 100)
    : 0;

  const initials = process.employee_full_name
    .split(" ")
    .slice(-2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();

  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full text-left rounded-xl border bg-card p-4 space-y-3 transition-all duration-150",
        "hover:shadow-sm hover:border-primary/20",
        selected && "border-primary shadow-sm ring-1 ring-primary/20",
      )}
    >
      <div className="flex items-start gap-3">
        {/* Avatar */}
        <div className="size-9 rounded-lg bg-muted flex items-center justify-center text-xs font-medium text-muted-foreground shrink-0">
          {initials || "?"}
        </div>

        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate">
            {process.employee_full_name || `NV ${process.employee_id.slice(0, 8)}`}
          </p>
          {process.employee_code && (
            <p className="text-xs text-muted-foreground mt-0.5">{process.employee_code}</p>
          )}
        </div>

        <Badge status={process.status} />
      </div>

      <div className="space-y-1.5">
        <Progress value={pct} />
        <p className="text-[11px] text-muted-foreground text-right">
          {process.completed_count}/{process.total_count}
        </p>
      </div>
    </button>
  );
}
