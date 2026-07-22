import { ApiError } from '@/lib/api/types';
import { getErrorMessage } from '@/lib/api/error-codes';

export function fmtDate(iso: string | null): string {
  if (!iso) return '—';
  try {
    // Backend có thể gửi Unix timestamp (giây) dạng string hoặc ISO 8601
    const parsed = Number(iso);
    const date = Number.isFinite(parsed) && parsed > 1000000000
      ? new Date(parsed * 1000) // Unix timestamp giây → ms
      : new Date(iso);          // ISO 8601
    if (isNaN(date.getTime())) return iso;
    return date.toLocaleString('vi-VN');
  } catch {
    return iso;
  }
}

export function apiErrorText(err: unknown): string {
  if (err instanceof ApiError) return getErrorMessage(err.errorCode);
  if (err instanceof Error) return err.message;
  return 'Lỗi không xác định';
}

export const NAVY = 'bg-slate-900';
