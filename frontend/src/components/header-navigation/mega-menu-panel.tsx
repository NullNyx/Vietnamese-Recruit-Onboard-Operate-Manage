"use client";

import { useRef, useCallback, type KeyboardEvent } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "motion/react";
import { cn } from "@/lib/utils";
import type { NavGroup } from "@/lib/header-nav-config";

interface MegaMenuPanelProps {
  group: NavGroup;
  isOpen: boolean;
  onLinkClick: (href: string) => void;
  activeSubLinkHref?: string | null;
}

export function MegaMenuPanel({
  group,
  isOpen,
  onLinkClick,
  activeSubLinkHref,
}: MegaMenuPanelProps): JSX.Element {
  const linkRefs = useRef<(HTMLAnchorElement | null)[]>([]);

  const setLinkRef = useCallback(
    (index: number) => (el: HTMLAnchorElement | null) => {
      linkRefs.current[index] = el;
    },
    [],
  );

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLAnchorElement>, index: number) => {
      const N = group.links.length;
      if (N === 0) return;

      let nextIndex: number | null = null;

      if (e.key === "ArrowDown") {
        e.preventDefault();
        nextIndex = (index + 1) % N;
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        nextIndex = (index - 1 + N) % N;
      }

      if (nextIndex !== null) {
        linkRefs.current[nextIndex]?.focus();
      }
    },
    [group.links.length],
  );

  // Use grid layout for groups with >4 links
  const useGrid = group.links.length > 4;

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: -8 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: -8 }}
          transition={{ duration: 0.15, ease: "easeOut" }}
          className={cn(
            "absolute left-0 top-full z-50 mt-1 rounded-lg border shadow-xl",
            "border-border/40 bg-card p-2",
            useGrid ? "min-w-[420px]" : "min-w-[220px]",
          )}
          role="menu"
          aria-label={`${group.label} submenu`}
        >
          <div
            className={cn(
              useGrid && "grid grid-cols-2 gap-1",
            )}
          >
            {group.links.map((link, index) => {
              const isActive = link.href === activeSubLinkHref;
              const Icon = link.icon;

              return (
                <Link
                  key={link.href}
                  ref={setLinkRef(index)}
                  href={link.href}
                  role="menuitem"
                  aria-current={isActive ? "page" : undefined}
                  onClick={(e) => {
                    e.preventDefault();
                    onLinkClick(link.href);
                  }}
                  onKeyDown={(e) => handleKeyDown(e, index)}
                  className={cn(
                    "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors outline-none",
                    "focus-visible:ring-2 focus-visible:ring-primary/50",
                    isActive
                      ? "bg-accent/10 text-accent border-l-2 border-primary/50"
                      : "text-muted-foreground hover:bg-accent/10 hover:text-foreground",
                  )}
                >
                  {Icon && (
                    <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                  )}
                  <div className="flex flex-col">
                    <span>{link.label}</span>
                    {link.description && (
                      <span className="text-xs text-muted-foreground/70 font-normal">
                        {link.description}
                      </span>
                    )}
                  </div>
                </Link>
              );
            })}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
