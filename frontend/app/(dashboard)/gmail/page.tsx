'use client';

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Mail, Inbox, RefreshCw, Plug, Unplug, Calendar as CalendarIcon, Send, Paperclip,
  Sparkles, Loader2, ChevronLeft, ChevronRight, PenSquare, X, Check, AlertCircle,
  History, Play, Ban, FileText, Tag, Filter, Clock,
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import * as gmailApi from '@/lib/api/gmail';
import type { OutboundEmail, ImportStatusResponse } from '@/lib/api/gmail';
import type { EmailMessage, OrganizationGoogleConnectionResponse } from '@/lib/api/types';
import { ApiError } from '@/lib/api/types';
import { getErrorMessage } from '@/lib/api/error-codes';
import { useAuthGuard } from '@/lib/auth/session';

// ---------------------------------------------------------------------------
// Tiny inline toast (no external lib) — Vietnamese, AI Studio style.
// ---------------------------------------------------------------------------
type Toast = { id: number; kind: 'success' | 'error' | 'info'; text: string };
const ToastCtx = React.createContext<{ push: (t: Omit<Toast, 'id'>) => void }>({ push: () => {} });
function useToast() { return React.useContext(ToastCtx); }
let toastId = 0;

function ToastProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<Toast[]>([]);
  const push = useCallback((t: Omit<Toast, 'id'>) => {
    const id = ++toastId;
    setItems((prev) => [...prev, { ...t, id }]);
    setTimeout(() => setItems((prev) => prev.filter((x) => x.id !== id)), 5000);
  }, []);
  return (
    <ToastCtx.Provider value={{ push }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 space-y-2 w-80">
        <AnimatePresence>
          {items.map((t) => (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, x: 40 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 40 }}
              className={`px-3.5 py-2.5 rounded-xl border text-xs font-medium shadow-md flex items-start gap-2 ${
                t.kind === 'success'
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                  : t.kind === 'error'
                    ? 'bg-rose-50 border-rose-200 text-rose-700'
                    : 'bg-slate-50 border-slate-200 text-slate-700'
              }`}
            >
              {t.kind === 'success' ? <Check className="w-4 h-4 mt-0.5 shrink-0" /> : <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />}
              <span className="break-words">{t.text}</span>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastCtx.Provider>
  );
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function fmtDate(iso: string | null): string {
  if (!iso) return '—';
  try { return new Date(iso).toLocaleString('vi-VN'); } catch { return iso; }
}

function apiErrorText(err: unknown): string {
  if (err instanceof ApiError) return getErrorMessage(err.errorCode);
  if (err instanceof Error) return err.message;
  return 'Lỗi không xác định';
}

const NAVY = 'bg-slate-900';

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------
export default function GmailPage() {
  return (
    <ToastProvider>
      <GmailPageInner />
    </ToastProvider>
  );
}

function GmailPageInner() {
  useAuthGuard({ requireAuth: true, requireAdmin: true });
  const { push } = useToast();
  const qc = useQueryClient();

  // --- connection status ---
  const conn = useQuery<OrganizationGoogleConnectionResponse, Error>({
    queryKey: ['gmail-connection'],
    queryFn: gmailApi.getConnectionStatus,
    staleTime: 30_000,
  });

  const isConnected = conn.data?.status === 'connected';
  const needsReauth = conn.data?.status === 'reauthorization_required';

  // --- calendars ---
  const calendars = useQuery({
    queryKey: ['gmail-calendars', conn.data?.status],
    queryFn: gmailApi.getCalendars,
    enabled: isConnected,
    staleTime: 60_000,
  });

  const selectCalMut = useMutation({
    mutationFn: (id: string) => gmailApi.selectCalendar(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['gmail-calendars'] }); push({ kind: 'success', text: 'Đã chọn calendar phỏng vấn.' }); },
    onError: (e) => push({ kind: 'error', text: `Chọn calendar thất bại: ${apiErrorText(e)}` }),
  });

  // --- messages ---
  const [category, setCategory] = useState<string>('');
  const messages = useQuery({
    queryKey: ['gmail-messages', category],
    queryFn: () => gmailApi.listMessages(category || undefined),
    enabled: isConnected,
    staleTime: 30_000,
  });

  const categories = useMemo(() => {
    const set = new Set<string>();
    messages.data?.messages?.forEach((m) => { if (m.category) set.add(m.category); });
    return Array.from(set).sort();
  }, [messages.data]);

  // --- selected message detail + attachments ---
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selected = useMemo(
    () => messages.data?.messages?.find((m) => m.id === selectedId) ?? null,
    [messages.data, selectedId],
  );
  const body = useQuery({
    queryKey: ['gmail-body', selectedId],
    queryFn: () => gmailApi.getMessageBody(selectedId!),
    enabled: !!selectedId,
    staleTime: 60_000,
  });
  const attachments = useMutation({
    mutationFn: (id: string) => gmailApi.getAttachments(id),
    onError: (e) => push({ kind: 'error', text: `Lấy attachments thất bại: ${apiErrorText(e)}` }),
  });
  const processAttachmentsMut = useMutation({
    mutationFn: (id: string) => gmailApi.processAttachments(id),
    onSuccess: (r) => { push({ kind: 'success', text: r.message || `Đã xử lý ${r.processed_count} CV.` }); qc.invalidateQueries({ queryKey: ['gmail-messages'] }); },
    onError: (e) => push({ kind: 'error', text: `Xử lý CV thất bại: ${apiErrorText(e)}` }),
  });

  // --- connection actions ---
  const connectMut = useMutation({
    mutationFn: () => (needsReauth ? gmailApi.reconnectConnection() : gmailApi.getAuthorizeUrl()),
    onSuccess: (res) => { if (res.redirect_url) window.location.href = res.redirect_url; else qc.invalidateQueries({ queryKey: ['gmail-connection'] }); },
    onError: (e) => push({ kind: 'error', text: `Kết nối thất bại: ${apiErrorText(e)}` }),
  });
  const disconnectMut = useMutation({
    mutationFn: () => gmailApi.disconnectConnection(),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['gmail-connection'] }); push({ kind: 'info', text: 'Đã ngắt kết nối Gmail.' }); },
    onError: (e) => push({ kind: 'error', text: `Ngắt kết nối thất bại: ${apiErrorText(e)}` }),
  });

  // --- sync ---
  const syncMut = useMutation({
    mutationFn: () => gmailApi.syncEmails(),
    onSuccess: (r) => { push({ kind: 'success', text: `Đã đồng bộ ${r.synced_count} email.` }); qc.invalidateQueries({ queryKey: ['gmail-messages'] }); },
    onError: (e) => {
      if (e instanceof ApiError && e.errorCode === 'GMAIL_NOT_CONNECTED') {
        qc.invalidateQueries({ queryKey: ['gmail-connection'] });
      }
      push({ kind: 'error', text: apiErrorText(e) });
    },
  });

  // --- classify ---
  const [classifying, setClassifying] = useState(false);
  const [classifyProgress, setClassifyProgress] = useState<string | null>(null);
  const handleClassify = useCallback(async () => {
    setClassifying(true);
    setClassifyProgress('Đang phân loại...');
    let total = 0, remaining = 1, totalToClassify: number | null = null, cv = 0;
    try {
      while (remaining > 0) {
        const r = await gmailApi.classifyBatch(5);
        if (totalToClassify === null) totalToClassify = r.remaining + r.classified_count;
        total += r.classified_count;
        cv += r.cv_processed_count ?? 0;
        remaining = r.remaining;
        setClassifyProgress(`AI đang phân loại... (${total}/${totalToClassify})`);
        if (r.classified_count === 0) break;
      }
      setClassifyProgress(null);
      push({ kind: 'success', text: `AI đã phân loại ${total} email${cv > 0 ? `, xử lý ${cv} CV` : ''}.` });
      qc.invalidateQueries({ queryKey: ['gmail-messages'] });
    } catch (e) {
      setClassifyProgress(null);
      push({ kind: 'error', text: `Phân loại thất bại: ${apiErrorText(e)}` });
    } finally {
      setClassifying(false);
    }
  }, [push, qc]);

  // --- compose / outbound ---
  const [composeOpen, setComposeOpen] = useState(false);
  const [replyTo, setReplyTo] = useState<EmailMessage | null>(null);

  const outbound = useQuery({
    queryKey: ['gmail-outbound'],
    queryFn: gmailApi.listOutboundEmails,
    enabled: isConnected,
    staleTime: 15_000,
  });
  const createOutboundMut = useMutation({
    mutationFn: (data: { to: string[]; cc?: string[]; subject: string; body_text?: string; body_html?: string; reply_to_message_id?: string }) =>
      gmailApi.createOutboundEmail(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['gmail-outbound'] }); push({ kind: 'success', text: 'Đã tạo email nháp (pending). Xác nhận để gửi thật.' }); setComposeOpen(false); },
    onError: (e) => push({ kind: 'error', text: `Tạo nháp thất bại: ${apiErrorText(e)}` }),
  });
  const sendOutboundMut = useMutation({
    mutationFn: (id: string) => gmailApi.sendOutboundEmail(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['gmail-outbound'] }); push({ kind: 'success', text: 'Đã gửi email thật.' }); },
    onError: (e) => { qc.invalidateQueries({ queryKey: ['gmail-outbound'] }); push({ kind: 'error', text: `Gửi thất bại: ${apiErrorText(e)}` }); },
  });
  const deleteOutboundMut = useMutation({
    mutationFn: (id: string) => gmailApi.deleteOutboundEmail(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['gmail-outbound'] }),
    onError: (e) => push({ kind: 'error', text: `Xóa nháp thất bại: ${apiErrorText(e)}` }),
  });

  // --- GMAIL_NOT_CONNECTED banner ---
  const connError = conn.error instanceof ApiError ? conn.error : null;
  const showNotConnectedBanner = !isConnected || connError?.errorCode === 'GMAIL_NOT_CONNECTED';

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-indigo-600">
          <Mail className="w-5 h-5" />
          <h1 className="text-xl font-bold text-slate-900">Kênh Gmail</h1>
        </div>
        {isConnected && (
          <div className="flex items-center gap-2">
            <button
              onClick={handleClassify}
              disabled={classifying}
              className="inline-flex items-center gap-1.5 text-xs font-medium bg-white border border-slate-200 rounded-lg px-3 py-1.5 hover:bg-slate-50 disabled:opacity-50"
            >
              <Sparkles className="w-3.5 h-3.5" /> {classifying ? 'Đang phân loại...' : 'Phân loại AI'}
            </button>
            <button
              onClick={() => syncMut.mutate()}
              disabled={syncMut.isPending}
              className="inline-flex items-center gap-1.5 text-xs font-medium bg-indigo-600 text-white rounded-lg px-3 py-1.5 hover:bg-indigo-700 disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${syncMut.isPending ? 'animate-spin' : ''}`} /> Đồng bộ
            </button>
            <button
              onClick={() => { setReplyTo(null); setComposeOpen(true); }}
              className="inline-flex items-center gap-1.5 text-xs font-medium bg-white border border-slate-200 rounded-lg px-3 py-1.5 hover:bg-slate-50"
            >
              <PenSquare className="w-3.5 h-3.5" /> Soạn email
            </button>
          </div>
        )}
      </div>

      {/* Connection panel */}
      <ConnectionPanel
        status={conn.data?.status ?? null}
        email={conn.data?.email ?? null}
        loading={conn.isLoading}
        error={connError ? apiErrorText(conn.error) : conn.error ? 'Không thể kiểm tra trạng thái' : null}
        notConnectedCode={connError?.errorCode === 'GMAIL_NOT_CONNECTED' ? 'GMAIL_NOT_CONNECTED' : null}
        onConnect={() => connectMut.mutate()}
        onDisconnect={() => disconnectMut.mutate()}
        connectLoading={connectMut.isPending}
        disconnectLoading={disconnectMut.isPending}
      />

      {isConnected && (
        <>
          {/* Calendars + selected calendar (bắt buộc cho tạo Interview) */}
          <div className="p-4 bg-white rounded-2xl border border-slate-200 shadow-sm shadow-slate-100">
            <div className="flex items-center gap-2 mb-3">
              <CalendarIcon className="w-4 h-4 text-indigo-600" />
              <h2 className="font-bold text-sm text-slate-900">Calendar phỏng vấn (Organization)</h2>
              <span className="ml-auto text-[10px] text-slate-400 font-mono">bắt buộc chọn để tạo Interview</span>
            </div>
            {calendars.isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin text-slate-400" />
            ) : calendars.error ? (
              <p className="text-xs text-rose-500">Không tải được calendars: {apiErrorText(calendars.error)}</p>
            ) : (
              <div className="space-y-1.5">
                {calendars.data?.calendars?.length ? (
                  calendars.data.calendars.map((c) => {
                    const selected = calendars.data.selected_calendar_id === c.id;
                    return (
                      <label key={c.id} className="flex items-center gap-2 p-2 rounded-lg border border-slate-100 hover:bg-slate-50 cursor-pointer">
                        <input
                          type="radio"
                          name="calendar"
                          checked={selected}
                          disabled={selectCalMut.isPending}
                          onChange={() => selectCalMut.mutate(c.id)}
                          className="accent-indigo-600"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="text-xs font-medium text-slate-800 truncate">{c.summary}{c.primary && <span className="text-[10px] text-slate-400"> · primary</span>}</div>
                          <div className="text-[10px] text-slate-400 font-mono truncate">{c.id}</div>
                        </div>
                        {selected && <Check className="w-3.5 h-3.5 text-emerald-500" />}
                      </label>
                    );
                  })
                ) : (
                  <p className="text-xs text-slate-400">Không có calendar nào.</p>
                )}
              </div>
            )}
          </div>

          {/* Historical import */}
          <HistoricalImportPanel />

          {/* Classification progress overlay */}
          {classifying && classifyProgress && (
            <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-50/80">
              <div className="flex flex-col items-center gap-3 rounded-xl border border-slate-200 bg-white px-8 py-6 shadow-md">
                <Sparkles className="w-6 h-6 text-indigo-600 animate-pulse" />
                <p className="text-sm font-medium text-slate-800">AI đang phân loại email</p>
                <p className="text-xs text-slate-500">{classifyProgress}</p>
              </div>
            </div>
          )}

          {/* Messages + detail */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* List */}
            <div className="lg:col-span-1 bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="px-3 py-2 border-b border-slate-100 flex items-center gap-2">
                <Filter className="w-3.5 h-3.5 text-slate-400" />
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="text-xs bg-transparent border-none focus:outline-none text-slate-600"
                >
                  <option value="">Tất cả danh mục</option>
                  {categories.map((c) => (<option key={c} value={c}>{c}</option>))}
                </select>
                <button onClick={() => messages.refetch()} className="ml-auto p-1 rounded hover:bg-slate-100 text-slate-400">
                  <RefreshCw className={`w-3.5 h-3.5 ${messages.isFetching ? 'animate-spin' : ''}`} />
                </button>
              </div>
              <div className="max-h-[60vh] overflow-y-auto">
                {messages.isLoading ? (
                  <div className="p-6 text-center"><Loader2 className="w-5 h-5 animate-spin text-slate-300 mx-auto" /></div>
                ) : messages.error ? (
                  <div className="p-4 text-xs text-rose-500">Lỗi: {apiErrorText(messages.error)}</div>
                ) : (messages.data?.messages?.length ?? 0) === 0 ? (
                  <EmptyState
                    title={category ? 'Không có email khớp bộ lọc' : 'Chưa có email nào'}
                    hint={category ? 'Không có email nào khớp với bộ lọc hiện tại — hãy thử đổi danh mục hoặc đồng bộ lại.' : 'Nhấn Đồng bộ để tải email từ Gmail về.'}
                  />
                ) : (
                  messages.data!.messages.map((m) => (
                    <button
                      key={m.id}
                      onClick={() => { setSelectedId(m.id); attachments.reset(); }}
                      className={`w-full text-left px-3 py-2.5 border-b border-slate-50 hover:bg-slate-50 transition-colors ${selectedId === m.id ? 'bg-indigo-50' : ''}`}
                    >
                      <div className="flex items-center gap-2">
                        {m.category && <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-600">{m.category}</span>}
                        {m.has_attachments && <Paperclip className="w-3 h-3 text-slate-400" />}
                        <span className="text-xs font-medium text-slate-700 truncate flex-1">{m.subject || '(không tiêu đề)'}</span>
                      </div>
                      <div className="text-[10px] text-slate-400 truncate mt-0.5">{m.sender_email}</div>
                    </button>
                  ))
                )}
              </div>
            </div>

            {/* Detail */}
            <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
              {selected ? (
                <div className="flex flex-col h-full">
                  <div className="px-4 py-3 border-b border-slate-100">
                    <div className="flex items-center gap-2 mb-1">
                      <button onClick={() => setSelectedId(null)} className="text-slate-400 hover:text-slate-600 lg:hidden"><ChevronLeft className="w-4 h-4" /></button>
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
                      className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-50"
                    >
                      {attachments.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Paperclip className="w-3.5 h-3.5" />} Lấy attachments
                    </button>
                    <button
                      onClick={() => processAttachmentsMut.mutate(selected.id)}
                      disabled={processAttachmentsMut.isPending}
                      className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
                    >
                      <Sparkles className="w-3.5 h-3.5" /> Xử lý CV (parse)
                    </button>
                    <button
                      onClick={() => { setReplyTo(selected); setComposeOpen(true); }}
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
              ) : (
                <EmptyState title="Chọn một email bên trái để xem nội dung chi tiết." hint="AI sẽ tự động phân loại email sau khi đồng bộ." icon={<Inbox className="w-6 h-6 text-slate-300" />} />
              )}
            </div>
          </div>

          {/* Outbound emails (pending -> sending -> sent/failed) */}
          <OutboundSection
            items={outbound.data?.items ?? []}
            loading={outbound.isLoading}
            onSend={(id) => sendOutboundMut.mutate(id)}
            onDelete={(id) => deleteOutboundMut.mutate(id)}
            sending={sendOutboundMut.isPending}
          />
        </>
      )}

      {/* Compose dialog */}
      <ComposeDialog
        open={composeOpen}
        onClose={() => setComposeOpen(false)}
        replyTo={replyTo}
        replyBodyText={body.data?.plain_text ?? null}
        onSend={(d) => createOutboundMut.mutate(d)}
        sending={createOutboundMut.isPending}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Connection panel
