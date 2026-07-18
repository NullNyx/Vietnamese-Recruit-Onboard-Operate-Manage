'use client';

import React from 'react';
import {
  LayoutDashboard, Inbox, UserCheck, Briefcase, Calendar,
  CheckSquare, Users, Clock, FileText, FileSpreadsheet,
  Mail, Settings, LogOut, Sparkles, FileSearch, BarChart3
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import AppShell from '@/components/app-shell';
import type { NavItem } from '@/components/app-shell';

const navItems: NavItem[] = [
  { href: '/dashboard', label: 'Tổng quan & Metrics', icon: LayoutDashboard },
  { href: '/recruitment/inbox', label: 'Hộp thư Tuyển dụng (Inbox)', icon: Inbox },
  { href: '/recruitment/candidates', label: 'Ứng viên (Candidates)', icon: UserCheck },
  { href: '/recruitment/job-openings', label: 'Vị trí Tuyển dụng', icon: Briefcase },
  { href: '/recruitment/interviews', label: 'Lịch phỏng vấn', icon: Calendar },
  { href: '/recruitment/review', label: 'Review CV (Parse)', icon: FileSearch },
  { href: '/recruitment/metrics', label: 'Metrics Tuyển dụng', icon: BarChart3 },
  { href: '/onboarding', label: 'Onboarding Processes', icon: CheckSquare },
  { href: '/employees', label: 'Danh sách Nhân viên', icon: Users },
  { href: '/attendance', label: 'Chấm công & Allowlist', icon: Clock },
  { href: '/requests', label: 'Yêu cầu Nhân viên', icon: FileText },
  { href: '/payroll/payslips', label: 'Phiếu lương (Payslips)', icon: FileSpreadsheet },
  { href: '/gmail', label: 'Kênh Gmail', icon: Mail },
  { href: '/settings', label: 'Cấu hình AI & Hệ thống', icon: Settings },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  return (
    <AppShell
      roleLabel="/ Quản trị"
      sidebarSectionLabel="Hệ Thống HR"
      navItems={navItems}
      assistantHref="/assistant"
      userDisplayNameFallback="HR Admin"
      topBarExtra={
        <button
          onClick={() => router.push('/settings')}
          className="p-1.5 rounded-full hover:bg-slate-100 text-slate-500 hover:text-slate-700 transition-all"
          title="Cấu hình"
        >
          <Sparkles className="w-4 h-4" />
        </button>
      }
      
    >
      {children}
    </AppShell>
  );
}
