/**
 * Shared app shell — single layout used by both Dashboard and Employee route groups.
 *
 * Extracted from app/(dashboard)/layout.tsx and app/(employee)/layout.tsx
 * (~85% duplicate). All visual differences are parameterized as props.
 *
 * Follows AI Studio design system: slate/indigo, rounded-full pill, Inter + JetBrains Mono.
 */

'use client';

import React from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { Sparkles, LogOut } from 'lucide-react';
import { useSession } from '@/lib/auth/session';

export interface NavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

export interface AppShellProps {
  /** Role label shown in the top bar, e.g. "/ Quản trị" or "/ Nhân viên" */
  roleLabel: string;
  /** Section heading above the sidebar nav, e.g. "Hệ Thống HR" or "Trang Nhân Viên (ESS)" */
  sidebarSectionLabel: string;
  /** Navigation items rendered in the sidebar */
  navItems: NavItem[];
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
  sidebarBadge,
  assistantHref,
  userDisplayNameFallback,
  topBarExtra,
  children,
}: AppShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user } = useSession();

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

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans flex flex-col selection:bg-indigo-500 selection:text-white">
      {/* Top bar */}
      <header className="bg-white border-b border-slate-200 px-4 py-2 flex items-center justify-between z-50 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-black tracking-tighter text-sm shadow-md shadow-indigo-100">
            VR
          </div>
          <span className="font-semibold text-sm text-slate-800">Vroom HR</span>
          <span className="text-[10px] text-slate-400 font-mono hidden sm:inline">
            {roleLabel}
          </span>
        </div>
        <div className="flex items-center gap-3">
          {topBarExtra}
          <span className="text-xs text-slate-500 font-medium hidden sm:block">
            {user?.name ?? userDisplayNameFallback}
          </span>
          <button
            onClick={handleLogout}
            className="p-1.5 rounded-full hover:bg-rose-50 text-slate-400 hover:text-rose-500 transition-all"
            title="Đăng xuất"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </header>

      <div className="flex-1 flex flex-col lg:flex-row">
        {/* Sidebar */}
        <aside className="w-full lg:w-56 bg-white border-r border-slate-200 p-3 shrink-0 space-y-1 shadow-sm overflow-y-auto">
          {sidebarBadge && sidebarBadge}

          <div className="text-[9px] font-mono font-bold text-slate-400 px-3 uppercase tracking-wider mb-1">
            {sidebarSectionLabel}
          </div>

          {navItems.map((item) => (
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

          {/* AI Assistant Button */}
          <div className="pt-3 mt-3 border-t border-slate-100">
            <button
              onClick={() => router.push(assistantHref)}
              className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-xs font-medium bg-gradient-to-r from-indigo-600 to-indigo-500 text-white hover:from-indigo-500 hover:to-indigo-400 shadow-md shadow-indigo-100 transition-all"
            >
              <Sparkles className="w-4 h-4" />
              Trợ lý AI
            </button>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-4 lg:p-6 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
