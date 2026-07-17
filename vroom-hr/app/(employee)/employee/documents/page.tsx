'use client';

import React, { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { FolderOpen, FileText, Upload, Download, Plus } from 'lucide-react';
import { listDocuments, uploadDocument, downloadDocument } from '@/lib/api/employees';
import type { EmployeeDocument } from '@/lib/api/types';
import { useAuthGuard, useSession } from '@/lib/auth/session';
import {
  PageHeader, Card, SectionTitle, Field, TextInput, Select, ButtonPrimary, ButtonGhost,
  ErrorAlert, EmptyState, Modal, formatDate,
} from '@/components/operate';

const DOC_TYPES = ['Hợp đồng', 'CMND/CCCD', 'Bằng cấp', 'Sổ bảo hiểm', 'Khác'];

export default function EmployeeDocumentsPage() {
  useAuthGuard({ requireAuth: true, requireEmployee: true });
  const { user } = useSession();
  const employeeId = user?.employee_id ?? null;
  const qc = useQueryClient();

  const { data: documents, isLoading, error } = useQuery<EmployeeDocument[]>({
    queryKey: ['employee-documents', employeeId],
    queryFn: () => listDocuments(employeeId!),
    enabled: Boolean(employeeId),
  });

  const [uploadOpen, setUploadOpen] = useState(false);
  const [docType, setDocType] = useState(DOC_TYPES[0]);
  const [docDesc, setDocDesc] = useState('');
  const [docFile, setDocFile] = useState<File | null>(null);

  useEffect(() => {
    if (!uploadOpen) {
      setDocType(DOC_TYPES[0]);
      setDocDesc('');
      setDocFile(null);
    }
  }, [uploadOpen]);

  const uploadMut = useMutation({
    mutationFn: () => {
      if (!docFile) throw new Error('Vui lòng chọn tệp');
      return uploadDocument(employeeId!, docFile, docType, docDesc || undefined);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['employee-documents', employeeId] });
      setUploadOpen(false);
    },
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
      console.error(e);
    }
  };

  if (!employeeId) return null;

  return (
    <div className="space-y-6">
      <PageHeader
        icon={FolderOpen}
        title="Tài liệu của tôi"
        subtitle="Kho tài liệu cá nhân (MinIO presigned). Bạn có thể tải lên và tải xuống."
        actions={<ButtonPrimary onClick={() => setUploadOpen(true)}><Plus className="w-4 h-4" /> Tải tài liệu</ButtonPrimary>}
      />

      <Card>
        <SectionTitle icon={FolderOpen}>Danh sách tài liệu</SectionTitle>
        {error ? <ErrorAlert error={error} title="Không tải được tài liệu" />
          : isLoading && !documents ? <p className="text-sm text-slate-400">Đang tải…</p>
          : !documents?.length ? <EmptyState hasFilters={false} emptyData="Chưa có tài liệu nào của bạn." />
          : (
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
                </div>
              ))}
            </div>
          )}
        <p className="text-[10px] text-slate-400 mt-3">Việc xóa tài liệu do HR thực hiện.</p>
      </Card>

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
    </div>
  );
}