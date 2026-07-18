'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  FileSpreadsheet, Plus, Search, Eye, Pencil, Send, Trash2, ChevronLeft, ChevronRight,
} from 'lucide-react';
import {
  fetchPayslips, fetchPayslip, createPayslip, updatePayslip, publishPayslip, deletePayslip,
} from '@/lib/api/admin-payslips';
import type {
  Payslip, PayslipListResponse, CreatePayslipRequest, UpdatePayslipRequest,
} from '@/lib/api/admin-payslips';
import { listEmployees } from '@/lib/api/employees';
import type { EmployeeListResponse } from '@/lib/api/types';
import { useAuthGuard } from '@/lib/auth/session';
import {
  PageHeader, Card, SectionTitle, Field, TextInput, Select, ButtonPrimary, ButtonGhost, ButtonDanger,
  Badge, ErrorAlert, EmptyState, LoadingRows, Modal, formatVND, formatDateTime,
} from '@/components/shared-ui';

type StatusFilter = '' | 'draft' | 'published';

const blankDraft: CreatePayslipRequest = {
  employee_id: '',
  period_month: '',
  gross_salary: '',
  deductions: '0',
  insurance_employee: '0',
  taxable_income: '0',
  pit_amount: '0',
  net_salary: '',
  pdf_url: '',
};

function toMonthDay(ym: string): string {
  // YYYY-MM → YYYY-MM-01 (BE expects a full date; it normalizes day→1)
  return ym ? `${ym}-01` : '';
}
function toMonth(stat: string): string {
  // period_month date "YYYY-MM-01" → "YYYY-MM"
  if (!stat) return '';
  return stat.slice(0, 7);
}
const empName = (list: EmployeeListResponse | undefined, id: string) =>
  list?.items?.find((e) => e.id === id)?.full_name ?? id.slice(0, 8);

