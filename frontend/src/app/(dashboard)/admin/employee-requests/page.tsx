"use client";

import { useState } from "react";
import {
  CheckCircle,
  ClipboardList,
  Loader2,
  XCircle,
} from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  fetchSubmittedRequests,
  approveRequest,
  rejectRequest,
} from "@/lib/api/employee-requests";
import type { AdminEmployeeRequestItem } from "@/lib/api/employee-requests";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const REQUEST_TYPE_LABELS: Record<string, string> = {
  leave: "Nghỉ phép",
  overtime: "Tăng ca",
};

function statusBadgeColor(status: string): string {
  switch (status) {
    case "submitted":
      return "bg-amber-500/10 text-amber-500 border-amber-500/20";
    case "approved":
      return "bg-emerald-500/10 text-emerald-500 border-emerald-500/20";
    case "rejected":
      return "bg-red-500/10 text-red-500 border-destructive/20";
    case "cancelled":
      return "bg-gray-500/10 text-gray-400 border-gray-500/20";
    default:
      return "";
  }
}

function typeBadgeVariant(type: string): "default" | "secondary" {
  return type === "overtime" ? "secondary" : "default";
}

function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return "—";
  try {
    return new Date(dateStr).toLocaleString("vi-VN");
  } catch {
    return dateStr;
  }
}

// ---------------------------------------------------------------------------
// Skeleton rows
// ---------------------------------------------------------------------------

