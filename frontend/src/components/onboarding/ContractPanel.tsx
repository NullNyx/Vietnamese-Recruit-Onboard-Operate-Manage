'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  getOnboardingContractDraft as getContractDraft,
  updateOnboardingContractDraft as updateContractDraft,
  generateContractDraft,
  updateContractStatus,
  exportContractDraft,
  type OnboardingContractDraft,
} from '@/lib/api/onboarding';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';
import {
  FileText,
  Loader2,
  Sparkles,
  Download,
  Send,
  CheckCircle2,
  FileSignature,
  Edit,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';

// ─── Status helpers ──────────────────────────────────────────────────────

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: typeof FileText; next: string | null }> = {
  draft: { label: 'Nháp', color: 'bg-gray-100 text-gray-600', icon: FileText, next: 'ready' },
  ready: { label: 'Sẵn sàng', color: 'bg-blue-100 text-blue-700', icon: Send, next: 'sent' },
  sent: { label: 'Đã gửi', color: 'bg-amber-100 text-amber-700', icon: FileSignature, next: 'signed' },
  signed: { label: 'Đã ký', color: 'bg-emerald-100 text-emerald-700', icon: CheckCircle2, next: null },
};

const CONTRACT_TYPE_OPTIONS = [
  { value: 'labor', label: 'Hợp đồng lao động' },
  { value: 'offer', label: 'Offer letter' },
  { value: 'nda', label: 'NDA' },
  { value: 'other', label: 'Khác' },
];

// ─── Sub-components ──────────────────────────────────────────────────────