// ---------------------------------------------------------------------------
function ConnectionPanel({
  status, email, loading, error, notConnectedCode, onConnect, onDisconnect, connectLoading, disconnectLoading,
}: {
  status: string | null;
  email: string | null;
  loading: boolean;
  error: string | null;
  notConnectedCode: string | null;
  onConnect: () => void;
  onDisconnect: () => void;
  connectLoading: boolean;
  disconnectLoading: boolean;
}) {
  const connected = status === 'connected';
  return (
    <div className="p-4 bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center gap-3">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${connected ? 'bg-emerald-50' : 'bg-slate-100'}`}>
        {connected ? <Plug className="w-5 h-5 text-emerald-600" /> : <Unplug className="w-5 h-5 text-slate-400" />}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-bold text-slate-900">Organization Google Connection</h2>
          <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-semibold border ${
            connected ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
              : status === 'reauthorization_required' ? 'bg-amber-50 text-amber-700 border-amber-200'
              : 'bg-slate-50 text-slate-500 border-slate-200'
          }`}>
            {connected ? 'Đã kết nối' : status === 'reauthorization_required' ? 'Cần cấp lại quyền' : 'Chưa kết nối'}
          </span>
        </div>
        {connected && email && <p className="text-xs text-slate-500 mt-0.5 truncate">{email}</p>}
        {notConnectedCode && (
          <p className="text-[11px] text-rose-600 mt-0.5 font-mono">{notConnectedCode}: {getErrorMessage(notConnectedCode)}</p>
        )}
        {error && !notConnectedCode && <p className="text-[11px] text-rose-600 mt-0.5">{error}</p>}
        {loading && !status && <p className="text-[11px] text-slate-400 mt-0.5">Đang kiểm tra trạng thái...</p>}
      </div>
      {!connected && (
        <button
          onClick={onConnect}
          disabled={connectLoading || loading}
          className="inline-flex items-center gap-1.5 text-xs font-medium bg-indigo-600 text-white rounded-lg px-3 py-2 hover:bg-indigo-700 disabled:opacity-50"
        >
          {connectLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plug className="w-3.5 h-3.5" />}
          {status === 'reauthorization_required' ? 'Cấp lại quyền' : 'Kết nối Gmail'}
        </button>
      )}
      {connected && (
        <button
          onClick={() => { if (confirm('Ngắt kết nối Gmail của Organization?')) onDisconnect(); }}
          disabled={disconnectLoading}
          className="inline-flex items-center gap-1.5 text-xs font-medium bg-white border border-slate-200 text-slate-600 rounded-lg px-3 py-2 hover:bg-slate-50 disabled:opacity-50"
        >
          {disconnectLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Unplug className="w-3.5 h-3.5" />}
          Ngắt kết nối
        </button>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Historical import panel
// ---------------------------------------------------------------------------
function HistoricalImportPanel() {
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

// ---------------------------------------------------------------------------
// Outbound emails section
// ---------------------------------------------------------------------------
function OutboundSection({
  items, loading, onSend, onDelete, sending,
}: {
  items: OutboundEmail[];
  loading: boolean;
  onSend: (id: string) => void;
  onDelete: (id: string) => void;
  sending: boolean;
}) {
  const statusBadge = (s: string) => {
    const map: Record<string, string> = {
      pending: 'bg-amber-50 text-amber-700 border-amber-200',
      sending: 'bg-indigo-50 text-indigo-700 border-indigo-200',
      sent: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      failed: 'bg-rose-50 text-rose-700 border-rose-200',
    };
    return map[s] ?? 'bg-slate-50 text-slate-600 border-slate-200';
  };
  return (
    <div className="p-4 bg-white rounded-2xl border border-slate-200 shadow-sm">
      <div className="flex items-center gap-2 mb-3">
        <Send className="w-4 h-4 text-indigo-600" />
        <h2 className="font-bold text-sm text-slate-900">Email đang gửi (Outbound)</h2>
        <span className="text-[10px] text-slate-400 ml-auto">vòng đời pending → sending → sent/failed · gửi thật sau HR xác nhận</span>
      </div>
      {loading ? (
        <Loader2 className="w-4 h-4 animate-spin text-slate-300" />
      ) : items.length === 0 ? (
        <EmptyState title="Chưa có email nào đang chờ gửi." hint="Nhấn Soạn email để tạo thư nháp mới." />
      ) : (
        <div className="space-y-2">
          {items.map((m) => (
            <div key={m.id} className="p-3 bg-slate-50 rounded-lg border border-slate-100 flex items-start gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-xs font-semibold text-slate-800 truncate">{m.subject || '(không tiêu đề)'}</span>
                  <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded-full border ${statusBadge(m.status)}`}>{m.status}</span>
                </div>
                <p className="text-[11px] text-slate-500 truncate">To: {m.to.join(', ')}</p>
                {m.error_message && <p className="text-[11px] text-rose-500 truncate mt-0.5">Lỗi: {m.error_message}</p>}
                <p className="text-[10px] text-slate-400 mt-0.5">Tạo: {fmtDate(m.created_at)}{m.sent_at ? ` · Gửi: ${fmtDate(m.sent_at)}` : ''}</p>
              </div>
              {m.status === 'pending' && (
                <div className="flex items-center gap-1.5 shrink-0">
                  <button
                    onClick={() => { if (confirm('Gửi email này thật? Hành động ghi dữ liệu thật.')) onSend(m.id); }}
                    disabled={sending}
                    className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
                  >
                    {sending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />} Gửi thật
                  </button>
                  <button onClick={() => onDelete(m.id)} className="p-1.5 rounded-lg text-slate-400 hover:bg-rose-50 hover:text-rose-500"><X className="w-3.5 h-3.5" /></button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Compose dialog (creates pending outbound draft; HR confirms to actually send)
// ---------------------------------------------------------------------------
function ComposeDialog({
  open, onClose, replyTo, replyBodyText, onSend, sending,
}: {
  open: boolean;
  onClose: () => void;
  replyTo: EmailMessage | null;
  replyBodyText?: string | null;
  onSend: (data: { to: string[]; cc?: string[]; subject: string; body_text?: string; body_html?: string; reply_to_message_id?: string }) => void;
  sending: boolean;
}) {
  const [to, setTo] = useState('');
  const [cc, setCc] = useState('');
  const [subject, setSubject] = useState('');
  const [bodyText, setBodyText] = useState('');

  useEffect(() => {
    if (open) {
      setTo(replyTo ? replyTo.sender_email : '');
      setCc('');
      setSubject(replyTo ? `Re: ${replyTo.subject || ''}` : '');
      if (replyTo) {
        const date = replyTo.received_at ? new Date(replyTo.received_at).toLocaleString('vi-VN') : '';
        const header = `Vào ${date}, ${replyTo.sender_name || replyTo.sender_email} đã viết:\n`;
        const sourceText = replyBodyText || replyTo.snippet || '';
        const quoted = sourceText
          .split('\n')
          .map((line) => `> ${line}`)
          .join('\n');
        setBodyText(header + quoted + '\n\n');
      } else {
        setBodyText('');
      }
    }
  }, [open, replyTo, replyBodyText]);

  if (!open) return null;
  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const toArr = to.split(',').map((s) => s.trim()).filter(Boolean);
    if (toArr.length === 0 || !subject.trim()) return;
    onSend({
      to: toArr,
      cc: cc ? cc.split(',').map((s) => s.trim()).filter(Boolean) : undefined,
      subject: subject.trim(),
      body_text: bodyText,
      reply_to_message_id: replyTo?.gmail_message_id,
    });
  };
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
      <motion.form
        onSubmit={submit}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-lg bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden"
      >
        <div className="px-4 py-3 bg-slate-900 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white">Soạn email (tạo nháp pending)</h3>
          <button type="button" onClick={onClose} className="text-slate-300 hover:text-white"><X className="w-4 h-4" /></button>
        </div>
        <div className="p-4 space-y-3">
          <Field label="To">
            <input value={to} onChange={(e) => setTo(e.target.value)} required className="w-full text-xs border border-slate-200 rounded-lg px-2.5 py-2 focus:outline-none focus:border-indigo-500" placeholder="a@x.com, b@y.com" />
          </Field>
          <Field label="Cc">
            <input value={cc} onChange={(e) => setCc(e.target.value)} className="w-full text-xs border border-slate-200 rounded-lg px-2.5 py-2 focus:outline-none focus:border-indigo-500" placeholder="tùy chọn" />
          </Field>
          <Field label="Tiêu đề">
            <input value={subject} onChange={(e) => setSubject(e.target.value)} required className="w-full text-xs border border-slate-200 rounded-lg px-2.5 py-2 focus:outline-none focus:border-indigo-500" />
          </Field>
          <Field label="Nội dung">
            <textarea value={bodyText} onChange={(e) => setBodyText(e.target.value)} rows={6} className="w-full text-xs border border-slate-200 rounded-lg px-2.5 py-2 focus:outline-none focus:border-indigo-500 resize-none" />
          </Field>
          <p className="text-[10px] text-slate-400">Email được tạo ở trạng thái <b>pending</b>. Bạn cần bấm <b>Gửi thật</b> ở danh sách outbound để gửi (human-in-the-loop).</p>
        </div>
        <div className="px-4 py-3 bg-slate-50 border-t border-slate-100 flex items-center justify-end gap-2">
          <button type="button" onClick={onClose} className="text-xs px-3 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-white">Hủy</button>
          <button type="submit" disabled={sending} className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50">
            {sending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <PenSquare className="w-3.5 h-3.5" />} Tạo nháp
          </button>
        </div>
      </motion.form>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="text-[10px] font-mono uppercase text-slate-400">{label}</span>
      <div className="mt-1">{children}</div>
    </label>
  );
}

// ---------------------------------------------------------------------------
// Empty state
// ---------------------------------------------------------------------------
function EmptyState({ title, hint, icon }: { title: string; hint?: string; icon?: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-10 px-4">
      <div className="w-12 h-12 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-center mb-2">
        {icon ?? <Inbox className="w-6 h-6 text-slate-300" />}
      </div>
      <p className="text-sm font-medium text-slate-700">{title}</p>
      {hint && <p className="text-xs text-slate-400 mt-1 max-w-xs">{hint}</p>}
    </div>
  );
}