"use client";

import * as React from "react";
import { Loader2, Mail, AlertTriangle, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ConnectionStatus, CapabilityHealth } from "@/lib/api/types";
import { CapabilityHealthCards } from "./capability-health-cards";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface ConnectionPanelProps {
  status: ConnectionStatus | null;
  email: string | null;
  loading: boolean;
  error: string | null;
  onConnect: () => void;
  onDisconnect: () => void;
  onRetry: () => void;
  connectLoading: boolean;
  disconnectLoading: boolean;
  /** Optional capability health cards to show separately alongside the status */
  capabilities?: CapabilityHealth[];
  capabilitiesLoading?: boolean;
  /** When true, render in compact bar mode for the sidebar header */
  compact?: boolean;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ConnectionPanel({
  status,
  email,
  loading,
  error,
  onConnect,
  onDisconnect,
  onRetry,
  connectLoading,
  disconnectLoading,
  capabilities,
  capabilitiesLoading = false,
  compact = false,
}: ConnectionPanelProps) {
  if (compact) {
    return renderCompactBar({
      status,
      email,
      onDisconnect,
      disconnectLoading,
    });
  }

  // Initial loading state (fetching status)
  if (loading && status === null) {
    return (
      <div className="flex items-center justify-center rounded-lg border border-border bg-card p-6">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        <span className="ml-2 text-sm text-muted-foreground">
          Đang kiểm tra kết nối...
        </span>
      </div>
    );
  }

  // Error state (API call failed)
  if (error && status === null) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6">
        <div className="flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 shrink-0 text-red-500" />
          <div className="flex-1">
            <p className="text-sm font-medium text-red-800">
              Không thể kiểm tra trạng thái kết nối
            </p>
            <p className="mt-1 text-sm text-red-600">{error}</p>
          </div>
          <button
            onClick={onRetry}
            className="shrink-0 rounded-md bg-red-100 px-3 py-1.5 text-sm font-medium text-red-700 transition-colors hover:bg-red-200"
          >
            Thử lại
          </button>
        </div>
      </div>
    );
  }

  // Connected state
  if (status === "connected") {
    return (
      <div className="space-y-3">
        <div className="rounded-lg border border-green-200 bg-green-50 p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="inline-block h-2 w-2 rounded-full bg-green-500" />
                  <span className="text-sm font-medium text-green-800">
                    Đã kết nối
                  </span>
                </div>
                {email && (
                  <p className="mt-0.5 text-sm text-green-700">{email}</p>
                )}
              </div>
            </div>
            <button
              onClick={onDisconnect}
              disabled={disconnectLoading}
              className={cn(
                "inline-flex items-center gap-2 rounded-md border border-red-200 bg-card px-4 py-2 text-sm font-medium text-red-600 transition-colors hover:bg-red-50",
                disconnectLoading && "cursor-not-allowed opacity-60",
              )}
            >
              {disconnectLoading && <Loader2 className="h-4 w-4 animate-spin" />}
              Ngắt kết nối
            </button>
          </div>
        </div>
        {/* Capability health cards displayed separately */}
        {capabilities && capabilities.length > 0 && (
          <CapabilityHealthCards
            capabilities={capabilities}
            loading={capabilitiesLoading}
          />
        )}
      </div>
    );
  }

  // Reauthorization required state
  if (status === "reauthorization_required") {
    return (
      <div className="space-y-3">
        <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-yellow-100">
                <AlertTriangle className="h-5 w-5 text-yellow-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-yellow-800">
                  Phiên kết nối đã hết hạn
                </p>
                <p className="mt-0.5 text-sm text-yellow-700">
                  Vui lòng kết nối lại để tiếp tục sử dụng Gmail.
                </p>
              </div>
            </div>
            <button
              onClick={onConnect}
              disabled={connectLoading}
              className={cn(
                "inline-flex items-center gap-2 rounded-md bg-yellow-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-yellow-700",
                connectLoading && "cursor-not-allowed opacity-60",
              )}
            >
              {connectLoading && <Loader2 className="h-4 w-4 animate-spin" />}
              Kết nối lại
            </button>
          </div>
        </div>
        {/* Capability health cards displayed separately */}
        {capabilities && capabilities.length > 0 && (
          <CapabilityHealthCards
            capabilities={capabilities}
            loading={capabilitiesLoading}
          />
        )}
      </div>
    );
  }

  // Disconnected state (default)
  return (
    <div className="space-y-3">
      <div className="rounded-lg border border-border bg-card p-6">
        <div className="flex flex-col items-center gap-4 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
            <Mail className="h-6 w-6 text-muted-foreground" />
          </div>
          <div>
            <p className="text-sm font-medium text-foreground">
              Chưa kết nối Gmail
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              Kết nối tài khoản Gmail để đọc và gửi email trực tiếp từ Vroom HR.
            </p>
          </div>
          <button
            onClick={onConnect}
            disabled={connectLoading}
            className={cn(
              "inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90",
              connectLoading && "cursor-not-allowed opacity-60",
            )}
          >
            {connectLoading && <Loader2 className="h-4 w-4 animate-spin" />}
            Kết nối Gmail
          </button>
        </div>
      </div>
      {capabilities && capabilities.length > 0 && (
        <CapabilityHealthCards
          capabilities={capabilities}
          loading={capabilitiesLoading}
        />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Compact bar variant (used inside sidebar header)
// ---------------------------------------------------------------------------

function renderCompactBar({
  status,
  email,
  onDisconnect,
  disconnectLoading,
}: {
  status: ConnectionStatus | null;
  email: string | null;
  onDisconnect: () => void;
  disconnectLoading: boolean;
}) {
  if (status === "connected") {
    return (
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <span className="inline-block h-2 w-2 shrink-0 rounded-full bg-green-500" />
          <span className="text-xs font-medium text-green-700 truncate">
            {email || "Đã kết nối"}
          </span>
        </div>
        <button
          onClick={onDisconnect}
          disabled={disconnectLoading}
          className={cn(
            "shrink-0 rounded-md border border-red-200 bg-card px-2 py-1 text-[10px] font-medium text-red-600 transition-colors hover:bg-red-50",
            disconnectLoading && "cursor-not-allowed opacity-60",
          )}
        >
          {disconnectLoading ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            "Ngắt"
          )}
        </button>
      </div>
    );
  }

  if (status === "reauthorization_required") {
    return (
      <div className="flex items-center gap-2">
        <span className="inline-block h-2 w-2 shrink-0 rounded-full bg-yellow-500" />
        <span className="text-xs text-yellow-700 truncate">
          Phiên kết nối đã hết hạn
        </span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <span className="inline-block h-2 w-2 shrink-0 rounded-full bg-muted-foreground" />
      <span className="text-xs text-muted-foreground">Chưa kết nối</span>
    </div>
  );
}
