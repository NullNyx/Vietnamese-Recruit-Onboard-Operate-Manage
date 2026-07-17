"use client";

import { useEffect, useCallback, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { X, ChevronDown, LogOut } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

import { cn } from "@/lib/utils";
import type { NavGroup } from "@/lib/header-nav-config";
import { ThemeToggle } from "./theme-toggle";

interface MobileMenuOverlayProps {
  isOpen: boolean;
  onClose: () => void;
  navGroups: NavGroup[];
  currentPath: string;
  role?: "admin" | "user" | null;
  userName?: string | null;
}

export function MobileMenuOverlay({
  isOpen,
  onClose,
  navGroups,
  currentPath,
  role,
  userName,
}: MobileMenuOverlayProps) {
  const router = useRouter();
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  // Reset expanded groups when menu opens
  useEffect(() => {
    if (isOpen) {
      setExpandedGroups(new Set());
    }
  }, [isOpen]);

  // Lock body scroll when drawer is open
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

  // Escape key handler
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

  // Handle link click
  const handleLinkClick = (href: string) => {
    onClose();
    router.push(href);
  };

  // Toggle group expansion
  const toggleGroup = (groupId: string) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(groupId)) {
        next.delete(groupId);
      } else {
        next.add(groupId);
      }
      return next;
    });
  };

  // Handle logout
  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    window.location.href = "/login";
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-50 bg-black/30"
            aria-hidden="true"
            onClick={onClose}
          />

          {/* Drawer */}
          <motion.div
            initial={{ x: "-100%" }}
            animate={{ x: 0 }}
            exit={{ x: "-100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="fixed left-0 top-0 bottom-0 z-50 w-[320px] max-w-sm bg-background border-r border-border shadow-xl flex flex-col"
            role="dialog"
            aria-modal="true"
            aria-label="Menu điều hướng"
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-border px-4 py-3 shrink-0">
              <div className="flex flex-col">
                <span className="text-base font-semibold">Menu</span>
                {userName && (
                  <span className="text-xs text-muted-foreground">
                    {userName}
                    {role && (
                      <span className="ml-1.5 text-[10px] text-muted-foreground/60">
                        ({role === "admin" ? "Quản trị viên" : "Nhân viên"})
                      </span>
                    )}
                  </span>
                )}
              </div>
              <button
                onClick={onClose}
                className="flex h-10 w-10 items-center justify-center rounded-md hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                aria-label="Đóng menu"
              >
                <X className="h-5 w-5" aria-hidden="true" />
              </button>
            </div>

            {/* Navigation groups — scrollable */}
            <nav
              className="flex-1 overflow-y-auto px-3 py-4"
              aria-label="Điều hướng chính"
            >
              {navGroups.map((group) => {
                const isExpanded = expandedGroups.has(group.id);

                return (
                  <div key={group.id} className="mb-2">
                    {/* Group header — clickable to toggle */}
                    <button
                      type="button"
                      onClick={() => toggleGroup(group.id)}
                      className={cn(
                        "flex w-full items-center justify-between rounded-md px-3 py-2.5 text-sm font-medium transition-colors",
                        "hover:bg-accent/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                      )}
                      aria-expanded={isExpanded}
                    >
                      <span className="flex items-center gap-2">
                        {group.icon && (
                          <group.icon
                            className="h-4 w-4 text-muted-foreground"
                            aria-hidden="true"
                          />
                        )}
                        <span>{group.label}</span>
                      </span>
                      <motion.span
                        aria-hidden="true"
                        animate={{ rotate: isExpanded ? 180 : 0 }}
                        transition={{ duration: 0.2, ease: "easeOut" }}
                      >
                        <ChevronDown className="h-4 w-4 text-muted-foreground" />
                      </motion.span>
                    </button>

                    {/* Collapsible sub-links */}
                    <AnimatePresence initial={false}>
                      {isExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2, ease: "easeInOut" }}
                          className="overflow-hidden"
                        >
                          <div className="ml-2 mt-1 space-y-0.5 border-l border-border/40 pl-3">
                            {group.links.map((link) => {
                              const isLinkActive = currentPath === link.href;

                              return (
                                <Link
                                  key={link.href}
                                  href={link.href}
                                  onClick={(e) => {
                                    e.preventDefault();
                                    handleLinkClick(link.href);
                                  }}
                                  className={cn(
                                    "flex min-h-[40px] items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                                    isLinkActive
                                      ? "bg-accent/10 text-accent border-l-2 border-primary/50 -ml-[1px]"
                                      : "text-foreground/80 hover:bg-accent/5 hover:text-foreground",
                                  )}
                                  aria-current={isLinkActive ? "page" : undefined}
                                >
                                  {link.icon && (
                                    <link.icon
                                      className="h-4 w-4 shrink-0"
                                      aria-hidden="true"
                                    />
                                  )}
                                  <span>{link.label}</span>
                                </Link>
                              );
                            })}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                );
              })}
            </nav>

            {/* Footer */}
            <div className="shrink-0 border-t border-border px-4 py-3 flex items-center justify-between">
              <ThemeToggle />
              <button
                type="button"
                onClick={handleLogout}
                className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-destructive transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded-md px-2 py-1"
              >
                <LogOut className="h-4 w-4" />
                <span>Đăng xuất</span>
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
