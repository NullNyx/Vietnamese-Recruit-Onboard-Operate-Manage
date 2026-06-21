"use client";

import { useState } from "react";
import {
  CheckCircle,
  ClipboardList,
  Loader2,
  XCircle,
  RotateCcw,
} from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
import { listEmployees } from "@/lib/api/employees";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const REQUEST_TYPE_LABELS: Record<string, string> = {
  leave: "Nghỉ phép",
  overtime: "Tăng ca",
};

const STATUS_LABELS: Record<string, string> = {
  submitted: "Chờ duyệt",
  approved: "Đã duyệt",
  rejected: "Đã từ chối",
  cancelled: "Đã huỷ",
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
              {STATUS_LABELS[request.status] ?? request.status}
            </span>
            <span className="text-[12px] text-muted-foreground font-medium">
              {request.employee_name}
            </span>
          </div>

          {/* Reason preview */}
          {request.reason && (
            <p className="text-[13px] text-foreground leading-relaxed">
              <span className="font-medium text-muted-foreground">Lý do gửi: </span>
              {request.reason}
            </p>
          )}

          {/* Date + submitted time */}
          <div className="flex items-center gap-4 text-[12px] text-muted-foreground">
            <span>{dateInfo}</span>
            <span>Gửi lúc: {formatDateTime(request.submitted_at)}</span>
          </div>

          {/* Decision details */}
          {(request.status === "approved" || request.status === "rejected") && (
            <div className="mt-3 pt-3 border-t border-border/40 text-[12px] space-y-1 bg-muted/40 p-3 rounded-lg">
              <div className="font-semibold text-foreground flex items-center gap-1.5">
                {request.status === "approved" ? (
                  <CheckCircle className="h-4 w-4 text-emerald-500" />
                ) : (
                  <XCircle className="h-4 w-4 text-destructive" />
                )}
                {request.status === "approved" ? "Đã duyệt" : "Đã từ chối"}
                {request.reviewed_at && (
                  <span className="font-normal text-muted-foreground text-[11px]">
                    • {formatDateTime(request.reviewed_at)}
                  </span>
                )}
              </div>
              {request.review_reason && (
                <p className="text-[12px] text-muted-foreground italic pl-5.5">
                  &ldquo;{request.review_reason}&rdquo;
                </p>
              )}
            </div>
          )}

          {request.status === "cancelled" && (
            <div className="mt-3 pt-3 border-t border-border/40 text-[12px] space-y-1 bg-muted/40 p-3 rounded-lg">
              <div className="font-semibold text-foreground">Nhân viên đã huỷ yêu cầu</div>
              {request.cancellation_reason && (
                <p className="text-[12px] text-muted-foreground italic">
                  Lý do huỷ: &ldquo;{request.cancellation_reason}&rdquo;
                </p>
              )}
            </div>
          )}
        </div>

        {/* Action buttons */}
        {request.status === "submitted" && (
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
        )}
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

  // -- Filter states --
  const [requestType, setRequestType] = useState<"all" | "leave" | "overtime">("all");
  const [status, setStatus] = useState<"submitted" | "approved" | "rejected" | "cancelled">("submitted");
  const [dateFrom, setDateFrom] = useState<string>("");
  const [dateTo, setDateTo] = useState<string>("");
  const [employeeId, setEmployeeId] = useState<string>("all");

  // -- Fetch employees for filtering --
  const { data: employeesData } = useQuery({
    queryKey: ["employees-for-filter"],
    queryFn: () => listEmployees({ is_active: true, page_size: 100 }),
  });
  const employees = employeesData?.items ?? [];

  // -- Query --
  const {
    data,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["admin-employee-requests", requestType, status, dateFrom, dateTo, employeeId],
    queryFn: () =>
      fetchSubmittedRequests({
        request_type: requestType === "all" ? null : requestType,
        status: status,
        date_from: dateFrom || null,
        date_to: dateTo || null,
        employee_id: employeeId === "all" ? null : employeeId,
      }),
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

  function handleResetFilters() {
    setRequestType("all");
    setStatus("submitted");
    setDateFrom("");
    setDateTo("");
    setEmployeeId("all");
  }

  const isPending = approveMutation.isPending || rejectMutation.isPending;
  const requests = data?.requests ?? [];

  return (
    <div className="space-y-6 max-w-[1000px]">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-[24px] font-semibold tracking-[-0.3px] text-foreground">
            Quản lý yêu cầu nhân viên
          </h1>
          <p className="text-[14px] text-muted-foreground">
            Duyệt, từ chối hoặc lọc đơn nghỉ phép và tăng ca từ nhân viên
          </p>
        </div>
      </div>

      {/* Filter Toolbar */}
      <Card className="border-border/50 bg-card/50">
        <CardContent className="pt-6">
          <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
            {/* Request Type */}
            <div className="space-y-2">
              <Label className="text-[13px] font-medium text-foreground">Loại yêu cầu</Label>
              <Select
                value={requestType}
                onValueChange={(val) => setRequestType(val as "all" | "leave" | "overtime")}
              >
                <SelectTrigger className="h-9">
                  <SelectValue placeholder="Tất cả" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tất cả</SelectItem>
                  <SelectItem value="leave">Nghỉ phép</SelectItem>
                  <SelectItem value="overtime">Tăng ca</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Status */}
            <div className="space-y-2">
              <Label className="text-[13px] font-medium text-foreground">Trạng thái</Label>
              <Select
                value={status}
                onValueChange={(val) => setStatus(val as "submitted" | "approved" | "rejected" | "cancelled")}
              >
                <SelectTrigger className="h-9">
                  <SelectValue placeholder="Chờ duyệt" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="submitted">Chờ duyệt</SelectItem>
                  <SelectItem value="approved">Đã duyệt</SelectItem>
                  <SelectItem value="rejected">Đã từ chối</SelectItem>
                  <SelectItem value="cancelled">Đã huỷ</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Employee */}
            <div className="space-y-2">
              <Label className="text-[13px] font-medium text-foreground">Nhân viên</Label>
              <Select
                value={employeeId}
                onValueChange={setEmployeeId}
              >
                <SelectTrigger className="h-9">
                  <SelectValue placeholder="Tất cả" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tất cả</SelectItem>
                  {employees.map((emp) => (
                    <SelectItem key={emp.id} value={emp.id}>
                      {emp.full_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Date From */}
            <div className="space-y-2">
              <Label htmlFor="date-from" className="text-[13px] font-medium text-foreground">Từ ngày</Label>
              <Input
                id="date-from"
                type="date"
                className="h-9"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
              />
            </div>

            {/* Date To */}
            <div className="space-y-2">
              <Label htmlFor="date-to" className="text-[13px] font-medium text-foreground">Đến ngày</Label>
              <Input
                id="date-to"
                type="date"
                className="h-9"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
              />
            </div>
          </div>

          {(requestType !== "all" ||
            status !== "submitted" ||
            employeeId !== "all" ||
            dateFrom ||
            dateTo) && (
            <div className="flex justify-end mt-4">
              <Button
                variant="ghost"
                size="sm"
                className="text-[12px] h-8 text-muted-foreground hover:text-foreground"
                onClick={handleResetFilters}
              >
                <RotateCcw className="h-3.5 w-3.5 mr-1.5" />
                Xoá bộ lọc
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

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
            Không tìm thấy yêu cầu nào phù hợp với bộ lọc hiện tại.
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
