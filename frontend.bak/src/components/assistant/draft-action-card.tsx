"use client";

import { useState } from "react";
import { Check, X, FileEdit, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import type { DraftAction } from "@/lib/api/assistant";
import { confirmDraftAction, recordDraftDecision } from "@/lib/api/assistant";

interface DraftActionCardProps {
  draft: DraftAction;
  onConfirmed?: () => void | Promise<void>;
  onDismissed?: () => void;
  /** Optional custom confirm function. Defaults to HR confirm endpoint. */
  confirmAction?: (draft: DraftAction) => Promise<unknown>;
  /** Custom confirm button label (defaults to "Xác nhận") */
  confirmLabel?: string;
}

export function DraftActionCard({
  draft,
  onConfirmed,
  onDismissed,
  confirmAction,
  confirmLabel = "Xác nhận",
}: DraftActionCardProps) {
  const [confirming, setConfirming] = useState(false);
  const [confirmed, setConfirmed] = useState(false);

  const handleConfirm = async () => {
    if (onConfirmed) {
      // Prefill/redirect mode — no direct API call
      setConfirming(true);
      try {
        await onConfirmed();
        setConfirmed(true);
      } finally {
        setConfirming(false);
      }
      return;
    }
    setConfirming(true);
    try {
      const fn: (draft: DraftAction) => Promise<unknown> = confirmAction ?? confirmDraftAction;
      await fn(draft);
      await recordDraftDecision(draft, "confirm");
      setConfirmed(true);
      toast.success("Đã gửi thành công!");
      
    } catch (err) {
      toast.error(
        `Gửi thất bại: ${
          err instanceof Error ? err.message : "Lỗi không xác định"
        }`,
      );
    } finally {
      setConfirming(false);
    }
  };

  const handleDismiss = async () => {
    if (!onDismissed) {
      try {
        await recordDraftDecision(draft, "reject");
      } catch (err) {
        toast.error(
          `Không thể ghi nhận từ chối: ${err instanceof Error ? err.message : "Lỗi không xác định"}`,
        );
      }
    }
    onDismissed?.();
  };

      if (confirmed) {
        return (
          <Card className="border-success/30 bg-success/5">
            <CardContent className="flex items-center gap-2 py-4 text-success">
              <Check className="h-4 w-4" />
              <span className="text-sm font-medium">Đã xác nhận và gửi thành công.</span>
            </CardContent>
          </Card>
        );
      }

      const isLeaveDraft = draft.action_type === "submit_leave_request";
      const isOvertimeDraft = draft.action_type === "submit_overtime_request";

      return (
        <Card className="border-l-4 border-primary shadow-sm rounded-r-xl">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm font-medium text-foreground">
              <div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary/10">
                <FileEdit className="h-3.5 w-3.5 text-primary" />
              </div>
              {isLeaveDraft
                ? "Draft — Đơn nghỉ phép"
                : isOvertimeDraft
                  ? "Draft — Đơn tăng ca"
                  : `Draft Action — ${draft.action_type}`}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground leading-relaxed">{draft.preview}</p>
          </CardContent>
          <CardFooter className="gap-2">
            <Button size="sm" onClick={handleConfirm} disabled={confirming} className="shadow-sm">
              {confirming ? (
                <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
              ) : (
                <FileEdit className="mr-1.5 h-3.5 w-3.5" />
              )}
              {confirmLabel}
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={handleDismiss}
              disabled={confirming}
              className="border-border/60 hover:bg-muted"
            >
              <X className="mr-1.5 h-3.5 w-3.5" />
              Hủy
            </Button>
          </CardFooter>
        </Card>
      );
}
