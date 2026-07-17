/**
 * Shared UI primitives — single source of truth for Vroom HR frontend.
 *
 * Merged from lib/dashboard-ui.tsx + components/operate.tsx (2025-Q2 restructure).
 * Follows AI Studio design system: slate/indigo, rounded-2xl cards, rounded-full
 * pill buttons, Inter + JetBrains Mono. Vietnamese labels default.
 *
 * Keep dependency-free beyond lucide-react; no heavy design library.
 */

'use client';

import React from 'react';
import { AlertTriangle, Inbox, Loader2 } from 'lucide-react';
import type { ApiError } from '@/lib/api/types';
import { getErrorMessage } from '@/lib/api/error-codes';

// ---------------------------------------------------------------------------
// Error banner — renders BE error_code via registry when available
// ---------------------------------------------------------------------------

/**
 * Render a BE error_code with the mapped Vietnamese message (never self-fabricated).
 * Accepts optional `title` override (default: "Đã xảy ra lỗi. Vui lòng thử lại.").
 */
export function ErrorBanner({
  error,
  title = 'Đã xảy ra lỗi. Vui lòng thử lại.',
}: {
  error: unknown;
  title?: string;
}) {
  if (!error) return null;
  let msg = title;
  let code: string | undefined;
  if (error instanceof Error) {
    const apiErr = error as ApiError;
    code = apiErr.errorCode;
    msg = code ? getErrorMessage(code) : apiErr.message || msg;
  }
  return (
    <div className="flex items-start gap-2 p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700">
      <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
      <div className="min-w-0 text-sm">
        <p className="break-words font-semibold">{msg}</p>
        {code && code !== 'UNKNOWN_ERROR' && (
          <code className="text-[11px] font-mono text-rose-400 block mt-0.5">{code}</code>
        )}
      </div>
    </div>
  );
}

/** @deprecated Alias for ErrorBanner — kept for backward compat. Use ErrorBanner directly. */
export const ErrorAlert = ErrorBanner;

// ---------------------------------------------------------------------------
// Loading
// ---------------------------------------------------------------------------

/** Centered loading spinner with optional label. */
export function Loading({ label = 'Đang tải...' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="animate-spin w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full" />
      <span className="ml-3 text-sm text-slate-500">{label}</span>
    </div>
  );
}

