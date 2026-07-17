/**
 * Shared UI primitives for the Phase 2 Operate surfaces (Employees,
 * Attendance, Employee Requests, Payslips) — HR and ESS.
 *
 * Kept intentionally tiny and dependency-free (only lucide-react) so each
 * feature page can compose them without importing a heavy design library.
 * Styling follows the AI Studio design system: slate/indigo, rounded-2xl
 * cards, soft shadows, mono accents.
 */

'use client';

import React from 'react';
import { AlertTriangle, Inbox, Loader2 } from 'lucide-react';
import { ApiError } from '@/lib/api/types';
import { getErrorMessage } from '@/lib/api/error-codes';

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
// Loading
// ---------------------------------------------------------------------------

export function Loading({ label = 'Đang tải…' }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 text-sm text-slate-400 py-4">
      <Loader2 className="w-4 h-4 animate-spin" />
      {label}
    </div>
  );
}

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
// Error — renders BE error_code via the registry when available
// ---------------------------------------------------------------------------

export function ErrorAlert({ error, title = 'Đã xảy ra lỗi' }: { error: unknown; title?: string }) {
  if (!error) return null;
  let message: string;
  let code: string | undefined;
  if (error instanceof ApiError) {
    code = error.errorCode;
    message = getErrorMessage(error.errorCode);
    // If the registry fell back to the raw code, prefer the BE message instead.
    if (message === `Lỗi: ${error.errorCode}` && error.message) {
      message = error.message;
    }
  } else if (error instanceof Error) {
    message = error.message;
  } else {
    message = 'Lỗi không xác định';
  }
  return (
    <div className="flex items-start gap-2 p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700">
      <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
      <div className="text-xs">
        <p className="font-semibold">{title}</p>
        <p className="mt-0.5">{message}</p>
        {code && code !== 'UNKNOWN_ERROR' && (
          <p className="mt-0.5 font-mono text-[10px] text-rose-500/80">error_code: {code}</p>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Empty state — distinguishes "filter matched nothing" vs "no data yet"
// ---------------------------------------------------------------------------

export function EmptyState({
  hasFilters,
  emptyFiltered = 'Không có bản ghi nào khớp với bộ lọc hiện tại.',
  emptyData = 'Chưa có bản ghi nào.',
}: {
  hasFilters: boolean;
  emptyFiltered?: string;
  emptyData?: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-10 px-4">
      <div className="p-2.5 bg-slate-100 rounded-xl mb-3">
        <Inbox className="w-6 h-6 text-slate-400" />
      </div>
      <p className="text-sm text-slate-500 max-w-sm">
        {hasFilters ? emptyFiltered : emptyData}
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Badge
// ---------------------------------------------------------------------------

type BadgeTone = 'slate' | 'indigo' | 'emerald' | 'amber' | 'rose' | 'sky';

const TONES: Record<BadgeTone, string> = {
  slate: 'bg-slate-100 text-slate-600 border-slate-200',
  indigo: 'bg-indigo-50 text-indigo-700 border-indigo-200',
  emerald: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  amber: 'bg-amber-50 text-amber-700 border-amber-200',
  rose: 'bg-rose-50 text-rose-700 border-rose-200',
  sky: 'bg-sky-50 text-sky-700 border-sky-200',
};

export function Badge({
  tone = 'slate',
  children,
}: {
  tone?: BadgeTone;
  children: React.ReactNode;
}) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-mono font-bold border ${TONES[tone]}`}
    >
      {children}
    </span>
  );
}

/** Map a status string to a tone + Vietnamese label. */
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
// Card / section / field primitives
// ---------------------------------------------------------------------------

export function Card({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`p-5 bg-white rounded-2xl border border-slate-200 shadow-sm shadow-slate-100 ${className}`}>
      {children}
    </div>
  );
}

export function SectionTitle({ icon: Icon, children }: { icon: React.ComponentType<{ className?: string }>; children: React.ReactNode }) {
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
// Buttons
// ---------------------------------------------------------------------------

const BTN =
  'inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed';

export function ButtonPrimary(props: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button {...props} className={`${BTN} bg-indigo-600 text-white hover:bg-indigo-500 shadow-sm shadow-indigo-100 ${props.className ?? ''}`} />;
}

export function ButtonGhost(props: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button {...props} className={`${BTN} bg-white text-slate-600 border border-slate-200 hover:bg-slate-50 ${props.className ?? ''}`} />;
}

export function ButtonDanger(props: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button {...props} className={`${BTN} bg-rose-50 text-rose-600 border border-rose-200 hover:bg-rose-100 ${props.className ?? ''}`} />;
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="w-full max-w-lg bg-white rounded-2xl border border-slate-200 shadow-xl p-5 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-slate-900 text-sm">{title}</h3>
          <button onClick={onClose} aria-label="Đóng" className="text-slate-400 hover:text-slate-600 text-lg leading-none">×</button>
        </div>
        {children}
      </div>
    </div>
  );
}

/** Format a string Decimal/number as VND currency. */
export function formatVND(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === '') return '—';
  const n = typeof value === 'string' ? Number(value) : value;
  if (!Number.isFinite(n)) return String(value);
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', maximumFractionDigits: 0 }).format(n);
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