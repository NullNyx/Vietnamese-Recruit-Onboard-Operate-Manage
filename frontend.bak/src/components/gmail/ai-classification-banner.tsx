"use client";

import * as React from "react";
import { Sparkles, ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";
import type { EmailMessage } from "@/lib/api/types";
import { CATEGORY_META } from "./utils";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface AIClassificationBannerProps {
  emails: EmailMessage[];
  selectedCategory: string | null;
  onCategoryChange: (category: string | null) => void;
  onClassify?: () => void;
  classifying?: boolean;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/**
 * AI Classification Banner — the primary UI element that communicates
 * to HR users that the system is automatically categorizing their emails.
 *
 * Shows:
 * - AI status indicator ("AI đã phân loại X/Y email")
 * - Quick-access category pills (clickable to filter)
 * - Expandable to show all categories
 */
export function AIClassificationBanner({
  emails,
  selectedCategory,
  onCategoryChange,
  onClassify,
  classifying = false,
}: AIClassificationBannerProps) {
  const [expanded, setExpanded] = React.useState(false);

  // Calculate stats
  const stats = React.useMemo(() => {
    const total = emails.length;
    const classified = emails.filter(
      (e) => e.category && e.category !== "uncategorized",
    ).length;
    const unclassified = total - classified;

    // Count per category (sorted by count desc)
    const counts: Record<string, number> = {};
    for (const email of emails) {
      const cat = email.category || "uncategorized";
      counts[cat] = (counts[cat] || 0) + 1;
    }

    const sortedCategories = Object.entries(counts)
      .sort(([, a], [, b]) => b - a)
      .filter(([cat]) => cat !== "uncategorized");

    return { total, classified, unclassified, counts, sortedCategories };
  }, [emails]);

  if (stats.total === 0) return null;

  // Show top 5 categories in collapsed mode
  const visibleCategories = expanded
    ? stats.sortedCategories
    : stats.sortedCategories.slice(0, 5);

  return (
    <div className="bg-card border-b border-border">
      {/* AI Status Header */}
      <div className="flex items-center justify-between px-4 py-2.5">
        <div className="flex items-center gap-2">
          <div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary/10">
            <Sparkles className="h-3.5 w-3.5 text-primary" />
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-medium text-muted-foreground">
              AI phân loại
            </span>
            <span className="rounded-full bg-primary/10 px-1.5 py-0.5 text-[10px] font-semibold text-primary">
              {stats.classified}/{stats.total}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Classify button — shown when there are unclassified emails */}
          {stats.unclassified > 0 && onClassify && (
            <button
              type="button"
              onClick={onClassify}
              disabled={classifying}
              className={cn(
                "flex items-center gap-1 rounded-md px-2.5 py-1 text-[11px] font-medium transition-colors",
                classifying
                  ? "bg-primary/5 text-primary/50 cursor-not-allowed"
                  : "bg-primary/10 text-primary hover:bg-primary/20",
              )}
            >
              <Sparkles
                className={cn("h-3 w-3", classifying && "animate-spin")}
              />
              {classifying
                ? "Đang phân loại..."
                : `Phân loại (${stats.unclassified})`}
            </button>
          )}

          {/* Filter active indicator */}
          {selectedCategory && (
            <button
              type="button"
              onClick={() => onCategoryChange(null)}
              className="flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground hover:bg-accent transition-colors"
            >
              ✕ Bỏ lọc
            </button>
          )}
        </div>
      </div>

      {/* Category Pills */}
      <div className="px-4 pb-2.5">
        <div className="flex flex-wrap gap-1.5">
          {/* "All" pill */}
          <button
            type="button"
            onClick={() => onCategoryChange(null)}
            className={cn(
              "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-medium transition-colors",
              selectedCategory === null
                ? "bg-primary/10 text-foreground ring-1 ring-primary/20"
                : "bg-muted text-muted-foreground hover:bg-accent",
            )}
          >
            Tất cả
            <span className="text-[10px] opacity-60">{stats.total}</span>
          </button>

          {/* Category pills */}
          {visibleCategories.map(([category, count]) => {
            const meta = CATEGORY_META[category];
            if (!meta) return null;

            return (
              <button
                key={category}
                type="button"
                onClick={() =>
                  onCategoryChange(
                    selectedCategory === category ? null : category,
                  )
                }
                className={cn(
                  "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-medium transition-colors",
                  selectedCategory === category
                    ? "bg-primary/10 text-foreground ring-1 ring-primary/20"
                    : "bg-muted text-muted-foreground hover:bg-accent",
                )}
              >
                <span>{meta.icon}</span>
                <span>{meta.label}</span>
                <span className="text-[10px] opacity-60">{count}</span>
              </button>
            );
          })}

          {/* Unclassified pill (if any) */}
          {stats.unclassified > 0 && (
            <button
              type="button"
              onClick={() =>
                onCategoryChange(
                  selectedCategory === "uncategorized" ? null : "uncategorized",
                )
              }
              className={cn(
                "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-medium transition-colors",
                selectedCategory === "uncategorized"
                  ? "bg-primary/10 text-foreground ring-1 ring-primary/20"
                  : "bg-muted text-muted-foreground hover:bg-accent",
              )}
            >
              <span>❓</span>
              <span>Chưa phân loại</span>
              <span className="text-[10px] opacity-60">
                {stats.unclassified}
              </span>
            </button>
          )}

          {/* Expand/collapse toggle */}
          {stats.sortedCategories.length > 5 && (
            <button
              type="button"
              onClick={() => setExpanded(!expanded)}
              className="inline-flex items-center gap-0.5 rounded-full px-2 py-1 text-[11px] text-muted-foreground hover:text-foreground transition-colors"
            >
              {expanded ? (
                <>
                  Thu gọn <ChevronUp className="h-3 w-3" />
                </>
              ) : (
                <>
                  +{stats.sortedCategories.length - 5} loại{" "}
                  <ChevronDown className="h-3 w-3" />
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
