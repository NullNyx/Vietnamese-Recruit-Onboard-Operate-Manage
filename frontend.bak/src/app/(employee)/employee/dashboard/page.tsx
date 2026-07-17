"use client";

import { useEffect, useState } from "react";
import {
  DollarSign,
  FileText,
  User,
      Clock,
      ClipboardList,
      LogIn,
      Loader2,
} from "lucide-react";
import Link from "next/link";

export default function EmployeeDashboardPage() {
  const [todayState, setTodayState] = useState<
    "loading" | "checked-in" | "empty" | "completed" | "error"
  >("loading");
  const [todayRecord, setTodayRecord] = useState<{
    check_in_at: string | null;
    check_out_at: string | null;
  } | null>(null);

  useEffect(() => {
    fetchToday();
  }, []);

      return (
        <div className="animate-fade-in space-y-8 max-w-[900px]">
          <div className="fade-in-section space-y-1">
            <h1 className="text-[24px] font-semibold tracking-[-0.3px] text-foreground">
              Tổng quan
            </h1>
            <p className="text-[14px] text-muted-foreground">
              Chào mừng bạn đến với Employee Self-Service
            </p>
          </div>

          {/* Quick actions — 2x2 on desktop, stack on mobile */}
          <div className="fade-in-section grid grid-cols-1 gap-4 sm:grid-cols-2">
            <QuickActionLink
              href="/employee/profile"
              icon={User}
              iconBg="bg-primary/10"
              iconColor="text-primary"
              title="Hồ sơ cá nhân"
              description="Xem và cập nhật thông tin"
            />
            <QuickActionLink
              href="/employee/documents"
              icon={FileText}
              iconBg="bg-secondary/10"
              iconColor="text-secondary"
              title="Tài liệu"
              description="Kho tài liệu cá nhân"
            />
            <QuickActionLink
              href="/employee/attendance"
              icon={Clock}
              iconBg="bg-accent/10"
              iconColor="text-accent"
              title="Chấm công"
              description="Check-in/check-out và lịch sử"
            />
            <QuickActionLink
              href="/employee/requests"
              icon={ClipboardList}
              iconBg="bg-success/10"
              iconColor="text-success"
              title="Yêu cầu"
              description="Đơn nghỉ phép, tăng ca và theo dõi"
            />
            <QuickActionLink
              href="/employee/payslips"
              icon={DollarSign}
              iconBg="bg-success/10"
              iconColor="text-success"
              title="Bảng lương"
              description="Phiếu lương đã phát hành"
            />
          </div>

          {/* Status cards — thin, scannable */}
          <div className="fade-in-section grid grid-cols-1 gap-4 sm:grid-cols-2">
            <StatusCard
              icon={todayState === "loading" ? Loader2 : todayRecord?.check_in_at ? LogIn : Clock}
              iconBg="bg-accent/10"
              iconColor={todayState === "loading" ? "text-muted-foreground" : "text-accent"}
              iconSpin={todayState === "loading"}
              title="Chấm công hôm nay"
              value={getTodayLabel()}
              subtitle={getTodaySub()}
            />
            <Link
              href="/employee/requests"
              className="card-hover group rounded-xl border border-border/40 bg-card p-5 transition-all"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-success/10">
                    <ClipboardList className="h-5 w-5 text-success" />
                  </div>
                  <div>
                    <p className="text-[12px] text-muted-foreground">Yêu cầu chờ duyệt</p>
                    <p className="text-[18px] font-semibold text-foreground">—</p>
                  </div>
                </div>
                <span className="text-xs font-medium text-success opacity-0 transition-opacity group-hover:opacity-100">
                  Xem →
                </span>
              </div>
            </Link>
          </div>


        </div>
  );

  // --- helpers ---

  async function fetchToday() {
    try {
      const res = await fetch("/api/attendance/me/today", {
        credentials: "include",
      });
      if (!res.ok) {
        setTodayState("error");
        return;
      }
      const data: {
        check_in_at: string | null;
        check_out_at: string | null;
      } | null = await res.json();
      if (!data) {
        setTodayState("empty");
      } else if (data.check_in_at && !data.check_out_at) {
        setTodayState("checked-in");
      } else if (data.check_in_at && data.check_out_at) {
        setTodayState("completed");
      } else {
        setTodayState("empty");
      }
      setTodayRecord(data);
    } catch {
      setTodayState("error");
    }
  }

  function getTodayLabel(): string {
    switch (todayState) {
      case "loading":
        return "Đang tải...";
      case "empty":
        return "Chưa check-in";
      case "checked-in":
        return "Đã check-in";
      case "completed":
        return "Đã hoàn tất";
      case "error":
        return "Không tải được";
    }
  }

  function getTodaySub(): string {
    switch (todayState) {
      case "loading":
        return "—";
      case "empty":
        return "Chưa check-in hôm nay";
      case "checked-in": {
        const t = todayRecord?.check_in_at;
        return t
          ? `Check-in lúc ${new Date(t).toLocaleTimeString("vi-VN", {
              hour: "2-digit",
              minute: "2-digit",
            })}`
          : "Đã check-in";
      }
      case "completed":
        return "Đã hoàn tất chấm công hôm nay";
      case "error":
        return "Thử lại sau";
    }
  }
}

// --- sub-components ---

    function QuickActionLink({
      href,
      icon: Icon,
      iconBg,
      iconColor,
      title,
      description,
    }: {
      href: string;
      icon: React.ComponentType<{ className?: string }>;
      iconBg: string;
      iconColor: string;
      title: string;
      description: string;
    }) {
      return (
        <Link
          href={href}
          className="card-hover group flex items-center gap-4 rounded-xl border border-border/40 bg-card p-5 transition-all"
        >
          <div
            className={`flex h-10 w-10 items-center justify-center rounded-lg ${iconBg}`}
          >
            <Icon className={`h-5 w-5 ${iconColor}`} />
          </div>
          <div>
            <h3 className="text-[14px] font-medium text-foreground">{title}</h3>
            <p className="text-[12px] text-muted-foreground">{description}</p>
          </div>
        </Link>
      );
    }
    
    function StatusCard({
      icon: Icon,
      iconBg,
      iconColor,
      iconSpin,
      title,
      value,
      subtitle,
    }: {
      icon: React.ComponentType<{ className?: string }>;
      iconBg: string;
      iconColor: string;
      iconSpin?: boolean;
      title: string;
      value: string;
      subtitle: string;
    }) {
      return (
        <div className="rounded-xl border border-border/40 bg-card p-5 card-hover">
          <div className="flex items-center gap-3">
            <div
              className={`flex h-10 w-10 items-center justify-center rounded-lg ${iconBg}`}
            >
              <Icon
                className={`h-5 w-5 ${iconColor} ${iconSpin ? "animate-spin" : ""}`}
              />
            </div>
            <div className="min-w-0">
              <p className="text-[12px] text-muted-foreground">{title}</p>
              <p className="text-[18px] font-semibold text-foreground">{value}</p>
              <p className="truncate text-[12px] text-muted-foreground/80">{subtitle}</p>
            </div>
          </div>
        </div>
      );
    }
