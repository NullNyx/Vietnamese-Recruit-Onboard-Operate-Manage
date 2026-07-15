"use client";

import { useState, useRef, useEffect, useCallback, type ReactNode } from "react";
import { Send, Loader2, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import { MessageBubble } from "./message-bubble";
import { DraftActionCard } from "./draft-action-card";
import {
  sendChatMessage,
  startSession,
  endSession,
  sendFeedback,
  type ChatMessage,
  type DraftAction,
  type ChatResponse,
} from "@/lib/api/assistant";

export interface ChatInterfaceProps {
  sendMessage?: (
    messages: ChatMessage[],
    sessionId?: string,
  ) => Promise<ChatResponse>;
  confirmAction?: (draft: DraftAction) => Promise<unknown>;
  title?: string;
  description?: string;
  suggestions?: string[];
  icon?: ReactNode;
  /** Called when draft action should open request form with prefill */
  onOpenRequestDialog?: (values: {
    leave?: Record<string, string>;
    overtime?: Record<string, string>;
  }) => void | Promise<void>;
  /** Type of assistant for session tracking: 'hr' or 'employee' */
  assistantType?: "hr" | "employee";
  /** Custom session start handler (e.g. for employee assistant) */
  onSessionStart?: (assistantType: "hr" | "employee") => Promise<{ session_id: string }>;
  /** Custom session end handler */
  onSessionEnd?: (sessionId: string) => Promise<void>;
}

export function ChatInterface({
  sendMessage = sendChatMessage,
  confirmAction,
  title = "Trợ lý AI Vroom HR",
  description = "Hỏi tôi về dữ liệu nhân sự của bạn.",
  suggestions,
  icon,
  onOpenRequestDialog,
  assistantType = "hr",
  onSessionStart,
  onSessionEnd,
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [lastError, setLastError] = useState<string | null>(null);
  const [draftAction, setDraftAction] = useState<DraftAction | null>(null);
  const [prefillValues, setPrefillValues] = useState<{
    leave?: Record<string, string>;
    overtime?: Record<string, string>;
  } | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const sessionIdRef = useRef<string | null>(null);
  const mountedRef = useRef(true);

  // Start session on mount, end on unmount
  useEffect(() => {
    mountedRef.current = true;
    const startSess = onSessionStart ?? startSession;
    const endSess = onSessionEnd ?? endSession;

    startSess(assistantType)
      .then((res) => {
        if (mountedRef.current) {
          sessionIdRef.current = res.session_id;
        }
      })
      .catch((err) => {
        console.warn("Failed to start assistant session:", err);
      });

    return () => {
      mountedRef.current = false;
      const sid = sessionIdRef.current;
      if (sid) {
        endSess(sid).catch((err) => {
          console.warn("Failed to end assistant session:", err);
        });
      }
    };
  }, [assistantType, onSessionStart, onSessionEnd]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // Store onOpenRequestDialog in ref to avoid re-running effect on reference change
  const onOpenRequestDialogRef = useRef(onOpenRequestDialog);
  onOpenRequestDialogRef.current = onOpenRequestDialog;

  // Open request dialog when prefill values are set
  useEffect(() => {
    if (prefillValues && onOpenRequestDialogRef.current) {
      Promise.resolve(onOpenRequestDialogRef.current(prefillValues)).finally(() => {
        setPrefillValues(null);
        setDraftAction(null);
      });
    }
  }, [prefillValues]);

  const handleSend = async (retry = false) => {
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    const userMessage: ChatMessage = { role: "user", content: trimmed };
    const updatedMessages = retry ? messages : [...messages, userMessage];
    setMessages(updatedMessages);
    setInput("");
    setLastError(null);
    setDraftAction(null);
    setLoading(true);

    try {
      const response = await sendMessage(updatedMessages, sessionIdRef.current ?? undefined);

      // Filter out tool-call only messages (content=null, role=assistant)
      const displayMessages = response.messages.filter(
        (m) => !(m.role === "assistant" && m.content === null && m.tool_calls),
      );

      setMessages([...updatedMessages, ...displayMessages]);

      if (response.draft_action) {
        setDraftAction(response.draft_action);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Không thể kết nối trợ lý";
      setInput(trimmed);
      setLastError(message);
      toast.error(`Lỗi: ${message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFeedback = useCallback(
    async (messageIndex: number, feedbackType: "up" | "down", optionalText?: string) => {
      const sid = sessionIdRef.current;
      if (!sid) {
        toast.error("Không thể gửi đánh giá: chưa có session");
        return;
      }
      try {
        await sendFeedback({
          session_id: sid,
          message_index: messageIndex,
          feedback_type: feedbackType,
          optional_text: optionalText,
        });
      } catch (err) {
        console.warn("Failed to send feedback:", err);
        toast.error("Không thể gửi đánh giá");
      }
    },
    [],
  );

  const handleDraftConfirm = () => {
    if (!draftAction) {
      return;
    }

    if (draftAction.action_type === "submit_leave_request") {
      setPrefillValues({
        leave: {
          leave_type: String(draftAction.confirm_body.leave_type ?? ""),
          start_date: String(draftAction.confirm_body.start_date ?? ""),
          end_date: String(draftAction.confirm_body.end_date ?? ""),
          reason: String(draftAction.confirm_body.reason ?? ""),
        },
      });
    } else if (draftAction.action_type === "submit_overtime_request") {
      setPrefillValues({
        overtime: {
          work_date: String(draftAction.confirm_body.work_date ?? ""),
          start_time: String(draftAction.confirm_body.start_time ?? ""),
          end_time: String(draftAction.confirm_body.end_time ?? ""),
          reason: String(draftAction.confirm_body.reason ?? ""),
          project_or_task: String(draftAction.confirm_body.project_or_task ?? ""),
        },
      });
    } else {
      toast.error("Loại yêu cầu không được hỗ trợ: " + draftAction.action_type);
      return;
    }
  };

  const defaultSuggestions = suggestions || [
    "Có bao nhiêu candidate đang reviewing?",
    "Onboarding nào đang chạy?",
    "Soạn email chúc mừng cho Nguyễn Văn A",
  ];

  const defaultIcon = icon || (
    <MessageSquare className="h-8 w-8 text-primary" />
  );

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col">
      <ScrollArea className="flex-1 px-4">
        <div ref={scrollRef} className="space-y-4 py-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 mb-4">
                {defaultIcon}
              </div>
              <h3 className="text-lg font-medium mb-2">{title}</h3>
              <p className="text-sm text-muted-foreground max-w-md">
                {description}
              </p>
              <div className="mt-6 flex flex-wrap justify-center gap-2">
                {defaultSuggestions.map((suggestion) => (
                  <Button
                    key={suggestion}
                    variant="outline"
                    size="sm"
                    className="text-xs"
                    onClick={() => {
                      setInput(suggestion);
                      textareaRef.current?.focus();
                    }}
                  >
                    {suggestion}
                  </Button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <MessageBubble
              key={i}
              message={msg}
              messageIndex={i}
              sessionId={sessionIdRef.current ?? undefined}
              onFeedback={handleFeedback}
            />
          ))}

          {loading && (
            <div className="flex gap-3 justify-start">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
                <Loader2 className="h-4 w-4 text-primary animate-spin" />
              </div>
              <div className="flex items-center rounded-lg bg-muted px-4 py-2">
                <span className="text-sm text-muted-foreground">
                  Đang suy nghĩ...
                </span>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {draftAction && (
        <div className="border-t px-4 py-3">
          <DraftActionCard
            draft={draftAction}
            confirmAction={confirmAction}
            confirmLabel={onOpenRequestDialog ? "Mở form" : "Xác nhận"}
            onConfirmed={onOpenRequestDialog ? handleDraftConfirm : undefined}
            onDismissed={() => setDraftAction(null)}
          />
        </div>
      )}

      {lastError && (
        <div className="flex items-center justify-between gap-3 border-t px-4 py-2 text-sm text-destructive">
          <span>Không thể kết nối trợ lý: {lastError}</span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setLastError(null);
              handleSend(true);
            }}
            disabled={loading}
          >
            Thử lại
          </Button>
        </div>
      )}

      <div className="border-t px-4 py-3">
        <div className="flex gap-2">
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Nhập tin nhắn..."
            rows={1}
            className="min-h-[44px] resize-none"
            disabled={loading}
          />
          <Button
            onClick={() => handleSend()}
            disabled={!input.trim() || loading}
            size="icon"
            className="shrink-0"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
