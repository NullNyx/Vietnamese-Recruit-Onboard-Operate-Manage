'use client';

import { useAuthGuard, useSession } from '@/lib/auth/session';
import { User, Clock, FileText, FileSpreadsheet, FolderOpen, Sparkles } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function EmployeeDashboardPage() {
  useAuthGuard({ requireAuth: true, requireEmployee: true });
  const { user } = useSession();
  const router = useRouter();

  const cards = [
    { href: '/employee/profile', icon: User, title: 'Hồ sơ của tôi', desc: 'Xem và cập nhật thông tin liên lạc.' },
    { href: '/employee/documents', icon: FolderOpen, title: 'Tài liệu của tôi', desc: 'Tải lên / tải xuống tài liệu cá nhân.' },
    { href: '/employee/attendance', icon: Clock, title: 'Chấm công', desc: 'Check-in/check-out hôm nay và lịch sử.' },
    { href: '/employee/requests', icon: FileText, title: 'Yêu cầu của tôi', desc: 'Gửi và theo dõi yêu cầu nghỉ phép, tăng ca.' },
    { href: '/employee/payslips', icon: FileSpreadsheet, title: 'Phiếu lương', desc: 'Xem phiếu lương đã phát hành.' },
    { href: '/employee/assistant', icon: Sparkles, title: 'Trợ lý AI', desc: 'Trợ lý hội thoại dành cho nhân viên.' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-2 text-indigo-600 mb-1">
          <User className="w-5 h-5" />
          <h1 className="text-xl font-bold text-slate-900">Bảng cá nhân (ESS)</h1>
        </div>
        <p className="text-sm text-slate-500">
          Chào {user?.name ?? 'bạn'} — Employee Self-Service. Chọn một mục bên dưới để bắt đầu.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {cards.map((card) => (
          <button
            key={card.href}
            onClick={() => router.push(card.href)}
            className="p-5 text-left bg-white rounded-2xl border border-slate-200 shadow-sm shadow-slate-100 hover:border-indigo-200 hover:shadow-indigo-100 transition-all group"
          >
            <div className="p-2 bg-indigo-50 rounded-lg w-fit mb-3 group-hover:bg-indigo-100 transition-all">
              <card.icon className="w-5 h-5 text-indigo-600" />
            </div>
            <h3 className="font-bold text-sm text-slate-900 mb-1">{card.title}</h3>
            <p className="text-xs text-slate-500 leading-relaxed">{card.desc}</p>
          </button>
        ))}
      </div>
    </div>
  );
}