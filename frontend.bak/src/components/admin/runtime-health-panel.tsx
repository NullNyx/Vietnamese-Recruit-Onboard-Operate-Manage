"use client";

import type { LucideIcon } from "lucide-react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  XCircle,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useRuntimeHealth } from "@/hooks/queries";
import type { RuntimeHealthStatus, RuntimeServiceStatus } from "@/lib/api/admin";

const SERVICE_LABELS: Record<string, string> = {
  redis: "Redis",
  postgresql: "PostgreSQL",
  minio: "MinIO",
  "gmail-worker": "Gmail Worker",
  "onboarding-worker": "Onboarding Worker",
};

const STATUS_META: Record<
  RuntimeHealthStatus,
  { icon: LucideIcon; label: string; className: string }
> = {
  healthy: {
    icon: CheckCircle2,
    label: "Ổn định",
    className: "border-emerald-200 bg-emerald-50 text-emerald-700",
  },
  degraded: {
    icon: AlertTriangle,
    label: "Giảm chất lượng",
    className: "border-amber-200 bg-amber-50 text-amber-700",
  },
  unhealthy: {
    icon: XCircle,
    label: "Lỗi",
    className: "border-destructive/30 bg-destructive/10 text-destructive",
  },
};

function formatServiceName(name: string): string {
  return SERVICE_LABELS[name] ?? name.replaceAll("-", " ");
}

function formatLatency(latencyMs: number | null): string | null {
  if (latencyMs === null || !Number.isFinite(latencyMs)) return null;
  return `${latencyMs.toFixed(1)} ms`;
}

function statusBadge(status: RuntimeHealthStatus) {
  const meta = STATUS_META[status];
  const Icon = meta.icon;

  return (
    <Badge variant="outline" className={`gap-1.5 ${meta.className}`}>
      <Icon className="h-3.5 w-3.5" aria-hidden="true" />
      {meta.label}
    </Badge>
  );
}

function LoadingRows() {
  return (
    <div className="divide-y divide-border/50" aria-hidden="true">
      {Array.from({ length: 5 }).map((_, index) => (
        <div key={index} className="flex items-center justify-between gap-4 py-3">
          <div className="flex min-w-0 items-center gap-3">
            <Skeleton className="h-8 w-8 rounded-full" />
            <div className="space-y-2">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-3 w-24" />
            </div>
          </div>
          <Skeleton className="h-6 w-24" />
        </div>
      ))}
    </div>
  );
}

function RuntimeServiceRow({ service }: { service: RuntimeServiceStatus }) {
  const meta = STATUS_META[service.status];
  const Icon = meta.icon;
  const latency = formatLatency(service.latency_ms);
  const detail = service.detail;
  const secondary = [latency, detail].filter(Boolean).join(" · ");

  return (
    <li className="flex flex-col gap-2 py-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex min-w-0 items-start gap-3">
        <span className={`mt-0.5 rounded-full border p-1.5 ${meta.className}`}>
          <Icon className="h-4 w-4" aria-hidden="true" />
        </span>
        <div className="min-w-0">
          <p className="text-sm font-medium text-foreground">
            {formatServiceName(service.name)}
          </p>
          <p className="mt-1 break-words text-xs text-muted-foreground">
            {secondary || "Đang theo dõi"}
          </p>
        </div>
      </div>
      <div className="sm:shrink-0">{statusBadge(service.status)}</div>
    </li>
  );
}

export function RuntimeHealthPanel() {
  const { data, error, isError, isFetching, isLoading, refetch } = useRuntimeHealth();
  const overallStatus = data?.status ?? "healthy";
  const overallMeta = STATUS_META[overallStatus];
  const OverallIcon = overallMeta.icon;
  const errorMessage = error instanceof Error ? error.message : "Không thể tải trạng thái runtime";

  return (
    <section
      className="rounded-lg border border-border/30 bg-card p-5"
      aria-labelledby="runtime-health-heading"
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
            <h2
              id="runtime-health-heading"
              className="text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground"
            >
              Backbone Flow runtime
            </h2>
          </div>
          <p className="mt-2 text-sm text-muted-foreground">
            Redis, PostgreSQL, MinIO, Gmail Worker, Onboarding Worker
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {data && (
            <Badge variant="outline" className={`gap-1.5 ${overallMeta.className}`}>
              <OverallIcon className="h-3.5 w-3.5" aria-hidden="true" />
              Tổng thể: {overallMeta.label}
            </Badge>
          )}
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => void refetch()}
            disabled={isFetching}
            aria-label="Làm mới trạng thái runtime"
          >
            <RefreshCw className={`h-4 w-4 ${isFetching ? "animate-spin" : ""}`} aria-hidden="true" />
            <span>Làm mới</span>
          </Button>
        </div>
      </div>

      <div className="mt-4" aria-live="polite">
        {isLoading ? (
          <LoadingRows />
        ) : isError ? (
          <div
            role="alert"
            className="rounded-md border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive"
          >
            {errorMessage}
          </div>
        ) : data?.services.length ? (
          <ul className="divide-y divide-border/50">
            {data.services.map((service) => (
              <RuntimeServiceRow key={service.name} service={service} />
            ))}
          </ul>
        ) : (
          <div className="rounded-md border border-border/40 p-4 text-sm text-muted-foreground">
            Chưa có dữ liệu runtime
          </div>
        )}
      </div>
    </section>
  );
}
