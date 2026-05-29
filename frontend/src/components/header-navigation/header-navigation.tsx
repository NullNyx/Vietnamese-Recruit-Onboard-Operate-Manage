"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Menu } from "lucide-react";

import { cn } from "@/lib/utils";
import { useCurrentUser } from "@/hooks/use-current-user";
import { useActiveNavItem } from "@/hooks/use-active-nav-item";
import { adminNavConfig } from "@/lib/admin-nav-config";
import { essNavConfig } from "@/lib/ess-nav-config";
import type { HeaderNavConfig } from "@/lib/header-nav-config";
import { CommandBar } from "@/components/command-bar";

import { NavItemTrigger } from "./nav-item-trigger";
import { MegaMenuPanel } from "./mega-menu-panel";
import { HeaderUtilities } from "./header-utilities";
import { MobileMenuOverlay } from "./mobile-menu-overlay";

interface HeaderNavigationProps {
  className?: string;
}

export function HeaderNavigation({ className }: HeaderNavigationProps) {
  const { user, loading, error } = useCurrentUser();
  const pathname = usePathname();
  const router = useRouter();

  // Determine if role is valid
  const isValidRole = user?.role === "admin" || user?.role === "user";

  // Select config based on user role
  const config: HeaderNavConfig =
    user?.role === "admin" ? adminNavConfig : essNavConfig;

  // Active state from hook
  const { activeGroupId, activeSubLinkHref } = useActiveNavItem(
    config.groups,
    pathname,
  );

  // Menu state: at most one open at a time
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [commandBarOpen, setCommandBarOpen] = useState(false);

  // Refs for click-outside detection and focus management
  const navContainerRef = useRef<HTMLElement>(null);
  const triggerRefs = useRef<Map<string, HTMLButtonElement>>(new Map());

  // Toggle menu: open if closed, close if open (single-open invariant)
  const handleToggle = useCallback((groupId: string) => {
    setOpenMenuId((prev) => (prev === groupId ? null : groupId));
  }, []);

  // Hover intent: open the hovered group's menu
  const handleHoverIntent = useCallback((groupId: string) => {
    setOpenMenuId(groupId);
  }, []);

  // Link click: close menu and navigate
  const handleLinkClick = useCallback(
    (href: string) => {
      setOpenMenuId(null);
      router.push(href);
    },
    [router],
  );

  // Close menu and return focus to trigger
  const closeMenuAndFocusTrigger = useCallback(() => {
    if (openMenuId) {
      const trigger = triggerRefs.current.get(openMenuId);
      setOpenMenuId(null);
      // Return focus to the trigger after state update
      setTimeout(() => trigger?.focus(), 0);
    }
  }, [openMenuId]);

  // Click-outside handler
  useEffect(() => {
    if (!openMenuId) return;

    function handleClickOutside(event: MouseEvent) {
      const target = event.target as Node;
      if (
        navContainerRef.current &&
        !navContainerRef.current.contains(target)
      ) {
        setOpenMenuId(null);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [openMenuId]);

  // Escape key handler
  useEffect(() => {
    if (!openMenuId) return;

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        closeMenuAndFocusTrigger();
      }
    }

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [openMenuId, closeMenuAndFocusTrigger]);

  // Ctrl+K / ⌘K to open CommandBar
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key === "k") {
        event.preventDefault();
        setCommandBarOpen((prev) => !prev);
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Lateral ArrowLeft/ArrowRight keyboard navigation between groups
  useEffect(() => {
    if (!openMenuId) return;

    function handleArrowKeys(event: KeyboardEvent) {
      if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;

      // Only handle if focus is on a trigger or within the nav container
      const activeElement = document.activeElement;
      if (!navContainerRef.current?.contains(activeElement as Node)) {
        return;
      }

      event.preventDefault();

      const groups = config.groups;
      const currentIndex = groups.findIndex((g) => g.id === openMenuId);
      if (currentIndex === -1) return;

      const M = groups.length;
      let nextIndex: number;

      if (event.key === "ArrowRight") {
        nextIndex = (currentIndex + 1) % M;
      } else {
        nextIndex = (currentIndex - 1 + M) % M;
      }

      const nextGroup = groups[nextIndex];
      setOpenMenuId(nextGroup.id);

      // Focus the next trigger
      setTimeout(() => {
        const nextTrigger = triggerRefs.current.get(nextGroup.id);
        nextTrigger?.focus();
      }, 0);
    }

    document.addEventListener("keydown", handleArrowKeys);
    return () => document.removeEventListener("keydown", handleArrowKeys);
  }, [openMenuId, config.groups]);

  // Close menus on route change
  useEffect(() => {
    setOpenMenuId(null);
    setMobileMenuOpen(false);
  }, [pathname]);

  // Redirect to /login when unauthenticated or role is invalid (client-side fallback)
  useEffect(() => {
    if (!loading && (!user || !isValidRole)) {
      router.push("/login");
    }
  }, [loading, user, isValidRole, router]);

  // Handle Enter/Space on trigger: open menu and focus first link
  const handleTriggerKeyDown = useCallback(
    (event: React.KeyboardEvent, groupId: string) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        setOpenMenuId(groupId);
        // Focus first link in the mega menu panel after it renders
        setTimeout(() => {
          const panel = navContainerRef.current?.querySelector(
            `[aria-label="${config.groups.find((g) => g.id === groupId)?.label} submenu"] a`,
          );
          (panel as HTMLElement)?.focus();
        }, 0);
      }
    },
    [config.groups],
  );

  // Loading state
  if (loading) {
    return (
      <header
        className={cn(
          "fixed top-0 left-0 right-0 z-40 h-14 border-b bg-background",
          className,
        )}
      >
        <div className="flex h-full items-center px-4">
          <div className="h-5 w-24 animate-pulse rounded bg-muted" />
        </div>
      </header>
    );
  }

  // Error state
  if (error) {
    return (
      <header
        className={cn(
          "fixed top-0 left-0 right-0 z-40 h-14 border-b bg-background",
          className,
        )}
      >
        <div className="flex h-full items-center px-4">
          <p className="text-sm text-destructive">
            Không thể tải thông tin người dùng
          </p>
        </div>
      </header>
    );
  }

  // Unauthenticated or invalid role state — render minimal header, redirect handled by effect above
  if (!user || !isValidRole) {
    return (
      <header
        className={cn(
          "fixed top-0 left-0 right-0 z-40 h-14 border-b bg-background",
          className,
        )}
      />
    );
  }

  return (
    <>
      <header
        className={cn(
          "fixed top-0 left-0 right-0 z-40 h-14 border-b bg-background",
          className,
        )}
      >
        <nav
          ref={navContainerRef}
          className="flex h-full items-center px-4"
          role="navigation"
          aria-label="Điều hướng chính"
        >
          {/* Logo */}
          <Link
            href={config.logo.href}
            className="mr-6 flex items-center gap-2 text-sm font-bold tracking-tight"
          >
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-primary-foreground text-xs font-bold">
              V
            </span>
            <span className="hidden sm:inline">{config.logo.label}</span>
          </Link>

          {/* Desktop navigation items — hidden on mobile */}
          <div className="hidden md:flex md:items-center md:gap-1">
            {config.groups.map((group) => (
              <div key={group.id} className="relative">
                <div
                  ref={(el) => {
                    // Capture the button inside this wrapper
                    const btn = el?.querySelector("button");
                    if (btn) {
                      triggerRefs.current.set(
                        group.id,
                        btn as HTMLButtonElement,
                      );
                    }
                  }}
                  onKeyDown={(e) => handleTriggerKeyDown(e, group.id)}
                >
                  <NavItemTrigger
                    group={group}
                    isActive={activeGroupId === group.id}
                    isOpen={openMenuId === group.id}
                    onToggle={() => handleToggle(group.id)}
                    onHoverIntent={() => handleHoverIntent(group.id)}
                  />
                </div>
                <MegaMenuPanel
                  group={group}
                  isOpen={openMenuId === group.id}
                  onLinkClick={handleLinkClick}
                  activeSubLinkHref={activeSubLinkHref}
                />
              </div>
            ))}
          </div>

          {/* Spacer */}
          <div className="flex-1" />

          {/* Header utilities (search, notifications, account) */}
          <HeaderUtilities
            onSearchClick={() => setCommandBarOpen(true)}
            user={user}
          />

          {/* Hamburger toggle — visible on mobile only */}
          <button
            type="button"
            className="ml-2 inline-flex h-9 w-9 items-center justify-center rounded-md hover:bg-accent md:hidden"
            onClick={() => setMobileMenuOpen(true)}
            aria-label="Mở menu"
            aria-expanded={mobileMenuOpen}
          >
            <Menu className="h-5 w-5" />
          </button>
        </nav>
      </header>

      {/* Mobile menu overlay */}
      <MobileMenuOverlay
        isOpen={mobileMenuOpen}
        onClose={() => setMobileMenuOpen(false)}
        navGroups={config.groups}
        currentPath={pathname}
      />

      {/* Command bar */}
      <CommandBar open={commandBarOpen} onOpenChange={setCommandBarOpen} />
    </>
  );
}
