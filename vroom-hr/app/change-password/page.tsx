'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useQueryClient } from '@tanstack/react-query';
import { Shield, AlertTriangle, Eye, EyeOff, CheckCircle } from 'lucide-react';
import { changePassword, type CurrentUser } from '@/lib/api/auth';
import { useSession } from '@/lib/auth/session';
import { getErrorMessage } from '@/lib/api/error-codes';
import type { ApiError } from '@/lib/api/types';

export default function ChangePasswordPage() {
  const router = useRouter();
  const qc = useQueryClient();
  const { isAuthenticated, mustChangePassword, isLoading } = useSession();

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);

  // Redirect if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace('/login');
    }
  }, [isLoading, isAuthenticated, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess(false);

    if (!currentPassword || !newPassword) {
      setError('Vui lòng nhập đầy đủ thông tin.');
      return;
    }
    if (newPassword.length < 12) {
      setError('Mật khẩu mới phải từ 12 ký tự trở lên.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('Xác nhận mật khẩu mới không trùng khớp.');
      return;
    }
    if (newPassword === currentPassword) {
      setError('Mật khẩu mới không được trùng với mật khẩu hiện tại.');
      return;
    }

    setIsSubmitting(true);
    try {
      const result = await changePassword(currentPassword, newPassword);
      // BUG-10 fix: BE set HttpOnly cookie mới + đỗi mật khẩu, nhưng useSession() chỉ
      // biết user qua GET /api/auth/me — React Query cache ['session'] vãn giư giá
      // trị STALE (user củ với must_change_password=true, hoặc null từ khi /login mount
      // lần đầu 401). Nếu không sync cache ngay, trang protected tiếp theo thấy
      // isAuthenticated=false (stale) → redirect /login nhầm → T4 timeout → cascade
      // T5/T6/T7. Change-password response body đã chứa user mới đầy đủ, dụng nó cập
      // nhật cache ngay (cookie HttpOnly không đọc được từ JS).
      qc.setQueryData<CurrentUser | null>(['session'], result.user);
      setSuccess(true);
      // Redirect theo role: admin → /dashboard, employee (ESS) → /employee.
      // Trước đây hardcode '/dashboard' cho mọi user → employee bị /dashboard
      // (admin-only) bounce /employee, gây detour + /admin 403 noise + race.
      const target = result.user.role === 'admin' ? '/dashboard' : '/employee';
      setTimeout(() => {
        router.replace(target);
      }, 2000);

    } catch (err: unknown) {
      if (err instanceof Error) {
        const apiErr = err as ApiError;
        const msg = getErrorMessage(apiErr.errorCode) || apiErr.message || 'Đổi mật khẩu thất bại. Vui lòng thử lại.';
        setError(msg);
      } else {
        setError('Đổi mật khẩu thất bại. Vui lòng thử lại.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50">
        <div className="animate-spin w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-screen p-4 bg-slate-50 text-slate-900 relative overflow-hidden">
      <div className="absolute top-[-20%] left-[-20%] w-[60%] h-[60%] rounded-full bg-indigo-50/40 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-20%] w-[60%] h-[60%] rounded-full bg-indigo-100/30 blur-[120px] pointer-events-none" />

      <div className="w-full max-w-md p-8 bg-white/95 backdrop-blur-xl rounded-2xl border border-slate-200/80 shadow-xl shadow-slate-100 relative z-10">
        {/* Brand Banner */}
        <div className="flex items-center gap-3 mb-8">
          <div className="p-2 bg-gradient-to-tr from-indigo-600 to-indigo-500 rounded-lg text-white font-black tracking-tighter text-xl shadow-md shadow-indigo-100">
            VR
          </div>
          <div>
            <span className="font-sans font-bold text-lg tracking-tight text-slate-900 block">Vroom HR</span>
            <span className="text-xs text-slate-500 block font-mono">Đổi mật khẩu</span>
          </div>
        </div>

        {mustChangePassword && !success && (
          <div className="p-3 mb-6 bg-amber-50 border border-amber-200 text-amber-700 rounded-xl text-sm flex items-start gap-2">
            <Shield className="w-4 h-4 shrink-0 mt-0.5" />
            <span>Bạn cần đổi mật khẩu trước khi tiếp tục sử dụng hệ thống.</span>
          </div>
        )}

        {error && (
          <div className="p-3 mb-6 bg-rose-50 border border-rose-200 text-rose-600 rounded-xl text-sm flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="p-6 mb-6 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-xl text-center">
            <CheckCircle className="w-12 h-12 mx-auto mb-3 text-emerald-500" />
            <p className="font-semibold">Đổi mật khẩu thành công!</p>
            <p className="text-sm mt-1">Đang chuyển hướng đến trang quản trị...</p>
          </div>
        )}

        {!success && (
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-xs font-mono uppercase text-slate-500 mb-2 font-semibold">Mật khẩu hiện tại</label>
              <div className="relative">
                <input
                  id="change-password-current-input"
                  type={showCurrent ? 'text' : 'password'}
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="Nhập mật khẩu hiện tại..."
                  className="w-full p-3 pr-10 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                  required
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowCurrent(!showCurrent)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showCurrent ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-mono uppercase text-slate-500 mb-2 font-semibold">Mật khẩu mới (≥12 ký tự)</label>
              <div className="relative">
                <input
                  id="change-password-new-input"
                  type={showNew ? 'text' : 'password'}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Nhập mật khẩu mới..."
                  className="w-full p-3 pr-10 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                  required
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  onClick={() => setShowNew(!showNew)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showNew ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-mono uppercase text-slate-500 mb-2 font-semibold">Xác nhận mật khẩu mới</label>
              <input
                id="change-password-confirm-input"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Gõ lại mật khẩu mới..."
                className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                required
                autoComplete="new-password"
              />
            </div>

            <button
              id="change-password-submit-button"
              type="submit"
              disabled={isSubmitting}
              className="w-full py-3.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-semibold rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-indigo-100 transition-all"
            >
              {isSubmitting ? 'Đang xử lý...' : 'Đổi mật khẩu'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
