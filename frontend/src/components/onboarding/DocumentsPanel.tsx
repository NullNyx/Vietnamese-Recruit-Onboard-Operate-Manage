'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  listOnboardingDocuments,
  uploadOnboardingDocument,
  verifyOnboardingDocument,
  onboardingKeys,
  type OnboardingDocument,
} from '@/lib/api/onboarding';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';
import {
  AlertCircle,
  Check,
  FileText,
  Loader2,
  Upload,
  X,
  Sparkles,
  RotateCcw,
  ThumbsUp,
  ThumbsDown,
  Info,
  FileWarning,
} from 'lucide-react';
import { useRef, useState } from 'react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';

// ─── Helpers ───────────────────────────────────────────────────────────

const STATUS_LABELS: Record<string, { label: string; color: string; icon: typeof FileText }> = {
  pending: { label: 'Chờ tải lên', color: 'bg-gray-100 text-gray-600', icon: FileText },
  uploaded: { label: 'Đã tải lên', color: 'bg-blue-100 text-blue-700', icon: Upload },
  verified: { label: 'Đã xác thực', color: 'bg-emerald-100 text-emerald-700', icon: Check },
  rejected: { label: 'Từ chối', color: 'bg-red-100 text-red-700', icon: X },
};

function getStatusMeta(status: string) {
  return STATUS_LABELS[status] || STATUS_LABELS.pending;
}

// ─── Empty State ───────────────────────────────────────────────────────

function EmptyDocsState() {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
      <FileText className="h-10 w-10 mb-3 opacity-30" />
      <p className="text-sm">Không có tài liệu nào</p>
    </div>
  );
}

// ─── Document Card ─────────────────────────────────────────────────────

