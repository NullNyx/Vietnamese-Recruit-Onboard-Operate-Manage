"use client";

import * as React from "react";
import {
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  XCircle,
  Loader2,
} from "lucide-react";
import type { CapabilityHealth, CapabilityHealthState } from "@/lib/api/types";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Icon helper
// ---------------------------------------------------------------------------

const healthIcons: Record<CapabilityHealthState, React.ReactNode> = {
  healthy: <CheckCircle2 className="h-4 w-4 text-green-600" />,
  unhealthy: <XCircle className="h-4 w-4 text-red-600" />,
  unknown: <HelpCircle className="h-4 w-4 text-yellow-600" />,
  unavailable: <AlertTriangle className="h-4 w-4 text-muted-foreground" />,
};

const healthColors: Record<
  CapabilityHealthState,
  { border: string; bg: string; text: string }
> = {
  healthy: { border: "border-green-200", bg: "bg-green-50", text: "text-green-800" },
  unhealthy: { border: "border-red-200", bg: "bg-red-50", text: "text-red-800" },
  unknown: { border: "border-yellow-200", bg: "bg-yellow-50", text: "text-yellow-800" },
  unavailable: { border: "border-border", bg: "bg-card", text: "text-muted-foreground" },
};

const healthLabels: Record<CapabilityHealthState, string> = {
  healthy: "Healthy",
  unhealthy: "Unhealthy",
  unknown: "Unknown",
  unavailable: "Unavailable",
};

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface CapabilityHealthCardsProps {
  capabilities: CapabilityHealth[];
  loading?: boolean;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function CapabilityHealthCards({
  capabilities,
  loading = false,
}: CapabilityHealthCardsProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center rounded-lg border border-border bg-card p-4">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        <span className="ml-2 text-sm text-muted-foreground">
          Đang kiểm tra trạng thái dịch vụ...
        </span>
      </div>
    );
  }

  if (capabilities.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2">
      {capabilities.map((cap) => {
        const colors = healthColors[cap.health];
        return (
          <div
            key={cap.capability}
            className={cn(
              "flex items-center gap-2 rounded-lg border px-3 py-2",
              colors.border,
              colors.bg,
            )}
          >
            {healthIcons[cap.health]}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                <span className={cn("text-xs font-medium", colors.text)}>
                  {cap.label}
                </span>
                <span
                  className={cn(
                    "text-[10px] px-1.5 py-0.5 rounded-full",
                    colors.bg,
                    colors.text,
                  )}
                >
                  {healthLabels[cap.health]}
                </span>
              </div>
              {cap.description && (
                <p className="text-[10px] text-muted-foreground mt-0.5">
                  {cap.description}
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
