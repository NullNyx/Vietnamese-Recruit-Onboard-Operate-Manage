"use client";

import { cn } from "@/lib/utils";
import type { OnboardingProcess } from "@/lib/api/onboarding";
import { AlertCircle, CheckCircle2, Clock, Check } from "lucide-react";

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

function getReadiness(process: OnboardingProcess) {
  if (process.status === "complete") {
    return {
      badgeText: "Hoàn thành",
      badgeColor: "bg-emerald-100 text-emerald-700",
      icon: Check,
      hint: "Đã kích hoạt",
    };
  }

  const isSetupMissing = process.missing_setup_fields && process.missing_setup_fields.length > 0;
  const tasksRemaining = process.total_count - process.completed_count;
  
  if (isSetupMissing) {
    const fieldMap: Record<string, string> = {
      department: "phòng ban",
      position: "chức vụ",
      start_date: "ngày bắt đầu"
    };
    const missingCount = process.missing_setup_fields.length;
    const firstMissing = fieldMap[process.missing_setup_fields[0]] || process.missing_setup_fields[0];
    
    return {
      badgeText: "Thiếu Setup",
      badgeColor: "bg-amber-100 text-amber-700",
      icon: AlertCircle,
      hint: missingCount > 1 ? `Thiếu ${firstMissing} & ${missingCount - 1} mục` : `Thiếu ${firstMissing}`,
    };
  }

  if (tasksRemaining > 0) {
    return {
      badgeText: "Đang xử lý",
      badgeColor: "bg-blue-100 text-blue-700",
      icon: Clock,
      hint: `Còn ${tasksRemaining} task`,
    };
  }

  return {
    badgeText: "Sẵn sàng",
    badgeColor: "bg-emerald-100 text-emerald-800 border border-emerald-300",
    icon: CheckCircle2,
    hint: "Có thể kích hoạt ngay",
  };
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

  const readiness = getReadiness(process);
  const Icon = readiness.icon;

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

        <span className={cn("inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium shrink-0", readiness.badgeColor)}>
          <Icon className="size-3" />
          {readiness.badgeText}
        </span>
      </div>

      <div className="space-y-1.5">
        <Progress value={pct} />
        <div className="flex items-center justify-between">
          <p className="text-[11px] font-medium text-muted-foreground">
            {readiness.hint}
          </p>
          <p className="text-[11px] text-muted-foreground text-right">
            {process.completed_count}/{process.total_count}
          </p>
        </div>
      </div>
    </button>
  );
}
