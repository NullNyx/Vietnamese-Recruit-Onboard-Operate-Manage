'use client';

import React, { useState, useCallback, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  BookOpen, Upload, FileText, Search, ChevronLeft, ChevronRight,
  CheckCircle, Clock, AlertTriangle, XCircle, Loader2,
  Pencil, UploadCloud, Trash2, Filter, Info,
} from 'lucide-react';
import { useAuthGuard } from '@/lib/auth/session';
import {
  uploadDocument,
  listDocuments,
  getDocumentDetail,
  updateDocumentMetadata,
  replaceDocumentFile,
  deleteDocument,
} from '@/lib/api/knowledge-base';
import type {
  DocumentListItem,
  DocumentListResponse,
  DocumentDetail,
  DocumentStatus,
  KbType,
  DocumentUpdateRequest,
} from '@/lib/api/knowledge-base';
import {
  PageHeader, Card, SectionTitle, Loading, LoadingRows, EmptyState,
  Badge, ButtonPrimary, ButtonGhost, ButtonDanger, TextInput, Select,
  Field, Modal, ErrorBanner, formatDateTime, statusTone,
} from '@/components/shared-ui';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const CATEGORIES = [
  { value: 'general', label: 'Chung' },
  { value: 'policy', label: 'Chính sách' },
  { value: 'procedure', label: 'Quy trình' },
  { value: 'form', label: 'Biểu mẫu' },
  { value: 'training', label: 'Đào tạo' },
  { value: 'legal', label: 'Pháp lý' },
  { value: 'other', label: 'Khác' },
];

const CATEGORY_LABELS: Record<string, string> = Object.fromEntries(
  CATEGORIES.map((c) => [c.value, c.label]),
);

const KB_TABS: { value: KbType; label: string }[] = [
  { value: 'hr', label: 'HR' },
  { value: 'employee', label: 'Nhân viên' },
];

const STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: 'all', label: 'Tất cả trạng thái' },
  { value: 'ready', label: 'Sẵn sàng' },
  { value: 'pending', label: 'Đang xử lý' },
  { value: 'processing', label: 'Đang indexing' },
  { value: 'error', label: 'Lỗi' },
];

const CATEGORY_FILTER_OPTIONS: { value: string; label: string }[] = [
  { value: 'all', label: 'Tất cả danh mục' },
  ...CATEGORIES,
];

const PAGE_SIZE = 10;

// ---------------------------------------------------------------------------
// Status helpers
// ---------------------------------------------------------------------------

const STATUS_META: Record<DocumentStatus, { label: string; tone: 'slate' | 'amber' | 'emerald' | 'rose' | 'sky' }> = {
  pending: { label: 'Chờ xử lý', tone: 'slate' },
  processing: { label: 'Đang xử lý', tone: 'sky' },
  ready: { label: 'Sẵn sàng', tone: 'emerald' },
  error: { label: 'Lỗi', tone: 'rose' },
};

function StatusBadge({ status }: { status: DocumentStatus }) {
  const meta = STATUS_META[status] ?? { label: status, tone: 'slate' as const };
  return <Badge tone={meta.tone}>{meta.label}</Badge>;
}

function DocumentIcon({ mimeType }: { mimeType: string }) {
  if (mimeType.includes('pdf')) return <FileText className="w-5 h-5 text-rose-500" />;
  if (mimeType.includes('word') || mimeType.includes('doc')) return <FileText className="w-5 h-5 text-blue-500" />;
  return <FileText className="w-5 h-5 text-slate-400" />;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// ---------------------------------------------------------------------------
// Upload Modal
// ---------------------------------------------------------------------------

function UploadModal({
  open,
  onClose,
  kbType,
}: {
  open: boolean;
  onClose: () => void;
  kbType: KbType;
}) {
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [displayName, setDisplayName] = useState('');
  const [category, setCategory] = useState('general');
  const [error, setError] = useState<string | null>(null);

  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error('Vui lòng chọn file.');
      if (!displayName.trim()) throw new Error('Vui lòng nhập tên hiển thị.');
      return uploadDocument(file, displayName.trim(), category, kbType);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kb-documents', kbType] });
      setFile(null);
      setDisplayName('');
      setCategory('general');
      setError(null);
      onClose();
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null;
    setFile(f);
    if (f && !displayName) {
      const name = f.name.replace(/\.[^/.]+$/, '');
      setDisplayName(name);
    }
  };

  const kbLabel = kbType === 'hr' ? 'HR' : 'Nhân viên';

  return (
    <Modal open={open} onClose={onClose} title={`Tải lên tài liệu (${kbLabel})`}>
      <div className="space-y-4">
        {error && <ErrorBanner error={error} />}

        <Field label="File tài liệu" hint="Hỗ trợ PDF, DOCX, DOC, TXT (tối đa 20MB)">
          <input
            type="file"
            accept=".pdf,.docx,.doc,.txt"
            onChange={handleFileChange}
            className="w-full text-sm text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
          />
        </Field>

        <Field label="Tên hiển thị">
          <TextInput
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="VD: Quy định làm việc từ xa"
          />
        </Field>

        <Field label="Danh mục">
          <Select value={category} onChange={(e) => setCategory(e.target.value)}>
            {CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </Select>
        </Field>

        <div className="flex items-center justify-end gap-2 pt-2">
          <ButtonGhost onClick={onClose}>Hủy</ButtonGhost>
          <ButtonPrimary
            onClick={() => uploadMutation.mutate()}
            disabled={uploadMutation.isPending || !file}
          >
            {uploadMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Đang tải lên...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                Tải lên
              </>
            )}
          </ButtonPrimary>
        </div>
      </div>
    </Modal>
  );
}

