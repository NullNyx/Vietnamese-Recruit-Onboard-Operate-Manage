"use client";

import { FileText, User, Sparkles } from "lucide-react";
import Link from "next/link";

export default function EmployeeDashboardPage() {
  return (
    <div className="space-y-8 max-w-[900px]">
      <div className="space-y-1">
        <h1 className="text-[24px] font-semibold tracking-[-0.3px] text-foreground">
          Tổng quan
        </h1>
        <p className="text-[14px] text-muted-foreground">
          Chào mừng bạn đến với Employee Self-Service Portal
        </p>
      </div>

      {/* Quick links */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Link
          href="/employee/profile"
          className="group flex items-center gap-4 rounded-xl border border-border bg-card p-5 transition-all hover:bg-accent"
         >
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#e4f222]/10 dark:bg-[#e4f222]/20">
            <User className="h-5 w-5 text-[#b8c21b] dark:text-[#e4f222]" />
          </div>
          <div>
            <h3 className="text-[14px] font-medium text-foreground">
              Hồ sơ cá nhân
            </h3>
            <p className="text-[12px] text-muted-foreground">
              Xem và cập nhật thông tin
            </p>
          </div>
        </Link>

        <Link
          href="/employee/documents"
          className="group flex items-center gap-4 rounded-xl border border-border bg-card p-5 transition-all hover:bg-accent"
        >
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#5e6ad2]/10 dark:bg-[#5e6ad2]/20">
            <FileText className="h-5 w-5 text-[#4a54a8] dark:text-[#5e6ad2]" />
          </div>
          <div>
            <h3 className="text-[14px] font-medium text-foreground">Tài liệu</h3>
            <p className="text-[12px] text-muted-foreground">Kho tài liệu cá nhân</p>
          </div>
        </Link>
      </div>

      {/* AI Assistant hint */}
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="flex items-center gap-3">
          <Sparkles className="h-5 w-5 text-[#b8c21b] dark:text-[#e4f222]" />
          <div>
            <h3 className="text-[14px] font-medium text-foreground">
              AI Assistant
            </h3>
            <p className="text-[12px] text-muted-foreground">
              Các tính năng AI sẽ được tích hợp trong phiên bản tiếp theo — bao
              gồm smart notifications, document analysis, và personalized
              insights.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
