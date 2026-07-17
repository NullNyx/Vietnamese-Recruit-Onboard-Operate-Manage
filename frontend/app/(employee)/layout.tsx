'use client';

import React from 'react';
import {
  LayoutDashboard, Clock, FileText, FileSpreadsheet,
  User,
} from 'lucide-react';
import { useSession } from '@/lib/auth/session';
import AppShell from '@/components/app-shell';
import type { NavItem } from '@/components/app-shell';

const navItems: NavItem[] = [
  { href: '/employee', label: 'Bảng cá nhân (ESS)', icon: LayoutDashboard },
  { href: '/employee/attendance', label: 'Chấm công', icon: Clock },
  { href: '/employee/requests', label: 'Yêu cầu của tôi', icon: FileText },
  { href: '/employee/payslips', label: 'Phiếu lương', icon: FileSpreadsheet },
];

export default function EmployeeLayout({ children }: { children: React.ReactNode }) {
  const { user } = useSession();

  return (
    <AppShell
      roleLabel="/ Nhân viên"
      sidebarSectionLabel="Trang Nhân Viên (ESS)"
      navItems={navItems}
      assistantHref="/employee/assistant"
      userDisplayNameFallback="Nhân viên"
      sidebarBadge={
        <div className="p-2.5 mb-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-xs">
            <User className="w-4 h-4" />
          </div>
          <div className="overflow-hidden">
            <span className="font-semibold text-[11px] text-slate-800 block truncate">
              {user?.name ?? 'Nhân viên'}
            </span>
            <span className="text-[9px] text-slate-400 block truncate">
              {user?.email ?? ''}
            </span>
          </div>
        </div>
      }
    >
      {children}
    </AppShell>
  );
}