/** Skeleton rows for table/list loading placeholders. */
export function LoadingRows({ count = 5 }: { count?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="animate-pulse h-12 bg-slate-100 rounded-lg" />
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Empty state — distinguishes "filter matched nothing" vs "no data yet"
// ---------------------------------------------------------------------------

export function EmptyState({
  filtered,
  onReset,
  emptyFiltered = 'Không có bản ghi khớp với bộ lọc hiện tại.',
  emptyData = 'Chưa có bản ghi nào.',
  hintFiltered = 'Thử thay đổi từ khóa hoặc bộ lọc.',
  hintData = 'Dữ liệu sẽ xuất hiện khi có bản ghi.',
}: {
  filtered: boolean;
  onReset?: () => void;
  emptyFiltered?: string;
  emptyData?: string;
  hintFiltered?: string;
  hintData?: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <Inbox className="w-10 h-10 text-slate-300 mb-3" />
      <p className="text-sm font-medium text-slate-600">
        {filtered ? emptyFiltered : emptyData}
      </p>
      <p className="text-xs text-slate-400 mt-1">
        {filtered ? hintFiltered : hintData}
      </p>
      {filtered && onReset && (
        <button
          onClick={onReset}
          className="mt-4 px-4 py-2 text-xs font-medium bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-full transition-all"
        >
          Xóa bộ lọc
        </button>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Status pill + Badge (two distinct primitives)
// ---------------------------------------------------------------------------

/** Status pill — color by group; label Vietnamese. Used in pipeline dashboards. */
export function StatusPill({
  status,
  label,
  tone = 'slate',
}: {
  status: string;
  label: string;
  tone?: 'slate' | 'indigo' | 'amber' | 'emerald' | 'rose' | 'violet';
}) {
  const tones: Record<string, string> = {
    slate: 'bg-slate-100 text-slate-700 border-slate-200',
    indigo: 'bg-indigo-50 text-indigo-700 border-indigo-200',
    amber: 'bg-amber-50 text-amber-700 border-amber-200',
    emerald: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    rose: 'bg-rose-50 text-rose-700 border-rose-200',
    violet: 'bg-violet-50 text-violet-700 border-violet-200',
  };
  return (
    <span className={`inline-flex items-center text-[10px] font-mono px-2 py-0.5 rounded-full font-semibold border ${tones[tone]}`}>
      {label}
    </span>
  );
}

type BadgeTone = 'slate' | 'indigo' | 'emerald' | 'amber' | 'rose' | 'sky';

const BADGE_TONES: Record<BadgeTone, string> = {
  slate: 'bg-slate-100 text-slate-600 border-slate-200',
  indigo: 'bg-indigo-50 text-indigo-700 border-indigo-200',
  emerald: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  amber: 'bg-amber-50 text-amber-700 border-amber-200',
  rose: 'bg-rose-50 text-rose-700 border-rose-200',
  sky: 'bg-sky-50 text-sky-700 border-sky-200',
};

/** Simple badge — children-driven. Use StatusPill for pipeline status with predefined labels. */
export function Badge({
  tone = 'slate',
  children,
}: {
  tone?: BadgeTone;
  children: React.ReactNode;
}) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-mono font-bold border ${BADGE_TONES[tone]}`}
    >
      {children}
    </span>
  );
}

/** Map a status string to a tone. */
export function statusTone(status: string): BadgeTone {
  switch (status) {
    case 'active':
    case 'approved':
    case 'published':
    case 'completed':
    case 'healthy':
      return 'emerald';
    case 'submitted':
    case 'draft':
    case 'checked_in':
      return 'amber';
    case 'inactive':
    case 'rejected':
    case 'cancelled':
    case 'unhealthy':
      return 'rose';
    default:
      return 'slate';
  }
}

// ---------------------------------------------------------------------------
// Status metadata maps (Vietnamese, per CONTEXT.md)
// ---------------------------------------------------------------------------

export const CANDIDATE_STATUS_META: Record<
  string,
  { label: string; tone: 'slate' | 'indigo' | 'amber' | 'emerald' | 'rose' | 'violet' }
> = {
  new: { label: 'Mới', tone: 'slate' },
  reviewing: { label: 'Đang review', tone: 'indigo' },
  interview_scheduled: { label: 'Đã lên lịch PV', tone: 'violet' },
  accepted: { label: 'Đã nhận', tone: 'emerald' },
  rejected: { label: 'Từ chối', tone: 'rose' },
  archived: { label: 'Lưu trữ', tone: 'slate' },
};

export const INBOX_STATUS_META: Record<
  string,
  { label: string; tone: 'amber' | 'rose' | 'indigo' | 'slate' }
> = {
  needs_classification: { label: 'Cần xác nhận phân loại', tone: 'amber' },
  needs_information: { label: 'Cần bổ sung thông tin', tone: 'rose' },
  ready_for_review: { label: 'Sẵn sàng review', tone: 'indigo' },
  resolved: { label: 'Đã xử lý', tone: 'slate' },
};

export const JOB_STATUS_META: Record<
  string,
  { label: string; tone: 'slate' | 'emerald' | 'indigo' | 'rose' }
> = {
  draft: { label: 'Bản nháp', tone: 'slate' },
  open: { label: 'Đang tuyển', tone: 'emerald' },
  closed: { label: 'Đã đóng', tone: 'indigo' },
  cancelled: { label: 'Đã hủy', tone: 'rose' },
};

export const CONFLICT_STATUS_META: Record<
  string,
  { label: string; tone: 'amber' | 'emerald' | 'rose' | 'slate' }
> = {
  pending: { label: 'Chờ xử lý', tone: 'amber' },
  resolved: { label: 'Đã giải quyết', tone: 'emerald' },
};

export const AUDIT_ACTION_LABELS: Record<string, string> = {
  role_change: 'Thay đổi quyền',
  user_create: 'Tạo tài khoản',
  user_update: 'Cập nhật tài khoản',
  user_delete: 'Xóa tài khoản',
  permission_grant: 'Cấp quyền',
  permission_revoke: 'Thu hồi quyền',
  login: 'Đăng nhập',
  settings_update: 'Cập nhật cài đặt',
  employee_create: 'Tạo nhân viên',
  employee_update: 'Cập nhật nhân viên',
  whitelist_add: 'Thêm whitelist',
  whitelist_remove: 'Xóa whitelist',
  oauth_update: 'Cập nhật OAuth',
  org_domain_update: 'Cập nhật domain',
  assistant_tool_config: 'Cấu hình tool assistant',
  org_google_connect: 'Kết nối Google',
  org_google_reconnect: 'Kết nối lại Google',
  org_google_switch_account: 'Chuyển tài khoản Google',
  org_google_disconnect: 'Ngắt kết nối Google',
  org_ai_config_update: 'Cập nhật cấu hình AI',
  org_ai_config_rotate: 'Xoay API key AI',
  org_ai_config_revoke: 'Thu hồi cấu hình AI',
  org_ai_config_source: 'Thay đổi nguồn credential AI',
  org_ai_classification_rollout: 'Triển khai phân loại AI',
};

export const MIME_TYPE_LABELS: Record<string, string> = {
  'application/pdf': 'PDF',
  'application/msword': 'Word',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'Word (DOCX)',
  'text/plain': 'Văn bản',
  'image/png': 'PNG',
  'image/jpeg': 'JPEG',
};

export const SERVICE_LABELS: Record<string, string> = {
  redis: 'Bộ nhớ đệm',
  postgresql: 'Cơ sở dữ liệu',
  minio: 'Lưu trữ tài liệu',
  'gmail-worker': 'Đồng bộ email',
  'onboarding-worker': 'Xử lý onboarding',
};

// ---------------------------------------------------------------------------
// Page header
// ---------------------------------------------------------------------------

export function PageHeader({
  icon: Icon,
  title,
  subtitle,
  actions,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-3">
      <div>
        <div className="flex items-center gap-2 text-indigo-600 mb-1">
          <Icon className="w-5 h-5" />
          <h1 className="text-xl font-bold text-slate-900">{title}</h1>
        </div>
        {subtitle && <p className="text-sm text-slate-500">{subtitle}</p>}
      </div>
      {actions && <div className="shrink-0">{actions}</div>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Card / section / field primitives
// ---------------------------------------------------------------------------

export function Card({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`p-5 bg-white rounded-2xl border border-slate-200 shadow-sm shadow-slate-100 ${className}`}>
      {children}
    </div>
  );
}

export function SectionTitle({
  icon: Icon,
  children,
}: {
  icon: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <Icon className="w-5 h-5 text-indigo-600" />
      <h2 className="font-bold text-slate-900">{children}</h2>
    </div>
  );
}

export function Field({
  label,
  children,
  hint,
}: {
  label: string;
  children: React.ReactNode;
  hint?: string;
}) {
  return (
    <label className="block">
      <span className="text-xs font-semibold text-slate-600 mb-1 block">{label}</span>
      {children}
      {hint && <span className="text-[10px] text-slate-400 mt-1 block">{hint}</span>}
    </label>
  );
}

const inputCls =
  'w-full px-3 py-2 rounded-lg border border-slate-200 bg-white text-sm text-slate-900 placeholder-slate-300 focus:outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 transition-all';

export function TextInput(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={`${inputCls} ${props.className ?? ''}`} />;
}

export function TextArea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...props} className={`${inputCls} ${props.className ?? ''}`} />;
}

export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} className={`${inputCls} ${props.className ?? ''}`} />;
}

// ---------------------------------------------------------------------------
// Buttons — rounded-full per AI Studio DESIGN.md (pill: 9999px)
// ---------------------------------------------------------------------------

const BTN =
  'inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-full text-xs font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed';

export function ButtonPrimary(props: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={`${BTN} bg-indigo-600 text-white hover:bg-indigo-500 shadow-sm shadow-indigo-100 ${props.className ?? ''}`}
    />
  );
}

export function ButtonGhost(props: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={`${BTN} bg-white text-slate-600 border border-slate-200 hover:bg-slate-50 ${props.className ?? ''}`}
    />
  );
}

export function ButtonDanger(props: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={`${BTN} bg-rose-50 text-rose-600 border border-rose-200 hover:bg-rose-100 ${props.className ?? ''}`}
    />
  );
}

// ---------------------------------------------------------------------------
// Modal (lightweight)
// ---------------------------------------------------------------------------

export function Modal({
  open,
  onClose,
  title,
  children,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}) {
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="w-full max-w-lg bg-white rounded-2xl border border-slate-200 shadow-xl p-5 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-slate-900 text-sm">{title}</h3>
          <button
            onClick={onClose}
            aria-label="Đóng"
            className="text-slate-400 hover:text-slate-600 text-lg leading-none"
          >
            ×
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Formatting helpers
// ---------------------------------------------------------------------------

/** Format a string Decimal/number as VND currency. */
export function formatVND(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === '') return '—';
  const n = typeof value === 'string' ? Number(value) : value;
  if (!Number.isFinite(n)) return String(value);
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
    maximumFractionDigits: 0,
  }).format(n);
}

/** Format an ISO date/time into a Vietnamese localized string. */
export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return String(iso);
  return d.toLocaleString('vi-VN');
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return String(iso);
  return d.toLocaleDateString('vi-VN');
}

/**
 * Format runtime detail string for HR users.
 * - null/undefined → empty string
 * - "last beat:" prefix → relative time in Vietnamese
 * - heartbeat-related → "Không hoạt động"
 * - fallback: return detail as-is
 */
export function formatRuntimeDetail(detail: string | null): string {
  if (detail == null) return '';
  if (detail.startsWith('last beat:')) {
    const raw = detail.slice('last beat:'.length).trim();
    const ts = parseFloat(raw);
    if (Number.isNaN(ts)) return detail;
    const now = Date.now() / 1000;
    const diff = Math.max(0, now - ts);
    if (diff < 60) return 'Vừa xong';
    if (diff < 3600) return `${Math.floor(diff / 60)} phút trước`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} giờ trước`;
    return `${Math.floor(diff / 86400)} ngày trước`;
  }
  if (detail === 'no heartbeat' || detail.includes('heartbeat'))
    return 'Không hoạt động';
  return detail;
}

/** Format latency in ms → Vietnamese qualitative label. */
export function formatLatency(latencyMs: number | null): string {
  if (latencyMs == null) return '';
  if (latencyMs < 100) return 'Nhanh';
  if (latencyMs < 500) return 'Bình thường';
  return 'Chậm';
}

/** Format audit details as a Vietnamese-readable string (never raw JSON). */
export function formatAuditDetails(details: unknown): string {
  if (!details) return '—';
  if (typeof details !== 'object' || details === null) return String(details);

  const fieldMap: Record<string, string> = {
    role: 'Quyền',
    email: 'Email',
    name: 'Tên',
    employee_id: 'Mã NV',
    permissions: 'Quyền hạn',
  };

  try {
    const entries = Object.entries(details as Record<string, unknown>);
    if (entries.length === 0) return '—';
    return entries
      .map(([key, value]) => {
        const label = fieldMap[key] ?? key;
        const val =
          typeof value === 'object' ? JSON.stringify(value) : String(value);
        return `${label}: ${val}`;
      })
      .join(', ');
  } catch {
    return JSON.stringify(details);
  }
}

/** Confidence as percent. */
export function confidencePct(c: number | null | undefined): string {
  if (c == null) return '—';
  return `${Math.round(c * 100)}%`;
}
