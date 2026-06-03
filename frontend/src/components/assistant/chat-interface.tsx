"use client";

import { useState, useRef, useEffect } from "react";
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
} from "@/lib/api/assistant";

export function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [draftAction, setDraftAction] = useState<DraftAction | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

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
      const response = await sendChatMessage(updatedMessages);

      // Add new assistant messages to conversation
      setMessages([...updatedMessages, ...response.messages]);

      // Show draft action if present
      if (response.draft_action) {
        setDraftAction(response.draft_action);
      }
    } catch (err) {
      toast.error(
        `Lỗi: ${err instanceof Error ? err.message : "Không thể kết nối trợ lý"}`
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

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col">
      {/* Chat messages area */}
      <ScrollArea className="flex-1 px-4">
        <div ref={scrollRef} className="space-y-4 py-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 mb-4">
                <MessageSquare className="h-8 w-8 text-primary" />
              </div>
              <h3 className="text-lg font-medium mb-2">Trợ lý AI Vroom HR</h3>
              <p className="text-sm text-muted-foreground max-w-md">
                Hỏi tôi về dữ liệu tuyển dụng, tiến độ onboarding, hoặc yêu cầu soạn email.
              </p>
              <div className="mt-6 flex flex-wrap justify-center gap-2">
                {[
                  "Có bao nhiêu candidate đang reviewing?",
                  "Onboarding nào đang chạy?",
                  "Soạn email chúc mừng cho Nguyễn Văn A",
                ].map((suggestion) => (
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
                <span className="text-sm text-muted-foreground">Đang suy nghĩ...</span>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Draft Action */}
      {draftAction && (
        <div className="border-t px-4 py-3">
          <DraftActionCard
            draft={draftAction}
            onConfirmed={() => setDraftAction(null)}
            onDismissed={() => setDraftAction(null)}
          />
        </div>
      )}

      {/* Input area */}
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
