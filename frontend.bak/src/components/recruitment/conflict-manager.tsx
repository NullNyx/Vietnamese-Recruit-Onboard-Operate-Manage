"use client";

import * as React from "react";
import {
  AlertTriangle,
  Loader2,
  CheckCircle2,
  RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { toast } from "sonner";
import type { CalendarConflict } from "@/lib/api/recruitment";
import { resolveCalendarConflict } from "@/lib/api/recruitment";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface ConflictManagerProps {
  conflicts: CalendarConflict[];
  onConflictResolved?: (conflict: CalendarConflict) => void;
  loading?: boolean;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ConflictManager({
  conflicts,
  onConflictResolved,
  loading = false,
}: ConflictManagerProps) {
  const [resolveDialog, setResolveDialog] = React.useState<{
    open: boolean;
    conflict: CalendarConflict | null;
    choice: "keep_google" | "overwrite_vroom";
  }>({ open: false, conflict: null, choice: "keep_google" });
  const [resolving, setResolving] = React.useState(false);

  const unresolved = conflicts.filter((c) => c.status === "unresolved");

  if (unresolved.length === 0) {
    return null;
  }

  async function handleResolve() {
    if (!resolveDialog.conflict) return;
    setResolving(true);
    try {
      const resolved = await resolveCalendarConflict(
        resolveDialog.conflict.id,
        { choice: resolveDialog.choice },
      );
      toast.success(
        resolveDialog.choice === "keep_google"
          ? "Đã giữ lịch Google Calendar"
          : "Đã cập nhật lịch Google Calendar",
      );
      onConflictResolved?.(resolved);
      setResolveDialog({ open: false, conflict: null, choice: "keep_google" });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Không thể giải quyết xung đột";
      toast.error(message);
    } finally {
      setResolving(false);
    }
  }

  return (
    <>
      <Card className="border-amber-300">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            Xung đột lịch ({unresolved.length})
          </CardTitle>
          <CardDescription>
            Lịch trên Google Calendar đã thay đổi. Chọn cách giải quyết cho từng
            xung đột.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {unresolved.map((conflict) => (
            <div
              key={conflict.id}
              className="rounded-md border border-amber-200 bg-amber-50/50 p-3"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1 space-y-1">
                  <p className="text-xs font-medium text-muted-foreground">
                    Xung đột Calendar
                  </p>
                  <p className="truncate text-xs font-mono text-muted-foreground">
                    Event: {conflict.calendar_event_id}
                  </p>
                      {(conflict.conflict_details?.etag_mismatch as boolean) && (
                      
                    <Badge
                      variant="outline"
                      className="text-amber-600 border-amber-300"
                    >
                      ETag mismatch
                    </Badge>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      setResolveDialog({
                        open: true,
                        conflict,
                        choice: "keep_google",
                      })
                    }
                    disabled={resolving || loading}
                    className="gap-1.5 text-xs"
                  >
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    Giữ Google
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      setResolveDialog({
                        open: true,
                        conflict,
                        choice: "overwrite_vroom",
                      })
                    }
                    disabled={resolving || loading}
                    className="gap-1.5 text-xs"
                  >
                    <RefreshCw className="h-3.5 w-3.5" />
                    Ghi đè
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Resolve confirmation dialog */}
      <AlertDialog
        open={resolveDialog.open}
        onOpenChange={(open) => {
          if (!open && !resolving) {
            setResolveDialog({ open: false, conflict: null, choice: "keep_google" });
          }
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Giải quyết xung đột lịch</AlertDialogTitle>
            <AlertDialogDescription>
              {resolveDialog.choice === "keep_google"
                ? "Cập nhật dữ liệu Vroom để khớp với lịch trên Google Calendar. Mọi thay đổi trên Google sẽ được giữ nguyên."
                : "Ghi đè lịch Google Calendar bằng dữ liệu hiện tại của Vroom. Lịch trên Google sẽ được cập nhật."}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <Button
              variant="outline"
              onClick={() =>
                setResolveDialog({
                  open: false,
                  conflict: null,
                  choice: "keep_google",
                })
              }
              disabled={resolving}
            >
              Hủy
            </Button>
            <Button
              variant={resolveDialog.choice === "overwrite_vroom" ? "default" : "secondary"}
              onClick={handleResolve}
              disabled={resolving}
            >
              {resolving && <Loader2 className="animate-spin" />}
              {resolveDialog.choice === "keep_google"
                ? "Giữ lịch Google"
                : "Ghi đè bằng Vroom"}
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
