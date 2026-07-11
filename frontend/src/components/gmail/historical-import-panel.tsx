"use client";

import * as React from "react";
import { Download, StopCircle, Eye, Loader2 } from "lucide-react";
import * as importApi from "@/lib/api/gmail";
import { useToast } from "@/components/gmail/toast-provider";

/**
 * HistoricalImportPanel — allows HR to import old recruitment emails.
 *
 * Provides a controlled UI for:
 * 1. Selecting a time window (7 or 30 days).
 * 2. Previewing the estimated count of new emails.
 * 3. Starting the background import job.
 * 4. Tracking progress (total, processed, cv, errors).
 * 5. Cancelling a running job.
 */
export function HistoricalImportPanel() {
  const { addToast } = useToast();

  // Window selection
  const [days, setDays] = React.useState<7 | 30>(7);

  // Preview state
  const [previewData, setPreviewData] =
    React.useState<importApi.ImportPreviewResponse | null>(null);
  const [previewLoading, setPreviewLoading] = React.useState(false);

  // Job state
  const [importStatus, setImportStatus] =
    React.useState<importApi.ImportStatusResponse | null>(null);

  const [startLoading, setStartLoading] = React.useState(false);
  const [cancelLoading, setCancelLoading] = React.useState(false);
  const [expanded, setExpanded] = React.useState(false);

  // Poll for status while a job is running
  const isRunning = importStatus?.status === "running";

  React.useEffect(() => {
    if (!isRunning) return;

    const interval = setInterval(async () => {
      try {
        const status = await importApi.getImportStatus();
        setImportStatus(status);
      } catch {
        // Silently fail on poll
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [isRunning]);

  // Preview handler
  const handlePreview = React.useCallback(async () => {
    setPreviewLoading(true);
    setPreviewData(null);
    try {
      const result = await importApi.previewImport(days);
      setPreviewData(result);
    } catch (err) {
      addToast(
        err instanceof Error ? err.message : "Không thể xem trước số email",
        "error",
      );
    } finally {
      setPreviewLoading(false);
    }
  }, [days, addToast]);

  // Start import handler
  const handleStartImport = React.useCallback(async () => {
    setStartLoading(true);
    try {
      const result = await importApi.startImport(days);
      setImportStatus({
        job_id: result.job_id,
        status: "running",
        days: result.days,
        total_count: 0,
        processed_count: 0,
        cv_count: 0,
        errors: 0,
        started_at: new Date().toISOString(),
        completed_at: null,
        error_message: null,
      });
      addToast(result.message, "success");
      // Also fetch the initial status to get total_count
      const status = await importApi.getImportStatus();
      setImportStatus(status);
    } catch (err) {
      addToast(
        err instanceof Error ? err.message : "Không thể bắt đầu import",
        "error",
      );
    } finally {
      setStartLoading(false);
    }
  }, [days, addToast]);

  // Cancel handler
  const handleCancelImport = React.useCallback(async () => {
    setCancelLoading(true);
    try {
      const result = await importApi.cancelImport();
      if (result.status === "cancelled") {
        setImportStatus((prev) =>
          prev ? { ...prev, status: "cancelled" } : prev,
        );
      }
      addToast(result.message, "success");
    } catch (err) {
      addToast(
        err instanceof Error ? err.message : "Không thể dừng import",
        "error",
      );
    } finally {
      setCancelLoading(false);
    }
  }, [addToast]);

  // Format elapsed time
  const formatTime = (isoString: string | null): string => {
    if (!isoString) return "";
    const date = new Date(isoString);
    return date.toLocaleTimeString("vi-VN", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  // Progress percentage
  const progressPercent =
    importStatus && importStatus.total_count > 0
      ? Math.round(
          (importStatus.processed_count / importStatus.total_count) * 100,
        )
      : 0;

  return (
    <div className="rounded-lg border border-border bg-card">
      {/* Header */}
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between px-4 py-3 text-left hover:bg-accent/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Download className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium text-foreground">
            Import email cũ
          </span>
        </div>
        <div className="flex items-center gap-2">
          {isRunning && (
            <span className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-medium text-blue-700">
              <span className="h-1.5 w-1.5 rounded-full bg-blue-500 animate-pulse" />
              Đang chạy
            </span>
          )}
          <span className="text-xs text-muted-foreground">
            {expanded ? "▲" : "▼"}
          </span>
        </div>
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="border-t border-border px-4 py-3 space-y-3">
          {/* Case 1: No active job — show controls */}
          {!isRunning && (
            <>
              {/* Window selector */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground shrink-0">
                  Import email từ
                </span>
                <select
                  value={days}
                  onChange={(e) => setDays(Number(e.target.value) as 7 | 30)}
                  className="rounded-md border border-input bg-background px-2 py-1 text-xs text-foreground"
                >
                  <option value={7}>7 ngày</option>
                  <option value={30}>30 ngày</option>
                </select>
                <span className="text-xs text-muted-foreground">trước</span>
              </div>

              {/* Preview button */}
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handlePreview}
                  disabled={previewLoading}
                  className="inline-flex items-center gap-1.5 rounded-md border border-input bg-background px-3 py-1.5 text-xs font-medium text-foreground hover:bg-accent transition-colors disabled:opacity-50"
                >
                  {previewLoading ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Eye className="h-3.5 w-3.5" />
                  )}
                  Xem trước số email
                </button>

                {/* Preview results */}
                {previewData && (
                  <span className="text-xs text-muted-foreground">
                    {previewData.estimated_count > 0 ? (
                      <>
                        <strong className="text-foreground">
                          {previewData.estimated_count}
                        </strong>{" "}
                        email mới có thể import
                        {previewData.already_imported_count > 0 && (
                          <>
                            {" "}
                            (<strong>{previewData.already_imported_count}</strong>{" "}
                            đã import trước đó)
                          </>
                        )}
                      </>
                    ) : (
                      "Không có email mới trong khoảng thời gian này"
                    )}
                  </span>
                )}
              </div>

              {/* Start import button */}
              {previewData && previewData.estimated_count > 0 && (
                <button
                  type="button"
                  onClick={handleStartImport}
                  disabled={startLoading}
                  className="inline-flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50 w-full justify-center"
                >
                  {startLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Download className="h-4 w-4" />
                  )}
                  Import {previewData.estimated_count} email (
                  {days === 7 ? "7" : "30"} ngày)
                </button>
              )}
            </>
          )}

          {/* Case 2: Job running/completed — show status */}
          {importStatus && (
            <div className="space-y-2">
              {/* Status label */}
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-foreground">
                  Trạng thái:{" "}
                  {importStatus.status === "running" && "Đang import"}
                  {importStatus.status === "completed" && "Hoàn tất"}
                  {importStatus.status === "cancelled" && "Đã dừng"}
                  {importStatus.status === "failed" && "Thất bại"}
                </span>
                <span className="text-[10px] text-muted-foreground">
                  {importStatus.started_at &&
                    `Bắt đầu: ${formatTime(importStatus.started_at)}`}
                </span>
              </div>

              {/* Progress bar */}
              {importStatus.total_count > 0 && (
                <div className="w-full h-2 rounded-full bg-muted overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      importStatus.status === "completed"
                        ? "bg-green-500"
                        : importStatus.status === "failed"
                          ? "bg-red-500"
                          : "bg-primary"
                    }`}
                    style={{
                      width: `${Math.min(progressPercent, 100)}%`,
                    }}
                  />
                </div>
              )}

              {/* Counters */}
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="rounded-md bg-muted px-2 py-1">
                  <div className="text-xs font-semibold text-foreground">
                    {importStatus.processed_count}
                  </div>
                  <div className="text-[10px] text-muted-foreground">
                    Đã xử lý
                  </div>
                </div>
                <div className="rounded-md bg-muted px-2 py-1">
                  <div className="text-xs font-semibold text-foreground">
                    {importStatus.cv_count}
                  </div>
                  <div className="text-[10px] text-muted-foreground">CV</div>
                </div>
                <div className="rounded-md bg-muted px-2 py-1">
                  <div className="text-xs font-semibold text-foreground">
                    {importStatus.total_count || "?"}
                  </div>
                  <div className="text-[10px] text-muted-foreground">
                    Tổng số
                  </div>
                </div>
              </div>

              {/* Error message */}
              {importStatus.error_message && (
                <div className="rounded-md bg-red-50 px-3 py-2 text-[10px] text-red-700">
                  {importStatus.error_message}
                </div>
              )}

              {/* Cancel button (only for running jobs) */}
              {importStatus.status === "running" && (
                <button
                  type="button"
                  onClick={handleCancelImport}
                  disabled={cancelLoading}
                  className="inline-flex items-center gap-1.5 rounded-md border border-red-200 bg-red-50 px-3 py-1.5 text-xs font-medium text-red-700 hover:bg-red-100 transition-colors disabled:opacity-50 w-full justify-center"
                >
                  {cancelLoading ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <StopCircle className="h-3.5 w-3.5" />
                  )}
                  Dừng import
                </button>
              )}

              {/* Error count */}
              {importStatus.errors > 0 && (
                <p className="text-[10px] text-muted-foreground">
                  {importStatus.errors} lỗi trong quá trình xử lý
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
