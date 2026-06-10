"use client";

import { ClipboardList, FileEdit, Clock, Plus } from "lucide-react";
import Link from "next/link";

export default function EmployeeRequestsPage() {
  return (
    <div className="space-y-6 max-w-[900px]">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h1 className="text-[24px] font-semibold tracking-[-0.3px] text-[#f7f8f8]">
            Yêu cầu của tôi
          </h1>
          <p className="text-[14px] text-[#8a8f98]">
            Đơn nghỉ phép, tăng ca và các yêu cầu khác
          </p>
        </div>
        <Link
          href="/employee/requests/new"
          className="inline-flex items-center gap-2 rounded-lg bg-[#e4f222] px-4 py-2 text-sm font-medium text-black transition-opacity hover:opacity-90"
        >
          <Plus className="h-4 w-4" />
          Tạo yêu cầu
        </Link>
      </div>

      {/* Request type quick-actions */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <RequestTypeCard
          icon={FileEdit}
          iconBg="bg-[#5e6ad2]/10"
          iconColor="text-[#5e6ad2]"
          title="Đơn nghỉ phép"
          description="Gửi yêu cầu nghỉ phép năm, nghỉ không lương, nghỉ bệnh"
        />
        <RequestTypeCard
          icon={Clock}
          iconBg="bg-[#f59e0b]/10"
          iconColor="text-[#f59e0b]"
          title="Đơn tăng ca"
          description="Đăng ký tăng ca và xác nhận giờ làm thêm"
        />
      </div>

      {/* Empty state */}
      <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-12 text-center">
        <ClipboardList className="mx-auto h-10 w-10 text-[#8a8f98]" />
        <h3 className="mt-4 text-[14px] font-medium text-[#f7f8f8]">
          Chưa có yêu cầu nào
        </h3>
        <p className="mt-1 text-[12px] text-[#8a8f98]">
          Các yêu cầu của bạn sẽ xuất hiện ở đây sau khi được gửi.
        </p>
      </div>
    </div>
  );
}

function RequestTypeCard({
  icon: Icon,
  iconBg,
  iconColor,
  title,
  description,
}: {
  icon: React.ComponentType<{ className?: string }>;
  iconBg: string;
  iconColor: string;
  title: string;
  description: string;
}) {
  return (
    <button
      type="button"
      className="group flex items-center gap-4 rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 text-left transition-all hover:border-white/[0.1] hover:bg-white/[0.04]"
    >
      <div
        className={`flex h-10 w-10 items-center justify-center rounded-lg ${iconBg}`}
      >
        <Icon className={`h-5 w-5 ${iconColor}`} />
      </div>
      <div>
        <h3 className="text-[14px] font-medium text-[#f7f8f8]">{title}</h3>
        <p className="text-[12px] text-[#8a8f98]">{description}</p>
      </div>
    </button>
  );
}
