'use client';

import React, { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { User, Save } from 'lucide-react';
import { getEmployee, updateEmployee } from '@/lib/api/employees';
import { listDepartments } from '@/lib/api/departments';
import { listPositions } from '@/lib/api/positions';
import type { Employee, Department, Position } from '@/lib/api/types';
import { useAuthGuard, useSession } from '@/lib/auth/session';
import {
  PageHeader, Card, SectionTitle, Field, TextInput, TextArea, Select,
  ButtonPrimary, ErrorAlert, Badge, formatDateTime,
} from '@/components/operate';

export default function EmployeeProfilePage() {
  useAuthGuard({ requireAuth: true, requireEmployee: true });
  const { user } = useSession();
  const employeeId = user?.employee_id ?? null;
  const qc = useQueryClient();

  const { data: employee, isLoading, error } = useQuery<Employee>({
    queryKey: ['employee', employeeId],
    queryFn: () => getEmployee(employeeId!),
    enabled: Boolean(employeeId),
  });
  const { data: departments } = useQuery<Department[]>({ queryKey: ['departments-list'], queryFn: listDepartments, staleTime: 60_000 });
  const { data: positions } = useQuery<Position[]>({ queryKey: ['positions-list'], queryFn: listPositions, staleTime: 60_000 });

  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [editing, setEditing] = useState(false);

  // Populate editable fields once the profile arrives.
  useEffect(() => {
    if (employee) {
      setPhone(employee.phone ?? '');
      setAddress(employee.address ?? '');
    }
  }, [employee]);

  const saveMut = useMutation({
    mutationFn: () => updateEmployee(employeeId!, { phone, address }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['employee', employeeId] });
      setEditing(false);
    },
  });

  if (!employeeId) {
    return (
      <div className="space-y-6">
        <PageHeader icon={User} title="Hồ sơ của tôi" subtitle="Tài khoản chưa liên kết Employee." />
        <Card><SectionTitle icon={User}>Hồ sơ</SectionTitle>
          <p className="text-xs text-rose-600">Tài khoản đăng nhập chưa gắn với Employee. Vui lòng liên hệ HR.</p>
        </Card>
      </div>
    );
  }

  const deptName = (id: string | null) => departments?.find((d) => d.id === id)?.name ?? '—';
  const posName = (id: string | null) => positions?.find((p) => p.id === id)?.name ?? '—';

  return (
    <div className="space-y-6">
      <PageHeader
        icon={User}
        title="Hồ sơ của tôi"
        subtitle="Xem thông tin nhân sự. Bạn chỉ có thể tự cập nhật điện thoại và địa chỉ."
        actions={employee && !editing ? (
          <ButtonPrimary onClick={() => setEditing(true)}><Save className="w-4 h-4" /> Cập nhật liên lạc</ButtonPrimary>
        ) : null}
      />

      {isLoading ? <p className="text-sm text-slate-400">Đang tải hồ sơ…</p>
        : error ? <ErrorAlert error={error} title="Không tải được hồ sơ" />
        : employee && (
          <Card>
            <SectionTitle icon={User}>Thông tin hồ sơ</SectionTitle>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field label="Mã nhân viên"><TextInput value={employee.employee_code} disabled /></Field>
              <Field label="Họ tên"><TextInput value={employee.full_name} disabled /></Field>
              <Field label="Email"><TextInput value={employee.email} disabled /></Field>
              <Field label="Trạng thái">
                <div className="pt-1"><Badge tone={employee.is_active ? 'emerald' : 'rose'}>{employee.is_active ? 'Đang hoạt động' : 'Không hoạt động'}</Badge></div>
              </Field>
              <Field label="Phòng ban"><TextInput value={deptName(employee.department_id)} disabled /></Field>
              <Field label="Chức vụ"><TextInput value={posName(employee.position_id)} disabled /></Field>
              <Field label="Ngày bắt đầu"><TextInput value={employee.start_date ?? '—'} disabled /></Field>
              <Field label="Loại hợp đồng"><TextInput value={employee.contract_type ?? '—'} disabled /></Field>

              <Field label="Điện thoại (sửa được)">
                <TextInput value={phone} disabled={!editing} onChange={(e) => setPhone(e.target.value)} />
              </Field>
              <Field label="Địa chỉ (sửa được)">
                <TextArea rows={2} value={address} disabled={!editing} onChange={(e) => setAddress(e.target.value)} />
              </Field>
            </div>

            <div className="flex items-center justify-between pt-4 mt-4 border-t border-slate-100">
              <span className="text-[10px] font-mono text-slate-400">Cập nhật {formatDateTime(employee.updated_at)}</span>
              {editing && (
                <div className="flex gap-2">
                  <button onClick={() => { setEditing(false); }} className="px-3 py-2 rounded-lg text-xs font-semibold bg-white border border-slate-200 hover:bg-slate-50">Hủy</button>
                  <ButtonPrimary onClick={() => saveMut.mutate()} disabled={saveMut.isPending}>
                    {saveMut.isPending ? 'Đang lưu…' : 'Lưu thay đổi'}
                  </ButtonPrimary>
                </div>
              )}
            </div>
            {saveMut.isError && <div className="mt-3"><ErrorAlert error={saveMut.error} /></div>}
          </Card>
        )}
    </div>
  );
}