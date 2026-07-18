import { ApiError } from '@/lib/api/types';
import { getErrorMessage } from '@/lib/api/error-codes';

export function fmtDate(iso: string | null): string {
  if (!iso) return '—';
  try { return new Date(iso).toLocaleString('vi-VN'); } catch { return iso; }
}

export function apiErrorText(err: unknown): string {
  if (err instanceof ApiError) return getErrorMessage(err.errorCode);
  if (err instanceof Error) return err.message;
  return 'Lỗi không xác định';
}

export const NAVY = 'bg-slate-900';
