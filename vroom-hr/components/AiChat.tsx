'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  Sparkles, Send, Bot, User, Check, AlertCircle, RefreshCw,
  ChevronDown, ChevronUp, Loader2, ThumbsUp, ThumbsDown, X, FileEdit,
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import type {
  ChatMessage, DraftAction, ChatResponse, AssistantFeedbackRequest, SessionStartResponse,
} from '@/lib/api/assistant';

// ---------------------------------------------------------------------------
// Props — API functions are injected so this one panel serves HR + ESS.
// HR page injects lib/api/assistant; ESS page injects lib/api/employee-assistant.
// The LLM never writes — confirm calls the real write endpoint directly.
// ---------------------------------------------------------------------------

export interface AiChatApi {
  sendMessage: (messages: ChatMessage[], sessionId?: string) => Promise<ChatResponse>;
  confirmAction: (draft: DraftAction) => Promise<unknown>;
  startSession: (assistantType: 'hr' | 'employee') => Promise<SessionStartResponse>;
  endSession: (sessionId: string) => Promise<void>;
  sendFeedback?: (feedback: AssistantFeedbackRequest) => Promise<void>;
  /** Record the human decision (confirm/reject) for audit — HR assistant only. */
  recordDecision?: (draft: DraftAction, decision: 'confirm' | 'reject') => Promise<void>;
}

export interface AiChatProps {
  assistantType: 'hr' | 'employee';
  api: AiChatApi;
  title?: string;
  description?: string;
  suggestions?: string[];
  /** For ESS: open the request form prefilled from a draft (leave/overtime). */
  onOpenRequestDialog?: (values: {
    leave?: Record<string, string>;
    overtime?: Record<string, string>;
  }) => void | Promise<void>;
  /** Start collapsed (panel mode) — default expanded. */
  defaultOpen?: boolean;
  className?: string;
}

let idCounter = 0;
function uid(prefix: string): string {
  idCounter += 1;
  return `${prefix}-${Date.now()}-${idCounter}`;
}

function nowTime(): string {
  return new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
}

// ---------------------------------------------------------------------------
// Draft Action card — human-in-the-loop. Confirm fires the real write endpoint.
// ---------------------------------------------------------------------------

const ACTION_LABELS: Record<string, string> = {
  draft_interview_invitation: 'Thư mời phỏng vấn',
  draft_congratulations_email: 'Email chúc mừng (Offer)',
  submit_leave_request: 'Đơn nghỉ phép',
  submit_overtime_request: 'Đơn tăng ca',
};

function friendlyParams(draft: DraftAction): { label: string; value: string }[] {
  const p = draft.parameters ?? {};
  const out: { label: string; value: string }[] = [];
  const push = (label: string, value: unknown) => {
    if (value === undefined || value === null || value === '') return;
    out.push({ label, value: String(value) });
  };
  push('Ứng viên', p.candidate_name ?? p.candidateName);
  push('Vị trí', p.job_title ?? p.jobTitle);
  push('Thời gian', (p.date_time ?? p.dateTime)?.toString()?.replace('T', ' '));
  push('Nhân viên', p.employee_name ?? p.employeeName);
  push('Từ ngày', p.start_date ?? p.startDate);
  push('Đến ngày', p.end_date ?? p.endDate);
  push('Ngày làm thêm', p.work_date ?? p.workDate);
  push('Lý do', p.reason);
  push('Dự án/Công việc', p.project_or_task ?? p.projectOrTask);
  return out;
}