export default function PayslipsPage() {
  useAuthGuard({ requireAuth: true, requireAdmin: true });
  const qc = useQueryClient();

  const [employeeId, setEmployeeId] = useState('');
  const [status, setStatus] = useState<StatusFilter>('');
  const [periodMonth, setPeriodMonth] = useState('');
  const [page, setPage] = useState(1);
  const [submitted, setSubmitted] = useState({ employeeId, status, periodMonth, page });

  const { data: employees } = useQuery<EmployeeListResponse>({
    queryKey: ['employees-list', { all: true }],
    queryFn: () => listEmployees({ page: 1, page_size: 100, is_active: true }),
    staleTime: 60_000,
  });

  const { data, isLoading, error } = useQuery<PayslipListResponse>({
    queryKey: ['admin-payslips', submitted],
    queryFn: () =>
      fetchPayslips({
        page: submitted.page,
        page_size: 20,
        employee_id: submitted.employeeId || undefined,
        status: (submitted.status as 'draft' | 'published' | undefined) || undefined,
        period_month: submitted.periodMonth || undefined,
      }),
    placeholderData: (prev) => prev,
  });

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;
  const apply = () => setSubmitted({ employeeId, status, periodMonth, page: 1 });
  const gotoPage = (p: number) => {
    const np = Math.min(Math.max(1, p), totalPages);
    setPage(np);
    setSubmitted({ ...submitted, page: np });
  };

  // Create draft
  const [createOpen, setCreateOpen] = useState(false);
  const [draft, setDraft] = useState<CreatePayslipRequest>(blankDraft);
  const createMut = useMutation({
    mutationFn: (d: CreatePayslipRequest) => createPayslip(d),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-payslips'] });
      setCreateOpen(false);
      setDraft(blankDraft);
    },
  });
  const submitCreate = () => {
    createMut.mutate({ ...draft, period_month: toMonthDay(draft.period_month) });
  };

  // View / edit
  const [viewId, setViewId] = useState<string | null>(null);
  const { data: viewed } = useQuery<Payslip>({
    queryKey: ['admin-payslip', viewId],
    queryFn: () => fetchPayslip(viewId!),
    enabled: Boolean(viewId),
  });
  const [editMode, setEditMode] = useState(false);
  const [editForm, setEditForm] = useState<UpdatePayslipRequest>({});

  const startEdit = () => {
    if (!viewed) return;
    setEditForm({
      gross_salary: viewed.gross_salary,
      deductions: viewed.deductions,
      insurance_employee: viewed.insurance_employee,
      taxable_income: viewed.taxable_income,
      pit_amount: viewed.pit_amount,
      net_salary: viewed.net_salary,
      pdf_url: viewed.pdf_url ?? '',
    });
    setEditMode(true);
  };

  const editMut = useMutation({
    mutationFn: (d: UpdatePayslipRequest) => updatePayslip(viewId!, d),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-payslip', viewId] });
      qc.invalidateQueries({ queryKey: ['admin-payslips'] });
      setEditMode(false);
    },
  });

  const publishMut = useMutation({
    mutationFn: (id: string) => publishPayslip(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-payslip', viewId] });
      qc.invalidateQueries({ queryKey: ['admin-payslips'] });
    },
  });
  const delMut = useMutation({
    mutationFn: (id: string) => deletePayslip(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-payslips'] });
      setViewId(null);
    },
  });

  const canMutate = (p: Payslip) => p.status === 'draft';

  return (
    <div className="space-y-6">
      <PageHeader
        icon={FileSpreadsheet}
        title="Phiếu lương (Payslips)"
        subtitle="Quản lý phiếu lương theo kỳ: tạo bản nháp, sửa, phát hành hoặc xóa. Nhân viên chỉ nhìn thấy phiếu lương đã được phát hành."
        actions={
          <ButtonPrimary onClick={() => setCreateOpen(true)}>
            <Plus className="w-4 h-4" /> Tạo draft
          </ButtonPrimary>
        }
      />

      <Card>
        <SectionTitle icon={Search}>Bộ lọc</SectionTitle>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 items-end">
          <Field label="Nhân viên">
            <Select value={employeeId} onChange={(e) => setEmployeeId(e.target.value)}>
              <option value="">Tất cả</option>
              {employees?.items?.map((e) => <option key={e.id} value={e.id}>{e.full_name}</option>)}
            </Select>
          </Field>
          <Field label="Trạng thái">
            <Select value={status} onChange={(e) => setStatus(e.target.value as StatusFilter)}>
              <option value="">Tất cả</option>
              <option value="draft">Bản nháp</option>
              <option value="published">Đã phát hành</option>
            </Select>
          </Field>
          <Field label="Kỳ lương (YYYY-MM)">
            <TextInput type="month" value={periodMonth} onChange={(e) => setPeriodMonth(e.target.value)} />
          </Field>
          <div />
          <ButtonPrimary onClick={apply} className="h-[38px]"><Search className="w-4 h-4" /> Lọc</ButtonPrimary>
        </div>
      </Card>

      <Card>
        <SectionTitle icon={FileSpreadsheet}>Danh sách</SectionTitle>
        {error ? <ErrorAlert error={error} title="Không tải được payslips" />
          : isLoading && !data ? <LoadingRows count={6} />
          : !data?.payslips?.length ? <EmptyState filtered={Boolean(submitted.employeeId || submitted.status || submitted.periodMonth)} />
          : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-[10px] font-mono uppercase text-slate-400 border-b border-slate-100">
                    <th className="py-2 px-2">Nhân viên</th>
                    <th className="py-2 px-2">Kỳ</th>
                    <th className="py-2 px-2">Lương gross</th>
                    <th className="py-2 px-2">Net</th>
                    <th className="py-2 px-2">Trạng thái</th>
                    <th className="py-2 px-2">Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {data.payslips.map((p) => (
                    <tr key={p.id} className="border-b border-slate-50 hover:bg-slate-50">
                      <td className="py-2.5 px-2 text-xs font-semibold text-slate-800">{empName(employees, p.employee_id)}</td>
                      <td className="py-2.5 px-2 font-mono text-xs text-slate-500">{toMonth(p.period_month)}</td>
                      <td className="py-2.5 px-2 text-xs text-slate-600">{formatVND(p.gross_salary)}</td>
                      <td className="py-2.5 px-2 text-xs font-semibold text-slate-800">{formatVND(p.net_salary)}</td>
                      <td className="py-2.5 px-2"><Badge tone={p.status === 'published' ? 'emerald' : 'amber'}>{p.status === 'published' ? 'Đã phát hành' : 'Bản nháp'}</Badge></td>
                      <td className="py-2.5 px-2">
                        <button onClick={() => { setViewId(p.id); setEditMode(false); }} className="p-1.5 rounded-lg hover:bg-slate-200 text-slate-500 hover:text-indigo-600 transition-all" title="Xem">
                          <Eye className="w-4 h-4" />
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
            <span className="text-xs text-slate-500">{data.total} payslips · trang {submitted.page} / {totalPages}</span>
            <div className="flex items-center gap-2">
              <button onClick={() => gotoPage(submitted.page - 1)} disabled={submitted.page <= 1} className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 disabled:opacity-40 transition-all"><ChevronLeft className="w-4 h-4" /></button>
              <button onClick={() => gotoPage(submitted.page + 1)} disabled={submitted.page >= totalPages} className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 disabled:opacity-40 transition-all"><ChevronRight className="w-4 h-4" /></button>
            </div>
          </div>
        )}
      </Card>

      {/* Create draft modal */}
      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="Tạo payslip draft">
        <div className="space-y-3">
          <Field label="Nhân viên *">
            <Select value={draft.employee_id} onChange={(e) => setDraft({ ...draft, employee_id: e.target.value })}>
              <option value="">Chọn nhân viên…</option>
              {employees?.items?.map((e) => <option key={e.id} value={e.id}>{e.full_name}</option>)}
            </Select>
          </Field>
          <Field label="Kỳ lương (YYYY-MM) *">
            <TextInput type="month" value={draft.period_month} onChange={(e) => setDraft({ ...draft, period_month: e.target.value })} />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Lương gross *"><TextInput value={draft.gross_salary} onChange={(e) => setDraft({ ...draft, gross_salary: e.target.value })} /></Field>
            <Field label="Lương net *"><TextInput value={draft.net_salary} onChange={(e) => setDraft({ ...draft, net_salary: e.target.value })} /></Field>
            <Field label="Khấu trừ"><TextInput value={draft.deductions} onChange={(e) => setDraft({ ...draft, deductions: e.target.value })} /></Field>
            <Field label="Bảo hiểm (NV)"><TextInput value={draft.insurance_employee} onChange={(e) => setDraft({ ...draft, insurance_employee: e.target.value })} /></Field>
            <Field label="Thu nhập chịu thuế"><TextInput value={draft.taxable_income} onChange={(e) => setDraft({ ...draft, taxable_income: e.target.value })} /></Field>
            <Field label="Thuế TNCN"><TextInput value={draft.pit_amount} onChange={(e) => setDraft({ ...draft, pit_amount: e.target.value })} /></Field>
          </div>
          <Field label="PDF URL (tùy chọn)"><TextInput value={draft.pdf_url} onChange={(e) => setDraft({ ...draft, pdf_url: e.target.value })} /></Field>
          {createMut.isError && <ErrorAlert error={createMut.error} />}
          <div className="flex justify-end gap-2">
            <ButtonGhost onClick={() => setCreateOpen(false)}>Hủy</ButtonGhost>
            <ButtonPrimary onClick={submitCreate} disabled={createMut.isPending || !draft.employee_id || !draft.period_month || !draft.gross_salary || !draft.net_salary}>
              {createMut.isPending ? 'Đang tạo…' : 'Tạo draft'}
            </ButtonPrimary>
          </div>
        </div>
      </Modal>

      {/* View / edit / publish / delete modal */}
      <Modal open={!!viewId} onClose={() => { setViewId(null); setEditMode(false); }} title={editMode ? 'Sửa payslip draft' : 'Chi tiết payslip'}>
        {viewed && (
          <div className="space-y-3">
            <div className="flex items-center gap-2 flex-wrap">
              <Badge tone={viewed.status === 'published' ? 'emerald' : 'amber'}>{viewed.status === 'published' ? 'Đã phát hành' : 'Bản nháp'}</Badge>
              <span className="text-xs font-semibold text-slate-800">{empName(employees, viewed.employee_id)}</span>
              <span className="font-mono text-[10px] text-slate-400">Kỳ {toMonth(viewed.period_month)}</span>
              {viewed.published_at && <span className="text-[10px] text-slate-400">Phát hành {formatDateTime(viewed.published_at)}</span>}
            </div>

            {!editMode ? (
              <div className="grid grid-cols-2 gap-2 text-xs">
                <Row label="Lương gross" value={formatVND(viewed.gross_salary)} />
                <Row label="Lương net" value={formatVND(viewed.net_salary)} />
                <Row label="Khấu trừ" value={formatVND(viewed.deductions)} />
                <Row label="Bảo hiểm (NV)" value={formatVND(viewed.insurance_employee)} />
                <Row label="Thu nhập chịu thuế" value={formatVND(viewed.taxable_income)} />
                <Row label="Thuế TNCN" value={formatVND(viewed.pit_amount)} />
                {viewed.pdf_url && <div className="col-span-2"><Row label="PDF URL" value={viewed.pdf_url} /></div>}
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-3">
                <Field label="Lương gross"><TextInput value={editForm.gross_salary ?? ''} onChange={(e) => setEditForm({ ...editForm, gross_salary: e.target.value })} /></Field>
                <Field label="Lương net"><TextInput value={editForm.net_salary ?? ''} onChange={(e) => setEditForm({ ...editForm, net_salary: e.target.value })} /></Field>
                <Field label="Khấu trừ"><TextInput value={editForm.deductions ?? ''} onChange={(e) => setEditForm({ ...editForm, deductions: e.target.value })} /></Field>
                <Field label="Bảo hiểm (NV)"><TextInput value={editForm.insurance_employee ?? ''} onChange={(e) => setEditForm({ ...editForm, insurance_employee: e.target.value })} /></Field>
                <Field label="Thu nhập chịu thuế"><TextInput value={editForm.taxable_income ?? ''} onChange={(e) => setEditForm({ ...editForm, taxable_income: e.target.value })} /></Field>
                <Field label="Thuế TNCN"><TextInput value={editForm.pit_amount ?? ''} onChange={(e) => setEditForm({ ...editForm, pit_amount: e.target.value })} /></Field>
                <Field label="PDF URL (trống để xóa)"><TextInput value={editForm.pdf_url ?? ''} onChange={(e) => setEditForm({ ...editForm, pdf_url: e.target.value })} /></Field>
              </div>
            )}

            {editMode && editMut.isError && <ErrorAlert error={editMut.error} />}
            {publishMut.isError && <ErrorAlert error={publishMut.error} />}
            {delMut.isError && <ErrorAlert error={delMut.error} />}

            <div className="flex flex-wrap justify-between gap-2 pt-2 border-t border-slate-100">
              <ButtonDanger onClick={() => delMut.mutate(viewed.id)} disabled={delMut.isPending || !canMutate(viewed)}>
                <Trash2 className="w-4 h-4" /> Xóa draft
              </ButtonDanger>
              <div className="flex gap-2">
                {editMode ? (
                  <>
                    <ButtonGhost onClick={() => setEditMode(false)}>Hủy sửa</ButtonGhost>
                    <ButtonPrimary onClick={() => editMut.mutate(editForm)} disabled={editMut.isPending}>
                      <Pencil className="w-4 h-4" /> {editMut.isPending ? 'Đang lưu…' : 'Lưu draft'}
                    </ButtonPrimary>
                  </>
                ) : (
                  <>
                    <ButtonGhost onClick={() => { setViewId(null); setEditMode(false); }}>Đóng</ButtonGhost>
                    <ButtonGhost onClick={startEdit} disabled={!canMutate(viewed)}>
                      <Pencil className="w-4 h-4" /> Sửa draft
                    </ButtonGhost>
                    <ButtonPrimary onClick={() => publishMut.mutate(viewed.id)} disabled={publishMut.isPending || !canMutate(viewed)}>
                      <Send className="w-4 h-4" /> {publishMut.isPending ? 'Đang phát hành…' : 'Phát hành'}
                    </ButtonPrimary>
                  </>
                )}
              </div>
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