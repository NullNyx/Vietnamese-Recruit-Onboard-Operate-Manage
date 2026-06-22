"use client";

import { useState, useRef, useEffect, type ReactNode } from "react";
import { Send, Loader2, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import { MessageBubble } from "./message-bubble";
import { DraftActionCard } from "./draft-action-card";
import {
  sendChatMessage,
  type ChatMessage,
  type DraftAction,
  type ChatResponse,
} from "@/lib/api/assistant";

export interface ChatInterfaceProps {
  sendMessage?: (
    messages: ChatMessage[],
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
  }) => void;
}

export function ChatInterface({
  sendMessage = sendChatMessage,
  confirmAction,
  title = "Trợ lý AI Vroom HR",
  description = "Hỏi tôi về dữ liệu nhân sự của bạn.",
  suggestions,
  icon,
  onOpenRequestDialog,
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [draftAction, setDraftAction] = useState<DraftAction | null>(null);
  const [prefillValues, setPrefillValues] = useState<{
    leave?: Record<string, string>;
    overtime?: Record<string, string>;
  } | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // Open request dialog when prefill values are set
  useEffect(() => {
    if (prefillValues && onOpenRequestDialog) {
      onOpenRequestDialog(prefillValues);
      setPrefillValues(null);
      setDraftAction(null);
    }
  }, [prefillValues, onOpenRequestDialog]);

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    const userMessage: ChatMessage = { role: "user", content: trimmed };
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInput("");
    setDraftAction(null);
    setLoading(true);

    try {
      const response = await sendMessage(updatedMessages);

      // Filter out tool-call only messages (content=null, role=assistant)
      // that would render as empty bubbles or stuck loaders in the UI.
      const displayMessages = response.messages.filter(
        (m) => !(m.role === "assistant" && m.content === null && m.tool_calls),
      );

      setMessages([...updatedMessages, ...displayMessages]);

      if (response.draft_action) {
        setDraftAction(response.draft_action);
      }
    } catch (err) {
      toast.error(
        `Lỗi: ${err instanceof Error ? err.message : "Không thể kết nối trợ lý"}`,
      );
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

  const handleDraftConfirm = () => {
    if (!draftAction) {
      return;
    }

    // If onOpenRequestDialog exists, use prefill flow; otherwise fallback to confirmAction
    if (!onOpenRequestDialog) {
      confirmAction?.(draftAction);
      return;
    }

    // Translate draft action to prefill values
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
            <MessageBubble key={i} message={msg} />
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
            onClick={handleSend}
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
