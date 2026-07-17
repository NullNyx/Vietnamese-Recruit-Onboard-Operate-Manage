'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FileSpreadsheet, Eye } from 'lucide-react';
import { fetchMyPayslips, fetchMyPayslip } from '@/lib/api/payslips';
import type { Payslip, PayslipListResponse } from '@/lib/api/payslips';
import { useAuthGuard } from '@/lib/auth/session';
import {
  PageHeader, Card, SectionTitle, ButtonPrimary, ErrorAlert, EmptyState, Badge, Modal, formatVND, formatDateTime,
} from '@/components/operate';

export default function EmployeePayslipsPage() {
  useAuthGuard({ requireAuth: true, requireEmployee: true });

  const { data, isLoading, error } = useQuery<PayslipListResponse>({
    queryKey: ['my-payslips'],
    queryFn: fetchMyPayslips,
  });

  const [viewId, setViewId] = useState<string | null>(null);
  const { data: viewed } = useQuery<Payslip>({
    queryKey: ['my-payslip', viewId],
    queryFn: () => fetchMyPayslip(viewId!),
    enabled: Boolean(viewId),
  });

  const toMonth = (p: string) => (p ? p.slice(0, 7) : '—');

  // BUG-12 defense-in-depth: BE `/api/payslips/me` đã filter `status='published'`
  // (payslip_repository.list_by_employee). FE filter lại một lần nữa để bảo
  // boundary Employee-chỉ-xem-published ngay cả nếu BE ever leak — KHÔNG bao
  // giờ render row draft/unpublished (và cũng không render label liên quan).
  const publishedPayslips = (data?.payslips ?? []).filter(
    (p) => p.status === 'published',
  );

  return (
    <div className="space-y-6">
      <PageHeader
        icon={FileSpreadsheet}
        title="Phiếu lương"
        subtitle="Xem phiếu lương đã phát hành của bạn."
      />

      <Card>
        <SectionTitle icon={FileSpreadsheet}>Danh sách phiếu lương</SectionTitle>
        {error ? <ErrorAlert error={error} title="Không tải được phiếu lương" />
          : isLoading && !data ? <p className="text-sm text-slate-400">Đang tải…</p>
          : !publishedPayslips.length ? <EmptyState hasFilters={false} emptyData="Chưa có phiếu lương nào được phát hành cho bạn." />
          : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-[10px] font-mono uppercase text-slate-400 border-b border-slate-100">
                    <th className="py-2 px-2">Kỳ lương</th>
                    <th className="py-2 px-2">Lương gross</th>
                    <th className="py-2 px-2">Lương net</th>
                    <th className="py-2 px-2">Phát hành</th>
                    <th className="py-2 px-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {publishedPayslips.map((p) => (
                    <tr key={p.id} className="border-b border-slate-50 hover:bg-slate-50">
                      <td className="py-2.5 px-2 font-mono text-xs text-slate-600">{toMonth(p.period_month)}</td>
                      <td className="py-2.5 px-2 text-xs text-slate-600">{formatVND(p.gross_salary)}</td>
                      <td className="py-2.5 px-2 text-xs font-semibold text-slate-800">{formatVND(p.net_salary)}</td>
                      <td className="py-2.5 px-2"><Badge tone="emerald">Đã phát hành</Badge></td>
                      <td className="py-2.5 px-2">
                        <button onClick={() => setViewId(p.id)} className="p-1.5 rounded-lg hover:bg-slate-200 text-slate-500 hover:text-indigo-600 transition-all" title="Xem chi tiết">
                          <Eye className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
      </Card>

      <Modal open={!!viewId} onClose={() => setViewId(null)} title="Chi tiết phiếu lương">
        {viewed && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Badge tone="emerald">Đã phát hành</Badge>
              <span className="font-mono text-[10px] text-slate-400">Kỳ {toMonth(viewed.period_month)} · phát hành {formatDateTime(viewed.published_at)}</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <Row label="Lương gross" value={formatVND(viewed.gross_salary)} />
              <Row label="Lương net" value={formatVND(viewed.net_salary)} />
              <Row label="Khấu trừ" value={formatVND(viewed.deductions)} />
              <Row label="Bảo hiểm (NV)" value={formatVND(viewed.insurance_employee)} />
              <Row label="Thu nhập chịu thuế" value={formatVND(viewed.taxable_income)} />
              <Row label="Thuế TNCN" value={formatVND(viewed.pit_amount)} />
            </div>
            <div className="flex justify-end pt-2">
              <ButtonPrimary onClick={() => setViewId(null)}>Đóng</ButtonPrimary>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-2 bg-slate-50 rounded-lg border border-slate-100">
      <p className="text-[10px] font-mono text-slate-400 uppercase">{label}</p>
      <p className="text-xs font-semibold text-slate-800">{value}</p>
    </div>
  );
}