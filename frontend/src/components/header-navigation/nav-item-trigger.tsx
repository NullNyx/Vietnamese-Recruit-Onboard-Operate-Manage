"use client";

import { useCallback, useRef } from "react";
import { cn } from "@/lib/utils";
import type { NavGroup } from "@/lib/header-nav-config";

interface NavItemTriggerProps {
  group: NavGroup;
  isActive: boolean;
  isOpen: boolean;
  onToggle: () => void;
  onHoverIntent: () => void;
}

export function NavItemTrigger({
  group,
  isActive,
  isOpen,
  onToggle,
  onHoverIntent,
}: NavItemTriggerProps): JSX.Element {
  const hoverTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleMouseEnter = useCallback(() => {
    hoverTimerRef.current = setTimeout(() => {
      onHoverIntent();
      hoverTimerRef.current = null;
    }, 300);
  }, [onHoverIntent]);

  const handleMouseLeave = useCallback(() => {
    if (hoverTimerRef.current !== null) {
      clearTimeout(hoverTimerRef.current);
      hoverTimerRef.current = null;
    }
  }, []);

  const Icon = group.icon;

  return (
    <button
      type="button"
      className={cn(
        "relative inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium transition-colors",
        "rounded-md hover:bg-accent hover:text-accent-foreground",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        isActive && "text-primary font-semibold",
        isActive &&
          "after:absolute after:bottom-0 after:left-2 after:right-2 after:h-0.5 after:bg-primary after:rounded-full",
        isOpen && "bg-accent text-accent-foreground",
      )}
      aria-expanded={isOpen}
      aria-haspopup="true"
      onClick={onToggle}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {Icon && <Icon className="size-4" />}
      <span>{group.label}</span>
    </button>
  );
}
