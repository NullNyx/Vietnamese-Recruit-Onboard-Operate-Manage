'use client';

import React from 'react';
import { usePathname, useRouter } from 'next/navigation';
import {
  LayoutDashboard, Clock, FileText, FileSpreadsheet,
  User, LogOut, Sparkles
} from 'lucide-react';
import { useSession } from '@/lib/auth/session';

const navItems = [
  { href: '/employee', label: 'Bảng cá nhân (ESS)', icon: LayoutDashboard },
  { href: '/employee/attendance', label: 'Chấm công', icon: Clock },
  { href: '/employee/requests', label: 'Yêu cầu của tôi', icon: FileText },
  { href: '/employee/payslips', label: 'Phiếu lương', icon: FileSpreadsheet },
];

export default function EmployeeLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user } = useSession();

  const isActive = (href: string) => {
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
          <span className="text-[10px] text-slate-400 font-mono hidden sm:inline">/ Nhân viên</span>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push('/employee/assistant')}
            className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500 hover:text-slate-700 transition-all"
            title="Trợ lý AI"
          >
            <Sparkles className="w-4 h-4" />
          </button>
          <span className="text-xs text-slate-500 font-medium hidden sm:block">
            {user?.name ?? 'Nhân viên'}
          </span>
          <button
            onClick={handleLogout}
            className="p-1.5 rounded-lg hover:bg-rose-50 text-slate-400 hover:text-rose-500 transition-all"
            title="Đăng xuất"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </header>

      <div className="flex-1 flex flex-col lg:flex-row">
        {/* Sidebar */}
        <aside className="w-full lg:w-56 bg-white border-r border-slate-200 p-3 shrink-0 space-y-1 shadow-sm overflow-y-auto">
          {/* User Badge */}
          <div className="p-2.5 mb-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-xs">
              <User className="w-4 h-4" />
            </div>
            <div className="overflow-hidden">
              <span className="font-semibold text-[11px] text-slate-800 block truncate">{user?.name ?? 'Nhân viên'}</span>
              <span className="text-[9px] text-slate-400 block truncate">{user?.email ?? ''}</span>
            </div>
          </div>

          <div className="text-[9px] font-mono font-bold text-slate-400 px-3 uppercase tracking-wider mb-1">
            Trang Nhân Viên (ESS)
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
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-4 lg:p-6 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
