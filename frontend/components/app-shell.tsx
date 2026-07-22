/**
 * Shared app shell — single layout used by both Dashboard and Employee route groups.
 *
 * Extracted from app/(dashboard)/layout.tsx and app/(employee)/layout.tsx
 * (~85% duplicate). All visual differences are parameterized as props.
 *
 * Follows AI Studio design system: slate/indigo, rounded-full pill, Inter + JetBrains Mono.
 *
 * v2: Added nav grouping (navGroups), mobile hamburger menu.
 * v3: i18n — replaced hardcoded text with useTranslations.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { useRouter } from '@/i18n/navigation';
import { Sparkles, LogOut, Menu, X } from 'lucide-react';
import { useSession } from '@/lib/auth/session';
import { useTranslations } from 'next-intl';
import LocaleSwitcher from '@/components/locale-switcher';

export interface NavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

export interface NavGroup {
  /** Section header label, e.g. "Tuyển dụng" */
  label: string;
  items: NavItem[];
}

export interface AppShellProps {
  /** Role label shown in the top bar, e.g. "/ Quản trị" or "/ Nhân viên" */
  roleLabel: string;
  /** Section heading above the sidebar nav, e.g. "Hệ Thống HR" or "Trang Nhân Viên (ESS)" */
  sidebarSectionLabel: string;
  /** Navigation items rendered in the sidebar (flat style — backward compat) */
  navItems?: NavItem[];
  /** Navigation groups with section headers (preferred over navItems) */
  navGroups?: NavGroup[];
  /** Sidebar badge: the org/user card rendered above the nav section */
  sidebarBadge?: React.ReactNode;
  /** Where the AI Assistant button links to, e.g. "/assistant" or "/employee/assistant" */
  assistantHref: string;
  /** Default fallback for user display name */
  userDisplayNameFallback: string;
  /** Optional extra button in the top bar (e.g. settings gear icon) */
  topBarExtra?: React.ReactNode;
  children: React.ReactNode;
}

export default function AppShell({
  roleLabel,
  sidebarSectionLabel,
  navItems,
  navGroups,
  sidebarBadge,
  assistantHref,
  userDisplayNameFallback,
  topBarExtra,
  children,
}: AppShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user } = useSession();
  const t = useTranslations('appShell');

  // Mobile sidebar toggle
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Close sidebar on route change (mobile)
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- close sidebar on navigation
    setSidebarOpen(false);
  }, [pathname]);

  const isActive = (href: string) => {
    // Special case for root dashboard
    if (href === '/dashboard') return pathname === '/dashboard' || pathname === '/';
    if (href === '/employee') return pathname === '/employee' || pathname === '/employee/dashboard';
    return pathname.startsWith(href);
  };

  const handleLogout = async () => {
    try {
      await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
    } catch {
      // ignore
    }
    router.replace('/login');
  };

  // Resolve items to render: flat items first, then grouped items
  const groups: NavGroup[] = [
    ...(navItems && navItems.length > 0 ? [{ label: '', items: navItems }] : []),
    ...(navGroups ?? []),
  ];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans flex flex-col selection:bg-indigo-500 selection:text-white">
      {/* Top bar */}
      <header className="bg-white border-b border-slate-200 px-4 py-2 flex items-center justify-between z-50 shadow-sm">
        <div className="flex items-center gap-3">
          {/* Hamburger for mobile */}
          <button
            onClick={() => setSidebarOpen((p) => !p)}
            className="lg:hidden p-1.5 rounded-lg hover:bg-slate-100 text-slate-500 transition-all"
            title={t('menu')}
          >
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>

          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-black tracking-tighter text-sm shadow-md shadow-indigo-100">
            VR
          </div>
          <span className="font-semibold text-sm text-slate-800">{t('brand')}</span>
          <span className="text-[10px] text-slate-400 font-mono hidden sm:inline">
            {roleLabel}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <LocaleSwitcher />
          {topBarExtra}
          <span className="text-xs text-slate-500 font-medium hidden sm:block">
            {user?.name ?? userDisplayNameFallback}
          </span>
          <button
            onClick={handleLogout}
            className="p-1.5 rounded-full hover:bg-rose-50 text-slate-400 hover:text-rose-500 transition-all"
            title={t('logout')}
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </header>

      <div className="flex-1 flex flex-col lg:flex-row relative">
        {/* Mobile overlay */}
        {sidebarOpen && (
          <div
            className="lg:hidden fixed inset-0 bg-black/40 z-40"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Sidebar */}
        <aside
          className={`w-full lg:w-56 bg-white border-r border-slate-200 p-3 shrink-0 space-y-1 shadow-sm overflow-y-auto
            fixed lg:sticky top-[49px] lg:top-0 left-0 bottom-0 z-50 lg:z-auto
            transition-transform lg:transition-none
            ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          `}
        >
          {sidebarBadge && sidebarBadge}

          {sidebarSectionLabel && (
            <div className="text-[9px] font-mono font-bold text-purple-500 px-3 uppercase tracking-wider mb-2">
              {sidebarSectionLabel}
            </div>
          )}

          {groups.map((group, gi) => (
            <div key={gi}>
              {group.label && (
                <div className="text-[9px] font-mono font-bold text-slate-400 px-3 uppercase tracking-wider mb-1 mt-2 first:mt-0">
                  {group.label}
                </div>
              )}
              {group.items.map((item) => (
                <button
                  key={item.href}
                  onClick={() => router.push(item.href)}
                  className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium transition-all ${
                    isActive(item.href)
                      ? 'bg-indigo-50 border border-indigo-100 text-indigo-600 font-semibold shadow-sm shadow-indigo-50/10'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-indigo-600'
                  }`}
                >
                  <item.icon className="w-4 h-4 shrink-0" />
                  <span className="truncate">{item.label}</span>
                </button>
              ))}
            </div>
          ))}

          {/* AI Assistant Button */}
          <div className="pt-3 mt-3 border-t border-slate-100">
            <button
              onClick={() => router.push(assistantHref)}
              className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-xs font-medium bg-gradient-to-r from-indigo-600 to-indigo-500 text-white hover:from-indigo-500 hover:to-indigo-400 shadow-md shadow-indigo-100 transition-all"
            >
              <Sparkles className="w-4 h-4" />
              {t('assistant')}
            </button>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-4 lg:p-6 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
