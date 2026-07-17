'use client';

import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Clock, LogIn, LogOut, CalendarDays } from 'lucide-react';
import {
  checkIn, checkOut, getTodayRecord, getMyHistory,
} from '@/lib/api/attendance';
import type { AttendanceRecord, HistoryResponse } from '@/lib/api/attendance';
import { useAuthGuard } from '@/lib/auth/session';
import {
  PageHeader, Card, SectionTitle, ButtonPrimary, ErrorAlert, EmptyState, Badge, formatDateTime,
} from '@/components/shared-ui';

export default function EmployeeAttendancePage() {
  useAuthGuard({ requireAuth: true, requireEmployee: true });
  const qc = useQueryClient();

  const { data: today, isLoading, error } = useQuery<AttendanceRecord | null>({
    queryKey: ['attendance-today', 'me'],
    queryFn: () => getTodayRecord(),
  });

  const { data: history } = useQuery<HistoryResponse>({
    queryKey: ['attendance-history', 'me'],
    queryFn: () => getMyHistory({ days: 30 }),
  });

  const checkInMut = useMutation({
    mutationFn: () => checkIn(),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['attendance-today', 'me'] }),
  });
  const checkOutMut = useMutation({
    mutationFn: () => checkOut(),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['attendance-today', 'me'] }),
  });

  const checkedIn = Boolean(today?.check_in_at);
  const checkedOut = Boolean(today?.check_out_at);

  return (
    <div className="space-y-6">
      <PageHeader icon={Clock} title="Chấm công" subtitle="Check-in / check-out hôm nay và lịch sử 30 ngày gần đây." />

      {/* Today */}
      <Card>
        <SectionTitle icon={Clock}>Hôm nay</SectionTitle>
        {isLoading ? <p className="text-sm text-slate-400">Đang tải…</p>
          : error ? <ErrorAlert error={error} title="Không tải được bản ghi hôm nay" />
          : (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                  <div className="flex items-center gap-2 mb-1">
                    <LogIn className="w-4 h-4 text-indigo-600" />
                    <span className="text-[10px] font-mono uppercase text-slate-400">Check-in</span>
                  </div>
                  <p className="text-sm font-semibold text-slate-800">{formatDateTime(today?.check_in_at ?? null)}</p>
                  {today?.check_in_ip && <p className="text-[10px] font-mono text-slate-400">{today.check_in_ip}</p>}
                </div>
                <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                  <div className="flex items-center gap-2 mb-1">
                    <LogOut className="w-4 h-4 text-indigo-600" />
                    <span className="text-[10px] font-mono uppercase text-slate-400">Check-out</span>
                  </div>
                  <p className="text-sm font-semibold text-slate-800">{formatDateTime(today?.check_out_at ?? null)}</p>
                  {today?.check_out_ip && <p className="text-[10px] font-mono text-slate-400">{today.check_out_ip}</p>}
                </div>
              </div>

              <div className="flex items-center gap-2 flex-wrap">
                <Badge tone={checkedIn ? 'emerald' : 'slate'}>{checkedIn ? 'Đã check-in' : 'Chưa check-in'}</Badge>
                {checkedOut && <Badge tone="emerald">Đã check-out</Badge>}
              </div>

              <div className="flex gap-2">
                <ButtonPrimary onClick={() => checkInMut.mutate()} disabled={checkInMut.isPending || checkedIn}>
                  <LogIn className="w-4 h-4" /> {checkInMut.isPending ? 'Đang xử lý…' : 'Check-in'}
                </ButtonPrimary>
                <ButtonPrimary onClick={() => checkOutMut.mutate()} disabled={checkOutMut.isPending || !checkedIn || checkedOut}>
                  <LogOut className="w-4 h-4" /> {checkOutMut.isPending ? 'Đang xử lý…' : 'Check-out'}
                </ButtonPrimary>
              </div>

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
        <SectionTitle icon={CalendarDays}>Lịch sử 30 ngày</SectionTitle>
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