function DraftActionCard({
  draft,
  onConfirm,
  onReject,
  onOpenRequest,
}: {
  draft: DraftAction;
  onConfirm: () => void;
  onReject: () => void;
  onOpenRequest?: () => void;
}) {
  const [state, setState] = useState<'idle' | 'pending' | 'done' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);

  const handleConfirm = async () => {
    setState('pending');
    setError(null);
    try {
      await onConfirm();
      setState('done');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Lỗi không xác định');
      setState('error');
    }
  };

  const handleReject = async () => {
    setState('pending');
    try {
      await onReject();
      setState('idle');
    } catch {
      setState('idle');
    }
  };

  if (state === 'done') {
    return (
      <div className="flex items-center gap-2 px-3 py-2.5 bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs rounded-xl font-medium">
        <Check className="w-3.5 h-3.5" />
        Đã xác nhận và ghi thành công.
      </div>
    );
  }

  const label = ACTION_LABELS[draft.action_type] ?? `Draft Action — ${draft.action_type}`;
  const params = friendlyParams(draft);

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-3.5 bg-white rounded-xl border border-dashed border-indigo-300/80 space-y-2.5 shadow-sm"
    >
      <div className="flex items-center justify-between border-b border-slate-100 pb-2">
        <span className="inline-flex items-center gap-1.5 text-[10px] font-mono text-indigo-600 uppercase tracking-wider font-semibold">
          <FileEdit className="w-3 h-3" />
          Đề xuất từ trợ lý AI
        </span>
        <span className="text-[10px] px-2 py-0.5 rounded-full font-sans font-semibold border bg-amber-50 text-amber-700 border-amber-100">
          {label}
        </span>
      </div>

      {params.length > 0 && (
        <div className="text-xs space-y-1 text-slate-700">
          {params.map((row) => (
            <div key={row.label} className="flex gap-1.5">
              <span className="text-slate-500 shrink-0">{row.label}:</span>
              <span className="text-slate-900 font-semibold break-words">{row.value}</span>
            </div>
          ))}
        </div>
      )}

      {draft.preview && (
        <div className="text-[11px] text-slate-600 max-h-32 overflow-y-auto p-2 bg-slate-50 rounded border border-slate-200 whitespace-pre-wrap leading-relaxed">
          {draft.preview}
        </div>
      )}

      {draft.provenance && Object.keys(draft.provenance).length > 0 && (
        <details className="text-[10px] text-slate-400">
          <summary className="cursor-pointer hover:text-slate-600">Nguồn dữ liệu (provenance)</summary>
          <pre className="mt-1 p-1.5 bg-slate-50 rounded overflow-x-auto font-mono text-[9px]">
            {JSON.stringify(draft.provenance, null, 2)}
          </pre>
        </details>
      )}

      {error && (
        <div className="text-[11px] text-rose-600 bg-rose-50 border border-rose-100 p-1.5 rounded flex items-start gap-1">
          <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
          <span className="break-words">{error}</span>
        </div>
      )}

      <div className="flex gap-2 pt-1">
        <button
          type="button"
          onClick={handleConfirm}
          disabled={state === 'pending'}
          className="flex-1 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-bold text-xs rounded-lg transition-all shadow-md shadow-indigo-100 flex items-center justify-center gap-1.5"
        >
          {state === 'pending' ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Check className="w-3.5 h-3.5 stroke-[3]" />
          )}
          {onOpenRequest ? 'Mở form' : 'Xác nhận & Ghi dữ liệu'}
        </button>
        <button
          type="button"
          onClick={handleReject}
          disabled={state === 'pending'}
          className="px-3 py-2 bg-white hover:bg-slate-50 border border-slate-200 text-slate-600 font-medium text-xs rounded-lg transition-all flex items-center gap-1"
        >
          <X className="w-3.5 h-3.5" />
          Hủy
        </button>
      </div>
    </motion.div>
  );
}

// ---------------------------------------------------------------------------
// Feedback row (thumbs up/down) for an assistant message.
// ---------------------------------------------------------------------------

