"use client";

import * as React from "react";
import { Paperclip } from "lucide-react";
import { cn } from "@/lib/utils";
import type { EmailMessage } from "@/lib/api/types";
import { formatRelativeDate, CATEGORY_META } from "./utils";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface EmailListProps {
  emails: EmailMessage[];
  selectedId: string | null;
  loading: boolean;
  onSelect: (id: string) => void;
  connected: boolean;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Truncate a snippet to a maximum of 100 characters, appending "..." if longer.
 */
function truncateSnippet(snippet: string): string {
  if (snippet.length <= 100) return snippet;
  return snippet.slice(0, 100) + "...";
}

// ---------------------------------------------------------------------------
// Skeleton Loading State
// ---------------------------------------------------------------------------

function EmailListSkeleton() {
  return (
    <div className="flex flex-col gap-1 p-2">
      {Array.from({ length: 6 }).map((_, i) => (
        <div
          key={i}
          className="animate-pulse rounded-lg border border-border bg-card p-4"
        >
          <div className="flex items-center justify-between">
            <div className="h-4 w-32 rounded bg-muted" />
            <div className="h-3 w-16 rounded bg-muted" />
          </div>
          <div className="mt-2 h-4 w-48 rounded bg-muted" />
          <div className="mt-2 h-3 w-full rounded bg-muted" />
          <div className="mt-2 flex gap-1">
            <div className="h-5 w-16 rounded bg-muted" />
          </div>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function EmailList({
  emails,
  selectedId,
  loading,
  onSelect,
  connected,
}: EmailListProps) {
  // Hide when not connected
  if (!connected) {
    return null;
  }

  // Loading state
  if (loading) {
    return <EmailListSkeleton />;
  }

  // Sort emails by received_at descending (newest first)
  const sortedEmails = [...emails].sort(
    (a, b) =>
      new Date(b.received_at).getTime() - new Date(a.received_at).getTime(),
  );

  // Empty state
  if (sortedEmails.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center">
        <p className="text-sm text-muted-foreground">Không có email nào</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-1 overflow-y-auto p-2">
      {sortedEmails.map((email) => {
        const isSelected = email.id === selectedId;

        return (
          <button
            key={email.id}
            type="button"
            onClick={() => onSelect(email.id)}
            className={cn(
              "w-full rounded-lg border p-3 text-left transition-colors",
              "hover:bg-accent",
              isSelected
                ? "border-primary bg-primary/5"
                : "border-border bg-card",
            )}
          >
            {/* Header: sender + date */}
            <div className="flex items-center justify-between gap-2">
              <div className="min-w-0 flex-1 truncate">
                <span className="text-sm font-medium text-foreground">
                  {email.sender_name}
                </span>
                <span className="ml-1 text-xs text-muted-foreground hidden sm:inline">
                  &lt;{email.sender_email}&gt;
                </span>
              </div>
              <div className="flex shrink-0 items-center gap-1">
                {email.has_attachments && (
                  <Paperclip className="h-3.5 w-3.5 text-muted-foreground" />
                )}
                <span className="text-xs text-muted-foreground whitespace-nowrap">
                  {formatRelativeDate(email.received_at)}
                </span>
              </div>
            </div>

            {/* Subject */}
            <p className="mt-1 truncate text-sm font-medium text-foreground">
              {email.subject}
            </p>

            {/* Snippet */}
            <p className="mt-0.5 text-xs text-muted-foreground line-clamp-2">
              {truncateSnippet(email.snippet)}
            </p>

            {/* Category badge */}
            {email.category && CATEGORY_META[email.category] && (
              <div className="mt-2 flex flex-wrap gap-1">
                <span
                  className={cn(
                    "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
                    CATEGORY_META[email.category].bg,
                    CATEGORY_META[email.category].text,
                  )}
                >
                  <span>{CATEGORY_META[email.category].icon}</span>
                  {CATEGORY_META[email.category].label}
                </span>
              </div>
            )}
          </button>
        );
      })}
    </div>
  );
}
