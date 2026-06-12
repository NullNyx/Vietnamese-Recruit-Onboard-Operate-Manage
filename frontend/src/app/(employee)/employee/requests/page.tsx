"use client";

import { useState, useEffect } from "react";
import {
  CalendarDays,
  Clock,
  FileEdit,
  Loader2,
  XCircle,
} from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Tabs,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  fetchMyRequests,
  cancelLeave,
  cancelOvertime,
} from "@/lib/api/employee-requests";
import type { EmployeeRequestListItem } from "@/lib/api/employee-requests";
import { CreateRequestDialog } from "./create-request-dialog";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const REQUEST_TYPE_LABELS: Record<"leave" | "overtime", string> = {
  leave: "Nghỉ phép",
  overtime: "Tăng ca",
};

const STATUS_LABELS: Record<"submitted" | "approved" | "rejected" | "cancelled", string> = {
  submitted: "Đã gửi",
  approved: "Đã duyệt",
  rejected: "Từ chối",
  cancelled: "Đã huỷ",
};

function typeBadgeVariant(type: "leave" | "overtime"): "default" | "secondary" {
  return type === "overtime" ? "secondary" : "default";
}

function statusBadgeColor(status: "submitted" | "approved" | "rejected" | "cancelled"): string {
  switch (status) {
    case "submitted":
      return "bg-amber-500/10 text-amber-500 border-amber-500/20";
    case "approved":
      return "bg-emerald-500/10 text-emerald-500 border-emerald-500/20";
    case "rejected":
      return "bg-red-500/10 text-red-500 border-red-500/20";
    case "cancelled":
      return "bg-gray-500/10 text-gray-400 border-gray-500/20";
    default:
      return "";
  }
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "—";
  try {
    return new Date(dateStr).toLocaleDateString("vi-VN");
  } catch {
    return dateStr;
  }
}

function formatDateRange(start: string | null, end: string | null): string {
  if (!start) return "—";
  if (!end || start === end) return formatDate(start);
  return `${formatDate(start)} → ${formatDate(end)}`;
}

