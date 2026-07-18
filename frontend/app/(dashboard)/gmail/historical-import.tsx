'use client';

import React, { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { History, Loader2, Tag, Play, Ban, Clock } from 'lucide-react';
import * as gmailApi from '@/lib/api/gmail';
import { useToast } from './toast';
import { fmtDate, apiErrorText } from './helpers';

// ---------------------------------------------------------------------------
// Historical import panel
// ---------------------------------------------------------------------------
export function HistoricalImportPanel() {
  const { push } = useToast();
  const qc = useQueryClient();
  const [days, setDays] = useState(7);
  const previewMut = useMutation({ mutationFn: (d: number) => gmailApi.previewImport(d) });
  const startMut = useMutation({
    mutationFn: (d: number) => gmailApi.startImport(d),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['gmail-import-status'] }); push({ kind: 'success', text: 'Đã bắt đầu import.' }); },
    onError: (e) => push({ kind: 'error', text: `Bắt đầu import thất bại: ${apiErrorText(e)}` }),
  });
  const status = useQuery({ queryKey: ['gmail-import-status'], queryFn: gmailApi.getImportStatus, staleTime: 15_000 });
  const cancelMut = useMutation({
    mutationFn: () => gmailApi.cancelImport(),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['gmail-import-status'] }); push({ kind: 'info', text: 'Đã hủy import.' }); },
    onError: (e) => push({ kind: 'error', text: `Hủy thất bại: ${apiErrorText(e)}` }),
  });

  const running = status.data?.status === 'running' || status.data?.status === 'pending';

  // Poll while running.
  useEffect(() => {
    if (!running) return;
    const t = setInterval(() => qc.invalidateQueries({ queryKey: ['gmail-import-status'] }), 4000);
    return () => clearInterval(t);
  }, [running, qc]);

  return (
    <div className="p-4 bg-white rounded-2xl border border-slate-200 shadow-sm">
      <div className="flex items-center gap-2 mb-3">
        <History className="w-4 h-4 text-indigo-600" />
        <h2 className="font-bold text-sm text-slate-900">Import email lịch sử</h2>
      </div>
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="text-slate-500">Cửa sổ:</span>
        {[7, 30].map((d) => (
          <button
            key={d}
            onClick={() => setDays(d)}
            disabled={running || startMut.isPending}
            className={`px-2.5 py-1.5 rounded-lg border text-xs font-medium ${days === d ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'}`}
          >
            {d} ngày
          </button>
        ))}
        <button
          onClick={() => previewMut.mutate(days)}
          disabled={running || previewMut.isPending}
          className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-50"
        >
          {previewMut.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Tag className="w-3.5 h-3.5" />} Xem trước
        </button>
        <button
          onClick={() => startMut.mutate(days)}
          disabled={running || startMut.isPending}
          className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {startMut.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />} Bắt đầu
        </button>
        {running && (
          <button
            onClick={() => cancelMut.mutate()}
            disabled={cancelMut.isPending}
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-rose-50 text-rose-600 border border-rose-200 hover:bg-rose-100 disabled:opacity-50"
          >
            {cancelMut.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Ban className="w-3.5 h-3.5" />} Hủy
          </button>
        )}
      </div>

      {previewMut.data && (
        <div className="mt-3 p-3 bg-slate-50 rounded-lg border border-slate-100 text-xs text-slate-600">
          Ước lượng <b className="text-slate-900">{previewMut.data.estimated_count}</b> email (đã import {previewMut.data.already_imported_count}) trong {days} ngày.
        </div>
      )}

      {status.data && (
        <div className="mt-3 p-3 bg-slate-50 rounded-lg border border-slate-100 text-xs text-slate-600 space-y-1">
          <div className="flex items-center gap-2">
            <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${running ? 'bg-amber-50 text-amber-700' : 'bg-slate-100 text-slate-500'}`}>{status.data.status}</span>
            {status.data.days != null && <span className="text-slate-400">· {status.data.days} ngày · {status.data.processed_count}/{status.data.total_count}</span>}
          </div>
          <div className="flex items-center gap-3 text-slate-400">
            <span>Job application: <b className="text-slate-600">{status.data.job_application_count}</b></span>
            <span>Lỗi: <b className="text-slate-600">{status.data.errors}</b></span>
            {status.data.started_at && <span className="inline-flex items-center gap-1"><Clock className="w-3 h-3" />{fmtDate(status.data.started_at)}</span>}
          </div>
          {status.data.error_message && <p className="text-rose-500">{status.data.error_message}</p>}
        </div>
      )}
    </div>
  );
}