function FeedbackRow({
  messageIndex,
  sessionId,
  sendFeedback,
}: {
  messageIndex: number;
  sessionId?: string;
  sendFeedback?: AiChatApi['sendFeedback'];
}) {
  const [sent, setSent] = useState<'up' | 'down' | null>(null);
  if (!sendFeedback || !sessionId) return null;
  const submit = (type: 'up' | 'down') => {
    setSent(type);
    sendFeedback({ session_id: sessionId, message_index: messageIndex, feedback_type: type }).catch(() => {});
  };
  return (
    <div className="flex items-center gap-1 mt-1">
      <button
        type="button"
        onClick={() => submit('up')}
        className={`p-1 rounded-md hover:bg-indigo-50 transition-colors ${sent === 'up' ? 'text-indigo-600' : 'text-slate-300'}`}
        aria-label="Hữu ích"
      >
        <ThumbsUp className="w-3.5 h-3.5" />
      </button>
      <button
        type="button"
        onClick={() => submit('down')}
        className={`p-1 rounded-md hover:bg-rose-50 transition-colors ${sent === 'down' ? 'text-rose-500' : 'text-slate-300'}`}
        aria-label="Không hữu ích"
      >
        <ThumbsDown className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main AiChat panel
// ---------------------------------------------------------------------------

export default function AiChat({
  assistantType,
  api,
  title,
  description,
  suggestions,
  onOpenRequestDialog,
  defaultOpen = true,
  className,
}: AiChatProps) {
  const welcome: ChatMessage = {
    role: 'assistant',
    content:
      assistantType === 'hr'
        ? 'Xin chào HR! Tôi là Trợ lý AI Vroom HR. Tôi có thể đọc dữ liệu ứng viên, lịch phỏng vấn, onboarding và soạn nháp email mời phỏng vấn / chúc mừng. Mọi ghi dữ liệu đều do bạn xác nhận.'
        : 'Chào bạn! Tôi là Trợ lý nhân viên. Tôi có thể kiểm tra chấm công, số dư phép và soạn nháp yêu cầu nghỉ phép / tăng ca của bạn. Bạn cần tự xác nhận mọi yêu cầu.',
    tool_call_id: undefined,
    tool_calls: undefined,
    name: undefined,
  };

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [draftAction, setDraftAction] = useState<DraftAction | null>(null);
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const sessionIdRef = useRef<string | null>(null);
  const mountedRef = useRef(true);
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const titleText =
    title ?? (assistantType === 'hr' ? 'Trợ lý AI Vroom HR' : 'Trợ lý Nhân viên (ESS)');
  const descText =
    description ??
    (assistantType === 'hr'
      ? 'Hỏi về dữ liệu tuyển dụng / onboarding; soạn nháp action cho HR xác nhận.'
      : 'Hỏi về chấm công, phép; soạn nháp yêu cầu của bạn.');
  const chipSuggestions =
    suggestions ??
    (assistantType === 'hr'
      ? ['Có bao nhiêu candidate đang reviewing?', 'Onboarding nào đang chạy?', 'Soạn email chúc mừng cho Nguyễn Văn A']
      : ['Số dư phép của tôi?', 'Soạn đơn nghỉ phép 2 ngày', 'Lịch chấm công tuần này']);

  // Session lifecycle
  useEffect(() => {
    mountedRef.current = true;
    api
      .startSession(assistantType)
      .then((res) => {
        if (mountedRef.current) sessionIdRef.current = res.session_id;
      })
      .catch((err) => {
        console.warn('Failed to start assistant session:', err);
      });
    return () => {
      mountedRef.current = false;
      const sid = sessionIdRef.current;
      if (sid) {
        api.endSession(sid).catch((err) => console.warn('Failed to end session:', err));
      }
    };
  }, [api, assistantType]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const handleSend = useCallback(
    async (retryText?: string) => {
      const text = (retryText ?? input).trim();
      if (!text || loading) return;
      const userMessage: ChatMessage = { role: 'user', content: text };
      const history = [...messages, userMessage];
      setMessages(history);
      setInput('');
      setError(null);
      setDraftAction(null);
      setLoading(true);
      try {
        const res: ChatResponse = await api.sendMessage(history, sessionIdRef.current ?? undefined);
        const display = res.messages.filter(
          (m) => !(m.role === 'assistant' && m.content === null && m.tool_calls),
        );
        setMessages([...history, ...display]);
        if (res.draft_action) setDraftAction(res.draft_action);
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Không thể kết nối trợ lý';
        setError(msg);
        setInput(text);
      } finally {
        setLoading(false);
      }
    },
    [api, input, loading, messages],
  );

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleDraftConfirm = useCallback(async () => {
    if (!draftAction) return;
    if (onOpenRequestDialog && (draftAction.action_type === 'submit_leave_request' || draftAction.action_type === 'submit_overtime_request')) {
      const b = draftAction.confirm_body as Record<string, unknown>;
      const values: { leave?: Record<string, string>; overtime?: Record<string, string> } = {};
      if (draftAction.action_type === 'submit_leave_request') {
        values.leave = {
          leave_type: String(b.leave_type ?? ''),
          start_date: String(b.start_date ?? ''),
          end_date: String(b.end_date ?? ''),
          reason: String(b.reason ?? ''),
        };
      } else {
        values.overtime = {
          work_date: String(b.work_date ?? ''),
          start_time: String(b.start_time ?? ''),
          end_time: String(b.end_time ?? ''),
          reason: String(b.reason ?? ''),
          project_or_task: String(b.project_or_task ?? ''),
        };
      }
      await Promise.resolve(onOpenRequestDialog(values));
      setDraftAction(null);
      return;
    }
    await api.confirmAction(draftAction);
    await api.recordDecision?.(draftAction, 'confirm');
    setDraftAction(null);
  }, [api, draftAction, onOpenRequestDialog]);

  const handleDraftReject = useCallback(async () => {
    if (!draftAction) return;
    try {
      await api.recordDecision?.(draftAction, 'reject');
    } catch {
      // ignore — reject is best-effort audit
    }
    setDraftAction(null);
  }, [api, draftAction]);

  const displayMessages = messages.length === 0 ? [welcome] : messages;

  return (
    <div
      id="ai-assistant-chat-panel"
      className={`flex flex-col bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-md shadow-slate-100 transition-all duration-300 ${className ?? 'h-full'}`}
    >
      {/* Header */}
      <div
        onClick={() => setIsOpen((o) => !o)}
        className="flex items-center justify-between px-4 py-3.5 bg-slate-900 border-b border-slate-950 cursor-pointer select-none"
      >
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-indigo-400 animate-pulse" />
          <h3 className="font-sans font-semibold text-sm text-white flex items-center gap-1.5">
            {titleText}
            <span className="text-[10px] bg-indigo-500/25 text-indigo-200 px-1.5 py-0.5 rounded-full font-mono">
              Human-in-the-loop
            </span>
          </h3>
        </div>
        <button className="text-slate-300 hover:text-white transition-all">
          {isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
        </button>
      </div>

      {isOpen && (
        <>
          {/* Chat Body */}
          <div ref={scrollRef} className="flex-1 p-4 overflow-y-auto space-y-4 h-[350px] md:h-[450px]">
            {messages.length === 0 && (
              <div className="flex flex-col items-center text-center py-8">
                <div className="w-12 h-12 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center mb-3">
                  <Bot className="w-6 h-6 text-indigo-600" />
                </div>
                <p className="text-sm text-slate-700 font-medium mb-1">{titleText}</p>
                <p className="text-xs text-slate-500 max-w-sm leading-relaxed mb-4">{descText}</p>
                <div className="flex flex-wrap justify-center gap-1.5">
                  {chipSuggestions.map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => {
                        setInput(s);
                        textareaRef.current?.focus();
                      }}
                      className="text-[11px] px-2.5 py-1 rounded-lg border border-slate-200 text-slate-600 hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-600 transition-colors"
                    >
                      {s}
                    </button>
                    ))}
                  </div>
              </div>
            )}

            {messages.map((m, i) => (
              <div key={i} className={`flex gap-2.5 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {m.role === 'assistant' && (
                  <div className="w-7 h-7 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center shrink-0">
                    <Bot className="w-4 h-4 text-indigo-600" />
                  </div>
                )}
                <div className="max-w-[85%] space-y-1.5">
                  <div
                    className={`p-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                      m.role === 'user'
                        ? 'bg-indigo-600 text-white font-medium rounded-tr-none shadow-sm shadow-indigo-100'
                        : 'bg-slate-50 text-slate-800 rounded-tl-none border border-slate-200'
                    }`}
                  >
                    {m.content ?? ''}
                  </div>
                  {m.role === 'assistant' && m.content && (
                    <FeedbackRow
                      messageIndex={i}
                      sessionId={sessionIdRef.current ?? undefined}
                      sendFeedback={api.sendFeedback}
                    />
                  )}
                </div>
                {m.role === 'user' && (
                  <div className="w-7 h-7 rounded-lg bg-indigo-600 text-white flex items-center justify-center shrink-0 shadow-sm">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="flex gap-2.5 justify-start">
                <div className="w-7 h-7 rounded-lg bg-indigo-50 flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4 text-indigo-600" />
                </div>
                <div className="bg-slate-50 text-slate-500 border border-slate-200 p-3.5 rounded-2xl rounded-tl-none text-xs flex items-center gap-2">
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  Trợ lý đang truy vấn dữ liệu và phân tích...
                </div>
              </div>
            )}
          </div>

          {/* Draft Action */}
          <AnimatePresence>
            {draftAction && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="px-4 pb-2"
              >
                    <DraftActionCard
                      draft={draftAction}
                      onConfirm={handleDraftConfirm}
                      onReject={handleDraftReject}
                      onOpenRequest={
                        onOpenRequestDialog &&
                        (draftAction.action_type === 'submit_leave_request' ||
                         draftAction.action_type === 'submit_overtime_request')
                          ? () => handleDraftConfirm()
                          : undefined
                      }
                    />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Error */}
          {error && (
            <div className="mx-4 mb-2 flex items-center justify-between gap-2 border border-rose-200 bg-rose-50 px-3 py-2 rounded-lg text-xs text-rose-600">
              <span className="flex items-center gap-1.5">
                <AlertCircle className="w-3.5 h-3.5" />
                <span className="break-words">{error}</span>
              </span>
              <button
                type="button"
                onClick={() => {
                  setError(null);
                  handleSend();
                }}
                className="text-rose-600 underline hover:text-rose-700 shrink-0"
              >
                Thử lại
              </button>
            </div>
          )}

          {/* Form */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="p-3 bg-slate-50 border-t border-slate-200 flex gap-2"
          >
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              placeholder={assistantType === 'hr' ? 'Nhập câu hỏi hoặc yêu cầu soạn email...' : 'Hỏi về chấm công, phép hoặc soạn nháp yêu cầu...'}
              className="flex-1 bg-white border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 resize-none max-h-32"
              disabled={loading}
            />
                <button
                  type="submit"
                  aria-label="Gửi"
                  disabled={loading || !input.trim()}
                  className="p-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-100 text-white disabled:text-slate-400 rounded-xl transition-all shrink-0 shadow-md shadow-indigo-50"
                >
                  <span className="sr-only">Gửi</span>
                  <Send className="w-4 h-4" />
                </button>
          </form>
        </>
      )}
    </div>
  );
}