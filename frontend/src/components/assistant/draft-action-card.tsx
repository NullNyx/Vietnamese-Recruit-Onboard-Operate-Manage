"use client";

import { useState } from "react";
import { Check, X, FileEdit, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import type { DraftAction } from "@/lib/api/assistant";
import { confirmDraftAction } from "@/lib/api/assistant";

interface DraftActionCardProps {
  draft: DraftAction;
  onConfirmed?: () => void;
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
      onConfirmed();
      return;
    }
    setConfirming(true);
    try {
      const fn: (draft: DraftAction) => Promise<unknown> = confirmAction ?? confirmDraftAction;
      await fn(draft);
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

  const handleDismiss = () => {
    onDismissed?.();
  };

  if (confirmed) {
    return (
      <Card className="border-green-200 bg-green-50">
        <CardContent className="flex items-center gap-2 py-4 text-green-700">
          <Check className="h-4 w-4" />
          <span className="text-sm">Đã xác nhận và gửi thành công.</span>
        </CardContent>
      </Card>
    );
  }

  const isLeaveDraft = draft.action_type === "submit_leave_request";
  const isOvertimeDraft = draft.action_type === "submit_overtime_request";

  return (
    <Card className="border-blue-200">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm font-medium">
          <FileEdit className="h-4 w-4" />
          {isLeaveDraft
            ? "Draft — Đơn nghỉ phép"
            : isOvertimeDraft
              ? "Draft — Đơn tăng ca"
              : `Draft Action — ${draft.action_type}`}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">{draft.preview}</p>
      </CardContent>
      <CardFooter className="gap-2">
        <Button size="sm" onClick={handleConfirm} disabled={confirming}>
          {confirming ? (
            <Loader2 className="mr-1 h-3 w-3 animate-spin" />
          ) : (
            <FileEdit className="mr-1 h-3 w-3" />
          )}
          {confirmLabel}
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={handleDismiss}
          disabled={confirming}
        >
          <X className="mr-1 h-3 w-3" />
          Hủy
        </Button>
      </CardFooter>
    </Card>
  );
}
