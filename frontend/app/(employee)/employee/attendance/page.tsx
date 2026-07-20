'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Clock, LogIn, LogOut, CalendarDays, ChevronLeft, ChevronRight } from 'lucide-react';
import {
  checkIn, checkOut, getTodayRecord, getMyHistory,
} from '@/lib/api/attendance';
import type { AttendanceRecord, HistoryResponse } from '@/lib/api/attendance';
import { useAuthGuard } from '@/lib/auth/session';
import { toast } from 'sonner';
import {
  PageHeader, Card, SectionTitle, ButtonPrimary, ButtonGhost, ButtonDanger, ErrorAlert, EmptyState, Badge, LoadingRows, formatDateTime,
} from '@/components/shared-ui';

/** Format relative time (e.g. "2 giờ trước", "5 phút trước"). */
function relativeTime(iso: string | null): string | null {
  if (!iso) return null;
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'vừa xong';
  if (mins < 60) return `${mins} phút trước`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} giờ trước`;
  const days = Math.floor(hours / 24);
  return `${days} ngày trước`;
}

export default function EmployeeAttendancePage() {
  useAuthGuard({ requireAuth: true, requireEmployee: true });
  const qc = useQueryClient();

  const { data: today, isLoading, error } = useQuery<AttendanceRecord | null>({
    queryKey: ['attendance-today', 'me'],
    queryFn: () => getTodayRecord(),
  });

  const now = new Date();
  const [histYear, setHistYear] = useState(now.getFullYear());
  const [histMonth, setHistMonth] = useState(now.getMonth() + 1);

  const { data: history } = useQuery<HistoryResponse>({
    queryKey: ['attendance-history', 'me', histYear, histMonth],
    queryFn: () => getMyHistory({ year: histYear, month: histMonth }),
  });

  const goPrevMonth = () => {
    if (histMonth === 1) { setHistYear(histYear - 1); setHistMonth(12); }
    else setHistMonth(histMonth - 1);
  };
  const goNextMonth = () => {
    if (histMonth === 12) { setHistYear(histYear + 1); setHistMonth(1); }
    else setHistMonth(histMonth + 1);
  };
  const isCurrentMonth = histYear === now.getFullYear() && histMonth === now.getMonth() + 1;

      const checkInMut = useMutation({
        mutationFn: () => checkIn(),
        retry: 1,
        onSuccess: (data) => {
          qc.invalidateQueries({ queryKey: ['attendance-today', 'me'] });
          toast.success(data.message || 'Check-in thành công!');
        },
        onError: (err: any) => toast.error(err?.message || 'Check-in thất bại'),
      });
      const checkOutMut = useMutation({
        mutationFn: () => checkOut(),
        retry: 1,
        onSuccess: (data) => {
          qc.invalidateQueries({ queryKey: ['attendance-today', 'me'] });
          toast.success(data.message || 'Check-out thành công!');
        },
        onError: (err: any) => toast.error(err?.message || 'Check-out thất bại'),
      });

  const [confirmCheckOut, setConfirmCheckOut] = useState(false);
  const checkedIn = Boolean(today?.check_in_at);
  const checkedOut = Boolean(today?.check_out_at);
  const isMutating = checkInMut.isPending || checkOutMut.isPending;

  return (
    <div className="space-y-6">
      <PageHeader icon={Clock} title="Chấm công" subtitle="Điểm danh đầu giờ và cuối giờ hôm nay, cùng lịch sử chấm công 30 ngày gần nhất." />

      {/* Today */}
      <Card>
        <SectionTitle icon={Clock}>Hôm nay</SectionTitle>
            {isLoading ? <LoadingRows count={2} />
              : error ? <ErrorAlert error={error} title="Không tải được bản ghi hôm nay" />
          : (
            <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    <div className={`p-4 bg-slate-50 rounded-xl border border-slate-100 ${checkInMut.isPending ? 'opacity-60 animate-pulse' : ''}`}>
                      <div className="flex items-center gap-2 mb-1">
                        <LogIn className="w-4 h-4 text-indigo-600" />
                        <span className="text-[10px] font-mono uppercase text-slate-400">Check-in</span>
                        {checkInMut.isPending && <span className="text-[10px] text-indigo-500 animate-pulse">đang xử lý…</span>}
                      </div>
                      <p className="text-sm font-semibold text-slate-800">{formatDateTime(today?.check_in_at ?? null)}</p>
                      {today?.check_in_at && <p className="text-[10px] text-slate-400">{relativeTime(today.check_in_at)}</p>}
                      {today?.check_in_ip && <p className="text-[10px] font-mono text-slate-400">{today.check_in_ip}</p>}
                    </div>
                    <div className={`p-4 bg-slate-50 rounded-xl border border-slate-100 ${checkOutMut.isPending ? 'opacity-60 animate-pulse' : ''}`}>
                      <div className="flex items-center gap-2 mb-1">
                        <LogOut className="w-4 h-4 text-indigo-600" />
                        <span className="text-[10px] font-mono uppercase text-slate-400">Check-out</span>
                        {checkOutMut.isPending && <span className="text-[10px] text-indigo-500 animate-pulse">đang xử lý…</span>}
                      </div>
                      <p className="text-sm font-semibold text-slate-800">{formatDateTime(today?.check_out_at ?? null)}</p>
                      {today?.check_out_at && <p className="text-[10px] text-slate-400">{relativeTime(today.check_out_at)}</p>}
                      {today?.check_out_ip && <p className="text-[10px] font-mono text-slate-400">{today.check_out_ip}</p>}
                    </div>
                  </div>

              <div className="flex items-center gap-2 flex-wrap">
                <Badge tone={checkedIn ? 'emerald' : 'slate'}>{checkedIn ? 'Đã check-in' : 'Chưa check-in'}</Badge>
                {checkedOut && <Badge tone="emerald">Đã check-out</Badge>}
              </div>

                  <div className="flex gap-2">
                    <ButtonPrimary onClick={() => checkInMut.mutate()} disabled={isMutating || checkedIn}>
                      <LogIn className="w-4 h-4" /> {checkInMut.isPending ? 'Đang xử lý…' : 'Check-in'}
                    </ButtonPrimary>
                    <ButtonPrimary onClick={() => setConfirmCheckOut(true)} disabled={isMutating || !checkedIn || checkedOut}>
                      <LogOut className="w-4 h-4" /> Check-out
                    </ButtonPrimary>
                  </div>

                  {/* Check-out confirmation */}
                  {confirmCheckOut && (
                    <div className="p-3 bg-amber-50 rounded-xl border border-amber-200 space-y-2">
                      <p className="text-xs text-amber-800">Xác nhận check-out — thao tác này đánh dấu kết thúc ngày làm việc hôm nay.</p>
                      <div className="flex gap-2">
                        <ButtonDanger onClick={() => { setConfirmCheckOut(false); checkOutMut.mutate(); }} disabled={checkOutMut.isPending}>
                          {checkOutMut.isPending ? 'Đang xử lý…' : 'Xác nhận Check-out'}
                        </ButtonDanger>
                        <ButtonGhost onClick={() => setConfirmCheckOut(false)} disabled={checkOutMut.isPending}>Hủy</ButtonGhost>
                      </div>
                    </div>
                  )}

              {checkInMut.isError && <ErrorAlert error={checkInMut.error} />}
              {checkOutMut.isError && <ErrorAlert error={checkOutMut.error} />}
              <p className="text-[10px] text-slate-400">
                Chấm công bị giới hạn theo Network Allowlist (CIDR) do HR cấu hình. Nếu ngoài mạng văn phòng, kiểm tra liên hệ HR.
              </p>
            </div>
          )}
      </Card>

          {/* History */}
          <Card>
            <div className="flex items-center justify-between mb-3">
              <SectionTitle icon={CalendarDays}>Lịch sử chấm công</SectionTitle>
              <div className="flex items-center gap-2">
                <button onClick={goPrevMonth} className="p-1 rounded hover:bg-slate-100"><ChevronLeft className="w-4 h-4" /></button>
                <span className="text-xs font-medium text-slate-700 min-w-[100px] text-center">
                  Tháng {histMonth}/{histYear}
                </span>
                <button onClick={goNextMonth} disabled={isCurrentMonth} className="p-1 rounded hover:bg-slate-100 disabled:opacity-30"><ChevronRight className="w-4 h-4" /></button>
              </div>
            </div>
        {!history || !history.records.length ? (
          <EmptyState filtered={false} emptyData="Chưa có bản ghi chấm công nào." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[10px] font-mono uppercase text-slate-400 border-b border-slate-100">
                  <th className="py-2 px-2">Ngày</th>
                  <th className="py-2 px-2">Check-in</th>
                  <th className="py-2 px-2">Check-out</th>
                  <th className="py-2 px-2">Trạng thái</th>
                </tr>
              </thead>
              <tbody>
                {history.records.map((r) => (
                  <tr key={r.id} className="border-b border-slate-50">
                    <td className="py-2.5 px-2 text-xs text-slate-600">{r.work_date}</td>
                    <td className="py-2.5 px-2 text-xs text-slate-600">{formatDateTime(r.check_in_at)}</td>
                    <td className="py-2.5 px-2 text-xs text-slate-600">{formatDateTime(r.check_out_at)}</td>
                    <td className="py-2.5 px-2"><Badge tone={r.check_out_at ? 'emerald' : 'amber'}>{r.check_out_at ? 'Đã check-out' : 'Đã check-in'}</Badge></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}