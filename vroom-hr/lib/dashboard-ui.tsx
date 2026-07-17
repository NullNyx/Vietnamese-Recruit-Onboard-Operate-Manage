'use client';

import React from 'react';
import { AlertTriangle, Inbox } from 'lucide-react';
import type { ApiError } from '@/lib/api/types';
import { getErrorMessage } from '@/lib/api/error-codes';

/** Render a BE error_code with the mapped Vietnamese message (never self-fabricated). */
export function ErrorBanner({ error }: { error: unknown }) {
  if (!error) return null;
  let msg = 'Đã xảy ra lỗi. Vui lòng thử lại.';
  let code = '';
  if (error instanceof Error) {
    const apiErr = error as ApiError;
    code = apiErr.errorCode ?? '';
    msg = code ? getErrorMessage(code) : apiErr.message;
  }
  return (
    <div className="p-3 bg-rose-50 border border-rose-200 text-rose-600 rounded-xl text-sm flex items-start gap-2">
      <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
      <div className="min-w-0">
        <p className="break-words">{msg}</p>
        {code && <code className="text-[11px] font-mono text-rose-400">{code}</code>}
      </div>
    </div>
  );
}

/** Loading spinner. */
export function Loading({ label = 'Đang tải...' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="animate-spin w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full" />
      <span className="ml-3 text-sm text-slate-500">{label}</span>
    </div>
  );
}

/**
 * Empty state. Use `filtered` to distinguish "trống do bộ lọc" vs "chưa có dữ liệu"
 * (per CONTEXT.md UX language).
 */
export function EmptyState({
  filtered,
  onReset,
}: {
  filtered: boolean;
  onReset?: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <Inbox className="w-10 h-10 text-slate-300 mb-3" />
      <p className="text-sm font-medium text-slate-600">
        {filtered ? 'Không có bản ghi khớp với bộ lọc hiện tại.' : 'Chưa có bản ghi nào.'}
      </p>
      <p className="text-xs text-slate-400 mt-1">
        {filtered ? 'Thử thay đổi từ khóa hoặc bộ lọc.' : 'Dữ liệu sẽ xuất hiện khi có bản ghi.'}
      </p>
      {filtered && onReset && (
        <button
          onClick={onReset}
          className="mt-4 px-4 py-2 text-xs font-medium bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-lg transition-all"
        >
          Xóa bộ lọc
        </button>
      )}
    </div>
  );
}

/** Status pill — color by group; label Vietnamese. */
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

/** Candidate status → {label, tone} (Vietnamese, per CONTEXT.md pipeline). */
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

/** Inbox status → {label, tone, group}. */
export const INBOX_STATUS_META: Record<
  string,
  { label: string; tone: 'amber' | 'rose' | 'indigo' | 'slate' }
> = {
  needs_classification: { label: 'Cần xác nhận phân loại', tone: 'amber' },
  needs_information: { label: 'Cần bổ sung thông tin', tone: 'rose' },
  ready_for_review: { label: 'Sẵn sàng review', tone: 'indigo' },
  resolved: { label: 'Đã xử lý', tone: 'slate' },
};

/** Job Opening status → {label, tone}. */
export const JOB_STATUS_META: Record<
  string,
  { label: string; tone: 'slate' | 'emerald' | 'indigo' | 'rose' }
> = {
  draft: { label: 'Bản nháp', tone: 'slate' },
  open: { label: 'Đang tuyển', tone: 'emerald' },
  closed: { label: 'Đã đóng', tone: 'indigo' },
  cancelled: { label: 'Đã hủy', tone: 'rose' },
};
    /** Conflict interview status → {label, tone} (Vietnamese). */
    export const CONFLICT_STATUS_META: Record<
      string,
      { label: string; tone: 'amber' | 'emerald' | 'rose' | 'slate' }
    > = {
      pending: { label: 'Chờ xử lý', tone: 'amber' },
      resolved: { label: 'Đã giải quyết', tone: 'emerald' },
    };

    /** Audit action type → Vietnamese label. */
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

    /** MIME type → human-readable label. */
    export const MIME_TYPE_LABELS: Record<string, string> = {
      'application/pdf': 'PDF',
      'application/msword': 'Word',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'Word (DOCX)',
      'text/plain': 'Văn bản',
      'image/png': 'PNG',
      'image/jpeg': 'JPEG',
    };

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
            const val = typeof value === 'object' ? JSON.stringify(value) : String(value);
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