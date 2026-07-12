"use client";

import * as React from "react";
import {
  Calendar,
  CalendarClock,
  Clock,
  Globe,
  CheckCircle2,
  XCircle,
  RefreshCw,
  User,
  Mail,
  Loader2,
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
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Separator } from "@/components/ui/separator";
import type { InterviewResponse } from "@/lib/api/recruitment";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const INTERVIEW_STATUS_LABELS: Record<string, string> = {
  scheduled: "Đã lên lịch",
  completed: "Đã hoàn thành",
  cancelled: "Đã hủy",
};

const INTERVIEW_STATUS_COLORS: Record<string, string> = {
  scheduled:
    "bg-blue-100 text-blue-800",
  completed:
    "bg-green-100 text-green-800",
  cancelled:
    "bg-gray-100 text-gray-800",
};

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface InterviewListProps {
  interviews: InterviewResponse[];
  candidateId: string;
  /** Called to create a replacement interview after cancellation. */
  onReplacement?: (interview: InterviewResponse) => void;
  /** Called to complete a scheduled interview. */
  onComplete?: (interview: InterviewResponse) => void;
  /** Called to cancel a scheduled interview. */
  onCancel?: (interview: InterviewResponse) => void;
  /** Loading state for actions. */
  actionLoading?: boolean;
  /** Currently loading interview ID for action. */
  loadingInterviewId?: string | null;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatInterviewDate(isoString: string): string {
  if (!isoString) return "";
  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) return "";
  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const year = date.getFullYear();
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${day}/${month}/${year} ${hours}:${minutes}`;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function InterviewList({
  interviews,
  onReplacement,
  onComplete,
  onCancel,
  actionLoading = false,
  loadingInterviewId,
}: InterviewListProps) {
  if (interviews.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <CalendarClock className="h-5 w-5" />
            Lịch phỏng vấn
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Chưa có lịch phỏng vấn nào.
          </p>
        </CardContent>
      </Card>
    );
  }

  const sorted = [...interviews].sort(
    (a, b) => new Date(b.start_at).getTime() - new Date(a.start_at).getTime(),
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <CalendarClock className="h-5 w-5" />
          Lịch phỏng vấn
        </CardTitle>
        <CardDescription>
          {interviews.length} buổi phỏng vấn
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {sorted.map((interview) => {
            const isScheduled = interview.status === "scheduled";
            const isCancelled = interview.status === "cancelled";
          const isLoading = loadingInterviewId === interview.id && actionLoading;
          const statusLabel = INTERVIEW_STATUS_LABELS[interview.status] ?? interview.status;
          const statusColor = INTERVIEW_STATUS_COLORS[interview.status] ?? "bg-gray-100 text-gray-800";

          return (
            <div
              key={interview.id}
              className={`rounded-md border p-4 transition-colors ${
                isCancelled ? "opacity-60" : ""
              }`}
            >
              {/* Header: round name + status */}
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <h4 className="truncate text-sm font-semibold">
                    {interview.round_name}
                  </h4>
                </div>
                <Badge className={statusColor}>{statusLabel}</Badge>
              </div>

              {/* Details */}
              <div className="mt-2 space-y-1.5 text-sm text-muted-foreground">
                {/* Start/End */}
                <div className="flex items-center gap-2">
                  <Clock className="h-3.5 w-3.5 shrink-0" />
                  <span>
                    {formatInterviewDate(interview.start_at)}
                    {" — "}
                    {formatInterviewDate(interview.end_at)}
                  </span>
                </div>

                {/* Timezone */}
                <div className="flex items-center gap-2">
                  <Globe className="h-3.5 w-3.5 shrink-0" />
                  <span>{interview.timezone}</span>
                </div>

                {/* Calendar event link */}
                {interview.calendar_event_id && (
                  <div className="flex items-center gap-2">
                    <Calendar className="h-3.5 w-3.5 shrink-0" />
                    <span className="truncate text-xs font-mono">
                      ID: {interview.calendar_event_id}
                    </span>
                  </div>
                )}

                {interview.needs_relink && (
                  <Badge variant="outline" className="text-amber-600 border-amber-300 bg-amber-50">
                    Cần cập nhật lịch
                  </Badge>
                )}
              </div>

              {/* Participants */}
              {interview.participants.length > 0 && (
                <div className="mt-3">
                  <Separator className="mb-2" />
                  <p className="mb-1 text-xs font-medium text-muted-foreground">
                    Người tham gia ({interview.participants.length})
                  </p>
                  <div className="space-y-1">
                    {interview.participants.map((p) => (
                      <div
                        key={p.id}
                        className="flex items-center gap-2 text-xs text-muted-foreground"
                      >
                        {p.type === "candidate" && <User className="h-3 w-3 shrink-0" />}
                        {p.type === "employee" && <User className="h-3 w-3 shrink-0" />}
                        {p.type === "external" && <Mail className="h-3 w-3 shrink-0" />}
                        <span className="truncate">{p.name ?? p.email}</span>
                        {p.email && p.name && (
                          <span className="truncate text-[10px] opacity-60">
                            ({p.email})
                          </span>
                        )}
                        {p.type === "candidate" && (
                          <Badge variant="outline" className="text-[10px] px-1 py-0">
                            UV
                          </Badge>
                        )}
                        {p.type === "employee" && (
                          <Badge variant="outline" className="text-[10px] px-1 py-0">
                            PV
                          </Badge>
                        )}
                        {p.type === "external" && (
                          <Badge variant="outline" className="text-[10px] px-1 py-0">
                            Ngoài
                          </Badge>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Action buttons */}
              {isScheduled && (onComplete || onCancel) && (
                <div className="mt-3 flex flex-wrap gap-2">
                  <TooltipProvider>
                    {onComplete && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => onComplete(interview)}
                            disabled={actionLoading}
                            className="gap-1.5"
                          >
                            {isLoading ? (
                              <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            ) : (
                              <CheckCircle2 className="h-3.5 w-3.5" />
                            )}
                            Hoàn thành
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                          Đánh dấu buổi phỏng vấn đã hoàn thành
                        </TooltipContent>
                      </Tooltip>
                    )}
                    {onCancel && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => onCancel(interview)}
                            disabled={actionLoading}
                            className="gap-1.5 text-destructive hover:text-destructive"
                          >
                            {isLoading ? (
                              <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            ) : (
                              <XCircle className="h-3.5 w-3.5" />
                            )}
                            Hủy
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                          Hủy buổi phỏng vấn (gửi thông báo hủy qua Calendar)
                        </TooltipContent>
                      </Tooltip>
                    )}
                  </TooltipProvider>
                </div>
              )}

              {/* Replacement action for cancelled interviews */}
              {isCancelled && onReplacement && (
                <div className="mt-3">
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => onReplacement(interview)}
                          disabled={actionLoading}
                          className="gap-1.5"
                        >
                          {isLoading ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <RefreshCw className="h-3.5 w-3.5" />
                          )}
                          Đặt lịch thay thế
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>
                        Tạo buổi phỏng vấn mới thay thế cho buổi đã hủy
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </div>
              )}
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
