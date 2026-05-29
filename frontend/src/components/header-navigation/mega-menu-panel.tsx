"use client";

import { useRef, useCallback, type KeyboardEvent } from "react";
import Link from "next/link";
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

  if (!isOpen) {
    return <></>;
  }

  return (
    <div
      className="absolute left-0 top-full z-50 mt-1 min-w-[220px] rounded-lg border border-[#6C7278]/20 bg-white p-2 shadow-lg"
      role="menu"
      aria-label={`${group.label} submenu`}
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
              "focus-visible:ring-2 focus-visible:ring-[#B8422E]/50",
              isActive
                ? "bg-[#F7F5F2] font-semibold text-[#1A1C1E]"
                : "text-[#6C7278] hover:bg-[#F7F5F2] hover:text-[#1A1C1E]",
            )}
          >
            {Icon && <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />}
            <span>{link.label}</span>
          </Link>
        );
      })}
    </div>
  );
}
