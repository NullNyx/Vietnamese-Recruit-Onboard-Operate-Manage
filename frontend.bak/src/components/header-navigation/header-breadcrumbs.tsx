"use client";

import { Breadcrumbs } from "@/components/breadcrumbs";
import { cn } from "@/lib/utils";

interface HeaderBreadcrumbsProps {
  className?: string;
}

/**
 * Breadcrumb strip embedded inside the header.
 * Hidden on mobile (<md), shown on tablet and desktop.
 */
export function HeaderBreadcrumbs({ className }: HeaderBreadcrumbsProps) {
  return (
    <div
      className={cn(
        "hidden md:flex md:items-center md:pl-4 md:border-l md:border-border/40 min-w-0",
        className,
      )}
    >
      <Breadcrumbs showHome={false} />
    </div>
  );
}
