"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Menu } from "lucide-react";
import { useScroll, useMotionValueEvent } from "motion/react";

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
import { HeaderBreadcrumbs } from "./header-breadcrumbs";

interface HeaderNavigationProps {
  className?: string;
}

function readE2EUserOverride() {
  if (typeof window === "undefined") return null;
  return (window as typeof window & {
    __VROOM_HR_E2E_CURRENT_USER__?: { role?: string } | null;
  }).__VROOM_HR_E2E_CURRENT_USER__ ?? null;
}

export function HeaderNavigation({ className }: HeaderNavigationProps) {
  const { user, loading, error } = useCurrentUser();
  const e2eUser = readE2EUserOverride();
  const activeUser = (e2eUser as typeof user | null) ?? user;
  const activeLoading = e2eUser ? false : loading;
  const activeError = error;
  const pathname = usePathname();
  const router = useRouter();

  // Scroll shadow detection
  const { scrollY } = useScroll();
  const [isScrolled, setIsScrolled] = useState(false);

  useMotionValueEvent(scrollY, "change", (latest) => {
    setIsScrolled(latest > 0);
  });

  // Determine if role is valid
  const isValidRole = activeUser?.role === "admin" || activeUser?.role === "user";

  // Select config based on user role
  const config: HeaderNavConfig =
    activeUser?.role === "admin" ? adminNavConfig : essNavConfig;

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
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
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
    if (!activeLoading && (!activeUser || !isValidRole)) {
      router.push("/login");
    }
  }, [activeLoading, activeUser, isValidRole, router]);

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

  // Loading state — full skeleton shimmer
  if (activeLoading) {
    return (
      <header
        className={cn(
          "fixed top-0 left-0 right-0 z-40 h-14 border-b bg-background",
          className,
        )}
      >
        <div className="flex h-full items-center px-6 gap-4 animate-pulse">
          {/* Logo skeleton */}
          <div className="h-7 w-7 rounded-md bg-muted" />
          <div className="hidden sm:block h-4 w-20 rounded bg-muted" />
          {/* Nav items skeleton */}
          <div className="hidden md:flex md:items-center md:gap-3 ml-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-4 w-16 rounded bg-muted" />
            ))}
          </div>
          {/* Spacer */}
          <div className="flex-1" />
          {/* Utilities skeleton */}
          <div className="flex items-center gap-2">
            <div className="h-8 w-24 rounded-lg bg-muted" />
            <div className="h-8 w-8 rounded-md bg-muted" />
            <div className="h-8 w-8 rounded-md bg-muted" />
            <div className="h-8 w-8 rounded-full bg-muted" />
          </div>
        </div>
      </header>
    );
  }

  // Error state
  if (activeError) {
    return (
      <header
        className={cn(
          "fixed top-0 left-0 right-0 z-40 h-14 border-b bg-background",
          className,
        )}
      >
        <div className="flex h-full items-center px-6">
          <p className="text-sm text-destructive">
            Không thể tải thông tin người dùng
          </p>
        </div>
      </header>
    );
  }

  // Unauthenticated or invalid role state — render minimal header, redirect handled by effect above
  if (!activeUser || !isValidRole) {
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
          "fixed top-0 left-0 right-0 z-40 h-14 transition-shadow duration-200",
          "border-b bg-background/85 backdrop-blur-md",
          isScrolled && "shadow-sm",
          className,
        )}
      >
        <nav
          ref={navContainerRef}
          className="flex h-full items-center px-6 gap-3"
          role="navigation"
          aria-label="Điều hướng chính"
        >
          {/* Logo */}
          <Link
            href={config.logo.href}
            className="flex items-center gap-2 text-sm font-bold tracking-tight shrink-0"
          >
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-gradient-to-br from-primary to-primary/80 text-primary-foreground text-xs font-bold shadow-sm">
              V
            </span>
            <span className="hidden sm:inline">{config.logo.label}</span>
          </Link>

          {/* Breadcrumbs (desktop/tablet only) */}
          <HeaderBreadcrumbs />

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
            user={activeUser}
          />

          {/* Hamburger toggle — visible on mobile only */}
          <button
            type="button"
            className="ml-2 inline-flex h-10 w-10 items-center justify-center rounded-md hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 md:hidden"
            onClick={() => setMobileMenuOpen(true)}
            aria-label="Mở menu"
            aria-expanded={mobileMenuOpen}
          >
            <Menu className="h-5 w-5" />
          </button>
        </nav>
      </header>

      {/* Mobile menu overlay — slide-in drawer */}
      <MobileMenuOverlay
        isOpen={mobileMenuOpen}
        onClose={() => setMobileMenuOpen(false)}
        navGroups={config.groups}
        currentPath={pathname}
        role={activeUser?.role}
        userName={activeUser?.name}
      />

      {/* Command bar */}
      <CommandBar open={commandBarOpen} onOpenChange={setCommandBarOpen} />
    </>
  );
}
