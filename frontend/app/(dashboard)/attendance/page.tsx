'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Clock, Network, Plus, Trash2, Save, Pencil, ChevronLeft, ChevronRight,
} from 'lucide-react';
import {
  listAttendanceRecords, correctAttendanceRecord,
  getNetworkAllowlist, updateNetworkAllowlist, addNetworkToAllowlist, removeNetworkFromAllowlist,
} from '@/lib/api/attendance';
import type {
  AttendanceListResponse, AttendanceRecord, CorrectionData,
  NetworkAllowlistResponse,
} from '@/lib/api/attendance';
import { listEmployees } from '@/lib/api/employees';
import type { EmployeeListResponse } from '@/lib/api/types';
import { useAuthGuard } from '@/lib/auth/session';
import {
  PageHeader, Card, SectionTitle, Field, TextInput, Select, ButtonPrimary, ButtonGhost, ButtonDanger,
  Badge, ErrorAlert, EmptyState, LoadingRows, Modal, formatDateTime,
} from '@/components/shared-ui';

type Tab = 'records' | 'network';

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}
function firstOfMonthISO() {
  const d = new Date();
  return new Date(d.getFullYear(), d.getMonth(), 1).toISOString().slice(0, 10);
}
/** Convert an ISO datetime to a datetime-local input value (no timezone shift). */
function toLocalInput(iso: string | null): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
/** Convert a datetime-local value to ISO string (or null if cleared). */
function fromLocalInput(value: string): string | null {
  if (!value) return null;
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return null;
  return d.toISOString();
}

