"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, RefreshCw } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { formatDate } from "@/lib/recruitment-utils";
import {
  getJobOpening,
  type JobOpeningDetail,
  type JobOpeningStatus,
} from "@/lib/api/recruitment";
import { ApiError } from "@/lib/api/types";

// ---------------------------------------------------------------------------
// Status labels and colors
// ---------------------------------------------------------------------------

const JO_STATUS_LABELS: Record<JobOpeningStatus, string> = {
  draft: "Nháp",
  open: "Đang tuyển",
  closed: "Đã đóng",
  cancelled: "Đã huỷ",
};

const JO_STATUS_COLORS: Record<JobOpeningStatus, string> = {
  draft:
    "bg-gray-100 text-gray-700",
  open: "bg-green-100 text-green-800",
  closed:
    "bg-yellow-100 text-yellow-800",
  cancelled:
    "bg-red-100 text-red-800",
};

// ---------------------------------------------------------------------------
// Candidate status labels (matching the pipeline states per CONTEXT.md)
// ---------------------------------------------------------------------------

const CANDIDATE_STATUS_LABELS: Record<string, string> = {
  new: "Mới",
  reviewing: "Đang xét",
  interview_scheduled: "Đã lên lịch PV",
  accepted: "Đã nhận",
  rejected: "Đã từ chối",
  archived: "Đã lưu trữ",
};

const CANDIDATE_STATUS_ORDER = [
  "new",
  "reviewing",
  "interview_scheduled",
  "accepted",
  "rejected",
  "archived",
];

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type PageState =
  | { kind: "loading" }
  | { kind: "not_found" }
  | { kind: "error"; message: string }
  | { kind: "loaded"; jobOpening: JobOpeningDetail };

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

export default function JobOpeningDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const [pageState, setPageState] = useState<PageState>({ kind: "loading" });

  const fetchData = useCallback(async () => {
    setPageState({ kind: "loading" });
    try {
      const jo = await getJobOpening(id);
      setPageState({ kind: "loaded", jobOpening: jo });
    } catch (err) {
      if (err instanceof ApiError && err.statusCode === 404) {
        setPageState({ kind: "not_found" });
      } else {
        setPageState({
          kind: "error",
          message:
            err instanceof ApiError
              ? err.message
              : "Không thể tải thông tin vị trí tuyển dụng",
        });
      }
    }
  }, [id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // -----------------------------------------------------------------------
  // Loading
  // -----------------------------------------------------------------------

  if (pageState.kind === "loading") {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-4 w-48" />
        <Skeleton className="h-8 w-64" />
        <div className="flex gap-4">
          <Skeleton className="h-6 w-24" />
          <Skeleton className="h-6 w-20" />
        </div>
        <div className="space-y-3">
          <Skeleton className="h-5 w-32" />
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-20 w-full rounded-lg" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  // -----------------------------------------------------------------------
  // Not Found
  // -----------------------------------------------------------------------

  if (pageState.kind === "not_found") {
    return (
      <div className="flex flex-col items-center justify-center p-12 space-y-4">
        <p className="text-lg text-muted-foreground">
          Không tìm thấy vị trí tuyển dụng
        </p>
        <Link href="/recruitment/job-openings">
          <Button variant="outline">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Quay lại danh sách
          </Button>
        </Link>
      </div>
    );
  }

  // -----------------------------------------------------------------------
  // Error
  // -----------------------------------------------------------------------

  if (pageState.kind === "error") {
    return (
      <div className="flex flex-col items-center justify-center p-12 space-y-4">
        <p className="text-lg text-destructive">{pageState.message}</p>
        <Button variant="outline" onClick={fetchData}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Thử lại
        </Button>
      </div>
    );
  }

  // -----------------------------------------------------------------------
  // Loaded
  // -----------------------------------------------------------------------

  const { jobOpening: jo } = pageState;
  const counts = jo.candidate_counts ?? {};
  const totalCandidates = Object.values(counts).reduce((a, b) => a + b, 0);
  const acceptedCount = counts.accepted ?? 0;
  const remaining = jo.target_headcount - acceptedCount;

  return (
    <div className="p-6 space-y-6">
      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb">
        <ol className="flex items-center gap-2 text-sm text-muted-foreground">
          <li>
            <Link
              href="/recruitment/job-openings"
              className="hover:text-foreground transition-colors"
            >
              Vị trí tuyển dụng
            </Link>
          </li>
          <li aria-hidden="true">&gt;</li>
          <li className="text-foreground font-medium">{jo.title}</li>
        </ol>
      </nav>

      {/* Header */}
      <div className="space-y-3">
        <h1 className="text-2xl font-bold text-foreground break-words">{jo.title}</h1>
        {jo.position_name && (
          <span className="text-sm text-muted-foreground">{jo.position_name}</span>
        )}
        <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
          <span>Ngày tạo: {formatDate(jo.created_at)}</span>
          {jo.opened_at && (
            <span>Ngày mở: {formatDate(jo.opened_at)}</span>
          )}
          {jo.closed_at && (
            <span>Ngày đóng: {formatDate(jo.closed_at)}</span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <Badge className={JO_STATUS_COLORS[jo.status as JobOpeningStatus]}>
            {JO_STATUS_LABELS[jo.status as JobOpeningStatus]}
          </Badge>
        </div>
      </div>

      {/* Description — show if non-empty */}
      {jo.description && (
        <div className="rounded-md border bg-muted/30 p-4">
          <h2 className="text-sm font-medium mb-2">Mô tả</h2>
          <p className="text-sm text-muted-foreground whitespace-pre-wrap">
            {jo.description}
          </p>
        </div>
      )}

      {/* Headcount summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatBox label="Chỉ tiêu" value={jo.target_headcount} />
        <StatBox label="Đã nhận" value={acceptedCount} />
        <StatBox
          label={
            remaining > 0
              ? "Còn thiếu"
              : remaining === 0
                ? "Đã đủ"
                : "Vượt chỉ tiêu"
          }
          value={remaining <= 0 ? Math.abs(remaining) : remaining}
          highlight={
            remaining === 0
              ? "positive"
              : remaining < 0
                ? "overfilled"
                : undefined
          }
        />
        <StatBox label="Tổng ứng viên" value={totalCandidates} />
      </div>

      {/* Candidate counts by status */}
      <div>
        <h2 className="text-lg font-semibold mb-4">
          Ứng viên theo trạng thái
        </h2>
        {totalCandidates === 0 ? (
          <p className="text-sm text-muted-foreground">
            Chưa có ứng viên nào được gán vào vị trí này
          </p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {CANDIDATE_STATUS_ORDER.map((statusKey) => {
              const count = counts[statusKey] ?? 0;
              return (
                <div
                  key={statusKey}
                  className={cn(
                    "rounded-md border p-3 flex flex-col",
                    count > 0
                      ? "bg-card"
                      : "bg-muted/30 text-muted-foreground",
                  )}
                >
                  <span className="text-xs text-muted-foreground">
                    {CANDIDATE_STATUS_LABELS[statusKey] ?? statusKey}
                  </span>
                  <span className="text-2xl font-semibold tabular-nums mt-1">
                    {count}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function StatBox({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string | number;
  highlight?: "positive" | "overfilled";
}) {
  return (
    <div className="rounded-md border p-4">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span
        className={cn(
          "block text-2xl font-semibold tabular-nums mt-1",
          highlight === "positive" && "text-green-600",
          highlight === "overfilled" && "text-orange-600",
        )}
      >
        {value}
      </span>
    </div>
  );
}