function DocumentCard({
  doc,
  isComplete,
  onUpload,
  onVerify,
  onReject,
}: {
  doc: OnboardingDocument;
  isComplete: boolean;
  onUpload: (doc: OnboardingDocument) => void;
  onVerify: (doc: OnboardingDocument) => void;
  onReject: (doc: OnboardingDocument) => void;
}) {
  const meta = getStatusMeta(doc.status);
  const Icon = meta.icon;

  return (
    <div className="rounded-xl border bg-card p-4 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1 min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">{doc.display_name}</span>
            {doc.is_required && (
              <span className="text-[10px] font-medium text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200">
                Bắt buộc
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <span className={cn('inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium', meta.color)}>
              <Icon className="size-3" />
              {meta.label}
            </span>
          </div>
        </div>
      </div>

      {/* Rejection reason */}
      {doc.status === 'rejected' && doc.reject_reason && (
        <div className="flex items-start gap-2 p-2 rounded-lg bg-red-50 text-red-700 text-xs">
          <FileWarning className="size-3.5 mt-0.5 shrink-0" />
          <span>{doc.reject_reason}</span>
        </div>
      )}

      {/* Verified by */}
      {doc.status === 'verified' && (
        <p className="text-xs text-muted-foreground">
          Đã xác thực {doc.verified_at ? new Date(doc.verified_at).toLocaleString('vi-VN') : ''}
        </p>
      )}

      {/* AI extraction placeholder */}
      <div className="rounded-lg border border-dashed bg-muted/30 p-3 flex items-start gap-2.5">
        <Sparkles className="size-4 text-muted-foreground/40 mt-0.5 shrink-0" />
        <div className="text-xs text-muted-foreground/60 space-y-1 flex-1">
          <p className="font-medium text-muted-foreground/50">Trích xuất AI</p>
          {doc.ai_extraction ? (
            <div className="flex items-center gap-2">
              <span className="text-[11px]">Có dữ liệu gợi ý</span>
              <div className="flex gap-1">
                <button className="inline-flex items-center gap-1 rounded px-1.5 py-0.5 bg-emerald-100 text-emerald-700 text-[10px] hover:bg-emerald-200">
                  <ThumbsUp className="size-3" /> Áp dụng
                </button>
                <button className="inline-flex items-center gap-1 rounded px-1.5 py-0.5 bg-red-100 text-red-600 text-[10px] hover:bg-red-200">
                  <ThumbsDown className="size-3" /> Bỏ qua
                </button>
              </div>
            </div>
          ) : (
            <p className="text-[11px]">Chưa có gợi ý AI. Kết quả trích xuất sẽ hiển thị tại đây.</p>
          )}
        </div>
      </div>

      {/* Actions */}
      {!isComplete && (
        <div className="flex gap-2 pt-1">
          {doc.status === 'pending' || doc.status === 'rejected' ? (
            <Button
              size="sm"
              variant="outline"
              className="h-8 text-xs"
              onClick={() => onUpload(doc)}
            >
              <Upload className="size-3.5 mr-1" />
              Tải lên
            </Button>
          ) : null}
          {doc.status === 'uploaded' ? (
            <>
              <Button
                size="sm"
                variant="outline"
                className="h-8 text-xs text-emerald-600"
                onClick={() => onVerify(doc)}
              >
                <Check className="size-3.5 mr-1" />
                Xác thực
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="h-8 text-xs text-red-600"
                onClick={() => onReject(doc)}
              >
                <X className="size-3.5 mr-1" />
                Từ chối
              </Button>
            </>
          ) : null}
          {doc.status === 'rejected' && (
            <Button
              size="sm"
              variant="outline"
              className="h-8 text-xs"
              onClick={() => onUpload(doc)}
            >
              <RotateCcw className="size-3.5 mr-1" />
              Tải lại
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Main Component ────────────────────────────────────────────────────

export function DocumentsPanel({ processId, isComplete }: { processId: string; isComplete: boolean }) {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadingDoc, setUploadingDoc] = useState<OnboardingDocument | null>(null);
  const [actionDoc, setActionDoc] = useState<OnboardingDocument | null>(null);
  const [actionType, setActionType] = useState<'verify' | 'reject' | null>(null);
  const [rejectReason, setRejectReason] = useState('');

  const { data: documents, isLoading } = useQuery({
    queryKey: ['onboarding', 'documents', processId],
    queryFn: () => listOnboardingDocuments(processId),
  });

  const uploadMutation = useMutation({
    mutationFn: (docId: string) => uploadOnboardingDocument(docId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['onboarding', 'documents', processId] });
      toast.success('Đã tải lên');
    },
    onError: (err: Error) => toast.error(err.message || 'Tải lên thất bại'),
  });

  const verifyMutation = useMutation({
    mutationFn: ({ docId, data }: { docId: string; data: { verified: boolean; reject_reason?: string | null } }) =>
      verifyOnboardingDocument(docId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['onboarding', 'documents', processId] });
      toast.success(actionType === 'verify' ? 'Đã xác thực' : 'Đã từ chối');
      setActionDoc(null);
      setActionType(null);
      setRejectReason('');
    },
    onError: (err: Error) => toast.error(err.message || 'Thao tác thất bại'),
  });

  const handleFileSelect = (doc: OnboardingDocument) => {
    setUploadingDoc(doc);
    // Simulate upload: trigger a file picker, then upload
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.pdf,.jpg,.jpeg,.png,.doc,.docx';
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) {
        // For MVP we just mark uploaded without file bytes (minio integration is async)
        await uploadMutation.mutateAsync(doc.id);
      }
      setUploadingDoc(null);
    };
    input.click();
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!documents || documents.length === 0) return <EmptyDocsState />;

  return (
    <div className="space-y-3">
      {/* Summary */}
      <div className="flex items-center gap-4 text-xs text-muted-foreground mb-4">
        <span>Tổng: {documents.length}</span>
        <span className="text-amber-600">Chờ: {documents.filter(d => d.status === 'pending').length}</span>
        <span className="text-blue-600">Đã tải: {documents.filter(d => d.status === 'uploaded').length}</span>
        <span className="text-emerald-600">Đã xác thực: {documents.filter(d => d.status === 'verified').length}</span>
        <span className="text-red-600">Từ chối: {documents.filter(d => d.status === 'rejected').length}</span>
      </div>

      {documents.map((doc) => (
        <DocumentCard
          key={doc.id}
          doc={doc}
          isComplete={isComplete}
          onUpload={handleFileSelect}
          onVerify={(d) => { setActionDoc(d); setActionType('verify'); }}
          onReject={(d) => { setActionDoc(d); setActionType('reject'); setRejectReason(''); }}
        />
      ))}

      {/* Reject dialog */}
      <AlertDialog open={actionType === 'reject' && !!actionDoc} onOpenChange={(open) => !open && setActionDoc(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Từ chối tài liệu</AlertDialogTitle>
            <AlertDialogDescription>
              Nhập lý do từ chối cho <strong>{actionDoc?.display_name}</strong>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="px-6">
            <textarea
              className="w-full min-h-[80px] rounded-lg border p-2 text-sm"
              placeholder="Lý do từ chối..."
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
            />
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setActionDoc(null)}>Hủy</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={!rejectReason.trim()}
              onClick={() => {
                if (actionDoc) {
                  verifyMutation.mutate({ docId: actionDoc.id, data: { verified: false, reject_reason: rejectReason } });
                }
              }}
            >
              Xác nhận từ chối
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Upload file input */}
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        onChange={(e) => {
          if (e.target.files?.[0] && uploadingDoc) {
            uploadMutation.mutate(uploadingDoc.id);
          }
        }}
      />
    </div>
  );
}
