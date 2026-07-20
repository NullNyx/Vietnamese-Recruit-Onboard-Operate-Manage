'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useRouter } from 'next/navigation';
import {
  Users, FileText, KeyRound, Save, Upload, Download, Trash2, Plus, ArrowLeft,
} from 'lucide-react';
import {
  getEmployee, updateEmployee, deleteEmployee, listDocuments, uploadDocument, downloadDocument, deleteDocument,
  getEmployeeAccountStatus, createEmployeeAccount, deleteEmployeeAccount,
} from '@/lib/api/employees';
import { listDepartments } from '@/lib/api/departments';
import { listPositions } from '@/lib/api/positions';
import type { Employee, EmployeeDocument, Department, Position, EmployeeUpdateData } from '@/lib/api/types';
import type { EmployeeAccountStatusResponse, EmployeeAccountCreateResponse } from '@/lib/api/auth';
import { useAuthGuard } from '@/lib/auth/session';
import {
  PageHeader, Card, SectionTitle, Field, TextInput, TextArea, Select,
  ButtonPrimary, ButtonGhost, ButtonDanger, Badge, ErrorAlert, Modal, formatDateTime, formatDate,
} from '@/components/shared-ui';

const DOC_TYPES = ['Hợp đồng', 'CMND/CCCD', 'Bằng cấp', 'Sổ bảo hiểm', 'Khác'];

