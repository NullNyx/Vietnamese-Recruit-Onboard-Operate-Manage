"use client";

import { ClipboardList, FileEdit, Clock } from "lucide-react";

export default function EmployeeRequestsPage() {
  return (
    <div className="space-y-6 max-w-[900px]">
      <div className="space-y-1">
        <h1 className="text-[24px] font-semibold tracking-[-0.3px] text-[#f7f8f8]">
          Yêu cầu của tôi
        </h1>
        <p className="text-[14px] text-[#8a8f98]">
          Đơn nghỉ phép, tăng ca và các yêu cầu khác
        </p>
      </div>

      {/* Request type cards — non-interactive placeholders */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="flex items-center gap-4 rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#5e6ad2]/10">
            <FileEdit className="h-5 w-5 text-[#5e6ad2]" />
          </div>
          <div>
            <h3 className="text-[14px] font-medium text-[#f7f8f8]">
              Đơn nghỉ phép
            </h3>
            <p className="text-[12px] text-[#8a8f98]">
              Gửi yêu cầu nghỉ phép năm, nghỉ không lương, nghỉ bệnh
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#f59e0b]/10">
            <Clock className="h-5 w-5 text-[#f59e0b]" />
          </div>
          <div>
            <h3 className="text-[14px] font-medium text-[#f7f8f8]">
              Đơn tăng ca
            </h3>
            <p className="text-[12px] text-[#8a8f98]">
              Đăng ký tăng ca và xác nhận giờ làm thêm
            </p>
          </div>
        </div>
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