function ReviewSkeleton() {
  return (
    <div className="rounded-xl border border-border/50 bg-card/50 p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-3 flex-1">
          <div className="flex items-center gap-2">
            <Skeleton className="h-5 w-24 rounded-full" />
            <Skeleton className="h-5 w-16 rounded-full" />
            <Skeleton className="h-5 w-20 rounded-full" />
          </div>
          <Skeleton className="h-4 w-3/4" />
          <div className="flex gap-4">
            <Skeleton className="h-3 w-28" />
            <Skeleton className="h-3 w-24" />
          </div>
        </div>
        <div className="flex gap-2">
          <Skeleton className="h-8 w-20 rounded-md" />
          <Skeleton className="h-8 w-20 rounded-md" />
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Review card
// ---------------------------------------------------------------------------

function ReviewCard({
  request,
  onReview,
}: {
  request: AdminEmployeeRequestItem;
  onReview: (r: AdminEmployeeRequestItem, action: "approve" | "reject") => void;
}) {
  const isOvertime = request.request_type === "overtime";
  const dateInfo = isOvertime
    ? `Ngày làm: ${formatDateTime(request.work_date)}`
    : `${formatDateTime(request.start_date)} → ${formatDateTime(request.end_date)}`;

  return (
    <div className="rounded-xl border border-border/50 bg-card/50 p-5 transition-colors hover:bg-accent/50">
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
              Đã gửi
            </span>
            <span className="text-[12px] text-muted-foreground">
              {request.employee_name}
            </span>
          </div>

          {/* Reason preview */}
          {request.reason && (
            <p className="text-[13px] text-foreground leading-relaxed line-clamp-2">
              {request.reason}
            </p>
          )}

          {/* Date + submitted time */}
          <div className="flex items-center gap-4 text-[12px] text-muted-foreground">
            <span>{dateInfo}</span>
            <span>Gửi lúc: {formatDateTime(request.submitted_at)}</span>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex flex-col gap-2 shrink-0">
          <Button
            size="sm"
            variant="default"
            className="bg-emerald-600 hover:bg-emerald-500 text-white text-[12px] h-8 px-4"
            onClick={() => onReview(request, "approve")}
          >
            <CheckCircle className="h-3.5 w-3.5 mr-1.5" />
            Duyệt
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="border-red-500/30 text-destructive hover:bg-red-500/10 text-[12px] h-8 px-4"
            onClick={() => onReview(request, "reject")}
          >
            <XCircle className="h-3.5 w-3.5 mr-1.5" />
            Từ chối
          </Button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Confirm dialog
// ---------------------------------------------------------------------------

function ConfirmReviewDialog({
  request,
  action,
  open,
  onOpenChange,
  onConfirm,
  isPending,
  reviewReason,
  onReviewReasonChange,
}: {
  request: AdminEmployeeRequestItem | null;
  action: "approve" | "reject" | null;
  open: boolean;
  onOpenChange: (v: boolean) => void;
  onConfirm: () => void;
  isPending: boolean;
  reviewReason: string;
  onReviewReasonChange: (v: string) => void;
}) {
  if (!request || !action) return null;

  const isApprove = action === "approve";
  const title = isApprove ? "Duyệt yêu cầu" : "Từ chối yêu cầu";
  const description = isApprove
    ? `Bạn có chắc muốn duyệt yêu cầu ${REQUEST_TYPE_LABELS[request.request_type]?.toLowerCase() ?? request.request_type} của ${request.employee_name}?`
    : `Bạn có chắc muốn từ chối yêu cầu ${REQUEST_TYPE_LABELS[request.request_type]?.toLowerCase() ?? request.request_type} của ${request.employee_name}?`;

  const reasonRequired = !isApprove;
  const reasonLabel = isApprove ? "Lý do (không bắt buộc)" : "Lý do từ chối (bắt buộc)";
  const reasonPlaceholder = isApprove
    ? "Nhập lý do duyệt (nếu có)..."
    : "Nhập lý do từ chối...";
  const reasonError = reasonRequired && reviewReason.trim().length === 0;

  function handleActionClick(e: React.MouseEvent) {
    e.preventDefault();
    if (reasonRequired && reviewReason.trim().length === 0) {
      toast.error("Vui lòng nhập lý do từ chối");
      return;
    }
    onConfirm();
  }

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          <AlertDialogDescription>{description}</AlertDialogDescription>
        </AlertDialogHeader>
        <div className="space-y-2 px-6">
          <Label htmlFor="review-reason" className="text-[13px]">
            {reasonLabel}
          </Label>
          <Textarea
            id="review-reason"
            value={reviewReason}
            onChange={(e) => onReviewReasonChange(e.target.value)}
            placeholder={reasonPlaceholder}
            className={reasonError ? "border-red-500" : ""}
            disabled={isPending}
            rows={3}
          />
        </div>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isPending}>Huỷ</AlertDialogCancel>
          <Button
            type="button"
            onClick={handleActionClick}
            disabled={isPending}
            className={
              isApprove
                ? "bg-emerald-600 hover:bg-emerald-500 text-white"
                : "bg-red-600 hover:bg-red-500 text-white"
            }
          >
            {isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            {isApprove ? "Xác nhận duyệt" : "Xác nhận từ chối"}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function AdminEmployeeRequestsPage() {
  const queryClient = useQueryClient();

  // -- Review dialog state --
  const [reviewTarget, setReviewTarget] = useState<{
    request: AdminEmployeeRequestItem;
    action: "approve" | "reject";
  } | null>(null);
  const [reviewReason, setReviewReason] = useState("");
  const reviewDialogOpen = reviewTarget !== null;

  // -- Query --
  const {
    data,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["admin-employee-requests"],
    queryFn: fetchSubmittedRequests,
    refetchInterval: 30_000,
  });

  // -- Approve mutation --
  const approveMutation = useMutation({
    mutationFn: async ({
      request,
      reason,
    }: {
      request: AdminEmployeeRequestItem;
      reason: string;
    }) => {
      return approveRequest(request.id, reason || null);
    },
    onSuccess: () => {
      toast.success("Đã duyệt yêu cầu thành công");
      queryClient.invalidateQueries({ queryKey: ["admin-employee-requests"] });
      setReviewTarget(null);
      setReviewReason("");
    },
    onError: (err: Error) => {
      toast.error(err.message || "Duyệt yêu cầu thất bại");
    },
  });

  // -- Reject mutation --
  const rejectMutation = useMutation({
    mutationFn: async ({
      request,
      reason,
    }: {
      request: AdminEmployeeRequestItem;
      reason: string;
    }) => {
      return rejectRequest(request.id, reason);
    },
    onSuccess: () => {
      toast.success("Đã từ chối yêu cầu");
      queryClient.invalidateQueries({ queryKey: ["admin-employee-requests"] });
      setReviewTarget(null);
      setReviewReason("");
    },
    onError: (err: Error) => {
      toast.error(err.message || "Từ chối yêu cầu thất bại");
    },
  });

  function handleReviewClick(
    request: AdminEmployeeRequestItem,
    action: "approve" | "reject",
  ) {
    setReviewTarget({ request, action });
    setReviewReason("");
  }

  function handleConfirm() {
    if (!reviewTarget) return;
    const { request, action } = reviewTarget;
    const trimmedReason = reviewReason.trim();
    if (action === "approve") {
      approveMutation.mutate({ request, reason: trimmedReason });
    } else {
      rejectMutation.mutate({ request, reason: trimmedReason });
    }
  }

  const isPending = approveMutation.isPending || rejectMutation.isPending;
  const requests = data?.requests ?? [];

  return (
    <div className="space-y-6 max-w-[1000px]">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-[24px] font-semibold tracking-[-0.3px] text-foreground">
            Yêu cầu chờ duyệt
          </h1>
          <p className="text-[14px] text-muted-foreground">
            Duyệt hoặc từ chối đơn nghỉ phép và tăng ca từ nhân viên
          </p>
        </div>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="space-y-3">
          <ReviewSkeleton />
          <ReviewSkeleton />
          <ReviewSkeleton />
        </div>
      )}

      {/* Error */}
      {isError && !isLoading && (
        <div className="rounded-xl border border-destructive/20 bg-destructive/10 p-12 text-center">
          <Loader2 className="mx-auto h-10 w-10 text-destructive" />
          <h3 className="mt-4 text-[14px] font-medium text-foreground">
            Không thể tải dữ liệu
          </h3>
          <p className="mt-1 text-[12px] text-muted-foreground">
            {error instanceof Error ? error.message : "Đã có lỗi xảy ra. Vui lòng thử lại sau."}
          </p>
        </div>
      )}

      {/* Empty */}
      {!isLoading && !isError && requests.length === 0 && (
        <div className="rounded-xl border border-border/50 bg-card/50 p-12 text-center">
          <ClipboardList className="mx-auto h-10 w-10 text-muted-foreground" />
          <h3 className="mt-4 text-[14px] font-medium text-foreground">
            Không có yêu cầu nào
          </h3>
          <p className="mt-1 text-[12px] text-muted-foreground">
            Tất cả yêu cầu đã được xử lý. Yêu cầu mới sẽ xuất hiện ở đây.
          </p>
        </div>
      )}

      {/* List */}
      {!isLoading && !isError && requests.length > 0 && (
        <div className="space-y-3">
          {requests.map((request) => (
            <ReviewCard
              key={request.id}
              request={request}
              onReview={handleReviewClick}
            />
          ))}
        </div>
      )}

      {/* Confirm dialog */}
      <ConfirmReviewDialog
        request={reviewTarget?.request ?? null}
        action={reviewTarget?.action ?? null}
        open={reviewDialogOpen}
        onOpenChange={(v) => {
          if (!v) {
            setReviewTarget(null);
            setReviewReason("");
          }
        }}
        onConfirm={handleConfirm}
        isPending={isPending}
        reviewReason={reviewReason}
        onReviewReasonChange={setReviewReason}
      />
    </div>
  );
}
