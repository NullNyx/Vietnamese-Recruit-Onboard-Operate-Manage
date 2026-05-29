"use client";

import { useEffect, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { X } from "lucide-react";

import { cn } from "@/lib/utils";
import type { NavGroup } from "@/lib/header-nav-config";

interface MobileMenuOverlayProps {
  isOpen: boolean;
  onClose: () => void;
  navGroups: NavGroup[];
  currentPath: string;
}

export function MobileMenuOverlay({
  isOpen,
  onClose,
  navGroups,
  currentPath,
}: MobileMenuOverlayProps) {
  const router = useRouter();

  // Prevent background scroll when overlay is open
  useEffect(() => {
    if (isOpen) {
      document.body.classList.add("overflow-hidden");
    } else {
      document.body.classList.remove("overflow-hidden");
    }

    return () => {
      document.body.classList.remove("overflow-hidden");
    };
  }, [isOpen]);

  // Handle Escape key to dismiss overlay
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    },
    [onClose],
  );

  useEffect(() => {
    if (isOpen) {
      document.addEventListener("keydown", handleKeyDown);
    }

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, handleKeyDown]);

  // Handle link click: close overlay and navigate
  const handleLinkClick = (href: string) => {
    onClose();
    router.push(href);
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-50 bg-background"
      role="dialog"
      aria-modal="true"
      aria-label="Menu điều hướng"
    >
      {/* Header with close button */}
      <div className="flex items-center justify-between border-b px-4 py-3">
        <span className="text-lg font-semibold">Menu</span>
        <button
          onClick={onClose}
          className="flex h-10 w-10 items-center justify-center rounded-md hover:bg-accent"
          aria-label="Đóng menu"
        >
          <X className="h-5 w-5" aria-hidden="true" />
        </button>
      </div>

      {/* Navigation groups */}
      <nav
        className="overflow-y-auto px-4 py-4"
        style={{ maxHeight: "calc(100vh - 57px)" }}
        aria-label="Điều hướng chính"
      >
        {navGroups.map((group) => (
          <div key={group.id} className="mb-6">
            {/* Group section header */}
            <div className="mb-2 flex items-center gap-2 px-2">
              {group.icon && (
                <group.icon
                  className="h-4 w-4 text-muted-foreground"
                  aria-hidden="true"
                />
              )}
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                {group.label}
              </span>
            </div>

            {/* Sub-links */}
            <div className="space-y-0.5">
              {group.links.map((link) => {
                const isActive = currentPath === link.href;

                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    onClick={(e) => {
                      e.preventDefault();
                      handleLinkClick(link.href);
                    }}
                    className={cn(
                      "flex min-h-[44px] items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                      isActive
                        ? "bg-accent text-accent-foreground font-semibold"
                        : "text-foreground/80 hover:bg-accent hover:text-accent-foreground",
                    )}
                    aria-current={isActive ? "page" : undefined}
                  >
                    {link.icon && (
                      <link.icon
                        className="h-5 w-5 shrink-0"
                        aria-hidden="true"
                      />
                    )}
                    <span>{link.label}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>
    </div>
  );
}