export default function AttendancePage() {
  useAuthGuard({ requireAuth: true, requireAdmin: true });
  const qc = useQueryClient();
  const [tab, setTab] = useState<Tab>('records');

  return (
    <div className="space-y-6">
      <PageHeader
        icon={Clock}
        title="Chấm công & Allowlist"
        subtitle="Xem và sửa bản ghi chấm công (mọi sửa đổi đều được ghi lại lý do). Quản lý danh sách mạng văn phòng được phép chấm công."
      />

      <div className="flex gap-2">
        <button
          onClick={() => setTab('records')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            tab === 'records' ? 'bg-indigo-600 text-white' : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
          }`}
        >
          <Clock className="w-4 h-4 inline mr-1.5" /> Danh sách bản ghi
        </button>
        <button
          onClick={() => setTab('network')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            tab === 'network' ? 'bg-indigo-600 text-white' : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
          }`}
        >
          <Network className="w-4 h-4 inline mr-1.5" /> Network Allowlist
        </button>
      </div>

      {tab === 'records' ? <RecordsTab /> : <NetworkTab qc={qc} />}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Records tab
// ---------------------------------------------------------------------------

function RecordsTab() {
  const qc = useQueryClient();
  const [start, setStart] = useState(firstOfMonthISO());
  const [end, setEnd] = useState(todayISO());
  const [employeeId, setEmployeeId] = useState('');
  const [status, setStatus] = useState<'checked_in' | 'completed' | ''>('');
  const [page, setPage] = useState(1);
  const [submitted, setSubmitted] = useState({ start, end, employeeId, status, page });

  const { data: employees } = useQuery<EmployeeListResponse>({
    queryKey: ['employees-list', { active: true, all: true }],
    queryFn: () => listEmployees({ page: 1, page_size: 100, is_active: true }),
    staleTime: 60_000,
  });

  const { data, isLoading, error } = useQuery<AttendanceListResponse>({
    queryKey: ['attendance-records', submitted],
    queryFn: () =>
      listAttendanceRecords({
        start_date: submitted.start,
        end_date: submitted.end,
        employee_id: submitted.employeeId || undefined,
        status: (submitted.status as 'checked_in' | 'completed' | undefined) || undefined,
        page: submitted.page,
        page_size: 20,
      }),
    enabled: Boolean(submitted.start && submitted.end),
    placeholderData: (prev) => prev,
  });

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;
  const apply = () => setSubmitted({ start, end, employeeId, status, page: 1 });

  // Correction dialog
  const [correctTarget, setCorrectTarget] = useState<AttendanceRecord | null>(null);
  const [cIn, setCIn] = useState('');
  const [cOut, setCOut] = useState('');
  const [cReason, setCReason] = useState('');

  const openCorrect = (r: AttendanceRecord) => {
    setCorrectTarget(r);
    setCIn(toLocalInput(r.check_in_at));
    setCOut(toLocalInput(r.check_out_at));
    setCReason('');
  };

  const correctMut = useMutation({
    mutationFn: (payload: CorrectionData) => correctAttendanceRecord(correctTarget!.id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['attendance-records'] });
      setCorrectTarget(null);
    },
  });

  const submitCorrection = () => {
    const payload: CorrectionData = {
      check_in_at: fromLocalInput(cIn),
      check_out_at: fromLocalInput(cOut),
      correction_reason: cReason,
    };
    correctMut.mutate(payload);
  };

  const gotoPage = (p: number) => {
    const np = Math.min(Math.max(1, p), totalPages);
    setPage(np);
    setSubmitted({ ...submitted, page: np });
  };

  return (
    <Card>
      <SectionTitle icon={Clock}>Lọc bản ghi chấm công</SectionTitle>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 items-end">
        <Field label="Từ ngày *"><TextInput type="date" value={start} onChange={(e) => setStart(e.target.value)} /></Field>
        <Field label="Đến ngày *"><TextInput type="date" value={end} onChange={(e) => setEnd(e.target.value)} /></Field>
        <Field label="Nhân viên">
          <Select value={employeeId} onChange={(e) => setEmployeeId(e.target.value)}>
            <option value="">Tất cả</option>
            {employees?.items?.map((e) => <option key={e.id} value={e.id}>{e.full_name}</option>)}
          </Select>
        </Field>
        <Field label="Trạng thái">
          <Select value={status} onChange={(e) => setStatus(e.target.value as 'checked_in' | 'completed' | '')}>
            <option value="">Tất cả</option>
            <option value="checked_in">Đã check-in</option>
            <option value="completed">Đã check-out</option>
          </Select>
        </Field>
        <ButtonPrimary onClick={apply} className="h-[38px]">Lọc</ButtonPrimary>
      </div>

      <div className="mt-4">
        {error ? (
          <ErrorAlert error={error} title="Không tải được bản ghi" />
        ) : isLoading && !data ? (
          <LoadingRows count={6} />
        ) : !data?.records?.length ? (
          <EmptyState filtered={Boolean(submitted.employeeId || submitted.status)} />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[10px] font-mono uppercase text-slate-400 border-b border-slate-100">
                  <th className="py-2 px-2">Nhân viên</th>
                  <th className="py-2 px-2">Ngày</th>
                  <th className="py-2 px-2">Check-in</th>
                  <th className="py-2 px-2">Check-out</th>
                  <th className="py-2 px-2">IP</th>
                  <th className="py-2 px-2">Trạng thái</th>
                  <th className="py-2 px-2"></th>
                </tr>
              </thead>
              <tbody>
                {data.records.map((r) => (
                  <tr key={r.id} className="border-b border-slate-50 hover:bg-slate-50">
                    <td className="py-2.5 px-2">
                      <div className="font-semibold text-slate-800 text-xs">{r.employee_name ?? '—'}</div>
                      <div className="font-mono text-[10px] text-slate-400">{r.employee_code ?? ''}</div>
                    </td>
                    <td className="py-2.5 px-2 text-xs text-slate-600">{r.work_date}</td>
                    <td className="py-2.5 px-2 text-xs text-slate-600">{formatDateTime(r.check_in_at)}</td>
                    <td className="py-2.5 px-2 text-xs text-slate-600">{formatDateTime(r.check_out_at)}</td>
                    <td className="py-2.5 px-2 font-mono text-[10px] text-slate-400">{r.check_in_ip ?? '—'}</td>
                    <td className="py-2.5 px-2">
                      <Badge tone={r.check_out_at ? 'emerald' : 'amber'}>
                        {r.check_out_at ? 'completed' : 'checked_in'}
                      </Badge>
                    </td>
                    <td className="py-2.5 px-2">
                      <button onClick={() => openCorrect(r)} className="p-1.5 rounded-lg hover:bg-indigo-50 text-slate-500 hover:text-indigo-600 transition-all" title="Hiệu chỉnh">
                        <Pencil className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {data && data.total > data.page_size && (
          <div className="flex items-center justify-between pt-4 border-t border-slate-100 mt-4">
            <span className="text-xs text-slate-500">{data.total} bản ghi · trang {submitted.page} / {totalPages}</span>
            <div className="flex items-center gap-2">
              <button onClick={() => gotoPage(submitted.page - 1)} disabled={submitted.page <= 1} className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 disabled:opacity-40 transition-all"><ChevronLeft className="w-4 h-4" /></button>
              <button onClick={() => gotoPage(submitted.page + 1)} disabled={submitted.page >= totalPages} className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 disabled:opacity-40 transition-all"><ChevronRight className="w-4 h-4" /></button>
            </div>
          </div>
        )}
      </div>

      {/* Correction modal */}
      <Modal open={!!correctTarget} onClose={() => setCorrectTarget(null)} title="Hiệu chỉnh bản ghi chấm công">
        {correctTarget && (
          <div className="space-y-3">
            <p className="text-xs text-slate-500">
              Employee: <strong>{correctTarget.employee_name ?? '—'}</strong> · ngày {correctTarget.work_date}
            </p>
            <p className="text-[10px] text-slate-400">Mọi hiệu chỉnh được ghi audit log. Lý do bắt buộc.</p>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Check-in (để trống để xóa)">
                <TextInput type="datetime-local" value={cIn} onChange={(e) => setCIn(e.target.value)} />
              </Field>
              <Field label="Check-out (để trống để xóa)">
                <TextInput type="datetime-local" value={cOut} onChange={(e) => setCOut(e.target.value)} />
              </Field>
            </div>
            <Field label="Lý do hiệu chỉnh *">
              <TextInput value={cReason} onChange={(e) => setCReason(e.target.value)} placeholder="Quên check-in do lỗi mạng…" />
            </Field>
            {correctMut.isError && <ErrorAlert error={correctMut.error} />}
            <div className="flex justify-end gap-2 pt-2">
              <ButtonGhost onClick={() => setCorrectTarget(null)}>Hủy</ButtonGhost>
              <ButtonPrimary onClick={submitCorrection} disabled={correctMut.isPending || !cReason || (!cIn && !cOut)}>
                <Save className="w-4 h-4" /> {correctMut.isPending ? 'Đang lưu…' : 'Lưu hiệu chỉnh'}
              </ButtonPrimary>
            </div>
          </div>
        )}
      </Modal>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Network allowlist tab
// ---------------------------------------------------------------------------

function NetworkTab({ qc }: { qc: ReturnType<typeof useQueryClient> }) {
  const { data, isLoading, error } = useQuery<NetworkAllowlistResponse>({
    queryKey: ['attendance-network-allowlist'],
    queryFn: getNetworkAllowlist,
  });

  const [newCidr, setNewCidr] = useState('');
  const [bulkText, setBulkText] = useState('');
  const [replaceOpen, setReplaceOpen] = useState(false);

  const addMut = useMutation({
    mutationFn: (cidrs: string[]) => addNetworkToAllowlist(cidrs),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['attendance-network-allowlist'] }),
  });
  const removeMut = useMutation({
    mutationFn: (cidr: string) => removeNetworkFromAllowlist(cidr),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['attendance-network-allowlist'] }),
  });
  const replaceMut = useMutation({
    mutationFn: (networks: string[]) => updateNetworkAllowlist(networks),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['attendance-network-allowlist'] });
      setReplaceOpen(false);
      setBulkText('');
    },
  });

  const addOne = () => {
    const v = newCidr.trim();
    if (!v) return;
    addMut.mutate([v]);
    setNewCidr('');
  };

  return (
    <Card>
      <SectionTitle icon={Network}>Network Allowlist (CIDR)</SectionTitle>
      <p className="text-xs text-slate-500 mb-4">
        Chỉ cho phép chấm công từ các mạng trong danh sách. Mọi thay đổi được audit.
      </p>

      {error ? <ErrorAlert error={error} title="Không tải được allowlist" />
        : isLoading && !data ? <LoadingRows count={3} />
        : !data?.networks?.length ? (
          <EmptyState filtered={false} emptyData="Chưa có CIDR nào. Kiểm tra traffic đang đi qua IP nào trước khi thêm." />
        ) : (
          <div className="space-y-2">
            {data.networks.map((cidr) => (
              <div key={cidr} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg border border-slate-100">
                <span className="font-mono text-xs text-slate-700 flex-1">{cidr}</span>
                <button onClick={() => removeMut.mutate(cidr)} disabled={removeMut.isPending} className="p-1.5 rounded-lg hover:bg-rose-100 text-slate-400 hover:text-rose-500 transition-all" title="Xóa CIDR">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}

      <div className="mt-4 pt-4 border-t border-slate-100 space-y-3">
        <Field label="Thêm CIDR" hint="Ví dụ: 192.168.1.0/24">
          <div className="flex gap-2">
            <TextInput value={newCidr} onChange={(e) => setNewCidr(e.target.value)} placeholder="10.0.0.0/8" />
            <ButtonPrimary onClick={addOne} disabled={addMut.isPending || !newCidr.trim()} className="whitespace-nowrap">
              <Plus className="w-4 h-4" /> Thêm
            </ButtonPrimary>
          </div>
        </Field>
        {addMut.isError && <ErrorAlert error={addMut.error} />}
        {removeMut.isError && <ErrorAlert error={removeMut.error} />}

        <ButtonGhost onClick={() => { setBulkText(data?.networks.join('\n') ?? ''); setReplaceOpen(true); }}>
          Thay thế toàn bộ danh sách
        </ButtonGhost>
      </div>

      <Modal open={replaceOpen} onClose={() => setReplaceOpen(false)} title="Thay thế allowlist">
        <div className="space-y-3">
          <Field label="Danh sách CIDR (mỗi dòng một CIDR)">
            <textarea
              rows={8}
              value={bulkText}
              onChange={(e) => setBulkText(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-white text-sm font-mono focus:outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
              placeholder={'192.168.1.0/24\n10.0.0.0/8'}
            />
          </Field>
          <p className="text-[10px] text-rose-500">Cảnh báo: thao tác này thay thế toàn bộ danh sách hiện tại.</p>
          {replaceMut.isError && <ErrorAlert error={replaceMut.error} />}
          <div className="flex justify-end gap-2">
            <ButtonGhost onClick={() => setReplaceOpen(false)}>Hủy</ButtonGhost>
            <ButtonDanger onClick={() => replaceMut.mutate(bulkText.split('\n').map((s) => s.trim()).filter(Boolean))} disabled={replaceMut.isPending}>
              {replaceMut.isPending ? 'Đang lưu…' : 'Thay thế'}
            </ButtonDanger>
          </div>
        </div>
      </Modal>
    </Card>
  );
}