function DraftEditor({
  content,
  contractType,
  isLocked,
  onContentChange,
  onTypeChange,
  onGenerate,
  onSave,
  onExport,
  isSaving,
  isGenerating,
}: {
  content: string;
  contractType: string;
  isLocked: boolean;
  onContentChange: (v: string) => void;
  onTypeChange: (v: string) => void;
  onGenerate: () => void;
  onSave: () => void;
  onExport: () => void;
  isSaving: boolean;
  isGenerating: boolean;
}) {
  return (
    <div className="space-y-4">
      {/* Contract type */}
      <div className="flex items-center gap-3">
        <label className="text-sm font-medium text-muted-foreground min-w-24">Loại hợp đồng</label>
        <select
          value={contractType}
          onChange={(e) => onTypeChange(e.target.value)}
          disabled={isLocked}
          className="h-9 rounded-lg border bg-background px-3 text-sm"
        >
          {CONTRACT_TYPE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>

      {/* Content editor */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-muted-foreground">Nội dung hợp đồng</label>
        <Textarea
          value={content}
          onChange={(e) => onContentChange(e.target.value)}
          placeholder="Nhập nội dung hợp đồng..."
          className="min-h-[300px] font-mono text-sm"
          disabled={isLocked}
        />
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 flex-wrap">
        <Button
          variant="outline"
          size="sm"
          className="h-8 text-xs"
          onClick={onGenerate}
          disabled={isGenerating || isLocked}
        >
          <Sparkles className="size-3.5 mr-1" />
          {isGenerating ? 'Đang tạo...' : 'Tạo AI (placeholder)'}
        </Button>
        <Button
          variant="default"
          size="sm"
          className="h-8 text-xs"
          onClick={onSave}
          disabled={isSaving || isLocked}
        >
          <Edit className="size-3.5 mr-1" />
          {isSaving ? 'Đang lưu...' : 'Lưu'}
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="h-8 text-xs"
          onClick={onExport}
        >
          <Download className="size-3.5 mr-1" />
          Xuất file
        </Button>
      </div>
    </div>
  );
}

function StatusTracker({
  currentStatus,
  onAdvance,
  isPending,
}: {
  currentStatus: string;
  onAdvance: () => void;
  isPending: boolean;
}) {
  const steps = ['draft', 'ready', 'sent', 'signed'];
  const config = STATUS_CONFIG[currentStatus] || STATUS_CONFIG.draft;
  const Icon = config.icon;

  return (
    <div className="rounded-xl border bg-card p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium">Trạng thái</h4>
        <span className={cn('inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium border', config.color)}>
          <Icon className="size-3.5" />
          {config.label}
        </span>
      </div>

      {/* Progress bar */}
      <div className="flex items-center gap-1">
        {steps.map((step, idx) => {
          const stepIdx = steps.indexOf(currentStatus);
          const isActive = idx <= stepIdx;
          return (
            <div key={step} className="flex items-center gap-1 flex-1">
              <div className={cn(
                'h-2 rounded-full flex-1 transition-colors',
                isActive ? 'bg-primary' : 'bg-secondary',
                idx === 0 ? 'rounded-l-full' : '',
                idx === steps.length - 1 ? 'rounded-r-full' : '',
              )} />
            </div>
          );
        })}
      </div>

      {/* Step labels */}
      <div className="flex justify-between text-[10px] text-muted-foreground">
        <span>Nháp</span>
        <span>Sẵn sàng</span>
        <span>Đã gửi</span>
        <span>Đã ký</span>
      </div>

      {/* Advance button */}
      {config.next && (
        <Button
          size="sm"
          className="h-8 text-xs w-full"
          onClick={onAdvance}
          disabled={isPending}
        >
          {isPending ? 'Đang cập nhật...' : `Chuyển sang "${STATUS_CONFIG[config.next]?.label}"`}
        </Button>
      )}
    </div>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────

export function ContractPanel({
  processId,
  isComplete,
  initialDraft,
}: {
  processId: string;
  isComplete: boolean;
  initialDraft?: OnboardingContractDraft | null;
}) {
  const queryClient = useQueryClient();
  const [localContent, setLocalContent] = useState('');
  const [localType, setLocalType] = useState('labor');
  
  const { data: draft, isLoading, isError, refetch } = useQuery({
    queryKey: ['onboarding', 'contract', processId],
    queryFn: () => getContractDraft(processId),
    enabled: !!processId,
    initialData: initialDraft ?? undefined,
  });

  // Sync local state from server data
  useEffect(() => {
    if (draft) {
      setLocalContent(draft.content || '');
      setLocalType(draft.contract_type);
    }
  }, [draft]);

  const saveMutation = useMutation({
    mutationFn: (data: { content?: string; contract_type?: string }) =>
      updateContractDraft(processId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['onboarding', 'contract', processId] });
      toast.success('Đã lưu hợp đồng');
    },
    onError: (err: Error) => toast.error(err.message || 'Lưu thất bại'),
  });

  const generateMutation = useMutation({
    mutationFn: () => generateContractDraft(processId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['onboarding', 'contract', processId] });
      toast.success('Đã tạo nội dung AI (placeholder)');
    },
    onError: (err: Error) => toast.error(err.message || 'Tạo thất bại'),
  });

  const statusMutation = useMutation({
    mutationFn: (status: OnboardingContractDraft['status']) => updateContractStatus(processId, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['onboarding', 'contract', processId] });
      toast.success('Đã cập nhật trạng thái');
    },
    onError: (err: Error) => toast.error(err.message || 'Cập nhật thất bại'),
  });

  const handleSave = () => {
    saveMutation.mutate({ content: localContent, contract_type: localType });
  };

  const handleAdvance = () => {
    if (draft) {
      const next = STATUS_CONFIG[draft.status]?.next as OnboardingContractDraft['status'] | null;
      if (next) {
        statusMutation.mutate(next);
      }
    }
  };

  const handleExport = () => {
    exportContractDraft(processId).then((text) => {
      const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `contract-${processId}.txt`;
      a.click();
      URL.revokeObjectURL(url);
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground gap-2">
        <FileText className="h-10 w-10 opacity-30" />
        <p className="text-sm">Không thể tải hợp đồng</p>
        <button onClick={() => refetch()} className="text-xs text-primary hover:underline">Thử lại</button>
      </div>
    );
  }

  if (!draft) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
        <FileText className="h-10 w-10 mb-3 opacity-30" />
        <p className="text-sm">Chưa có hợp đồng</p>
      </div>
    );
  }

  const currentConfig = STATUS_CONFIG[draft.status] || STATUS_CONFIG.draft;
  const StatusIcon = currentConfig.icon;
  return (
    <div className="space-y-4">
      {/* Status header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <StatusIcon className="size-4" />
          <span className="text-sm font-medium">{currentConfig.label}</span>
          <span className="text-xs text-muted-foreground">v{draft.revision}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Editor */}
        <div className="lg:col-span-2">
      <DraftEditor
            content={localContent}
            contractType={localType}
            isLocked={isComplete || (draft.status !== 'draft' && draft.status !== 'ready')}
            onContentChange={(v) => { setLocalContent(v); }}
            onTypeChange={(v) => { setLocalType(v); }}
            onGenerate={() => generateMutation.mutate()}
            onSave={handleSave}
            onExport={handleExport}
            isSaving={saveMutation.isPending}
            isGenerating={generateMutation.isPending}
          />
        </div>

        {/* Status panel sidebar */}
        <div>
          <StatusTracker
            currentStatus={draft.status}
            onAdvance={handleAdvance}
            isPending={statusMutation.isPending}
          />
        </div>
      </div>
    </div>
  );
}
