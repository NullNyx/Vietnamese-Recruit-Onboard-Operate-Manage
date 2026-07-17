"use client";

import * as React from "react";
import {
  CheckCircle,
  AlertCircle,
  RefreshCw,
  Sparkles,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import {
  listReviewQueue,
  submitCorrection,
  retryParse,
  dismissReview,
  getCVPresignedUrl,
} from "@/lib/api/recruitment";
import type {
  CVReviewItem,
  CVReviewListResponse,
  ParsedCVInput,
} from "@/lib/api/recruitment";
import { ApiError } from "@/lib/api/types";
import { ReviewItem } from "@/components/recruitment/review-item";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const PAGE_SIZE_OPTIONS = [10, 20, 50] as const;
const DEFAULT_PAGE_SIZE = 20;

// ---------------------------------------------------------------------------
// Skeleton Loading Component
// ---------------------------------------------------------------------------

function ReviewSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 4 }).map((_, i) => (
        <div
          key={i}
          className="rounded-xl border border-border/30 bg-card p-5 space-y-3 shadow-sm"
        >
          <div className="flex items-center gap-3">
            <Skeleton className="h-5 w-32" />
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-5 w-20 ml-auto" />
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-4 w-24" />
          </div>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Empty State Component
// ---------------------------------------------------------------------------

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-green-50 to-green-100/50 ring-1 ring-green-200/30 dark:from-green-950/30 dark:to-green-900/20 dark:ring-green-800/30">
        <CheckCircle className="h-6 w-6 text-green-600 dark:text-green-400" strokeWidth={1.5} />
      </div>
      <p className="text-sm font-medium text-muted-foreground">
        Không có CV nào cần xem xét
      </p>
      <p className="mt-1 text-xs text-muted-foreground/60">
        Tất cả CV đã được xử lý hoặc đang chờ dữ liệu mới
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Error State Component
// ---------------------------------------------------------------------------

function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-14 text-center">
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-destructive/10 ring-1 ring-destructive/20">
        <AlertCircle className="h-6 w-6 text-destructive" strokeWidth={1.5} />
      </div>
      <p className="text-sm font-medium text-muted-foreground mb-4">
        Không thể tải danh sách
      </p>
      <Button variant="outline" size="sm" onClick={onRetry}>
        <RefreshCw className="h-4 w-4 mr-2" />
        Thử lại
      </Button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Pagination Component
// ---------------------------------------------------------------------------

function Pagination({
  page,
  pageSize,
  total,
  onPageChange,
  onPageSizeChange,
}: {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
}) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="flex flex-wrap items-center justify-between gap-4 pt-4">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <span>Hiển thị</span>
        <Select
          value={String(pageSize)}
          onValueChange={(val) => onPageSizeChange(Number(val))}
        >
          <SelectTrigger className="h-8 w-[70px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {PAGE_SIZE_OPTIONS.map((size) => (
              <SelectItem key={size} value={String(size)}>
                {size}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <span>mục / trang</span>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-sm tabular-nums text-muted-foreground">
          Trang {page} / {totalPages}
        </span>
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page Component
// ---------------------------------------------------------------------------

export default function CVReviewPage() {
  const [data, setData] = React.useState<CVReviewListResponse | null>(null);
  const [items, setItems] = React.useState<CVReviewItem[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(false);
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(DEFAULT_PAGE_SIZE);

  const fetchData = React.useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const response = await listReviewQueue({ page, page_size: pageSize });
      setData(response);
      setItems(response.items);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize]);

  React.useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handlePageChange = React.useCallback((newPage: number) => {
    setPage(newPage);
  }, []);

  const handlePageSizeChange = React.useCallback((newSize: number) => {
    setPageSize(newSize);
    setPage(1);
  }, []);

  const handleSubmitCorrection = React.useCallback(
    async (cvDocumentId: string, correctionData: ParsedCVInput) => {
      try {
        await submitCorrection(cvDocumentId, correctionData);
        toast.success("Đã cập nhật CV thành công");
        setItems((prev) => prev.filter((item) => item.id !== cvDocumentId));
      } catch (err) {
        if (err instanceof ApiError) {
          if (err.statusCode === 404) {
            toast.error("CV không tồn tại hoặc đã bị xóa");
            setItems((prev) =>
              prev.filter((item) => item.id !== cvDocumentId)
            );
            return;
          }
          if (err.statusCode === 422) {
            throw err;
          }
          toast.error(err.message || "Đã xảy ra lỗi. Vui lòng thử lại.");
        } else {
          toast.error("Đã xảy ra lỗi. Vui lòng thử lại.");
        }
        throw err;
      }
    },
    []
  );

  const handleRetryParse = React.useCallback(
    async (cvDocumentId: string) => {
      try {
        const updatedItem = await retryParse(cvDocumentId);
        setItems((prev) =>
          prev.map((item) =>
            item.id === cvDocumentId ? updatedItem : item
          )
        );
        toast.success("Đã phân tích lại CV thành công");
      } catch (err) {
        if (err instanceof ApiError && err.statusCode === 404) {
          toast.error("CV không tồn tại hoặc đã bị xóa");
          setItems((prev) =>
            prev.filter((item) => item.id !== cvDocumentId)
          );
          return;
        }
        toast.error(
          err instanceof ApiError
            ? err.message
            : "Đã xảy ra lỗi. Vui lòng thử lại."
        );
      }
    },
    []
  );

  const handleDismiss = React.useCallback(
    async (cvDocumentId: string) => {
      try {
        await dismissReview(cvDocumentId);
        setItems((prev) =>
          prev.filter((item) => item.id !== cvDocumentId)
        );
        toast.success("Đã bỏ qua CV");
      } catch (err) {
        if (err instanceof ApiError && err.statusCode === 404) {
          toast.error("CV không tồn tại hoặc đã bị xóa");
          setItems((prev) =>
            prev.filter((item) => item.id !== cvDocumentId)
          );
          return;
        }
        toast.error(
          err instanceof ApiError
            ? err.message
            : "Đã xảy ra lỗi. Vui lòng thử lại."
        );
      }
    },
    []
  );

  const handleViewOriginal = React.useCallback(
    async (cvDocumentId: string) => {
      const item = items.find((i) => i.id === cvDocumentId);
      if (!item || !item.candidate_id) {
        toast.error("Không thể mở CV gốc. Thiếu thông tin ứng viên.");
        return;
      }
      try {
        const response = await getCVPresignedUrl(
          item.candidate_id,
          cvDocumentId
        );
        window.open(response.presigned_url, "_blank");
      } catch {
        toast.error("Không thể tải tài liệu. Vui lòng thử lại.");
      }
    },
    [items]
  );

  const total = data?.total ?? 0;

  return (
    <div className="animate-page-enter space-y-6 max-w-[1200px] mx-auto overflow-x-hidden pb-10">
      {/* ─── Page header ──────────────────────────────── */}
      <div>
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
            <Sparkles className="h-4 w-4" strokeWidth={1.5} />
          </div>
          <h1 className="font-heading text-2xl font-bold">Xem xét CV</h1>
        </div>
        <p className="mt-1 text-sm text-muted-foreground ml-10">
          Xem xét và chỉnh sửa CV được phân tích tự động
        </p>
      </div>

      {/* ─── Content ──────────────────────────────────── */}
      {loading ? (
        <ReviewSkeleton />
      ) : error ? (
        <ErrorState onRetry={fetchData} />
      ) : items.length === 0 ? (
        <EmptyState />
      ) : (
        <>
          {/* Summary bar */}
          <div className="animate-fade-in flex items-center gap-4 rounded-xl border border-border/30 bg-card px-5 py-3 shadow-sm">
            <Sparkles className="h-3.5 w-3.5 text-muted-foreground/60" strokeWidth={1.5} />
            <span className="text-sm text-muted-foreground">
              Có <strong className="text-foreground tabular-nums">{total}</strong> CV cần xem xét
            </span>
          </div>

          {/* Review items list */}
          <div className="space-y-4" aria-live="polite">
            {items.map((item) => (
              <ReviewItem
                key={item.id}
                item={item}
                onSubmitCorrection={handleSubmitCorrection}
                onRetryParse={handleRetryParse}
                onDismiss={handleDismiss}
                onViewOriginal={handleViewOriginal}
              />
            ))}
          </div>

          {/* Pagination */}
          <Pagination
            page={page}
            pageSize={pageSize}
            total={total}
            onPageChange={handlePageChange}
            onPageSizeChange={handlePageSizeChange}
          />
        </>
      )}
    </div>
  );
}
