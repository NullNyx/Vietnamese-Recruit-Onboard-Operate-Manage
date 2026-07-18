'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { FileText, Plus, X } from 'lucide-react';
import {
  fetchMyRequests, createLeave, createOvertime, cancelLeave, cancelOvertime,
} from '@/lib/api/employee-requests';
import type {
  EmployeeRequestListResponse, EmployeeRequestListItem, CreateLeaveData, CreateOvertimeData,
} from '@/lib/api/employee-requests';
import { useAuthGuard } from '@/lib/auth/session';
import {
  PageHeader, Card, SectionTitle, Field, TextInput, TextArea, Select, ButtonPrimary, ButtonGhost,
  Badge, ErrorAlert, EmptyState, Modal, formatDate, formatDateTime,
} from '@/components/shared-ui';

const LEAVE_TYPES: { value: CreateLeaveData['leave_type']; label: string }[] = [
  { value: 'annual', label: 'Nghỉ phép năm' },
  { value: 'sick', label: 'Nghỉ ốm' },
  { value: 'unpaid', label: 'Nghỉ không lương' },
  { value: 'other', label: 'Khác' },
];

type FormTab = 'leave' | 'overtime';

export default function EmployeeRequestsPage() {
  useAuthGuard({ requireAuth: true, requireEmployee: true });
  const qc = useQueryClient();

  const [tab, setTab] = useState<FormTab>('leave');
  const [leaveForm, setLeaveForm] = useState<CreateLeaveData>({ leave_type: 'annual', start_date: '', end_date: '', reason: '' });
  const [otForm, setOtForm] = useState<CreateOvertimeData>({ work_date: '', start_time: '', end_time: '', reason: '', project_or_task: '' });

  const [cancelTarget, setCancelTarget] = useState<EmployeeRequestListItem | null>(null);

  const { data, isLoading, error } = useQuery<EmployeeRequestListResponse>({
    queryKey: ['my-requests'],
    queryFn: fetchMyRequests,
  });

  const leaveMut = useMutation({
    mutationFn: (d: CreateLeaveData) => createLeave(d),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['my-requests'] });
      setLeaveForm({ leave_type: 'annual', start_date: '', end_date: '', reason: '' });
    },
  });
  const otMut = useMutation({
    mutationFn: (d: CreateOvertimeData) => createOvertime(d),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['my-requests'] });
      setOtForm({ work_date: '', start_time: '', end_time: '', reason: '', project_or_task: '' });
    },
  });
  const cancelMut = useMutation<unknown, unknown, EmployeeRequestListItem>({
    mutationFn: async (r: EmployeeRequestListItem) => {
      if (r.request_type === 'leave') { await cancelLeave(r.id, null); } else { await cancelOvertime(r.id, null); }
      // handled above
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['my-requests'] });
      setCancelTarget(null);
    },
  });

  const submitLeave = () => leaveMut.mutate(leaveForm);
  const submitOt = () => otMut.mutate({ ...otForm, project_or_task: otForm.project_or_task || undefined });

  return (
    <div className="space-y-6">
      <PageHeader icon={FileText} title="Yêu cầu của tôi" subtitle="Gửi yêu cầu nghỉ phép hoặc tăng ca và theo dõi trạng thái. Yêu cầu cần được HR duyệt trước khi có hiệu lực." />

      {/* Create form */}
      <Card>
        <div className="flex gap-2 mb-4">
          {(['leave', 'overtime'] as FormTab[]).map((t) => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${tab === t ? 'bg-indigo-600 text-white' : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'}`}>
              {t === 'leave' ? 'Nghỉ phép' : 'Tăng ca'}
            </button>
          ))}
        </div>

        {tab === 'leave' ? (
          <div className="space-y-3">
            <SectionTitle icon={Plus}>Tạo yêu cầu nghỉ phép</SectionTitle>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <Field label="Loại nghỉ">
                <Select value={leaveForm.leave_type} onChange={(e) => setLeaveForm({ ...leaveForm, leave_type: e.target.value as CreateLeaveData['leave_type'] })}>
                  {LEAVE_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                </Select>
              </Field>
              <Field label="Từ ngày *"><TextInput aria-label="Từ ngày nghỉ phép" type="date" value={leaveForm.start_date} onChange={(e) => setLeaveForm({ ...leaveForm, start_date: e.target.value })} /></Field>
              <Field label="Đến ngày *"><TextInput aria-label="Đến ngày nghỉ phép" type="date" value={leaveForm.end_date} onChange={(e) => setLeaveForm({ ...leaveForm, end_date: e.target.value })} /></Field>
            </div>
              <Field label="Lý do *"><TextArea rows={2} aria-label="Lý do nghỉ phép" placeholder="Nhập lý do nghỉ phép…" value={leaveForm.reason} onChange={(e) => setLeaveForm({ ...leaveForm, reason: e.target.value })} /></Field>
            {leaveMut.isError && <ErrorAlert error={leaveMut.error} />}
            <div className="flex justify-end">
              {/* BUG-11: aria-label rõ ràng để E2E/AT target deterministically; nút disabled đến khi
                  start_date+end_date+reason đầy đủ (xem disabled logic) — phải fill đủ form trước. */}
              <ButtonPrimary aria-label="Gửi yêu cầu nghỉ phép" onClick={submitLeave} disabled={leaveMut.isPending || !leaveForm.start_date || !leaveForm.end_date || !leaveForm.reason}>
                {leaveMut.isPending ? 'Đang gửi…' : 'Gửi yêu cầu'}
              </ButtonPrimary>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <SectionTitle icon={Plus}>Tạo yêu cầu tăng ca</SectionTitle>
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
              <Field label="Ngày làm *"><TextInput type="date" aria-label="Ngày làm tăng ca" value={otForm.work_date} onChange={(e) => setOtForm({ ...otForm, work_date: e.target.value })} /></Field>
              <Field label="Bắt đầu *"><TextInput type="time" aria-label="Giờ bắt đầu tăng ca" value={otForm.start_time} onChange={(e) => setOtForm({ ...otForm, start_time: e.target.value })} /></Field>
              <Field label="Kết thúc *"><TextInput type="time" aria-label="Giờ kết thúc tăng ca" value={otForm.end_time} onChange={(e) => setOtForm({ ...otForm, end_time: e.target.value })} /></Field>
              <Field label="Dự án / công việc"><TextInput value={otForm.project_or_task ?? ''} onChange={(e) => setOtForm({ ...otForm, project_or_task: e.target.value })} /></Field>
            </div>
              <Field label="Lý do *"><TextArea rows={2} aria-label="Lý do tăng ca" placeholder="Nhập lý do tăng ca…" value={otForm.reason} onChange={(e) => setOtForm({ ...otForm, reason: e.target.value })} /></Field>
            {otMut.isError && <ErrorAlert error={otMut.error} />}
            <div className="flex justify-end">
              <ButtonPrimary aria-label="Gửi yêu cầu tăng ca" onClick={submitOt} disabled={otMut.isPending || !otForm.work_date || !otForm.start_time || !otForm.end_time || !otForm.reason}>
                {otMut.isPending ? 'Đang gửi…' : 'Gửi yêu cầu'}
              </ButtonPrimary>
            </div>
          </div>
        )}
      </Card>

      {/* My requests list */}
      <Card>
        <SectionTitle icon={FileText}>Yêu cầu của tôi</SectionTitle>
        {error ? <ErrorAlert error={error} title="Không tải được yêu cầu" />
          : isLoading && !data ? <p className="text-sm text-slate-400">Đang tải…</p>
          : !data?.requests?.length ? <EmptyState filtered={false} emptyData="Bạn chưa gửi yêu cầu nào." />
          : (
            <div className="space-y-2">
              {data.requests.map((r) => (
                <div key={r.id} className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap mb-1">
                        <Badge tone={r.request_type === 'leave' ? 'sky' : 'indigo'}>{r.request_type === 'leave' ? 'Nghỉ phép' : 'Tăng ca'}</Badge>
                        <Badge tone={toneFor(r.status)}>{labelFor(r.status)}</Badge>
                        <span className="text-[10px] font-mono text-slate-400">{formatDateTime(r.submitted_at)}</span>
                      </div>
                      <p className="text-xs text-slate-600">
                        {r.request_type === 'leave'
                          ? `${r.leave_type ?? '—'}: ${formatDate(r.start_date)} → ${formatDate(r.end_date)}`
                          : `${formatDate(r.work_date)} ${r.start_time ?? ''}→${r.end_time ?? ''}${r.duration_minutes ? ` (${r.duration_minutes} phút)` : ''}`}
                      </p>
                      {r.reason && <p className="text-xs text-slate-500 mt-1 italic">"{r.reason}"</p>}
                      {r.review_reason && <p className="text-[11px] text-slate-500 mt-1">HR: {r.review_reason} · {formatDateTime(r.reviewed_at)}</p>}
                    </div>
                    {r.status === 'submitted' && (
                      <ButtonGhost onClick={() => setCancelTarget(r)} className="!px-2.5">
                        <X className="w-4 h-4" /> Hủy
                      </ButtonGhost>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
      </Card>

      <Modal open={!!cancelTarget} onClose={() => setCancelTarget(null)} title="Hủy yêu cầu">
        {cancelTarget && (
          <div className="space-y-3">
            <p className="text-xs text-slate-500">Bạn đang hủy yêu cầu {cancelTarget.request_type === 'leave' ? 'nghỉ phép' : 'tăng ca'} đang chờ duyệt.</p>
            {cancelMut.isError && <ErrorAlert error={cancelMut.error} />}
            <div className="flex justify-end gap-2">
              <ButtonGhost onClick={() => setCancelTarget(null)}>Để sau</ButtonGhost>
              <ButtonPrimary onClick={() => cancelTarget && cancelMut.mutate(cancelTarget)} disabled={cancelMut.isPending}>
                {cancelMut.isPending ? 'Đang hủy…' : 'Xác nhận hủy'}
              </ButtonPrimary>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

function toneFor(s: string) {
  switch (s) {
    case 'approved': return 'emerald' as const;
    case 'rejected': return 'rose' as const;
    case 'cancelled': return 'slate' as const;
    default: return 'amber' as const;
  }
}
function labelFor(s: string) {
  switch (s) {
    case 'submitted': return 'Chờ duyệt';
    case 'approved': return 'Đã duyệt';
    case 'rejected': return 'Từ chối';
    case 'cancelled': return 'Đã hủy';
    default: return s;
  }
}