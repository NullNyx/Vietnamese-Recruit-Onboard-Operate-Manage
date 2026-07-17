'use client';

import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { Upload, ArrowLeft, CheckCircle, XCircle } from 'lucide-react';
import { importEmployees } from '@/lib/api/employees';
import type { ImportResult } from '@/lib/api/types';
import { useAuthGuard } from '@/lib/auth/session';
import {
  PageHeader, Card, SectionTitle, ButtonPrimary, ButtonGhost, ErrorAlert,
} from '@/components/shared-ui';

export default function ImportEmployeesPage() {
  useAuthGuard({ requireAuth: true, requireAdmin: true });
  const router = useRouter();
  const qc = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);

  const importMut = useMutation({
    mutationFn: () => {
      if (!file) throw new Error('Vui lòng chọn tệp Excel .xlsx');
      return importEmployees(file);
    },
    onSuccess: (r) => {
      setResult(r);
      qc.invalidateQueries({ queryKey: ['employees-list'] });
      qc.invalidateQueries({ queryKey: ['departments-list'] });
      qc.invalidateQueries({ queryKey: ['positions-list'] });
    },
  });

  return (
    <div className="space-y-6">
      <PageHeader
        icon={Upload}
        title="Import Nhân viên"
        subtitle="Nhập danh sách Employee từ tệp Excel (.xlsx). Phòng ban/Chức vụ mới sẽ tự tạo."
        actions={
          <ButtonGhost onClick={() => router.push('/employees')}>
            <ArrowLeft className="w-4 h-4" /> Danh sách
          </ButtonGhost>
        }
      />

      <Card>
        <SectionTitle icon={Upload}>Chọn tệp</SectionTitle>
        <input
          type="file"
          accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="text-xs"
        />
        <p className="text-[10px] text-slate-400 mt-2">Tệp tối đa 10MB · định dạng .xlsx</p>

        {importMut.isError && <div className="mt-3"><ErrorAlert error={importMut.error} /></div>}

        <div className="flex justify-end mt-4">
          <ButtonPrimary onClick={() => importMut.mutate()} disabled={importMut.isPending || !file}>
            <Upload className="w-4 h-4" /> {importMut.isPending ? 'Đang nhập…' : 'Import'}
          </ButtonPrimary>
        </div>
      </Card>

      {result && (
        <Card>
          <SectionTitle icon={CheckCircle}>Kết quả import</SectionTitle>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
              <p className="text-2xl font-bold text-slate-900">{result.total_rows}</p>
              <p className="text-[10px] text-slate-400">Tổng dòng</p>
            </div>
            <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-100">
              <p className="text-2xl font-bold text-emerald-700">{result.success_count}</p>
              <p className="text-[10px] text-emerald-600">Thành công</p>
            </div>
            <div className="p-3 bg-rose-50 rounded-xl border border-rose-100">
              <p className="text-2xl font-bold text-rose-700">{result.error_count}</p>
              <p className="text-[10px] text-rose-600">Lỗi</p>
            </div>
            <div className="p-3 bg-indigo-50 rounded-xl border border-indigo-100">
              <p className="text-2xl font-bold text-indigo-700">
                {(result.departments_created ?? 0) + (result.positions_created ?? 0)}
              </p>
              <p className="text-[10px] text-indigo-600">Phòng ban/Chức vụ mới</p>
            </div>
          </div>

          {result.errors?.length > 0 && (
            <div className="mt-4">
              <div className="flex items-center gap-2 mb-2 text-rose-600">
                <XCircle className="w-4 h-4" />
                <span className="text-xs font-semibold">Chi tiết lỗi</span>
              </div>
              <div className="max-h-48 overflow-y-auto space-y-1">
                {result.errors.map((e, i) => (
                  <div key={i} className="text-[11px] font-mono text-slate-600 p-2 bg-slate-50 rounded">
                    Dòng {e.row}: {e.message}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex justify-end mt-4">
            <ButtonGhost onClick={() => router.push('/employees')}>Hoàn tất</ButtonGhost>
          </div>
        </Card>
      )}
    </div>
  );
}