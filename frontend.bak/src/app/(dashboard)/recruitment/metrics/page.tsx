"use client";

import * as React from "react";
import {
  Clock,
  CheckCircle,
  XCircle,
  Layers,
  RefreshCw,
  Loader2,
  AlertCircle,
  Sparkles,
} from "lucide-react";

import { getMetrics } from "@/lib/api/recruitment";
import type { MetricsResponse } from "@/lib/api/recruitment";
import { MetricCard } from "@/components/recruitment/metric-card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent } from "@/components/ui/card";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const AUTO_REFRESH_INTERVAL_MS = 30_000;
const MANUAL_REFRESH_TIMEOUT_MS = 10_000;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatProcessingTime(ms: number): string {
  return (ms / 1000).toFixed(1) + "s";
}

function formatPercentage(ratio: number): string {
  return (ratio * 100).toFixed(1) + "%";
}

function formatQueueDepth(count: number): string {
  return String(Math.round(count));
}

// ---------------------------------------------------------------------------
// Skeleton Loading State
// ---------------------------------------------------------------------------

function MetricsSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <Card key={i} className="shadow-sm">
          <CardContent className="flex items-center gap-4 p-6">
            <Skeleton className="h-12 w-12 rounded-lg shrink-0" />
            <div className="space-y-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-7 w-16" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Error State
// ---------------------------------------------------------------------------

function MetricsError({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 gap-4">
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-destructive/10 ring-1 ring-destructive/20">
        <AlertCircle className="h-6 w-6 text-destructive" strokeWidth={1.5} />
      </div>
      <p className="text-sm font-medium text-muted-foreground">
        Không thể tải số liệu
      </p>
      <Button variant="outline" size="sm" onClick={onRetry}>
        Thử lại
      </Button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

export default function MetricsDashboardPage() {
  const [metrics, setMetrics] = React.useState<MetricsResponse | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(false);
  const [refreshing, setRefreshing] = React.useState(false);

  const fetchMetrics = React.useCallback(async () => {
    try {
      const data = await getMetrics();
      setMetrics(data);
      setError(false);
    } catch {
      setError(true);
    }
  }, []);

  const loadMetrics = React.useCallback(async () => {
    setLoading(true);
    setError(false);
    await fetchMetrics();
    setLoading(false);
  }, [fetchMetrics]);

  React.useEffect(() => {
    loadMetrics();
  }, [loadMetrics]);

  // Auto-refresh every 30 seconds while page is visible
  React.useEffect(() => {
    let intervalId: ReturnType<typeof setInterval> | null = null;

    function startInterval() {
      if (intervalId) return;
      intervalId = setInterval(() => {
        fetchMetrics();
      }, AUTO_REFRESH_INTERVAL_MS);
    }

    function stopInterval() {
      if (intervalId) {
        clearInterval(intervalId);
        intervalId = null;
      }
    }

    function handleVisibilityChange() {
      if (document.visibilityState === "visible") {
        fetchMetrics();
        startInterval();
      } else {
        stopInterval();
      }
    }

    if (document.visibilityState === "visible") {
      startInterval();
    }

    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      stopInterval();
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [fetchMetrics]);

  const handleManualRefresh = React.useCallback(async () => {
    setRefreshing(true);

    const timeoutId = setTimeout(() => {
      setRefreshing(false);
    }, MANUAL_REFRESH_TIMEOUT_MS);

    try {
      await fetchMetrics();
    } finally {
      clearTimeout(timeoutId);
      setRefreshing(false);
    }
  }, [fetchMetrics]);

  const handleRetry = React.useCallback(() => {
    loadMetrics();
  }, [loadMetrics]);

  return (
    <div className="animate-page-enter space-y-6 max-w-[1200px] mx-auto overflow-x-hidden pb-10">
      {/* ─── Page Header ───────────────────────────────── */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Layers className="h-4 w-4" strokeWidth={1.5} />
            </div>
            <h1 className="font-heading text-2xl font-bold tracking-tight">
              Số liệu Pipeline
            </h1>
          </div>
          <p className="mt-1 text-sm text-muted-foreground ml-10">
            Thống kê xử lý CV trong 24 giờ qua
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleManualRefresh}
          disabled={refreshing || loading}
          aria-label="Làm mới"
          className="shrink-0"
        >
          {refreshing ? (
            <Loader2 className="h-4 w-4 animate-spin mr-2" />
          ) : (
            <RefreshCw className="h-4 w-4 mr-2" />
          )}
          Làm mới
        </Button>
      </div>

      {/* ─── Summary bar — when data is loaded ──────────── */}
      {!loading && !error && metrics && (
        <div className="animate-fade-in flex items-center gap-4 rounded-xl border border-border/30 bg-card px-5 py-3 shadow-sm">
          <Sparkles className="h-3.5 w-3.5 text-muted-foreground/60" strokeWidth={1.5} />
          <span className="text-sm text-muted-foreground">
            Tự động làm mới mỗi 30 giây
          </span>
          <span className="hidden sm:inline text-xs text-muted-foreground/50">·</span>
          <span className="hidden sm:inline text-xs text-muted-foreground/60">
            Pipeline CV
          </span>
        </div>
      )}

      {/* ─── Content ────────────────────────────────────── */}
      {loading ? (
        <MetricsSkeleton />
      ) : error ? (
        <MetricsError onRetry={handleRetry} />
      ) : metrics ? (
        <div className="stagger-children grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="animate-fade-in">
            <MetricCard
              label="Thời gian xử lý TB"
              value={formatProcessingTime(metrics.average_processing_time_ms)}
              icon={Clock}
              type="processing_time"
              rawValue={metrics.average_processing_time_ms}
            />
          </div>
          <div className="animate-fade-in">
            <MetricCard
              label="Tỷ lệ thành công"
              value={formatPercentage(metrics.success_rate)}
              icon={CheckCircle}
              type="success_rate"
              rawValue={metrics.success_rate}
            />
          </div>
          <div className="animate-fade-in">
            <MetricCard
              label="Tỷ lệ thất bại"
              value={formatPercentage(metrics.failure_rate)}
              icon={XCircle}
              type="failure_rate"
              rawValue={metrics.failure_rate}
            />
          </div>
          <div className="animate-fade-in">
            <MetricCard
              label="Hàng đợi"
              value={formatQueueDepth(metrics.queue_depth)}
              icon={Layers}
              type="queue_depth"
              rawValue={metrics.queue_depth}
            />
          </div>
        </div>
      ) : null}
    </div>
  );
}
