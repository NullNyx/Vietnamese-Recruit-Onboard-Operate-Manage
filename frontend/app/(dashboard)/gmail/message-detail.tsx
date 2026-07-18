'use client';

import React from 'react';
import { ChevronLeft, Paperclip, Sparkles, Send, FileText, Loader2, Inbox } from 'lucide-react';
import type { EmailMessage } from '@/lib/api/types';
import { EmptyState } from './empty-state';
import { fmtDate } from './helpers';

// ---------------------------------------------------------------------------
// Message detail + attachments + CV actions
// ---------------------------------------------------------------------------
export function MessageDetail({
  selected,
  body,
  attachments,
  processAttachmentsMut,
  onBack,
  onReply,
}: {
  selected: EmailMessage | null;
  body: { isLoading: boolean; data?: { plain_text?: string; html?: string } | null };
  attachments: { isPending: boolean; data?: { attachments: Array<{ attachment_id: string; filename: string; size_bytes: number }> } | null; mutate: (id: string) => void; reset: () => void };
  processAttachmentsMut: { isPending: boolean; data?: { message?: string; processed_count: number } | null; mutate: (id: string) => void };
  onBack: () => void;
  onReply: (msg: EmailMessage) => void;
}) {
  if (!selected) {
    return (
      <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <EmptyState title="Chọn một email bên trái để xem nội dung chi tiết." hint="AI sẽ tự động phân loại email sau khi đồng bộ." icon={<Inbox className="w-6 h-6 text-slate-300" />} />
      </div>
    );
  }

  return (
    <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="flex flex-col h-full">
        <div className="px-4 py-3 border-b border-slate-100">
          <div className="flex items-center gap-2 mb-1">
            <button onClick={onBack} className="text-slate-400 hover:text-slate-600 lg:hidden"><ChevronLeft className="w-4 h-4" /></button>
            <h3 className="text-sm font-semibold text-slate-900 flex-1 truncate">{selected.subject || '(không tiêu đề)'}</h3>
            {selected.category && <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-600">{selected.category}</span>}
          </div>
          <p className="text-[11px] text-slate-500">Từ: {selected.sender_name} &lt;{selected.sender_email}&gt; · {fmtDate(selected.received_at)}</p>
        </div>
        <div className="p-4 text-sm text-slate-700 whitespace-pre-wrap max-h-[40vh] overflow-y-auto">
          {body.isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : body.data?.plain_text || body.data?.html ? (
            body.data.html ? (
              <div dangerouslySetInnerHTML={{ __html: body.data.html }} />
            ) : body.data.plain_text
          ) : '(không có nội dung)'}
        </div>
        <div className="px-4 py-3 border-t border-slate-100 flex flex-wrap items-center gap-2">
          <button
            onClick={() => attachments.mutate(selected.id)}
            disabled={attachments.isPending}
            className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50"
          >
            <Paperclip className="w-3.5 h-3.5" /> Lấy attachments
          </button>
          <button
            onClick={() => processAttachmentsMut.mutate(selected.id)}
            disabled={processAttachmentsMut.isPending}
            className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            <Sparkles className="w-3.5 h-3.5" /> Xử lý CV (parse)
          </button>
          <button
            onClick={() => onReply(selected)}
            className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 ml-auto"
          >
            <Send className="w-3.5 h-3.5" /> Trả lời
          </button>
        </div>
        {attachments.data && (
          <div className="px-4 pb-3 space-y-1">
            <p className="text-[10px] font-mono uppercase text-slate-400">Attachments ({attachments.data.attachments.length})</p>
            {attachments.data.attachments.map((a) => (
              <div key={a.attachment_id} className="text-xs text-slate-600 flex items-center gap-2">
                <FileText className="w-3.5 h-3.5 text-slate-400" />
                <span className="truncate">{a.filename}</span>
                <span className="text-[10px] text-slate-400">{(a.size_bytes / 1024).toFixed(1)}KB</span>
              </div>
            ))}
          </div>
        )}
        {processAttachmentsMut.data && (
          <div className="px-4 pb-3 text-xs text-emerald-600">{processAttachmentsMut.data.message || `Đã xử lý ${processAttachmentsMut.data.processed_count} CV`}</div>
        )}
      </div>
    </div>
  );
}
