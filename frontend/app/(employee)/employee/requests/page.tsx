'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { FileText, Plus, X, CheckCircle } from 'lucide-react';
import {
  fetchMyRequests, createLeave, createOvertime, cancelLeave, cancelOvertime, fetchLeaveBalance,
} from '@/lib/api/employee-requests';
import type {
  EmployeeRequestListResponse, EmployeeRequestListItem, CreateLeaveData, CreateOvertimeData, LeaveBalance,
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

/** Client-side overtime duration calculator (mirrors backend derive_duration). */
function calcDuration(startTime: string, endTime: string): number | null {
  if (!startTime || !endTime) return null;
  const [sh, sm] = startTime.split(':').map(Number);
  const [eh, em] = endTime.split(':').map(Number);
  if (isNaN(sh) || isNaN(sm) || isNaN(eh) || isNaN(em)) return null;
  let mins = (eh * 60 + em) - (sh * 60 + sm);
  if (mins <= 0) mins += 24 * 60; // overnight
  return mins;
}

function formatDuration(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (h > 0 && m > 0) return `${h} giờ ${m} phút`;
  if (h > 0) return `${h} giờ`;
  return `${m} phút`;
}

/** Simple toast that auto-dismisses after 3s. */
function SuccessToast({ message, onDone }: { message: string; onDone: () => void }) {
  useEffect(() => {
    const t = setTimeout(onDone, 3000);
    return () => clearTimeout(t);
  }, [onDone]);
  return (
    <div className="fixed top-4 right-4 z-50 flex items-center gap-2 px-4 py-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-700 shadow-lg animate-in fade-in slide-in-from-top-2">
      <CheckCircle className="w-4 h-4 shrink-0" />
      <span className="text-sm font-semibold">{message}</span>
    </div>
  );
}

export default function EmployeeRequestsPage() {
  useAuthGuard({ requireAuth: true, requireEmployee: true });
  const qc = useQueryClient();

  const [tab, setTab] = useState<FormTab>('leave');
  const [leaveForm, setLeaveForm] = useState<CreateLeaveData>({ leave_type: 'annual', start_date: '', end_date: '', reason: '' });
  const [otForm, setOtForm] = useState<CreateOvertimeData>({ work_date: '', start_time: '', end_time: '', reason: '', project_or_task: '' });

  const [cancelTarget, setCancelTarget] = useState<EmployeeRequestListItem | null>(null);
  const [cancelReason, setCancelReason] = useState('');
  const [toast, setToast] = useState<string | null>(null);

  const listRef = useRef<HTMLDivElement>(null);

  // Queries
  const { data, isLoading, error } = useQuery<EmployeeRequestListResponse>({
    queryKey: ['my-requests'],
    queryFn: fetchMyRequests,
  });

  const { data: balance } = useQuery<LeaveBalance>({
    queryKey: ['my-leave-balance'],
    queryFn: fetchLeaveBalance,
    staleTime: 60_000,
  });

  // --- Client-side validation helpers ---

  const leaveDateError =
    leaveForm.start_date && leaveForm.end_date && leaveForm.end_date < leaveForm.start_date
      ? 'Ngày kết thúc phải sau hoặc bằng ngày bắt đầu'
      : null;

  const otTimeError =
    otForm.start_time && otForm.end_time && otForm.end_time <= otForm.start_time
      ? 'Giờ kết thúc phải sau giờ bắt đầu'
      : null;

  const otDuration = calcDuration(otForm.start_time, otForm.end_time);

  // --- Mutations ---

  const leaveMut = useMutation({
    mutationFn: (d: CreateLeaveData) => createLeave(d),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['my-requests'] });
      qc.invalidateQueries({ queryKey: ['my-leave-balance'] });
      setLeaveForm({ leave_type: 'annual', start_date: '', end_date: '', reason: '' });
      setToast('Đã gửi yêu cầu nghỉ phép thành công!');
    },
  });
  const otMut = useMutation({
    mutationFn: (d: CreateOvertimeData) => createOvertime(d),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['my-requests'] });
      setOtForm({ work_date: '', start_time: '', end_time: '', reason: '', project_or_task: '' });
      setToast('Đã gửi yêu cầu tăng ca thành công!');
    },
  });
  const cancelMut = useMutation<unknown, unknown, { request: EmployeeRequestListItem; reason: string }>({
    mutationFn: async ({ request, reason }) => {
      const r = reason.trim() || null;
      if (request.request_type === 'leave') {
        await cancelLeave(request.id, r);
      } else {
        await cancelOvertime(request.id, r);
      }
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['my-requests'] });
      qc.invalidateQueries({ queryKey: ['my-leave-balance'] });
      setCancelTarget(null);
      setCancelReason('');
      setToast('Đã hủy yêu cầu thành công.');
    },
  });

  // --- Handlers ---

  const switchTab = (t: FormTab) => {
    setTab(t);
    // M-4: Clear mutation errors on tab switch
    leaveMut.reset();
    otMut.reset();
  };

  const submitLeave = () => leaveMut.mutate(leaveForm);
  const submitOt = () => otMut.mutate({ ...otForm, project_or_task: otForm.project_or_task || undefined });

  const leaveDisabled =
    leaveMut.isPending || !leaveForm.start_date || !leaveForm.end_date || !leaveForm.reason || !!leaveDateError;
  const otDisabled =
    otMut.isPending || !otForm.work_date || !otForm.start_time || !otForm.end_time || !otForm.reason || !!otTimeError;

  return (
    <div className="space-y-6">
      <PageHeader icon={FileText} title="Yêu cầu của tôi" subtitle="Gửi yêu cầu nghỉ phép hoặc tăng ca và theo dõi trạng thái. Yêu cầu cần được HR duyệt trước khi có hiệu lực." />

      {/* Success toast */}
      {toast && <SuccessToast message={toast} onDone={() => setToast(null)} />}

      {/* Leave balance card (C-1) */}
      {balance && (
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-bold text-slate-900">Số ngày phép năm</p>
              <p className="text-xs text-slate-500">
                Đã dùng {balance.approved_days_used} ngày
                {balance.pending_days > 0 && ` · ${balance.pending_days} ngày đang chờ duyệt`}
              </p>
            </div>
            <div className="text-right">
              <span className={`text-2xl font-bold ${balance.remaining_days > 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                {balance.remaining_days}
              </span>
              <span className="text-sm text-slate-500"> / {balance.annual_entitlement_days} ngày</span>
            </div>
          </div>
          {/* Progress bar */}
          <div className="mt-2 w-full bg-slate-100 rounded-full h-2">
            <div
              className="bg-indigo-500 h-2 rounded-full transition-all"
              style={{ width: `${Math.min(100, (balance.approved_days_used / balance.annual_entitlement_days) * 100)}%` }}
            />
          </div>
        </Card>
      )}

      {/* Create form */}
      <Card>
        <div className="flex gap-2 mb-4">
          {(['leave', 'overtime'] as FormTab[]).map((t) => (
            <button key={t} onClick={() => switchTab(t)}
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
              <Field label="Từ ngày *">
                <TextInput aria-label="Từ ngày nghỉ phép" type="date" value={leaveForm.start_date} onChange={(e) => setLeaveForm({ ...leaveForm, start_date: e.target.value })} />
              </Field>
              <Field label="Đến ngày *">
                <TextInput aria-label="Đến ngày nghỉ phép" type="date" value={leaveForm.end_date} onChange={(e) => setLeaveForm({ ...leaveForm, end_date: e.target.value })} />
              </Field>
            </div>
            {/* Client-side date validation error (M-2) */}
            {leaveDateError && <p className="text-xs text-rose-600 font-medium">{leaveDateError}</p>}
            <Field label="Lý do *"><TextArea rows={2} aria-label="Lý do nghỉ phép" placeholder="Nhập lý do nghỉ phép…" value={leaveForm.reason} onChange={(e) => setLeaveForm({ ...leaveForm, reason: e.target.value })} /></Field>
            {leaveMut.isError && <ErrorAlert error={leaveMut.error} />}
            <div className="flex justify-end">
              <ButtonPrimary aria-label="Gửi yêu cầu nghỉ phép" onClick={submitLeave} disabled={leaveDisabled}>
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
            {/* Client-side time validation + real-time duration (M-2, M-3) */}
            {otTimeError && <p className="text-xs text-rose-600 font-medium">{otTimeError}</p>}
            {!otTimeError && otDuration != null && (
              <p className="text-xs text-indigo-600 font-medium">Tổng thời gian: {formatDuration(otDuration)}</p>
            )}
            <Field label="Lý do *"><TextArea rows={2} aria-label="Lý do tăng ca" placeholder="Nhập lý do tăng ca…" value={otForm.reason} onChange={(e) => setOtForm({ ...otForm, reason: e.target.value })} /></Field>
            {otMut.isError && <ErrorAlert error={otMut.error} />}
            <div className="flex justify-end">
              <ButtonPrimary aria-label="Gửi yêu cầu tăng ca" onClick={submitOt} disabled={otDisabled}>
                {otMut.isPending ? 'Đang gửi…' : 'Gửi yêu cầu'}
              </ButtonPrimary>
            </div>
          </div>
        )}
      </Card>

      {/* My requests list */}
      <Card>
        <div ref={listRef}>
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
                        {r.reason && <p className="text-xs text-slate-500 mt-1 italic">&ldquo;{r.reason}&rdquo;</p>}
                        {r.review_reason && <p className="text-[11px] text-slate-500 mt-1">HR: {r.review_reason} · {formatDateTime(r.reviewed_at)}</p>}
                        {r.cancellation_reason && <p className="text-[11px] text-slate-400 mt-1">Lý do hủy: {r.cancellation_reason}</p>}
                      </div>
                      {r.status === 'submitted' && (
                        <ButtonGhost onClick={() => { setCancelTarget(r); setCancelReason(''); }} className="!px-2.5">
                          <X className="w-4 h-4" /> Hủy
                        </ButtonGhost>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
        </div>
      </Card>

      {/* Cancel modal with optional reason (M-5) */}
      <Modal open={!!cancelTarget} onClose={() => setCancelTarget(null)} title="Hủy yêu cầu">
        {cancelTarget && (
          <div className="space-y-3">
            <p className="text-xs text-slate-500">Bạn đang hủy yêu cầu {cancelTarget.request_type === 'leave' ? 'nghỉ phép' : 'tăng ca'} đang chờ duyệt.</p>
            <Field label="Lý do hủy (không bắt buộc)" hint="Giúp HR hiểu lý do bạn hủy">
              <TextInput
                aria-label="Lý do hủy yêu cầu"
                value={cancelReason}
                onChange={(e) => setCancelReason(e.target.value)}
                placeholder="VD: Đổi kế hoạch, không cần nghỉ nữa…"
              />
            </Field>
            {cancelMut.isError && <ErrorAlert error={cancelMut.error} />}
            <div className="flex justify-end gap-2">
              <ButtonGhost onClick={() => setCancelTarget(null)}>Để sau</ButtonGhost>
              <ButtonPrimary
                onClick={() => cancelTarget && cancelMut.mutate({ request: cancelTarget, reason: cancelReason })}
                disabled={cancelMut.isPending}
              >
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