// ---------------------------------------------------------------------------
// Edit Metadata Modal (PATCH — Issue #261)
// ---------------------------------------------------------------------------

function EditMetadataModal({
  doc,
  open,
  onClose,
  kbType,
}: {
  doc: DocumentListItem | null;
  open: boolean;
  onClose: () => void;
  kbType: KbType;
}) {
  const queryClient = useQueryClient();
  const [displayName, setDisplayName] = useState(doc?.display_name ?? '');
  const [category, setCategory] = useState(doc?.category ?? 'general');
  const [description, setDescription] = useState(doc?.description ?? '');
  const [error, setError] = useState<string | null>(null);

  // Reset form when doc changes
  React.useEffect(() => {
    if (doc) {
      setDisplayName(doc.display_name);
      setCategory(doc.category);
      setDescription(doc.description ?? '');
      setError(null);
    }
  }, [doc]);

  const updateMutation = useMutation({
    mutationFn: async () => {
      if (!doc) throw new Error('Không có tài liệu để sửa.');
      if (!displayName.trim()) throw new Error('Vui lòng nhập tên hiển thị.');
      const body: DocumentUpdateRequest = { display_name: displayName.trim(), category };
      if (description.trim()) {
        body.description = description.trim();
      }
      return updateDocumentMetadata(doc.id, body, kbType);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kb-documents', kbType] });
      setError(null);
      onClose();
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  return (
    <Modal open={open} onClose={onClose} title="Sửa thông tin tài liệu">
      <div className="space-y-4">
        {error && <ErrorBanner error={error} />}
        <p className="text-xs text-slate-500">
          Sửa metadata không làm thay đổi file hoặc re-index. Chỉ cập nhật thông tin hiển thị.
        </p>

        <Field label="Tên hiển thị">
          <TextInput
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="VD: Quy định làm việc từ xa"
          />
        </Field>

        <Field label="Danh mục">
          <Select value={category} onChange={(e) => setCategory(e.target.value)}>
            {CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </Select>
        </Field>

        <Field label="Mô tả" hint="Mô tả ngắn về nội dung tài liệu (không bắt buộc)">
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400"
            placeholder="VD: Quy định về chế độ làm việc từ xa áp dụng từ tháng 7/2026"
          />
        </Field>

        <div className="flex items-center justify-end gap-2 pt-2">
          <ButtonGhost onClick={onClose}>Hủy</ButtonGhost>
          <ButtonPrimary
            onClick={() => updateMutation.mutate()}
            disabled={updateMutation.isPending || !displayName.trim()}
          >
            {updateMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Đang lưu...
              </>
            ) : (
              'Lưu thay đổi'
            )}
          </ButtonPrimary>
        </div>
      </div>
    </Modal>
  );
}

// ---------------------------------------------------------------------------
// Delete Confirm Dialog (Issue #261)
// ---------------------------------------------------------------------------

function DeleteConfirmModal({
  doc,
  open,
  onClose,
  kbType,
}: {
  doc: DocumentListItem | null;
  open: boolean;
  onClose: () => void;
  kbType: KbType;
}) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  const deleteMutation = useMutation({
    mutationFn: async () => {
      if (!doc) throw new Error('Không có tài liệu để xóa.');
      return deleteDocument(doc.id, kbType);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kb-documents', kbType] });
      setError(null);
      onClose();
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  return (
    <Modal open={open} onClose={onClose} title="Xác nhận xóa tài liệu">
      <div className="space-y-4">
        {error && <ErrorBanner error={error} />}

        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-rose-500 mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-semibold text-rose-700">
                Bạn có chắc chắn muốn xóa tài liệu này?
              </p>
              <p className="text-xs text-rose-600 mt-1">
                Hành động này không thể hoàn tác. Tất cả chunks, file trong lưu trữ,
                và metadata sẽ bị xóa vĩnh viễn.
              </p>
            </div>
          </div>
        </div>

        {doc && (
          <div className="text-sm text-slate-700">
            <span className="font-medium">{doc.display_name}</span>
            <span className="text-slate-400"> — {formatFileSize(doc.file_size)}</span>
          </div>
        )}

        <div className="flex items-center justify-end gap-2 pt-2">
          <ButtonGhost onClick={onClose}>Hủy</ButtonGhost>
          <ButtonDanger
            onClick={() => deleteMutation.mutate()}
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Đang xóa...
              </>
            ) : (
              <>
                <Trash2 className="w-4 h-4" />
                Xóa vĩnh viễn
              </>
            )}
          </ButtonDanger>
        </div>
      </div>
    </Modal>
  );
}

// ---------------------------------------------------------------------------
// Document Detail Modal
// ---------------------------------------------------------------------------

function DetailModal({
  docId,
  open,
  onClose,
  kbType,
}: {
  docId: string | null;
  open: boolean;
  onClose: () => void;
  kbType: KbType;
}) {
  const { data: doc, isLoading, error } = useQuery<DocumentDetail>({
    queryKey: ['kb-document-detail', kbType, docId],
    queryFn: () => getDocumentDetail(docId!, kbType),
    enabled: !!docId && open,
  });

  return (
    <Modal open={open} onClose={onClose} title="Chi tiết tài liệu">
      {isLoading ? (
        <Loading label="Đang tải chi tiết..." />
      ) : error ? (
        <ErrorBanner error={error} />
      ) : doc ? (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <Field label="Tên hiển thị">
              <p className="text-sm text-slate-900 font-medium">{doc.display_name}</p>
            </Field>
            <Field label="Trạng thái">
              <StatusBadge status={doc.status} />
            </Field>
            <Field label="Danh mục">
              <p className="text-sm text-slate-700">{CATEGORY_LABELS[doc.category] ?? doc.category}</p>
            </Field>
            <Field label="Tên file">
              <p className="text-sm text-slate-700 truncate">{doc.file_name}</p>
            </Field>
            <Field label="Kích thước">
              <p className="text-sm text-slate-700">{formatFileSize(doc.file_size)}</p>
            </Field>
            <Field label="Loại file">
              <p className="text-sm text-slate-700">{doc.mime_type}</p>
            </Field>
            <Field label="Số đoạn (chunks)">
              <p className="text-sm text-slate-700">{doc.chunk_count}</p>
            </Field>
            <Field label="Ngày tải lên">
              <p className="text-sm text-slate-700">{formatDateTime(doc.created_at)}</p>
            </Field>
          </div>
          {doc.description && (
            <Field label="Mô tả">
              <p className="text-sm text-slate-600 whitespace-pre-wrap">{doc.description}</p>
            </Field>
          )}
          {doc.error_message && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl">
              <p className="text-xs font-semibold text-rose-700 mb-1">Lỗi xử lý:</p>
              <p className="text-xs text-rose-600 whitespace-pre-wrap">{doc.error_message}</p>
            </div>
          )}
        </div>
      ) : null}
    </Modal>
  );
}

// ---------------------------------------------------------------------------
// Document Row with action buttons and error tooltip (Issue #261)
// ---------------------------------------------------------------------------

function DocumentRow({
  doc,
  onEdit,
  onReupload,
  onDelete,
  onDetail,
}: {
  doc: DocumentListItem;
  onEdit: (doc: DocumentListItem) => void;
  onReupload: (doc: DocumentListItem) => void;
  onDelete: (doc: DocumentListItem) => void;
  onDetail: (id: string) => void;
}) {
  const [showErrorTooltip, setShowErrorTooltip] = useState(false);

  return (
    <div className="flex items-center gap-4 p-3 bg-slate-50 rounded-xl border border-slate-100 hover:border-indigo-200 transition-colors">
      <DocumentIcon mimeType={doc.mime_type} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <button
            className="text-sm font-semibold text-slate-900 truncate hover:text-indigo-600 transition-colors text-left"
            onClick={() => onDetail(doc.id)}
          >
            {doc.display_name}
          </button>
          <StatusBadge status={doc.status} />
          {doc.status === 'error' && doc.error_message && (
            <div className="relative">
              <button
                className="text-rose-400 hover:text-rose-600 transition-colors"
                onMouseEnter={() => setShowErrorTooltip(true)}
                onMouseLeave={() => setShowErrorTooltip(false)}
                onClick={() => setShowErrorTooltip(!showErrorTooltip)}
              >
                <Info className="w-4 h-4" />
              </button>
              {showErrorTooltip && (
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 bg-rose-50 border border-rose-200 rounded-xl shadow-lg z-10">
                  <p className="text-xs font-semibold text-rose-700 mb-1">Lỗi xử lý:</p>
                  <p className="text-xs text-rose-600 whitespace-pre-wrap line-clamp-6">
                    {doc.error_message}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
        <div className="flex items-center gap-3 mt-0.5">
          <span className="text-[11px] text-slate-400">
            {doc.file_name}
          </span>
          <span className="text-[11px] text-slate-400">
            {formatFileSize(doc.file_size)}
          </span>
          {doc.chunk_count > 0 && (
            <span className="text-[11px] text-slate-400">
              {doc.chunk_count} đoạn
            </span>
          )}
        </div>
      </div>
      <div className="text-right shrink-0 flex items-center gap-1">
        <div className="mr-3">
          <span className="text-[11px] text-slate-400 block">
            {CATEGORY_LABELS[doc.category] ?? doc.category}
          </span>
          <div className="text-[10px] text-slate-400 mt-0.5">
            {formatDateTime(doc.created_at)}
          </div>
        </div>

        {/* Action buttons */}
        <button
          onClick={(e) => { e.stopPropagation(); onEdit(doc); }}
          className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 transition-all"
          title="Sửa thông tin"
        >
          <Pencil className="w-4 h-4" />
        </button>
        <button
          onClick={(e) => { e.stopPropagation(); onReupload(doc); }}
          className="p-1.5 rounded-lg text-slate-400 hover:text-amber-600 hover:bg-amber-50 transition-all"
          title="Upload lại file"
        >
          <UploadCloud className="w-4 h-4" />
        </button>
        <button
          onClick={(e) => { e.stopPropagation(); onDelete(doc); }}
          className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-all"
          title="Xóa tài liệu"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function KnowledgeBasePage() {
  useAuthGuard({ requireAuth: true, requireAdmin: true });

  const [page, setPage] = useState(1);
  const [showUpload, setShowUpload] = useState(false);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<KbType>('hr');

  // Filters (Issue #261)
  const [filterCategory, setFilterCategory] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');

  // Action modals
  const [editingDoc, setEditingDoc] = useState<DocumentListItem | null>(null);
  const [deletingDoc, setDeletingDoc] = useState<DocumentListItem | null>(null);
  const [reuploadDoc, setReuploadDoc] = useState<DocumentListItem | null>(null);
  const reuploadInputRef = useRef<HTMLInputElement>(null);

  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery<DocumentListResponse>({
    queryKey: ['kb-documents', activeTab, page, filterCategory, filterStatus],
    queryFn: () =>
      listDocuments(
        activeTab,
        page,
        PAGE_SIZE,
        filterCategory,
        filterStatus,
      ),
    staleTime: 10 * 1000,
  });

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  const hasActiveFilters = filterCategory !== 'all' || filterStatus !== 'all';

  const handleTabChange = (tab: KbType) => {
    setActiveTab(tab);
    setPage(1);
    setFilterCategory('all');
    setFilterStatus('all');
  };

  const handleResetFilters = () => {
    setFilterCategory('all');
    setFilterStatus('all');
    setPage(1);
  };

  // Re-upload mutation (Issue #261)
  const reuploadMutation = useMutation({
    mutationFn: async ({ docId, file }: { docId: string; file: File }) => {
      return replaceDocumentFile(docId, file, activeTab);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kb-documents', activeTab] });
      setReuploadDoc(null);
    },
    onError: () => {
      // Error handled in the UI via the inline input
    },
  });

  const handleReuploadClick = (doc: DocumentListItem) => {
    setReuploadDoc(doc);
    // Trigger hidden file input
    setTimeout(() => {
      reuploadInputRef.current?.click();
    }, 100);
  };

  const handleReuploadFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && reuploadDoc) {
      reuploadMutation.mutate({ docId: reuploadDoc.id, file });
    }
    // Reset input for next use
    if (e.target) e.target.value = '';
  };

  const kbLabel = activeTab === 'hr' ? 'HR' : 'Nhân viên';

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        icon={BookOpen}
        title="Tài liệu nội bộ"
        subtitle="Quản lý tài liệu Knowledge Base cho HR và Nhân viên. Tải lên tài liệu để hệ thống tự động xử lý và lập chỉ mục."
        actions={
          <ButtonPrimary onClick={() => setShowUpload(true)}>
            <Upload className="w-4 h-4" />
            Tải lên tài liệu
          </ButtonPrimary>
        }
      />

      {/* Tabs */}
      <div className="flex items-center gap-1 bg-slate-100 rounded-xl p-1 w-fit">
        {KB_TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => handleTabChange(tab.value)}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-all ${
              activeTab === tab.value
                ? 'bg-white text-indigo-700 shadow-sm'
                : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Filters (Issue #261) */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <Select
            value={filterCategory}
            onChange={(e) => { setFilterCategory(e.target.value); setPage(1); }}
            className="text-sm"
          >
            {CATEGORY_FILTER_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </Select>
        </div>
        <Select
          value={filterStatus}
          onChange={(e) => { setFilterStatus(e.target.value); setPage(1); }}
          className="text-sm"
        >
          {STATUS_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </Select>
        {hasActiveFilters && (
          <button
            onClick={handleResetFilters}
            className="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
          >
            Xóa bộ lọc
          </button>
        )}
        {data && (
          <span className="text-xs text-slate-400 ml-auto">
            {data.total} tài liệu
          </span>
        )}
      </div>

      {/* Document List */}
      <Card>
        <SectionTitle icon={FileText}>
          Danh sách tài liệu {kbLabel}
        </SectionTitle>

        {isLoading ? (
          <LoadingRows count={5} />
        ) : error ? (
          <ErrorBanner error={error} />
        ) : data?.items.length ? (
          <div className="space-y-2">
            {data.items.map((doc) => (
              <DocumentRow
                key={doc.id}
                doc={doc}
                onEdit={setEditingDoc}
                onReupload={handleReuploadClick}
                onDelete={setDeletingDoc}
                onDetail={setSelectedDocId}
              />
            ))}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between pt-3">
                <span className="text-xs text-slate-500">
                  Trang {page} / {totalPages}
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page <= 1}
                    className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 disabled:opacity-40 transition-all"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setPage((p) => p + 1)}
                    disabled={page >= totalPages}
                    className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 disabled:opacity-40 transition-all"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : hasActiveFilters ? (
          <EmptyState
            filtered={true}
            onReset={handleResetFilters}
            emptyFiltered="Không có tài liệu nào khớp với bộ lọc hiện tại."
            hintFiltered="Thử thay đổi danh mục hoặc trạng thái."
          />
        ) : (
          <EmptyState
            filtered={false}
            emptyData={`Chưa có tài liệu nào trong Knowledge Base ${kbLabel}.`}
            hintData="Tải lên tài liệu PDF, DOCX để bắt đầu xây dựng kho kiến thức."
          />
        )}
      </Card>

      {/* Modals */}
      <UploadModal
        open={showUpload}
        onClose={() => setShowUpload(false)}
        kbType={activeTab}
      />
      <DetailModal
        docId={selectedDocId}
        open={!!selectedDocId}
        onClose={() => setSelectedDocId(null)}
        kbType={activeTab}
      />
      <EditMetadataModal
        doc={editingDoc}
        open={!!editingDoc}
        onClose={() => setEditingDoc(null)}
        kbType={activeTab}
      />
      <DeleteConfirmModal
        doc={deletingDoc}
        open={!!deletingDoc}
        onClose={() => setDeletingDoc(null)}
        kbType={activeTab}
      />

      {/* Hidden file input for re-upload (Issue #261) */}
      <input
        ref={reuploadInputRef}
        type="file"
        accept=".pdf,.docx,.doc,.txt"
        className="hidden"
        onChange={handleReuploadFileChange}
      />

      {/* Re-upload status indicator */}
      {reuploadMutation.isPending && reuploadDoc && (
        <div className="fixed bottom-4 right-4 z-50 p-3 bg-indigo-50 border border-indigo-200 rounded-xl shadow-lg flex items-center gap-3">
          <Loader2 className="w-4 h-4 animate-spin text-indigo-600" />
          <div>
            <p className="text-sm font-medium text-indigo-700">Đang upload lại file...</p>
            <p className="text-xs text-indigo-500">{reuploadDoc.display_name}</p>
          </div>
        </div>
      )}
      {reuploadMutation.isError && (
        <div className="fixed bottom-4 right-4 z-50 p-3 bg-rose-50 border border-rose-200 rounded-xl shadow-lg">
          <p className="text-sm font-medium text-rose-700">Upload lại thất bại</p>
          <p className="text-xs text-rose-600">
            {reuploadMutation.error instanceof Error ? reuploadMutation.error.message : 'Lỗi không xác định'}
          </p>
        </div>
      )}
    </div>
  );
}