function formatTime(timeStr: string | null): string {
  if (!timeStr) return "—";
  try {
    return new Date(`2000-01-01T${timeStr}`).toLocaleTimeString("vi-VN", {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return timeStr;
  }
}

// ---------------------------------------------------------------------------
// Skeleton row
// ---------------------------------------------------------------------------

function RequestSkeleton() {
  return (
    <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-3 flex-1">
          <div className="flex items-center gap-2">
            <Skeleton className="h-5 w-20 rounded-full" />
            <Skeleton className="h-5 w-16 rounded-full" />
          </div>
          <Skeleton className="h-4 w-3/4" />
          <div className="flex gap-4">
            <Skeleton className="h-3 w-28" />
            <Skeleton className="h-3 w-24" />
          </div>
        </div>
        <Skeleton className="h-8 w-16 rounded-md" />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Request card
// ---------------------------------------------------------------------------

function RequestCard({
  request,
  onCancel,
}: {
  request: EmployeeRequestListItem;
  onCancel: (r: EmployeeRequestListItem) => void;
}) {
  const isOvertime = request.request_type === "overtime";

  return (
    <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 transition-colors hover:bg-white/[0.04]">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2 min-w-0 flex-1">
          {/* Badge row */}
          <div className="flex flex-wrap items-center gap-2">
            <Badge
              variant={typeBadgeVariant(request.request_type)}
              className="pointer-events-none"
            >
              {REQUEST_TYPE_LABELS[request.request_type] ?? request.request_type}
            </Badge>
            <span
              className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${statusBadgeColor(request.status)}`}
            >
              {STATUS_LABELS[request.status] ?? request.status}
            </span>
          </div>

          {/* Reason preview */}
          {request.reason && (
            <p className="text-[13px] text-[#f7f8f8] leading-relaxed line-clamp-2">
              {request.reason}
            </p>
          )}

          {/* Detail row */}
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[12px] text-[#8a8f98]">
            {isOvertime ? (
              <>
                <span className="flex items-center gap-1">
                  <CalendarDays className="h-3 w-3" />
                  {formatDate(request.work_date)}
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {formatTime(request.start_time)} → {formatTime(request.end_time)}
                </span>
              </>
            ) : (
              <>
                <span className="flex items-center gap-1">
                  <CalendarDays className="h-3 w-3" />
                  {formatDateRange(request.start_date, request.end_date)}
                </span>
                {request.leave_type && (
                  <span className="capitalize">
                    {request.leave_type === "annual"
                      ? "Nghỉ phép năm"
                      : request.leave_type === "sick"
                        ? "Nghỉ bệnh"
                        : request.leave_type === "unpaid"
                          ? "Nghỉ không lương"
                          : "Khác"}
                  </span>
                )}
              </>
            )}
            {request.duration_minutes != null && isOvertime && (
              <span>{Math.round(request.duration_minutes / 60)}h</span>
            )}
          </div>
        </div>

        {/* Cancel button — only for own submitted requests */}
        {request.status === "submitted" && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onCancel(request)}
            className="shrink-0 text-[12px] text-red-400 hover:text-red-300 hover:bg-red-500/10"
          >
            <XCircle className="mr-1 h-3.5 w-3.5" />
            Huỷ
          </Button>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Cancel dialog
// ---------------------------------------------------------------------------

function CancelDialog({
  request,
  open,
  onOpenChange,
  onConfirm,
  isPending,
}: {
  request: EmployeeRequestListItem | null;
  open: boolean;
  onOpenChange: (v: boolean) => void;
  onConfirm: (reason: string) => void;
  isPending: boolean;
}) {
  const [reason, setReason] = useState("");

  // Reset reason when dialog opens
  useEffect(() => {
    if (open) setReason("");
  }, [open]);

  const label =
    request?.request_type === "leave" ? "nghỉ phép" : "tăng ca";

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Huỷ đơn {label}</AlertDialogTitle>
          <AlertDialogDescription>
            Bạn có chắc muốn huỷ đơn {label} này? Hành động này không thể hoàn tác.
          </AlertDialogDescription>
        </AlertDialogHeader>

        <div className="space-y-2">
          <label className="text-[13px] font-medium text-[#f7f8f8]">
            Lý do huỷ
          </label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value.slice(0, 2000))}
            placeholder="Nhập lý do huỷ (không bắt buộc)..."
            rows={2}
            className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-none"
          />
        </div>

        <AlertDialogFooter>
          <AlertDialogCancel disabled={isPending}>Không, giữ lại</AlertDialogCancel>
          <AlertDialogAction
            disabled={isPending}
            onClick={(e) => {
              e.preventDefault();
              onConfirm(reason);
            }}
          >
            {isPending && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />}
            {isPending ? "Đang huỷ..." : "Xác nhận huỷ"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function EmployeeRequestsPage() {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState("all");

  // -- Cancel state --
  const [cancellingRequest, setCancellingRequest] =
    useState<EmployeeRequestListItem | null>(null);
  const cancelDialogOpen = cancellingRequest !== null;

  // -- Queries --
  const {
    data,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["employee-requests"],
    queryFn: fetchMyRequests,
    staleTime: 30_000,
  });

  // Show toast on error — wrapped in useEffect to avoid render-phase side effect
  useEffect(() => {
    if (isError && error instanceof Error) {
      toast.error(error.message || "Không thể tải yêu cầu");
    }
  }, [isError, error]);

  // -- Cancel mutation --
  const cancelMutation = useMutation({
    mutationFn: async ({
      request,
      reason,
    }: {
      request: EmployeeRequestListItem;
      reason: string;
    }) => {
      if (request.request_type === "leave") {
        return cancelLeave(request.id, reason || null);
      }
      if (request.request_type === "overtime") {
        return cancelOvertime(request.id, reason || null);
      }
      throw new Error(`Unknown request type: ${request.request_type}`);
    },
    onSuccess: () => {
      toast.success("Đã huỷ yêu cầu thành công");
      queryClient.invalidateQueries({ queryKey: ["employee-requests"] });
      setCancellingRequest(null);
    },
    onError: (err: Error) => {
      toast.error(err.message || "Huỷ yêu cầu thất bại");
    },
  });

  function handleCancelConfirm(reason: string) {
    if (!cancellingRequest) return;
    cancelMutation.mutate({ request: cancellingRequest, reason });
  }

  // -- Derived state --
  const requests = data?.requests ?? [];
  const filtered =
    filter === "all"
      ? requests
      : requests.filter((r) => r.request_type === filter);

  const emptyMessage =
    filter === "all"
      ? "Chưa có yêu cầu nào."
      : filter === "leave"
        ? "Chưa có đơn nghỉ phép nào."
        : "Chưa có đơn tăng ca nào.";

  return (
    <div className="space-y-6 max-w-[900px]">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-[24px] font-semibold tracking-[-0.3px] text-[#f7f8f8]">
            Yêu cầu của tôi
          </h1>
          <p className="text-[14px] text-[#8a8f98]">
            Đơn nghỉ phép, tăng ca và các yêu cầu khác
          </p>
        </div>
        <CreateRequestDialog />
      </div>

      {/* Filter tabs */}
      <Tabs value={filter} onValueChange={setFilter}>
        <TabsList>
          <TabsTrigger value="all">Tất cả</TabsTrigger>
          <TabsTrigger value="leave">Nghỉ phép</TabsTrigger>
          <TabsTrigger value="overtime">Tăng ca</TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Loading */}
      {isLoading && (
        <div className="space-y-3">
          <RequestSkeleton />
          <RequestSkeleton />
          <RequestSkeleton />
        </div>
      )}

      {/* Error */}
      {isError && !isLoading && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-12 text-center">
          <Loader2 className="mx-auto h-10 w-10 text-red-400" />
          <h3 className="mt-4 text-[14px] font-medium text-[#f7f8f8]">
            Không thể tải dữ liệu
          </h3>
          <p className="mt-1 text-[12px] text-[#8a8f98]">
            {error instanceof Error ? error.message : "Đã có lỗi xảy ra. Vui lòng thử lại sau."}
          </p>
        </div>
      )}

      {/* Empty */}
      {!isLoading && !isError && filtered.length === 0 && (
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-12 text-center">
          <FileEdit className="mx-auto h-10 w-10 text-[#8a8f98]" />
          <h3 className="mt-4 text-[14px] font-medium text-[#f7f8f8]">
            {emptyMessage}
          </h3>
          <p className="mt-1 text-[12px] text-[#8a8f98]">
            Các yêu cầu của bạn sẽ xuất hiện ở đây sau khi được gửi.
          </p>
        </div>
      )}

      {/* List */}
      {!isLoading && !isError && filtered.length > 0 && (
        <div className="space-y-3">
          {filtered.map((request) => (
            <RequestCard
              key={request.id}
              request={request}
              onCancel={setCancellingRequest}
            />
          ))}
        </div>
      )}

      {/* Cancel dialog */}
      <CancelDialog
        request={cancellingRequest}
        open={cancelDialogOpen}
        onOpenChange={(v) => {
          if (!v) setCancellingRequest(null);
        }}
        onConfirm={handleCancelConfirm}
        isPending={cancelMutation.isPending}
      />
    </div>
  );
}
