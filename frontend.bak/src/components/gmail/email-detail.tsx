"use client";

import * as React from "react";
import { ArrowLeft, Reply, ChevronDown, ChevronUp, RotateCw, FileText } from "lucide-react";
import type { EmailMessage, MessageBodyResponse } from "@/lib/api/types";
import { ApiError } from "@/lib/api/types";
import { getMessageBody } from "@/lib/api/gmail";
import { AttachmentViewer } from "@/components/gmail/attachment-viewer";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface EmailDetailProps {
  email: EmailMessage | null;
  onBack: () => void;
  onReply: (email: EmailMessage) => void;
  onReclassify?: (emailId: string) => void;
  reclassifying?: string | null;
  onProcessAttachments?: (messageId: string) => void;
  processingAttachments?: string | null;
}

// ---------------------------------------------------------------------------
// Date Formatting (dd/MM/yyyy HH:mm)
// ---------------------------------------------------------------------------

function formatDetailDate(isoDate: string): string {
  const date = new Date(isoDate);
  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const year = date.getFullYear();
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${day}/${month}/${year} ${hours}:${minutes}`;
}

// ---------------------------------------------------------------------------
// Skeleton Loading State
// ---------------------------------------------------------------------------

function EmailDetailSkeleton() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="animate-pulse space-y-3 w-full max-w-md px-6">
        <div className="h-4 w-3/4 rounded bg-muted" />
        <div className="h-4 w-full rounded bg-muted" />
        <div className="h-4 w-5/6 rounded bg-muted" />
        <div className="h-4 w-2/3 rounded bg-muted" />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function EmailDetail({ email, onBack, onReply, onReclassify, reclassifying, onProcessAttachments, processingAttachments }: EmailDetailProps) {
  const [body, setBody] = React.useState<MessageBodyResponse | null>(null);
  const [bodyLoading, setBodyLoading] = React.useState(false);
  const [bodyError, setBodyError] = React.useState<string | null>(null);
  const [headerExpanded, setHeaderExpanded] = React.useState(false);

  // Fetch email body when email changes
  React.useEffect(() => {
    if (!email) {
      setBody(null);
      setBodyError(null);
      return;
    }

    let cancelled = false;

    async function fetchBody() {
      setBodyLoading(true);
      setBodyError(null);
      setBody(null);

      try {
        const response = await getMessageBody(email!.gmail_message_id);
        if (!cancelled) {
          setBody(response);
        }
      } catch (err) {
        if (!cancelled) {
          if (err instanceof ApiError && err.statusCode === 502) {
            setBodyError("Không thể tải nội dung email. Vui lòng thử lại.");
          } else {
            setBodyError("Đã xảy ra lỗi khi tải nội dung email.");
          }
        }
      } finally {
        if (!cancelled) {
          setBodyLoading(false);
        }
      }
    }

    fetchBody();

    return () => {
      cancelled = true;
    };
  }, [email]);

  // Collapse header when switching emails
  React.useEffect(() => {
    setHeaderExpanded(false);
  }, [email?.id]);

  // Retry handler for 502 errors
  function handleRetry() {
    if (!email) return;

    setBodyLoading(true);
    setBodyError(null);
    setBody(null);

    getMessageBody(email.gmail_message_id)
      .then((response) => {
        setBody(response);
      })
      .catch((err) => {
        if (err instanceof ApiError && err.statusCode === 502) {
          setBodyError("Không thể tải nội dung email. Vui lòng thử lại.");
        } else {
          setBodyError("Đã xảy ra lỗi khi tải nội dung email.");
        }
      })
      .finally(() => {
        setBodyLoading(false);
      });
  }

  // No email selected
  if (!email) {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <p className="text-sm text-muted-foreground">
          Chọn một email để xem nội dung
        </p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {/* Compact header: subject + sender + actions */}
      <div className="shrink-0 border-b border-border px-4 py-3">
        {/* Row 1: Back (mobile) + Subject + Reply */}
        <div className="flex items-start gap-3">
          <button
            type="button"
            onClick={onBack}
            className="mt-0.5 shrink-0 text-muted-foreground hover:text-foreground lg:hidden"
            aria-label="Quay lại"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>

          <div className="min-w-0 flex-1">
            <h2 className="text-base font-semibold text-foreground leading-tight">
              {email.subject}
            </h2>

            {/* Row 2: Sender info (compact) */}
            <div className="mt-1 flex items-center gap-2 text-sm">
              <span className="font-medium text-foreground">
                {email.sender_name}
              </span>
              <span className="text-muted-foreground">·</span>
              <span className="text-muted-foreground text-xs">
                {formatDetailDate(email.received_at)}
              </span>

              {/* Expand/collapse details */}
              <button
                type="button"
                onClick={() => setHeaderExpanded(!headerExpanded)}
                className="ml-1 text-muted-foreground hover:text-foreground"
                aria-label={
                  headerExpanded ? "Thu gọn chi tiết" : "Xem chi tiết"
                }
              >
                {headerExpanded ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </button>
            </div>

            {/* Expanded details */}
            {headerExpanded && (
              <div className="mt-2 space-y-0.5 text-xs text-muted-foreground">
                <div>
                  <span className="text-foreground">Từ: </span>
                  {email.sender_name} &lt;{email.sender_email}&gt;
                </div>
                <div>
                  <span className="text-foreground">Đến: </span>
                  {email.recipient_emails.join(", ")}
                </div>
                {email.cc_emails.length > 0 && (
                  <div>
                    <span className="text-foreground">CC: </span>
                    {email.cc_emails.join(", ")}
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            {/* Process CV button — shown for recruitment emails with attachments */}
            {email.category === "recruitment" && email.has_attachments && email.processing_status === "classified" && onProcessAttachments && (
              <button
                type="button"
                onClick={() => onProcessAttachments(email.gmail_message_id)}
                disabled={processingAttachments === email.gmail_message_id}
                className="shrink-0 flex items-center gap-1.5 rounded-md bg-blue-100 px-3 py-1.5 text-sm font-medium text-blue-700 hover:bg-blue-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <FileText className="h-4 w-4" />
                <span className="hidden sm:inline">
                  {processingAttachments === email.gmail_message_id ? "Đang xử lý CV..." : "Xử lý CV"}
                </span>
              </button>
            )}

            {/* Reclassify button — shown for needs_review emails */}
            {email.processing_status === "needs_review" && onReclassify && (
              <button
                type="button"
                onClick={() => onReclassify(email.id)}
                disabled={reclassifying === email.id}
                className="shrink-0 flex items-center gap-1.5 rounded-md bg-orange-100 px-3 py-1.5 text-sm font-medium text-orange-700 hover:bg-orange-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <RotateCw className="h-4 w-4" />
                <span className="hidden sm:inline">
                  {reclassifying === email.id ? "Đang phân loại..." : "Phân loại lại"}
                </span>
              </button>
            )}

            {/* Reply button */}
            <button
              type="button"
              onClick={() => onReply(email)}
              className="shrink-0 flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              <Reply className="h-4 w-4" />
              <span className="hidden sm:inline">Trả lời</span>
            </button>
          </div>
        </div>
      </div>

      {/* Email body — takes all remaining space */}
      <div className="flex-1 overflow-y-auto min-h-0">
        {bodyLoading && <EmailDetailSkeleton />}

        {bodyError && (
          <div className="flex flex-col items-center justify-center gap-3 p-8 text-center h-full">
            <p className="text-sm text-destructive">{bodyError}</p>
            <button
              type="button"
              onClick={handleRetry}
              className="rounded-md border border-border px-4 py-2 text-sm font-medium text-foreground hover:bg-accent transition-colors"
            >
              Thử lại
            </button>
          </div>
        )}

        {!bodyLoading && !bodyError && body && (
          <>
            {body.html ? (
              <iframe
                srcDoc={body.html}
                sandbox=""
                title="Nội dung email"
                className="h-full w-full border-0"
              />
            ) : body.plain_text ? (
              <div className="p-5">
                <pre className="whitespace-pre-wrap break-words text-sm text-foreground font-sans leading-relaxed">
                  {body.plain_text}
                </pre>
              </div>
            ) : (
              <div className="flex h-full items-center justify-center">
                <p className="text-sm text-muted-foreground italic">
                  Không có nội dung email
                </p>
              </div>
            )}
          </>
        )}
      </div>

      {/* Attachment viewer — shown when email has attachments */}
      {email && (
        <AttachmentViewer
          messageId={email.gmail_message_id}
          hasAttachments={email.has_attachments}
        />
      )}
    </div>
  );
}
