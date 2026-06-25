"use client";

import React from "react";
import Link from "next/link";
import {
  Users,
  Building2,
  Briefcase,
  UserPlus,
  FileText,
  ArrowUpRight,
  Target,
  Mail,
  UserCheck,
  Clock,
} from "lucide-react";

import { useRouter } from "next/navigation";
import { useCurrentUser } from "@/hooks/use-current-user";
import { useDashboardStats } from "@/hooks/queries";
import { RuntimeHealthPanel } from "@/components/admin/runtime-health-panel";
import { StatCard } from "@/components/stat-card";

// ─── Quick Action ───────────────────────────────────────────────────────────
function QuickAction({
  title,
  href,
  icon: Icon,
  description,
  variant = "default",
}: {
  title: string;
  href: string;
  icon: React.ElementType;
  description?: string;
  variant?: "default" | "primary";
}) {
  const isPrimary = variant === "primary";

  return (
    <Link
      href={href}
      className={`group flex items-start gap-4 rounded-xl p-4 transition-all ${
        isPrimary
          ? "bg-primary text-primary-foreground"
          : "border border-border/50 bg-card text-foreground hover:border-border hover:shadow-sm"
      }`}
    >
      <div
        className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${
          isPrimary ? "bg-primary-foreground/20" : "bg-secondary"
        }`}
      >
        <Icon
          className={`h-5 w-5 ${isPrimary ? "text-primary-foreground" : "text-muted-foreground"}`}
          aria-hidden="true"
        />
      </div>
      <div className="flex-1 min-w-0 space-y-0.5">
        <h3 className="text-sm font-semibold">{title}</h3>
        {description && (
          <p
            className={`text-xs ${isPrimary ? "text-primary-foreground/70" : "text-muted-foreground"}`}
          >
            {description}
          </p>
        )}
      </div>
      <ArrowUpRight
        className={`mt-1 h-3.5 w-3.5 shrink-0 opacity-0 transition-opacity group-hover:opacity-100 ${
          isPrimary ? "text-primary-foreground/70" : "text-muted-foreground"
        }`}
      />
    </Link>
  );
}

// ─── Empty State Panel ──────────────────────────────────────────────────────
function EmptyPanel({
  title,
  icon: Icon,
}: {
  title: string;
  icon: React.ElementType;
}) {
  return (
    <div className="rounded-xl border border-border/30 bg-card p-6">
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground">
        {title}
      </h3>
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-secondary">
          <Icon className="h-5 w-5 text-muted-foreground/60" aria-hidden="true" />
        </div>
        <p className="text-sm text-muted-foreground">Chưa có dữ liệu</p>
        <p className="mt-1 text-xs text-muted-foreground/60">
          Dữ liệu sẽ hiển thị khi có hoạt động mới
        </p>
      </div>
    </div>
  );
}

// ─── Helpers ────────────────────────────────────────────────────────────────
function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "Chào buổi sáng";
  if (hour < 18) return "Chào buổi chiều";
  return "Chào buổi tối";
}

function formatDate() {
  return new Date().toLocaleDateString("vi-VN", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

// ─── Main Dashboard ─────────────────────────────────────────────────────────
export default function DashboardPage() {
  const { data: stats, isLoading: loading } = useDashboardStats();
  const { user } = useCurrentUser();
  const router = useRouter();

  // Redirect employees to their self-service dashboard
  React.useEffect(() => {
    if (!loading && user && user.role === "user" && user.employee_id) {
      router.replace("/employee/dashboard");
    }
  }, [user, loading, router]);
  const [greeting, setGreeting] = React.useState("");
  const [dateStr, setDateStr] = React.useState("");

  React.useEffect(() => {
    setGreeting(getGreeting());
    setDateStr(formatDate());
  }, []);

  return (
    <div className="space-y-10 max-w-[1440px] mx-auto overflow-x-hidden">
      {/* ─── Welcome ─────────────────────────────────────────────────────── */}
      <div>
        <h1 className="font-heading text-2xl font-semibold text-foreground">
          {greeting}
          {user?.email ? `, ${user.email.split("@")[0]}` : ""}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">{dateStr}</p>
      </div>

      {/* ─── Stats Grid ──────────────────────────────────────────────────── */}
      <div>
        <h2 className="mb-4 text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground">
          Tổng quan
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <StatCard
            title="Nhân viên"
            value={stats?.employees ?? 0}
            icon={Users}
            loading={loading}
          />
          <StatCard
            title="Phòng ban"
            value={stats?.departments ?? 0}
            icon={Building2}
            loading={loading}
          />
          <StatCard
            title="Chức vụ"
            value={stats?.positions ?? 0}
            icon={Briefcase}
            loading={loading}
          />
        </div>
        </div>

        {user?.role === "admin" && <RuntimeHealthPanel />}

        {/* Install CTA — show for all users */}
        <div className="rounded-xl border border-border/30 bg-card p-4">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-semibold">Cài đặt Vroom HR cho công ty</p>
              <p className="text-xs text-muted-foreground">Tự host trên hạ tầng của bạn — Docker Compose, không phụ thuộc vendor</p>
            </div>
            <a
              href="https://github.com/NullNyx/Vietnamese-Recruit-Onboard-Operate-Manage"
              target="_blank"
              rel="noopener noreferrer"
              className="shrink-0 inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/>
              </svg>
              Cài đặt cho công ty
            </a>
          </div>
        </div>

        {/* ─── Quick Actions ───────────────────────────────────────────────── */}
        <div>
        <h2 className="mb-4 text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground">
          Thao tác nhanh
        </h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <QuickAction
            title="Thêm nhân viên"
            href="/employees/new"
            icon={UserPlus}
            description="Nhập thông tin nhân viên mới"
            variant="primary"
          />
          <QuickAction
            title="Import Excel"
            href="/employees/import"
            icon={FileText}
            description="Nhập hàng loạt từ file"
          />
          <QuickAction
            title="Tuyển dụng"
            href="/recruitment"
            icon={Target}
            description="Quản lý ứng viên và phỏng vấn"
          />
          <QuickAction
            title="Phòng ban"
            href="/settings/departments"
            icon={Building2}
            description="Cơ cấu tổ chức"
          />
          <QuickAction
            title="Chức vụ"
            href="/settings/positions"
            icon={Briefcase}
            description="Danh sách vị trí"
          />
          <QuickAction
            title="Gmail"
            href="/gmail"
            icon={Mail}
            description="Hộp thư kết nối"
          />
        </div>
      </div>

      {/* ─── Bottom Panels ───────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <EmptyPanel title="Hoạt động gần đây" icon={Clock} />
        <EmptyPanel title="Nhân viên mới tháng này" icon={UserCheck} />
      </div>
    </div>
  );
}