export default function EmployeeDetailPage() {
  useAuthGuard({ requireAuth: true, requireAdmin: true });
  const params = useParams<{ id: string }>();
  const id = params.id;
  const router = useRouter();
  const qc = useQueryClient();

  const { data: employee, isLoading, error } = useQuery<Employee>({
    queryKey: ['employee', id],
    queryFn: () => getEmployee(id),
    enabled: Boolean(id),
  });
  const { data: departments } = useQuery<Department[]>({ queryKey: ['departments-list'], queryFn: listDepartments, staleTime: 60_000 });
  const { data: positions } = useQuery<Position[]>({ queryKey: ['positions-list'], queryFn: listPositions, staleTime: 60_000 });

  const { data: documents } = useQuery<EmployeeDocument[]>({
    queryKey: ['employee-documents', id],
    queryFn: () => listDocuments(id),
    enabled: Boolean(id),
  });

  const { data: account } = useQuery<EmployeeAccountStatusResponse>({
    queryKey: ['employee-account', id],
    queryFn: () => getEmployeeAccountStatus(id),
    enabled: Boolean(id),
  });

  // ---- Edit form ----
  const [form, setForm] = useState<Partial<Employee> | null>(null);
  const editActive = form !== null;
  const startEdit = () => setForm(employee ? { ...employee } : {});
  const submitEdit = () => {
    if (!form) return;
    const { id:_id, is_active:_a, employee_code:_c, candidate_id:_cid, created_at:_ca, updated_at:_ua, ...rest } = form;
    const u = Object.fromEntries(
      Object.entries(rest).map(([k, v]) => [k, v ?? undefined]),
    ) as EmployeeUpdateData;
    updateMut.mutate(u);
  };
  const cancelEdit = () => setForm(null);

  const updateMut = useMutation({
    mutationFn: (data: EmployeeUpdateData) => updateEmployee(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['employee', id] });
      qc.invalidateQueries({ queryKey: ['employees-list'] });
      setForm(null);
    },
  });

  // ---- Documents ----
  const [uploadOpen, setUploadOpen] = useState(false);
  const [docType, setDocType] = useState(DOC_TYPES[0]);
  const [docDesc, setDocDesc] = useState('');
  const [docFile, setDocFile] = useState<File | null>(null);

  const uploadMut = useMutation({
    mutationFn: () => {
      if (!docFile) throw new Error('Vui lòng chọn tệp');
      return uploadDocument(id, docFile, docType, docDesc || undefined);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['employee-documents', id] });
      setUploadOpen(false);
      setDocFile(null);
      setDocDesc('');
      setDocType(DOC_TYPES[0]);
    },
  });

  const delDocMut = useMutation({
    mutationFn: (documentId: string) => deleteDocument(documentId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['employee-documents', id] }),
  });

  const handleDownload = async (docId: string, name: string) => {
    try {
      const blob = await downloadDocument(docId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = name;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      // surfaced via error state is overkill for one-off; alert minimal
      console.error(e);
    }
  };

  // ---- Account ----
  const [createdPwd, setCreatedPwd] = useState<string | null>(null);
  const createAccountMut = useMutation<EmployeeAccountCreateResponse, unknown, void>({
    mutationFn: () => createEmployeeAccount(id),
    onSuccess: (data) => {
      setCreatedPwd(data.temporary_password);
      qc.invalidateQueries({ queryKey: ['employee-account', id] });
    },
  });

  // ---- Delete Employee ----
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const deleteEmpMut = useMutation({
    mutationFn: () => deleteEmployee(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['employees-list'] });
      router.push('/employees');
    },
  });

  // ---- Delete Account ----
  const deleteAccountMut = useMutation({
    mutationFn: () => deleteEmployeeAccount(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['employee-account', id] });
    },
  });

  if (isLoading) return <div className="text-sm text-slate-400">Đang tải hồ sơ nhân viên…</div>;
  if (error) return <ErrorAlert error={error} title="Không tải được hồ sơ nhân viên" />;
  if (!employee) return null;

  const editing = editActive ? form! : employee;

  return (
    <div className="space-y-6">
      <PageHeader
        icon={Users}
        title={employee.full_name}
        subtitle={`${employee.employee_code} · ${employee.email}`}
        actions={
          <div className="flex gap-2">
            <ButtonDanger onClick={() => setDeleteConfirm(true)} disabled={deleteEmpMut.isPending}>
              <Trash2 className="w-4 h-4" /> Xóa nhân viên
            </ButtonDanger>
            <ButtonGhost onClick={() => router.push('/employees')}>
              <ArrowLeft className="w-4 h-4" /> Danh sách
            </ButtonGhost>
            {!editActive ? (
              <ButtonPrimary onClick={startEdit}><Save className="w-4 h-4" /> Sửa hồ sơ</ButtonPrimary>
            ) : (
              <>
                <ButtonGhost onClick={cancelEdit}>Hủy</ButtonGhost>
                <ButtonPrimary onClick={submitEdit} disabled={updateMut.isPending}>
                  {updateMut.isPending ? 'Đang lưu…' : 'Lưu thay đổi'}
                </ButtonPrimary>
              </>
            )}
          </div>
        }
      />

      <Card>
        <SectionTitle icon={Users}>Thông tin hồ sơ</SectionTitle>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Field label="Họ tên">
            <TextInput value={editing.full_name ?? ''} disabled={!editActive}
              onChange={(e) => setForm({ ...form!, full_name: e.target.value })} />
          </Field>
          <Field label="Email">
            <TextInput value={editing.email ?? ''} disabled={!editActive}
              onChange={(e) => setForm({ ...form!, email: e.target.value })} />
          </Field>
          <Field label="Điện thoại">
            <TextInput value={editing.phone ?? ''} disabled={!editActive}
              onChange={(e) => setForm({ ...form!, phone: e.target.value })} />
          </Field>
          <Field label="Ngày sinh">
            <TextInput type="date" value={editing.date_of_birth ?? ''} disabled={!editActive}
              onChange={(e) => setForm({ ...form!, date_of_birth: e.target.value || undefined })} />
          </Field>
          <Field label="Giới tính">
            <Select value={editing.gender ?? ''} disabled={!editActive}
              onChange={(e) => setForm({ ...form!, gender: e.target.value || undefined })}>
              <option value="">—</option>
              <option value="male">Nam</option>
              <option value="female">Nữ</option>
              <option value="other">Khác</option>
            </Select>
          </Field>
          <Field label="Phòng ban">
            <Select value={editing.department_id ?? ''} disabled={!editActive}
              onChange={(e) => setForm({ ...form!, department_id: e.target.value || undefined })}>
              <option value="">—</option>
              {departments?.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </Select>
            {(!departments || departments.length === 0) && editActive && (
              <p className="text-[10px] text-amber-600 mt-1">Chưa có phòng ban. Phòng ban được tự động tạo khi import danh sách nhân viên.</p>
            )}
          </Field>
          <Field label="Chức vụ">
            <Select value={editing.position_id ?? ''} disabled={!editActive}
              onChange={(e) => setForm({ ...form!, position_id: e.target.value || undefined })}>
              <option value="">—</option>
              {positions?.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </Select>
            {(!positions || positions.length === 0) && editActive && (
              <p className="text-[10px] text-amber-600 mt-1">Chưa có chức vụ. Chức vụ được tự động tạo khi import danh sách nhân viên.</p>
            )}
          </Field>
          <Field label="Ngày bắt đầu">
            <TextInput type="date" value={editing.start_date ?? ''} disabled={!editActive}
              onChange={(e) => setForm({ ...form!, start_date: e.target.value })} />
          </Field>
          <Field label="Số CMND/CCCD">
            <TextInput value={editing.id_number ?? ''} disabled={!editActive}
              onChange={(e) => setForm({ ...form!, id_number: e.target.value })} />
          </Field>
          <Field label="Mã số thuế">
            <TextInput value={editing.tax_code ?? ''} disabled={!editActive}
              onChange={(e) => setForm({ ...form!, tax_code: e.target.value })} />
          </Field>
          <Field label="Loại hợp đồng">
            <Select value={editing.contract_type ?? ''} disabled={!editActive}
              onChange={(e) => setForm({ ...form!, contract_type: e.target.value || undefined })}>
              <option value="">—</option>
              <option value="full_time">Xác định thời hạn</option>
              <option value="indefinite">Vô thời hạn</option>
              <option value="probation">Thử việc</option>
              <option value="contractor">Cộng tác viên</option>
              <option value="intern">Thực tập</option>
            </Select>
          </Field>
          <Field label="Địa chỉ">
            <TextArea value={editing.address ?? ''} disabled={!editActive} rows={2}
              onChange={(e) => setForm({ ...form!, address: e.target.value })} />
          </Field>
        </div>
        <div className="flex items-center gap-2 mt-4">
          <Badge tone={employee.is_active ? 'emerald' : 'rose'}>
            {employee.is_active ? 'Đang hoạt động' : 'Không hoạt động'}
          </Badge>
          <span className="text-[10px] font-mono text-slate-400">Cập nhật {formatDateTime(employee.updated_at)}</span>
        </div>
      </Card>

      {/* Documents */}
      <Card>
        <SectionTitle icon={FileText}>Tài liệu (MinIO)</SectionTitle>
        <div className="flex justify-between items-center mb-3">
          <p className="text-xs text-slate-500">Lưu trữ qua presigned, tải xuống có phân quyền.</p>
          <ButtonPrimary onClick={() => setUploadOpen(true)}><Plus className="w-4 h-4" /> Tải tài liệu</ButtonPrimary>
        </div>
        {!documents || documents.length === 0 ? (
          <p className="text-sm text-slate-400 py-4 text-center">Chưa có tài liệu nào.</p>
        ) : (
          <div className="space-y-2">
            {documents.map((doc) => (
              <div key={doc.id} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg border border-slate-100">
                <FileText className="w-4 h-4 text-slate-400 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-slate-800 truncate">{doc.file_name}</p>
                  <p className="text-[10px] text-slate-400">{doc.document_type} · {formatDate(doc.uploaded_at)}</p>
                </div>
                <button onClick={() => handleDownload(doc.id, doc.file_name)} className="p-1.5 rounded-lg hover:bg-slate-200 text-slate-500 hover:text-indigo-600 transition-all" title="Tải xuống">
                  <Download className="w-4 h-4" />
                </button>
                <button onClick={() => delDocMut.mutate(doc.id)} disabled={delDocMut.isPending} className="p-1.5 rounded-lg hover:bg-rose-100 text-slate-400 hover:text-rose-500 transition-all" title="Xóa">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}

        <Modal open={uploadOpen} onClose={() => setUploadOpen(false)} title="Tải lên tài liệu">
          <div className="space-y-3">
            <Field label="Loại tài liệu">
              <Select value={docType} onChange={(e) => setDocType(e.target.value)}>
                {DOC_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
              </Select>
            </Field>
            <Field label="Mô tả (tùy chọn)">
              <TextInput value={docDesc} onChange={(e) => setDocDesc(e.target.value)} />
            </Field>
            <Field label="Tệp">
              <input type="file" onChange={(e) => setDocFile(e.target.files?.[0] ?? null)} className="text-xs" />
            </Field>
            {uploadMut.isError && <ErrorAlert error={uploadMut.error} />}
            <div className="flex justify-end gap-2 pt-2">
              <ButtonGhost onClick={() => setUploadOpen(false)}>Hủy</ButtonGhost>
              <ButtonPrimary onClick={() => uploadMut.mutate()} disabled={uploadMut.isPending || !docFile}>
                <Upload className="w-4 h-4" /> {uploadMut.isPending ? 'Đang tải…' : 'Tải lên'}
              </ButtonPrimary>
            </div>
          </div>
        </Modal>
      </Card>

      {/* Employee Account */}
      <Card>
        <SectionTitle icon={KeyRound}>Tài khoản nhân viên</SectionTitle>
        <p className="text-xs text-slate-500 mb-3">
          HR tạo tài khoản cho Employee. Chỉ Employee đang <strong>active</strong> mới được nhận tài khoản.
        </p>
        {account?.exists ? (
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 text-xs space-y-1">
            <p><span className="text-slate-500">Email:</span> <span className="font-semibold text-slate-800">{account.email}</span></p>
            <p><span className="text-slate-500">Vai trò:</span> <span className="font-mono">{account.role === 'user' ? 'Nhân viên' : account.role}</span></p>
            <p><span className="text-slate-500">Bắt buộc đổi mật khẩu:</span> {account.must_change_password ? 'Có' : 'Không'}</p>
            <div className="pt-2">
              <ButtonDanger onClick={() => deleteAccountMut.mutate()} disabled={deleteAccountMut.isPending}>
                <Trash2 className="w-4 h-4" /> {deleteAccountMut.isPending ? 'Đang xóa…' : 'Xóa tài khoản'}
              </ButtonDanger>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {employee.is_active ? (
              <>
                <p className="text-xs text-slate-500">Employee chưa có tài khoản đăng nhập.</p>
                <ButtonPrimary onClick={() => createAccountMut.mutate()} disabled={createAccountMut.isPending}>
                  <KeyRound className="w-4 h-4" /> {createAccountMut.isPending ? 'Đang tạo…' : 'Tạo tài khoản'}
                </ButtonPrimary>
              </>
            ) : (
              <p className="text-xs text-rose-600">Employee chưa active — không đủ điều kiện nhận tài khoản.</p>
            )}
          </div>
        )}
        {createAccountMut.isError && <div className="mt-2"><ErrorAlert error={createAccountMut.error} /></div>}
        <Modal open={!!createdPwd} onClose={() => setCreatedPwd(null)} title="Tài khoản đã được tạo">
          <div className="space-y-2">
            <p className="text-xs text-slate-500">Cấp mật khẩu tạm thời cho Employee (bắt buộc đổi trong lần đăng nhập đầu tiên):</p>
            <div className="p-3 bg-slate-900 rounded-lg font-mono text-sm text-emerald-300 break-all">{createdPwd ?? ''}</div>
            <p className="text-[10px] text-slate-400">Lưu lại ngay — mật khẩu tạm thời sẽ không hiển thị lại.</p>
            <div className="flex justify-end pt-2">
              <ButtonPrimary onClick={() => setCreatedPwd(null)}>Đã ghi nhận</ButtonPrimary>
            </div>
          </div>
        </Modal>

        {/* Delete Employee Confirmation */}
        <Modal open={deleteConfirm} onClose={() => setDeleteConfirm(false)} title="Xác nhận xóa nhân viên">
          <div className="space-y-3">
            <p className="text-sm text-slate-600">
              Bạn có chắc muốn xóa nhân viên <strong>{employee.full_name}</strong> ({employee.employee_code})?
            </p>
            <p className="text-xs text-rose-600">
              Thao tác này sẽ vô hiệu hóa (soft-delete) nhân viên. Dữ liệu sẽ được giữ lại nhưng nhân viên sẽ không còn truy cập được hệ thống.
            </p>
            {deleteEmpMut.isError && <ErrorAlert error={deleteEmpMut.error} />}
            <div className="flex justify-end gap-2 pt-2">
              <ButtonGhost onClick={() => setDeleteConfirm(false)}>Hủy</ButtonGhost>
              <ButtonDanger onClick={() => deleteEmpMut.mutate()} disabled={deleteEmpMut.isPending}>
                {deleteEmpMut.isPending ? 'Đang xóa…' : 'Xác nhận xóa'}
              </ButtonDanger>
            </div>
          </div>
        </Modal>
      </Card>
    </div>
  );
}