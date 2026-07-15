"use client";

import { useState } from "react";
import { ThumbsUp, ThumbsDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

type FeedbackType = "up" | "down";

interface FeedbackButtonsProps {
  messageIndex: number;
  sessionId: string;
  onFeedback: (
    messageIndex: number,
    feedbackType: FeedbackType,
    optionalText?: string,
  ) => Promise<void>;
}

export function FeedbackButtons({
  messageIndex,
  onFeedback,
}: FeedbackButtonsProps) {
  const [submittedFeedback, setSubmittedFeedback] =
    useState<FeedbackType | null>(null);
  const [showTextInput, setShowTextInput] = useState(false);
  const [feedbackText, setFeedbackText] = useState("");
  const [sending, setSending] = useState(false);

  const handleFeedback = async (type: FeedbackType) => {
    if (submittedFeedback || sending) return;

    if (type === "down") {
      // Show optional text input first; user submits via the text form
      setShowTextInput(true);
      return;
    }

    // thumbs up: submit immediately
    setSending(true);
    try {
      await onFeedback(messageIndex, type);
      setSubmittedFeedback(type);
    } finally {
      setSending(false);
    }
  };

  const handleSubmitDownWithText = async () => {
    if (submittedFeedback || sending) return;

    setSending(true);
    try {
      await onFeedback(messageIndex, "down", feedbackText || undefined);
      setSubmittedFeedback("down");
      setShowTextInput(false);
    } finally {
      setSending(false);
    }
  };

  const handleTextKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmitDownWithText();
    }
  };

  return (
    <div className="mt-2">
      <div className="flex items-center gap-1">
        <button
          type="button"
          onClick={() => handleFeedback("up")}
          disabled={submittedFeedback !== null || sending}
          className={`inline-flex h-7 w-7 items-center justify-center rounded-md text-xs transition-colors ${
            submittedFeedback === "up"
              ? "bg-primary/10 text-primary"
              : "text-muted-foreground hover:bg-muted hover:text-foreground"
          } disabled:opacity-60 disabled:cursor-not-allowed`}
          aria-label="Thumbs up"
        >
          <ThumbsUp className="h-3.5 w-3.5" />
        </button>
        <button
          type="button"
          onClick={() => handleFeedback("down")}
          disabled={submittedFeedback !== null || sending}
          className={`inline-flex h-7 w-7 items-center justify-center rounded-md text-xs transition-colors ${
            submittedFeedback === "down"
              ? "bg-destructive/10 text-destructive"
              : "text-muted-foreground hover:bg-muted hover:text-foreground"
          } disabled:opacity-60 disabled:cursor-not-allowed`}
          aria-label="Thumbs down"
        >
          <ThumbsDown className="h-3.5 w-3.5" />
        </button>

        {submittedFeedback === "up" && (
          <span className="text-xs text-muted-foreground ml-1">
            Đã đánh giá
          </span>
        )}
      </div>

      {showTextInput && !submittedFeedback && (
        <div className="mt-2 flex flex-col gap-2">
          <Textarea
            value={feedbackText}
            onChange={(e) => setFeedbackText(e.target.value)}
            onKeyDown={handleTextKeyDown}
            placeholder="Phản hồi thêm (không bắt buộc)..."
            rows={2}
            className="min-h-[60px] resize-none text-xs"
            disabled={sending}
          />
          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="text-xs h-7"
              onClick={() => {
                // Submit down without text
                handleSubmitDownWithText();
              }}
              disabled={sending}
            >
              {sending ? "Đang gửi..." : "Gửi"}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
