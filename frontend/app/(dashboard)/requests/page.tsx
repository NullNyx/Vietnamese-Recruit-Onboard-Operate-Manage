'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { FileText, Check, X, Search } from 'lucide-react';
import {
  fetchSubmittedRequests, approveRequest, rejectRequest,
} from '@/lib/api/employee-requests';
import type {
  AdminReviewQueueResponse, AdminEmployeeRequestItem, ReviewQueueFilters,
} from '@/lib/api/employee-requests';
import { listEmployees } from '@/lib/api/employees';
import type { EmployeeListResponse } from '@/lib/api/types';
import { useAuthGuard } from '@/lib/auth/session';
import {
  PageHeader, Card, SectionTitle, Field, TextInput, Select, ButtonPrimary, ButtonGhost, ButtonDanger,
  Badge, ErrorAlert, EmptyState, LoadingRows, Modal, formatDate, formatDateTime,
} from '@/components/shared-ui';

export default function RequestsReviewPage() {
  useAuthGuard({ requireAuth: true, requireAdmin: true });
  const qc = useQueryClient();

  const [requestType, setRequestType] = useState<'' | 'leave' | 'overtime'>('');
  const [statusFilter, setStatusFilter] = useState<'' | 'submitted' | 'approved' | 'rejected' | 'cancelled'>('submitted');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [employeeId, setEmployeeId] = useState('');
  const [submitted, setSubmitted] = useState({ requestType, statusFilter, dateFrom, dateTo, employeeId });

  const { data: employees } = useQuery<EmployeeListResponse>({
    queryKey: ['employees-list', { all: true }],
    queryFn: () => listEmployees({ page: 1, page_size: 100, is_active: true }),
    staleTime: 60_000,
  });

  const filters: ReviewQueueFilters = {
    request_type: submitted.requestType || undefined,
    status: submitted.statusFilter || undefined,
    date_from: submitted.dateFrom || undefined,
    date_to: submitted.dateTo || undefined,
    employee_id: submitted.employeeId || undefined,
  };

  const { data, isLoading, error } = useQuery<AdminReviewQueueResponse>({
    queryKey: ['admin-requests', submitted],
    queryFn: () => fetchSubmittedRequests(filters),
    placeholderData: (prev) => prev,
  });

  const apply = () => setSubmitted({ requestType, statusFilter, dateFrom, dateTo, employeeId });
  const hasFilters =
    Boolean(submitted.requestType || submitted.dateFrom || submitted.dateTo || submitted.employeeId) ||
    submitted.statusFilter !== 'submitted';

  // Approve / reject
  const [rejectTarget, setRejectTarget] = useState<AdminEmployeeRequestItem | null>(null);
  const [rejectReason, setRejectReason] = useState('');

  const approveMut = useMutation({
    mutationFn: (id: string) => approveRequest(id, null),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin-requests'] }),
  });
  const rejectMut = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) => rejectRequest(id, reason),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-requests'] });
      setRejectTarget(null);
      setRejectReason('');
    },
  });

  const renderDetail = (r: AdminEmployeeRequestItem) => {
    if (r.request_type === 'leave') {
      return `${r.leave_type ?? '—'} · ${formatDate(r.start_date)} → ${formatDate(r.end_date)}`;
    }
    return `${formatDate(r.work_date)} · ${r.start_time ?? '—'}→${r.end_time ?? '—'}${r.duration_minutes ? ` (${r.duration_minutes} phút)` : ''}`;
  };

  return (
    <div className="space-y-6">
      <PageHeader
        icon={FileText}
        title="Yêu cầu Nhân viên (Review queue)"
        subtitle="Duyệt hoặc từ chối yêu cầu nghỉ phép và tăng ca của nhân viên. Khi từ chối cần nêu rõ lý do. Mọi quyết định đều được lưu lại."
      />

      <Card>
        <SectionTitle icon={Search}>Bộ lọc</SectionTitle>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3 items-end">
          <Field label="Loại">
            <Select value={requestType} onChange={(e) => setRequestType(e.target.value as '' | 'leave' | 'overtime')}>
              <option value="">Tất cả</option>
              <option value="leave">Nghỉ phép</option>
              <option value="overtime">Tăng ca</option>
            </Select>
          </Field>
          <Field label="Trạng thái">
            <Select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value as '' | 'submitted' | 'approved' | 'rejected' | 'cancelled')}>
              <option value="submitted">Chờ duyệt</option>
              <option value="approved">Đã duyệt</option>
              <option value="rejected">Từ chối</option>
              <option value="cancelled">Đã hủy</option>
              <option value="">Tất cả</option>
            </Select>
          </Field>
          <Field label="Từ ngày"><TextInput type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} /></Field>
          <Field label="Đến ngày"><TextInput type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} /></Field>
          <Field label="Nhân viên">
            <Select value={employeeId} onChange={(e) => setEmployeeId(e.target.value)}>
              <option value="">Tất cả</option>
              {employees?.items?.map((e) => <option key={e.id} value={e.id}>{e.full_name}</option>)}
            </Select>
          </Field>
          <ButtonPrimary onClick={apply} className="h-[38px]"><Search className="w-4 h-4" /> Lọc</ButtonPrimary>
        </div>
      </Card>

      <Card>
        <SectionTitle icon={FileText}>Hàng đợi</SectionTitle>
        {error ? <ErrorAlert error={error} title="Không tải được hàng đợi" />
          : isLoading && !data ? <LoadingRows count={6} />
          : !data?.requests?.length ? <EmptyState filtered={hasFilters} />
          : (
            <div className="space-y-2">
              {data.requests.map((r) => (
                <div key={r.id} className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <Badge tone={r.request_type === 'leave' ? 'sky' : 'indigo'}>{r.request_type === 'leave' ? 'Nghỉ phép' : 'Tăng ca'}</Badge>
                        <Badge tone={statusToneOf(r.status)}>{statusLabel(r.status)}</Badge>
                        <span className="text-xs font-semibold text-slate-800">{r.employee_name}</span>
                        <span className="text-[10px] font-mono text-slate-400">{formatDateTime(r.submitted_at)}</span>
                      </div>
                      <p className="text-xs text-slate-600">{renderDetail(r)}</p>
                      {r.reason && <p className="text-xs text-slate-500 mt-1 italic">"{r.reason}"</p>}
                      {r.review_reason && (
                        <p className="text-[11px] text-slate-500 mt-1">
                          Quyết định: {r.review_reason} · {formatDateTime(r.reviewed_at)}
                        </p>
                      )}
                    </div>
                    {r.status === 'submitted' && (
                      <div className="flex gap-2 shrink-0">
                        <ButtonPrimary
                          onClick={() => approveMut.mutate(r.id)}
                          disabled={approveMut.isPending}
                          className="!px-2.5"
                        >
                          <Check className="w-4 h-4" /> Duyệt
                        </ButtonPrimary>
                        <ButtonDanger onClick={() => setRejectTarget(r)} className="!px-2.5">
                          <X className="w-4 h-4" /> Từ chối
                        </ButtonDanger>
                      </div>
                    )}
                  </div>
                  {approveMut.isError && approveMut.variables === r.id && <div className="mt-2"><ErrorAlert error={approveMut.error} /></div>}
                </div>
              ))}
            </div>
          )}
      </Card>

      <Modal open={!!rejectTarget} onClose={() => setRejectTarget(null)} title="Từ chối yêu cầu">
        {rejectTarget && (
          <div className="space-y-3">
            <p className="text-xs text-slate-500">
              {rejectTarget.employee_name} · {renderDetail(rejectTarget)}
            </p>
            <Field label="Lý do từ chối *">
              <TextInput value={rejectReason} onChange={(e) => setRejectReason(e.target.value)} placeholder="Lý do bắt buộc…" />
            </Field>
            {rejectMut.isError && <ErrorAlert error={rejectMut.error} />}
            <div className="flex justify-end gap-2">
              <ButtonGhost onClick={() => setRejectTarget(null)}>Hủy</ButtonGhost>
              <ButtonDanger onClick={() => rejectTarget && rejectMut.mutate({ id: rejectTarget.id, reason: rejectReason })} disabled={rejectMut.isPending || !rejectReason.trim()}>
                {rejectMut.isPending ? 'Đang xử lý…' : 'Từ chối yêu cầu'}
              </ButtonDanger>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

function statusToneOf(s: string) {
  switch (s) {
    case 'approved': return 'emerald' as const;
    case 'rejected': return 'rose' as const;
    case 'cancelled': return 'slate' as const;
    default: return 'amber' as const;
  }
}
function statusLabel(s: string) {
  switch (s) {
    case 'submitted': return 'Chờ duyệt';
    case 'approved': return 'Đã duyệt';
    case 'rejected': return 'Từ chối';
    case 'cancelled': return 'Đã hủy';
    default: return s;
  }
}